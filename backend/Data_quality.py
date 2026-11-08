import io
import re

import numpy as np
import pandas as pd

from backend.data_processing import nettoyer_donnees
from backend.statistiques import (
    preparer_donnees,
    RAYON_MARRAKECH_KM
)


ABSENT = ("", "Non renseigné", "Non renseignée", "nan", "None")

COLONNES_QUALITE = [
    "nom",
    "adresse",
    "telephone",
    "site_web",
    "sous_secteur",
    "latitude",
    "longitude"
]

# Domaines partagés par plusieurs entreprises : ne comptent
# pas comme doublon
DOMAINES_RESEAUX = (
    "facebook.com", "instagram.com", "linkedin.com",
    "linktr.ee", "wa.me", "google.com", "business.site"
)


# ==========================================
# OUTILS
# ==========================================

def est_absent(valeur):

    if valeur is None:
        return True

    try:
        if pd.isna(valeur):
            return True
    except (TypeError, ValueError):
        pass

    return str(valeur).strip() in ABSENT


def _domaine(url):

    if est_absent(url):
        return None

    d = str(url).lower().strip()

    d = re.sub(r"^https?://", "", d)

    d = d.split("/")[0]

    d = re.sub(r"^www\.", "", d)

    return d or None


def _chiffres(tel):

    if est_absent(tel):
        return None

    c = re.sub(r"\D", "", str(tel))

    return c if len(c) >= 9 else None


# ==========================================
# COMPLÉTUDE ET SCORE
# ==========================================

def completude(df):
    """% de valeurs réellement renseignées par colonne
    (« Non renseigné » compte comme manquant)."""

    lignes = []

    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "colonne", "renseignees",
                "manquantes", "pourcentage"
            ]
        )

    for colonne in COLONNES_QUALITE:

        if colonne not in df.columns:
            continue

        ok = int(
            (~df[colonne].apply(est_absent)).sum()
        )

        lignes.append(
            {
                "colonne": colonne,
                "renseignees": ok,
                "manquantes": len(df) - ok,
                "pourcentage": round(ok / len(df) * 100, 1)
            }
        )

    return pd.DataFrame(lignes)


def score_qualite(df):
    """Score global de 0 à 100 = moyenne de la complétude."""

    c = completude(df)

    if c.empty:
        return 0

    return int(round(c["pourcentage"].mean()))


# ==========================================
# DIAGNOSTIC DU NETTOYAGE (brut -> propre)
# ==========================================

def diagnostic_nettoyage(df_brut):
    """Rejoue les étapes de nettoyage et compte ce que
    chacune a retiré ou corrigé."""

    if df_brut is None or df_brut.empty:
        return pd.DataFrame()

    d = df_brut.copy()

    etapes = []

    etapes.append(
        ("📥 Lignes brutes", len(d), "Données collectées")
    )

    # 1) sans nom
    nom = d.get("nom", pd.Series("", index=d.index))

    sans_nom = nom.fillna("").astype(str).str.strip().eq("")

    etapes.append(
        ("🗑️ Lignes sans nom", int(sans_nom.sum()),
         "Supprimées")
    )

    d = d[~sans_nom]

    # 2) coordonnées invalides
    lat = pd.to_numeric(
        d.get("latitude"), errors="coerce"
    )

    lon = pd.to_numeric(
        d.get("longitude"), errors="coerce"
    )

    invalides = lat.isna() | lon.isna()

    etapes.append(
        ("📍 Coordonnées invalides", int(invalides.sum()),
         "Supprimées")
    )

    d = d[~invalides]

    # 3) doublons place_id
    if "place_id" in d.columns:

        dup_id = d.duplicated(subset=["place_id"])

        etapes.append(
            ("♊ Doublons Google (place_id)",
             int(dup_id.sum()), "Supprimés")
        )

        d = d[~dup_id]

    # 4) doublons nom + position
    dup_pos = d.duplicated(
        subset=["nom", "latitude", "longitude"]
    )

    etapes.append(
        ("♊ Doublons nom + position",
         int(dup_pos.sum()), "Supprimés")
    )

    d = d[~dup_pos]

    # 5) valeurs remplacées par « Non renseigné »
    for colonne, libelle in [
        ("telephone", "📞 Téléphones manquants"),
        ("site_web", "🌐 Sites web manquants"),
        ("adresse", "🗺️ Adresses manquantes")
    ]:

        if colonne in d.columns:

            manquants = d[colonne].apply(est_absent).sum()

            etapes.append(
                (libelle, int(manquants),
                 "Remplacés par « Non renseigné »")
            )

    etapes.append(
        ("✅ Lignes après nettoyage",
         len(nettoyer_donnees(df_brut)), "Données propres")
    )

    return pd.DataFrame(
        etapes,
        columns=["etape", "lignes", "action"]
    )


# ==========================================
# PROBLÈMES DE QUALITÉ
# ==========================================

def fiches_incompletes(df):
    """Entreprises sans site et/ou sans téléphone."""

    if df is None or df.empty:
        return pd.DataFrame()

    sans_site = df["site_web"].apply(est_absent)

    sans_tel = df["telephone"].apply(est_absent)

    d = df[sans_site | sans_tel].copy()

    d["manque"] = np.where(
        sans_site[d.index] & sans_tel[d.index],
        "Site + téléphone",
        np.where(
            sans_site[d.index],
            "Site web",
            "Téléphone"
        )
    )

    return d


def doublons_potentiels(df):
    """Entreprises qui partagent le même téléphone, le même
    site (hors réseaux sociaux) ou le même nom."""

    if df is None or df.empty:
        return pd.DataFrame()

    d = df.copy()

    d["_tel"] = d["telephone"].apply(_chiffres)

    d["_site"] = d["site_web"].apply(_domaine)

    d["_site"] = d["_site"].where(
        ~d["_site"].fillna("").str.endswith(
            DOMAINES_RESEAUX
        ),
        None
    )

    d["_nom"] = d["nom"].astype(str).str.lower().str.strip()

    morceaux = []

    for cle, motif in [
        ("_tel", "Même téléphone"),
        ("_site", "Même site web"),
        ("_nom", "Même nom")
    ]:

        sous = d[
            d[cle].notna()
            & d.duplicated(subset=[cle], keep=False)
        ].copy()

        if sous.empty:
            continue

        sous["motif"] = motif

        sous["groupe"] = sous[cle].astype(str)

        morceaux.append(sous)

    if not morceaux:
        return pd.DataFrame()

    resultat = pd.concat(morceaux)

    colonnes = [
        "motif", "groupe", "nom", "adresse",
        "telephone", "site_web"
    ]

    return (
        resultat[colonnes]
        .sort_values(["motif", "groupe", "nom"])
        .reset_index(drop=True)
    )


def hors_marrakech(df):
    """Entreprises à plus de 25 km du centre."""

    if df is None or df.empty:
        return pd.DataFrame()

    d = preparer_donnees(df)

    d = d[d["distance_km"] > RAYON_MARRAKECH_KM].copy()

    d["distance_km"] = d["distance_km"].round(0)

    return d


# ==========================================
# EXPORT EXCEL (si openpyxl est installé)
# ==========================================

def vers_excel(df):
    """Retourne les octets d'un fichier .xlsx, ou None si
    openpyxl n'est pas installé."""

    try:

        import openpyxl  # noqa: F401

    except ImportError:

        return None

    tampon = io.BytesIO()

    with pd.ExcelWriter(
        tampon,
        engine="openpyxl"
    ) as ecrivain:

        df.to_excel(
            ecrivain,
            index=False,
            sheet_name="Entreprises"
        )

    return tampon.getvalue()