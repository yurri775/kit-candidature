# LinkedIn « Candidature simplifiée », pilotée dans ton navigateur (port CDP 9334 par défaut, variable CDP_PORT).
# usage : python auto/linkedin_easy_apply.py <dossier> <job_id> [--send]
# Parcourt les étapes : téléphone, CV du dossier, questions (réponses ci-dessous), lettre.
# S'arrête et affiche la question si elle n'est pas couverte. Sans --send, s'arrête avant « Envoyer ».
import sys, glob, os, re
from playwright.sync_api import sync_playwright

D, JOB = sys.argv[1], sys.argv[2]
SEND = '--send' in sys.argv
cv = glob.glob(D + '/CV_*.pdf'); cv = [c for c in cv if 'sans_photo' not in c][0]
lt_txt = ''
for n in ('cover_letter.txt', 'lettre_motivation.txt'):
    if os.path.exists(os.path.join(D, n)): lt_txt = open(os.path.join(D, n)).read().strip()
lt_pdf = (glob.glob(D + '/Lettre_*.pdf') or [None])[0]

import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from moi import *
# (mots-clés dans la question, réponse). Les valeurs viennent de moi.py.
REP_TEXTE = [
    (r'^headline|^titre', TITRE),
    (r'^summary|^résumé$|^resume$', RESUME),
    (r'salai|salary|rémunération|remuneration|compensation|package', SALAIRE_ANNUEL),
    (r'préavis|preavis|notice', PREAVIS_MOIS),
    (r'linkedin', LINKEDIN),
    (r'site|portfolio|website|github', SITE),
    (r'ville|city|localisation|location', VILLE),
    (TECHNOS_PRINCIPALES, ANNEES_TECHNOS_PRINCIPALES),
    (r"ann[ée]es?|years?|expérience|experience", ANNEES_EXPERIENCE),
]
REP_OUI_NON = [
    (r'future (job )?opportunit|futures? opportunit|talent pool|vivier|newsletter|marketing', 'Non'),  # réutilisation des données : Non
    (r'(need|require|nécessit|besoin|avez-vous besoin).{0,60}(sponsor|visa|permis)', 'Non'),
    (r'autoris|authori[sz]|allowed to work|droit de travailler|legally|eligible to work|work permit|EU citizen|citoyen|without .{0,40}(sponsor|visa)', 'Oui'),
    (r'sponsor|visa', 'Non'),
    (r'déménag|relocat|reloc|commut|trajet|se déplacer|travel|on-?site|sur site|hybrid|hybride|présentiel', 'Oui'),
    (r'master|bac\s*\+\s*5|bachelor|licence|diplôm|degree', 'Oui'),
    (r'permis|driv', 'Oui'),
    (r'français|french|anglais|english', 'Oui'),
    (r'disponib|available|immediately|start', 'Oui'),
    (r'python|sql|docker|kubernetes|azure|java|react|power ?bi|linux|git|ci/cd|devops|cloud|machine learning|llm|ia\b|ai\b|data|cyber|sécurité|security', 'Oui'),
]
NIVEAUX = {r'français|french': ['Natif ou bilingue', 'Native or bilingual', 'Natif', 'Native'],
           r'anglais|english': ['Courant', 'Professionnel', 'Professional', 'Fluent', 'Compétence professionnelle complète', 'Full professional proficiency'],
           r'allemand|german|luxembourg': ['Aucun', 'None', 'Élémentaire', 'Elementary']}


def cherche(regles, q):
    for pat, v in regles:
        if re.search(pat, q, re.I): return v
    return None


with sync_playwright() as p:
    pg = [x for x in p.chromium.connect_over_cdp(f"http://127.0.0.1:{_os.environ.get('CDP_PORT', '9334')}").contexts[0].pages if 'linkedin' in x.url][-1]
    pg.bring_to_front(); W = pg.wait_for_timeout
    if f'/jobs/view/{JOB}' not in pg.url or 'Postuler chez' not in pg.locator('body').inner_text():
        pg.goto(f'https://www.linkedin.com/jobs/view/{JOB}/'); W(6000)
        t = pg.locator('main').inner_text()
        if 'Candidature envoyée' in t: print('DEJA POSTULE'); sys.exit(0)
        [b for b in pg.locator('button:visible').all() if 'Candidature simplifiée' in (b.inner_text() or '')][0].click(); W(4000)

    def label(el):
        return el.evaluate("""e => { let l = (e.labels && e.labels[0]) ? e.labels[0].innerText : (e.getAttribute('aria-label') || '');
            const fs = e.closest('fieldset'); if (fs && fs.querySelector('legend')) l = fs.querySelector('legend').innerText + ' ' + l;
            return l.replace(/\\s+/g, ' ').trim(); }""")

    for etape in range(12):
        body = pg.locator('body').inner_text()
        i = body.find('Postuler chez'); print('--- étape', body[i:i+120].split('\n')[2:3], )
        # téléphone
        for el in pg.locator('input[type=tel]:visible').all():
            if not el.input_value(): el.fill(TEL_NATIONAL)
        # CV : téléverser celui du dossier s'il n'est pas déjà sélectionné
        f = pg.locator('input[type=file]')
        imp = [b for b in pg.locator('button:visible, label:visible, span:visible').all() if (b.inner_text() or '').strip() in ('Importer le CV', 'Upload resume')]
        if imp and os.path.basename(cv) not in body:
            with pg.expect_file_chooser() as fc: imp[0].click()
            fc.value.set_files(cv); W(6000); print('CV importé', os.path.basename(cv)); body = pg.locator('body').inner_text()
        elif f.count() and os.path.basename(cv) not in body and 'importez un CV' in body:
            ups = [x for x in f.all() if 'resume' in (x.get_attribute('id') or '').lower() or 'cv' in (x.get_attribute('name') or '').lower()] or [f.first]
            ups[0].set_input_files(cv); W(5000); print('CV téléversé', os.path.basename(cv))
            body = pg.locator('body').inner_text()
            if f.count() > 1 and lt_pdf:
                for x in f.all():
                    if 'cover' in (x.get_attribute('id') or '').lower() or 'lettre' in label(x).lower():
                        x.set_input_files(lt_pdf); W(4000); print('lettre téléversée')
        inconnues = []
        # textes et zones de texte
        for el in pg.locator('input[type=text]:visible, input[type=number]:visible, textarea:visible').all():
            q = label(el)
            if not q or q == 'Photo' or 'Rechercher' in q or el.input_value(): continue
            if el.evaluate('e=>e.tagName') == 'TEXTAREA' and re.search(r'lettre|cover|motivation|message|additional|complément', q, re.I):
                el.fill(lt_txt[:3900]); print('lettre collée'); continue
            v = cherche(REP_TEXTE, q)
            if v is None: inconnues.append('TEXTE: ' + q); continue
            el.fill(v); W(400)
            # champs à suggestion (ville)
            opt = pg.locator('[role=option]:visible')
            if opt.count(): opt.first.click(); W(400)
            print('  ', q[:70], '->', v)
        # listes déroulantes
        for el in pg.locator('select:visible').all():
            q = label(el); opts = el.evaluate('s=>[...s.options].map(o=>o.text.trim())')
            cur = el.evaluate('s=>s.options[s.selectedIndex] ? s.options[s.selectedIndex].text.trim() : ""')
            if cur and not re.search(r'sélection|select an option|choisir', cur, re.I): continue
            choix = None
            for pat, prefs in NIVEAUX.items():
                if re.search(pat, q, re.I) and not re.search(r'\?.*(oui|yes)', q, re.I):
                    choix = next((o for pr in prefs for o in opts if o.lower() == pr.lower()), None)
            if not choix and re.search(r'start|commencer|disponib|available|notice|préavis', q, re.I):
                choix = next((o for pr in ('Immediately', 'Immédiatement', 'Within 1 month', 'Moins d’un mois', "Moins d'un mois") for o in opts if o == pr), None)
            if not choix:
                v = cherche(REP_OUI_NON, q)
                if v: choix = next((o for o in opts if o.lower() in ((v.lower(), 'yes') if v == 'Oui' else (v.lower(), 'no'))), None)
            if not choix: inconnues.append(f'LISTE: {q} {opts}'); continue
            el.select_option(label=choix); W(300); print('  ', q[:70], '->', choix)
        # boutons radio (par groupe)
        noms = []
        for r in pg.locator('input[type=radio]').all():
            n = r.get_attribute('name')
            if n and n not in noms: noms.append(n)
        for n in noms:
            grp = pg.locator(f'input[type=radio][name="{n}"]')
            if any(x.is_checked() for x in grp.all()): continue
            q = grp.first.evaluate("""e => { let x = e; for (let i = 0; i < 8 && x; i++) { x = x.parentElement;
                    if (x && x.innerText && x.innerText.replace(/\\s+/g, ' ').length > 40) return x.innerText.replace(/\\s+/g, ' ').slice(0, 300); } return ''; }""")
            v = cherche(REP_OUI_NON, q)
            vals = {x.evaluate("e=>{ const l = (e.labels&&e.labels[0]) ? e.labels[0].innerText : ''; if (l.trim()) return l.trim();"
                               " let y = e.parentElement; for (let i = 0; i < 3 && y; i++) { if (y.innerText && y.innerText.trim()) return y.innerText.trim(); y = y.parentElement; } return e.value; }"): x for x in grp.all()}
            cible = None
            if v: cible = next((x for k, x in vals.items() if k.lower() in ((v.lower(), 'yes') if v == 'Oui' else (v.lower(), 'no'))), None)
            if not cible: inconnues.append(f'RADIO: {q} {list(vals)}'); continue
            cible.evaluate('e=>e.click()'); W(300); print('  ', q[:70], '->', v)
        if inconnues:
            print('QUESTIONS NON COUVERTES :'); [print('  ', x) for x in inconnues]; sys.exit(2)
        # consentement obligatoire au traitement des données de la candidature (jamais les options marketing)
        for c in pg.locator('input[type=checkbox]').all():
            try:
                ctx_txt = c.evaluate("e => (e.closest('fieldset') || e.parentElement.parentElement.parentElement).innerText")
                if re.search(r'consent|privacy|confidentialit|données personnelles|personal data', ctx_txt, re.I) and not re.search(r'newsletter|marketing|offres similaires|job alert', ctx_txt, re.I):
                    if not c.is_checked(): c.evaluate('e=>e.click()'); W(300); print('   consentement candidature coché')
            except Exception: pass
        # ne pas s'abonner à l'entreprise
        for c in pg.locator('input[type=checkbox]').all():
            try:
                if 'suivre' in label(c).lower() or 'follow' in label(c).lower():
                    if c.is_checked(): c.evaluate('e=>e.click()')
            except Exception: pass
        btns = {b.inner_text().strip(): b for b in pg.locator('button:visible').all() if (b.inner_text() or '').strip()}
        if 'Envoyer la candidature' in btns or 'Submit application' in btns:
            pg.screenshot(path=D + '/avant_envoi.png')
            if not SEND: print('PRET A ENVOYER'); sys.exit(0)
            (btns.get('Envoyer la candidature') or btns['Submit application']).click(); W(6000)
            t = pg.locator('body').inner_text()
            pg.screenshot(path=D + '/confirmation_envoi.png')
            print('CONFIRME' if re.search(r'candidature a été envoyée|Candidature envoyée|application was sent', t) else 'NON CONFIRME ' + t[:300])
            for b in pg.locator('button:visible').all():
                if (b.inner_text() or '').strip() in ('Terminé', 'Done', 'OK'): b.click(); break
            sys.exit(0)
        nxt = btns.get('Suivant') or btns.get('Vérifier') or btns.get('Next') or btns.get('Review')
        if not nxt: print('pas de bouton suivant', list(btns)[:15]); sys.exit(3)
        nxt.click(); W(2500)
        err = [l for l in pg.locator('body').inner_text().split('\n') if re.search(r'Veuillez|obligatoire|Enter a valid|requis', l)]
        if err: print('ERREURS', err[:5])
