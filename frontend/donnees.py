import os
from datetime import datetime, date

import pandas as pd
import streamlit as st

from backend.data_processing import (
    charger_donnees,
    charger_donnees_brutes,
    url_propre,
    whatsapp_url,
    RAW_FILE,
    CLEAN_FILE
)

from backend.Data_quality import (
    completude,
    score_qualite,
    diagnostic_nettoyage,
    fiches_incompletes,
    doublons_potentiels,
    hors_marrakech,
    vers_excel,
    est_absent
)

from backend.opportunities import (
    ajouter_si_absent,
    entreprises_suivies,
    normaliser_nom
)


NOMS_COLONNES = {
    "place_id": "ID Google",
    "nom": "Entreprise",
    "adresse": "Adresse",
    "telephone": "Téléphone",
    "site_web": "Site web",
    "sous_secteur": "Secteur",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "source": "Source"
}


def _date_fichier(chemin):
    """Date de dernière modification d'un fichier."""

    if not os.path.exists(chemin):
        return "—"

    return datetime.fromtimestamp(
        os.path.getmtime(chemin)
    ).strftime("%d/%m/%Y %H:%M")


def _boutons_telechargement(df, nom_fichier, cle):
    """CSV + Excel (si openpyxl est installé)."""

    col_a, col_b, _ = st.columns([1, 1, 2])

    with col_a:

        st.download_button(
            "⬇️ Télécharger en CSV",
            data=df.to_csv(
                index=False,
                encoding="utf-8-sig"
            ),
            file_name=f"{nom_fichier}.csv",
            mime="text/csv",
            key=f"{cle}_csv",
            use_container_width=True
        )

    with col_b:

        excel = vers_excel(df)

        if excel is not None:

            st.download_button(
                "⬇️ Télécharger en Excel",
                data=excel,
                file_name=f"{nom_fichier}.xlsx",
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
                key=f"{cle}_xlsx",
                use_container_width=True
            )

        else:

            st.caption(
                "Excel : `pip install openpyxl`"
            )


def _tableau_entreprises(df, hauteur=480):
    """Tableau avec liens cliquables (site, WhatsApp, Maps)."""

    d = pd.DataFrame()

    d["nom"] = df["nom"]

    if "sous_secteur" in df.columns:
        d["sous_secteur"] = df["sous_secteur"]

    d["telephone"] = df["telephone"]

    d["whatsapp"] = df["telephone"].apply(whatsapp_url)

    d["site_web"] = df["site_web"].apply(url_propre)

    d["maps"] = df.apply(
        lambda r: (
            "https://www.google.com/maps/search/"
            f"?api=1&query={r['latitude']},{r['longitude']}"
        )
        if pd.notna(r["latitude"])
        and pd.notna(r["longitude"])
        else None,
        axis=1
    )

    d["adresse"] = df["adresse"]

    st.dataframe(
        d,
        use_container_width=True,
        hide_index=True,
        height=hauteur,
        column_config={
            "nom": st.column_config.TextColumn(
                " Entreprise", width="large"
            ),
            "sous_secteur": st.column_config.TextColumn(
                " Secteur"
            ),
            "telephone": st.column_config.TextColumn(
                " Téléphone"
            ),
            "whatsapp": st.column_config.LinkColumn(
                " WhatsApp", display_text="💬 Écrire"
            ),
            "site_web": st.column_config.LinkColumn(
                "Site web", display_text="🔗 Ouvrir le site"
            ),
            "maps": st.column_config.LinkColumn(
                " Carte", display_text="📍 Voir sur Maps"
            ),
            "adresse": st.column_config.TextColumn(
                " Adresse", width="large"
            )
        }
    )


# ============================================================
# PAGE PRINCIPALE
# ============================================================

def afficher_donnees():

    st.header("🗃️ Gestion et qualité des données")

    st.write(
        "Consultez les données collectées, vérifiez leur qualité "
        "et explorez chaque entreprise en détail."
    )

    df_brut = charger_donnees_brutes()

    df_clean = charger_donnees()

    if (
        (df_brut is None or df_brut.empty)
        and (df_clean is None or df_clean.empty)
    ):

        st.info(
            "ℹ️ Aucune donnée disponible. "
            "Lancez une collecte dans l'onglet Entreprises."
        )

        return

    if df_brut is None:
        df_brut = pd.DataFrame()

    if df_clean is None:
        df_clean = pd.DataFrame()

    sous1, sous2, sous3, sous4, sous5 = st.tabs([
        " Vue d'ensemble",
        " Données brutes",
        " Données nettoyées",
        " Qualité",
        " Fiche entreprise"
    ])

    with sous1:
        _vue_ensemble(df_brut, df_clean)

    with sous2:
        _donnees_brutes(df_brut)

    with sous3:
        _donnees_nettoyees(df_clean)

    with sous4:
        _qualite(df_clean)

    with sous5:
        _fiche_entreprise(df_clean)


