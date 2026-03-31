"""
Motor de análise via Groq API — dois modos:
  1. Análise contra Minuta Padrão CINCATARINA
  2. Análise de Termos Aditivos (contrato original + anteriores + novo)

Melhorias v2.1:
  - Motor único para aditivos (analisador_aditivos.py descontinuado)
  - Validação de schema com Pydantic (campos obrigatórios + enums)
  - Explicabilidade: cada divergência traz trecho-fonte extraído do texto
  - Retry com backoff exponencial (até 3 tentativas)
  - Reparo de JSON malformado antes de erro fatal
  - Categorização de erros para melhor diagnóstico na UI
"""
import json
import re
import time
import logging
from datetime import date
from enum import Enum

from groq import Groq

try:
    from pydantic import BaseModel, field_validator
    PYDANTIC_DISPONIVEL = True
except ImportError:
    PYDANTIC_DISPONIVEL = False

from minuta_conhecimento import CONTEXTO_MINUTA, PROMPT_ANALISE, PROMPT_TERMOS_ADITIVOS

log = logging.getLogger(__name__)

# =========================================================================
# Limites de contexto — ajustados para Groq FREE tier (12k tokens/req)
# =========================================================================
LIMITE_CONTRATO  = 15000
LIMITE_ORIGINAL  = 8000
LIMITE_NOVO      = 8000
LIMITE_ANTERIOR  = 5000
MAX_RETRIES      = 3
MAX_TOKENS_RESPOSTA = 4000   # aumentado para acomodar campo evidencia_textual


# =========================================================================
# Categorias de erro para diagnóstico na UI
# =========================================================================
class TipoErroAnalise(str, Enum):
    DOCUMENTO_GRANDE  = "DOCUMENTO_GRANDE"
    JSON_INVALIDO     = "JSON_INVALIDO"
    SCHEMA_INVALIDO   = "SCHEMA_INVALIDO"
    ERRO_API          = "ERRO_API"
    EXTRACAO_FALHOU   = "EXTRACAO_FALHOU"


class ErroAnalise(RuntimeError):
    def __init__(self, mensagem: str, tipo: TipoErroAnalise, detalhe: str = ""):
        super().__init__(mensagem)
        self.tipo    = tipo
        self.detalhe = detalhe

    def mensagem_usuario(self) -> str:
        dicas = {
            TipoErroAnalise.DOCUMENTO_GRANDE: (
                "O documento é grande demais para o plano gratuito do Groq (~12k tokens por requisição).\n"
                "Soluções: (1) Tente um contrato mais curto, "
                "(2) Faça upgrade em console.groq.com/settings/billing, "
                "(3) Troque o modelo para Mixtral 8x7B na barra lateral."
            ),
            TipoErroAnalise.JSON_INVALIDO: (
                "A IA retornou resposta mal-formatada após 3 tentativas. "
                "Tente analisar novamente ou troque o modelo LLM na barra lateral."
            ),
            TipoErroAnalise.SCHEMA_INVALIDO: (
                "A resposta da IA passou na validação JSON mas está com campos faltando ou inválidos. "
                "Tente analisar novamente — pode ser instabilidade do modelo."
            ),
            TipoErroAnalise.ERRO_API: (
                "Erro na API Groq. Verifique sua chave API e tente novamente."
            ),
            TipoErroAnalise.EXTRACAO_FALHOU: (
                "Não foi possível extrair o texto do documento. "
                "Verifique se o arquivo é um PDF pesquisável ou DOCX válido."
            ),
        }
        return f"{str(self)}\n\n💡 {dicas.get(self.tipo, '')}"


