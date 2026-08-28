"""Generate a user-friendly, cleanly formatted PDF report for a ScamShield
analysis result.

Layout is intentionally airy and readable: a colored verdict banner, headed
sections with divider rules, bullet-pointed summary, red-flag cards with a
severity bar + badge, score bars, a bordered box for the analyzed posting and a
plain-language "how to read this" note.
"""

import io
import os
import re
from datetime import datetime, timezone

from fpdf import FPDF

PRIMARY = (79, 70, 229)
SCAM = (220, 38, 38)
CAUTION = (217, 119, 6)
SAFE = (22, 163, 74)
INK = (15, 23, 42)
SLATE = (51, 65, 85)
MUTED = (100, 116, 139)
LINE = (226, 232, 240)
CARD_BG = (248, 250, 252)
NOTE_BG = (241, 245, 249)

PAGE_W = 210.0
MARGIN_X = 14.0
CONTENT_W = PAGE_W - MARGIN_X * 2  # 182
BODY_FONT = 8.6

_STYLE_FILES = [
    ("", ("arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf")),
    ("B", ("arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf")),
    ("I", ("ariali.ttf", "DejaVuSans-Oblique.ttf", "LiberationSans-Italic.ttf")),
]


def _find_font_dir():
    candidates = [
        r"C:\Windows\Fonts",
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/dejavu",
        "/usr/share/fonts/truetype/liberation",
        "/usr/share/fonts/truetype/liberation2",
        "/usr/share/fonts/truetype/noto",
    ]
    for directory in candidates:
        if os.path.isdir(directory):
            return directory
    for root in ("/usr/share/fonts", "/usr/local/share/fonts"):
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if "DejaVuSans.ttf" in filenames:
                return dirpath
            dirnames[:] = [d for d in dirnames if d not in ("opentype", "postscript")]
    try:
        import matplotlib

        bundled = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
        if os.path.isdir(bundled):
            return bundled
    except Exception:
        pass
    return None


_FONT_DIR_CACHE = None


def _font_dir():
    global _FONT_DIR_CACHE
    if _FONT_DIR_CACHE is None:
        _FONT_DIR_CACHE = os.environ.get("SCAMSHIELD_FONT_DIR") or _find_font_dir()
    return _FONT_DIR_CACHE


def _font_files():
    directory = _font_dir()
    if not directory:
        raise RuntimeError(
            "No TrueType font found for PDF report generation. Set SCAMSHIELD_FONT_DIR "
            "or install fonts-dejavu-core / Liberation fonts."
        )
    files = {}
    for style, names in _STYLE_FILES:
        for name in names:
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                files[style] = path
                break
        else:
            raise FileNotFoundError(f"No font variant for style '{style}' in {directory}")
    return files


def _register_fonts(pdf):
    """Add TTF fonts to the PDF. Falls back to built-in core fonts if no
    .ttf file is available on the host (guarantees the PDF always builds)."""
    try:
        for style, path in _font_files().items():
            pdf.add_font("Arial", style, path)
        return "Arial"
    except Exception:
        return "Helvetica"


def score_meta(score):
    if score >= 0.7:
        return SCAM, "HIGH RISK", "this posting matches many known fraud patterns and is likely a scam"
    if score >= 0.4:
        return CAUTION, "MEDIUM RISK", "this posting shows some suspicious patterns and may be a scam"
    return SAFE, "LOW RISK", "this posting shows few known fraud patterns and is likely legitimate"


def _bar_color(value):
    if value >= 0.7:
        return SCAM
    if value >= 0.4:
        return CAUTION
    return SAFE


def _sanitize(text, max_len=1800, enc=None):
    text = re.sub(r"<[^>]+>", "", text or "")
    for entity, char in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')):
        text = text.replace(entity, char)
    text = re.sub(r"\s+", " ", text).strip()
    if enc:
        text = text.encode(enc, "replace").decode(enc)
    if len(text) > max_len:
        text = text[:max_len].rstrip() + "..."
    return text


