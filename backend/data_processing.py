import os
import re
import pandas as pd


# ==========================================
# DOSSIER DATA
# ==========================================

# ==========================================
# DOSSIER DATA
# ==========================================

# Chemin du projet : C:\Users\ORIGINAL\Desktop\app 2.0
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# C:\Users\ORIGINAL\Desktop\app 2.0\data
DATA_DIR = os.path.join(BASE_DIR, "data")

# Créer le dossier data s'il n'existe pas
os.makedirs(DATA_DIR, exist_ok=True)

# Fichiers CSV
RAW_FILE = os.path.join(
    DATA_DIR,
    "entreprises_informatique_brutes.csv"
)

CLEAN_FILE = os.path.join(
    DATA_DIR,
    "entreprises_informatique_marrakech.csv"
)


# ==========================================
# CLASSIFICATION DES SOUS-SECTEURS
# ==========================================

def determine_subsector(name, types_list):

    text = (
        str(name)
        + " "
        + " ".join(str(v) for v in types_list)
    ).lower()

    if any(x in text for x in [
        "cyber",
        "cybersécurité",
        "cybersecurity",
        "security"
    ]):
        return "Cybersécurité"

    if any(x in text for x in [
        "software",
        "logiciel",
        "programming",
        "developer",
        "development"
    ]):
        return "Développement logiciel"

    if any(x in text for x in [
        "data",
        "database",
        "cloud"
    ]):
        return "Data / Cloud / Base de données"

    if any(x in text for x in [
        "web",
        "website",
        "internet"
    ]):
        return "Web / Internet"

    if any(x in text for x in [
        "telecom",
        "télécom",
        "network",
        "réseau"
    ]):
        return "Télécom / Réseaux"

    if any(x in text for x in [
        "computer",
        "hardware",
        "electronics",
        "électronique"
    ]):
        return "Informatique / Hardware"

    if any(x in text for x in [
        "repair",
        "réparation",
        "maintenance",
        "support"
    ]):
        return "Support / Maintenance"

    if any(x in text for x in [
        "digital",
        "technology",
        "technologie",
        "solution"
    ]):
        return "Technologie / Digital"

    return "Informatique"


# ==========================================
# NORMALISATION
# ==========================================

def normaliser_texte(value):

    if value is None:
        return ""

    return str(value).lower().strip()


# ==========================================
# LIEN SITE WEB CLIQUABLE
# ==========================================

def url_propre(valeur):
    """Retourne une URL valide (avec https://) ou None
    si le site n'est pas renseigné."""

    texte = str(valeur).strip()

    if texte in ("", "Non renseigné", "nan", "None"):
        return None

    if not texte.lower().startswith(
        ("http://", "https://")
    ):
        texte = "https://" + texte

    return texte


def whatsapp_url(telephone):
    """Lien WhatsApp si le numéro est un mobile marocain
    (06 / 07), sinon None (les fixes 05 n'ont pas WhatsApp)."""

    chiffres = re.sub(
        r"\D",
        "",
        str(telephone)
    )

    if (
        chiffres.startswith("212")
        and len(chiffres) == 12
        and chiffres[3] in "67"
    ):
        return "https://wa.me/" + chiffres

    if (
        chiffres.startswith("0")
        and len(chiffres) == 10
        and chiffres[1] in "67"
    ):
        return "https://wa.me/212" + chiffres[1:]

    return None


# ==========================================
# NETTOYAGE DES DONNÉES
# ==========================================

