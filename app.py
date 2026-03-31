import streamlit as st
import os
from datetime import date, datetime

from extrator import extrair_texto
from analisador import (
    analisar_contrato,
    analisar_termos_aditivos,
    extrair_metadados_contrato,
    classificar_cor_status,
    classificar_cor_apontamento,
    classificar_icon_apontamento,
    status_icon,
    ErroAnalise,
)
from relatorio import gerar_relatorio_docx, gerar_relatorio_aditivos_docx, gerar_relatorio_html

# =============================================================================
# CONFIG
# =============================================================================
st.set_page_config(page_title="Analisador Jurídico — CINCATARINA", page_icon="⚖️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #f4f6fb; }
    .main-title { font-size: 2rem; font-weight: 700; color: #1F3864; margin-bottom: 0.2rem; }
    .sub-title { font-size: 1rem; color: #555; margin-bottom: 1.5rem; }
    .status-badge { display: inline-block; padding: 6px 18px; border-radius: 20px; font-weight: 700; font-size: 1.1rem; color: white; margin-bottom: 1rem; }
    .revisao-box { background: #fff8e1; border: 1.5px solid #ffc107; border-radius: 8px; padding: 1rem; margin-top: 0.5rem; }
    .validado-box { background: #e8f5e9; border: 1.5px solid #28a745; border-radius: 8px; padding: 0.7rem 1rem; margin-top: 0.5rem; }
    .sem-validacao-box { background: #fff3e0; border: 1.5px solid #fd7e14; border-radius: 8px; padding: 0.7rem 1rem; margin-top: 0.5rem; }
    .evidencia-box { background: #f0f4ff; border-left: 4px solid #4a6fa5; border-radius: 4px; padding: 0.5rem 0.8rem; margin-top: 0.4rem; font-size: 0.85rem; font-style: italic; color: #333; }
    div[data-testid="stSidebar"] { background-color: #1F3864; }
    div[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# WIDGET DE REVISÃO MANUAL (reutilizável)
# =============================================================================
def widget_revisao(chave: str, rotulo: str, revisoes: dict):
    if chave in revisoes:
        rev = revisoes[chave]
        if rev["status"] == "VALIDADO":
            st.markdown(f'<div class="validado-box">✅ Validado por <b>{rev["analista"]}</b> em {rev["timestamp"]}<br>{rev["justificativa"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="sem-validacao-box">📋 Sem validação por <b>{rev["analista"]}</b> em {rev["timestamp"]}<br>{rev["justificativa"]}</div>', unsafe_allow_html=True)
        if st.button("🔄 Refazer Decisão", key=f"refazer_{chave}"):
            del revisoes[chave]
            st.rerun()
        return

    with st.expander("✏️ Editar Decisão", expanded=False):
        analista = st.text_input("Nome do analista", key=f"an_{chave}")
        justificativa = st.text_area("Justificativa / Observação", key=f"ju_{chave}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Validar Manualmente", key=f"val_{chave}"):
                revisoes[chave] = {"status": "VALIDADO", "rotulo": rotulo, "analista": analista or "Não informado",
                                   "justificativa": justificativa or "Sem observação", "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")}
                st.rerun()
        with c2:
            if st.button("➡️ Seguir sem Validação", key=f"sem_{chave}"):
                revisoes[chave] = {"status": "SEM_VAL", "rotulo": rotulo, "analista": analista or "Não informado",
                                   "justificativa": justificativa or "Sem observação", "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")}
                st.rerun()

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("### ⚖️ Analisador Jurídico")
    st.markdown("CINCATARINA / MaxiFrota")
    st.markdown("---")

    # API Key — busca secrets → env → manual
    _chave_auto = ""
    try:
        _chave_auto = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    if not _chave_auto:
        _chave_auto = os.getenv("GROQ_API_KEY", "")

    if _chave_auto:
        groq_api_key = _chave_auto
        st.success("🔑 API Groq configurada", icon="✅")
    else:
        groq_api_key = st.text_input("🔑 Chave API Groq", type="password",
                                     help="Configure em Settings › Secrets no Streamlit Cloud, ou cole aqui")

    modelo = st.selectbox("Modelo LLM", ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"])
    st.markdown("---")
    modo = st.radio("📋 Modo de Análise", ["🏛️ Minuta Padrão", "📑 Termos Aditivos"],
                    help="Minuta Padrão: compara contrato com a minuta CINCATARINA\nTermos Aditivos: compara contrato original com termos")

# =============================================================================
# Inicializar session state
# =============================================================================
defaults = {
    "resultado": None,
    "revisoes": {},
    "texto_contrato": "",
    "texto_original": "",
    "texto_novo": "",
    "termos_anteriores_textos": [],
    "num_termos_anteriores": 0,
    "_resultado_modo": None,
    "_modo_anterior": modo,
}
for key, default_value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# Evita reaproveitar resultado de um modo no outro ao alternar o rádio
if st.session_state.get("_modo_anterior") != modo:
    st.session_state.resultado = None
    st.session_state.revisoes = {}
    st.session_state._resultado_modo = None
st.session_state._modo_anterior = modo

# =============================================================================
# MODO 1: MINUTA PADRÃO
# =============================================================================
if "Minuta" in modo:
    st.markdown('<div class="main-title">📋 Análise contra Minuta Padrão</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Faça upload do contrato e compare com a minuta CINCATARINA</div>', unsafe_allow_html=True)

    arquivo = st.file_uploader("📄 Upload do Contrato", type=["pdf", "docx", "doc"], key="upload_minuta")

    if arquivo and groq_api_key:
        arquivo_bytes = arquivo.read()
        # Invalidação por nome + tamanho (detecta mesmo arquivo com nome igual mas versão diferente)
        _file_id = f"{arquivo.name}_{len(arquivo_bytes)}"

        if st.session_state.get("_ultimo_arquivo_minuta") != _file_id:
            st.session_state._ultimo_arquivo_minuta = _file_id
            st.session_state.resultado = None
            st.session_state.revisoes = {}

            with st.spinner("📄 Extraindo texto do documento..."):
                texto = extrair_texto(arquivo_bytes, arquivo.name)
                st.session_state.texto_contrato = texto

            with st.spinner("🔍 Extraindo metadados com IA..."):
                try:
                    meta = extrair_metadados_contrato(texto, groq_api_key, modelo)
                    st.session_state._meta = meta
                except Exception:
                    st.session_state._meta = {}

        meta = st.session_state.get("_meta", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            municipio = st.text_input("🏙️ Município", value=meta.get("municipio", ""))
        with col2:
            numero = st.text_input("📝 Nº Contrato", value=meta.get("numero_contrato", ""))
        with col3:
            data_c = st.text_input("📅 Data", value=meta.get("data_contrato", date.today().strftime("%d/%m/%Y")))

        if st.button("🔍 Analisar Contrato", type="primary", use_container_width=True):
            with st.spinner("⚖️ Analisando conformidade com IA (até 3 tentativas automáticas)..."):
                try:
                    resultado = analisar_contrato(st.session_state.texto_contrato, municipio, numero, data_c, groq_api_key, modelo)
                    st.session_state.resultado = resultado
                    st.session_state._resultado_modo = "minuta"
                    st.session_state.revisoes = {}
                except ErroAnalise as e:
                    st.error(f"❌ {e.tipo.value}: {str(e)}")
                    st.info(e.mensagem_usuario())
                except Exception as e:
                    st.error(f"❌ Erro inesperado: {e}")
                    st.info("💡 Tente trocar o modelo LLM na barra lateral ou analisar novamente.")

    # Exibir resultado
    resultado = st.session_state.resultado
    if resultado and st.session_state.get("_resultado_modo") == "minuta" and "status_geral" in resultado:
        revisoes = st.session_state.revisoes
        status = resultado.get("status_geral", "—")
        cor = classificar_cor_status(status)
        st.markdown(f'<div class="status-badge" style="background:{cor}">{status}</div>', unsafe_allow_html=True)
        st.info(resultado.get("resumo_executivo", ""))

        # Abas
        tab_clausulas, tab_apon, tab_prazos, tab_multas, tab_foro, tab_extras = st.tabs(
            ["📖 Cláusulas", "🚨 Apontamentos", "📅 Prazos", "💰 Multas", "🏛️ Foro & Partes", "📌 Extras/Faltantes"])

        # Tab Cláusulas
        with tab_clausulas:
            mapeamento = resultado.get("mapeamento_clausulas", [])
            if mapeamento:
                for i, cl in enumerate(mapeamento):
                    s = cl.get("status", "—")
                    icon = status_icon(s)
                    with st.expander(f"{icon} {cl.get('clausula', f'Cláusula {i+1}')} — **{s}**"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**📋 No Contrato:**")
                            st.write(cl.get("resumo_contrato", "—"))
                        with c2:
                            st.markdown("**📜 Na Minuta Padrão:**")
                            st.write(cl.get("resumo_minuta", "—"))
                        if cl.get("observacao"):
                            st.caption(f"📝 {cl['observacao']}")
                        widget_revisao(f"clausula_{i}", cl.get("clausula", f"Cláusula {i+1}"), revisoes)
            else:
                st.info("O mapeamento cláusula a cláusula não foi retornado pela IA. Tente analisar novamente.")

        # Tab Apontamentos
        with tab_apon:
            apontamentos = resultado.get("apontamentos", [])
            if not apontamentos:
                st.success("✅ Nenhum apontamento identificado.")
            for i, ap in enumerate(apontamentos):
                icon = classificar_icon_apontamento(ap.get("tipo", ""))
                cor_ap = classificar_cor_apontamento(ap.get("tipo", ""))
                with st.expander(f"{icon} [{ap.get('tipo', '')}] {ap.get('clausula', '')} — {ap.get('descricao', '')[:60]}..."):
                    st.markdown(f"**Descrição:** {ap.get('descricao', '—')}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"🟢 **Previsto na Minuta:** {ap.get('previsto_minuta', '—')}")
                    with c2:
                        st.markdown(f"🟠 **Encontrado no Contrato:** {ap.get('encontrado_contrato', '—')}")
                    evidencia = ap.get("evidencia_textual", "")
                    if evidencia:
                        st.markdown(f'<div class="evidencia-box">📎 <b>Trecho-fonte:</b> "{evidencia}"</div>', unsafe_allow_html=True)
                    widget_revisao(f"apontamento_{i}", ap.get("clausula", f"Apontamento {i+1}"), revisoes)

        # Tab Prazos
        with tab_prazos:
            prazos = resultado.get("prazos_verificados", {})
            nomes = {"prazo_pagamento": "Prazo de Pagamento", "prazo_vigencia": "Prazo de Vigência",
                     "prazo_correcao_vicios": "Correção de Vícios", "prazo_relatorios": "Entrega de Relatórios"}
            for chave_p, nome in nomes.items():
                p_data = prazos.get(chave_p, {})
                s = p_data.get("status", "—")
                icon = status_icon(s)
                with st.expander(f"{icon} {nome} — **{s}**"):
                    st.write(f"**Previsto:** {p_data.get('previsto', '—')}")
                    st.write(f"**Encontrado:** {p_data.get('encontrado', '—')}")
                    widget_revisao(f"prazo_{chave_p}", nome, revisoes)

        # Tab Multas
        with tab_multas:
            multas = resultado.get("multas_verificadas", {})
            nomes_m = {"multa_atraso_diaria": "Multa Atraso (diária)", "multa_inexecucao_parcial": "Inexecução Parcial",
                       "multa_inexecucao_total": "Inexecução Total"}
            for chave_m, nome in nomes_m.items():
                m_data = multas.get(chave_m, {})
                s = m_data.get("status", "—")
                icon = status_icon(s)
                with st.expander(f"{icon} {nome} — **{s}**"):
                    st.write(f"**Previsto:** {m_data.get('previsto', '—')}")
                    st.write(f"**Encontrado:** {m_data.get('encontrado', '—')}")
                    widget_revisao(f"multa_{chave_m}", nome, revisoes)

        # Tab Foro
        with tab_foro:
            foro = resultado.get("foro_verificado", {})
            icon = status_icon(foro.get("status", ""))
            with st.expander(f"{icon} Foro — **{foro.get('status', '—')}**"):
                st.write(f"**Previsto:** {foro.get('previsto', '—')}")
                st.write(f"**Encontrado:** {foro.get('encontrado', '—')}")
                widget_revisao("foro", "Foro", revisoes)
            partes = resultado.get("partes_verificadas", {})
            nomes_p = {"contratante": "Contratante", "contratada": "Contratada (MaxiFrota)", "interveniente_cincatarina": "CINCATARINA"}
            for chave_p, nome in nomes_p.items():
                p_data = partes.get(chave_p, {})
                icon = status_icon(p_data.get("status", ""))
                with st.expander(f"{icon} {nome} — **{p_data.get('status', '—')}**"):
                    st.write(f"**Encontrado:** {p_data.get('encontrado', '—')}")
                    widget_revisao(f"parte_{chave_p}", nome, revisoes)

        # Tab Extras
        with tab_extras:
            extras = resultado.get("clausulas_extras", [])
            faltantes = resultado.get("clausulas_faltantes", [])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"### 🟣 Cláusulas Extras ({len(extras)})")
                for i, e in enumerate(extras):
                    with st.expander(f"🟣 {e[:60]}..."):
                        st.write(e)
                        widget_revisao(f"extra_{i}", e, revisoes)
                if not extras:
                    st.success("Nenhuma cláusula extra.")
            with c2:
                st.markdown(f"### ⛔ Cláusulas Faltantes ({len(faltantes)})")
                for i, f_item in enumerate(faltantes):
                    with st.expander(f"⛔ {f_item[:60]}..."):
                        st.write(f_item)
                        widget_revisao(f"faltante_{i}", f_item, revisoes)
                if not faltantes:
                    st.success("Nenhuma cláusula faltante.")

        # Export
        st.markdown("---")
        st.markdown("### 📥 Exportar Relatório")
        if revisoes:
            st.caption(f"📋 {len(revisoes)} decisão(ões) do analista registrada(s)")
        c1, c2 = st.columns(2)
        with c1:
            docx_bytes = gerar_relatorio_docx(resultado, revisoes)
            nome_arquivo = f"Analise_Juridica_{resultado.get('municipio', 'contrato')}_{resultado.get('numero_contrato', '')}.docx"
            st.download_button("⬇️ Download DOCX", docx_bytes, nome_arquivo,
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with c2:
            html_str = gerar_relatorio_html(resultado, "minuta", revisoes)
            nome_html = nome_arquivo.replace(".docx", ".html")
            st.download_button("⬇️ Download HTML", html_str, nome_html, "text/html", use_container_width=True)


# =============================================================================
# MODO 2: TERMOS ADITIVOS
# =============================================================================
else:
    st.markdown('<div class="main-title">📑 Análise de Termos Aditivos</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Compare contrato original, termos anteriores e novo termo aditivo</div>', unsafe_allow_html=True)

    col_orig, col_novo = st.columns(2)

    with col_orig:
        st.markdown("#### 📄 Contrato Original")
        file_original = st.file_uploader("Contrato Original", type=["pdf", "docx", "doc"], key="up_original", label_visibility="collapsed")

    with col_novo:
        st.markdown("#### 🆕 Novo Termo Aditivo")
        file_novo = st.file_uploader("Novo Termo Aditivo", type=["pdf", "docx", "doc"], key="up_novo", label_visibility="collapsed")

    # --- TERMOS ANTERIORES SEQUENCIAIS ---
    st.markdown("---")
    st.markdown("#### 📑 Termos Aditivos Anteriores")

    tem_anteriores = st.checkbox("Existem termos aditivos anteriores?", key="tem_anteriores")

    if tem_anteriores:
        if st.session_state.num_termos_anteriores == 0:
            st.session_state.num_termos_anteriores = 1

        for i in range(st.session_state.num_termos_anteriores):
            st.markdown(f"**{i+1}º Termo Aditivo Anterior**")
            f = st.file_uploader(
                f"{i+1}º Termo Aditivo",
                type=["pdf", "docx", "doc"],
                key=f"up_anterior_{i}",
                label_visibility="collapsed",
            )
            if f:
                st.caption(f"✅ {f.name}")

        if st.session_state.num_termos_anteriores < 10:
            if st.button(f"➕ Adicionar {st.session_state.num_termos_anteriores + 1}º Termo Aditivo Anterior", use_container_width=True):
                st.session_state.num_termos_anteriores += 1
                st.rerun()
    else:
        st.session_state.num_termos_anteriores = 0
        st.info("📌 Nenhum termo anterior — a análise comparará diretamente o contrato original com o novo termo.")

    # --- BOTÃO ANALISAR ---
    st.markdown("---")

    pode_analisar = file_original and file_novo and groq_api_key

    if st.button("🔍 Analisar Termos Aditivos", type="primary", use_container_width=True, disabled=not pode_analisar):
        try:
            with st.spinner("📄 Extraindo textos dos documentos..."):
                texto_orig = extrair_texto(file_original.read(), file_original.name)
                texto_novo = extrair_texto(file_novo.read(), file_novo.name)

                termos_ant = []
                for i in range(st.session_state.num_termos_anteriores):
                    f = st.session_state.get(f"up_anterior_{i}")
                    if f:
                        termos_ant.append(extrair_texto(f.read(), f.name))

            with st.spinner("⚖️ Analisando divergências com IA (até 3 tentativas automáticas)..."):
                resultado = analisar_termos_aditivos(texto_orig, termos_ant, texto_novo, groq_api_key, modelo)
                st.session_state.resultado = resultado
                st.session_state._resultado_modo = "aditivos"
                st.session_state.revisoes = {}
        except ErroAnalise as e:
                st.error(f"❌ {e.tipo.value}: {str(e)}")
                st.info(e.mensagem_usuario())
        except Exception as e:
                st.error(f"❌ Erro inesperado: {e}")
                st.info("💡 Tente trocar o modelo LLM na barra lateral ou analisar novamente.")

    if not pode_analisar and not groq_api_key:
        st.warning("⚠️ Configure a chave API Groq na barra lateral.")

    # --- EXIBIR RESULTADO TERMOS ADITIVOS ---
    resultado = st.session_state.resultado
    if resultado and st.session_state.get("_resultado_modo") == "aditivos" and ("divergencias" in resultado or "mapeamento_clausulas" in resultado):
        revisoes = st.session_state.revisoes
        status = resultado.get("status_geral", "—")
        cor = classificar_cor_status(status)
        st.markdown(f'<div class="status-badge" style="background:{cor}">{status}</div>', unsafe_allow_html=True)

        # Métricas
        divs = resultado.get("divergencias", [])
        criticas = sum(1 for d in divs if d.get("tipo") == "DIVERGÊNCIA CRÍTICA")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Divergências Críticas", criticas)
        c2.metric("Divergências", sum(1 for d in divs if d.get("tipo") == "DIVERGÊNCIA"))
        c3.metric("Alertas", sum(1 for d in divs if d.get("tipo") == "ALERTA"))
        c4.metric("Prazos Alterados", sum(1 for p in resultado.get("prazos", []) if p.get("status") not in ("OK", "NÃO LOCALIZADO")))

        st.info(resultado.get("resumo_executivo", ""))

        tab_clausulas, tab_apon, tab_prazos, tab_valores, tab_datas, tab_partes, tab_extras = st.tabs(
            ["📖 Cláusulas", "🚨 Apontamentos", "📅 Prazos", "💰 Valores", "📆 Datas", "👥 Partes", "📌 Extras/Faltantes"])

        # Tab Cláusulas
        with tab_clausulas:
            mapeamento = resultado.get("mapeamento_clausulas", [])
            if mapeamento:
                for i, cl in enumerate(mapeamento):
                    s = cl.get("status", "—")
                    icon = status_icon(s)
                    with st.expander(f"{icon} {cl.get('clausula', f'Cláusula {i+1}')} — **{s}**"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown("**📄 Original:**")
                            st.write(cl.get("resumo_original", "—"))
                        with c2:
                            st.markdown("**📑 Anteriores:**")
                            st.write(cl.get("resumo_anteriores", "N/A"))
                        with c3:
                            st.markdown("**🆕 Novo Termo:**")
                            st.write(cl.get("resumo_novo_termo", "—"))
                        if cl.get("observacao"):
                            st.caption(f"📝 {cl['observacao']}")
                        widget_revisao(f"clausula_ad_{i}", cl.get("clausula", f"Cláusula {i+1}"), revisoes)
            else:
                st.info("O mapeamento cláusula a cláusula não foi retornado pela IA.")

        # Tab Apontamentos
        with tab_apon:
            if not divs:
                st.success("✅ Nenhuma divergência encontrada.")
            for i, ap in enumerate(divs):
                icon = classificar_icon_apontamento(ap.get("tipo", ""))
                with st.expander(f"{icon} [{ap.get('tipo', '')}] {ap.get('clausula', '')} — {ap.get('descricao', '')[:60]}..."):
                    st.markdown(f"**Descrição:** {ap.get('descricao', '—')}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"🟢 **Previsto:** {ap.get('previsto', '—')}")
                    with c2:
                        st.markdown(f"🟠 **Encontrado:** {ap.get('encontrado', '—')}")
                    evidencia = ap.get("evidencia_textual", "")
                    if evidencia:
                        st.markdown(f'<div class="evidencia-box">📎 <b>Trecho-fonte:</b> "{evidencia}"</div>', unsafe_allow_html=True)
                    widget_revisao(f"apontamento_{i}", ap.get("clausula", f"Apontamento {i+1}"), revisoes)

        # Tab Prazos
        with tab_prazos:
            prazos = resultado.get("prazos", [])
            if not prazos:
                st.info("Nenhum prazo identificado.")
            for i, p_item in enumerate(prazos):
                s = p_item.get("status", "—")
                icon = status_icon(s)
                with st.expander(f"{icon} {p_item.get('item', f'Prazo {i+1}')} — **{s}**"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Original:** {p_item.get('contrato_original', '—')}")
                    c2.write(f"**Anteriores:** {p_item.get('termos_anteriores', '—')}")
                    c3.write(f"**Novo Termo:** {p_item.get('novo_termo', '—')}")
                    widget_revisao(f"prazo_ad_{i}", p_item.get("item", f"Prazo {i+1}"), revisoes)

        # Tab Valores
        with tab_valores:
            valores = resultado.get("valores", [])
            if not valores:
                st.info("Nenhum valor identificado.")
            for i, v in enumerate(valores):
                s = v.get("status", "—")
                icon = status_icon(s)
                with st.expander(f"{icon} {v.get('item', f'Valor {i+1}')} — **{s}**"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Original:** {v.get('contrato_original', '—')}")
                    c2.write(f"**Anteriores:** {v.get('termos_anteriores', '—')}")
                    c3.write(f"**Novo Termo:** {v.get('novo_termo', '—')}")
                    widget_revisao(f"valor_ad_{i}", v.get("item", f"Valor {i+1}"), revisoes)

        # Tab Datas
        with tab_datas:
            datas = resultado.get("datas", [])
            if not datas:
                st.info("Nenhuma data identificada.")
            for i, d in enumerate(datas):
                s = d.get("status", "—")
                icon = status_icon(s)
                with st.expander(f"{icon} {d.get('item', f'Data {i+1}')} — **{s}**"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Original:** {d.get('contrato_original', '—')}")
                    c2.write(f"**Anteriores:** {d.get('termos_anteriores', '—')}")
                    c3.write(f"**Novo Termo:** {d.get('novo_termo', '—')}")
                    widget_revisao(f"data_ad_{i}", d.get("item", f"Data {i+1}"), revisoes)

        # Tab Partes
        with tab_partes:
            partes = resultado.get("partes", {})
            if partes.get("contratante"):
                st.markdown(f"**Contratante:** {partes['contratante']}")
            if partes.get("contratada"):
                st.markdown(f"**Contratada:** {partes['contratada']}")
            for o in partes.get("outros", []):
                st.markdown(f"**Outro:** {o}")

            assinantes = resultado.get("assinantes_novo_termo", [])
            if assinantes:
                st.markdown("#### Assinantes do Novo Termo")
                for i, a in enumerate(assinantes):
                    pres = "✅ SIM" if a.get("presente_em_anteriores") else "❌ NÃO"
                    with st.expander(f"{a.get('nome', '—')} — {a.get('cargo', '—')} | Presente antes: {pres}"):
                        st.write(f"**Observação:** {a.get('observacao', '—')}")
                        widget_revisao(f"assinante_{i}", a.get("nome", f"Assinante {i+1}"), revisoes)

        # Tab Extras
        with tab_extras:
            extras = resultado.get("clausulas_extras", [])
            faltantes = resultado.get("clausulas_faltantes", [])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"### 🟣 Cláusulas Extras ({len(extras)})")
                for i, e in enumerate(extras):
                    with st.expander(f"🟣 {e[:60]}..."):
                        st.write(e)
                        widget_revisao(f"extra_ad_{i}", e, revisoes)
                if not extras:
                    st.success("Nenhuma extra.")
            with c2:
                st.markdown(f"### ⛔ Cláusulas Faltantes ({len(faltantes)})")
                for i, f_item in enumerate(faltantes):
                    with st.expander(f"⛔ {f_item[:60]}..."):
                        st.write(f_item)
                        widget_revisao(f"faltante_ad_{i}", f_item, revisoes)
                if not faltantes:
                    st.success("Nenhuma faltante.")

        # Export
        st.markdown("---")
        st.markdown("### 📥 Exportar Relatório")
        if revisoes:
            st.caption(f"📋 {len(revisoes)} decisão(ões) do analista registrada(s)")
        c1, c2 = st.columns(2)
        with c1:
            docx_bytes = gerar_relatorio_aditivos_docx(resultado, revisoes)
            nome_arq = f"Relatorio_Termos_Aditivos_{resultado.get('numero_contrato', 'contrato')}.docx"
            st.download_button("⬇️ Download DOCX", docx_bytes, nome_arq,
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with c2:
            html_str = gerar_relatorio_html(resultado, "aditivos", revisoes)
            nome_html = nome_arq.replace(".docx", ".html")
            st.download_button("⬇️ Download HTML", html_str, nome_html, "text/html", use_container_width=True)