def _severity_meta(severity):
    if severity >= 0.9:
        return SCAM, "CRITICAL"
    if severity >= 0.7:
        return CAUTION, "HIGH"
    return MUTED, "MEDIUM"


class _Report(FPDF):
    def __init__(self, format="A4"):
        super().__init__(format=format)
        self.font_family = "Arial"
        self.set_left_margin(MARGIN_X)
        self.set_right_margin(10)
        self.set_margins(MARGIN_X, 26, 10)

    def header(self):
        self.set_fill_color(*PRIMARY)
        self.rect(0, 0, self.w, 22, "F")
        self.set_font(self.font_family, "B", 15)
        self.set_text_color(255, 255, 255)
        self.set_xy(MARGIN_X, 5)
        self.cell(0, 10, "ScamShield", new_x="LMARGIN", new_y="NEXT")
        self.set_font(self.font_family, "", 9)
        self.set_text_color(224, 231, 255)
        self.cell(0, 5, "Job Posting Fraud Risk Report", new_x="LMARGIN", new_y="NEXT")
        # brand mark on the right
        self.set_font(self.font_family, "B", 13)
        self.set_xy(self.w - 46, 6)
        self.cell(34, 10, "SS", align="R")

    def footer(self):
        self.set_y(-14)
        self.set_font(self.font_family, "I", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="C")


def _text_height(pdf, w, h, text):
    """Measure rendered height of `text` wrapped within `w` at `h`/line.

    fpdf2 gotcha: `multi_cell(dry_run=True)` with no output returns False;
    must request `output="LINES"` to get the wrap result.
    """
    lines = pdf.multi_cell(w, h, text, dry_run=True, output="LINES")
    return len(lines) * h


def _fit_text(pdf, family, text, max_width):
    """Truncate `text` with an ellipsis so it fits `max_width` at the current font."""
    if pdf.get_string_width(text) <= max_width:
        return text
    while text and pdf.get_string_width(text + "...") > max_width:
        text = text[:-1]
    return text + "..."


def _section_heading(pdf, family, text, color):
    pdf.ln(3)
    y = pdf.get_y()
    pdf.set_fill_color(*color)
    pdf.rect(MARGIN_X, y + 1.5, 3, 6.5, "F")
    pdf.set_font(family, "B", 11.5)
    pdf.set_text_color(*INK)
    pdf.set_x(MARGIN_X + 7)
    pdf.cell(0, 8.5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*LINE)
    pdf.set_line_width(0.4)
    pdf.line(MARGIN_X, pdf.get_y() + 0.8, PAGE_W - 10, pdf.get_y() + 0.8)
    pdf.ln(3)
    pdf.set_line_width(0.2)


