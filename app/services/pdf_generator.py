"""
Generador de PDF para presupuestos energéticos.
ESTRUCTURA EXACTA según especificación del usuario.
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
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
    - Página 1: Portada del modelo Patricia Vázquez
    - Páginas 2-N: Contenido generado (TABLA 1, TABLA 2, TABLA 3)
    - Páginas finales: Contraportada del modelo
    """
    
    # 1. Cargar modelo Patricia Vázquez
    modelo_pattern = os.path.join(os.path.dirname(__file__), '..', '..', 'modelosPresuPDF', '*Patricia*.pdf')
    modelo_files = glob.glob(modelo_pattern)
    
    if not modelo_files:
        raise FileNotFoundError("No se encontró el PDF modelo de Patricia Vázquez")
    
    modelo_path = modelo_files[0]
    modelo_reader = PdfReader(modelo_path)
    
    # 2. Crear PDF temporal con contenido
    buffer_content = BytesIO()
    doc = SimpleDocTemplate(
        buffer_content, 
        pagesize=A4, 
        rightMargin=2*cm, 
        leftMargin=2*cm, 
        topMargin=2*cm, 
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#00095C'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0073EC'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # ============================================================
    # TABLA 1: DATOS DE LA FACTURA
    # ============================================================
    story.append(Paragraph("ESTUDIO COMPARATIVO DE TARIFAS ELÉCTRICAS", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    story.append(Paragraph(f"<b>Fecha del estudio:</b> {fecha_actual}", styles['Normal']))
    story.append(Spacer(1, 0.3*cm))
    
    cliente_nombre = factura.cliente.nombre if factura.cliente else "Cliente"
    story.append(Paragraph(f"<b>Cliente:</b> {cliente_nombre}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("TABLA 1: Datos de la Factura Analizada", heading_style))
    
    atr = getattr(factura, 'atr', '2.0TD') or '2.0TD'
    periodo_dias = getattr(factura, 'periodo_dias', 30) or 30
    
    tabla1_data = [
        ["Concepto", "Valor"],
        ["CUPS", factura.cups or "No disponible"],
        ["ATR (Tipo de tarifa)", atr],
        ["Periodo de facturación", f"{periodo_dias} días"],
        ["Consumo P1 (Punta)", fmt_num(getattr(factura, 'consumo_p1_kwh', None), suffix="kWh")],
        ["Consumo P2 (Llano)", fmt_num(getattr(factura, 'consumo_p2_kwh', None), suffix="kWh")],
        ["Consumo P3 (Valle)", fmt_num(getattr(factura, 'consumo_p3_kwh', None), suffix="kWh")],
        ["Potencia P1 (Punta)", fmt_num(getattr(factura, 'potencia_p1_kw', None), suffix="kW")],
        ["Potencia P2 (Valle)", fmt_num(getattr(factura, 'potencia_p2_kw', None), suffix="kW")],
        ["Alquiler contador", fmt_num(getattr(factura, 'alquiler_contador', None), suffix="€")],
        ["Impuesto eléctrico (IEE)", fmt_num(getattr(factura, 'impuesto_electrico', None), suffix="€")],
        ["IVA", fmt_num(getattr(factura, 'iva', None), suffix="€")],
        ["IVA porcentaje", fmt_num(getattr(factura, 'iva_porcentaje', 21), decimals=0, suffix="%")],
        ["TOTAL FACTURA ACTUAL", fmt_num(factura.total_factura, suffix="€")],
    ]
    
    tabla1 = Table(tabla1_data, colWidths=[10*cm, 6*cm])
    tabla1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00095C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FEE2E2')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(tabla1)
    story.append(PageBreak())
    
    # ============================================================
    # TABLA 2: ESTUDIO COMPARATIVO (DESGLOSE EXACTO)
    # ============================================================
    story.append(Paragraph("TABLA 2: Estudio Comparativo - Oferta Recomendada", heading_style))
    story.append(Spacer(1, 0.3*cm))
    
    provider = selected_offer.get('provider', 'N/A')
    plan_name = selected_offer.get('plan_name', 'N/A')
    story.append(Paragraph(f"<b>Tarifa propuesta:</b> {provider} - {plan_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Periodo:</b> {periodo_dias} días", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Leer breakdown
    breakdown = selected_offer.get('breakdown', {})
    coste_energia = float(breakdown.get('coste_energia', 0.0))
    coste_potencia = float(breakdown.get('coste_potencia', 0.0))
    
    # Obtener potencias y consumos para desglose
    pot_p1 = float(getattr(factura, 'potencia_p1_kw', 0) or 0)
    pot_p2 = float(getattr(factura, 'potencia_p2_kw', 0) or 0)
    cons_p1 = float(getattr(factura, 'consumo_p1_kwh', 0) or 0)
    cons_p2 = float(getattr(factura, 'consumo_p2_kwh', 0) or 0)
    cons_p3 = float(getattr(factura, 'consumo_p3_kwh', 0) or 0)
    
    # Calcular precios unitarios estimados
    precio_pot_p1 = (coste_potencia / 2 / pot_p1 / periodo_dias) if pot_p1 > 0 else 0
    precio_pot_p2 = (coste_potencia / 2 / pot_p2 / periodo_dias) if pot_p2 > 0 else 0
    
    total_kwh = cons_p1 + cons_p2 + cons_p3
    precio_energia = (coste_energia / total_kwh) if total_kwh > 0 else 0
    
    # Calcular estructura EXACTA
    subtotal_sin_impuestos = coste_energia + coste_potencia
    iee = subtotal_sin_impuestos * 0.0511269632
    alquiler = float(breakdown.get('alquiler_contador', 0.0))
    base_iva = subtotal_sin_impuestos + iee + alquiler
    
    iva_pct = float(getattr(factura, 'iva_porcentaje', 21)) / 100.0
    iva_importe = base_iva * iva_pct
    total_factura_nueva = base_iva + iva_importe
    
    tabla2_data = [
        ["Concepto", "Cálculo", "Importe"],
        # POTENCIA
        ["POTENCIA", "", ""],
        ["  └ P1 (Punta)", f"{pot_p1} kW × {precio_pot_p1:.6f} €/kW/día × {periodo_dias} días", fmt_num(coste_potencia / 2, suffix="€")],
        ["  └ P2 (Valle)", f"{pot_p2} kW × {precio_pot_p2:.6f} €/kW/día × {periodo_dias} días", fmt_num(coste_potencia / 2, suffix="€")],
        ["Subtotal Potencia", "", fmt_num(coste_potencia, suffix="€")],
        # ENERGÍA
        ["ENERGÍA", "", ""],
        ["  └ P1 (Punta)", f"{cons_p1} kWh × {precio_energia:.6f} €/kWh", fmt_num(cons_p1 * precio_energia, suffix="€")],
        ["  └ P2 (Llano)", f"{cons_p2} kWh × {precio_energia:.6f} €/kWh", fmt_num(cons_p2 * precio_energia, suffix="€")],
        ["  └ P3 (Valle)", f"{cons_p3} kWh × {precio_energia:.6f} €/kWh", fmt_num(cons_p3 * precio_energia, suffix="€")],
        ["Subtotal Energía", "", fmt_num(coste_energia, suffix="€")],
        # TOTALES
        ["SUBTOTAL SIN IMPUESTOS", "Potencia + Energía", fmt_num(subtotal_sin_impuestos, suffix="€")],
        ["IEE (5.11269632%)", "Subtotal × 0.0511269632", fmt_num(iee, suffix="€")],
        ["Alquiler contador", "", fmt_num(alquiler, suffix="€")],
        ["BASE IVA", "Subtotal + IEE + Alquiler", fmt_num(base_iva, suffix="€")],
        ["IVA (21%)", f"Base IVA × {int(iva_pct*100)}%", fmt_num(iva_importe, suffix="€")],
        ["TOTAL FACTURA", "Base IVA + IVA", fmt_num(total_factura_nueva, suffix="€")],
    ]
    
    tabla2 = Table(tabla2_data, colWidths=[6*cm, 5*cm, 5*cm])
    tabla2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00095C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#E2E8F0')),  # POTENCIA
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#E2E8F0')),  # ENERGÍA
        ('BACKGROUND', (0, 10), (-1, 10), colors.HexColor('#FEF2F2')),  # SUBTOTAL
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DCFCE7')),  # TOTAL
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 5), (0, 5), 'Helvetica-Bold'),
        ('FONTNAME', (0, 10), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(tabla2)
    story.append(PageBreak())
    
    # ============================================================
    # TABLA 3: AHORRO DESTACADO (VERDE GRANDE)
    # ============================================================
    story.append(Spacer(1, 2*cm))
    
    # Calcular ahorros
    total_factura_actual = float(factura.total_factura or 0.0)
    ahorro_periodo = total_factura_actual - total_factura_nueva
    factor_anual = 360.0 / float(periodo_dias)
    ahorro_anual = ahorro_periodo * factor_anual
    ahorro_mensual = ahorro_periodo * (30.0 / float(periodo_dias))
    
    # Título
    story.append(Paragraph("🎯 TU AHORRO ESTIMADO", title_style))
    story.append(Spacer(1, 1*cm))
    
    # Tabla principal (VERDE GRANDE)
    if ahorro_anual > 0:
        tabla3_data = [[f"AHORRO ANUAL: {ahorro_anual:.2f} €"]]
        bg_color = colors.HexColor('#16A34A')  # Verde
        text_color = colors.white
    else:
        tabla3_data = [[f"⚠️ COSTE ADICIONAL: {abs(ahorro_anual):.2f} €"]]
        bg_color = colors.HexColor('#DC2626')  # Rojo
        text_color = colors.white
    
    tabla3_principal = Table(tabla3_data, colWidths=[16*cm])
    tabla3_principal.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), text_color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 28),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOX', (0, 0), (-1, -1), 3, bg_color),
    ]))
    story.append(tabla3_principal)
    story.append(Spacer(1, 0.5*cm))
    
    # Detalles adicionales
    tabla3_detalles = [
        [f"Ahorro mensual: {ahorro_mensual:.2f} €"],
        [f"Ahorro en este periodo ({periodo_dias} días): {ahorro_periodo:.2f} €"],
    ]
    tabla3_det = Table(tabla3_detalles, colWidths=[16*cm])
    tabla3_det.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(tabla3_det)
    
    # 3. Generar PDF de contenido
    doc.build(story)
    buffer_content.seek(0)
    
    # 4. Combinar: Portada + Contenido + Contraportada
    writer = PdfWriter()
    
    # Añadir página 1 del modelo (portada)
    writer.add_page(modelo_reader.pages[0])
    
    # Añadir contenido generado
    content_reader = PdfReader(buffer_content)
    for page in content_reader.pages:
        writer.add_page(page)
    
    # Añadir última página del modelo (contraportada, índice len-1)
    if len(modelo_reader.pages) >= 6:
        writer.add_page(modelo_reader.pages[-1])  # Última página
    
    # 5. Escribir PDF final
    final_buffer = BytesIO()
    writer.write(final_buffer)
    final_buffer.seek(0)
    
    return final_buffer
