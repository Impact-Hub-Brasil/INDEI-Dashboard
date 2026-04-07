"""Identidade visual INDEI: cores da marca, tipografia e componentes reutilizáveis para Streamlit."""
from __future__ import annotations

import base64
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


def parse_brazilian_number_series(series: pd.Series) -> pd.Series:
    """Converte valores no padrão BR (ex.: R$ 18.329,13 ou 1.234.567) para float."""

    def one(x: object) -> float:
        if pd.isna(x):
            return np.nan
        if isinstance(x, (int, np.integer)):
            return float(x)
        if isinstance(x, float):
            return x if not np.isnan(x) else np.nan
        t = str(x).strip()
        if t.lower() in ("nan", "none", ""):
            return np.nan
        t = re.sub(r"[R$\s\u00a0]", "", t)
        if not t:
            return np.nan
        if "," in t:
            t = t.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
            t = t.replace(".", "")
        v = pd.to_numeric(t, errors="coerce")
        return float(v) if pd.notna(v) else np.nan

    return series.map(one)

ROOT = Path(__file__).resolve().parent
LOGO_SVG_PATH = ROOT / "INDEI - logo.svg"
LOGO_PNG_PATH = ROOT / "INDEI - logo.png"
IH_BRASIL_LOGO_PATH = ROOT / "IH Brasil - logo.png"

SIDEBAR_INDEI_ABOUT_MD = """
O INDEI é um índice que mede a prosperidade sistêmica dos municípios brasileiros com mais de 100 mil habitantes, avaliando o território em três eixos articulados: econômico-empresarial, sociocultural e ambiental.

Além de um ranking, o INDEI também funciona como ferramenta de diagnóstico para orientar estratégias de desenvolvimento sustentável e orquestração ecossistêmica, mostrando onde estão forças, fragilidades e “sementes de prosperidade” em cada cidade.
g
Realização: Impact Hub Brasil  |  Contato: contato@impacthub.net

[https://impacthub.org.br/indei](https://impacthub.org.br/indei)
""".strip()

BRAND = {
    "laranja": "#F69220",
    "creme": "#FFF5DE",
    "amarelo": "#FEC430",
    "verde_oliva": "#807921",
    "oliva_claro": "#A69B02",
    "verde_escuro": "#464F15",
    "magenta": "#D92387",
    "grafite": "#333333",
}

COLORWAY = [
    BRAND["laranja"],
    BRAND["magenta"],
    BRAND["verde_oliva"],
    BRAND["amarelo"],
    BRAND["verde_escuro"],
    BRAND["oliva_claro"],
]

SEQUENTIAL_SCALE = [
    [0.0, BRAND["verde_escuro"]],
    [0.35, BRAND["verde_oliva"]],
    [0.65, BRAND["amarelo"]],
    [1.0, BRAND["laranja"]],
]

DIVERGING_CORR = [
    [0.0, BRAND["magenta"]],
    [0.25, BRAND["laranja"]],
    [0.5, BRAND["creme"]],
    [0.75, BRAND["oliva_claro"]],
    [1.0, BRAND["verde_escuro"]],
]


def inject_indei_theme() -> None:
    c = BRAND
    st.markdown(
        f"""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,900;1,9..40,900&family=Montserrat:ital,wght@0,500;1,500&display=swap" rel="stylesheet">
<style>
    /* Mesma aparência em light/dark do SO: força esquema claro nos controlos nativos */
    html {{
        color-scheme: light only;
    }}
    .block-container {{
        padding-top: 1.1rem;
    }}
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {{
        background-color: {c["creme"]} !important;
    }}
    [data-testid="stHeader"] {{
        background-color: rgba(255, 245, 222, 0.96) !important;
    }}
    p, label, span, li, div[data-testid="stMarkdownContainer"] {{
        font-family: 'Montserrat', sans-serif;
        color: {c["grafite"]};
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 900 !important;
        color: {c["verde_escuro"]} !important;
        letter-spacing: -0.02em;
    }}
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {c["grafite"]} 0%, #252525 100%) !important;
    }}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {{
        color: {c["creme"]} !important;
    }}
    [data-testid="stSidebar"] a {{
        color: {c["amarelo"]} !important;
    }}
    /* Títulos na sidebar */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {{
        color: {c["creme"]} !important;
    }}
    /* Select / multiselect: fundo claro fixo (evita tema escuro do browser) */
    [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stMultiSelect"] [data-baseweb="select"] {{
        background-color: #ffffff !important;
        border-color: #d3d3d3 !important;
        color: {c["grafite"]} !important;
    }}
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
        color: {c["grafite"]} !important;
        background-color: transparent !important;
    }}
    /* Tags do multiselect: fundo #807921 e texto #FFF5DE (inclui spans internos do Base Web) */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        background-color: {c["verde_oliva"]} !important;
        border-color: {c["verde_oliva"]} !important;
        color: {c["creme"]} !important;
        -webkit-text-fill-color: {c["creme"]} !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"]:hover {{
        background-color: #6a6219 !important;
        border-color: #6a6219 !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    [data-testid="stMultiSelect"] [data-baseweb="tag"] button,
    [data-testid="stMultiSelect"] [data-baseweb="tag"] div {{
        color: {c["creme"]} !important;
        -webkit-text-fill-color: {c["creme"]} !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] svg,
    [data-testid="stMultiSelect"] [data-baseweb="tag"] path {{
        fill: {c["creme"]} !important;
    }}
    /* Fundo do container Plotly */
    [data-testid="stPlotlyChart"] {{
        background-color: {c["creme"]} !important;
        border-radius: 0.25rem;
    }}
    /* Expander / inputs principais: manter leitura clara em qualquer prefers-color-scheme */
    @media (prefers-color-scheme: dark) {{
        .stApp,
        [data-testid="stAppViewContainer"] {{
            background-color: {c["creme"]} !important;
            color: {c["grafite"]} !important;
        }}
        [data-testid="stSelectbox"] [data-baseweb="select"],
        [data-testid="stMultiSelect"] [data-baseweb="select"] {{
            background-color: #ffffff !important;
            color: {c["grafite"]} !important;
        }}
    }}
</style>
""",
        unsafe_allow_html=True,
    )


def _sidebar_logo_svg_base64() -> str | None:
    """SVG com preenchimento claro; base64 para usar em <img> (st.image não aceita SVG via PIL)."""
    if not LOGO_SVG_PATH.is_file():
        return None
    svg = LOGO_SVG_PATH.read_text(encoding="utf-8")
    for old in ("#464f15", "#464F15"):
        svg = svg.replace(old, BRAND["creme"])
    return base64.b64encode(svg.encode("utf-8")).decode("ascii")


def sidebar_branding(page_title: str | None = None) -> None:
    svg_b64 = _sidebar_logo_svg_base64()
    if svg_b64 is not None:
        st.sidebar.markdown(
            f'<img src="data:image/svg+xml;base64,{svg_b64}" alt="INDEI" '
            'style="width:100%;max-width:220px;height:auto;display:block;margin:0 auto;"/>',
            unsafe_allow_html=True,
        )
    elif LOGO_PNG_PATH.is_file():
        st.sidebar.image(str(LOGO_PNG_PATH), use_container_width=True)
    if page_title:
        st.sidebar.markdown(f"### {page_title}")
    st.sidebar.divider()
    st.sidebar.markdown(SIDEBAR_INDEI_ABOUT_MD)
    if IH_BRASIL_LOGO_PATH.is_file():
        st.sidebar.image(str(IH_BRASIL_LOGO_PATH), use_container_width=True)


def _visual_subdirs() -> tuple[Path | None, Path | None]:
    visual = ROOT / "Visual"
    if not visual.is_dir():
        return None, None
    outlined: Path | None = None
    filled: Path | None = None
    for d in sorted(visual.iterdir(), key=lambda p: p.name):
        if not d.is_dir():
            continue
        if d.name == "Preenchidos":
            filled = d
        else:
            outlined = d
    return outlined, filled


def _find_svg(folder: Path, key: str) -> Path | None:
    key_l = key.lower()
    for p in sorted(folder.glob("*.svg")):
        stem = p.stem.lower().replace(" ", "-")
        if key_l in stem or stem.startswith(key_l):
            return p
    return None


def decorative_svg_strip(keys: tuple[str, ...] = ("Estrela", "Mandacaru", "Guariroba")) -> None:
    outlined, filled = _visual_subdirs()
    if not outlined or not filled:
        return
    row1 = st.columns(len(keys))
    row2 = st.columns(len(keys))
    for i, key in enumerate(keys):
        o = _find_svg(outlined, key)
        f = _find_svg(filled, key)
        with row1[i]:
            if o:
                st.image(str(o), use_container_width=True)
            st.caption("Traçado")
        with row2[i]:
            if f:
                st.image(str(f), use_container_width=True)
            st.caption("Preenchido")


def plotly_brand_layout() -> dict:
    return {
        "font": dict(
            family="DM Sans, Montserrat, sans-serif",
            size=13,
            color=BRAND["grafite"],
        ),
        "title": dict(
            font=dict(
                family="DM Sans, Montserrat, sans-serif",
                size=18,
                color=BRAND["verde_escuro"],
            )
        ),
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": BRAND["creme"],
        "colorway": COLORWAY,
    }


def style_plotly(fig):
    fig.update_layout(**plotly_brand_layout())
    return fig


def style_choropleth_coloraxis(fig) -> None:
    fig.update_coloraxes(colorscale=SEQUENTIAL_SCALE, colorbar=dict(tickfont=dict(color=BRAND["grafite"])))


def style_choropleth_map_canvas(fig) -> None:
    """Fundo do mapa e da área do gráfico igual ao fundo da página (#FFF5DE)."""
    bg = BRAND["creme"]
    fig.update_layout(paper_bgcolor=bg)
    fig.update_geos(bgcolor=bg)


def style_scatter_trendline(fig) -> None:
    for tr in fig.data:
        mode = getattr(tr, "mode", None) or ""
        if "lines" in mode and getattr(tr, "fill", None) is None:
            tr.update(line=dict(color=BRAND["verde_escuro"], width=2))
