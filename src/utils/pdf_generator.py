import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

# Constants
GOLD = colors.HexColor("#D4AF37")

def generate_invoice_pdf(transaction, member, plan):
    """
    Generates a professional A4 Invoice using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- 1. HEADER SECTION ---
    # We use a Table to align Logo (Left) and Invoice Info (Right)
    header_data = [
        [
            Paragraph("<b>IRON<font color='#D4AF37'>LIFTER</font></b><br/><font size=10 color='#777777'>PREMIUM FITNESS CENTER</font>", styles['Normal']),
            Paragraph(f"<b>INVOICE</b><br/><font size=12>#{transaction.invoice_number}</font><br/><font size=10 color='#777777'>{transaction.date.strftime('%d %b, %Y')}</font>", 
                      ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=24, leading=28))
        ]
    ]
    
    header_table = Table(header_data, colWidths=[100*mm, 80*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15*mm))
    
    # --- 2. CLIENT INFO SECTION ---
    client_data = [
        [
            Paragraph(f"<font size=9 color='#999999'>BILLED TO</font><br/><b>{member.name}</b><br/>{member.email}<br/>{member.phone}", styles['Normal']),
            Paragraph(f"<font size=9 color='#999999'>PAYMENT DETAILS</font><br/>{transaction.payment_method}<br/><font color='green'><b>PAID</b></font>", 
                      ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=TA_RIGHT))
        ]
    ]
    
    client_table = Table(client_data, colWidths=[100*mm, 80*mm])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 15*mm))
    
    # --- 3. ITEMS TABLE ---
    data = [['DESCRIPTION', 'VALIDITY', 'AMOUNT']]
    data.append([
        Paragraph(f"<b>{plan.name} Membership</b><br/><font size=9 color='#666666'>Full access to gym facilities</font>", styles['Normal']),
        f"{plan.duration_days} Days",
        f"Rs {transaction.amount}"
    ])
    # Total Row
    data.append(['', 'GRAND TOTAL', f"Rs {transaction.amount}"])
    
    # Define style list separately to avoid SyntaxErrors
    table_style_list = [
        ('BACKGROUND', (0,0), (-1,0), colors.black),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('BOTTOMPADDING', (0,1), (-1,-1), 15),
        ('TOPPADDING', (0,1), (-1,-1), 15),
        ('LINEBELOW', (0,0), (-1,-2), 1, colors.HexColor("#EEEEEE")),
        # Total Row Styles
        ('LINEABOVE', (1,-1), (-1,-1), 1, colors.black),
        ('FONTNAME', (1,-1), (-1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (-1,-1), (-1,-1), GOLD),
        ('FONTSIZE', (1,-1), (-1,-1), 12),
    ]

    t = Table(data, colWidths=[110*mm, 40*mm, 30*mm])
    t.setStyle(TableStyle(table_style_list))
    elements.append(t)
    
    # --- 4. FOOTER ---
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph("Thank you for training with IronLifter.", ParagraphStyle(name='Centered', alignment=TA_CENTER, textColor=colors.grey, fontSize=9)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer