import streamlit as st


COULEUR_PAR_DEFAUT = "#FF4B4B"


def couleur_accent():
    """Couleur d'accent du thème actif (primaryColor de
    .streamlit/config.toml)."""

    try:

        couleur = st.get_option("theme.primaryColor")

    except Exception:

        couleur = None

    return couleur or COULEUR_PAR_DEFAUT


def _hex_vers_rgb(couleur):
    """'#RRGGBB' -> (r, g, b). Retourne None si invalide."""

    c = str(couleur).strip().lstrip("#")

    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)

    if len(c) != 6:
        return None

    try:
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _eclaircir(rgb, facteur):
    """Mélange la couleur avec du blanc."""

    return tuple(
        int(v + (255 - v) * facteur)
        for v in rgb
    )


def appliquer_style():
    """Habillage de l'application : cartes arrondies, onglets,
    boutons et titre en dégradé. S'adapte à la couleur d'accent
    du thème actif."""

    accent = couleur_accent()

    rgb = _hex_vers_rgb(accent)

    if rgb is None:

        # Couleur nommée (ex. "purple") : on garde le thème tel quel
        return

    r, g, b = rgb

    clair = "rgb({}, {}, {})".format(*_eclaircir(rgb, 0.45))

    css = f"""
    <style>

    /* ---------- Titre principal en dégradé ---------- */
    .stApp h1 {{
        background: linear-gradient(90deg, {accent}, {clair});
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }}

    /* ---------- Cartes de chiffres clés ---------- */
    [data-testid="stMetric"] {{
        background: rgba(128, 128, 128, 0.10);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-left: 4px solid {accent};
        border-radius: 12px;
        padding: 12px 16px;
    }}

    /* ---------- Onglets ---------- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px 10px 0 0;
        padding: 8px 18px;
    }}

    .stTabs [aria-selected="true"] {{
        background: rgba({r}, {g}, {b}, 0.18);
    }}

    /* ---------- Boutons ---------- */
    .stButton > button,
    .stDownloadButton > button,
    .stLinkButton > a {{
        border-radius: 10px;
        font-weight: 600;
    }}

    /* ---------- Tableaux et cartes ---------- */
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
    }}

    [data-testid="stExpander"] {{
        border-radius: 12px;
    }}

    /* ---------- Séparateurs aux couleurs du thème ---------- */
    hr {{
        border-color: rgba({r}, {g}, {b}, 0.35) !important;
    }}

    /* ---------- Masquer le pied « Made with Streamlit » ---------- */
    footer {{
        visibility: hidden;
    }}

    </style>
    """

    st.markdown(
        css,
        unsafe_allow_html=True
    )