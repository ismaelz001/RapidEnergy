
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_pro_invoice():
    doc = SimpleDocTemplate("factura_test_30TD_comercial.pdf", pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Encabezado
    elements.append(Paragraph("<b>FACTURA DE ENERGÍA ELÉCTRICA (TEST 3.0TD)</b>", styles['Title']))
    elements.append(Spacer(1, 20))
    
    # Datos Cliente
    elements.append(Paragraph("<b>Datos del punto de suministro:</b>", styles['Heading3']))
    data_cliente = [
        ["Titular:", "MecaEnergy Business S.L."],
        ["CUPS:", "ES0031000012345678MT"],
        ["Tarifa / ATR:", "3.0TD"],
        ["Periodo:", "01/12/2025 - 31/12/2025 (30 dias)"]
    ]
    t1 = Table(data_cliente, colWidths=[100, 300])
    elements.append(t1)
    elements.append(Spacer(1, 20))
    
    # Potencias
    elements.append(Paragraph("<b>Potencias Contratadas (kW):</b>", styles['Heading3']))
    pot_data = [
        ["P1", "P2", "P3", "P4", "P5", "P6"],
        ["25.20", "25.20", "25.20", "25.20", "25.20", "25.20"]
    ]
    t2 = Table(pot_data, colWidths=[60]*6)
    t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
    elements.append(t2)
    elements.append(Spacer(1, 20))
    
    # Consumos
    elements.append(Paragraph("<b>Consumos por Periodo (kWh):</b>", styles['Heading3']))
    cons_data = [
        ["Periodo", "Lectura (kWh)"],
        ["P1 (Punta)", "540"],
        ["P2 (Llano)", "480"],
        ["P3 (Valle)", "620"],
        ["P4 (Valle)", "410"],
        ["P5 (Valle)", "350"],
        ["P6 (Valle)", "780"]
    ]
    t3 = Table(cons_data, colWidths=[150, 100])
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
    elements.append(t3)
    elements.append(Spacer(1, 30))
    
    # TOTAL
    elements.append(Paragraph("<b>TOTAL FACTURA: 845,30 €</b>", styles['Heading1']))
    
    doc.build(elements)
    print("✅ Factura generada con éxito: factura_test_30TD_comercial.pdf")

if __name__ == "__main__":
    create_pro_invoice()
