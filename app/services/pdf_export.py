import io
from collections import defaultdict
from datetime import date
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus.flowables import Flowable

from app.models.budget_item import BudgetItemType, PaymentRhythm


# Web design colors (light mode)
C_INCOME     = colors.HexColor("#166534")
C_INCOME_BG  = colors.HexColor("#f0fdf4")
C_EXPENSE    = colors.HexColor("#b91c1c")
C_EXPENSE_BG = colors.HexColor("#fef2f2")
C_ACCENT     = colors.HexColor("#1a1a1a")
C_BG         = colors.HexColor("#eceae4")
C_SECTION_BG = colors.HexColor("#faf9f7")
C_BORDER     = colors.HexColor("#b8b4ac")
C_TEXT       = colors.HexColor("#111827")
C_MUTED      = colors.HexColor("#6b7280")
C_ROW_ALT    = colors.HexColor("#f3f2ef")
C_WHITE      = colors.white


# Chart colors matching CATEGORY_COLORS in PlanDetailPage.jsx
CHART_COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#4dc9f6", "#f67019", "#537bc4", "#acc236", "#166a8f",
]


class DonutChart(Flowable):
    """Inline donut chart + legend rendered via canvas methods."""

    def __init__(self, slices: list[dict], width: float = 170 * mm, height: float = 60 * mm):
        super().__init__()
        self.slices = slices   # [{"name": str, "amount": float, "color": str}]
        self.width  = width
        self.height = height

    def draw(self):
        if not self.slices:
            return

        total  = sum(s["amount"] for s in self.slices)
        r      = self.height * 0.44
        cx     = r + 4 * mm
        cy     = self.height / 2
        inner  = r * 0.52
        angle  = 90.0

        # Draw wedges clockwise from top
        for s in self.slices:
            extent = -(s["amount"] / total) * 360
            col    = colors.HexColor(s["color"])
            self.canv.setFillColor(col)
            self.canv.setStrokeColor(colors.white)
            self.canv.setLineWidth(1.2)
            self.canv.wedge(cx - r, cy - r, cx + r, cy + r,
                            angle, extent, stroke=1, fill=1)
            angle += extent

        # Donut hole
        self.canv.setFillColor(colors.HexColor("#faf9f7"))
        self.canv.setStrokeColor(colors.HexColor("#faf9f7"))
        self.canv.circle(cx, cy, inner, stroke=0, fill=1)

        # Legend
        legend_x = cx + r + 8 * mm
        item_h   = min(13, (self.height - 4 * mm) / max(len(self.slices), 1))
        start_y  = cy + (len(self.slices) - 1) * item_h / 2

        for s in self.slices:
            pct = s["amount"] / total * 100
            col = colors.HexColor(s["color"])

            # Swatch
            self.canv.setFillColor(col)
            self.canv.setStrokeColor(col)
            self.canv.rect(legend_x, start_y - 2.5, 8, 8, stroke=0, fill=1)

            # Label
            self.canv.setFont("Helvetica", 8)
            self.canv.setFillColor(colors.HexColor("#111827"))
            self.canv.drawString(legend_x + 11, start_y - 1,
                                 f"{s['name']}  {pct:.1f} %")
            start_y -= item_h


RHYTHM_LABELS = {
    PaymentRhythm.MONTHLY:       "Monatlich",
    PaymentRhythm.QUARTERLY:     "Vierteljährlich",
    PaymentRhythm.SEMI_ANNUALLY: "Halbjährlich",
    PaymentRhythm.ANNUALLY:      "Jährlich",
}


def _fmt(value: float) -> str:
    return f"{value:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_num(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _rhythm_label(rhythm) -> str:
    if isinstance(rhythm, PaymentRhythm):
        return RHYTHM_LABELS.get(rhythm, str(rhythm))
    return RHYTHM_LABELS.get(PaymentRhythm(rhythm), str(rhythm))


def generate_plan_pdf(plan_name: str, plan_description: str | None, items: list[dict]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    page_width = A4[0] - 36 * mm  # usable width

    title_style = ParagraphStyle(
        "PlanTitle",
        parent=styles["Normal"],
        fontSize=22,
        fontName="Helvetica-Bold",
        textColor=C_TEXT,
        spaceAfter=3,
        leading=26,
    )
    desc_style = ParagraphStyle(
        "PlanDesc",
        parent=styles["Normal"],
        fontSize=10,
        textColor=C_MUTED,
        spaceAfter=0,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=C_MUTED,
        alignment=TA_RIGHT,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=12,
        fontName="Helvetica-Bold",
        textColor=C_TEXT,
        spaceBefore=10,
        spaceAfter=4,
    )
    note_style = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontSize=9,
        textColor=C_MUTED,
        spaceAfter=0,
    )

    income_items  = [i for i in items if str(getattr(i.get("type"), "value", i.get("type"))) == "income"]
    expense_items = [i for i in items if str(getattr(i.get("type"), "value", i.get("type"))) == "expense"]

    total_income   = sum(i["monthly_amount"] for i in income_items)
    total_expenses = sum(i["monthly_amount"] for i in expense_items)
    balance        = total_income - total_expenses
    balance_color  = C_INCOME if balance >= 0 else C_EXPENSE

    elements = []

    # ── Header ───────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph(plan_name, title_style),
        Paragraph(date.today().strftime("Exportiert am %d.%m.%Y"), meta_style),
    ]]
    header_table = Table(header_data, colWidths=[page_width * 0.65, page_width * 0.35])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)

    if plan_description:
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(plan_description, desc_style))

    elements.append(Spacer(1, 3 * mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=5 * mm))

    # ── Stats bar (like web) ──────────────────────────────────────────────────
    col_w = page_width / 4
    stats_label_style = ParagraphStyle("SL", parent=styles["Normal"], fontSize=8,
                                       textColor=C_MUTED, fontName="Helvetica", spaceAfter=1)
    stats_value_style_income  = ParagraphStyle("SVI", parent=styles["Normal"], fontSize=14,
                                               fontName="Helvetica-Bold", textColor=C_INCOME)
    stats_value_style_expense = ParagraphStyle("SVE", parent=styles["Normal"], fontSize=14,
                                               fontName="Helvetica-Bold", textColor=C_EXPENSE)
    stats_value_style_balance = ParagraphStyle("SVB", parent=styles["Normal"], fontSize=14,
                                               fontName="Helvetica-Bold", textColor=balance_color)
    stats_value_style_neutral = ParagraphStyle("SVN", parent=styles["Normal"], fontSize=14,
                                               fontName="Helvetica-Bold", textColor=C_TEXT)

    stats_data = [[
        [Paragraph("Einnahmen", stats_label_style), Paragraph(_fmt(total_income), stats_value_style_income)],
        [Paragraph("Ausgaben", stats_label_style),  Paragraph(_fmt(total_expenses), stats_value_style_expense)],
        [Paragraph("Monatl. Bilanz", stats_label_style), Paragraph(_fmt(balance), stats_value_style_balance)],
        [Paragraph("Posten gesamt", stats_label_style), Paragraph(str(len(items)), stats_value_style_neutral)],
    ]]
    stats_table = Table(stats_data, colWidths=[col_w] * 4)
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_SECTION_BG),
        ("BOX",        (0, 0), (-1, -1), 0.5, C_BORDER),
        ("LINEAFTER",  (0, 0), (2, 0), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Items table helper ────────────────────────────────────────────────────
    def _build_items_table(title, item_list, header_bg, header_text_color, value_color):
        elements.append(Paragraph(title, section_style))
        if not item_list:
            elements.append(Paragraph("Keine Posten vorhanden.", note_style))
            elements.append(Spacer(1, 3 * mm))
            return

        col_widths = [page_width * 0.30, page_width * 0.20, page_width * 0.16, page_width * 0.18, page_width * 0.16]
        header = ["Beschreibung", "Kategorie", "Betrag", "Rhythmus", "Monatlich"]
        rows = [header]

        for idx, i in enumerate(item_list):
            note = i.get("note") or ""
            desc = i["description"] + (f"\n{note}" if note else "")
            rows.append([
                desc,
                i.get("category_name", str(i.get("category_id", ""))),
                _fmt(i["amount"]),
                _rhythm_label(i["payment_rhythm"]),
                _fmt(i["monthly_amount"]),
            ])

        section_total = sum(i["monthly_amount"] for i in item_list)
        rows.append(["", "", "", "Summe:", _fmt(section_total)])

        table = Table(rows, colWidths=col_widths)
        num_rows = len(rows)

        style_cmds = [
            # Header row
            ("FONTNAME",        (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",        (0, 0), (-1, 0), 9),
            ("BACKGROUND",      (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR",       (0, 0), (-1, 0), C_WHITE),
            ("TOPPADDING",      (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING",   (0, 0), (-1, 0), 5),
            # Data rows
            ("FONTNAME",        (0, 1), (-1, -2), "Helvetica"),
            ("FONTSIZE",        (0, 1), (-1, -1), 9),
            ("TOPPADDING",      (0, 1), (-1, -2), 4),
            ("BOTTOMPADDING",   (0, 1), (-1, -2), 4),
            ("TEXTCOLOR",       (0, 1), (-1, -2), C_TEXT),
            # Alternating rows
            *[("BACKGROUND", (0, r), (-1, r), C_ROW_ALT) for r in range(2, num_rows - 1, 2)],
            # Amount columns right-aligned
            ("ALIGN",           (2, 0), (-1, -1), "RIGHT"),
            ("FONTNAME",        (4, 1), (4, -2), "Helvetica-Bold"),
            ("TEXTCOLOR",       (4, 1), (4, -2), value_color),
            # Sum row
            ("FONTNAME",        (0, -1), (-1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR",       (0, -1), (-1, -1), value_color),
            ("LINEABOVE",       (0, -1), (-1, -1), 1, header_bg),
            ("TOPPADDING",      (0, -1), (-1, -1), 5),
            ("BOTTOMPADDING",   (0, -1), (-1, -1), 5),
            ("BACKGROUND",      (0, -1), (-1, -1), C_SECTION_BG),
            # Grid
            ("GRID",            (0, 0), (-1, -2), 0.3, C_BORDER),
            ("BOX",             (0, 0), (-1, -1), 0.5, C_BORDER),
        ]
        table.setStyle(TableStyle(style_cmds))
        elements.append(table)
        elements.append(Spacer(1, 5 * mm))

    _build_items_table("Einnahmen", income_items, C_INCOME, C_WHITE, C_INCOME)
    _build_items_table("Ausgaben", expense_items, C_EXPENSE, C_WHITE, C_EXPENSE)

    # ── Category breakdown ────────────────────────────────────────────────────
    def _build_category_table(title, type_items, total, header_bg, value_color, color_offset=0):
        elements.append(Paragraph(title, section_style))
        if not type_items:
            elements.append(Paragraph("Keine Posten vorhanden.", note_style))
            elements.append(Spacer(1, 3 * mm))
            return

        cat_sums = defaultdict(float)
        for i in type_items:
            cat_name = i.get("category_name", str(i.get("category_id", "")))
            cat_sums[cat_name] += i["monthly_amount"]

        sorted_cats = sorted(cat_sums.items(), key=lambda x: x[1], reverse=True)

        # Build slices for donut chart (same color order as web app)
        slices = [
            {
                "name":   cat_name,
                "amount": cat_sum,
                "color":  CHART_COLORS[(color_offset + idx) % len(CHART_COLORS)],
            }
            for idx, (cat_name, cat_sum) in enumerate(sorted_cats)
        ]
        elements.append(DonutChart(slices, width=page_width, height=58 * mm))
        elements.append(Spacer(1, 3 * mm))

        # Table below chart
        col_widths = [page_width * 0.50, page_width * 0.25, page_width * 0.25]
        rows = [["Kategorie", "Monatlich", "Anteil"]]
        for idx, (cat_name, cat_sum) in enumerate(sorted_cats):
            pct = (cat_sum / total * 100) if total > 0 else 0
            rows.append([cat_name, _fmt(cat_sum), f"{pct:.1f} %"])

        table = Table(rows, colWidths=col_widths)
        num_rows = len(rows)
        table.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("BACKGROUND",    (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("TEXTCOLOR",     (0, 1), (-1, -1), C_TEXT),
            ("TEXTCOLOR",     (1, 1), (2, -1), value_color),
            ("FONTNAME",      (1, 1), (2, -1), "Helvetica-Bold"),
            ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
            ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
            *[("BACKGROUND",  (0, r), (-1, r), C_ROW_ALT) for r in range(2, num_rows, 2)],
        ]))
        elements.append(table)
        elements.append(Spacer(1, 5 * mm))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=2 * mm, spaceAfter=4 * mm))
    _build_category_table("Kategorieauswertung - Einnahmen", income_items, total_income, C_INCOME, C_INCOME)
    _build_category_table("Kategorieauswertung - Ausgaben",  expense_items, total_expenses, C_EXPENSE, C_EXPENSE)

    doc.build(elements)
    return buffer.getvalue()
