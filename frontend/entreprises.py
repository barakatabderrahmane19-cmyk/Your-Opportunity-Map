import streamlit as st
import pandas as pd
import html
import folium
from streamlit_folium import st_folium

from backend.google_places import (
    collecter_entreprises_google,
    collecter_entreprises_multi_requetes,
    generer_requetes_marrakech
)

from backend.data_processing import (
    charger_donnees,
    charger_donnees_brutes,
    url_propre,
    whatsapp_url
)

from backend.opportunities import (
    ajouter_si_absent,
    entreprises_suivies,
    normaliser_nom
)

from datetime import date


# ============================================================
# LISTES DE RECHERCHE
# ============================================================

CATEGORIES = [
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

QUARTIERS = [
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


# ============================================================
# ICÔNES DES SOUS-SECTEURS (affichage du tableau)
# ============================================================

ICONES_SECTEURS = {
    "Informatique": "💻",
    "Web / Internet": "🌐",
    "Informatique / Hardware": "🔧",
    "Technologie / Digital": "📱",
    "Développement logiciel": "👨‍💻",
    "Télécom / Réseaux": "📡",
    "Data / Cloud / Base de données": "☁️",
    "Cybersécurité": "🔒"
}


# ============================================================
# APPLICATION ENTREPRISES
# ============================================================

def afficher_entreprises():

    st.header(
        " Entreprises informatiques à Marrakech"
    )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    st.sidebar.subheader(
        " Configuration"
    )

    simulation = st.sidebar.checkbox(
        "Mode simulation",
        value=True
    )

    api_key = ""

    if not simulation:

        api_key = st.sidebar.text_input(
            "Google Places API Key",
            type="password"
        )

    st.sidebar.markdown("---")

    # ========================================================
    # RECHERCHE SIMPLE
    # ========================================================

    st.subheader(
        "🔎 Recherche personnalisée"
    )

    query = st.text_input(
        "Recherche personnalisée",
        value="entreprises informatique Marrakech"
    )

    max_results = st.slider(
        "Résultats par page",
        min_value=5,
        max_value=20,
        value=20
    )

    # ========================================================
    # RECHERCHE AVANCÉE
    # ========================================================

    st.divider()

    st.subheader(
        " Recherche avancée"
    )

    st.write(
        "Sélectionnez les catégories et les quartiers "
        "à rechercher."
    )

    # ========================================================
    # CATÉGORIES
    # ========================================================

    categories_selectionnees = st.multiselect(
        " Catégories",
        options=CATEGORIES,
        default=[
            "entreprise informatique",
            "startup",
            "développement logiciel",
            "agence web",
            "data analyst"
        ]
    )

    # ========================================================
    # QUARTIERS
    # ========================================================

    quartiers_selectionnes = st.multiselect(
        "📍 Quartiers",
        options=QUARTIERS,
        default=[
            "Marrakech",
            "Gueliz Marrakech",
            "Sidi Ghanem Marrakech",
            "Targa Marrakech",
            "Semlalia Marrakech"
        ]
    )

    # ========================================================
    # RÉSUMÉ DES RECHERCHES
    # ========================================================

    nombre_categories = len(
        categories_selectionnees
    )

    nombre_quartiers = len(
        quartiers_selectionnes
    )

    nombre_requetes = (
        nombre_categories
        * nombre_quartiers
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            " Catégories",
            nombre_categories
        )

    with col2:

        st.metric(
            "📍 Quartiers",
            nombre_quartiers
        )

    with col3:

        st.metric(
            " Recherches",
            nombre_requetes
        )

    # ========================================================
    # AVERTISSEMENT SI BEAUCOUP DE REQUÊTES
    # ========================================================

    if nombre_requetes > 30:

        st.warning(
            "⚠️ Vous avez sélectionné beaucoup de recherches. "
            "Chaque recherche peut utiliser plusieurs pages "
            "Google Places."
        )

    # ========================================================
    # APERÇU DES REQUÊTES
    # ========================================================

    requetes_selectionnees = []

    for categorie in categories_selectionnees:

        for quartier in quartiers_selectionnes:

            requete = (
                f"{categorie} {quartier}"
            )

            requetes_selectionnees.append(
                requete
            )

    if requetes_selectionnees:

        with st.expander(
            " Voir les requêtes qui seront lancées"
        ):

            for requete in requetes_selectionnees:

                st.write(
                    f"• {requete}"
                )

    # ========================================================
    # BOUTON RECHERCHE AVANCÉE
    # ========================================================

    if st.button(
        " Lancer la recherche avancée",
        type="primary",
        use_container_width=True
    ):

        if simulation:

            st.info(
                " Mode simulation activé."
            )

            df_brut, df_clean = (
                collecter_entreprises_google(
                    api_key=api_key,
                    simulation=True,
                    query=query,
                    max_results=max_results
                )
            )

        else:

            if not api_key:

                st.error(
                    " Veuillez entrer votre clé "
                    "Google Places API."
                )

                return

            if not categories_selectionnees:

                st.error(
                    " Sélectionnez au moins "
                    "une catégorie."
                )

                return

            if not quartiers_selectionnes:

                st.error(
                    "Sélectionnez au moins "
                    "un quartier."
                )

                return

            st.info(
                f" {nombre_requetes} recherche(s) "
                "vont être effectuée(s)."
            )

            df_brut, df_clean = (
                collecter_entreprises_multi_requetes(
                    api_key=api_key,
                    requetes=requetes_selectionnees,
                    max_results_par_requete=max_results
                )
            )

        # ----------------------------------------------------
        # SESSION STATE
        # ----------------------------------------------------

        if df_brut is not None:

            st.session_state[
                "df_brut"
            ] = df_brut

        if df_clean is not None:

            st.session_state[
                "df_clean"
            ] = df_clean

    # ========================================================
    # CHARGEMENT DES DONNÉES
    # ========================================================

    df_clean = st.session_state.get(
        "df_clean",
        charger_donnees()
    )

    df_brut = st.session_state.get(
        "df_brut",
        charger_donnees_brutes()
    )

    if (
        df_clean is None
        or df_clean.empty
    ):

        st.info(
            "ℹ Aucune entreprise disponible. "
            "Lancez une recherche."
        )

        return

    # ========================================================
    # RÉSUMÉ
    # ========================================================

    st.divider()

    st.subheader(
        " Résumé"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Entreprises",
            len(df_clean)
        )

    with col2:

        if "sous_secteur" in df_clean.columns:

            nombre_secteurs = (
                df_clean[
                    "sous_secteur"
                ]
                .nunique()
            )

        else:

            nombre_secteurs = 0

        st.metric(
            " Sous-secteurs",
            nombre_secteurs
        )

    with col3:

        if "telephone" in df_clean.columns:

            nombre_telephones = (
                df_clean[
                    "telephone"
                ]
                .replace(
                    "Non renseigné",
                    ""
                )
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )

        else:

            nombre_telephones = 0

        st.metric(
            " Téléphones",
            nombre_telephones
        )

    # ========================================================
    # FILTRE
    # ========================================================

    st.divider()

    st.subheader(
        "🔍 Filtrer les entreprises"
    )

    recherche = st.text_input(
        "Rechercher par nom ou adresse",
        key="recherche_entreprise"
    )

    df_filtre = df_clean.copy()

    if recherche:

        texte = (
            df_filtre[
                "nom"
            ]
            .fillna("")
            .astype(str)
            + " "
            + df_filtre[
                "adresse"
            ]
            .fillna("")
            .astype(str)
        )

        masque = texte.str.contains(
            recherche,
            case=False,
            na=False
        )

        df_filtre = df_filtre[
            masque
        ]

    # ========================================================
    # FILTRE SOUS-SECTEUR
    # ========================================================

    if "sous_secteur" in df_filtre.columns:

        secteurs = sorted(
            df_filtre[
                "sous_secteur"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        secteur_selectionne = st.selectbox(
            " Sous-secteur",
            ["Tous"] + secteurs
        )

        if secteur_selectionne != "Tous":

            df_filtre = df_filtre[
                df_filtre[
                    "sous_secteur"
                ]
                == secteur_selectionne
            ]

    st.write(
        f"**{len(df_filtre)} entreprise(s) affichée(s)**"
    )

    # ========================================================
    # AJOUTER AU SUIVI
    # ========================================================

    st.subheader(
        "➕ Ajouter une entreprise au suivi"
    )

    if df_filtre.empty:

        st.info(
            "Aucune entreprise à ajouter avec ce filtre."
        )

    else:

        col_nom, col_bouton = st.columns([3, 1])

        with col_nom:

            nom_choisi = st.selectbox(
                "Entreprise à suivre "
                "(tapez pour rechercher)",
                df_filtre["nom"].tolist(),
                key="entreprise_a_suivre"
            )

        with col_bouton:

            st.write("")
            st.write("")

            ajouter = st.button(
                "📌 Ajouter au suivi",
                use_container_width=True
            )

        if ajouter:

            ligne = df_filtre[
                df_filtre["nom"] == nom_choisi
            ].iloc[0]

            notes = (
                f"Tél : {ligne.get('telephone', '')} | "
                f"Site : {ligne.get('site_web', '')} | "
                f"Adresse : {ligne.get('adresse', '')}"
            )

            ajoutee = ajouter_si_absent(
                entreprise=nom_choisi,
                poste="Stage",
                type_opportunite="Stage",
                source="Google",
                lien="",
                date=str(date.today()),
                statut="À contacter",
                notes=notes
            )

            if ajoutee:

                st.success(
                    f"✅ {nom_choisi} ajoutée au suivi "
                    "(statut : À contacter). "
                    "Retrouvez-la dans l'onglet Opportunités."
                )

            else:

                st.warning(
                    f"⚠️ {nom_choisi} est déjà dans votre suivi."
                )

    # ========================================================
    # TABLEAU
    # ========================================================

    st.subheader(
        "Liste des entreprises"
    )

    # --- Recherche rapide dans le tableau
    recherche = st.text_input(
        "🔎 Rechercher dans le tableau",
        placeholder="Nom, adresse ou secteur..."
    )

    df_table = df_filtre.copy()

    if recherche.strip():

        masque = pd.Series(
            False,
            index=df_table.index
        )

        for colonne in ["nom", "adresse", "sous_secteur"]:

            if colonne in df_table.columns:

                masque = masque | (
                    df_table[colonne]
                    .astype(str)
                    .str.contains(
                        recherche.strip(),
                        case=False,
                        regex=False,
                        na=False
                    )
                )

        df_table = df_table[masque]

    st.caption(
        f"{len(df_table)} entreprise(s) dans le tableau"
    )

    # --- Construction du tableau
    deja_suivies = entreprises_suivies()

    df_affichage = pd.DataFrame()

    df_affichage["suivi"] = df_table["nom"].apply(
        lambda n: "✅"
        if normaliser_nom(n) in deja_suivies
        else ""
    )

    df_affichage["nom"] = df_table["nom"]

    if "sous_secteur" in df_table.columns:

        df_affichage["sous_secteur"] = (
            df_table["sous_secteur"].apply(
                lambda x: ICONES_SECTEURS.get(x, "🖥️")
                + " "
                + str(x)
            )
        )

    if "telephone" in df_table.columns:

        df_affichage["telephone"] = df_table["telephone"]

        df_affichage["whatsapp"] = (
            df_table["telephone"].apply(whatsapp_url)
        )

    if "site_web" in df_table.columns:

        df_affichage["site_web"] = (
            df_table["site_web"].apply(url_propre)
        )

    if (
        "latitude" in df_table.columns
        and "longitude" in df_table.columns
    ):

        df_affichage["itineraire"] = df_table.apply(
            lambda r: (
                "https://www.google.com/maps/search/"
                f"?api=1&query={r['latitude']},{r['longitude']}"
            )
            if pd.notna(r["latitude"])
            and pd.notna(r["longitude"])
            else None,
            axis=1
        )

    if "adresse" in df_table.columns:

        df_affichage["adresse"] = df_table["adresse"]

    st.dataframe(
        df_affichage,
        use_container_width=True,
        hide_index=True,
        height=560,
        column_config={
            "suivi": st.column_config.TextColumn(
                "Suivi",
                width="small",
                help="✅ = déjà dans votre suivi"
            ),
            "nom": st.column_config.TextColumn(
                " Entreprise",
                width="large"
            ),
            "sous_secteur": st.column_config.TextColumn(
                " Secteur",
                width="medium"
            ),
            "telephone": st.column_config.TextColumn(
                " Téléphone",
                width="medium"
            ),
            "whatsapp": st.column_config.LinkColumn(
                " WhatsApp",
                display_text=" Écrire",
                width="small"
            ),
            "site_web": st.column_config.LinkColumn(
                " Site web",
                display_text="🔗 Ouvrir le site",
                width="medium"
            ),
            "itineraire": st.column_config.LinkColumn(
                "📍 Carte",
                display_text="📍 Voir sur Maps",
                width="medium"
            ),
            "adresse": st.column_config.TextColumn(
                " Adresse",
                width="large"
            )
        }
    )

    # ========================================================
    # TÉLÉCHARGEMENT
    # ========================================================

    st.download_button(
        label="⬇Télécharger les données nettoyées",
        data=df_filtre.to_csv(
            index=False,
            encoding="utf-8-sig"
        ),
        file_name="entreprises_marrakech.csv",
        mime="text/csv"
    )

    # ========================================================
    # CARTE
    # ========================================================

    st.divider()

    st.subheader(
        " 📍 Carte des entreprises"
    )

    if (
        "latitude" in df_filtre.columns
        and "longitude" in df_filtre.columns
    ):

        df_map = df_filtre.dropna(
            subset=[
                "latitude",
                "longitude"
            ]
        )

        if not df_map.empty:

            latitude_centre = (
                df_map[
                    "latitude"
                ].mean()
            )

            longitude_centre = (
                df_map[
                    "longitude"
                ].mean()
            )

            carte = folium.Map(
                location=[
                    latitude_centre,
                    longitude_centre
                ],
                zoom_start=12
            )

            for _, row in df_map.iterrows():

                nom = html.escape(
                    str(
                        row.get(
                            "nom",
                            "📍"
                        )
                    )
                )

                adresse = html.escape(
                    str(
                        row.get(
                            "adresse",
                            "📍"
                        )
                    )
                )

                telephone = html.escape(
                    str(
                        row.get(
                            "telephone",
                            "📍"
                        )
                    )
                )

                secteur = html.escape(
                    str(
                        row.get(
                            "sous_secteur",
                            "📍"
                        )
                    )
                )

                url_site = url_propre(
                    row.get("site_web")
                )

                if url_site:

                    site_web = (
                        '<a href="'
                        + html.escape(url_site, quote=True)
                        + '" target="_blank" '
                        'rel="noopener noreferrer">'
                        "🔗 Ouvrir le site</a>"
                    )

                else:

                    site_web = "Non renseigné"

                popup_html = f"""
                <div style="width:250px">

                    <h4>{nom}</h4>

                    <p>
                        <b>Adresse :</b><br>
                        {adresse}
                    </p>

                    <p>
                        <b>Téléphone :</b><br>
                        {telephone}
                    </p>

                    <p>
                        <b>Sous-secteur :</b><br>
                        {secteur}
                    </p>

                    <p>
                        <b>Site web :</b><br>
                        {site_web}
                    </p>

                </div>
                """

                folium.CircleMarker(
                    location=[
                        row["latitude"],
                        row["longitude"]
                    ],
                    radius=6,
                    color="#1F2A44",
                    weight=1,
                    fill=True,
                    fill_color="#E4572E",
                    fill_opacity=0.85,
                    popup=folium.Popup(
                        popup_html,
                        max_width=300
                    ),
                    tooltip=nom
                ).add_to(carte)

            st_folium(
                carte,
                width=None,
                height=500
            )

        else:

            st.warning(
                " Aucune coordonnée géographique disponible."
            )

    # ========================================================
    # DONNÉES BRUTES
    # ========================================================

    st.divider()

    st.subheader(
        " Données brutes"
    )

    if (
        df_brut is not None
        and not df_brut.empty
    ):

        with st.expander(
            "Afficher les données brutes"
        ):

            st.dataframe(
                df_brut,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                label="⬇ Télécharger les données brutes",
                data=df_brut.to_csv(
                    index=False,
                    encoding="utf-8-sig"
                ),
                file_name="entreprises_brutes.csv",
                mime="text/csv"
            )