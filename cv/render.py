# -*- coding: utf-8 -*-
import re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import CVS, CONTACT, FORMATION, CERTIFS, LANGUES

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = re.compile(r'(\*[^*]+\*|//[^/]+//)')

def parse(text):
    """'*gras* //ital//' -> [(chunk, bold, italic), ...]"""
    out = []
    for part in TOKEN.split(text):
        if not part: continue
        if part.startswith('*') and part.endswith('*') and len(part) > 2:
            out.append((part[1:-1], True, False))
        elif part.startswith('//') and part.endswith('//') and len(part) > 4:
            out.append((part[2:-2], False, True))
        else:
            out.append((part, False, False))
    return out

# ───────────────────────────────── LaTeX
ESC = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
       '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
def esc(s): return ''.join(ESC.get(c, c) for c in s)

def tex(text):
    out = []
    for chunk, b, i in parse(text):
        c = esc(chunk)
        if b: c = r'\textbf{' + c + '}'
        if i: c = r'\emph{' + c + '}'
        out.append(c)
    return ''.join(out)

PRE = r"""\documentclass[10pt,a4paper]{article}
\usepackage{fontspec}
\setmainfont{Arial}[Ligatures=NoCommon,Kerning=Off]
\usepackage[a4paper,top=%(top)s,bottom=%(bot)s,left=1.35cm,right=1.35cm]{geometry}
\usepackage[%(lang)s]{babel}
\usepackage{enumitem}\usepackage{titlesec}\usepackage{xcolor}
\usepackage[hidelinks]{hyperref}\usepackage{graphicx}\usepackage{microtype}
\definecolor{ink}{HTML}{111111}\definecolor{rule}{HTML}{444444}
\color{ink}\pagestyle{empty}\setlength{\parindent}{0pt}
\titleformat{\section}{\bfseries\large}{}{0em}{\MakeUppercase}[\vspace{-0.9ex}\color{rule}\rule{\linewidth}{0.7pt}]
\titlespacing*{\section}{0pt}{%(sec)s}{0.4ex}
\newcommand{\job}[4]{\textbf{#1} \textbar{} #2 \hfill \textbf{#3}\\[0.15ex]\textit{\small #4}\par\vspace{0.3ex}}
\setlist[itemize]{leftmargin=1.0em,itemsep=%(item)s,topsep=0.25ex,parsep=0pt,label=\textbullet}
\usepackage{anyfontsize}
\renewcommand{\small}{\fontsize{%(body)s}{%(lead)s}\selectfont}
\begin{document}
"""

SECTIONS_FR = dict(profil='Profil', comp='Compétences techniques', exp='Expérience professionnelle',
                   proj='Projets', form='Formation', cert='Certifications et langues')
SECTIONS_EN = dict(profil='Profile', comp='Skills', exp='Professional experience',
                   proj='Projects', form='Education', cert='Certifications & languages')

def build_tex(cv, tier):
    L = [PRE % dict(tier, lang=cv.get('lang', 'french'))]
    S = dict(SECTIONS_EN if cv.get('lang') == 'english' else SECTIONS_FR)
    S.update(cv.get('sections', {}))
    A = L.append
    # sans photo si le CV le demande (ex. charte diversité Société Générale) ou si photo.jpg est absent
    photo = not cv.get('sans_photo') and os.path.exists(os.path.join(HERE, 'photo.jpg'))
    A(r'\noindent' + '\n' + r'\begin{minipage}[b]{%s\textwidth}' % ('0.775' if photo else '1.0'))
    A(r'{\huge\bfseries ' + esc(CONTACT['nom']) + r'}\\[0.6ex]')
    A(r'{\large ' + tex(cv['titre']) + r'}\\[0.9ex]')
    C = dict(CONTACT); C.update(cv.get('contact', {}))
    A(r'{\small ' + tex(C['l1']) + r'\\[0.25ex]')
    A(tex(C['l2']) + r'\\[0.25ex]')
    A(tex(C['l3']) + '}')
    if photo:
        A(r'\end{minipage}\hfill' + '\n' + r'\begin{minipage}[b]{0.19\textwidth}')
        A(r'\raggedleft\includegraphics[width=2.75cm]{photo.jpg}' + '\n' + r'\end{minipage}' + '\n')
    else:
        A(r'\end{minipage}' + '\n')

    A(r'\section{%s}' % esc(S['profil']) + '\n' + r'\small')
    A(tex(cv['profil']) + '\n')

    A(r'\section{%s}' % esc(cv.get('titre_competences', S['comp'])) + '\n' + r'\small' + '\n' + r'\begin{itemize}')
    for s in cv['competences']: A(r'\item ' + tex(s))
    A(r'\end{itemize}' + '\n')

    A(r'\section{%s}' % esc(S['exp']) + '\n' + r'\small')
    for k, e in enumerate(cv['experiences']):
        A(r'\job{%s}{%s}{%s}{%s}' % (tex(e['titre']), tex(e['org']), tex(e['dates']), tex(e['sub'])))
        if e['bullets']:
            A(r'\begin{itemize}')
            for b in e['bullets']: A(r'\item ' + tex(b))
            A(r'\end{itemize}')
        if k < len(cv['experiences']) - 1: A(r'\vspace{0.35ex}' + '\n')

    if cv.get('projets'):
        A(r'\section{%s}' % esc(S['proj']) + '\n' + r'\small' + '\n' + r'\begin{itemize}')
        for p in cv['projets']: A(r'\item ' + tex(p))
        A(r'\end{itemize}' + '\n')

    A(r'\section{%s}' % esc(S['form']) + '\n' + r'\small')
    lines_ = []
    for t, rr, d, sub in cv.get('formation', FORMATION):
        lines_.append(r'\textbf{%s}%s \hfill \textbf{%s}' % (esc(t), esc(rr), esc(d)))
        if sub: lines_.append(r'{\footnotesize\itshape ' + esc(sub) + '}')
    A(('\\\\\n').join(lines_) + '\n')

    A(r'\section{%s}' % esc(S['cert']) + '\n' + r'\small')
    A(tex(cv.get('certifs', CERTIFS)) + r'\\' + '\n' + tex(cv.get('langues', LANGUES)))
    A(r'\end{document}')
    return '\n'.join(L)

