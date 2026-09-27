from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def new_doc(top=1.0, bottom=1.0, side=1.5):
    d = Document()
    for s in d.sections:
        s.top_margin, s.bottom_margin = Cm(top), Cm(bottom)
        s.left_margin = s.right_margin = Cm(side)
    n = d.styles['Normal']
    n.font.name, n.font.size = 'Arial', Pt(9.5)
    n.element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
    pf = n.paragraph_format
    pf.space_before, pf.space_after, pf.line_spacing = Pt(0), Pt(0), 1.0
    return d

def para(d, before=0, after=0, align=None, style=None):
    p = d.add_paragraph(style=style)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    if align: p.alignment = align
    return p

def run(p, text, b=False, i=False, size=9.5, caps=False):
    r = p.add_run(text)
    r.bold, r.italic = b, i
    r.font.size = Pt(size)
    r.font.name = 'Arial'
    r.font.all_caps = caps
    return r

def rich(p, parts, size=9.5):
    """parts: list of (text, bold, italic)"""
    for t, b, i in parts:
        run(p, t, b=b, i=i, size=size)

def bottom_rule(p):
    pPr = p._p.get_or_add_pPr()
    bd = OxmlElement('w:pBdr'); bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'), 'single'); bot.set(qn('w:sz'), '6')
    bot.set(qn('w:space'), '2'); bot.set(qn('w:color'), '444444')
    bd.append(bot); pPr.append(bd)

def section(d, title):
    p = para(d, before=8, after=4)
    run(p, title.upper(), b=True, size=11.5)
    bottom_rule(p)

def right_tab(p, width_cm):
    p.paragraph_format.tab_stops.add_tab_stop(Cm(width_cm), WD_TAB_ALIGNMENT.RIGHT)

def bullet(d, parts):
    p = para(d, before=0.5, after=0.5, style='List Bullet')
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    rich(p, parts)
    return p


from docx.shared import Emu
import copy

def float_picture(doc, paragraph, image_path, width_cm, from_right_cm, from_top_cm):
    """Insere une image ANCREE (flottante) en haut a droite : le texte reste lineaire
    pour les parseurs ATS, l'image ne s'intercale pas dans le flux."""
    run = paragraph.add_run()
    run.add_picture(image_path, width=Cm(width_cm))
    inline = run._r.find(qn('w:drawing'))[0]          # <wp:inline>
    anchor = OxmlElement('wp:anchor')
    for k, v in [('distT','0'),('distB','0'),('distL','114300'),('distR','114300'),
                 ('simplePos','0'),('relativeHeight','2'),('behindDoc','0'),
                 ('locked','0'),('layoutInCell','1'),('allowOverlap','1')]:
        anchor.set(k, v)

    sp = OxmlElement('wp:simplePos'); sp.set('x','0'); sp.set('y','0'); anchor.append(sp)

    hp = OxmlElement('wp:positionH'); hp.set('relativeFrom','margin')
    off = OxmlElement('wp:posOffset')
    page_w = doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin
    off.text = str(int(page_w - Cm(width_cm) - Cm(from_right_cm)))
    hp.append(off); anchor.append(hp)

    vp = OxmlElement('wp:positionV'); vp.set('relativeFrom','paragraph')
    off2 = OxmlElement('wp:posOffset'); off2.text = str(int(Cm(from_top_cm)))
    vp.append(off2); anchor.append(vp)

    for tag in ('wp:extent','wp:effectExtent','wp:docPr','a:graphic'):
        el = inline.find(qn(tag))
        if el is not None:
            anchor.append(copy.deepcopy(el))
    wrap = OxmlElement('wp:wrapSquare'); wrap.set('wrapText','bothSides')
    anchor.insert(list(anchor).index(anchor.find(qn('wp:docPr'))), wrap)

    drawing = run._r.find(qn('w:drawing'))
    drawing.remove(inline)
    drawing.append(anchor)


W = 18.0  # usable width in cm with 1.5cm margins on A4

def job(d, title, org, dates, sub):
    p = para(d, before=5, after=0); right_tab(p, W)
    run(p, title, b=True); run(p, " | " + org)
    run(p, "\t"); run(p, dates, b=True)
    q = para(d, before=0, after=1.5); run(q, sub, i=True, size=9)

