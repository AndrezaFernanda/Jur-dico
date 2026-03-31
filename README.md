# ⚖️ Analisador Jurídico — CINCATARINA v2.0

Análise jurídica automatizada com dois modos de operação.

## 📋 Dois Modos de Análise

### 🏛️ Modo 1: Minuta Padrão
Compara um contrato contra a minuta padrão do CINCATARINA para gestão de frota/combustíveis.
- Upload de um único contrato (PDF ou DOCX)
- Extração automática de metadados (município, número, data)
- Análise cláusula por cláusula com status OK/DIVERGENTE/AUSENTE
- Verificação de prazos, multas, foro, partes
- Identificação de cláusulas extras e faltantes

### 📑 Modo 2: Termos Aditivos
Compara contrato original + termos anteriores + novo termo aditivo.
- Upload de até 3 tipos de documento (original, anteriores, novo)
- Análise de divergências entre versões
- Verificação de prazos, valores, datas, assinantes
- Comparação cláusula por cláusula: Original × Anteriores × Novo

## 🔑 Configuração da API

### Streamlit Cloud (recomendado)
Em **Settings → Secrets** do app:
```toml
GROQ_API_KEY = "gsk_sua_chave_aqui"
```

### Local
Edite `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_sua_chave_aqui"
```

Se nenhuma chave estiver configurada, aparece campo para inserção manual.

## 🚀 Deploy

```bash
git init && git add . && git commit -m "v2.0"
git remote add origin https://github.com/seu-usuario/analisador-juridico.git
git push -u origin main
```

No Streamlit Cloud: conecte o repo, aponte para `app.py`, configure Secrets.

## 📦 Estrutura

| Arquivo | Função |
|---|---|
| `app.py` | Interface Streamlit com dois modos |
| `analisador.py` | Motor de análise Minuta Padrão (Groq) |
| `analisador_aditivos.py` | Motor de análise Termos Aditivos (Groq) |
| `minuta_conhecimento.py` | Base de conhecimento CINCATARINA |
| `extrator.py` | Extração de texto (PDF + OCR + DOCX) |
| `relatorio.py` | Gerador DOCX para ambos os modos |
| `requirements.txt` | Dependências Python |
| `packages.txt` | Dependências sistema (Tesseract, Poppler) |

## ✏️ Funcionalidades do Analista

- **Editar Decisão** em qualquer item (cláusulas, apontamentos, prazos, multas, etc.)
- **Validar Manualmente** ou **Seguir sem Validação**
- Todas as decisões aparecem no relatório DOCX
- Seção consolidada "Registro de Decisões do Analista"
