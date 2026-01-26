"""
Generador de PDF para presupuestos energéticos.
ESTRUCTURA EXACTA según screenshots proporcionados por el usuario.
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from pypdf import PdfReader, PdfWriter
from datetime import datetime
import glob
import os


def fmt_num(value, decimals=2, suffix=""):
    """Formatear números con manejo de None/NaN"""
    try:
        if value is None:
            return f"0.00 {suffix}".strip()
        num = float(value)
        if num != num:  # NaN check
            return f"0.00 {suffix}".strip()
        return f"{num:.{decimals}f} {suffix}".strip()
    except (ValueError, TypeError):
        return f"0.00 {suffix}".strip()


def generar_pdf_presupuesto(factura, selected_offer, db):
    """
    Genera PDF combinando:
    - Página 1: Portada Patricia Vázquez
    - Página 2+: Contenido técnico (Tablas A, B, C)
    - Última página: Contraportada Patricia Vázquez
    """
    
    # 0. Cargar modelo Patricia Vázquez
    modelo_pattern = os.path.join(os.path.dirname(__file__), '..', '..', 'modelosPresuPDF', '*Patricia*.pdf')
    modelo_files = glob.glob(modelo_pattern)
    if not modelo_files:
        raise FileNotFoundError("No se encontró el PDF modelo de Patricia Vázquez")
    modelo_reader = PdfReader(modelo_files[0])
    
    # 1. Crear contenido dinámico
    buffer_content = BytesIO()
    doc = SimpleDocTemplate(buffer_content, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    styles.add(ParagraphStyle(name='EnergyTitle', fontSize=22, textColor=colors.HexColor('#00095C'), alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=20))
    styles.add(ParagraphStyle(name='EnergyHeading', fontSize=14, textColor=colors.HexColor('#0073EC'), fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=10))
    styles.add(ParagraphStyle(name='EnergySubheading', fontSize=11, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=5))
    
    story = []
    
    # --- LOGO ---
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'energyluz_logo.png')
    if os.path.exists(logo_path):
        story.append(Image(logo_path, width=5*cm, height=1*cm, hAlign='CENTER'))
        story.append(Spacer(1, 0.5*cm))

    # --- TÍTULO Y FECHA ---
    story.append(Paragraph("PRESUPUESTO ENERGÉTICO", styles['EnergyTitle']))
    story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # --- DATOS DEL CLIENTE ---
    story.append(Paragraph("DATOS DEL CLIENTE", styles['EnergyHeading']))
    cliente_data = [
        ["Cliente:", (factura.cliente.nombre if factura.cliente else "N/A").upper()],
        ["CUPS:", factura.cups or "N/A"]
    ]
    t_cliente = Table(cliente_data, colWidths=[4*cm, 13*cm])
    t_cliente.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_cliente)
    story.append(Spacer(1, 0.8*cm))

    # --- SITUACIÓN ACTUAL ---
    story.append(Paragraph("SITUACIÓN ACTUAL", styles['EnergyHeading']))
    actual_total = float(factura.total_factura or 0.0)
    periodo = int(getattr(factura, 'periodo_dias', 30) or 30)
    
    t_actual = Table([
        ["Total factura actual:", f"{actual_total:.2f} € (periodo: {periodo} días)"]
    ], colWidths=[7*cm, 10*cm])
    t_actual.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_actual)
    story.append(Spacer(1, 0.8*cm))

    # --- OFERTA PROPUESTA ---
    story.append(Paragraph("OFERTA PROPUESTA", styles['EnergyHeading']))
    
    breakdown = selected_offer.get('breakdown', {})
    total_est = float(selected_offer.get('estimated_total', 0.0))
    ahorro_anual = (actual_total - total_est) * (360 / periodo)
    
    oferta_data = [
        ["Comercializadora:", selected_offer.get('provider', 'N/A')],
        ["Tarifa:", selected_offer.get('plan_name', 'N/A')],
        ["Total estimado:", f"{total_est:.2f} € (periodo: {periodo} días)"],
        ["Ahorro anual estimado (Ahorro Total):", f"{ahorro_anual:.2f} €/año"]
    ]
    t_oferta = Table(oferta_data, colWidths=[7*cm, 10*cm])
    t_oferta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('ALIGN', (1,1), (1,1), 'RIGHT'),
        ('ALIGN', (1,2), (1,2), 'RIGHT'),
        ('ALIGN', (1,3), (1,3), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_oferta)
    
    nota_style = ParagraphStyle(name='SmallNote', fontSize=8, textColor=colors.grey, italics=True, spaceBefore=5)
    story.append(Paragraph("*Precio medio estructural: (Energía + Potencia) / kWh total. Excluye impuestos y alquileres.", nota_style))
    story.append(Spacer(1, 0.5*cm))
    
    box_style = ParagraphStyle(name='BlueBox', fontSize=9, textColor=colors.HexColor('#2563EB'), backColor=colors.HexColor('#EFF6FF'), borderPadding=10, borderRadius=5)
    story.append(Paragraph("*Nota: La comparación se basa en el coste total final (IVA incl.). Tu tarifa actual incluye descuentos o condiciones comerciales especiales que impiden un desglose estructural exacto de energía y potencia. El ahorro anual estimado es el valor más preciso disponible.", box_style))
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("DESGLOSE TÉCNICO", styles['EnergyHeading']))
    story.append(Spacer(1, 0.3*cm))

    # --- TABLA A: DETALLE FACTURA ANALIZADA ---
    story.append(Paragraph("A) Detalle de la factura analizada (línea base)", styles['EnergySubheading']))
    
    # Datos reales de la factura
    iee_factura = float(getattr(factura, 'impuesto_electrico', 0) or 0)
    alquiler_factura = float(getattr(factura, 'alquiler_contador', 0) or 0)
    iva_factura = float(getattr(factura, 'iva', 0) or 0)
    estructural_factura = actual_total - iee_factura - alquiler_factura - iva_factura
    
    tabla_a_data = [
        ["Concepto", "Valor (€)"],
        ["Detalle Estructural (E+P)", "Incluido en Condiciones Actuales*"],
        ["Impuesto eléctrico", fmt_num(iee_factura, suffix=" €")],
        ["Alquiler contador", fmt_num(alquiler_factura, suffix=" €")],
        ["IVA (21%)", fmt_num(iva_factura, suffix=" €")],
        ["TOTAL FACTURA ANALIZADA", fmt_num(actual_total, suffix=" €")]
    ]
    t_a = Table(tabla_a_data, colWidths=[11*cm, 6*cm])
    t_a.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#FEF2F2')), # Rojo suave
    ]))
    story.append(t_a)
    story.append(Spacer(1, 0.8*cm))

    # --- TABLA B: DETALLE OFERTA RECOMENDADA ---
    story.append(Paragraph("B) Detalle de la oferta recomendada", styles['EnergySubheading']))
    
    coste_e = float(breakdown.get('coste_energia', 0.0))
    coste_p = float(breakdown.get('coste_potencia', 0.0))
    subtotal_ep = coste_e + coste_p
    alquiler_oferta = float(breakdown.get('alquiler_contador', 0.0))
    
    # Impuestos según screenshot (IEE + IVA agrupado)
    impuestos_total = total_est - subtotal_ep - alquiler_oferta
    
    tabla_b_data = [
        ["Concepto", "Valor estimado (€)"],
        ["Energía (E)", fmt_num(coste_e, suffix=" €")],
        ["Potencia (P)", fmt_num(coste_p, suffix=" €")],
        ["SUBTOTAL ESTRUCTURAL (E+P)", fmt_num(subtotal_ep, suffix=" €")],
        ["Impuestos (IEE + IVA)", fmt_num(impuestos_total, suffix=" €")],
        ["Alquiler contador", fmt_num(alquiler_oferta, suffix=" €")],
        ["TOTAL ESTIMADO CON IMPUESTOS", fmt_num(total_est, suffix=" €")]
    ]
    t_b = Table(tabla_b_data, colWidths=[11*cm, 6*cm])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#DCFCE7')), # Verde suave
    ]))
    story.append(t_b)
    story.append(Spacer(1, 0.8*cm))

    # --- TABLA C: CÁLCULO DE AHORRO ---
    story.append(Paragraph("C) Cálculo de ahorro", styles['EnergySubheading']))
    
    coste_diario = subtotal_ep / periodo
    
    tabla_c_data = [
        ["Concepto / Paso", "Fórmula", "Resultado"],
        ["3) Coste diario est.", "(E+P nueva) / días", f"{coste_diario:.2f} €/día"],
        ["4) Ahorro ANUAL TOTAL", "Ahorro periodo × (360 / días)", f"{ahorro_anual:.2f} €/año"]
    ]
    t_c = Table(tabla_c_data, colWidths=[6*cm, 7*cm, 4*cm])
    t_c.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2,1), (2,-1), 'RIGHT'),
    ]))
    story.append(t_c)
    story.append(Spacer(1, 1*cm))

    # --- RESUMEN FINAL ---
    story.append(Paragraph("RESUMEN", styles['EnergyHeading']))
    t_resumen = Table([
        ["AHORRO TOTAL ANUAL ESTIMADO:", f"{ahorro_anual:.2f} €/año"]
    ], colWidths=[11*cm, 6*cm])
    t_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#16A34A')), # Verde Energy
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 14),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(t_resumen)
    story.append(Spacer(1, 1*cm))

    # --- FOOTER ---
    footer_text = """
    <b>EnergyLuz</b> - Asesoramos nosotros, Ahorras tú<br/>
    📧 info@energyluz.es | 📞 646 229 534<br/>
    Especialistas en fotovoltaica y asesoramiento energético
    """
    story.append(Paragraph(footer_text, ParagraphStyle(name='Footer', fontSize=9, textColor=colors.HexColor('#0073EC'), alignment=TA_CENTER)))

    # 2. Generar PDF
    doc.build(story)
    buffer_content.seek(0)
    
    # 3. Combinar con modelo Patricia
    writer = PdfWriter()
    writer.add_page(modelo_reader.pages[0]) # Portada
    
    dynamic_reader = PdfReader(buffer_content)
    for p in dynamic_reader.pages:
        writer.add_page(p)
        
    if len(modelo_reader.pages) > 1:
        writer.add_page(modelo_reader.pages[-1]) # Contraportada
        
    final_buffer = BytesIO()
    writer.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer
