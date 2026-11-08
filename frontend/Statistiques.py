import streamlit as st
import pandas as pd
import altair as alt

from backend.data_processing import charger_donnees

from backend.opportunities import (
    charger_opportunites,
    entreprises_suivies,
    normaliser_nom,
    STATUTS
)

from backend.statistiques import (
    preparer_donnees,
    repartition,
    pourcentage_site_par_secteur,
    mots_frequents,
    stats_suivi,
    ORDRE_ZONES,
    CENTRE_LAT,
    CENTRE_LON,
    RAYON_MARRAKECH_KM
)


COULEUR = "#4C78A8"


# ============================================================
# GRAPHIQUES RÉUTILISABLES
# ============================================================

def barres_horizontales(df, categorie, valeur, titre_valeur,
                        ordre=None, hauteur=None):
    """Barres horizontales avec la valeur écrite au bout."""

    if hauteur is None:
        hauteur = max(120, 32 * len(df))

    tri = ordre if ordre else "-x"

    base = alt.Chart(df).encode(
        y=alt.Y(
            f"{categorie}:N",
            sort=tri,
            title=None,
            axis=alt.Axis(labelLimit=260)
        ),
        x=alt.X(
            f"{valeur}:Q",
            title=titre_valeur
        ),
        tooltip=[
            alt.Tooltip(f"{categorie}:N", title="Catégorie"),
            alt.Tooltip(f"{valeur}:Q", title=titre_valeur)
        ]
    )

    graphique = (
        base.mark_bar(color=COULEUR)
        + base.mark_text(
            align="left",
            dx=4
        ).encode(
            text=f"{valeur}:Q"
        )
    ).properties(height=hauteur)

    st.altair_chart(
        graphique,
        use_container_width=True
    )


def donut(df, categorie, valeur="nombre"):
    """Graphique en anneau."""

    graphique = alt.Chart(df).mark_arc(
        innerRadius=60
    ).encode(
        theta=alt.Theta(f"{valeur}:Q"),
        color=alt.Color(
            f"{categorie}:N",
            legend=alt.Legend(
                title=None,
                orient="bottom"
            )
        ),
        tooltip=[
            alt.Tooltip(f"{categorie}:N", title="Catégorie"),
            alt.Tooltip(f"{valeur}:Q", title="Nombre")
        ]
    ).properties(height=300)

    st.altair_chart(
        graphique,
        use_container_width=True
    )


# ============================================================
# ONGLET STATISTIQUES
# ============================================================