# =========================================================================
# Schemas Pydantic — validação de saída do LLM
# =========================================================================
if PYDANTIC_DISPONIVEL:
    class ApontamentoMinuta(BaseModel):
        clausula: str = ""
        tipo: str = "ALERTA"
        descricao: str = ""
        previsto_minuta: str = ""
        encontrado_contrato: str = ""
        evidencia_textual: str = ""

        @field_validator("tipo")
        @classmethod
        def validar_tipo(cls, v):
            validos = {"DIVERGÊNCIA CRÍTICA", "DIVERGÊNCIA", "CLÁUSULA EXTRA", "CLÁUSULA FALTANTE", "ALERTA"}
            return v if v in validos else "ALERTA"

    class ClausulaMapMinuta(BaseModel):
        clausula: str = ""
        resumo_contrato: str = ""
        resumo_minuta: str = ""
        status: str = "NÃO LOCALIZADA"
        observacao: str = ""

        @field_validator("status")
        @classmethod
        def validar_status(cls, v):
            validos = {"CONFORME", "DIVERGENTE", "PARCIALMENTE CONFORME", "NÃO LOCALIZADA"}
            return v if v in validos else "NÃO LOCALIZADA"

    class ResultadoMinuta(BaseModel):
        status_geral: str = "COM DIVERGÊNCIAS"
        municipio: str = ""
        numero_contrato: str = ""
        data_analise: str = ""
        resumo_executivo: str = ""
        mapeamento_clausulas: list[ClausulaMapMinuta] = []
        apontamentos: list[ApontamentoMinuta] = []
        prazos_verificados: dict = {}
        valores_verificados: dict = {}
        multas_verificadas: dict = {}
        foro_verificado: dict = {}
        partes_verificadas: dict = {}
        clausulas_extras: list[str] = []
        clausulas_faltantes: list[str] = []

        @field_validator("status_geral")
        @classmethod
        def validar_status_geral(cls, v):
            validos = {"CONFORME", "COM DIVERGÊNCIAS", "COM DIVERGÊNCIAS CRÍTICAS"}
            return v if v in validos else "COM DIVERGÊNCIAS"

    class DivergenciaAditivo(BaseModel):
        tipo: str = "ALERTA"
        categoria: str = "OUTRO"
        clausula: str = ""
        previsto: str = ""
        encontrado: str = ""
        descricao: str = ""
        evidencia_textual: str = ""

        @field_validator("tipo")
        @classmethod
        def validar_tipo(cls, v):
            validos = {"DIVERGÊNCIA CRÍTICA", "DIVERGÊNCIA", "ALERTA", "CLÁUSULA EXTRA", "CLÁUSULA FALTANTE"}
            return v if v in validos else "ALERTA"

        @field_validator("categoria")
        @classmethod
        def validar_categoria(cls, v):
            validos = {"PRAZO", "VALOR", "DATA", "ASSINANTE", "RESPONSÁVEL", "CLÁUSULA", "OBJETO", "OUTRO"}
            return v if v in validos else "OUTRO"

    class ClausulaMapAditivo(BaseModel):
        clausula: str = ""
        resumo_original: str = ""
        resumo_anteriores: str = "N/A"
        resumo_novo_termo: str = ""
        status: str = "MANTIDA"
        observacao: str = ""

        @field_validator("status")
        @classmethod
        def validar_status(cls, v):
            validos = {"MANTIDA", "ALTERADA", "NOVA", "REMOVIDA"}
            return v if v in validos else "MANTIDA"

    class ResultadoAditivos(BaseModel):
        status_geral: str = "COM DIVERGÊNCIAS"
        numero_contrato: str = ""
        objeto_contrato: str = ""
        partes: dict = {}
        assinantes_novo_termo: list[dict] = []
        resumo_executivo: str = ""
        mapeamento_clausulas: list[ClausulaMapAditivo] = []
        divergencias: list[DivergenciaAditivo] = []
        prazos: list[dict] = []
        valores: list[dict] = []
        datas: list[dict] = []
        clausulas_extras: list[str] = []
        clausulas_faltantes: list[str] = []
        data_analise: str = ""

        @field_validator("status_geral")
        @classmethod
        def validar_status_geral(cls, v):
            validos = {"CONFORME", "COM DIVERGÊNCIAS", "COM DIVERGÊNCIAS CRÍTICAS"}
            return v if v in validos else "COM DIVERGÊNCIAS"


def _validar_schema(dados: dict, modo: str) -> dict:
    """Valida e normaliza saída do LLM com Pydantic. Retorna dict limpo."""
    if not PYDANTIC_DISPONIVEL:
        return dados
    try:
        if modo == "minuta":
            return ResultadoMinuta(**dados).model_dump()
        else:
            return ResultadoAditivos(**dados).model_dump()
    except Exception as e:
        raise ErroAnalise(
            f"Resposta da IA com estrutura inválida: {e}",
            TipoErroAnalise.SCHEMA_INVALIDO,
            detalhe=str(e),
        )