# ============================================================
# 1) VUE D'ENSEMBLE
# ============================================================

def _vue_ensemble(df_brut, df_clean):

    score = score_qualite(df_clean)

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric(" Lignes brutes", len(df_brut))

    k2.metric(" Lignes propres", len(df_clean))

    k3.metric(
        " Lignes retirées",
        max(len(df_brut) - len(df_clean), 0)
    )

    k4.metric(" Score qualité", f"{score} / 100")

    k5.metric(
        " Dernière mise à jour",
        _date_fichier(CLEAN_FILE).split(" ")[0]
    )

    st.progress(
        score / 100
    )

    if score >= 90:
        st.success(
            "✅ Très bonne qualité : la plupart des fiches "
            "sont complètes."
        )
    elif score >= 75:
        st.info(
            "ℹ️ Qualité correcte : quelques fiches "
            "n'ont pas de site web ou de téléphone."
        )
    else:
        st.warning(
            "⚠️ Qualité moyenne : beaucoup de fiches sont "
            "incomplètes (voir l'onglet Qualité)."
        )

    st.caption(
        f"Fichier brut : {_date_fichier(RAW_FILE)}  •  "
        f"Fichier nettoyé : {_date_fichier(CLEAN_FILE)}"
    )

    st.divider()

    st.subheader("🧹 Ce que le nettoyage a fait")

    diag = diagnostic_nettoyage(df_brut)

    if diag.empty:

        st.info("Aucune donnée brute à analyser.")

    else:

        st.dataframe(
            diag,
            use_container_width=True,
            hide_index=True,
            column_config={
                "etape": st.column_config.TextColumn(
                    "Étape", width="large"
                ),
                "lignes": st.column_config.NumberColumn(
                    "Lignes concernées"
                ),
                "action": st.column_config.TextColumn(
                    "Action", width="large"
                )
            }
        )

        st.caption(
            "Les doublons et lignes invalides sont retirés ; "
            "les valeurs manquantes sont remplacées par "
            "« Non renseigné » pour garder une table uniforme."
        )

    st.divider()

    st.subheader(" Complétude par colonne")

    comp = completude(df_clean)

    if not comp.empty:

        comp["colonne"] = comp["colonne"].map(
            lambda c: NOMS_COLONNES.get(c, c)
        )

        st.dataframe(
            comp,
            use_container_width=True,
            hide_index=True,
            column_config={
                "colonne": st.column_config.TextColumn(
                    "Colonne"
                ),
                "renseignees": st.column_config.NumberColumn(
                    "Renseignées"
                ),
                "manquantes": st.column_config.NumberColumn(
                    "Manquantes"
                ),
                "pourcentage": st.column_config.ProgressColumn(
                    "Complétude",
                    min_value=0,
                    max_value=100,
                    format="%.0f %%"
                )
            }
        )


# ============================================================
# 2) DONNÉES BRUTES
# ============================================================

def _donnees_brutes(df_brut):

    st.subheader("📥 Données brutes")

    if df_brut.empty:

        st.info("Aucune donnée brute disponible.")

        return

    st.caption(
        "Données telles que reçues de Google Places, "
        "avant nettoyage."
    )

    recherche = st.text_input(
        "🔎 Rechercher",
        placeholder="Nom, adresse, secteur...",
        key="don_brut_recherche"
    )

    d = df_brut

    if recherche.strip():

        masque = pd.Series(False, index=d.index)

        for colonne in ["nom", "adresse", "sous_secteur"]:

            if colonne in d.columns:

                masque = masque | (
                    d[colonne]
                    .astype(str)
                    .str.contains(
                        recherche.strip(),
                        case=False,
                        regex=False,
                        na=False
                    )
                )

        d = d[masque]

    st.write(f"**{len(d)} ligne(s)**")

    st.dataframe(
        d,
        use_container_width=True,
        hide_index=True,
        height=480
    )

    _boutons_telechargement(
        d,
        "entreprises_informatique_brutes",
        "don_brut"
    )


# ============================================================
# 3) DONNÉES NETTOYÉES
# ============================================================