def afficher_statistiques():

    st.header(" Statistiques et visualisations")

    st.write(
        "Vue d'ensemble des entreprises collectées, "
        "de votre suivi et de votre profil CV."
    )

    df_brut = charger_donnees()

    if df_brut is None or df_brut.empty:

        st.info(
            "ℹ️ Aucune entreprise collectée. "
            "Lancez d'abord une collecte dans l'onglet Entreprises."
        )

        return

    df_tout = preparer_donnees(df_brut)

    # ============================================================
    # FILTRES
    # ============================================================

    col_f1, col_f2 = st.columns([3, 2])

    with col_f1:

        secteurs = sorted(
            df_tout["sous_secteur"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        secteurs_choisis = st.multiselect(
            "🏷️ Secteurs à analyser (vide = tous)",
            secteurs,
            key="stats_secteurs"
        )

    with col_f2:

        st.write("")

        marrakech_seulement = st.checkbox(
            f"📍 Marrakech seulement "
            f"(≤ {RAYON_MARRAKECH_KM} km du centre)",
            value=True,
            key="stats_marrakech"
        )

    df = df_tout.copy()

    nb_hors = int(
        (df["distance_km"] > RAYON_MARRAKECH_KM).sum()
    )

    if secteurs_choisis:

        df = df[
            df["sous_secteur"].isin(secteurs_choisis)
        ]

    if marrakech_seulement:

        df = df[
            ~(df["distance_km"] > RAYON_MARRAKECH_KM)
        ]

    if df.empty:

        st.warning(
            "⚠️ Aucune entreprise avec ces filtres."
        )

        return

    if nb_hors:

        st.caption(
            f"ℹ️ {nb_hors} entreprise(s) de votre base sont "
            f"situées à plus de {RAYON_MARRAKECH_KM} km de "
            "Marrakech (Agadir, Ben Guerir…)."
        )

    # ============================================================
    # CHIFFRES CLÉS
    # ============================================================

    suivies = entreprises_suivies()

    nb_suivies = int(
        df["nom"].apply(
            lambda n: normaliser_nom(n) in suivies
        ).sum()
    )

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric(" Entreprises", len(df))

    k2.metric(
        " Avec site web",
        f"{df['a_site'].mean() * 100:.0f} %"
    )

    k3.metric(
        " Avec téléphone",
        f"{df['a_tel'].mean() * 100:.0f} %"
    )

    k4.metric(
        " Secteurs",
        df["sous_secteur"].nunique()
    )

    k5.metric("📌 Déjà suivies", nb_suivies)

    st.divider()

    # ============================================================
    # SECTEURS + CONTACTS
    # ============================================================

    c1, c2 = st.columns(2)

    with c1:

        st.subheader(" Répartition par secteur")

        barres_horizontales(
            repartition(df, "sous_secteur"),
            "sous_secteur",
            "nombre",
            "Nombre d'entreprises"
        )

    with c2:

        st.subheader(" Possibilités de contact")

        donut(
            repartition(df, "contact"),
            "contact"
        )

        st.caption(
            "Les entreprises « Téléphone seulement » se "
            "contactent mieux par appel ou WhatsApp."
        )

    st.divider()

    # ============================================================
    # LOCALISATION
    # ============================================================

    c3, c4 = st.columns(2)

    with c3:

        st.subheader(" Distance du centre-ville")

        zones = repartition(df, "zone", ORDRE_ZONES)

        barres_horizontales(
            zones,
            "zone",
            "nombre",
            "Nombre d'entreprises",
            ordre=ORDRE_ZONES
        )

    with c4:

        st.subheader(" Quartiers identifiés")

        quartiers = repartition(df, "quartier")

        non_precise = int(
            quartiers.loc[
                quartiers["quartier"] == "Non précisé",
                "nombre"
            ].sum()
        )

        quartiers = quartiers[
            quartiers["quartier"] != "Non précisé"
        ].head(10)

        if quartiers.empty:

            st.info("Aucun quartier identifiable.")

        else:

            barres_horizontales(
                quartiers,
                "quartier",
                "nombre",
                "Nombre d'entreprises"
            )

        st.caption(
            f"{non_precise} adresse(s) sans quartier précisé "
            "(non affichées)."
        )

    st.divider()

    # ============================================================
    # QUALITÉ + MOTS FRÉQUENTS
    # ============================================================

    c5, c6 = st.columns(2)

    with c5:

        st.subheader(" % d'entreprises avec site web")

        pct = pourcentage_site_par_secteur(df)

        barres_horizontales(
            pct,
            "sous_secteur",
            "pourcentage",
            "% avec site web"
        )

    with c6:

        st.subheader(" Mots les plus fréquents dans les noms")

        mots = mots_frequents(df, 12)

        if mots.empty:

            st.info("Pas assez de données.")

        else:

            barres_horizontales(
                mots,
                "mot",
                "nombre",
                "Nombre d'entreprises"
            )

        st.caption(
            "Astuce : beaucoup de noms contiennent « agence » "
            "ou « communication » : ce sont plutôt des agences "
            "web/marketing que des éditeurs de logiciels."
        )

    st.divider()

    # ============================================================
    # CARTE DE CHALEUR
    # ============================================================

    st.subheader(" Où sont concentrées les entreprises ?")

    df_carte = df.dropna(
        subset=["latitude", "longitude"]
    )

    if marrakech_seulement is False:

        df_carte = df_carte[
            df_carte["distance_km"] <= 60
        ]

    if df_carte.empty:

        st.info("Aucune coordonnée disponible.")

    else:

        points = df_carte[
            ["nom", "latitude", "longitude"]
        ].copy()

        points["latitude"] = points["latitude"].astype(float)
        points["longitude"] = points["longitude"].astype(float)

        try:

            import pydeck as pdk

            chaleur = pdk.Layer(
                "HeatmapLayer",
                data=points,
                get_position="[longitude, latitude]",
                radius_pixels=45,
                intensity=1.5,
                threshold=0.03,
                opacity=0.85
            )

            pastilles = pdk.Layer(
                "ScatterplotLayer",
                data=points,
                get_position="[longitude, latitude]",
                get_radius=40,
                get_fill_color=[255, 255, 255, 170],
                pickable=True
            )

            st.pydeck_chart(
                pdk.Deck(
                    map_style=None,
                    initial_view_state=pdk.ViewState(
                        latitude=CENTRE_LAT,
                        longitude=CENTRE_LON,
                        zoom=11,
                        pitch=0
                    ),
                    layers=[chaleur, pastilles],
                    tooltip={"text": "{nom}"}
                )
            )

        except Exception:

            # Solution de secours : simple carte de points
            st.map(
                points.rename(
                    columns={
                        "latitude": "lat",
                        "longitude": "lon"
                    }
                )[["lat", "lon"]]
            )

        st.caption(
            "Les zones rouges/jaunes concentrent le plus "
            "d'entreprises (points blancs = une entreprise, "
            "survolez-les pour voir le nom)."
        )

    st.divider()

    # ============================================================
    # MON SUIVI
    # ============================================================

    st.subheader(" Mon suivi de candidatures")

    par_statut, par_semaine, par_source, par_type = stats_suivi(
        charger_opportunites()
    )

    if par_statut.empty:

        st.info(
            " Aucune opportunité suivie pour le moment. "
            "Ajoutez des entreprises à votre suivi pour "
            "voir ces graphiques."
        )

    else:

        s1, s2 = st.columns(2)

        with s1:

            st.markdown("**Entonnoir par statut**")

            barres_horizontales(
                par_statut,
                "statut",
                "nombre",
                "Nombre d'opportunités",
                ordre=STATUTS,
                hauteur=220
            )

        with s2:

            st.markdown("**Répartition par source**")

            donut(par_source, "source")

        if not par_semaine.empty:

            st.markdown("**Candidatures ajoutées par semaine**")

            courbe = alt.Chart(par_semaine).mark_line(
                point=True,
                color=COULEUR
            ).encode(
                x=alt.X("semaine:T", title="Semaine"),
                y=alt.Y(
                    "nombre:Q",
                    title="Nombre",
                    axis=alt.Axis(tickMinStep=1)
                ),
                tooltip=[
                    alt.Tooltip("semaine:T", title="Semaine"),
                    alt.Tooltip("nombre:Q", title="Nombre")
                ]
            ).properties(height=240)

            st.altair_chart(
                courbe,
                use_container_width=True
            )

    st.divider()

    # ============================================================
    # MON PROFIL CV (si un CV a été analysé)
    # ============================================================

    st.subheader(" Compatibilité avec mon CV")

    resultats_cv = st.session_state.get("cv_resultats")

    if resultats_cv is None or len(resultats_cv) == 0:

        st.info(
            "ℹDéposez votre CV dans l'onglet « Mon CV » "
            "pour voir ici la compatibilité par secteur."
        )

    else:

        v1, v2 = st.columns(2)

        with v1:

            st.markdown("**Distribution des scores**")

            histogramme = alt.Chart(resultats_cv).mark_bar(
                color=COULEUR
            ).encode(
                x=alt.X(
                    "score:Q",
                    bin=alt.Bin(step=10),
                    title="Score de compatibilité"
                ),
                y=alt.Y(
                    "count()",
                    title="Nombre d'entreprises"
                )
            ).properties(height=260)

            st.altair_chart(
                histogramme,
                use_container_width=True
            )

        with v2:

            st.markdown("**Score moyen par secteur**")

            moyenne = (
                resultats_cv
                .groupby("sous_secteur")["score"]
                .mean()
                .round(0)
                .reset_index()
            )

            barres_horizontales(
                moyenne,
                "sous_secteur",
                "score",
                "Score moyen (sur 100)"
            )