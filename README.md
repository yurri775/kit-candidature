# Kit candidature

Un kit pour chercher un emploi sans y passer ses soirées :

1. **Des CV « maîtres » propres et lisibles par les ATS**, générés en PDF et DOCX depuis un seul fichier texte.
2. **Un dossier par offre en 1 commande** : CV adapté (titre + 1re phrase du profil), lettre assemblée
   à partir de *tes* blocs, alertes (contrat, années d'expérience, techno manquante), suivi CSV.
3. **Des scripts qui remplissent les formulaires** (LinkedIn Candidature simplifiée pour commencer)
   dans ton propre navigateur. Ils ne répondent qu'avec *tes* réponses et s'arrêtent sur toute question inconnue.

## Installation (macOS)

```sh
brew install tectonic                 # compile les PDF
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
playwright install chromium           # pour auto/
```

Il faut aussi la police **Arial** (présente sur macOS) et, pour `postule.py`,
le CLI [`claude`](https://docs.claude.com/claude-code) connecté.

## 1. Tes CV maîtres

- Remplace l'exemple fictif (Camille Martin) dans `cv/content.py` par ton parcours.
  Balisage : `*gras*`, `//italique//`.
- Photo facultative : dépose `cv/photo.jpg` (elle n'est jamais publiée, cf. `.gitignore`).
  Un CV peut la retirer avec `sans_photo=True` (certaines entreprises l'exigent).
- Génère : `python cv/render.py` → `cv/out/`

Règles tenues par le générateur :
- **Arial sans ligatures** : Helvetica produit `ﬁ`/`ﬂ`, que les ATS ne lisent pas (« certiﬁcation »).
- **Une page**, réduite automatiquement si ça déborde.
- DOCX **sans tableau ni colonne** : le texte reste linéaire pour les parseurs.

## 2. Un dossier par offre

1. Écris `kit/profil.md` : les faits sur toi que l'IA a le droit d'utiliser, et rien d'autre.
2. Écris `kit/blocs_motivation.md` : tes accroches et paragraphes, avec tes vrais chiffres.
3. Lance :

```sh
python cv/postule.py https://url-de-l-offre     # ou : pbpaste | python cv/postule.py -
python cv/lettres_pdf.py ~/Downloads/candidatures   # lettres .txt → PDF propres
```

Le script **ne soumet rien** : tu relis, tu envoies.

## 3. Remplissage automatique (facultatif)

```sh
./auto/navigateur.sh     # navigateur sur un profil à part : connecte-toi à LinkedIn une fois
# remplis auto/moi.py avec TES réponses (salaire, préavis, ville…)
python auto/linkedin_easy_apply.py <dossier> <id_offre_linkedin>          # s'arrête avant l'envoi
python auto/linkedin_easy_apply.py <dossier> <id_offre_linkedin> --send   # envoie
```

Garde-fous :
- une question non prévue dans `moi.py` **arrête** le script (il n'invente jamais une réponse) ;
- les consentements marketing / « futures opportunités » sont refusés, seul le consentement nécessaire à la candidature est coché ;
- sans `--send`, rien ne part.

Va doucement : LinkedIn limite les comportements automatisés, reste à quelques candidatures par heure.

## Ce qu'on ne met jamais dans le dépôt

Ta photo, tes CV générés, ton suivi, tes mots de passe : tout est dans `.gitignore`.
Garde ton propre `content.py` dans un fork **privé**.
