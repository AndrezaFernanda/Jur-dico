"""
Extração de texto de PDF (nativo + OCR paralelo) e DOCX.

Melhorias aplicadas:
  - OCR paralelo com ThreadPoolExecutor (PDFs escaneados)
  - @st.cache_data para evitar re-processamento do mesmo arquivo
  - Extração híbrida: páginas com texto nativo + OCR apenas nas sem texto
"""
import io
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
import pdfplumber
from docx import Document as DocxDocument

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    OCR_DISPONIVEL = True
except ImportError:
    OCR_DISPONIVEL = False


@st.cache_data(show_spinner=False)
def extrair_texto(arquivo_bytes: bytes, nome_arquivo: str) -> str:
    """Extrai texto de PDF ou DOCX. Resultado cacheado por conteudo do arquivo."""
    nome = nome_arquivo.lower()
    if nome.endswith(".pdf"):
        return extrair_texto_pdf(arquivo_bytes)
    elif nome.endswith((".docx", ".doc")):
        return extrair_texto_docx(arquivo_bytes)
    else:
        raise ValueError(f"Formato nao suportado: {nome_arquivo}")


def extrair_texto_pdf(arquivo_bytes: bytes) -> str:
    """
    Extracao hibrida:
    1. Tenta texto nativo (pdfplumber) por pagina
    2. Paginas sem texto -> OCR individual (paralelo)
    3. Combina tudo na ordem correta
    """
    textos_por_pagina = []
    paginas_sem_texto = []

    with pdfplumber.open(io.BytesIO(arquivo_bytes)) as pdf:
        for i, pagina in enumerate(pdf.pages):
            t = pagina.extract_text()
            if t and len(t.strip()) > 30:
                textos_por_pagina.append((i, t))
            else:
                textos_por_pagina.append((i, None))
                paginas_sem_texto.append(i)

    # Se todas as paginas tem texto nativo, retorna direto
    if not paginas_sem_texto:
        texto_final = "\n".join(t for _, t in textos_por_pagina if t)
        if len(texto_final.strip()) > 100:
            return texto_final.strip()

    # OCR nas paginas que faltam (paralelo)
    if paginas_sem_texto and OCR_DISPONIVEL:
        imagens = convert_from_bytes(arquivo_bytes, dpi=300)
        imagens_para_ocr = [(idx, imagens[idx]) for idx in paginas_sem_texto if idx < len(imagens)]

        def _ocr_pagina(item):
            idx, img = item
            return idx, pytesseract.image_to_string(img, lang="por")

        with ThreadPoolExecutor(max_workers=4) as executor:
            resultados_ocr = dict(executor.map(_ocr_pagina, imagens_para_ocr))

        for i, (idx, texto) in enumerate(textos_por_pagina):
            if texto is None and idx in resultados_ocr:
                textos_por_pagina[i] = (idx, resultados_ocr[idx])

    texto_final = "\n".join(t for _, t in textos_por_pagina if t)

    if len(texto_final.strip()) < 100:
        if OCR_DISPONIVEL:
            return _ocr_completo(arquivo_bytes)
        return (
            "[AVISO] PDF escaneado detectado mas Tesseract OCR nao esta disponivel. "
            "Instale pytesseract + tesseract-ocr para processar este arquivo."
        )

    return texto_final.strip()


def _ocr_completo(arquivo_bytes: bytes) -> str:
    """OCR completo paralelo em todas as paginas (fallback)."""
    imagens = convert_from_bytes(arquivo_bytes, dpi=300)

    def _processar(img):
        return pytesseract.image_to_string(img, lang="por")

    with ThreadPoolExecutor(max_workers=4) as executor:
        textos = list(executor.map(_processar, imagens))

    return "\n".join(textos).strip()


def extrair_texto_docx(arquivo_bytes: bytes) -> str:
    doc = DocxDocument(io.BytesIO(arquivo_bytes))
    paragrafos = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragrafos)
