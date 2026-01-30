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
import logging
import glob
import os

logger = logging.getLogger(__name__)


def fmt_num(value, decimals=2, suffix="", fallback="0.00"):
    """Formatear n?meros con manejo de None/NaN"""
    try:
        if value is None:
            return fallback
        num = float(value)
        if num != num:  # NaN check
            return fallback
        formatted = f"{num:.{decimals}f} {suffix}".strip()
        return formatted
    except (ValueError, TypeError):
        return fallback


def normalize_pct(value):
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed / 100 if parsed > 1 else parsed


def generar_pdf_presupuesto(factura, selected_offer, db):
    """
    Genera PDF combinando:
    - Página 1: Portada Francisco Miguel
    - Página 2+: Contenido técnico (Tablas A, B, C)
    - Última página: Contraportada Francisco Miguel
    """
    
    # 0. Cargar modelo fijo de Francisco Miguel con búsqueda robusta
    # Intenta múltiples rutas para soportar diferentes entornos (dev, producción en Render, etc.)
    possible_paths = [
        # Ruta relativa desde services/
        os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'modelosPresuPDF',
            'Estudio EnergyLuz (Francisco Miguel Gallego).pdf'
        ),
        # Ruta desde raíz del proyecto (para Render)
        os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            '..',
            'modelosPresuPDF',
            'Estudio EnergyLuz (Francisco Miguel Gallego).pdf'
        ),
        # Búsqueda glob en el directorio actual y subdirectorios
    ]
    
    modelo_path = None
    for path in possible_paths:
        if os.path.isfile(path):
            modelo_path = path
            logger.info(f"[PDF] Modelo PDF encontrado en: {path}")
            break
    
    # Si no encontró en rutas predefinidas, buscar recursivamente
    if not modelo_path:
        try:
            for root, dirs, files in os.walk(os.path.dirname(__file__)):
                for f in files:
                    if "Francisco Miguel Gallego" in f and f.endswith(".pdf"):
                        modelo_path = os.path.join(root, f)
                        logger.info(f"[PDF] Modelo PDF encontrado por búsqueda en: {modelo_path}")
                        break
                if modelo_path:
                    break
        except Exception as e:
            logger.warning(f"[PDF] Error en búsqueda recursiva: {e}")
    
    if not modelo_path or not os.path.isfile(modelo_path):
        raise FileNotFoundError(
            f"No se encontró el PDF modelo 'Estudio EnergyLuz (Francisco Miguel Gallego).pdf' "
            f"en rutas esperadas. Búsqueda realizada desde: {os.path.dirname(__file__)}"
        )
    
    modelo_reader = PdfReader(modelo_path)
    
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
    
    # Datos reales de la factura (solo si se puede calcular sin inventar)
    iee_pct = 0.0511269632
    alquiler_factura = float(getattr(factura, 'alquiler_contador', 0) or 0)
    iva_pct = normalize_pct(getattr(factura, 'iva_porcentaje', None))
    coste_energia_actual = getattr(factura, 'coste_energia_actual', None)
    coste_potencia_actual = getattr(factura, 'coste_potencia_actual', None)

    subtotal_sin_impuestos = None
    if coste_energia_actual is not None and coste_potencia_actual is not None:
        try:
            subtotal_sin_impuestos = float(coste_energia_actual) + float(coste_potencia_actual)
        except (TypeError, ValueError):
            subtotal_sin_impuestos = None

    iee_factura = None
    iva_factura = None
    if subtotal_sin_impuestos is not None and iva_pct is not None:
        iee_factura = subtotal_sin_impuestos * iee_pct
        base_iva = subtotal_sin_impuestos + iee_factura + alquiler_factura
        iva_factura = base_iva * iva_pct

    iva_label = f"IVA ({iva_pct * 100:.0f}%)" if iva_pct is not None else "IVA"
    
    # Vista simplificada vs Desglosada
    mostrar_desglose_estructural = subtotal_sin_impuestos is not None and subtotal_sin_impuestos > 0

    logger.info(
        "[PDF] factura_id=%s subtotal_sin_impuestos=%s iva_pct=%s iee_pct=%s alquiler=%s iee_eur=%s iva_eur=%s",
        getattr(factura, 'id', None),
        subtotal_sin_impuestos,
        iva_pct,
        iee_pct,
        alquiler_factura,
        iee_factura,
        iva_factura,
    )
    
    if mostrar_desglose_estructural:
        # Si tenemos los datos, mostramos el desglose real
        tabla_a_data = [
            ["Concepto", "Valor (EUR)"],
            ["Energía (E)", fmt_num(coste_energia_actual, suffix=" EUR")],
            ["Potencia (P)", fmt_num(coste_potencia_actual, suffix=" EUR")],
            ["Impuesto eléctrico (IEE)", fmt_num(iee_factura, suffix=" EUR")],
            ["Alquiler contador", fmt_num(alquiler_factura, suffix=" EUR")],
            [iva_label, fmt_num(iva_factura, suffix=" EUR")],
            ["TOTAL FACTURA ANALIZADA", fmt_num(actual_total, suffix=" EUR")],
        ]
    else:
        # Vista simplificada: no inventar 0.00
        tabla_a_data = [
            ["Concepto", "Valor (EUR)"],
            ["Detalle Estructural (E+P)", "Incluido en Condiciones Actuales*"],
            ["Impuestos y Otros", "Incluidos en total*"],
            ["TOTAL FACTURA ANALIZADA", fmt_num(actual_total, suffix=" EUR")],
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
        ["Concepto", "Valor (EUR)"],
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

    # --- TABLA C: CÁLCULO PASO A PASO (Desglose de Fórmula) ---
    story.append(Paragraph("C) Cálculo paso a paso de la oferta propuesta", styles['EnergySubheading']))
    
    # ⭐ CRÍTICO: Leer consumos/potencias DESDE EL BREAKDOWN (no desde factura)
    # Esto garantiza que usamos los MISMOS valores que se usaron en el comparador
    consumo_p1 = float(breakdown.get('consumo_p1', 0) or 0)
    consumo_p2 = float(breakdown.get('consumo_p2', 0) or 0)
    consumo_p3 = float(breakdown.get('consumo_p3', 0) or 0)
    potencia_p1 = float(breakdown.get('potencia_p1', 0) or 0)
    potencia_p2 = float(breakdown.get('potencia_p2', 0) or 0)
    
    # Extraemos costes unitarios de breakdown
    tarifa_p1 = float(breakdown.get('precio_unitario_p1', 0) or 0)
    tarifa_p2 = float(breakdown.get('precio_unitario_p2', 0) or 0)
    tarifa_p3 = float(breakdown.get('precio_unitario_p3', 0) or 0)
    precio_potencia_p1 = float(breakdown.get('precio_potencia_p1', 0) or 0)
    precio_potencia_p2 = float(breakdown.get('precio_potencia_p2', 0) or 0)
    
    # IEE estándar según regulación
    iee_pct = 0.0511269632
    bono_social = float(breakdown.get('bono_social', 0) or 0)
    
    # --- TABLA C: DESGLOSE ESTRUCTURADO ---
    tabla_c_data = [
        ["PASO", "CONCEPTO", "FÓRMULA / CÁLCULO", "IMPORTE (€)"],
        ["1", "POTENCIA (P1+P2)", f"({potencia_p1:.2f} + {potencia_p2:.2f}) kW × días × tarifa", f"{coste_p:.2f}"],
        ["2", "CONSUMO (P1+P2+P3)", f"({consumo_p1:.2f} + {consumo_p2:.2f} + {consumo_p3:.2f}) kWh × tarifa", f"{coste_e:.2f}"],
        ["", "Total Potencia + Consumo", "", f"{subtotal_ep:.2f}"],
        ["3", "+ Bono Social (si aplica)", "Descuento regulatorio", f"-{bono_social:.2f}"],
        ["", "═══ TOTAL 1 ═══", "Subtotal (antes de impuestos)", f"{subtotal_ep - bono_social:.2f}"],
        ["4", "× Impuesto Eléctrico (IEE)", f"Subtotal × {iee_pct*100:.2f}%", f"{impuestos_total * (iee_pct/(iee_pct+0.21)):.2f}"],
        ["", "═══ TOTAL 2 ═══", "Después de impuesto eléctrico", f"{subtotal_ep - bono_social + (impuestos_total * (iee_pct/(iee_pct+0.21))):.2f}"],
        ["5", "+ Alquiler Contador", "Cuota fija de alquiler", f"{alquiler_oferta:.2f}"],
        ["", "═══ TOTAL 3 ═══", "Antes de IVA", f"{subtotal_ep - bono_social + (impuestos_total * (iee_pct/(iee_pct+0.21))) + alquiler_oferta:.2f}"],
        ["6", "IVA (21%)", f"Total 3 × 21%", f"{impuestos_total * (0.21/(iee_pct+0.21)):.2f}"],
        ["", "═══ IMPORTE TOTAL ═══", "TOTAL CON IVA", f"{total_est:.2f}"],
    ]
    
    t_c = Table(tabla_c_data, colWidths=[1.2*cm, 3.5*cm, 6.5*cm, 2.8*cm])
    t_c.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (3,0), (3,-1), 'RIGHT'),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#E2E8F0')),
        ('FONTNAME', (0, 7), (-1, 7), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 7), (-1, 7), colors.HexColor('#E2E8F0')),
        ('FONTNAME', (0, 9), (-1, 9), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 9), (-1, 9), colors.HexColor('#E2E8F0')),
        ('FONTNAME', (0, 11), (-1, 11), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 11), (-1, 11), 10),
        ('BACKGROUND', (0, 11), (-1, 11), colors.HexColor('#DCFCE7')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_c)
    story.append(Spacer(1, 0.8*cm))
    
    # Nota explicativa
    nota_formula = ParagraphStyle(
        name='NotaFormula',
        fontSize=8,
        textColor=colors.HexColor('#475569'),
        italics=True,
        spaceBefore=5
    )
    story.append(Paragraph(
        "* Esta tabla muestra el cálculo paso a paso de la tarifa propuesta, permitiendo auditar cada etapa del proceso. "
        "Los importes se calculan aplicando las tarifas unitarias de cada comercializadora.",
        nota_formula
    ))
    story.append(Spacer(1, 0.8*cm))

    # --- RESUMEN FINAL ---
    story.append(Paragraph("RESUMEN", styles['EnergyHeading']))
    
    # Ahorro ANUAL (Cifra Reina - Grande y Verde)
    ahorro_mensual_equiv = ahorro_anual / 12  # Calculamos el equivalente mensual
    
    t_resumen = Table([
        ["AHORRO TOTAL ANUAL:", f"{ahorro_anual:.2f} €/año"]
    ], colWidths=[10*cm, 7*cm])
    t_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#16A34A')), # Verde intenso
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 18),  # MÁS GRANDE
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 20),
        ('TOPPADDING', (0,0), (-1,-1), 20),
    ]))
    story.append(t_resumen)
    
    # Ahorro mensual (Secundario - Pequeño y gris)
    nota_mensual = ParagraphStyle(
        name='NotaMensual', 
        fontSize=9, 
        textColor=colors.HexColor('#64748B'), 
        alignment=TA_RIGHT,
        spaceBefore=5
    )
    story.append(Paragraph(
        f"(Equivalente mensual: ~{ahorro_mensual_equiv:.2f} €/mes)", 
        nota_mensual
    ))
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
