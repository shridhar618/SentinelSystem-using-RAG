"""
scripts/export_policies_pdf.py

Renders the organisation policies in policy_corpus/organization/*.md to review
copies in backend/policies_pdf/:

  - one PDF per policy, and
  - a single master document with a cover page, a table of contents and all
    nine policies in document-ID order, as both PDF and Word:
        Evolish_Policy_Manual.pdf
        Evolish_Policy_Manual.docx   (needs the `pandoc` command)

The Markdown files remain the source that is ingested; these copies are for
reading and sign-off only.

Usage (run from backend/):
    pip install reportlab
    python scripts/export_policies_pdf.py
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents

BACKEND_ROOT = Path(__file__).resolve().parent.parent
ORG_DIR = BACKEND_ROOT / "policy_corpus" / "organization"
OUT_DIR = BACKEND_ROOT / "policies_pdf"
NON_POLICY_FILES = {"README.md"}
COMPANY = "Evolish Technologies Pvt. Ltd."
MANUAL_TITLE = "Information Security and Data Governance Policy Manual"
MANUAL_NAME = "Evolish_Policy_Manual"
DISCLAIMER = (
    "Evolish Technologies Pvt. Ltd. is a fictional company. These policies were written for this academic "
    "project and modelled on RBI, DPDP Act 2023 and ISO/IEC 27001 practices."
)
INK = colors.HexColor("#1F2A44")
MUTED = colors.HexColor("#5A6478")
RULE = colors.HexColor("#B8C0CC")
SHADE = colors.HexColor("#EEF1F6")

_base = getSampleStyleSheet()
STYLES = {
    "title": ParagraphStyle("title", parent=_base["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24,
                            textColor=INK, alignment=TA_CENTER, spaceAfter=4),
    "company": ParagraphStyle("company", parent=_base["Normal"], fontName="Helvetica", fontSize=11, leading=14,
                              textColor=INK, alignment=TA_CENTER, spaceAfter=12),
    "h_main": ParagraphStyle("h_main", parent=_base["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16,
                             textColor=INK, spaceBefore=14, spaceAfter=5, keepWithNext=True),
    "h_clause": ParagraphStyle("h_clause", parent=_base["Heading3"], fontName="Helvetica-Bold", fontSize=10.5,
                               leading=14, textColor=INK, spaceBefore=9, spaceAfter=3, keepWithNext=True),
    "body": ParagraphStyle("body", parent=_base["Normal"], fontName="Helvetica", fontSize=9.5, leading=13.5,
                           spaceAfter=5),
    "bullet": ParagraphStyle("bullet", parent=_base["Normal"], fontName="Helvetica", fontSize=9.5, leading=13.5,
                             leftIndent=14, bulletIndent=4, spaceAfter=3),
    "cell": ParagraphStyle("cell", parent=_base["Normal"], fontName="Helvetica", fontSize=8, leading=10.5),
    "cell_head": ParagraphStyle("cell_head", parent=_base["Normal"], fontName="Helvetica-Bold", fontSize=8,
                                leading=10.5, textColor=INK),
    "cover_company": ParagraphStyle("cover_company", parent=_base["Normal"], fontName="Helvetica-Bold", fontSize=16,
                                    leading=20, textColor=INK, alignment=TA_CENTER, spaceAfter=18),
    "cover_title": ParagraphStyle("cover_title", parent=_base["Title"], fontName="Helvetica-Bold", fontSize=26,
                                  leading=32, textColor=INK, alignment=TA_CENTER, spaceAfter=14),
    "cover_note": ParagraphStyle("cover_note", parent=_base["Normal"], fontName="Helvetica", fontSize=10, leading=14,
                                 textColor=MUTED, alignment=TA_CENTER, spaceAfter=6),
    "toc_heading": ParagraphStyle("toc_heading", parent=_base["Heading1"], fontName="Helvetica-Bold", fontSize=16,
                                  leading=20, textColor=INK, spaceAfter=10),
    "toc_entry": ParagraphStyle("toc_entry", parent=_base["Normal"], fontName="Helvetica", fontSize=11, leading=22),
}


def inline(text: str) -> str:
    """Markdown inline markup -> reportlab paragraph markup."""
    text = escape(text.strip())
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.5">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def parse_table(lines):
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    return [row for row in rows if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)]


def build_table(rows, width):
    columns = len(rows[0])
    small = columns > 6
    cell = ParagraphStyle("c", parent=STYLES["cell"], fontSize=6.6 if small else 8, leading=8.6 if small else 10.5)
    head = ParagraphStyle("h", parent=STYLES["cell_head"], fontSize=6.6 if small else 8, leading=8.6 if small else 10.5)
    data = [[Paragraph(inline(value), head if index == 0 else cell) for value in row] for index, row in enumerate(rows)]
    if small:  # wide matrix: a broad first column, the rest shared evenly
        first = width * 0.24
        widths = [first] + [(width - first) / (columns - 1)] * (columns - 1)
    else:
        longest = [max(len(row[i]) for row in rows) for i in range(columns)]
        weights = [min(max(length, 8), 46) for length in longest]
        widths = [width * weight / sum(weights) for weight in weights]
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SHADE),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 if small else 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 if small else 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


class Policy:
    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").splitlines()
        self.title = self.lines[0].lstrip("# ").strip()
        self.doc_id = next(
            (m.group(1) for line in self.lines if (m := re.match(r"\|\s*Document ID\s*\|\s*(\S+)", line))), "")


def load_policies():
    paths = [path for path in ORG_DIR.glob("*.md") if path.name not in NON_POLICY_FILES]
    return sorted((Policy(path) for path in paths), key=lambda policy: policy.doc_id)


def story_for(policy: Policy, width):
    """Flowables for one policy. The title paragraph carries the policy so
    the manual can pick it up for the table of contents and the header."""
    lines, story, index = policy.lines, [], 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
        elif line.startswith("# "):
            title = Paragraph(inline(line[2:]), STYLES["title"])
            title.policy = policy
            story += [title, Paragraph(COMPANY, STYLES["company"])]
            index += 1
        elif line.startswith("## "):
            heading = line[3:].strip()
            clause = re.match(r"\d+\.\d+ ", heading)
            story.append(Paragraph(inline(heading), STYLES["h_clause" if clause else "h_main"]))
            index += 1
        elif line.startswith("|"):
            block = []
            while index < len(lines) and lines[index].startswith("|"):
                block.append(lines[index])
                index += 1
            story += [build_table(parse_table(block), width), Spacer(1, 6)]
        elif line.startswith("- "):
            story.append(Paragraph(inline(line[2:]), STYLES["bullet"], bulletText="•"))
            index += 1
        else:
            story.append(Paragraph(inline(line), STYLES["body"]))
            index += 1
    return story


def _page_furniture(canvas, document, left, right):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    top = A4[1] - 13 * mm
    canvas.drawString(20 * mm, top, left)
    canvas.drawRightString(A4[0] - 20 * mm, top, right)
    canvas.setStrokeColor(RULE)
    canvas.line(20 * mm, top - 2 * mm, A4[0] - 20 * mm, top - 2 * mm)
    canvas.drawString(20 * mm, 11 * mm, "Fictional company. Written for an academic project.")
    canvas.drawRightString(A4[0] - 20 * mm, 11 * mm, f"Page {document.page}")
    canvas.restoreState()


def _doc(out_path, title, subject, cls=SimpleDocTemplate):
    return cls(str(out_path), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=22 * mm,
               bottomMargin=20 * mm, title=title, author=COMPANY, subject=subject)


def render_policy(policy: Policy, out_path: Path) -> int:
    doc = _doc(out_path, policy.title, policy.doc_id)

    def decorate(canvas, document):
        _page_furniture(canvas, document, f"{COMPANY}  |  {policy.title}",
                        f"{policy.doc_id}  |  Version 1.0  |  Classification: Internal")

    doc.build(story_for(policy, doc.width), onFirstPage=decorate, onLaterPages=decorate)
    return doc.page


class ManualDoc(SimpleDocTemplate):
    """Feeds each policy title into the table of contents and records the
    page each policy starts on. The running header is drawn before a page's
    content, so it looks the policy up from the start pages recorded on the
    previous build pass (multiBuild runs until page numbers are stable)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_pages = {}

    def afterFlowable(self, flowable):
        policy = getattr(flowable, "policy", None)
        if policy is not None:
            self.start_pages[policy.doc_id] = (self.page, policy)
            self.notify("TOCEntry", (0, f"{policy.doc_id}   {policy.title}", self.page))

    def policy_on_page(self, page):
        started = [(start, policy) for start, policy in self.start_pages.values() if start <= page]
        return max(started, key=lambda item: item[0])[1] if started else None


