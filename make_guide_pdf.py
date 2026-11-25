"""Renders STEP_BY_STEP_GUIDE.md to CampusCart_Detailed_Guide.pdf (simple markdown subset)."""
import os
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

R = os.path.dirname(os.path.abspath(__file__))
ss = getSampleStyleSheet()
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9, leading=12)
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=14)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11.5)
C = ParagraphStyle("C", parent=ss["Code"], fontSize=7.6, leading=9.5, backColor=colors.HexColor("#f3f3f3"))


def inline(t):
    t = escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", t)
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)


story, code, tbl = [], None, []
lines = open(os.path.join(R, "STEP_BY_STEP_GUIDE.md"), encoding="utf-8").read().splitlines()


def flush_tbl():
    global tbl
    if tbl:
        rows = [[Paragraph(inline(c.strip()), B) for c in r.strip("|").split("|")] for r in tbl
                if not re.match(r"^\|[-| ]+\|$", r)]
        t = Table(rows, colWidths=[0.7 * cm, 4.6 * cm, 6 * cm, 5.7 * cm], repeatRows=1)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce6f1"))]))
        story.extend([t, Spacer(1, 6)])
        tbl = []


for ln in lines:
    s = ln.strip()
    if s.startswith("```"):
        if code is None:
            code = []
        else:
            story.extend([Preformatted("\n".join(code), C), Spacer(1, 4)])
            code = None
        continue
    if code is not None:
        code.append(ln.replace("📸", "[screenshot]"))
        continue
    ln = ln.replace("📸", "[screenshot]").replace("✔", "OK").replace("–", "-").replace("→", "->").replace("≈", "~").replace("–", "-")
    s = ln.strip()
    if s.startswith("|"):
        tbl.append(s)
        continue
    flush_tbl()
    if s.startswith("# "): story.append(Paragraph(inline(s[2:]), H1))
    elif s.startswith("## "): story.append(Paragraph(inline(s[3:]), H1))
    elif s.startswith("### "): story.append(Paragraph(inline(s[4:]), H2))
    elif s == "---" or not s: story.append(Spacer(1, 3))
    else:
        indent = (len(ln) - len(ln.lstrip())) * 2
        story.append(Paragraph(inline(s), ParagraphStyle("i", parent=B, leftIndent=indent)))
flush_tbl()
SimpleDocTemplate(os.path.join(R, "CampusCart_Detailed_Guide.pdf"), pagesize=A4, leftMargin=2 * cm,
                  rightMargin=2 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm).build(story)
print("ok")
