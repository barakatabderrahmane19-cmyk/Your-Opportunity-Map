import streamlit as st

from frontend.entreprises import afficher_entreprises
from frontend.donnees import afficher_donnees
from frontend.opportunites import afficher_opportunites
from frontend.Cv import afficher_cv
from frontend.Statistiques import afficher_statistiques


# ==========================================
# CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Your Opportunity Map",
    page_icon="",
    layout="wide"
)



# ==========================================
# TITRE
# ==========================================

st.title(" Your Opportunity Map")

st.write(
    "Système intelligent de recherche et de suivi "
    "des opportunités professionnelles à Marrakech."
)


# ==========================================
# LES 3 ONGLETS
# ==========================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    " Entreprises",
    " Données",
    " Opportunités",
    "📄 Mon CV",
    "📊 Statistiques"
])


# ==========================================
# ONGLET ENTREPRISES
# ==========================================

with tab1:
    afficher_entreprises()


# ==========================================
# ONGLET DONNÉES
# ==========================================

with tab2:
    afficher_donnees()


# ==========================================
# ONGLET OPPORTUNITÉS
# ==========================================

with tab3:
    afficher_opportunites()


# ==========================================
# ONGLET MON CV
# ==========================================

with tab4:
    afficher_cv()


# ==========================================
# ONGLET STATISTIQUES
# ==========================================

with tab5:
    afficher_statistiques()


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Your Opportunity Map — "
    "Find. Apply. Track. with Google Places API"
)


#cd "C:\Users\ORIGINAL\Desktop\your opportunity project by barakat"
#streamlit run app.py