from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import os


INVOICE_FOLDER = "static/invoices"
os.makedirs(INVOICE_FOLDER, exist_ok=True)


def generate_invoice(order_id, customer_name, items, total):
    file_path = os.path.join(INVOICE_FOLDER, f"invoice_{order_id}.pdf")

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Kuckoo Boo & mama!", styles["Title"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Invoice - Order #{order_id}", styles["Heading2"]))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"Customer: {customer_name}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Table Data
    data = [["Product", "Qty", "Price"]]

    for item in items:
        data.append([
            item["product_name"],
            str(item["quantity"]),
            f"₹{item['price']}"
        ])

    data.append(["", "", ""])
    data.append(["Total", "", f"₹{total}"])

    table = Table(data, colWidths=[250, 80, 100])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER')
    ]))

    elements.append(table)

    doc.build(elements)

    return file_path