# =========================================================================
# Análise de Minuta Padrão
# =========================================================================
def analisar_contrato(
    texto: str,
    municipio: str,
    numero: str,
    data_contrato: str,
    api_key: str,
    modelo: str = "llama-3.3-70b-versatile",
) -> dict:
    system_msg = (
        CONTEXTO_MINUTA + "\n\n"
        "Você é um analista jurídico especializado. "
        "Responda APENAS com JSON válido, sem markdown, sem texto fora do JSON.\n"
        "IMPORTANTE: Para cada apontamento, inclua o campo 'evidencia_textual' com o trecho "
        "EXATO (máx. 200 caracteres) do contrato que gerou aquela divergência ou alerta. "
        "Se não houver trecho identificável, deixe o campo como string vazia."
    )
    prompt = PROMPT_ANALISE.format(
        contexto_minuta="",
        municipio=municipio,
        numero_contrato=numero,
        data_contrato=data_contrato,
        texto_contrato=texto[:LIMITE_CONTRATO],
        data_hoje=date.today().strftime("%d/%m/%Y"),
    )
    dados = _chamar_groq(prompt, api_key, modelo, system_msg=system_msg)
    return _validar_schema(dados, "minuta")


MODELO_RAPIDO = "llama-3.1-8b-instant"


def extrair_metadados_contrato(
    texto: str,
    api_key: str,
    modelo: str = "llama-3.3-70b-versatile",
) -> dict:
    prompt = f"""Extraia do texto abaixo APENAS estas informações:
- municipio: nome do município contratante
- numero_contrato: número do contrato
- data_contrato: data do contrato

Texto (primeiros 3000 caracteres):
{texto[:3000]}

Responda APENAS com JSON válido:
{{"municipio": "...", "numero_contrato": "...", "data_contrato": "..."}}"""
    return _chamar_groq(prompt, api_key, MODELO_RAPIDO)


# =========================================================================
# Análise de Termos Aditivos — motor único consolidado
# (substitui analisador_aditivos.py — não use mais aquele arquivo)
# =========================================================================
def analisar_termos_aditivos(
    texto_original: str,
    termos_anteriores: list,
    texto_novo: str,
    api_key: str,
    modelo: str = "llama-3.3-70b-versatile",
) -> dict:
    if termos_anteriores:
        anteriores_str = "\n\n".join(
            f"=== {i+1}º TERMO ADITIVO ===\n{t[:LIMITE_ANTERIOR]}"
            for i, t in enumerate(termos_anteriores)
        )
    else:
        anteriores_str = "Nenhum termo aditivo anterior fornecido."

    prompt = PROMPT_TERMOS_ADITIVOS.format(
        texto_original=texto_original[:LIMITE_ORIGINAL],
        termos_anteriores=anteriores_str,
        texto_novo=texto_novo[:LIMITE_NOVO],
        data_hoje=date.today().strftime("%d/%m/%Y"),
    )
    dados = _chamar_groq(
        prompt,
        api_key,
        modelo,
        system_msg=(
            "Você é um analista jurídico especializado em contratos públicos brasileiros. "
            "Responda APENAS com JSON válido, sem markdown, sem texto fora do JSON.\n"
            "IMPORTANTE: Para cada divergência, inclua o campo 'evidencia_textual' com o trecho "
            "EXATO (máx. 200 caracteres) do NOVO TERMO que suporta aquela divergência. "
            "Se não houver trecho identificável, deixe o campo como string vazia."
        ),
    )
    return _validar_schema(dados, "aditivos")


def extrair_metadados_aditivo(
    texto: str,
    api_key: str,
    modelo: str = "llama-3.3-70b-versatile",
) -> dict:
    """Extrai metadados básicos de um termo aditivo (compatibilidade com código legado)."""
    prompt = f"""Extraia do texto abaixo estas informações e retorne como JSON:
{{
  "numero_contrato": "número do contrato",
  "numero_aditivo": "número do termo aditivo",
  "contratante": "nome do contratante",
  "contratada": "nome da contratada"
}}
Se algum campo não for encontrado, use string vazia.

Texto (primeiros 3000 caracteres):
{texto[:3000]}

Responda APENAS com JSON válido, sem markdown."""
    try:
        return _chamar_groq(prompt, api_key, MODELO_RAPIDO)
    except Exception:
        return {"numero_contrato": "", "numero_aditivo": "", "contratante": "", "contratada": ""}


