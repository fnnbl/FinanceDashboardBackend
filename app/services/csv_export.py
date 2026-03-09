import csv
import io

from app.models.budget_item import PaymentRhythm


RHYTHM_LABELS = {
    PaymentRhythm.MONTHLY:       "Monatlich",
    PaymentRhythm.QUARTERLY:     "Vierteljährlich",
    PaymentRhythm.SEMI_ANNUALLY: "Halbjährlich",
    PaymentRhythm.ANNUALLY:      "Jährlich",
}

TYPE_LABELS = {
    "income":  "Einnahme",
    "expense": "Ausgabe",
}


def _rhythm_label(rhythm) -> str:
    if isinstance(rhythm, PaymentRhythm):
        return RHYTHM_LABELS.get(rhythm, str(rhythm))
    return RHYTHM_LABELS.get(PaymentRhythm(rhythm), str(rhythm))


def _de_num(value: float) -> str:
    """Format number with German decimal comma for Excel DE compatibility."""
    return f"{value:.2f}".replace(".", ",")


def generate_plan_csv(items: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        "Typ",
        "Beschreibung",
        "Kategorie",
        "Betrag",
        "Zahlungsrhythmus",
        "Monatlicher Betrag",
        "Bemerkung",
    ])

    income_items  = [i for i in items if str(getattr(i.get("type"), "value", i.get("type"))) == "income"]
    expense_items = [i for i in items if str(getattr(i.get("type"), "value", i.get("type"))) == "expense"]

    def _write_items(item_list):
        for item in item_list:
            item_type = str(getattr(item.get("type"), "value", item.get("type")))
            writer.writerow([
                TYPE_LABELS.get(item_type, item_type),
                item["description"],
                item.get("category_name", str(item.get("category_id", ""))),
                _de_num(item["amount"]),
                _rhythm_label(item["payment_rhythm"]),
                _de_num(item["monthly_amount"]),
                item.get("note") or "",
            ])

    _write_items(income_items)
    _write_items(expense_items)

    # Summary rows
    total_income   = sum(i["monthly_amount"] for i in income_items)
    total_expenses = sum(i["monthly_amount"] for i in expense_items)
    balance        = total_income - total_expenses

    writer.writerow([])
    writer.writerow(["", "", "", "", "Summe Einnahmen:",  _de_num(total_income),   ""])
    writer.writerow(["", "", "", "", "Summe Ausgaben:",   _de_num(total_expenses), ""])
    writer.writerow(["", "", "", "", "Monatl. Bilanz:",   _de_num(balance),        ""])

    return buffer.getvalue().encode("utf-8-sig")
