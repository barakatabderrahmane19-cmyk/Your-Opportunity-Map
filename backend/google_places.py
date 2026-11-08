import streamlit as st
import pandas as pd
import requests
import time

from backend.data_processing import (
    determine_subsector,
    nettoyer_donnees,
    donnees_simulation,
    RAW_FILE,
    CLEAN_FILE
)


# ============================================================
# CONFIGURATION
# ============================================================

GOOGLE_PLACES_URL = (
    "https://places.googleapis.com/"
    "v1/places:searchText"
)

MAX_RESULTS_PER_PAGE = 20
MAX_PAGES = 3


# ============================================================
# RECHERCHE GOOGLE PLACES AVEC PAGINATION
# ============================================================

def rechercher_google_places(
    api_key,
    query,
    max_results=20,
    max_pages=3
):
    """
    Recherche des entreprises avec Google Places API (New).

    Une page peut contenir au maximum 20 résultats.
    Grâce au nextPageToken, on peut récupérer
    les pages suivantes.

    Maximum utilisé ici :
    3 pages x 20 résultats = jusqu'à 60 résultats
    par requête.
    """

    if not api_key:
        st.error(
            "❌ Aucune clé Google Places API."
        )
        return []

    tous_les_resultats = []

    page_token = None

    for page in range(
        1,
        min(max_pages, 3) + 1
    ):

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "places.id,"
                "places.displayName,"
                "places.formattedAddress,"
                "places.location,"
                "places.types,"
                "places.websiteUri,"
                "places.internationalPhoneNumber,"
                "nextPageToken"
            )
        }

        body = {
            "textQuery": query,
            "pageSize": min(
                max_results,
                MAX_RESULTS_PER_PAGE
            ),
            "languageCode": "fr",
            "regionCode": "MA"
        }

        # Pour les pages 2 et 3
        if page_token:

            body["pageToken"] = page_token

        try:

            response = requests.post(
                GOOGLE_PLACES_URL,
                headers=headers,
                json=body,
                timeout=30
            )

            # ------------------------------------------------
            # ERREUR HTTP
            # ------------------------------------------------

            if response.status_code != 200:

                try:
                    error_data = response.json()
                except Exception:
                    error_data = {}

                message = (
                    error_data
                    .get("error", {})
                    .get(
                        "message",
                        response.text
                    )
                )

                st.error(
                    f"❌ Erreur Google Places "
                    f"(page {page}) : {message}"
                )

                break

            data = response.json()

            places = data.get(
                "places",
                []
            )

            # Ajouter les résultats
            tous_les_resultats.extend(
                places
            )

            # ------------------------------------------------
            # PAS DE PAGE SUIVANTE
            # ------------------------------------------------

            page_token = data.get(
                "nextPageToken"
            )

            if not page_token:

                break

            # ------------------------------------------------
            # Google peut nécessiter un petit délai
            # avant que le token soit utilisable.
            # ------------------------------------------------

            time.sleep(2)

        except requests.exceptions.Timeout:

            st.error(
                f"❌ Timeout pendant la page {page}."
            )

            break

        except requests.exceptions.RequestException as e:

            st.error(
                f"❌ Erreur de connexion : {e}"
            )

            break

        except Exception as e:

            st.error(
                f"❌ Erreur inattendue : {e}"
            )

            break

    return tous_les_resultats


# ============================================================
# TRANSFORMATION GOOGLE → DATAFRAME
# ============================================================

def transformer_places_en_dataframe(
    places
):

    lignes = []

    for place in places:

        place_id = place.get(
            "id",
            ""
        )

        display_name = place.get(
            "displayName",
            {}
        )

        nom = display_name.get(
            "text",
            "Nom non renseigné"
        )

        adresse = place.get(
            "formattedAddress",
            ""
        )

        location = place.get(
            "location",
            {}
        )

        latitude = location.get(
            "latitude"
        )

        longitude = location.get(
            "longitude"
        )

        types = place.get(
            "types",
            []
        )

        telephone = place.get(
            "internationalPhoneNumber",
            ""
        )

        site_web = place.get(
            "websiteUri",
            ""
        )

        sous_secteur = determine_subsector(
            nom,
            types
        )

        lignes.append(
            {
                "place_id": place_id,
                "nom": nom,
                "adresse": adresse,
                "telephone": telephone,
                "site_web": site_web,
                "sous_secteur": sous_secteur,
                "latitude": latitude,
                "longitude": longitude,
                "source": "Google Places"
            }
        )

    return pd.DataFrame(
        lignes
    )


