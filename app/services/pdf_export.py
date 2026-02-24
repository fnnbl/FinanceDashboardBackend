import io
from decimal import Decimal
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models.budget_item import BudgetItem, BudgetItemType, PaymentRhythm


RHYTHM_LABELS = {
    PaymentRhythm.MONTHLY: "Monatlich",
    PaymentRhythm.QUARTERLY: "Vierteljaehrlich",
    PaymentRhythm.SEMI_ANNUALLY: "Halbjaehrlich",
    PaymentRhythm.ANNUALLY: "Jaehrlich",
}


def _fmt(value: float) -> str:
    return f"{value:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")


def generate_plan_pdf(plan_name: str, plan_description: str | None, items: list[dict]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("PlanTitle", parent=styles["Title"], fontSize=18, spaceAfter=6)
    heading_style = ParagraphStyle("SectionHead", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=6)
    normal_style = styles["Normal"]

    elements = []

    # Title
    elements.append(Paragraph(plan_name, title_style))
    if plan_description:
        elements.append(Paragraph(plan_description, normal_style))
    elements.append(Spacer(1, 8 * mm))

    income_items = [i for i in items if i["type"] == BudgetItemType.INCOME or i["type"] == "income"]
    expense_items = [i for i in items if i["type"] == BudgetItemType.EXPENSE or i["type"] == "expense"]

    total_income = sum(i["monthly_amount"] for i in income_items)
    total_expenses = sum(i["monthly_amount"] for i in expense_items)
    balance = total_income - total_expenses

    # Summary
    elements.append(Paragraph("Monatliche Uebersicht", heading_style))
    summary_data = [
        ["Monatliche Einnahmen", _fmt(total_income)],
        ["Monatliche Ausgaben", _fmt(total_expenses)],
        ["Bilanz", _fmt(balance)],
    ]
    summary_table = Table(summary_data, colWidths=[120 * mm, 50 * mm])
    balance_color = colors.HexColor("#2e7d32") if balance >= 0 else colors.HexColor("#c62828")
    summary_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor("#2e7d32")),
        ("TEXTCOLOR", (1, 1), (1, 1), colors.HexColor("#c62828")),
        ("TEXTCOLOR", (1, 2), (1, 2), balance_color),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6 * mm))

    # Items table helper
    def _build_items_table(title, item_list, header_color):
        elements.append(Paragraph(title, heading_style))
        if not item_list:
            elements.append(Paragraph("Keine Posten vorhanden.", normal_style))
            return

        header = ["Beschreibung", "Kategorie", "Betrag", "Rhythmus", "Monatlich"]
        rows = [header]
        for i in item_list:
            rhythm = i["payment_rhythm"]
            if isinstance(rhythm, PaymentRhythm):
                rhythm_label = RHYTHM_LABELS.get(rhythm, str(rhythm))
            else:
                rhythm_label = RHYTHM_LABELS.get(PaymentRhythm(rhythm), rhythm)
            rows.append([
                i["description"],
                i.get("category_name", str(i.get("category_id", ""))),
                _fmt(i["amount"]),
                rhythm_label,
                _fmt(i["monthly_amount"]),
            ])

        section_total = sum(i["monthly_amount"] for i in item_list)
        rows.append(["", "", "", "Summe:", _fmt(section_total)])

        col_widths = [55 * mm, 35 * mm, 30 * mm, 30 * mm, 30 * mm]
        table = Table(rows, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -2), 0.5, colors.lightgrey),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 4 * mm))

    _build_items_table("Einnahmen", income_items, colors.HexColor("#2e7d32"))
    _build_items_table("Ausgaben", expense_items, colors.HexColor("#c62828"))

    # Category breakdown
    elements.append(Paragraph("Kategorieauswertung - Ausgaben", heading_style))
    if expense_items:
        cat_sums = defaultdict(float)
        for i in expense_items:
            cat_name = i.get("category_name", str(i.get("category_id", "")))
            cat_sums[cat_name] += i["monthly_amount"]

        sorted_cats = sorted(cat_sums.items(), key=lambda x: x[1], reverse=True)
        cat_rows = [["Kategorie", "Monatlich", "Anteil"]]
        for cat_name, cat_sum in sorted_cats:
            pct = (cat_sum / total_expenses * 100) if total_expenses > 0 else 0
            cat_rows.append([cat_name, _fmt(cat_sum), f"{pct:.1f}%"])

        cat_table = Table(cat_rows, colWidths=[80 * mm, 50 * mm, 30 * mm])
        cat_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#455a64")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(cat_table)
    else:
        elements.append(Paragraph("Keine Ausgaben vorhanden.", normal_style))

    doc.build(elements)
    return buffer.getvalue()