# ───────────────────────────────── DOCX
from docxlib import *

def build_docx(cv, path):
    d = new_doc(top=0.7, bottom=0.45, side=1.35)
    p = para(d, after=1)
    if not cv.get('sans_photo') and os.path.exists(os.path.join(HERE, 'photo.jpg')):
        float_picture(d, p, os.path.join(HERE, 'photo.jpg'), width_cm=2.75, from_right_cm=0.0, from_top_cm=0.0)
    run(p, CONTACT['nom'], b=True, size=20)
    p = para(d, after=3); rich(p, parse(cv['titre']), size=12)
    C = dict(CONTACT); C.update(cv.get('contact', {}))
    for key in ('l1', 'l2', 'l3'):
        p = para(d, after=0); rich(p, parse(C[key]), size=9)

    S = dict(SECTIONS_EN if cv.get('lang') == 'english' else SECTIONS_FR)
    S.update(cv.get('sections', {}))
    section(d, S['profil'])
    p = para(d, after=0); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; rich(p, parse(cv['profil']))

    section(d, cv.get('titre_competences', S['comp']))
    for s in cv['competences']: bullet(d, parse(s))

    section(d, S['exp'])
    for e in cv['experiences']:
        job(d, e['titre'], e['org'], e['dates'], e['sub'])
        for b in e['bullets']: bullet(d, parse(b))

    if cv.get('projets'):
        section(d, S['proj'])
        for x in cv['projets']: bullet(d, parse(x))

    section(d, S['form'])
    for t, rest, dates, sub in cv.get('formation', FORMATION):
        p = para(d, after=0); right_tab(p, W)
        run(p, t, b=True); run(p, rest); run(p, "\t"); run(p, dates, b=True)
        if sub:
            q = para(d, after=1); run(q, sub, i=True, size=8.5)

    section(d, S['cert'])
    p = para(d, after=0); rich(p, parse(cv.get('certifs', CERTIFS)))
    p = para(d, after=0); rich(p, parse(cv.get('langues', LANGUES)))
    d.save(path)

# ───────────────────────────────── build
TIERS = [dict(body='9.0', lead='11.0', top='0.7cm', bot='0.45cm', sec='1.0ex', item='0.05ex'),
         dict(body='8.7', lead='10.6', top='0.6cm', bot='0.40cm', sec='0.8ex', item='0.0ex'),
         dict(body='8.4', lead='10.2', top='0.6cm', bot='0.40cm', sec='0.7ex', item='0.0ex'),
         dict(body='8.1', lead='9.8',  top='0.5cm', bot='0.35cm', sec='0.6ex', item='-0.1ex')]

from pypdf import PdfReader

def build(cv, outdir, name=None):
    """Construit un CV (PDF + DOCX) dans outdir. Retourne (pdf, docx, pages, tier)."""
    os.makedirs(outdir, exist_ok=True)
    name = name or cv['fichier']
    for ti, tier in enumerate(TIERS):
        tp = os.path.join(HERE, name + '.tex')
        open(tp, 'w').write(build_tex(cv, tier))
        res = subprocess.run(['tectonic', '-X', 'compile', '-o', outdir, tp],
                             capture_output=True, cwd=HERE)
        if res.returncode:
            raise RuntimeError('tectonic:\n' + res.stderr.decode()[-1200:])
        pdf = os.path.join(outdir, name + '.pdf')
        n = len(PdfReader(pdf).pages)
        if n == 1:
            break
    try: os.remove(tp)
    except OSError: pass
    dx = os.path.join(outdir, name + '.docx')
    build_docx(cv, dx)
    return pdf, dx, n, ti


def build_all():
    OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
    report = []
    for key, cv in CVS.items():
        pdf, dx, n, ti = build(cv, OUT)
        txt = '\n'.join(pg.extract_text() for pg in PdfReader(pdf).pages)
        lig = len(re.findall('[\ufb00-\ufb06]', txt))
        resid = len(re.findall(r'//|(?<!\S)\*|\*(?!\S)', txt))
        report.append((cv['fichier'], n, lig, ti, resid))
    print(f"{'fichier':52} pages lig tier balisage-residuel")
    for n_, pg, lig, ti, res in report:
        flag = '' if (pg == 1 and lig == 0 and res == 0) else '  <-- A VERIFIER'
        print(f'{n_:52} {pg:5} {lig:3} {ti:4} {res:6}{flag}')


if __name__ == '__main__':
    build_all()
