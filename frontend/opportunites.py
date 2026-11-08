import streamlit as st
import pandas as pd

from backend.opportunities import (
    charger_opportunites,
    ajouter_opportunite,
    sauvegarder_opportunites,
    TYPES,
    SOURCES,
    STATUTS
)

from backend.data_processing import charger_donnees


SAISIE_MANUELLE = "✍️ Autre (saisie manuelle)"


def afficher_opportunites():

    st.header("🎓 Suivi des opportunités")

    st.write(
        "Ajoutez et suivez vos stages, PFE, alternances "
        "et autres opportunités professionnelles."
    )

    # ============================================================
    # FORMULAIRE
    # ============================================================

    st.subheader("➕ Ajouter une opportunité")

    # Liste des entreprises déjà collectées (onglet Entreprises)
    df_entreprises = charger_donnees()

    if df_entreprises is not None and not df_entreprises.empty:

        liste_entreprises = (
            df_entreprises["nom"]
            .dropna()
            .astype(str)
            .tolist()
        )

    else:

        liste_entreprises = []

    with st.form("form_opportunite"):

        entreprise_choisie = st.selectbox(
            "🏢 Entreprise (liste de vos entreprises)",
            [SAISIE_MANUELLE] + liste_entreprises
        )

        entreprise_manuelle = st.text_input(
            "✍️ Ou saisissez le nom manuellement",
            help="Utilisé seulement si vous choisissez "
                 "« Saisie manuelle » ci-dessus."
        )

        poste = st.text_input(
            "💼 Poste / Stage"
        )

        type_opportunite = st.selectbox(
            "📌 Type",
            TYPES
        )

        source = st.selectbox(
            "🌐 Source",
            SOURCES
        )

        lien = st.text_input(
            "🔗 Lien de l'offre"
        )

        date = st.date_input(
            "📅 Date"
        )

        statut = st.selectbox(
            "📊 Statut",
            STATUTS
        )

        notes = st.text_area(
            "📝 Notes"
        )

        submitted = st.form_submit_button(
            "💾 Ajouter l'opportunité"
        )

        if submitted:

            if entreprise_choisie == SAISIE_MANUELLE:
                entreprise = entreprise_manuelle
            else:
                entreprise = entreprise_choisie

            if not entreprise.strip():

                st.error(
                    "❌ Veuillez choisir ou saisir "
                    "le nom de l'entreprise."
                )

            elif not poste.strip():

                st.error(
                    "❌ Veuillez saisir le poste ou le stage."
                )

            else:

                ajouter_opportunite(
                    entreprise=entreprise.strip(),
                    poste=poste,
                    type_opportunite=type_opportunite,
                    source=source,
                    lien=lien,
                    date=str(date),
                    statut=statut,
                    notes=notes
                )

                st.success(
                    "✅ Opportunité ajoutée avec succès !"
                )

                st.rerun()

    st.divider()

    # ============================================================
    # LISTE DES OPPORTUNITÉS
    # ============================================================

    st.subheader("📋 Mes opportunités")

    df = charger_opportunites()

    if df is None or df.empty:

        st.info(
            "ℹ️ Aucune opportunité enregistrée pour le moment."
        )

        return

    # ============================================================
    # STATISTIQUES
    # ============================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(
            "Total",
            len(df)
        )

    with col2:

        a_contacter = (
            df["statut"]
            == "À contacter"
        ).sum()

        st.metric(
            "À contacter",
            int(a_contacter)
        )

    with col3:

        candidatures = (
            df["statut"]
            == "Candidature envoyée"
        ).sum()

        st.metric(
            "Candidatures envoyées",
            int(candidatures)
        )

    with col4:

        entretiens = (
            df["statut"]
            == "Entretien"
        ).sum()

        st.metric(
            "Entretiens",
            int(entretiens)
        )

    with col5:

        acceptees = (
            df["statut"]
            == "Acceptée"
        ).sum()

        st.metric(
            "Acceptées",
            int(acceptees)
        )

    st.divider()

    # ============================================================
    # FILTRE PAR STATUT
    # ============================================================

    statuts = [
        "Tous"
    ] + sorted(
        df["statut"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    statut_filtre = st.selectbox(
        "🔎 Filtrer par statut",
        statuts
    )

    df_filtre = df.copy()

    if statut_filtre != "Tous":

        df_filtre = df_filtre[
            df_filtre["statut"]
            == statut_filtre
        ]

    st.write(
        f"**{len(df_filtre)} opportunité(s)**"
    )

    # ============================================================
    # TABLEAU ÉDITABLE
    # ============================================================

    st.caption(
        "✏️ Double-cliquez sur une case pour la modifier. "
        "Cochez « Supprimer » pour retirer une ligne, "
        "puis cliquez sur **Enregistrer**."
    )

    # Préparer le tableau pour l'éditeur
    df_editeur = df_filtre.copy()

    df_editeur["date"] = pd.to_datetime(
        df_editeur["date"],
        errors="coerce"
    ).dt.date

    df_editeur["supprimer"] = False

    df_modifie = st.data_editor(
        df_editeur,
        use_container_width=True,
        hide_index=True,
        key=f"editeur_opportunites_{statut_filtre}",
        column_config={
            "entreprise": st.column_config.TextColumn(
                "🏢 Entreprise"
            ),
            "poste": st.column_config.TextColumn(
                "💼 Poste"
            ),
            "type": st.column_config.SelectboxColumn(
                "📌 Type",
                options=TYPES
            ),
            "source": st.column_config.SelectboxColumn(
                "🌐 Source",
                options=SOURCES
            ),
            "lien": st.column_config.LinkColumn(
                "🔗 Lien"
            ),
            "date": st.column_config.DateColumn(
                "📅 Date"
            ),
            "statut": st.column_config.SelectboxColumn(
                "📊 Statut",
                options=STATUTS
            ),
            "notes": st.column_config.TextColumn(
                "📝 Notes"
            ),
            "supprimer": st.column_config.CheckboxColumn(
                "🗑️ Supprimer"
            )
        }
    )

    if st.button(
        "💾 Enregistrer les modifications",
        type="primary"
    ):

        df_complet = charger_opportunites()

        for index in df_modifie.index:

            if index not in df_complet.index:
                continue

            for colonne in df_complet.columns:

                valeur = df_modifie.at[index, colonne]

                if pd.isna(valeur):
                    valeur = ""

                df_complet.at[index, colonne] = str(valeur)

        # Supprimer les lignes cochées
        a_supprimer = df_modifie.index[
            df_modifie["supprimer"] == True
        ]

        df_complet = df_complet.drop(
            index=a_supprimer
        )

        sauvegarder_opportunites(
            df_complet
        )

        st.success(
            "✅ Modifications enregistrées."
        )

        st.rerun()

    # ============================================================
    # TÉLÉCHARGEMENT
    # ============================================================

    st.download_button(
        label="⬇️ Télécharger mes opportunités",
        data=df_filtre.to_csv(
            index=False,
            encoding="utf-8-sig"
        ),
        file_name="opportunites_marrakech.csv",
        mime="text/csv"
    )