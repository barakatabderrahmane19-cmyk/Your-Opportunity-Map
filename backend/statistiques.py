import re
import numpy as np
import pandas as pd

from backend.Cv_matching import normaliser_texte
from backend.opportunities import STATUTS


# ==========================================
# CONSTANTES
# ==========================================

# Centre de Marrakech (place Jemaa el-Fna)
CENTRE_LAT = 31.6258
CENTRE_LON = -7.9891

# Au-delà : entreprise hors Marrakech (Agadir, Ben Guerir...)
RAYON_MARRAKECH_KM = 25

ORDRE_ZONES = [
    "0-2 km (centre)",
    "2-5 km",
    "5-10 km",
    "10-25 km",
    "> 25 km (hors Marrakech)"
]

# mot-clé (sans accent) -> quartier affiché
QUARTIERS = {
    "gueliz": "Guéliz",
    "hivernage": "Hivernage",
    "medina": "Médina",
    "jemaa": "Médina",
    "sidi ghanem": "Sidi Ghanem",
    "massira": "Massira",
    "daoudiate": "Daoudiate",
    "targa": "Targa",
    "azli": "Azli",
    "semlalia": "Semlalia",
    "mhamid": "M'Hamid",
    "m'hamid": "M'Hamid",
    "menara": "Ménara",
    "nakhil": "Annakhil",
    "palmeraie": "Palmeraie",
    "el manar": "Al Manar",
    "al manar": "Al Manar",
    "al anbar": "Al Anbar",
    "route de casablanca": "Route de Casablanca",
    "route de fes": "Route de Fès"
}

MOTS_IGNORES = {
    "marrakech", "marrakesh", "maroc", "morocco", "marrakchi",
    "les", "des", "pour", "avec", "dans", "sur", "par", "aux",
    "the", "and", "your", "centre", "center", "sarl", "mar",
    "plus", "tout", "votre", "vos", "notre", "nos"
}


# ==========================================
# PRÉPARATION DES DONNÉES ENTREPRISES
# ==========================================

def _distance_km(lat, lon):
    """Distance (haversine) au centre de Marrakech."""

    lat = np.radians(lat.astype(float))
    lon = np.radians(lon.astype(float))

    lat0 = np.radians(CENTRE_LAT)
    lon0 = np.radians(CENTRE_LON)

    a = (
        np.sin((lat - lat0) / 2) ** 2
        + np.cos(lat0) * np.cos(lat)
        * np.sin((lon - lon0) / 2) ** 2
    )

    return 6371 * 2 * np.arcsin(np.sqrt(a))


def _quartier(adresse):

    texte = normaliser_texte(adresse)

    for mot, quartier in QUARTIERS.items():

        if mot in texte:
            return quartier

    return "Non précisé"


def _est_renseigne(valeur):

    return str(valeur).strip() not in (
        "", "Non renseigné", "nan", "None"
    )


def preparer_donnees(df):
    """Ajoute les colonnes utiles aux graphiques :
    distance_km, zone, quartier, a_site, a_tel, contact."""

    d = df.copy()

    if "latitude" in d.columns and "longitude" in d.columns:

        lat = pd.to_numeric(d["latitude"], errors="coerce")
        lon = pd.to_numeric(d["longitude"], errors="coerce")

        d["distance_km"] = _distance_km(lat, lon)

    else:

        d["distance_km"] = np.nan

    d["zone"] = pd.cut(
        d["distance_km"],
        bins=[-1, 2, 5, 10, RAYON_MARRAKECH_KM, np.inf],
        labels=ORDRE_ZONES
    ).astype(object)

    d["zone"] = d["zone"].where(
        d["distance_km"].notna(),
        "Position inconnue"
    )

    d["quartier"] = d.get(
        "adresse",
        pd.Series("", index=d.index)
    ).apply(_quartier)

    d["a_site"] = d.get(
        "site_web",
        pd.Series("", index=d.index)
    ).apply(_est_renseigne)

    d["a_tel"] = d.get(
        "telephone",
        pd.Series("", index=d.index)
    ).apply(_est_renseigne)

    def _contact(r):

        if r["a_site"] and r["a_tel"]:
            return "Site + téléphone"

        if r["a_site"]:
            return "Site seulement"

        if r["a_tel"]:
            return "Téléphone seulement"

        return "Aucun contact"

    d["contact"] = d.apply(_contact, axis=1)

    return d


# ==========================================
# AGRÉGATIONS
# ==========================================

def repartition(df, colonne, ordre=None):
    """Tableau [colonne, nombre, pourcentage]."""

    comptes = (
        df[colonne]
        .value_counts()
        .rename_axis(colonne)
        .reset_index(name="nombre")
    )

    if ordre:

        comptes[colonne] = pd.Categorical(
            comptes[colonne],
            categories=ordre,
            ordered=True
        )

        comptes = comptes.sort_values(colonne)

        comptes[colonne] = comptes[colonne].astype(str)

    total = comptes["nombre"].sum()

    comptes["pourcentage"] = (
        (comptes["nombre"] / total * 100).round(1)
        if total else 0
    )

    return comptes.reset_index(drop=True)


def pourcentage_site_par_secteur(df):
    """% d'entreprises avec site web, par sous-secteur."""

    if "sous_secteur" not in df.columns or df.empty:
        return pd.DataFrame(
            columns=["sous_secteur", "pourcentage", "nombre"]
        )

    g = df.groupby("sous_secteur").agg(
        nombre=("a_site", "size"),
        avec_site=("a_site", "sum")
    ).reset_index()

    g["pourcentage"] = (
        g["avec_site"] / g["nombre"] * 100
    ).round(1)

    return g[["sous_secteur", "pourcentage", "nombre"]]


def mots_frequents(df, n=15):
    """Mots les plus fréquents dans les noms d'entreprises."""

    compteur = {}

    for nom in df["nom"].dropna():

        texte = normaliser_texte(nom)

        for mot in set(re.findall(r"[a-z0-9]+", texte)):

            if len(mot) < 4 or mot in MOTS_IGNORES:
                continue

            compteur[mot] = compteur.get(mot, 0) + 1

    resultat = (
        pd.Series(compteur, dtype="int64")
        .sort_values(ascending=False)
        .head(n)
    )

    return pd.DataFrame(
        {
            "mot": resultat.index,
            "nombre": resultat.values
        }
    )


# ==========================================
# SUIVI DES OPPORTUNITÉS
# ==========================================

def stats_suivi(df_opp):
    """Retourne (par_statut, par_semaine, par_source, par_type)."""

    vide = pd.DataFrame()

    if df_opp is None or df_opp.empty:
        return vide, vide, vide, vide

    par_statut = (
        df_opp["statut"]
        .value_counts()
        .reindex(STATUTS, fill_value=0)
        .rename_axis("statut")
        .reset_index(name="nombre")
    )

    dates = pd.to_datetime(
        df_opp["date"],
        errors="coerce"
    ).dropna()

    if dates.empty:

        par_semaine = vide

    else:

        par_semaine = (
            dates.dt.to_period("W")
            .dt.start_time
            .value_counts()
            .sort_index()
            .rename_axis("semaine")
            .reset_index(name="nombre")
        )

    par_source = repartition(df_opp, "source")

    par_type = repartition(df_opp, "type")

    return par_statut, par_semaine, par_source, par_type