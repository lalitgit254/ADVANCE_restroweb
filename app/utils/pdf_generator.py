import io
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def generate_invoice_pdf(order, payment, restaurant):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18,
                                  textColor=colors.HexColor('#1a1a2e'))
    elements = []

    elements.append(Paragraph(restaurant.name if restaurant else 'RestaurantPro', title_style))
    elements.append(Paragraph(f'Invoice: {payment.invoice_number or "N/A"}', styles['Normal']))
    elements.append(Paragraph(f'Date: {datetime.now(timezone.utc).strftime("%d %b %Y")}', styles['Normal']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f'Order #: {order.order_number}', styles['Heading3']))
    elements.append(Spacer(1, 10))

    table_data = [['Item', 'Qty', 'Price', 'Total']]
    for item in order.items:
        table_data.append([
            item.food_name,
            str(item.quantity),
            f'₹{float(item.unit_price):.2f}',
            f'₹{float(item.total_price):.2f}',
        ])

    table_data.append(['', '', 'Subtotal', f'₹{float(order.subtotal):.2f}'])
    table_data.append(['', '', 'GST', f'₹{float(order.tax_amount):.2f}'])
    if float(order.discount_amount) > 0:
        table_data.append(['', '', 'Discount', f'-₹{float(order.discount_amount):.2f}'])
    table_data.append(['', '', 'Total', f'₹{float(order.total_amount):.2f}'])

    table = Table(table_data, colWidths=[3 * inch, 0.8 * inch, 1.2 * inch, 1.2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, -4), (-1, -1), 'RIGHT'),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
