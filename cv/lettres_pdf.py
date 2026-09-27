# -*- coding: utf-8 -*-
"""Convertit chaque lettre.txt / cover_letter.txt / lettre_motivation.txt d'un dossier de candidatures
en PDF propre (Arial, sans ligatures, lisible par les ATS).

    python cv/lettres_pdf.py ~/Downloads/candidatures
"""
import os, sys, glob, re, subprocess
B = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Downloads/candidatures')
T = r'''\documentclass[11pt]{article}
\usepackage[a4paper,margin=2.2cm]{geometry}
\usepackage{fontspec}\setmainfont{Arial}[Ligatures=NoCommon]
\setlength{\parindent}{0pt}\setlength{\parskip}{8pt}\pagestyle{empty}
\begin{document}
%s
\end{document}'''
def esc(s):
    for a, b in [('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'), ('_', r'\_'),
                 ('{', r'\{'), ('}', r'\}'), ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(a, b)
    return s
ok = 0
for f in sorted(sum((glob.glob(os.path.join(B, '**', n), recursive=True) for n in ('lettre.txt', 'cover_letter.txt', 'lettre_motivation.txt')), [])):
    d = os.path.dirname(f); name = 'Lettre_' + os.path.basename(d)
    paras = [esc(p).replace('\n', r'\\') for p in re.split(r'\n\s*\n', open(f).read().strip())]
    tex = os.path.join(d, name + '.tex'); open(tex, 'w').write(T % '\n\n'.join(paras))
    r = subprocess.run(['tectonic', '-X', 'compile', '-o', d, tex], capture_output=True)
    os.remove(tex)
    if r.returncode: print('ERREUR', d, r.stderr.decode()[-300:])
    else: ok += 1
print(ok, 'lettre(s) en PDF')