def _donnees_nettoyees(df_clean):

    st.subheader(" Données nettoyées")

    if df_clean.empty:

        st.info("Aucune donnée nettoyée disponible.")

        return

    c1, c2 = st.columns([2, 2])

    with c1:

        recherche = st.text_input(
            " Rechercher",
            placeholder="Nom, adresse, secteur...",
            key="don_clean_recherche"
        )

    with c2:

        secteurs = st.multiselect(
            " Secteurs",
            sorted(
                df_clean["sous_secteur"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="don_clean_secteurs"
        )

    f1, f2, _ = st.columns([1, 1, 2])

    with f1:

        avec_site = st.checkbox(
            " Avec site web seulement",
            key="don_clean_site"
        )

    with f2:

        avec_tel = st.checkbox(
            "📞 Avec téléphone seulement",
            key="don_clean_tel"
        )

    d = df_clean.copy()

    if recherche.strip():

        masque = pd.Series(False, index=d.index)

        for colonne in ["nom", "adresse", "sous_secteur"]:

            masque = masque | (
                d[colonne]
                .astype(str)
                .str.contains(
                    recherche.strip(),
                    case=False,
                    regex=False,
                    na=False
                )
            )

        d = d[masque]

    if secteurs:

        d = d[d["sous_secteur"].isin(secteurs)]

    if avec_site:

        d = d[~d["site_web"].apply(est_absent)]

    if avec_tel:

        d = d[~d["telephone"].apply(est_absent)]

    st.write(
        f"**{len(d)} entreprise(s)** sur {len(df_clean)}"
    )

    if d.empty:

        st.warning("⚠️ Aucun résultat avec ces filtres.")

        return

    _tableau_entreprises(d)

    _boutons_telechargement(
        d,
        "entreprises_informatique_marrakech",
        "don_clean"
    )


# ============================================================
# 4) QUALITÉ
# ============================================================

def _qualite(df_clean):

    st.subheader("🔍 Contrôle qualité")

    if df_clean.empty:

        st.info("Aucune donnée nettoyée disponible.")

        return

    incompletes = fiches_incompletes(df_clean)

    doublons = doublons_potentiels(df_clean)

    hors = hors_marrakech(df_clean)

    nb_sans_rien = (
        int((incompletes["manque"] == "Site + téléphone").sum())
        if not incompletes.empty else 0
    )

    q1, q2, q3, q4 = st.columns(4)

    q1.metric(" Fiches incomplètes", len(incompletes))

    q2.metric(" Sans aucun contact", nb_sans_rien)

    q3.metric(" Doublons potentiels", len(doublons))

    q4.metric(" Hors Marrakech", len(hors))

    st.divider()

    # ---------- Fiches incomplètes
    with st.expander(
        f" Fiches incomplètes ({len(incompletes)})"
    ):

        if incompletes.empty:

            st.success(" Toutes les fiches ont un site et un téléphone.")

        else:

            st.caption(
                "Entreprises sans site web et/ou sans téléphone. "
                "Cherchez-les sur Google Maps ou Facebook pour "
                "trouver un moyen de les contacter."
            )

            choix = st.radio(
                "Afficher",
                [
                    "Toutes",
                    "Site + téléphone",
                    "Site web",
                    "Téléphone"
                ],
                horizontal=True,
                key="don_incomplet_choix"
            )

            d = incompletes

            if choix != "Toutes":

                d = d[d["manque"] == choix]

            st.dataframe(
                d[["nom", "manque", "telephone",
                   "site_web", "adresse"]],
                use_container_width=True,
                hide_index=True,
                height=320,
                column_config={
                    "nom": "Entreprise",
                    "manque": "Il manque",
                    "telephone": "Téléphone",
                    "site_web": "Site web",
                    "adresse": "Adresse"
                }
            )

    # ---------- Doublons
    with st.expander(
        f"♊ Doublons potentiels ({len(doublons)})"
    ):

        if doublons.empty:

            st.success("✅ Aucun doublon potentiel détecté.")

        else:

            st.caption(
                "Entreprises qui partagent le même téléphone, "
                "site ou nom. Souvent ce sont des succursales "
                "légitimes ; vérifiez avant de supprimer."
            )

            st.dataframe(
                doublons,
                use_container_width=True,
                hide_index=True,
                height=320,
                column_config={
                    "motif": "Motif",
                    "groupe": "Valeur commune",
                    "nom": "Entreprise",
                    "adresse": "Adresse",
                    "telephone": "Téléphone",
                    "site_web": "Site web"
                }
            )

    # ---------- Hors Marrakech
    with st.expander(
        f" Entreprises hors Marrakech ({len(hors)})"
    ):

        if hors.empty:

            st.success("✅ Toutes les entreprises sont à Marrakech.")

        else:

            st.caption(
                "Entreprises à plus de 25 km du centre de "
                "Marrakech : probablement hors de votre zone "
                "de recherche."
            )

            st.dataframe(
                hors[["nom", "adresse", "distance_km"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "nom": "Entreprise",
                    "adresse": "Adresse",
                    "distance_km": st.column_config.NumberColumn(
                        "Distance (km)",
                        format="%d km"
                    )
                }
            )

    st.divider()

    st.subheader(" Structure des données")

    structure = [
        {
            "Colonne": NOMS_COLONNES.get(c, c),
            "Type": str(df_clean[c].dtype),
            "Valeurs non nulles": int(df_clean[c].notna().sum())
        }
        for c in df_clean.columns
    ]

    st.dataframe(
        structure,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 5) FICHE ENTREPRISE
# ============================================================

def _fiche_entreprise(df_clean):

    st.subheader(" Fiche d'une entreprise")

    if df_clean.empty:

        st.info("Aucune donnée nettoyée disponible.")

        return

    nom = st.selectbox(
        "Choisissez une entreprise (tapez pour rechercher)",
        df_clean["nom"].tolist(),
        key="don_fiche_nom"
    )

    ligne = df_clean[df_clean["nom"] == nom].iloc[0]

    col_info, col_carte = st.columns([3, 2])

    with col_info:

        st.markdown(f"###  {ligne['nom']}")

        st.write(f" **Secteur :** {ligne['sous_secteur']}")

        st.write(f" **Adresse :** {ligne['adresse']}")

        st.write(f" **Téléphone :** {ligne['telephone']}")

        url_site = url_propre(ligne["site_web"])

        url_wa = whatsapp_url(ligne["telephone"])

        url_maps = (
            "https://www.google.com/maps/search/"
            f"?api=1&query={ligne['latitude']},{ligne['longitude']}"
        )

        b1, b2, b3 = st.columns(3)

        with b1:

            if url_site:

                st.link_button(
                    "🔗 Site web",
                    url_site,
                    use_container_width=True
                )

            else:

                st.button(
                    "🔗 Site web",
                    disabled=True,
                    use_container_width=True,
                    key="don_fiche_nosite"
                )

        with b2:

            if url_wa:

                st.link_button(
                    "WhatsApp",
                    url_wa,
                    use_container_width=True
                )

            else:

                st.button(
                    " WhatsApp",
                    disabled=True,
                    use_container_width=True,
                    key="don_fiche_nowa"
                )

        with b3:

            st.link_button(
                "📍 Google Maps",
                url_maps,
                use_container_width=True
            )

        st.write("")

        if normaliser_nom(nom) in entreprises_suivies():

            st.success("✅ Cette entreprise est déjà dans votre suivi.")

        elif st.button(
            "📌 Ajouter au suivi",
            type="primary",
            key="don_fiche_ajout"
        ):

            ajouter_si_absent(
                entreprise=nom,
                poste="Stage",
                type_opportunite="Stage",
                source="Google",
                lien="",
                date=str(date.today()),
                statut="À contacter",
                notes=(
                    f"Tél : {ligne['telephone']} | "
                    f"Site : {ligne['site_web']} | "
                    f"Adresse : {ligne['adresse']}"
                )
            )

            st.success(
                "✅ Ajoutée au suivi (statut : À contacter)."
            )

    with col_carte:

        point = pd.DataFrame(
            {
                "lat": [float(ligne["latitude"])],
                "lon": [float(ligne["longitude"])]
            }
        )

        st.map(point, zoom=14)

        st.caption(
            f"Coordonnées : {ligne['latitude']:.5f}, "
            f"{ligne['longitude']:.5f}"
        )

    # Entreprises du même secteur à proximité d'autres idées
    meme_secteur = df_clean[
        (df_clean["sous_secteur"] == ligne["sous_secteur"])
        & (df_clean["nom"] != nom)
    ]

    if not meme_secteur.empty:

        with st.expander(
            f" Autres entreprises du secteur "
            f"« {ligne['sous_secteur']} » "
            f"({len(meme_secteur)})"
        ):

            _tableau_entreprises(
                meme_secteur,
                hauteur=300
            )