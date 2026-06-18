from pathlib import Path

import pandas as pd
import streamlit as st

from src.calculos import CRITERIO_REFERENCIA_PADRAO
from src.calculos_manuais import (
    ALIQUOTAS_ICMS_SUGERIDAS,
    ALIQUOTAS_PIS_COFINS_SUGERIDAS,
    CalculoManualInvalido,
    calcular_icms_reducao_manual,
    calcular_ipi_manual,
    calcular_pis_cofins_manual,
    calcular_reducao_por_valor_icms,
)
from src.nfe_parser import parsear_varios_xmls
from src.simulador_desmembramento import simular_desmembramento

BASE_DIR = Path(__file__).resolve().parent
SIMBOLO_SITE_PATH = BASE_DIR / "assets" / "simbolo_site.png"
PAGE_ICON = str(SIMBOLO_SITE_PATH) if SIMBOLO_SITE_PATH.exists() else "🧾"

st.set_page_config(
    page_title="Calculadora Fiscal",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


USUARIOS = {
    "admin": "112211bb",
    "guilherme": "112211bb",
}


MENU_PAGINAS = [
    "Dashboard",
    "Resultado XML",
    "Simulador",
    "Cálculos Manuais",
    "Fórmulas",
]


CRITERIOS_PREDBC = {
    "Valor da operação": "valor_operacao",
    "Quantidade x unitário + vOutro": "quantidade_unitario",
    "Somente vProd": "somente_vprod",
}


CRITERIO_PREDBC_PADRAO_LABEL = "Valor da operação"


def aplicar_css_global():
    st.markdown(
        """
        <style>
            :root {
                --bg-main: #F4F7FB;
                --sidebar-start: #050A1A;
                --sidebar-end: #0F1E45;
                --card: #FFFFFF;
                --card-soft: #F7F9FC;
                --text-main: #1F2937;
                --text-muted: #6B7280;
                --border: #E5E7EB;
                --primary: #2563EB;
                --success: #22C55E;
                --warning: #F59E0B;
                --danger: #EF4444;
            }

            .stApp {
                background: var(--bg-main);
            }

            .block-container {
                padding-top: 3.10rem;
                padding-bottom: 2rem;
                max-width: 1500px;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%);
                border-right: 1px solid rgba(255,255,255,0.08);
            }

            [data-testid="stSidebar"] * {
                color: rgba(255,255,255,0.92);
            }

            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stCaptionContainer,
            [data-testid="stSidebar"] small {
                color: rgba(255,255,255,0.68) !important;
            }

            [data-testid="stSidebar"] hr {
                border-color: rgba(255,255,255,0.12);
            }

            [data-testid="stSidebar"] div[role="radiogroup"] label {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 14px;
                padding: 0.48rem 0.65rem;
                margin-bottom: 0.35rem;
                transition: 0.16s ease;
            }

            [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
                background: rgba(255,255,255,0.12);
                border-color: rgba(255,255,255,0.18);
            }

            [data-testid="stSidebar"] .stButton > button {
                width: 100%;
                border-radius: 12px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                color: #FFFFFF;
            }

            [data-testid="stSidebar"] .stButton > button:hover {
                background: rgba(255,255,255,0.14);
                border-color: rgba(255,255,255,0.22);
                color: #FFFFFF;
            }

            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
                background: rgba(255,255,255,0.07);
                border: 1px dashed rgba(255,255,255,0.32);
                border-radius: 16px;
                padding: 0.9rem 0.75rem;
            }

            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
                background: rgba(255,255,255,0.14) !important;
                border: 1px solid rgba(255,255,255,0.22) !important;
                border-radius: 10px !important;
                color: #FFFFFF !important;
                font-weight: 700 !important;
            }

            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button * {
                color: #FFFFFF !important;
            }

            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span,
            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p {
                color: rgba(255,255,255,0.82) !important;
            }

            /*
             * Arquivo XML selecionado no uploader da sidebar.
             * A correção fica em duas camadas:
             * 1) quando o Streamlit expõe data-testid do arquivo, usamos o card escuro;
             * 2) quando a versão renderiza apenas o chip padrão claro, forçamos texto escuro.
             */
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stUploadedFile"],
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has([data-testid="stFileUploaderFileData"]),
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has([data-testid="stFileUploaderFileName"]),
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="Remove"]),
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="remover"]),
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="Remover"]),
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="Delete"]),
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="Excluir"]) {
                background-color: #111827 !important;
                border-color: rgba(255,255,255,0.22) !important;
                color: #F8FAFC !important;
                opacity: 1 !important;
                box-shadow: none !important;
            }

            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] *,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stUploadedFile"] *,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFileData"] *,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"],
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFileSize"],
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="Remove"]) *,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="remover"]) *,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="Remover"]) *,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="Delete"]) *,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has(button[aria-label*="Excluir"]) * {
                color: #F8FAFC !important;
                fill: #F8FAFC !important;
                opacity: 1 !important;
                text-shadow: none !important;
            }

            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] svg,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] svg path,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] svg,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] svg path {
                fill: #F8FAFC !important;
                color: #F8FAFC !important;
                opacity: 1 !important;
            }

            /*
             * Fallback para o chip claro padrão que aparece em algumas versões.
             * Nessa situação mantemos o fundo claro, mas forçamos o texto para escuro.
             */
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [title$=".xml"],
            [data-testid="stSidebar"] [data-testid="stFileUploader"] [title$=".XML"],
            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] [title$=".xml"],
            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] [title$=".XML"] {
                color: #0F172A !important;
                fill: #0F172A !important;
                opacity: 1 !important;
                font-weight: 800 !important;
                text-shadow: none !important;
            }

            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has([title$=".xml"]) *,
            [data-testid="stSidebar"] [data-testid="stFileUploader"] div:has([title$=".XML"]) *,
            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] div:has([title$=".xml"]) *,
            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] div:has([title$=".XML"]) * {
                opacity: 1 !important;
                text-shadow: none !important;
            }

            [data-testid="stSidebar"] [data-baseweb="select"] > div {
                background: #202A46 !important;
                border: 1px solid rgba(255,255,255,0.18) !important;
                border-radius: 10px !important;
                color: #FFFFFF !important;
                box-shadow: none !important;
            }

            [data-testid="stSidebar"] [data-baseweb="select"] input,
            [data-testid="stSidebar"] [data-baseweb="select"] textarea,
            [data-testid="stSidebar"] [data-baseweb="select"] [contenteditable="true"] {
                background: transparent !important;
                color: #FFFFFF !important;
                box-shadow: none !important;
            }

            [data-testid="stSidebar"] [data-baseweb="select"] span,
            [data-testid="stSidebar"] [data-baseweb="select"] div {
                color: rgba(255,255,255,0.92) !important;
            }

            [data-testid="stSidebar"] [data-baseweb="select"] svg {
                fill: rgba(255,255,255,0.80) !important;
                color: rgba(255,255,255,0.80) !important;
            }

            [data-testid="stSidebar"] input:not([aria-autocomplete="list"]) {
                background: #202A46 !important;
                border-color: rgba(255,255,255,0.18) !important;
                color: #FFFFFF !important;
            }

            .sidebar-brand {
                padding: 0.35rem 0.1rem 0.75rem 0.1rem;
            }

            .sidebar-title {
                font-size: 1.25rem;
                font-weight: 800;
                letter-spacing: -0.03em;
                color: #FFFFFF;
                margin-bottom: 0.2rem;
            }

            .sidebar-subtitle {
                font-size: 0.78rem;
                color: rgba(255,255,255,0.62);
                line-height: 1.35;
            }

            .hero-card {
                background: linear-gradient(135deg, #0B122A 0%, #0F1E45 52%, #163A75 100%);
                color: #FFFFFF;
                padding: 1.55rem 1.55rem 1.45rem 1.55rem;
                border-radius: 24px;
                border: 1px solid rgba(255,255,255,0.12);
                box-shadow: 0 16px 42px rgba(11,18,42,0.18);
                margin-top: 0.35rem;
                margin-bottom: 1.1rem;
            }

            .hero-eyebrow {
                color: rgba(255,255,255,0.66);
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 700;
                margin-bottom: 0.35rem;
            }

            .hero-title {
                font-size: 2rem;
                line-height: 1.1;
                font-weight: 850;
                letter-spacing: -0.04em;
                margin-bottom: 0.4rem;
            }

            .hero-text {
                color: rgba(255,255,255,0.72);
                font-size: 0.98rem;
                max-width: 880px;
            }


            .login-form-spacer {
                height: 8rem;
            }

            @media (max-height: 820px) {
                .login-form-spacer {
                    height: 5.5rem;
                }
            }

            .metric-card {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 20px;
                padding: 1rem 1.05rem;
                box-shadow: 0 10px 28px rgba(15,30,69,0.06);
                min-height: 112px;
            }

            .metric-label {
                color: var(--text-muted);
                font-size: 0.78rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                margin-bottom: 0.25rem;
            }

            .metric-value {
                color: var(--text-main);
                font-size: 1.75rem;
                font-weight: 850;
                letter-spacing: -0.04em;
            }

            .metric-help {
                color: var(--text-muted);
                font-size: 0.80rem;
                margin-top: 0.25rem;
            }

            .section-card {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 1.1rem 1.2rem;
                box-shadow: 0 10px 28px rgba(15,30,69,0.05);
                margin-bottom: 1rem;
            }

            .section-title {
                color: var(--text-main);
                font-size: 1.25rem;
                font-weight: 800;
                letter-spacing: -0.03em;
                margin-bottom: 0.2rem;
            }

            .section-subtitle {
                color: var(--text-muted);
                font-size: 0.9rem;
                margin-bottom: 0.8rem;
            }

            .pill-row {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
                margin-top: 0.75rem;
            }

            .pill {
                background: #EEF2FF;
                color: #1E3A8A;
                border: 1px solid #DBEAFE;
                border-radius: 999px;
                padding: 0.32rem 0.62rem;
                font-size: 0.78rem;
                font-weight: 700;
            }

            .status-ok {
                color: #166534;
                background: #DCFCE7;
                border: 1px solid #BBF7D0;
                padding: 0.2rem 0.45rem;
                border-radius: 999px;
                font-weight: 700;
                font-size: 0.78rem;
            }

            .status-alerta {
                color: #92400E;
                background: #FEF3C7;
                border: 1px solid #FDE68A;
                padding: 0.2rem 0.45rem;
                border-radius: 999px;
                font-weight: 700;
                font-size: 0.78rem;
            }

            .empty-state {
                background: #FFFFFF;
                border: 1px dashed #CBD5E1;
                border-radius: 24px;
                padding: 2rem;
                text-align: center;
                color: #475569;
                box-shadow: 0 10px 28px rgba(15,30,69,0.04);
            }

            .empty-title {
                font-size: 1.35rem;
                font-weight: 850;
                color: #1F2937;
                margin-bottom: 0.4rem;
            }

            div[data-testid="stDataFrame"] {
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid var(--border);
                box-shadow: 0 10px 24px rgba(15,30,69,0.04);
            }

            .stButton > button[kind="primary"] {
                border-radius: 14px;
                font-weight: 800;
                box-shadow: 0 10px 22px rgba(37,99,235,0.24);
            }

            .stDownloadButton > button {
                border-radius: 14px;
                font-weight: 700;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_sidebar():
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-title">Calculadora XML</div>
            <div class="sidebar-subtitle">
                Auditoria visual de ICMS, PIS/COFINS e desmembramento proporcional.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topo(titulo: str, subtitulo: str):
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-eyebrow">Análise fiscal de NF-e</div>
            <div class="hero-title">{titulo}</div>
            <div class="hero-text">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, valor: str, ajuda: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{valor}</div>
            <div class="metric-help">{ajuda}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(titulo: str, subtitulo: str = ""):
    st.markdown(
        f"""
        <div class="section-title">{titulo}</div>
        <div class="section-subtitle">{subtitulo}</div>
        """,
        unsafe_allow_html=True,
    )


def tela_login():
    """
    Tela simples de login com usuário e senha.
    Mantém o usuário logado usando st.session_state.
    """
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None

    if st.session_state.autenticado:
        with st.sidebar:
            st.success(f"Logado como: {st.session_state.usuario_logado}")
            if st.button("Sair"):
                st.session_state.autenticado = False
                st.session_state.usuario_logado = None
                st.rerun()
        return True

    render_topo(
        "Acesso ao sistema",
        "Informe usuário e senha para acessar a calculadora fiscal.",
    )

    st.markdown('<div class="login-form-spacer"></div>', unsafe_allow_html=True)

    col_esq, col_centro, col_dir = st.columns([1, 1.15, 1])

    with col_centro:
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button(
                "Entrar", type="primary", width="stretch"
            )

        if entrar:
            usuario = usuario.strip()
            if usuario in USUARIOS and senha == USUARIOS[usuario]:
                st.session_state.autenticado = True
                st.session_state.usuario_logado = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

    return False


def valor_float(valor, padrao=0.0):
    try:
        if valor is None:
            return padrao

        valor_texto = str(valor).replace(",", ".").strip()

        if valor_texto == "" or valor_texto.lower() == "nan":
            return padrao

        return float(valor_texto)
    except Exception:
        return padrao


def formatar_numero(valor, casas=2):
    try:
        if pd.isna(valor):
            return "0,00"
        return (
            f"{float(valor):,.{casas}f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    except Exception:
        return "0,00"


def montar_descricao_produto(linha):
    nf = linha.get("Número NF", "")
    item = linha.get("Número item", "")
    codigo = linha.get("Código produto XML", "")
    descricao = linha.get("Descrição produto", "")
    qtd = linha.get("qTrib", "")

    return f"NF {nf} | Item {item} | Cód. {codigo} | Qtd: {qtd} | {descricao}"


def config_colunas_resultado_xml():
    return {
        "qTrib": st.column_config.NumberColumn("qTrib", format="%.4f"),
        "vUnTrib": st.column_config.NumberColumn("vUnTrib", format="%.6f"),
        "Valor produto": st.column_config.NumberColumn("Valor produto", format="%.2f"),
        "vProd": st.column_config.NumberColumn("vProd", format="%.2f"),
        "vFrete": st.column_config.NumberColumn("vFrete", format="%.2f"),
        "vSeg": st.column_config.NumberColumn("vSeg", format="%.2f"),
        "vDesc": st.column_config.NumberColumn("vDesc", format="%.2f"),
        "vOutro": st.column_config.NumberColumn("vOutro", format="%.2f"),
        "Valor referência ICMS": st.column_config.NumberColumn(
            "Valor referência ICMS",
            format="%.2f",
        ),
        "Critério referência ICMS": st.column_config.TextColumn(
            "Critério referência ICMS"
        ),
        "vBC": st.column_config.NumberColumn("vBC", format="%.2f"),
        "pICMS": st.column_config.NumberColumn("pICMS", format="%.2f"),
        "vICMS": st.column_config.NumberColumn("vICMS", format="%.2f"),
        "Base PIS XML": st.column_config.NumberColumn("Base PIS XML", format="%.2f"),
        "Alíquota PIS XML": st.column_config.NumberColumn(
            "Alíquota PIS XML",
            format="%.2f",
        ),
        "Valor PIS XML": st.column_config.NumberColumn("Valor PIS XML", format="%.2f"),
        "Base COFINS XML": st.column_config.NumberColumn(
            "Base COFINS XML",
            format="%.2f",
        ),
        "Alíquota COFINS XML": st.column_config.NumberColumn(
            "Alíquota COFINS XML",
            format="%.2f",
        ),
        "Valor COFINS XML": st.column_config.NumberColumn(
            "Valor COFINS XML",
            format="%.2f",
        ),
        "Base PIS/COFINS calculada": st.column_config.NumberColumn(
            "Base PIS/COFINS calculada",
            format="%.2f",
        ),
        "pRedBC XML": st.column_config.NumberColumn("pRedBC XML", format="%.4f"),
        "pRedBC calculado": st.column_config.NumberColumn(
            "pRedBC calculado",
            format="%.4f",
        ),
        "Diferença pRedBC": st.column_config.NumberColumn(
            "Diferença pRedBC",
            format="%.4f",
        ),
    }


def config_colunas_simulador():
    return {
        "Quantidade": st.column_config.NumberColumn("Quantidade", format="%.4f"),
        "vUnTrib": st.column_config.NumberColumn("vUnTrib", format="%.6f"),
        "Valor produto": st.column_config.NumberColumn("Valor produto", format="%.2f"),
        "vProd proporcional": st.column_config.NumberColumn(
            "vProd proporcional",
            format="%.2f",
        ),
        "vFrete proporcional": st.column_config.NumberColumn(
            "vFrete proporcional",
            format="%.2f",
        ),
        "vSeg proporcional": st.column_config.NumberColumn(
            "vSeg proporcional",
            format="%.2f",
        ),
        "vDesc proporcional": st.column_config.NumberColumn(
            "vDesc proporcional",
            format="%.2f",
        ),
        "vOutro proporcional": st.column_config.NumberColumn(
            "vOutro proporcional",
            format="%.2f",
        ),
        "Valor referência ICMS": st.column_config.NumberColumn(
            "Valor referência ICMS",
            format="%.2f",
        ),
        "Critério referência ICMS": st.column_config.TextColumn(
            "Critério referência ICMS"
        ),
        "vBC": st.column_config.NumberColumn("vBC", format="%.2f"),
        "pICMS": st.column_config.NumberColumn("pICMS", format="%.2f"),
        "vICMS": st.column_config.NumberColumn("vICMS", format="%.2f"),
        "Base PIS/COFINS calculada": st.column_config.NumberColumn(
            "Base PIS/COFINS calculada",
            format="%.2f",
        ),
        "Base PIS XML proporcional": st.column_config.NumberColumn(
            "Base PIS XML proporcional",
            format="%.2f",
        ),
        "Alíquota PIS XML": st.column_config.NumberColumn(
            "Alíquota PIS XML",
            format="%.2f",
        ),
        "Valor PIS XML proporcional": st.column_config.NumberColumn(
            "Valor PIS XML proporcional",
            format="%.2f",
        ),
        "Base COFINS XML proporcional": st.column_config.NumberColumn(
            "Base COFINS XML proporcional",
            format="%.2f",
        ),
        "Alíquota COFINS XML": st.column_config.NumberColumn(
            "Alíquota COFINS XML",
            format="%.2f",
        ),
        "Valor COFINS XML proporcional": st.column_config.NumberColumn(
            "Valor COFINS XML proporcional",
            format="%.2f",
        ),
        "pRedBC XML": st.column_config.NumberColumn("pRedBC XML", format="%.4f"),
        "pRedBC calculado": st.column_config.NumberColumn(
            "pRedBC calculado",
            format="%.4f",
        ),
    }


def preparar_dataframe(linhas):
    df = pd.DataFrame(linhas)

    colunas_numericas = [
        "qTrib",
        "vUnTrib",
        "Valor produto",
        "vProd",
        "vFrete",
        "vSeg",
        "vDesc",
        "vOutro",
        "Valor referência ICMS",
        "vBC",
        "pICMS",
        "vICMS",
        "pRedBC XML",
        "pRedBC calculado",
    ]

    for coluna in colunas_numericas:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    if "pRedBC XML" in df.columns and "pRedBC calculado" in df.columns:
        df["Diferença pRedBC"] = df["pRedBC calculado"] - df["pRedBC XML"]
        df["Situação pRedBC"] = df.apply(classificar_predbc, axis=1)

    return df


def classificar_predbc(linha, tolerancia=0.05):
    xml = linha.get("pRedBC XML")
    calculado = linha.get("pRedBC calculado")

    if pd.isna(xml) and pd.isna(calculado):
        return "Sem pRedBC"

    if pd.isna(xml):
        return "Sem pRedBC XML"

    if pd.isna(calculado):
        return "Sem cálculo"

    diferenca = calculado - xml

    if abs(diferenca) <= tolerancia:
        return "OK"

    if diferenca > 0:
        return "Calculado maior"

    return "Calculado menor"


def opcoes_unicas(df, coluna):
    if coluna not in df.columns:
        return []

    valores = df[coluna].dropna().astype(str)
    valores = valores[valores.str.strip() != ""]
    return sorted(valores.unique().tolist())


def aplicar_filtros(df, filtros):
    df_filtrado = df.copy()

    for coluna, valores in filtros.items():
        if valores and coluna in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).isin(valores)]

    return df_filtrado.reset_index(drop=True)


def render_sidebar_inicio():
    with st.sidebar:
        render_brand_sidebar()
        st.divider()

        pagina = st.radio(
            "Navegação",
            MENU_PAGINAS,
            index=0,
            label_visibility="collapsed",
            key="pagina_navegacao",
        )

        st.divider()
        st.caption("Arquivos XML")
        arquivos_xml = st.file_uploader(
            "Selecione um ou vários XMLs de NF-e",
            type=["xml"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="uploader_xml_nfe",
        )

        st.divider()
        st.caption("Cálculo ICMS")
        criterio_label = st.selectbox(
            "Critério do pRedBC",
            options=list(CRITERIOS_PREDBC.keys()),
            index=list(CRITERIOS_PREDBC.keys()).index(CRITERIO_PREDBC_PADRAO_LABEL),
            key="criterio_predbc",
        )
        criterio_referencia_icms = CRITERIOS_PREDBC.get(
            criterio_label,
            CRITERIO_REFERENCIA_PADRAO,
        )

        return pagina, arquivos_xml, criterio_referencia_icms


def render_sidebar_filtros(df):
    filtros = {}

    if df is None or df.empty:
        return filtros

    with st.sidebar:
        st.divider()
        st.caption("Filtros da análise")

        filtros["Número NF"] = st.multiselect(
            "NF",
            opcoes_unicas(df, "Número NF"),
            placeholder="Todas",
            key="filtro_nf",
        )

        filtros["Nome emitente"] = st.multiselect(
            "Emitente",
            opcoes_unicas(df, "Nome emitente"),
            placeholder="Todos",
            key="filtro_emitente",
        )

        filtros["NCM"] = st.multiselect(
            "NCM",
            opcoes_unicas(df, "NCM"),
            placeholder="Todos",
            key="filtro_ncm",
        )

        filtros["CFOP"] = st.multiselect(
            "CFOP",
            opcoes_unicas(df, "CFOP"),
            placeholder="Todos",
            key="filtro_cfop",
        )

        filtros["CST/CSOSN ICMS"] = st.multiselect(
            "CST/CSOSN ICMS",
            opcoes_unicas(df, "CST/CSOSN ICMS"),
            placeholder="Todos",
            key="filtro_cst_icms",
        )

        if "Situação pRedBC" in df.columns:
            filtros["Situação pRedBC"] = st.multiselect(
                "Situação pRedBC",
                opcoes_unicas(df, "Situação pRedBC"),
                placeholder="Todas",
                key="filtro_situacao_predbc",
            )

    return filtros


def render_estado_inicial():
    render_topo(
        "Calculadora de redução de base ICMS em XML de NF-e",
        "Envie um ou mais XMLs pela barra lateral para iniciar a análise. O painel foi organizado para leitura fiscal rápida, com filtros laterais e navegação por seções.",
    )

    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-title">Nenhum XML enviado</div>
            <div>Use a barra lateral esquerda para selecionar os XMLs de NF-e.</div>
            <div class="pill-row" style="justify-content:center;">
                <span class="pill">Upload múltiplo</span>
                <span class="pill">Filtros laterais</span>
                <span class="pill">Dashboard fiscal</span>
                <span class="pill">Simulador proporcional</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_cards_resumo(df, arquivos_xml):
    total_xmls = len(arquivos_xml)
    total_itens = len(df)
    total_notas = (
        df["Chave de acesso"].nunique() if "Chave de acesso" in df.columns else 0
    )
    itens_com_predbc = (
        int(df["pRedBC XML"].notna().sum()) if "pRedBC XML" in df.columns else 0
    )
    divergentes = 0

    if "Situação pRedBC" in df.columns:
        divergentes = int(
            df["Situação pRedBC"].isin(["Calculado maior", "Calculado menor"]).sum()
        )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("XMLs", str(total_xmls), "Arquivos enviados")
    with col2:
        render_metric_card("Itens", str(total_itens), "Itens lidos no XML")
    with col3:
        render_metric_card("Notas", str(total_notas), "Chaves únicas")
    with col4:
        render_metric_card(
            "Com pRedBC", str(itens_com_predbc), "Itens com redução no XML"
        )
    with col5:
        render_metric_card(
            "Divergentes", str(divergentes), "Diferença acima da tolerância"
        )


def render_dashboard(df, arquivos_xml):
    render_topo(
        "Dashboard da análise XML",
        "Resumo dos arquivos processados, principais totais e distribuição das situações de redução de base.",
    )

    render_cards_resumo(df, arquivos_xml)

    col_esq, col_dir = st.columns([1.15, 1])

    with col_esq:
        render_section_header(
            "Resumo por emitente",
            "Quantidade de notas e itens agrupados pelo fornecedor do XML.",
        )

        if "Nome emitente" in df.columns:
            resumo_emitente = (
                df.groupby(["Nome emitente", "CNPJ emitente"], dropna=False)
                .agg(
                    Notas=("Chave de acesso", "nunique"),
                    Itens=("Número item", "count"),
                    Valor_produto=("Valor produto", "sum"),
                    Base_ICMS=("vBC", "sum"),
                    ICMS=("vICMS", "sum"),
                )
                .reset_index()
                .sort_values(["Itens", "Notas"], ascending=False)
            )

            st.dataframe(
                resumo_emitente,
                width="stretch",
                hide_index=True,
                column_config={
                    "Valor_produto": st.column_config.NumberColumn(
                        "Valor produto", format="%.2f"
                    ),
                    "Base_ICMS": st.column_config.NumberColumn(
                        "Base ICMS", format="%.2f"
                    ),
                    "ICMS": st.column_config.NumberColumn("ICMS", format="%.2f"),
                },
            )
        else:
            st.info("Coluna Nome emitente não encontrada no XML.")

    with col_dir:
        render_section_header(
            "Situação pRedBC",
            "Classificação automática entre XML e cálculo interno.",
        )

        if "Situação pRedBC" in df.columns:
            resumo_situacao = (
                df["Situação pRedBC"]
                .value_counts(dropna=False)
                .rename_axis("Situação")
                .reset_index(name="Quantidade")
            )
            st.dataframe(resumo_situacao, width="stretch", hide_index=True)
        else:
            st.info("Ainda não há coluna de situação pRedBC.")

    render_section_header(
        "Totais fiscais",
        "Somatório dos principais campos monetários extraídos e calculados.",
    )

    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1:
        render_metric_card(
            "Valor produto",
            f"R$ {formatar_numero(df.get('Valor produto', pd.Series(dtype=float)).sum())}",
            "Soma dos produtos",
        )
    with col_t2:
        render_metric_card(
            "Base ICMS",
            f"R$ {formatar_numero(df.get('vBC', pd.Series(dtype=float)).sum())}",
            "Soma de vBC",
        )
    with col_t3:
        render_metric_card(
            "ICMS",
            f"R$ {formatar_numero(df.get('vICMS', pd.Series(dtype=float)).sum())}",
            "Soma de vICMS",
        )
    with col_t4:
        render_metric_card(
            "Base PIS/COFINS",
            f"R$ {formatar_numero(df.get('Base PIS/COFINS calculada', pd.Series(dtype=float)).sum())}",
            "Valor produto - ICMS",
        )


def render_resultado_xml(df):
    render_topo(
        "Resultado XML",
        "Tabela fiscal item a item com campos originais do XML, cálculo do pRedBC e situação da divergência.",
    )

    render_section_header(
        "Itens extraídos do XML",
        "Clique na coluna lateral da tabela para selecionar um item e reaproveitar no simulador.",
    )

    col_acoes1, col_acoes2 = st.columns([1, 4])
    with col_acoes1:
        csv = df.to_csv(index=False, sep=";", encoding="utf-8-sig")
        st.download_button(
            "Baixar CSV",
            data=csv,
            file_name="analise_xml.csv",
            mime="text/csv",
            width="stretch",
        )

    with col_acoes2:
        st.caption(
            "A tabela abaixo respeita os filtros aplicados na barra lateral. "
            "Para voltar à visão completa, limpe os filtros."
        )

    evento_tabela_xml = st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config=config_colunas_resultado_xml(),
        selection_mode="single-row",
        on_select="rerun",
        key="tabela_itens_xml",
    )

    linhas_selecionadas = evento_tabela_xml.selection.rows

    if linhas_selecionadas:
        posicao_linha_selecionada = linhas_selecionadas[0]
        st.session_state["linha_xml_selecionada"] = posicao_linha_selecionada
        item_marcado = df.iloc[posicao_linha_selecionada]
        st.info(
            "Item selecionado: "
            f"NF {item_marcado.get('Número NF', '')} | "
            f"Item {item_marcado.get('Número item', '')} | "
            f"Código {item_marcado.get('Código produto XML', '')} | "
            f"{item_marcado.get('Descrição produto', '')}"
        )


def render_simulador(df, criterio_referencia_icms):
    render_topo(
        "Simulador de desmembramento",
        "Selecione um item da NF-e e informe a quantidade que será desmembrada. O sistema calcula valores proporcionais de ICMS, PIS e COFINS.",
    )

    colunas_obrigatorias = [
        "Número NF",
        "Número item",
        "Código produto XML",
        "Descrição produto",
        "qTrib",
        "vUnTrib",
        "Valor produto",
        "vProd",
        "vFrete",
        "vSeg",
        "vDesc",
        "vOutro",
        "vBC",
        "pICMS",
        "vICMS",
        "Base PIS/COFINS calculada",
        "Base PIS XML",
        "Alíquota PIS XML",
        "Valor PIS XML",
        "Base COFINS XML",
        "Alíquota COFINS XML",
        "Valor COFINS XML",
    ]

    colunas_faltando = [
        coluna for coluna in colunas_obrigatorias if coluna not in df.columns
    ]

    if colunas_faltando:
        st.error(
            "Não foi possível montar o simulador. "
            f"Colunas faltando no resultado do XML: {', '.join(colunas_faltando)}"
        )
        st.stop()

    df_simulador = df.copy()
    df_simulador["Produto para seleção"] = df_simulador.apply(
        montar_descricao_produto,
        axis=1,
    )

    opcoes_simulador = df_simulador.index.tolist()
    indice_padrao_simulador = 0

    if "linha_xml_selecionada" in st.session_state:
        posicao_salva = int(st.session_state["linha_xml_selecionada"])
        if 0 <= posicao_salva < len(opcoes_simulador):
            indice_padrao_simulador = posicao_salva

    render_section_header(
        "Seleção do item",
        "A lista abaixo considera os filtros aplicados na barra lateral.",
    )

    indice_selecionado = st.selectbox(
        "Produto da NF-e",
        options=opcoes_simulador,
        index=indice_padrao_simulador,
        format_func=lambda indice: df_simulador.loc[indice, "Produto para seleção"],
    )

    item_original = df_simulador.loc[indice_selecionado].to_dict()
    quantidade_original = valor_float(item_original.get("qTrib"))

    if quantidade_original <= 0:
        st.error("A quantidade original do item é inválida para simulação.")
        st.stop()

    render_section_header(
        "Dados originais do item", "Principais valores usados na simulação."
    )
    st.caption(
        "Critério de pRedBC em uso: "
        f"{item_original.get('Critério referência ICMS', 'Valor da operação')}"
    )

    col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)

    with col_a:
        render_metric_card("Qtd. original", f"{quantidade_original:.4f}")
    with col_b:
        render_metric_card(
            "vUnTrib", f"{valor_float(item_original.get('vUnTrib')):.6f}"
        )
    with col_c:
        render_metric_card(
            "Valor produto", f"R$ {formatar_numero(item_original.get('Valor produto'))}"
        )
    with col_d:
        render_metric_card(
            "vBC ICMS", f"R$ {formatar_numero(item_original.get('vBC'))}"
        )
    with col_e:
        render_metric_card("vICMS", f"R$ {formatar_numero(item_original.get('vICMS'))}")
    with col_f:
        render_metric_card(
            "Base PIS/COFINS",
            f"R$ {formatar_numero(item_original.get('Base PIS/COFINS calculada'))}",
        )

    with st.expander("Ver dados completos do item selecionado", expanded=False):
        st.dataframe(
            pd.DataFrame([item_original]),
            width="stretch",
            hide_index=True,
            column_config=config_colunas_resultado_xml(),
        )

    render_section_header("Parâmetro do desmembramento")

    col_input, col_q1, col_q2, col_q3 = st.columns([1.2, 1, 1, 1])

    with col_input:
        quantidade_desmembrada = st.number_input(
            "Quantidade a desmembrar",
            min_value=0.0001,
            max_value=float(quantidade_original),
            value=1.0000 if quantidade_original >= 1 else float(quantidade_original),
            step=1.0000,
            format="%.4f",
        )

    quantidade_restante = quantidade_original - quantidade_desmembrada

    with col_q1:
        render_metric_card("Original", f"{quantidade_original:.4f}")
    with col_q2:
        render_metric_card("Desmembrada", f"{quantidade_desmembrada:.4f}")
    with col_q3:
        render_metric_card("Restante", f"{quantidade_restante:.4f}")

    if st.button("Simular desmembramento", type="primary", width="stretch"):
        try:
            resultado_simulacao = simular_desmembramento(
                item_original=item_original,
                quantidade_desmembrada=quantidade_desmembrada,
                criterio_referencia_icms=criterio_referencia_icms,
            )

            df_resultado_simulacao = pd.DataFrame(resultado_simulacao)

            render_section_header(
                "Resultado da simulação",
                "Linhas proporcionais do item desmembrado e do saldo restante.",
            )

            st.dataframe(
                df_resultado_simulacao,
                width="stretch",
                hide_index=True,
                column_config=config_colunas_simulador(),
            )

        except ValueError as erro:
            st.error(str(erro))
        except Exception as erro:
            st.error(f"Erro ao simular desmembramento: {erro}")


def formatar_valor_resultado_manual(campo: str, valor) -> str:
    """Formata valores do módulo manual para exibição limpa."""
    if campo == "Situação":
        return str(valor)

    if "p.p." in campo:
        return f"{formatar_numero(valor, 4)} p.p."

    if "%" in campo:
        return f"{formatar_numero(valor, 4)}%"

    if campo.startswith(("Valor", "Base", "Total")):
        return f"R$ {formatar_numero(valor)}"

    return str(valor)


def render_tabela_resultado_manual(resultado: dict, grupo: str, nome_arquivo: str):
    linhas = [
        {
            "Grupo": grupo,
            "Campo": campo,
            "Valor": formatar_valor_resultado_manual(campo, valor),
        }
        for campo, valor in resultado.items()
    ]

    df_resultado = pd.DataFrame(linhas)
    st.dataframe(df_resultado, width="stretch", hide_index=True)

    csv = df_resultado.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "Baixar resultado em CSV",
        data=csv,
        file_name=nome_arquivo,
        mime="text/csv",
        width="stretch",
    )


def render_submodulo_icms_reducao():
    render_section_header(
        "ICMS com redução de base",
        "Informe o valor de referência, a redução da base e a alíquota nominal do ICMS.",
    )

    with st.form("form_manual_icms_reducao"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            valor_referencia_icms = st.text_input(
                "Valor referência ICMS",
                placeholder="Ex.: 1000,00",
                key="manual_icms_valor_referencia",
            )

        with col2:
            reducao_icms = st.text_input(
                "Redução de base ICMS (%)",
                placeholder="Ex.: 20,00",
                key="manual_icms_reducao",
            )

        with col3:
            sugestao_icms = st.selectbox(
                "Sugestão alíquota ICMS",
                options=list(ALIQUOTAS_ICMS_SUGERIDAS.keys()) + ["Manual"],
                index=0,
                key="manual_icms_sugestao",
            )

        with col4:
            aliquota_icms_manual = st.text_input(
                "Alíquota ICMS manual (%)",
                placeholder="Vazio = sugestão",
                key="manual_icms_aliquota_manual",
            )

        calcular = st.form_submit_button(
            "Calcular ICMS", type="primary", width="stretch"
        )

    if not calcular:
        st.info("Preencha os campos do ICMS e clique em Calcular ICMS.")
        return

    try:
        resultado = calcular_icms_reducao_manual(
            valor_referencia_icms=valor_referencia_icms,
            reducao_icms=reducao_icms,
            sugestao_icms=sugestao_icms,
            aliquota_icms_manual=aliquota_icms_manual,
        )
    except CalculoManualInvalido as erro:
        st.error(str(erro))
        return
    except Exception as erro:
        st.error(f"Erro ao calcular ICMS manualmente: {erro}")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            "Base ICMS reduzida",
            f"R$ {formatar_numero(resultado.get('Base ICMS reduzida'))}",
            f"Redução: {formatar_numero(resultado.get('Redução ICMS %'), 4)}%",
        )
    with col2:
        render_metric_card(
            "Valor ICMS",
            f"R$ {formatar_numero(resultado.get('Valor ICMS'))}",
            f"Alíquota: {formatar_numero(resultado.get('Alíquota ICMS %'), 4)}%",
        )
    with col3:
        render_metric_card(
            "Valor reduzido",
            f"R$ {formatar_numero(resultado.get('Valor redução ICMS'))}",
            "Diferença entre referência e base reduzida",
        )
    with col4:
        render_metric_card(
            "Alíquota efetiva",
            f"{formatar_numero(resultado.get('Alíquota efetiva ICMS %'), 4)}%",
            "Percentual final sobre o valor de referência",
        )

    render_tabela_resultado_manual(
        resultado,
        grupo="ICMS",
        nome_arquivo="calculo_manual_icms.csv",
    )


def render_submodulo_aliquota_efetiva():
    render_section_header(
        "Alíquota efetiva e pRedBC equivalente",
        "Use quando você tem o valor total do produto e o valor do ICMS destacado.",
    )

    with st.form("form_manual_aliquota_efetiva"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            valor_total_produto = st.text_input(
                "Valor total do produto",
                placeholder="Ex.: 967,20",
                key="manual_efetiva_valor_total_produto",
            )

        with col2:
            valor_icms = st.text_input(
                "Valor do ICMS",
                placeholder="Ex.: 96,72",
                key="manual_efetiva_valor_icms",
            )

        with col3:
            sugestao_icms = st.selectbox(
                "Alíquota ICMS nominal",
                options=list(ALIQUOTAS_ICMS_SUGERIDAS.keys()) + ["Manual"],
                index=0,
                key="manual_efetiva_sugestao_icms",
            )

        with col4:
            aliquota_icms_manual = st.text_input(
                "Alíquota nominal manual (%)",
                placeholder="Vazio = sugestão",
                key="manual_efetiva_aliquota_icms_manual",
            )

        calcular = st.form_submit_button(
            "Calcular alíquota efetiva", type="primary", width="stretch"
        )

    if not calcular:
        st.info("Preencha o valor total, o ICMS destacado e clique em Calcular alíquota efetiva.")
        return

    try:
        resultado = calcular_reducao_por_valor_icms(
            valor_total_produto=valor_total_produto,
            valor_icms=valor_icms,
            sugestao_icms=sugestao_icms,
            aliquota_icms_manual=aliquota_icms_manual,
        )
    except CalculoManualInvalido as erro:
        st.error(str(erro))
        return
    except Exception as erro:
        st.error(f"Erro ao calcular alíquota efetiva: {erro}")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            "Alíquota efetiva",
            f"{formatar_numero(resultado.get('Alíquota efetiva ICMS %'), 4)}%",
            "Percentual real do ICMS destacado",
        )
    with col2:
        render_metric_card(
            "pRedBC equivalente",
            f"{formatar_numero(resultado.get('pRedBC equivalente %'), 4)}%",
            "Redução de base equivalente",
        )
    with col3:
        render_metric_card(
            "Base ICMS estimada",
            f"R$ {formatar_numero(resultado.get('Base ICMS estimada'))}",
            "Base aproximada para o ICMS informado",
        )
    with col4:
        render_metric_card(
            "Redução da alíquota",
            f"{formatar_numero(resultado.get('Redução da alíquota em p.p.'), 4)} p.p.",
            "Diferença entre nominal e efetiva",
        )

    st.success(
        "Leitura fiscal: redução de "
        f"{formatar_numero(resultado.get('Alíquota ICMS nominal %'), 4)}% para "
        f"{formatar_numero(resultado.get('Alíquota efetiva ICMS %'), 4)}%. "
        f"pRedBC equivalente: {formatar_numero(resultado.get('pRedBC equivalente %'), 4)}%."
    )

    render_tabela_resultado_manual(
        resultado,
        grupo="Alíquota efetiva",
        nome_arquivo="calculo_manual_aliquota_efetiva.csv",
    )


def render_submodulo_ipi():
    render_section_header(
        "IPI",
        "Informe a base e a alíquota do IPI. A alíquota deve ser definida conforme o produto/NCM.",
    )

    with st.form("form_manual_ipi"):
        col1, col2 = st.columns(2)

        with col1:
            base_ipi = st.text_input(
                "Base IPI",
                placeholder="Ex.: 1000,00",
                key="manual_ipi_base",
            )

        with col2:
            aliquota_ipi = st.text_input(
                "Alíquota IPI (%)",
                placeholder="Ex.: 5,00",
                key="manual_ipi_aliquota",
            )

        calcular = st.form_submit_button(
            "Calcular IPI", type="primary", width="stretch"
        )

    if not calcular:
        st.info("Preencha a base e a alíquota para calcular o IPI.")
        return

    try:
        resultado = calcular_ipi_manual(base_ipi=base_ipi, aliquota_ipi=aliquota_ipi)
    except CalculoManualInvalido as erro:
        st.error(str(erro))
        return
    except Exception as erro:
        st.error(f"Erro ao calcular IPI manualmente: {erro}")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card(
            "Valor IPI",
            f"R$ {formatar_numero(resultado.get('Valor IPI'))}",
            f"Alíquota: {formatar_numero(resultado.get('Alíquota IPI %'), 4)}%",
        )
    with col2:
        render_metric_card(
            "Total com IPI",
            f"R$ {formatar_numero(resultado.get('Total com IPI'))}",
            "Base acrescida do IPI",
        )
    with col3:
        render_metric_card(
            "Base IPI",
            f"R$ {formatar_numero(resultado.get('Base IPI'))}",
            "Base informada manualmente",
        )

    render_tabela_resultado_manual(
        resultado,
        grupo="IPI",
        nome_arquivo="calculo_manual_ipi.csv",
    )


def render_submodulo_pis_cofins():
    render_section_header(
        "PIS e COFINS",
        "Informe a base e escolha uma sugestão de regime ou preencha as alíquotas manualmente.",
    )

    with st.form("form_manual_pis_cofins"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            base_pis_cofins = st.text_input(
                "Base PIS/COFINS",
                placeholder="Ex.: 1000,00",
                key="manual_piscofins_base",
            )

        with col2:
            sugestao_pis_cofins = st.selectbox(
                "Sugestão PIS/COFINS",
                options=list(ALIQUOTAS_PIS_COFINS_SUGERIDAS.keys()) + ["Manual"],
                index=0,
                key="manual_piscofins_sugestao",
            )

        with col3:
            aliquota_pis_manual = st.text_input(
                "Alíquota PIS manual (%)",
                placeholder="Vazio = sugestão",
                key="manual_piscofins_aliquota_pis",
            )

        with col4:
            aliquota_cofins_manual = st.text_input(
                "Alíquota COFINS manual (%)",
                placeholder="Vazio = sugestão",
                key="manual_piscofins_aliquota_cofins",
            )

        calcular = st.form_submit_button(
            "Calcular PIS/COFINS", type="primary", width="stretch"
        )

    if not calcular:
        st.info("Preencha a base de PIS/COFINS e clique em Calcular PIS/COFINS.")
        return

    try:
        resultado = calcular_pis_cofins_manual(
            sugestao_pis_cofins=sugestao_pis_cofins,
            base_pis_cofins=base_pis_cofins,
            aliquota_pis_manual=aliquota_pis_manual,
            aliquota_cofins_manual=aliquota_cofins_manual,
        )
    except CalculoManualInvalido as erro:
        st.error(str(erro))
        return
    except Exception as erro:
        st.error(f"Erro ao calcular PIS/COFINS manualmente: {erro}")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            "Valor PIS",
            f"R$ {formatar_numero(resultado.get('Valor PIS'))}",
            f"Alíquota: {formatar_numero(resultado.get('Alíquota PIS %'), 4)}%",
        )
    with col2:
        render_metric_card(
            "Valor COFINS",
            f"R$ {formatar_numero(resultado.get('Valor COFINS'))}",
            f"Alíquota: {formatar_numero(resultado.get('Alíquota COFINS %'), 4)}%",
        )
    with col3:
        render_metric_card(
            "Total PIS/COFINS",
            f"R$ {formatar_numero(resultado.get('Total PIS/COFINS'))}",
            "Soma dos dois tributos",
        )
    with col4:
        render_metric_card(
            "Base PIS/COFINS",
            f"R$ {formatar_numero(resultado.get('Base PIS/COFINS'))}",
            "Base informada manualmente",
        )

    render_tabela_resultado_manual(
        resultado,
        grupo="PIS/COFINS",
        nome_arquivo="calculo_manual_pis_cofins.csv",
    )


def render_calculos_manuais():
    render_topo(
        "Cálculos Manuais",
        "Escolha um submódulo e calcule cada tributo separadamente, sem depender de XML.",
    )

    submodulo = st.radio(
        "Submódulo",
        [
            "ICMS / Redução",
            "Alíquota efetiva / pRedBC",
            "IPI",
            "PIS e COFINS",
        ],
        horizontal=True,
        key="manual_submodulo",
    )

    st.divider()

    if submodulo == "ICMS / Redução":
        render_submodulo_icms_reducao()
    elif submodulo == "Alíquota efetiva / pRedBC":
        render_submodulo_aliquota_efetiva()
    elif submodulo == "IPI":
        render_submodulo_ipi()
    elif submodulo == "PIS e COFINS":
        render_submodulo_pis_cofins()

    st.warning(
        "Observação: os cálculos manuais são simulações. Regime tributário, CST/CSOSN, NCM, benefício fiscal "
        "e regra específica do produto ainda precisam ser conferidos na análise fiscal."
    )


def render_formulas():
    render_topo(
        "Fórmulas utilizadas",
        "Referência dos critérios aplicados na leitura do XML e na simulação proporcional.",
    )

    render_section_header("Redução de base ICMS")
    st.code(
        "pRedBC calculado = 100 - ((vBC / Valor referência ICMS) * 100)",
        language="text",
    )
    st.write(
        "O campo `Valor referência ICMS` é recalculado conforme o critério escolhido "
        "na barra lateral em `Critério do pRedBC`. Campos ausentes no XML, como "
        "`vFrete`, `vSeg`, `vDesc` ou `vOutro`, são considerados como `0`."
    )

    render_section_header("Critérios de Valor referência ICMS")
    st.code(
        "Critério 1: Quantidade x unitário + vOutro\n"
        "Valor referência ICMS = qTrib * vUnTrib + vOutro\n\n"
        "Critério 2: Valor da operação\n"
        "Valor referência ICMS = vProd + vFrete + vSeg + vOutro - vDesc\n\n"
        "Critério 3: Somente vProd\n"
        "Valor referência ICMS = vProd",
        language="text",
    )

    render_section_header("Base PIS/COFINS calculada")
    st.code("Base PIS/COFINS calculada = Valor produto - vICMS", language="text")

    render_section_header("Cálculos Manuais")
    st.code(
        "Base ICMS reduzida = Valor referência ICMS * (1 - Redução ICMS / 100)\n"
        "Valor ICMS = Base ICMS reduzida * Alíquota ICMS / 100\n"
        "Alíquota efetiva = (Valor ICMS / Valor total produto) * 100\n"
        "Base ICMS estimada = Valor ICMS / (Alíquota ICMS nominal / 100)\n"
        "pRedBC equivalente = 100 - ((Base ICMS estimada / Valor total produto) * 100)\n"
        "Valor IPI = Base IPI * Alíquota IPI / 100\n"
        "Base PIS/COFINS automática = Valor referência ICMS - Valor ICMS\n"
        "Valor PIS = Base PIS/COFINS * Alíquota PIS / 100\n"
        "Valor COFINS = Base PIS/COFINS * Alíquota COFINS / 100",
        language="text",
    )

    render_section_header("Simulador proporcional")
    st.code(
        "Fator = Quantidade desmembrada / Quantidade original\n"
        "Valor proporcional = Valor original * Fator",
        language="text",
    )


aplicar_css_global()

if not tela_login():
    st.stop()

pagina, arquivos_xml, criterio_referencia_icms = render_sidebar_inicio()

if pagina == "Cálculos Manuais":
    render_calculos_manuais()
    st.stop()

if not arquivos_xml:
    render_estado_inicial()
    st.stop()

try:
    linhas = parsear_varios_xmls(
        arquivos_xml, criterio_referencia_icms=criterio_referencia_icms
    )
except Exception as erro:
    st.error(f"Erro ao processar XML: {erro}")
    st.stop()

if not linhas:
    st.warning("Nenhum item de NF-e foi encontrado nos XMLs enviados.")
    st.stop()

df_original = preparar_dataframe(linhas)

filtros = render_sidebar_filtros(df_original)

df = aplicar_filtros(df_original, filtros)

if df.empty:
    render_topo(
        "Nenhum item encontrado",
        "Os XMLs foram lidos, mas os filtros laterais não retornaram itens.",
    )
    st.warning("Limpe ou ajuste os filtros na barra lateral para visualizar os itens.")
    st.stop()

if pagina == "Dashboard":
    render_dashboard(df, arquivos_xml)
elif pagina == "Resultado XML":
    render_resultado_xml(df)
elif pagina == "Simulador":
    render_simulador(df, criterio_referencia_icms)
elif pagina == "Cálculos Manuais":
    render_calculos_manuais()
elif pagina == "Fórmulas":
    render_formulas()
