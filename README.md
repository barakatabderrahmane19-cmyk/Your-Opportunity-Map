# 🗺️ Your Opportunity Map

Application web de **recherche et de suivi des stages et opportunités IT à Marrakech**.
Elle collecte les entreprises informatiques via l'API Google Places, nettoie les données,
les affiche sur un tableau et une carte, compare votre CV aux entreprises et suit vos candidatures.

🔗 **Application en ligne : [https://your-opportunity-map-hnqmqsensmevxf4biuky3j.streamlit.app/](https://your-opportunity-map-hnqmqsensmevxf4biuky3j.streamlit.app/)**
## ✨ Fonctionnalités

| Onglet | Rôle |
|---|---|
| **Entreprises** | Collecte Google Places (ou mode simulation), filtres, tableau avec liens (site, WhatsApp, Maps), carte, ajout au suivi |
| **Données** | Données brutes et nettoyées, score de qualité, doublons, fiches incomplètes, fiche détaillée d'une entreprise |
| **Opportunités** | Suivi des candidatures : tableau éditable (statut, notes, suppression), liées aux entreprises |
| **Mon CV** | Dépôt du CV (PDF, DOCX, TXT), détection des compétences, classement des entreprises compatibles |
| **Statistiques** | Graphiques : secteurs, contacts, distance, quartiers, carte de chaleur, suivi, compatibilité CV |

## 🧰 Technologies

Python 3.12 · Streamlit · Pandas · Altair · Folium · pydeck · Google Places API (New)

## 📦 Installation

**Prérequis :** [Python 3.10 ou plus](https://www.python.org/downloads/) et [Git](https://git-scm.com/downloads).

```bash
# 1. Récupérer le code
git clone https://github.com/barakatabderrahmane19-cmyk/Your-Opportunity-Map.git
cd Your-Opportunity-Map

# 2. Créer un environnement virtuel (recommandé)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Installer les dépendances
pip install -r requirements.txt
```

## ⚙️ Configuration

L'application fonctionne de deux façons :

1. **Sans clé API** : cochez **« Mode simulation »** dans la barre latérale de l'onglet *Entreprises*.
   Les données déjà présentes dans le dossier `data/` s'affichent normalement.
2. **Avec Google Places** : pour lancer une vraie collecte,
   - créez un projet sur [Google Cloud Console](https://console.cloud.google.com/),
   - activez **Places API (New)** et créez une **clé API**,
   - collez la clé dans la barre latérale de l'application (champ « clé API »).

> 🔒 La clé n'est **jamais enregistrée** dans le code. Ne publiez jamais un fichier contenant votre clé
> (`.streamlit/secrets.toml` est exclu du dépôt par le `.gitignore`).

Le thème (couleurs) se règle dans `.streamlit/config.toml`.

## ▶️ Exécution

```bash
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501.

## 🗂️ Structure du projet

```
├── app.py                  Point d'entrée (5 onglets)
├── requirements.txt        Dépendances Python
├── .streamlit/config.toml  Thème de l'application
├── frontend/               Interface : un fichier par onglet (+ style.py)
├── backend/                Logique : Google Places, nettoyage, CV, statistiques, qualité
└── data/                   Fichiers CSV (entreprises brutes et nettoyées)
```

## 📝 Remarques

- Le suivi des candidatures est enregistré dans `data/opportunites_marrakech.csv` (non publié sur GitHub).
- Sur la version en ligne (Streamlit Community Cloud), les fichiers créés pendant l'utilisation
  ne sont pas conservés de façon permanente : le suivi peut être réinitialisé au redémarrage du serveur.
- Le CV déposé est lu en mémoire uniquement : il n'est ni enregistré ni envoyé sur Internet.

## 👤 Auteur

   **Barakat Abderrahmane** – Projet réalisé dans le cadre de la formation Assistant data analyst / ISTA NTIC SYBA.