def render_manual_pdf(policies, out_path: Path) -> int:
    doc = _doc(out_path, f"{COMPANY} - {MANUAL_TITLE}", "EV-SEC-001 to EV-SEC-009", cls=ManualDoc)
    toc = TableOfContents()
    toc.levelStyles = [STYLES["toc_entry"]]
    story = [
        Spacer(1, 55 * mm),
        Paragraph(COMPANY, STYLES["cover_company"]),
        Paragraph(MANUAL_TITLE, STYLES["cover_title"]),
        Paragraph(f"{policies[0].doc_id} to {policies[-1].doc_id}", STYLES["cover_note"]),
        Paragraph("Version 1.0  |  Effective 1 November 2026  |  Next review 1 November 2027", STYLES["cover_note"]),
        Paragraph("Approved by the Board Risk Committee  |  Classification: Internal", STYLES["cover_note"]),
        Spacer(1, 70 * mm),
        Paragraph(DISCLAIMER, STYLES["cover_note"]),
        PageBreak(),
        Paragraph("Contents", STYLES["toc_heading"]),
        toc,
    ]
    for policy in policies:
        story.append(PageBreak())
        story += story_for(policy, doc.width)

    def decorate(canvas, document):
        if document.page == 1:
            return
        policy = document.policy_on_page(document.page)
        right = f"{policy.doc_id}  |  {policy.title}" if policy else "Contents"
        _page_furniture(canvas, document, f"{COMPANY}  |  Policy Manual", right)

    doc.multiBuild(story, onFirstPage=decorate, onLaterPages=decorate)
    return doc.page


