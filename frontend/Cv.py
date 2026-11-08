import streamlit as st
from datetime import date
from frontend.ia_candidature import afficher_generateur_candidature

from backend.data_processing import (
    charger_donnees,
    url_propre,
    whatsapp_url
)

from backend.Cv_matching import (
    extraire_texte_cv,
    analyser_cv,
    classer_entreprises,
    liens_recherche_offres
)

from backend.opportunities import (
    ajouter_si_absent
)


def afficher_cv():

    st.header("📄 Mon CV – opportunités compatibles")

    st.write(
        "Déposez votre CV : l'application détecte vos compétences "
        "et classe les entreprises de Marrakech selon leur "
        "compatibilité avec votre profil."
    )

    st.caption(
        " Votre CV est lu uniquement dans l'application : "
        "il n'est ni envoyé sur Internet ni enregistré."
    )

    fichier = st.file_uploader(
        "📎 Déposez votre CV (PDF, DOCX ou TXT)",
        type=["pdf", "docx", "txt"]
    )

    if fichier is None:

        st.info(
            "ℹ Aucun CV déposé pour le moment."
        )

        return

    # ============================================================
    # LECTURE DU CV
    # ============================================================

    try:

        texte = extraire_texte_cv(fichier)

    except Exception as erreur:

        st.error(
            f"❌ Impossible de lire le CV : {erreur}"
        )

        return

    if len(texte.strip()) < 30:

        st.warning(
            "⚠️ Aucun texte lisible dans ce CV. "
            "S'il s'agit d'un PDF scanné (image), "
            "exportez-le en PDF texte ou en DOCX."
        )

        return

    competences, par_secteur = analyser_cv(texte)

    if not competences:

        st.warning(
            "⚠️ Aucune compétence IT reconnue dans ce CV. "
            "Vérifiez que la section « Compétences » "
            "est bien présente."
        )

        return

    # ============================================================
    # PROFIL DÉTECTÉ
    # ============================================================

    st.subheader(" Profil détecté")

    st.markdown(
        " ".join(
            f"`{mot}`"
            for mot in list(competences)[:30]
        )
    )

    st.write(
        "**Secteurs les plus proches :** "
        + ", ".join(
            f"{secteur} ({len(mots)})"
            for secteur, mots in sorted(
                par_secteur.items(),
                key=lambda x: -len(x[1])
            )[:3]
        )
    )

    st.divider()

    # ============================================================
    # ENTREPRISES COMPATIBLES
    # ============================================================

    st.subheader(" Entreprises compatibles")

    df_entreprises = charger_donnees()

    if df_entreprises is None or df_entreprises.empty:

        st.info(
            "ℹ️ Aucune entreprise collectée. "
            "Lancez d'abord une collecte dans l'onglet Entreprises."
        )

        return

    resultats = classer_entreprises(
        df_entreprises,
        competences,
        par_secteur
    )

    # Mémorisé pour l'onglet Statistiques
    st.session_state["cv_resultats"] = resultats[
        ["nom", "sous_secteur", "score"]
    ].copy()

    col1, col2 = st.columns([2, 1])

    with col1:

        nombre = st.slider(
            "Nombre d'entreprises à afficher",
            min_value=5,
            max_value=min(100, len(resultats)),
            value=min(20, len(resultats))
        )

    with col2:

        st.write("")

        avec_contact = st.checkbox(
            "📞 Seulement avec téléphone ou site",
            value=False
        )

    if avec_contact:

        resultats = resultats[
            (resultats["site_web"] != "Non renseigné")
            | (resultats["telephone"] != "Non renseigné")
        ]

    top = resultats.head(nombre).copy()

    affichage = top[
        ["score", "nom", "sous_secteur", "pourquoi",
         "telephone", "site_web"]
    ].copy()

    affichage["whatsapp"] = top["telephone"].apply(
        whatsapp_url
    )

    affichage["site_web"] = top["site_web"].apply(
        url_propre
    )

    st.dataframe(
        affichage[
            ["score", "nom", "sous_secteur", "pourquoi",
             "telephone", "whatsapp", "site_web"]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "score": st.column_config.ProgressColumn(
                " Compatibilité",
                min_value=0,
                max_value=100,
                format="%d %%",
                width="medium"
            ),
            "nom": st.column_config.TextColumn(
                " Entreprise",
                width="large"
            ),
            "sous_secteur": st.column_config.TextColumn(
                " Secteur"
            ),
            "pourquoi": st.column_config.TextColumn(
                " Pourquoi",
                width="large"
            ),
            "telephone": st.column_config.TextColumn(
                " Téléphone"
            ),
            "whatsapp": st.column_config.LinkColumn(
                " WhatsApp",
                display_text="💬 Écrire"
            ),
            "site_web": st.column_config.LinkColumn(
                " Site web",
                display_text="🔗 Ouvrir le site"
            )
        }
    )

    # ============================================================
    # AJOUT AU SUIVI
    # ============================================================

    st.subheader("📌 Ajouter au suivi")

    choix = st.multiselect(
        "Choisissez les entreprises à contacter",
        top["nom"].tolist()
    )

    if st.button(
        "📌 Ajouter la sélection à mon suivi",
        type="primary",
        disabled=not choix
    ):

        ajoutees = 0

        deja = 0

        for nom in choix:

            ligne = top[top["nom"] == nom].iloc[0]

            notes = (
                f"Compatibilité CV : {ligne['score']} % | "
                f"Tél : {ligne['telephone']} | "
                f"Site : {ligne['site_web']}"
            )

            if ajouter_si_absent(
                entreprise=nom,
                poste="Stage",
                type_opportunite="Stage",
                source="Google",
                lien="",
                date=str(date.today()),
                statut="À contacter",
                notes=notes
            ):
                ajoutees += 1
            else:
                deja += 1

        if ajoutees:
            st.success(
                f"✅ {ajoutees} entreprise(s) ajoutée(s) "
                "au suivi (onglet Opportunités)."
            )

        if deja:
            st.warning(
                f"⚠️ {deja} entreprise(s) étaient déjà suivies."
            )

    st.divider()

    # ============================================================
    # OFFRES DE STAGE (RECHERCHES PRÊTES)
    # ============================================================

    st.subheader("🔗 Chercher des offres de stage")

    st.write(
        "Recherches prêtes à ouvrir, construites avec "
        "vos compétences :"
    )

    liens = liens_recherche_offres(competences)

    colonnes = st.columns(3)

    for i, (libelle, url) in enumerate(liens):

        with colonnes[i % 3]:

            st.link_button(
                libelle,
                url,
                use_container_width=True
            )
    afficher_generateur_candidature(texte, top)