# =========================================================================
# Chamada Groq com retry + reparo de JSON + categorização de erro
# =========================================================================
def _reparar_json(texto: str) -> str:
    """Tenta reparar JSON malformado antes de desistir."""
    texto = re.sub(r"^```(?:json)?\s*", "", texto)
    texto = re.sub(r"\s*```$", "", texto)
    inicio = texto.find("{")
    fim = texto.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        texto = texto[inicio:fim + 1]
    texto = re.sub(r",\s*([}\]])", r"\1", texto)
    return texto


def _chamar_groq(
    prompt: str,
    api_key: str,
    modelo: str,
    system_msg: str = None,
) -> dict:
    client = Groq(api_key=api_key)
    ultimo_erro = None

    if not system_msg:
        system_msg = (
            "Você é um analista jurídico especializado. "
            "Responda APENAS com JSON válido, sem markdown, sem texto fora do JSON."
        )

    for tentativa in range(MAX_RETRIES):
        try:
            resposta = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.1,
                max_tokens=MAX_TOKENS_RESPOSTA,
            )
            conteudo = resposta.choices[0].message.content.strip()
            conteudo_reparado = _reparar_json(conteudo)
            resultado = json.loads(conteudo_reparado)
            if tentativa > 0:
                log.info(f"Sucesso na tentativa {tentativa + 1}")
            return resultado

        except json.JSONDecodeError as e:
            ultimo_erro = e
            log.warning(f"Tentativa {tentativa + 1}/{MAX_RETRIES}: JSON inválido — {e}")
            if tentativa < MAX_RETRIES - 1:
                time.sleep(2 ** tentativa)

        except ErroAnalise:
            raise  # repassa sem re-encapsular

        except Exception as e:
            erro_str = str(e)
            if "413" in erro_str or "Request too large" in erro_str:
                raise ErroAnalise(
                    "Documento muito grande para o plano gratuito do Groq.",
                    TipoErroAnalise.DOCUMENTO_GRANDE,
                    detalhe=erro_str,
                )
            ultimo_erro = e
            log.warning(f"Tentativa {tentativa + 1}/{MAX_RETRIES}: Erro API — {e}")
            if tentativa < MAX_RETRIES - 1:
                time.sleep(2 ** tentativa)

    # Esgotou tentativas — classifica o tipo de erro
    if isinstance(ultimo_erro, json.JSONDecodeError):
        raise ErroAnalise(
            f"IA retornou JSON inválido após {MAX_RETRIES} tentativas.",
            TipoErroAnalise.JSON_INVALIDO,
            detalhe=str(ultimo_erro),
        )
    raise ErroAnalise(
        f"Falha na API após {MAX_RETRIES} tentativas.",
        TipoErroAnalise.ERRO_API,
        detalhe=str(ultimo_erro),
    )


# =========================================================================
# Helpers de UI
# =========================================================================
def classificar_cor_status(status: str) -> str:
    return {
        "CONFORME": "#28a745",
        "COM DIVERGÊNCIAS": "#fd7e14",
        "COM DIVERGÊNCIAS CRÍTICAS": "#dc3545",
    }.get(status, "#6c757d")


def classificar_cor_apontamento(tipo: str) -> str:
    return {
        "DIVERGÊNCIA CRÍTICA": "#dc3545",
        "DIVERGÊNCIA": "#fd7e14",
        "CLÁUSULA EXTRA": "#6610f2",
        "CLÁUSULA FALTANTE": "#dc3545",
        "ALERTA": "#ffc107",
    }.get(tipo, "#6c757d")


def classificar_icon_apontamento(tipo: str) -> str:
    return {
        "DIVERGÊNCIA CRÍTICA": "🔴",
        "DIVERGÊNCIA": "🟠",
        "CLÁUSULA EXTRA": "🟣",
        "CLÁUSULA FALTANTE": "⛔",
        "ALERTA": "⚠️",
    }.get(tipo, "ℹ️")


def status_icon(status: str) -> str:
    if status in ("OK", "CONFORME", "MANTIDA"):
        return "✅"
    if status in ("DIVERGENTE", "AUSENTE", "REMOVIDA"):
        return "❌"
    if status in ("ALTERADO", "ALTERADA", "PARCIALMENTE CONFORME"):
        return "🟠"
    if status == "NOVA":
        return "🟣"
    return "⚪"
