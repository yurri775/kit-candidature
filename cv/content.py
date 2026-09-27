# -*- coding: utf-8 -*-
"""Contenu de TES CV maîtres. Balisage : *gras*, //italique//.

Exemple fictif (Camille Martin) : remplace tout par ton parcours.
Règle d'or : un CV maître par grand type de poste (3 à 6), jamais un CV par offre.
postule.py ne change ensuite que le titre et la 1re phrase du profil.
"""

CONTACT = {
    "nom": "CAMILLE MARTIN",
    "l1": "Lille (59) | +33 6 00 00 00 00 | camille.martin@example.com | linkedin.com/in/camille-martin",
    "l2": "github.com/camille-martin | Nationalité française | Permis B",
    "l3": "*Disponible à partir du 1er octobre 2026* | Mobile en France et au Luxembourg",
}

# (diplôme, suite de la ligne, dates, détail facultatif)
FORMATION = [
    ("Master 2 Informatique", " — Université de Lille", "2024 – 2026",
     "Apprentissage automatique, bases de données, génie logiciel, cloud."),
    ("Licence Informatique", " — Université de Lille", "2021 – 2024", None),
]

CERTIFS = "*Certifications* : Microsoft Azure *AZ-900* ; AWS Cloud Practitioner."
LANGUES = "*Langues* : français (langue maternelle) ; *anglais B2* (TOEIC 850)."

CVS = {}

# ─────────────────────────────── 1. DÉVELOPPEMENT BACKEND (français)
CVS["backend"] = dict(
 fichier="CV_Camille_MARTIN_Backend",
 titre="Développeuse Backend — Python, Java Spring Boot, SQL",
 profil="Diplômée d'un Master 2 Informatique (Université de Lille, septembre 2026). "
        "Je conçois des API *Python* et *Java* testées, conteneurisées et documentées, "
        "et j'ai mis en production une application utilisée chaque jour par une équipe métier.",
 competences=[
  "*Langages* : *Python*, *Java*, SQL, JavaScript.",
  "*Backend* : FastAPI, *Spring Boot*, API REST, tests unitaires (pytest, JUnit).",
  "*Données* : PostgreSQL, modélisation, optimisation de requêtes.",
  "*Outils* : *Docker*, Git, CI/CD (GitHub Actions), Linux.",
 ],
 experiences=[
  dict(titre="Développeuse backend — Stage de fin d'études", org="ENTREPRISE EXEMPLE, Lille",
       dates="Mars – Août 2026", sub="Équipe de 6 développeurs, produit SaaS B2B", bullets=[
   "Développement d'une *API FastAPI* de facturation : 14 points d'accès, 92 % de couverture de tests.",
   "*Division par 3 du temps de réponse* d'un rapport en réécrivant deux requêtes PostgreSQL.",
   "Conteneurisation *Docker* et pipeline *GitHub Actions* jusqu'à la préproduction."]),
  dict(titre="Développeuse — Stage", org="PME EXEMPLE, Roubaix", dates="Juin – Août 2025",
       sub="Outil interne de suivi des commandes", bullets=[
   "Application *Spring Boot* + React pour 25 utilisateurs quotidiens."]),
 ],
 projets=[
  "*Gestionnaire de budget* — API Python + interface React, déployée sur un VPS avec Docker.",
 ],
)

# ─────────────────────────────── 2. DATA (anglais)
CVS["data_en"] = dict(
 lang="english",
 fichier="CV_Camille_MARTIN_Data_EN",
 titre="Data Analyst / Data Engineer — Python, SQL, Power BI",
 profil="MSc Computer Science graduate (University of Lille, September 2026). "
        "I build *Python ETL pipelines* and *Power BI dashboards* that business teams actually use.",
 competences=[
  "*Data*: *Python* (pandas), *SQL* (PostgreSQL), ETL, data quality checks.",
  "*BI*: *Power BI*, KPI design with business teams.",
  "*Tools*: Docker, Git, Linux, Azure (AZ-900).",
 ],
 experiences=[
  dict(titre="Data Engineer — Final-year internship", org="EXAMPLE COMPANY, Lille",
       dates="March – August 2026", sub="Sales analytics team", bullets=[
   "Built *Python ETL pipelines* feeding the sales data warehouse (2M rows/day).",
   "Designed 4 *Power BI dashboards* used weekly by 30 sales managers."]),
 ],
 formation=[
  ("MSc Computer Science", " — University of Lille, France", "2024 – 2026", None),
  ("BSc Computer Science", " — University of Lille, France", "2021 – 2024", None),
 ],
 certifs="*Certifications*: Microsoft Azure *AZ-900*; AWS Cloud Practitioner.",
 langues="*Languages*: French (native); *English B2* (TOEIC 850).",
 sections=dict(),
)

# CV parmi lesquels postule.py a le droit de choisir
MASTERS = ["backend", "data_en"]