_PAGE_BREAK = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```'


def render_manual_docx(policies, out_path: Path) -> bool:
    """Word copy via pandoc. Returns False if pandoc is not installed."""
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return False
    parts = [
        "---",
        f'title: "{MANUAL_TITLE}"',
        f'subtitle: "{COMPANY}"',
        f'author: "{policies[0].doc_id} to {policies[-1].doc_id}  |  Version 1.0  |  Classification: Internal"',
        'date: "Effective 1 November 2026. Approved by the Board Risk Committee."',
        "toc-title: Contents",
        "---",
        "",
        f"*{DISCLAIMER}*",
    ]
    for policy in policies:
        # A blank line after every line keeps numbered clauses as separate
        # paragraphs; table rows must stay contiguous.
        body, previous_table = [], False
        for line in policy.lines:
            is_table = line.startswith("|")
            if body and not (is_table and previous_table):
                body.append("")
            body.append(line)
            previous_table = is_table
        parts += ["", _PAGE_BREAK, "", *body]
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "manual.md"
        source.write_text("\n".join(parts) + "\n", encoding="utf-8")
        subprocess.run(
            [pandoc, str(source), "-f", "markdown-fancy_lists-startnum", "-o", str(out_path),
             "--toc", "--toc-depth=1"],
            check=True,
        )
    return True


def main():
    OUT_DIR.mkdir(exist_ok=True)
    policies = load_policies()
    if not policies:
        sys.exit(f"No policy files found in {ORG_DIR}")
    for policy in policies:
        out_path = OUT_DIR / (policy.path.stem + ".pdf")
        print(f"{out_path.name}: {render_policy(policy, out_path)} pages")
    manual_pdf = OUT_DIR / f"{MANUAL_NAME}.pdf"
    print(f"{manual_pdf.name}: {render_manual_pdf(policies, manual_pdf)} pages")
    manual_docx = OUT_DIR / f"{MANUAL_NAME}.docx"
    if render_manual_docx(policies, manual_docx):
        print(f"{manual_docx.name}: written")
    else:
        print(f"{manual_docx.name}: skipped (pandoc not found)")


if __name__ == "__main__":
    main()
