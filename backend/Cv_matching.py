import io
import re
import unicodedata
from urllib.parse import quote_plus

import pandas as pd


# ==========================================
# MOTS-CLÉS PAR SOUS-SECTEUR
# (les noms de secteurs = ceux de ta base)
# ==========================================

MOTS_CLES_SECTEURS = {

    "Développement logiciel": [
        "python", "java", "javascript", "typescript", "c#", "c++",
        ".net", "php", "laravel", "symfony", "django", "flask",
        "spring", "spring boot", "react", "angular", "vue",
        "node", "nodejs", "flutter", "react native", "kotlin",
        "swift", "android", "developpeur", "developpement",
        "full stack", "fullstack", "backend", "frontend", "api",
        "rest", "git", "github", "pfe", "genie logiciel",
        "poo", "uml", "agile", "scrum"
    ],

    "Web / Internet": [
        "html", "css", "javascript", "wordpress", "woocommerce",
        "prestashop", "shopify", "seo", "ui", "ux", "figma",
        "web design", "webdesign", "developpeur web",
        "integrateur", "bootstrap", "tailwind", "react", "vue",
        "php", "laravel", "e-commerce", "ecommerce",
        "site web", "photoshop", "illustrator", "community manager",
        "reseaux sociaux", "marketing digital"
    ],

    "Data / Cloud / Base de données": [
        "data", "data science", "data analyst", "data engineer",
        "sql", "mysql", "postgresql", "mongodb", "oracle",
        "power bi", "tableau", "excel", "pandas", "numpy",
        "machine learning", "deep learning", "intelligence artificielle",
        "ia", "nlp", "tensorflow", "pytorch", "big data", "spark",
        "hadoop", "etl", "bi", "business intelligence",
        "cloud", "aws", "azure", "gcp", "docker", "kubernetes",
        "devops", "ci/cd", "python"
    ],

    "Cybersécurité": [
        "cybersecurite", "securite informatique", "securite",
        "pentest", "penetration", "kali", "wireshark", "nmap",
        "owasp", "iso 27001", "firewall", "pare-feu", "siem",
        "soc", "forensic", "cryptographie", "vulnerabilite",
        "ethical hacking", "ctf"
    ],

    "Télécom / Réseaux": [
        "reseau", "reseaux", "cisco", "ccna", "ccnp", "routage",
        "switching", "vlan", "vpn", "tcp/ip", "telecom",
        "telecommunications", "fibre", "fibre optique", "voip",
        "wifi", "mikrotik", "huawei", "gns3", "packet tracer",
        "linux", "administration reseau"
    ],

    "Informatique / Hardware": [
        "maintenance", "hardware", "materiel", "depannage",
        "support technique", "helpdesk", "help desk", "windows",
        "windows server", "active directory", "administration systeme",
        "systemes", "linux", "virtualisation", "vmware",
        "hyper-v", "infrastructure", "assemblage", "reseau",
        "support utilisateurs", "glpi"
    ],

    "Informatique": [
        "informatique", "it", "support", "assistance",
        "systemes d'information", "systeme d'information", "erp",
        "sap", "odoo", "crm", "gestion", "bureautique",
        "microsoft office", "office 365", "administration",
        "infrastructure", "logiciel", "base de donnees"
    ],

    "Technologie / Digital": [
        "digital", "transformation digitale", "innovation",
        "startup", "start-up", "erp", "crm", "odoo", "mobile",
        "application mobile", "iot", "blockchain", "e-commerce",
        "marketing digital", "ux", "ui", "chatbot",
        "automatisation", "rpa", "no code", "low code"
    ],
}


# Mots présents dans presque tous les noms d'entreprises
NOMS_TROP_GENERIQUES = {
    "informatique", "securite", "systemes", "administration"
}


# ==========================================
# OUTILS DE TEXTE
# ==========================================

def normaliser_texte(texte):
    """Minuscules + sans accents (sécurité = securite)."""

    if texte is None:
        return ""

    texte = unicodedata.normalize(
        "NFKD",
        str(texte)
    )

    texte = "".join(
        c for c in texte
        if not unicodedata.combining(c)
    )

    # apostrophes typographiques -> simples
    texte = texte.replace("’", "'")

    return texte.lower()


def _compter(mot_cle, texte_normalise):
    """Nombre d'apparitions du mot-clé (mot entier)."""

    motif = (
        r"(?<![a-z0-9])"
        + re.escape(normaliser_texte(mot_cle))
        + r"(?![a-z0-9])"
    )

    return len(
        re.findall(
            motif,
            texte_normalise
        )
    )


# ==========================================
# LECTURE DU CV (PDF / DOCX / TXT)
# ==========================================

