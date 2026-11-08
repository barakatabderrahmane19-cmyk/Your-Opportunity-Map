from urllib.parse import quote

import streamlit as st

from backend.ia import (
    generer_candidature,
    separer_objet,
    ErreurIA,
    CANAUX,
    FOURNISSEURS
)

from backend.data_processing import whatsapp_url


def _cle_depuis_secrets(nom):
    """Clé enregistrée dans .streamlit/secrets.toml (usage local)."""

    try:
        return str(st.secrets.get(nom, "") or "")
    except Exception:
        return ""


def afficher_generateur_candidature(texte_cv, entreprises):
    """Section « Message de candidature » (IA).

    texte_cv    : texte brut du CV.
    entreprises : DataFrame avec nom, sous_secteur, site_web, telephone.
    """

    st.divider()

    st.subheader("✉️ Message de candidature (IA)")

    if entreprises is None or len(entreprises) == 0:

        st.info("Aucune entreprise disponible.")

        return

    fournisseur = st.radio(
        "Fournisseur d'IA",
        FOURNISSEURS,
        horizontal=True,
        key="ia_fournisseur"
    )

    gemini = fournisseur == FOURNISSEURS[0]

    if gemini:

        st.caption(
            "🆓 Gemini est gratuit avec une clé créée sur "
            "aistudio.google.com. Avec le palier gratuit, Google peut "
            "utiliser les requêtes pour améliorer ses produits : "
            "gardez l'option de masquage ci-dessous cochée."
        )

        nom_secret, libelle_cle = "GEMINI_API_KEY", "🔑 Clé API Gemini"

    else:

        st.caption(
            "💳 Claude est payant (facturation à l'usage sur "
            "console.anthropic.com)."
        )

        nom_secret, libelle_cle = "ANTHROPIC_API_KEY", "🔑 Clé API Anthropic"

    st.caption(
        "🔒 Le texte de votre CV est envoyé au fournisseur choisi pour "
        "rédiger le message ; l'application ne l'enregistre pas. "
        "Relisez toujours le message avant de l'envoyer."
    )

    cle = _cle_depuis_secrets(nom_secret)

    if not cle:

        cle = st.text_input(
            libelle_cle,
            type="password",
            help="Jamais enregistrée par l'application.",
            key=f"ia_cle_{nom_secret}"
        )

    masquer = st.checkbox(
        "🛡️ Masquer mon email et mon téléphone avant l'envoi",
        value=True,
        key="ia_masquer"
    )

    col1, col2 = st.columns([3, 1])

    with col1:

        nom = st.selectbox(
            "🏢 Entreprise ciblée",
            entreprises["nom"].tolist(),
            key="ia_entreprise"
        )

    with col2:

        canal = st.radio(
            "Canal",
            CANAUX,
            horizontal=True,
            key="ia_canal"
        )

    ligne = entreprises[entreprises["nom"] == nom].iloc[0]

    if st.button(
        "✨ Générer le message",
        type="primary",
        key="ia_generer"
    ):

        try:

            with st.spinner("Rédaction en cours..."):

                texte = generer_candidature(
                    cle_api=cle,
                    cv_texte=texte_cv,
                    entreprise=nom,
                    secteur=ligne.get("sous_secteur", ""),
                    site=ligne.get("site_web", ""),
                    canal=canal,
                    fournisseur=fournisseur,
                    masquer=masquer
                )

            st.session_state["ia_message"] = {
                "entreprise": nom,
                "canal": canal,
                "telephone": ligne.get("telephone", "")
            }

            st.session_state["ia_texte"] = texte

        except ErreurIA as erreur:

            st.error(f"❌ {erreur}")

    message = st.session_state.get("ia_message")

    if not message or "ia_texte" not in st.session_state:

        return

    st.markdown(
        f"**Message pour {message['entreprise']}** ({message['canal']}) "
        "— vous pouvez le modifier :"
    )

    texte = st.text_area(
        "Message",
        key="ia_texte",
        height=260,
        label_visibility="collapsed"
    )

    if message["canal"] == "Email":

        objet, corps = separer_objet(texte)

        st.link_button(
            "📧 Ouvrir dans ma messagerie",
            "mailto:?subject=" + quote(objet) + "&body=" + quote(corps)
        )

    else:

        lien = whatsapp_url(message["telephone"])

        if lien:

            st.link_button(
                "💬 Ouvrir dans WhatsApp",
                lien + "?text=" + quote(texte)
            )

        else:

            st.caption(
                "Pas de numéro WhatsApp pour cette entreprise "
                "(numéro fixe ou absent) : copiez le message."
            )