def nettoyer_donnees(df):

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    colonnes = [
        "place_id",
        "nom",
        "adresse",
        "telephone",
        "site_web",
        "sous_secteur",
        "latitude",
        "longitude",
        "source"
    ]

    # Créer les colonnes manquantes
    for colonne in colonnes:

        if colonne not in df.columns:

            if colonne in [
                "latitude",
                "longitude"
            ]:
                df[colonne] = None

            else:
                df[colonne] = ""

    # Nom
    df["nom"] = (
        df["nom"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Supprimer les lignes sans nom
    df = df[
        df["nom"].str.len() > 0
    ]

    # Téléphone
    df["telephone"] = (
        df["telephone"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df.loc[
        df["telephone"] == "",
        "telephone"
    ] = "Non renseigné"

    # Site web
    df["site_web"] = (
        df["site_web"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df.loc[
        df["site_web"] == "",
        "site_web"
    ] = "Non renseigné"

    # Adresse
    df["adresse"] = (
        df["adresse"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df.loc[
        df["adresse"] == "",
        "adresse"
    ] = "Non renseignée"

    # Sous-secteur
    df["sous_secteur"] = (
        df["sous_secteur"]
        .fillna("Informatique")
        .astype(str)
        .str.strip()
    )

    # Latitude
    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    # Longitude
    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    # Supprimer les coordonnées invalides
    df = df.dropna(
        subset=[
            "latitude",
            "longitude"
        ]
    )

    # Supprimer les doublons Google
    if "place_id" in df.columns:

        df = df.drop_duplicates(
            subset=["place_id"]
        )

    # Supprimer les doublons nom + position
    df = df.drop_duplicates(
        subset=[
            "nom",
            "latitude",
            "longitude"
        ]
    )

    # Trier par nom
    df = df.sort_values(
        by="nom",
        ascending=True
    )

    return df.reset_index(
        drop=True
    )


# ==========================================
# DONNÉES DE SIMULATION
# ==========================================

def donnees_simulation():

    simulated_data = [

        {
            "place_id": "simulation_1",
            "nom": "Digital Morocco Solutions",
            "adresse": "Avenue Mohammed V, Gueliz, Marrakech",
            "telephone": "+212 524 43 00 01",
            "site_web": "https://example.com",
            "sous_secteur": "Développement logiciel",
            "latitude": 31.6340,
            "longitude": -8.0130,
            "source": "Simulation"
        },

        {
            "place_id": "simulation_2",
            "nom": "Atlas Web & Cloud",
            "adresse": "Boulevard Zerktouni, Marrakech",
            "telephone": "+212 524 44 00 02",
            "site_web": "https://example.com",
            "sous_secteur": "Web / Internet",
            "latitude": 31.6250,
            "longitude": -8.0200,
            "source": "Simulation"
        },

        {
            "place_id": "simulation_3",
            "nom": "Marrakech Cyber Defense",
            "adresse": "Sidi Ghanem, Marrakech",
            "telephone": "+212 524 33 55 66",
            "site_web": "Non renseigné",
            "sous_secteur": "Cybersécurité",
            "latitude": 31.6600,
            "longitude": -8.0250,
            "source": "Simulation"
        },

        {
            "place_id": "simulation_4",
            "nom": "Marrakech Digital Solutions",
            "adresse": "Gueliz, Marrakech",
            "telephone": "Non renseigné",
            "site_web": "Non renseigné",
            "sous_secteur": "Technologie / Digital",
            "latitude": 31.6320,
            "longitude": -8.0080,
            "source": "Simulation"
        },

        {
            "place_id": "simulation_5",
            "nom": "Atlas Technology Center",
            "adresse": "Daoudiate, Marrakech",
            "telephone": "Non renseigné",
            "site_web": "Non renseigné",
            "sous_secteur": "Informatique",
            "latitude": 31.6480,
            "longitude": -8.0000,
            "source": "Simulation"
        }
    ]

    return pd.DataFrame(
        simulated_data
    )


# ==========================================
# CHARGER LES DONNÉES PROPRES
# ==========================================

def charger_donnees():

    if not os.path.exists(
        CLEAN_FILE
    ):
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            CLEAN_FILE,
            encoding="utf-8-sig"
        )

        return nettoyer_donnees(df)

    except Exception:

        return pd.DataFrame()


# ==========================================
# CHARGER LES DONNÉES BRUTES
# ==========================================

def charger_donnees_brutes():

    if not os.path.exists(
        RAW_FILE
    ):
        return pd.DataFrame()

    try:

        return pd.read_csv(
            RAW_FILE,
            encoding="utf-8-sig"
        )

    except Exception:

        return pd.DataFrame()