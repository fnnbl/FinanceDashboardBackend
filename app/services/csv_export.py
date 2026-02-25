import csv
import io

from app.models.budget_item import PaymentRhythm


RHYTHM_LABELS = {
    PaymentRhythm.MONTHLY: "Monatlich",
    PaymentRhythm.QUARTERLY: "Vierteljaehrlich",
    PaymentRhythm.SEMI_ANNUALLY: "Halbjaehrlich",
    PaymentRhythm.ANNUALLY: "Jaehrlich",
}

TYPE_LABELS = {
    "income": "Einnahme",
    "expense": "Ausgabe",
}


def generate_plan_csv(items: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        "Beschreibung",
        "Typ",
        "Kategorie",
        "Betrag",
        "Zahlungsrhythmus",
        "Monatlicher Betrag",
        "Bemerkung",
    ])

    for item in items:
        rhythm = item["payment_rhythm"]
        if isinstance(rhythm, PaymentRhythm):
            rhythm_label = RHYTHM_LABELS.get(rhythm, str(rhythm))
        else:
            rhythm_label = RHYTHM_LABELS.get(PaymentRhythm(rhythm), str(rhythm))

        item_type = str(item["type"].value if hasattr(item["type"], "value") else item["type"])
        type_label = TYPE_LABELS.get(item_type, item_type)

        writer.writerow([
            item["description"],
            type_label,
            item.get("category_name", str(item.get("category_id", ""))),
            str(item["amount"]).replace(".", ","),
            rhythm_label,
            str(item["monthly_amount"]).replace(".", ","),
            item.get("note") or "",
        ])

    return buffer.getvalue().encode("utf-8-sig")