# ============================================================
# SAUVEGARDE ET NETTOYAGE
# ============================================================

def sauvegarder_donnees(
    df_brut
):

    if (
        df_brut is None
        or df_brut.empty
    ):

        return pd.DataFrame()

    # --------------------------------------------------------
    # Suppression des doublons par place_id
    # --------------------------------------------------------

    if "place_id" in df_brut.columns:

        df_brut = df_brut.drop_duplicates(
            subset=["place_id"]
        )

    # --------------------------------------------------------
    # Nettoyage
    # --------------------------------------------------------

    df_clean = nettoyer_donnees(
        df_brut
    )

    # --------------------------------------------------------
    # Sauvegarde données brutes
    # --------------------------------------------------------

    df_brut.to_csv(
        RAW_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # Sauvegarde données nettoyées
    # --------------------------------------------------------

    df_clean.to_csv(
        CLEAN_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    return df_clean


# ============================================================
# RECHERCHE SIMPLE
# ============================================================

def collecter_entreprises_google(
    api_key,
    simulation=False,
    query="entreprises informatique Marrakech",
    max_results=20
):

    # --------------------------------------------------------
    # MODE SIMULATION
    # --------------------------------------------------------

    if simulation:

        st.info(
            "💡 Mode Simulation activé : "
            "aucune requête Google n'est envoyée."
        )

        df_sim = donnees_simulation()

        df_sim = nettoyer_donnees(
            df_sim
        )

        return df_sim, df_sim

    # --------------------------------------------------------
    # VÉRIFICATION CLÉ
    # --------------------------------------------------------

    if not api_key:

        st.error(
            "❌ Aucune clé Google Places "
            "n'a été fournie."
        )

        return None, None

    # --------------------------------------------------------
    # RECHERCHE
    # --------------------------------------------------------

    st.info(
        f"🔎 Recherche : {query}"
    )

    places = rechercher_google_places(
        api_key=api_key,
        query=query,
        max_results=max_results,
        max_pages=MAX_PAGES
    )

    if not places:

        st.warning(
            "❌ Aucun résultat trouvé."
        )

        return None, None

    # --------------------------------------------------------
    # TRANSFORMATION
    # --------------------------------------------------------

    df_brut = transformer_places_en_dataframe(
        places
    )

    if df_brut.empty:

        st.warning(
            "❌ Aucun résultat exploitable."
        )

        return None, None

    # --------------------------------------------------------
    # NOMBRE AVANT DOUBLONS
    # --------------------------------------------------------

    nombre_avant = len(
        df_brut
    )

    # --------------------------------------------------------
    # SUPPRESSION DOUBLONS
    # --------------------------------------------------------

    if "place_id" in df_brut.columns:

        df_brut = df_brut.drop_duplicates(
            subset=["place_id"]
        )

    nombre_apres = len(
        df_brut
    )

    doublons = (
        nombre_avant
        - nombre_apres
    )

    # --------------------------------------------------------
    # NETTOYAGE
    # --------------------------------------------------------

    df_clean = nettoyer_donnees(
        df_brut
    )

    # --------------------------------------------------------
    # SAUVEGARDE
    # --------------------------------------------------------

    df_brut.to_csv(
        RAW_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    df_clean.to_csv(
        CLEAN_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    st.success(
        f"✅ {nombre_apres} entreprise(s) "
        f"unique(s) trouvée(s)."
    )

    if doublons > 0:

        st.info(
            f"♻️ {doublons} doublon(s) supprimé(s)."
        )

    return df_brut, df_clean


# ============================================================
# RECHERCHE MULTI-CATEGORIES + QUARTIERS
# ============================================================

def collecter_entreprises_multi_requetes(
    api_key,
    requetes,
    max_results_par_requete=20
):

    if not api_key:

        st.error(
            "❌ Aucune clé Google Places API."
        )

        return None, None

    if not requetes:

        st.warning(
            "❌ Aucune requête de recherche."
        )

        return None, None

    # --------------------------------------------------------
    # STOCKAGE GLOBAL
    # --------------------------------------------------------

    tous_les_resultats = []

    # --------------------------------------------------------
    # PROGRESSION
    # --------------------------------------------------------

    progress_bar = st.progress(
        0
    )

    statut = st.empty()

    total = len(
        requetes
    )

    # --------------------------------------------------------
    # RECHERCHE DE CHAQUE REQUÊTE
    # --------------------------------------------------------

    for index, requete in enumerate(
        requetes,
        start=1
    ):

        statut.write(
            f"🔎 Recherche "
            f"{index}/{total} : "
            f"{requete}"
        )

        places = rechercher_google_places(
            api_key=api_key,
            query=requete,
            max_results=max_results_par_requete,
            max_pages=MAX_PAGES
        )

        tous_les_resultats.extend(
            places
        )

        progress_bar.progress(
            index / total
        )

    # --------------------------------------------------------
    # FIN RECHERCHE
    # --------------------------------------------------------

    statut.success(
        "✅ Toutes les recherches sont terminées."
    )

    if not tous_les_resultats:

        st.warning(
            "❌ Aucun résultat trouvé."
        )

        return None, None

    # --------------------------------------------------------
    # TRANSFORMATION
    # --------------------------------------------------------

    df_brut = transformer_places_en_dataframe(
        tous_les_resultats
    )

    if df_brut.empty:

        st.warning(
            "❌ Aucun résultat exploitable."
        )

        return None, None

    # --------------------------------------------------------
    # NOMBRE AVANT DOUBLONS
    # --------------------------------------------------------

    nombre_avant = len(
        df_brut
    )

    # --------------------------------------------------------
    # SUPPRESSION DOUBLONS
    # --------------------------------------------------------

    if "place_id" in df_brut.columns:

        df_brut = df_brut.drop_duplicates(
            subset=["place_id"]
        )

    nombre_apres = len(
        df_brut
    )

    doublons = (
        nombre_avant
        - nombre_apres
    )

    # --------------------------------------------------------
    # NETTOYAGE
    # --------------------------------------------------------

    df_clean = nettoyer_donnees(
        df_brut
    )

    # --------------------------------------------------------
    # SAUVEGARDE
    # --------------------------------------------------------

    df_brut.to_csv(
        RAW_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    df_clean.to_csv(
        CLEAN_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # RÉSULTATS
    # --------------------------------------------------------

    st.success(
        f"🎉 Recherche terminée ! "
        f"{nombre_apres} entreprises uniques trouvées."
    )

    st.info(
        f"📥 Résultats Google reçus : "
        f"{nombre_avant}"
    )

    if doublons > 0:

        st.info(
            f"♻️ Doublons supprimés : "
            f"{doublons}"
        )

    st.info(
        f"📊 Entreprises après nettoyage : "
        f"{len(df_clean)}"
    )

    return df_brut, df_clean


# ============================================================
# CATÉGORIES + QUARTIERS DE MARRAKECH
# ============================================================

def generer_requetes_marrakech():

    categories = [

        "entreprise informatique",

        "startup",

        "software",

        "développement logiciel",

        "agence web",

        "cybersécurité",

        "data science",

        "data analyst",

        "cloud",

        "IT consulting",

        "digital",

        "technologie",

        "télécommunication",

        "informatique",

        "services informatiques"

    ]

    quartiers = [

        "Marrakech",

        "Gueliz Marrakech",

        "Sidi Ghanem Marrakech",

        "Mhamid Marrakech",

        "Daoudiate Marrakech",

        "Semlalia Marrakech",

        "Hivernage Marrakech",

        "Agdal Marrakech",

        "Massira Marrakech",

        "Targa Marrakech",

        "Sidi Youssef Ben Ali Marrakech"

    ]

    requetes = []

    # --------------------------------------------------------
    # Catégories générales
    # --------------------------------------------------------

    for categorie in categories:

        requetes.append(
            f"{categorie} Marrakech"
        )

    # --------------------------------------------------------
    # Catégories + quartiers
    # --------------------------------------------------------

    for categorie in categories:

        for quartier in quartiers:

            requetes.append(
                f"{categorie} {quartier}"
            )

    # --------------------------------------------------------
    # Suppression des doublons de requêtes
    # --------------------------------------------------------

    requetes = list(
        dict.fromkeys(
            requetes
        )
    )

    return requetes
    