#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
postule.py — prépare un dossier de candidature complet à partir d'une offre.

    ./venv/bin/python postule.py <url>
    ./venv/bin/python postule.py offre.txt
    pbpaste | ./venv/bin/python postule.py -

Produit dans ~/Downloads/candidatures/<date>_<Entreprise>/ :
    CV_....pdf / .docx    CV adapté à l'offre
    lettre.txt            lettre assemblée depuis tes blocs
    offre.txt             l'annonce archivée
    dossier.json          ce que le modèle a décidé, et pourquoi

Puis ajoute une ligne dans kit/suivi_candidatures.csv.
Le système NE SOUMET RIEN : tu relis, tu envoies.
"""
import sys, os, re, json, csv, subprocess, datetime, textwrap, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
KIT  = os.path.join(HERE, '..', 'kit')
OUT_ROOT = os.path.expanduser(os.environ.get('CANDIDATURES_DIR', '~/Downloads/candidatures'))
SUIVI = os.path.join(KIT, 'suivi_candidatures.csv')
sys.path.insert(0, HERE)

import render
from content import CVS, MASTERS, CONTACT
PROFIL = open(os.path.join(KIT, 'profil.md'), encoding='utf-8').read()


# ───────────────────────────────────────────── récupération de l'offre
def lire_offre(source):
    if source == '-':
        return sys.stdin.read()
    if os.path.exists(source):
        return open(source, encoding='utf-8', errors='replace').read()
    if source.startswith(('http://', 'https://')):
        import requests
        html = requests.get(source, timeout=25, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'
        }).text
        html = re.sub(r'(?is)<(script|style|nav|footer|svg)[^>]*>.*?</\1>', ' ', html)
        txt = re.sub(r'(?s)<[^>]+>', '\n', html)
        txt = re.sub(r'&nbsp;?', ' ', txt)
        txt = re.sub(r'&(amp|lt|gt|quot|#39);', ' ', txt)
        txt = '\n'.join(l.strip() for l in txt.splitlines() if l.strip())
        if len(txt) < 600:
            sys.exit("Page trop pauvre (site en JavaScript ?).\n"
                     "Copie le texte de l'annonce et relance :\n"
                     "    pbpaste | ./venv/bin/python postule.py -")
        return txt
    sys.exit(f"Source introuvable : {source}")


# ───────────────────────────────────────────── appel du modèle
SCHEMA = """{
  "entreprise": "", "poste": "", "ville": "",
  "type_contrat": "CDI | CDD | alternance | stage | freelance | inconnu",
  "lane": "<une clé exacte parmi la liste>",
  "titre_cv": "intitulé pour la ligne sous le nom, calqué sur le poste, max 90 caractères",
  "phrase_profil": "UNE phrase qui remplacera la 1re phrase du profil, citant l'entreprise ou son secteur",
  "blocs_retenus": ["B1", "B3"],
  "lettre": "lettre complète assemblée : accroche + 2 ou 3 blocs + clôture, en français",
  "alertes": ["points bloquants ou risques, ex: 'alternance : non éligible', 'stack Node absente', '10 ans requis'"],
  "pourquoi": "2 phrases : pourquoi ce CV et ces blocs"
}"""

def demander_au_modele(offre, lanes, blocs):
    prompt = f"""Tu prépares une candidature pour {CONTACT['nom'].title()}.

FAITS SUR LE CANDIDAT (ne jamais inventer au-delà) :
{PROFIL}

CV DISPONIBLES (choisis-en un, clé exacte) :
{lanes}

BLOCS DE LETTRE DISPONIBLES (réutilise le texte tel quel, adapte juste les [CROCHETS]) :
{blocs}

ANNONCE :
<<<
{offre[:14000]}
>>>

