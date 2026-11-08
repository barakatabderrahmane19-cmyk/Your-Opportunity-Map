import os
import pandas as pd


# ==========================================
# CHEMINS (même logique que data_processing.py)
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(BASE_DIR, "data")

OPPORTUNITY_FILE = os.path.join(
    DATA_DIR,
    "opportunites_marrakech.csv"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ==========================================
# LISTES DE VALEURS (partagées avec le frontend)
# ==========================================

COLONNES = [
    "entreprise",
    "poste",
    "type",
    "source",
    "lien",
    "date",
    "statut",
    "notes"
]

TYPES = [
    "Stage",
    "PFE",
    "Alternance",
    "Emploi",
    "Freelance",
    "Autre"
]

SOURCES = [
    "LinkedIn",
    "Google",
    "Indeed",
    "ReKrute",
    "Site de l'entreprise",
    "Autre"
]

STATUTS = [
    "À contacter",
    "Candidature envoyée",
    "Entretien",
    "Acceptée",
    "Refusée"
]


# ==========================================
# OUTILS
# ==========================================

def normaliser_nom(nom):
    """Pour comparer deux noms d'entreprise sans tenir
    compte des majuscules ni des espaces en trop."""

    if nom is None:
        return ""

    return " ".join(
        str(nom).lower().split()
    )


# ==========================================
# CHARGER
# ==========================================

def charger_opportunites():

    colonnes = COLONNES

    if not os.path.exists(
        OPPORTUNITY_FILE
    ):
        return pd.DataFrame(
            columns=colonnes
        )

    try:

        df = pd.read_csv(
            OPPORTUNITY_FILE,
            encoding="utf-8-sig"
        )

        for colonne in colonnes:

            if colonne not in df.columns:
                df[colonne] = ""

        # Évite d'afficher "nan" dans les cases vides
        df = df[colonnes].fillna("")

        return df.reset_index(
            drop=True
        )

    except Exception:

        return pd.DataFrame(
            columns=colonnes
        )


# ==========================================
# SAUVEGARDER (NOUVEAU)
# ==========================================

def sauvegarder_opportunites(df):
    """Écrase le CSV avec le DataFrame complet."""

    df = df.copy()

    for colonne in COLONNES:

        if colonne not in df.columns:
            df[colonne] = ""

    df = df[COLONNES].fillna("")

    df.to_csv(
        OPPORTUNITY_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    return df


# ==========================================
# AJOUTER
# ==========================================

def ajouter_opportunite(
    entreprise,
    poste,
    type_opportunite,
    source,
    lien,
    date,
    statut,
    notes
):

    nouvelle_ligne = pd.DataFrame(
        [
            {
                "entreprise": entreprise,
                "poste": poste,
                "type": type_opportunite,
                "source": source,
                "lien": lien,
                "date": date,
                "statut": statut,
                "notes": notes
            }
        ]
    )

    df = charger_opportunites()

    df = pd.concat(
        [
            df,
            nouvelle_ligne
        ],
        ignore_index=True
    )

    df.to_csv(
        OPPORTUNITY_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    return df


# ==========================================
# LIEN AVEC LES ENTREPRISES (NOUVEAU)
# ==========================================

def entreprises_suivies():
    """Ensemble des noms d'entreprises déjà suivies
    (normalisés)."""

    df = charger_opportunites()

    return {
        normaliser_nom(nom)
        for nom in df["entreprise"]
        if normaliser_nom(nom)
    }


def ajouter_si_absent(
    entreprise,
    poste,
    type_opportunite,
    source,
    lien,
    date,
    statut,
    notes
):
    """Ajoute l'opportunité seulement si l'entreprise
    n'est pas déjà suivie. Retourne True si ajoutée,
    False si elle existait déjà."""

    if normaliser_nom(entreprise) in entreprises_suivies():
        return False

    ajouter_opportunite(
        entreprise=entreprise,
        poste=poste,
        type_opportunite=type_opportunite,
        source=source,
        lien=lien,
        date=date,
        statut=statut,
        notes=notes
    )

    return True