def extraire_texte_cv(fichier):
    """Lit un fichier uploadé Streamlit et retourne son texte.
    Le CV n'est ni envoyé sur Internet ni sauvegardé."""

    nom = fichier.name.lower()

    contenu = fichier.getvalue()

    if nom.endswith(".pdf"):

        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError(
                "Module manquant : installez-le avec "
                "`pip install pypdf`."
            )

        lecteur = PdfReader(
            io.BytesIO(contenu)
        )

        return "\n".join(
            (page.extract_text() or "")
            for page in lecteur.pages
        )

    if nom.endswith(".docx"):

        try:
            from docx import Document
        except ImportError:
            raise RuntimeError(
                "Module manquant : installez-le avec "
                "`pip install python-docx`."
            )

        document = Document(
            io.BytesIO(contenu)
        )

        morceaux = [
            p.text
            for p in document.paragraphs
        ]

        # Les CV mettent souvent les compétences dans des tableaux
        for tableau in document.tables:
            for ligne in tableau.rows:
                for cellule in ligne.cells:
                    morceaux.append(cellule.text)

        return "\n".join(morceaux)

    if nom.endswith(".txt"):

        return contenu.decode(
            "utf-8",
            errors="ignore"
        )

    raise RuntimeError(
        "Format non supporté (PDF, DOCX ou TXT)."
    )


# ==========================================
# ANALYSE DU PROFIL
# ==========================================

def analyser_cv(texte):
    """Retourne :
    - competences : {mot_cle: nb_apparitions} (trié)
    - par_secteur : {secteur: [mots-clés trouvés]}"""

    texte_n = normaliser_texte(texte)

    competences = {}

    par_secteur = {}

    for secteur, mots in MOTS_CLES_SECTEURS.items():

        trouves = []

        for mot in mots:

            nombre = _compter(
                mot,
                texte_n
            )

            if nombre > 0:

                trouves.append(mot)

                competences[mot] = nombre

        if trouves:
            par_secteur[secteur] = trouves

    competences = dict(
        sorted(
            competences.items(),
            key=lambda x: -x[1]
        )
    )

    return competences, par_secteur


# ==========================================
# SCORE DES ENTREPRISES
# ==========================================

def classer_entreprises(df, competences, par_secteur):
    """Ajoute un score de compatibilité (0-100) et une
    explication à chaque entreprise, triées du meilleur
    au moins bon."""

    if df is None or df.empty:
        return pd.DataFrame()

    max_hits = max(
        [len(v) for v in par_secteur.values()],
        default=0
    )

    resultats = df.copy()

    scores = []
    raisons = []

    for _, ligne in resultats.iterrows():

        secteur = str(
            ligne.get("sous_secteur", "")
        )

        nom_n = normaliser_texte(
            ligne.get("nom", "")
        )

        score = 20  # base : toute entreprise IT de la liste

        raison = []

        # --- 1) secteur compatible avec le CV
        mots_secteur = par_secteur.get(secteur, [])

        if mots_secteur and max_hits:

            score += 55 * len(mots_secteur) / max_hits

            raison.append(
                "Secteur « "
                + secteur
                + " » : "
                + ", ".join(mots_secteur[:4])
            )

        # --- 2) nom de l'entreprise lié à une compétence
        # (mots courts type "it", "ui", "bi" ignorés pour
        # éviter les faux positifs)
        liees = [
            mot for mot in competences
            if len(mot) > 3
            and mot not in NOMS_TROP_GENERIQUES
            and _compter(mot, nom_n) > 0
        ]

        if liees:

            score += 10

            raison.append(
                "Nom lié à : "
                + ", ".join(liees[:2])
            )

        # --- 3) facilité de contact
        site = str(ligne.get("site_web", ""))

        tel = str(ligne.get("telephone", ""))

        if site not in ("", "Non renseigné", "nan"):
            score += 10
            raison.append("Site web")

        if tel not in ("", "Non renseigné", "nan"):
            score += 5
            raison.append("Téléphone")

        scores.append(
            int(round(min(score, 100)))
        )

        raisons.append(
            " • ".join(raison)
        )

    resultats["score"] = scores

    resultats["pourquoi"] = raisons

    return resultats.sort_values(
        ["score", "nom"],
        ascending=[False, True]
    ).reset_index(drop=True)


# ==========================================
# LIENS DE RECHERCHE D'OFFRES
# ==========================================

def liens_recherche_offres(
    competences,
    ville="Marrakech",
    nb_requetes=3
):
    """Liens vers des recherches d'offres de stage prêtes
    à ouvrir, construits avec les compétences du CV."""

    # mots trop génériques pour une recherche d'offre
    inutiles = {
        "it", "ia", "bi", "ui", "ux", "api", "git", "rest",
        "poo", "uml", "soc", "ctf", "pfe", "support",
        "gestion", "administration", "systemes", "informatique",
        "digital", "mobile", "maintenance", "materiel"
    }

    mots = [
        m for m in competences
        if m not in inutiles
    ][:nb_requetes]

    liens = []

    for mot in mots:

        requete = f"stage {mot}"

        liens.append(
            (
                f"LinkedIn – {requete}",
                "https://www.linkedin.com/jobs/search/?keywords="
                + quote_plus(requete)
                + "&location="
                + quote_plus(ville + ", Maroc")
            )
        )

        liens.append(
            (
                f"Indeed – {requete}",
                "https://ma.indeed.com/jobs?q="
                + quote_plus(requete)
                + "&l="
                + quote_plus(ville)
            )
        )

        liens.append(
            (
                f"Google – {requete}",
                "https://www.google.com/search?q="
                + quote_plus(
                    f"{requete} {ville} offre"
                )
            )
        )

    return liens