def _verdict_banner(pdf, family, score, color, verdict, verdict_note, label, sanitize):
    total_h = 36
    if pdf.get_y() + total_h + 8 > pdf.h - pdf.b_margin:
        pdf.add_page()
    y0 = pdf.get_y()

    pdf.set_fill_color(*color)
    pdf.rect(MARGIN_X, y0, CONTENT_W, total_h, "F")

    pdf.set_xy(MARGIN_X + 8, y0 + 3)
    pdf.set_font(family, "B", 21)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(56, 14, f"{score * 100:.0f}%")
    pdf.set_xy(MARGIN_X + 8, y0 + 17)
    pdf.set_font(family, "B", 7.5)
    pdf.cell(56, 5, "SCAM LIKELIHOOD")

    pdf.set_xy(MARGIN_X + 74, y0 + 4)
    pdf.set_font(family, "B", 13)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, verdict)
    pdf.set_xy(MARGIN_X + 74, y0 + 13)
    pdf.set_font(family, "", 8.5)
    pdf.set_text_color(*NOTE_BG)
    note = sanitize(f"{verdict_note.capitalize()}" + (f"  \u2022  {label}" if label else ""), 220)
    pdf.multi_cell(CONTENT_W - 74 - 8, 5, note, new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(y0 + total_h + 2)


def _meta_line(pdf, family, result, now):
    pdf.set_font(family, "", 8.5)
    pdf.set_text_color(*MUTED)
    parts = [f"Generated: {now}"]
    if result.get("type"):
        parts.append(f"Source: {result.get('type')}")
    if result.get("hash"):
        parts.append(f"Report ID: {result.get('hash')}")
    pdf.set_x(MARGIN_X)
    pdf.cell(0, 5, "   |   ".join(parts), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _summary_bullets(pdf, family, bullets, sanitize):
    for bullet in bullets:
        safe = sanitize(str(bullet))
        if pdf.get_y() + 8 > pdf.h - pdf.b_margin:
            pdf.add_page()
        pdf.set_font(family, "B", 9)
        pdf.set_text_color(*PRIMARY)
        pdf.set_x(MARGIN_X + 3)
        pdf.cell(6, 5.2, "-")
        pdf.set_font(family, "", BODY_FONT)
        pdf.set_text_color(*SLATE)
        pdf.set_x(MARGIN_X + 11)
        pdf.multi_cell(CONTENT_W - 11, 5.2, safe, new_x="LMARGIN", new_y="NEXT")


def _flag_card(pdf, family, flag, sanitize):
    name = sanitize(str(flag.get("name", "Red flag")))
    explanation = sanitize(str(flag.get("explanation", "")))
    evidence = [sanitize(str(e), 140) for e in (flag.get("evidence") or [])][:6]
    sev_color, sev_label = _severity_meta(float(flag.get("severity", 0.5)))

    pad_top = 6.5
    content_x = MARGIN_X + 11
    content_w = CONTENT_W - 11
    badge_w = 24
    max_name_w = CONTENT_W - 11 - badge_w - 6

    pdf.set_font(family, "B", 9.5)
    name = _fit_text(pdf, family, name, max_name_w)

    pdf.set_font(family, "", BODY_FONT)
    expl_h = _text_height(pdf, content_w, 4.8, explanation)
    ev_h = 0.0
    if evidence:
        pdf.set_font(family, "I", 8.2)
        ev_text = "Evidence: " + " | ".join(evidence)
        ev_h = _text_height(pdf, content_w, 4.2, ev_text)
    pad_btm = 6.5
    total_h = pad_top + 7 + expl_h + ev_h + pad_btm

    if pdf.get_y() + total_h + 2 > pdf.h - pdf.b_margin:
        pdf.add_page()
    y0 = pdf.get_y()

    # card background + left severity bar
    pdf.set_fill_color(*CARD_BG)
    pdf.rect(MARGIN_X, y0, CONTENT_W, total_h, "F")
    pdf.set_fill_color(*sev_color)
    pdf.rect(MARGIN_X, y0, 4, total_h, "F")

    # severity badge (top-right)
    pdf.set_fill_color(*sev_color)
    pdf.set_font(family, "B", 7.5)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(PAGE_W - 10 - badge_w, y0 + pad_top - 1)
    pdf.cell(badge_w, 6.5, sev_label, align="C", fill=True)

    # flag name
    pdf.set_xy(content_x, y0 + pad_top - 1)
    pdf.set_font(family, "B", 9.5)
    pdf.set_text_color(*sev_color)
    pdf.cell(0, 7, name, new_x="LMARGIN", new_y="NEXT")

    # explanation
    pdf.set_x(content_x)
    pdf.set_font(family, "", BODY_FONT)
    pdf.set_text_color(*SLATE)
    pdf.multi_cell(content_w, 4.8, explanation, new_x="LMARGIN", new_y="NEXT")

    # evidence strip
    if evidence:
        pdf.set_x(content_x)
        pdf.set_font(family, "I", 8.2)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(content_w, 4.2, "Evidence: " + " | ".join(evidence), new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(y0 + total_h + 3)


def _score_bar(pdf, family, label, value, color):
    pdf.set_font(family, "", 8.5)
    pdf.set_text_color(*MUTED)
    pdf.set_x(MARGIN_X)
    pdf.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
    pct = max(0.0, min(1.0, value or 0.0))
    y = pdf.get_y() + 1
    bar_w = 152
    pdf.set_fill_color(*LINE)
    pdf.rect(MARGIN_X, y, bar_w, 4.5, "F")
    pdf.set_fill_color(*color)
    if pct > 0.01:
        pdf.rect(MARGIN_X, y, bar_w * pct, 4.5, "F")
    pdf.set_font(family, "B", 9)
    pdf.set_text_color(*INK)
    pdf.set_xy(MARGIN_X + bar_w + 6, y - 0.5)
    pdf.cell(0, 6, f"{pct * 100:.0f}%")
    pdf.set_xy(MARGIN_X, y + 7.5)


def _boxed_text(pdf, family, title, text, color, sanitize):
    """A titled, bordered, softly-filled box used for the posting + disclaimer."""
    pdf.set_font(family, "", BODY_FONT)
    inner_w = CONTENT_W - 8
    text_h = _text_height(pdf, inner_w, 4.8, text)
    h = text_h + 12
    if pdf.get_y() + h > pdf.h - pdf.b_margin:
        pdf.add_page()
    y0 = pdf.get_y()

    pdf.set_fill_color(*CARD_BG)
    pdf.set_draw_color(*LINE)
    pdf.rect(MARGIN_X, y0, CONTENT_W, h, "DF")

    pdf.set_xy(MARGIN_X + 6, y0 + 3)
    pdf.set_font(family, "B", 9)
    pdf.set_text_color(*INK)
    pdf.cell(0, 5.5, title, new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(MARGIN_X + 6)
    pdf.set_font(family, "", BODY_FONT)
    pdf.set_text_color(*SLATE)
    pdf.multi_cell(inner_w, 4.8, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(y0 + h + 3)


def build_pdf_report(result, source_text="", title="ScamShield Analysis Report"):
    score = float(result.get("score", 0))
    color, verdict, verdict_note = score_meta(score)
    label = result.get("label", "")
    now = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    pdf = _Report(format="A4")
    family = _register_fonts(pdf)
    pdf.font_family = family
    sanitize = (lambda t, m=1800: _sanitize(t, m, enc="latin-1")) if family == "Helvetica" else _sanitize
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title + generation time
    pdf.set_font(family, "B", 15)
    pdf.set_text_color(*INK)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    _meta_line(pdf, family, result, now)

    _verdict_banner(pdf, family, score, color, verdict, verdict_note, label, sanitize)

    summary = result.get("explanation", {}).get("bullet_points", [])
    if summary:
        _section_heading(pdf, family, "Summary", PRIMARY)
        _summary_bullets(pdf, family, summary, sanitize)

    red_flags = result.get("red_flags") or []
    if red_flags:
        _section_heading(pdf, family, f"Detected red flags ({len(red_flags)})", color)
        for flag in red_flags:
            _flag_card(pdf, family, flag, sanitize)

    scores = [
        ("Rule engine score", result.get("rule_score")),
        ("AI model confidence", result.get("model_confidence")),
        ("Known-template match", result.get("duplicate_template_score")),
    ]
    present = [(name, value) for name, value in scores if value is not None]
    if present:
        _section_heading(pdf, family, "Score breakdown", PRIMARY)
        for name, value in present:
            _score_bar(pdf, family, name, float(value), _bar_color(float(value)))

    source = sanitize(source_text or result.get("ocr_text") or "")
    if source:
        _boxed_text(pdf, family, "Analyzed posting", source, color, sanitize)

    _boxed_text(
        pdf,
        family,
        "How to read this report",
        (
            "The scam-likelihood score estimates how closely the posting matches known fraud "
            "patterns (fee or security-deposit requests, too-good salaries, generic "
            "email/WhatsApp contacts, urgency pressure). A high score does not prove fraud - "
            "always verify the employer directly through its official website before paying "
            "anything or sharing personal details. This report is generated by ScamShield, an "
            "AI-assisted detection tool, and is not legal advice."
        ),
        color,
        sanitize,
    )

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()