CONSIGNES :
- Choisis le CV le plus proche du TITRE du poste.
- Lettre : accroche + 2 ou 3 blocs MAXIMUM + clôture. Insère UNE phrase qui prouve que l'annonce a été lue
  (un produit, un client, un chiffre, une techno cités dans l'annonce).
- Si l'annonce tutoie, tutoie. Sinon vouvoie.
- Si une techno demandée manque au candidat, utilise le bloc B7 et sois honnête. N'invente JAMAIS une compétence.
- Dans "alertes", signale sans complaisance : contrat qui n'est pas un CDI, années d'expérience exigées
  hors de portée, techno centrale absente, localisation incompatible avec la zone de recherche indiquée dans les faits.

Réponds UNIQUEMENT par un objet JSON valide, sans texte autour, de la forme :
{SCHEMA}"""

    r = subprocess.run(['claude', '-p', prompt], capture_output=True, text=True, timeout=420)
    if r.returncode:
        sys.exit("Echec de l'appel claude :\n" + (r.stderr or '')[-800:])
    out = r.stdout.strip()
    m = re.search(r'\{.*\}', out, re.S)
    if not m:
        sys.exit("Le modèle n'a pas renvoyé de JSON :\n" + out[:800])
    return json.loads(m.group())


# ───────────────────────────────────────────── utilitaires
def denoyauter(txt):
    """Retire les marqueurs stylistiques que les detecteurs d'IA reperent en premier :
    tiret cadratin surabondant, guillemets courbes, espaces insecables etroites."""
    txt = re.sub(r'\s+—\s+(alors que|et |mais |c\'est |ce qui)', r', \1', txt)
    txt = re.sub(r'\s+—\s+', ' : ', txt)
    txt = txt.replace('—', '-').replace('’', "'").replace(' ', ' ')
    txt = re.sub(r' :\s*:', ' :', txt)
    return txt


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+', '_', s).strip('_')[:40] or 'Entreprise'

def remplacer_1re_phrase(profil, nouvelle):
    m = re.match(r'(.+?[.!?])(\s|$)', profil, re.S)
    return nouvelle.strip() + ' ' + profil[m.end():].lstrip() if m else nouvelle

def tracer(d, dossier):
    ligne = [datetime.date.today().isoformat(), d['entreprise'], d['poste'],
             d.get('type_contrat', ''), d.get('ville', ''), d.get('source', ''),
             d['lane'], d.get('url', ''), '', 'A envoyer',
             (datetime.date.today() + datetime.timedelta(days=7)).isoformat(),
             ' | '.join(d.get('alertes', [])) or dossier]
    existe = os.path.exists(SUIVI)
    with open(SUIVI, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if not existe:
            w.writerow(['Date','Entreprise','Poste','Type','Ville','Source','CV envoye',
                        'Lien offre','Contact','Statut','Relance prevue','Notes'])
        w.writerow(ligne)


# ───────────────────────────────────────────── principal
def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    source = sys.argv[1]
    offre = lire_offre(source)
    print(f"Annonce lue : {len(offre)} caractères")

    lanes = '\n'.join(f'  - {k} : {CVS[k]["titre"]}' for k in MASTERS)
    blocs = open(os.path.join(KIT, 'blocs_motivation.md'), encoding='utf-8').read()

    print("Analyse par claude (30-90 s)...")
    d = demander_au_modele(offre, lanes, blocs)
    d['url'] = source if source.startswith('http') else ''
    d['source'] = 'URL' if d['url'] else 'copier-coller'

    if d['lane'] not in CVS:
        sys.exit(f"Lane inconnue renvoyée par le modèle : {d['lane']}")

    dossier = os.path.join(OUT_ROOT, f"{datetime.date.today():%Y-%m-%d}_{slug(d['entreprise'])}")
    os.makedirs(dossier, exist_ok=True)

    cv = dict(CVS[d['lane']])
    cv['titre']  = d['titre_cv']
    cv['profil'] = remplacer_1re_phrase(cv['profil'], d['phrase_profil'])
    cv['fichier'] = f"CV_{slug(CONTACT['nom'])}_{slug(d['entreprise'])}"

    print("Génération du CV...")
    pdf, dx, pages, tier = render.build(cv, dossier)

    d['lettre'] = denoyauter(d['lettre'])
    open(os.path.join(dossier, 'lettre.txt'), 'w', encoding='utf-8').write(d['lettre'])
    open(os.path.join(dossier, 'offre.txt'), 'w', encoding='utf-8').write(offre)
    json.dump(d, open(os.path.join(dossier, 'dossier.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    tracer(d, dossier)

    print(f"""
┌─ {d['entreprise']} — {d['poste']}
│  {d.get('type_contrat','?')} · {d.get('ville','?')}
│  CV      : {d['lane']}  ({pages} page, palier {tier})
│  Blocs   : {', '.join(d.get('blocs_retenus', []))}
│  Raison  : {d.get('pourquoi','')}
└─ {dossier}""")

    if d.get('alertes'):
        print("\n  /!\\  A VERIFIER AVANT D'ENVOYER")
        for a in d['alertes']:
            print('       - ' + '\n         '.join(textwrap.wrap(a, 86)))
    print("\n  Relis lettre.txt, puis envoie. Le systeme ne soumet rien.\n")
    subprocess.run(['open', dossier])


if __name__ == '__main__':
    main()
