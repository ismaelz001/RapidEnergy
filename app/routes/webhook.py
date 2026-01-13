from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.conn import get_db
from app.db.models import Factura, Cliente, Comparativa
from app.exceptions import DomainError
from pydantic import BaseModel
from typing import Optional
import json
import logging
import inspect


router = APIRouter(prefix="/webhook", tags=["webhook"])


class FacturaUpdate(BaseModel):
    atr: Optional[str] = None
    potencia_p1_kw: Optional[float] = None
    potencia_p2_kw: Optional[float] = None
    consumo_p1_kwh: Optional[float] = None
    consumo_p2_kwh: Optional[float] = None
    consumo_p3_kwh: Optional[float] = None
    consumo_p4_kwh: Optional[float] = None
    consumo_p5_kwh: Optional[float] = None
    consumo_p6_kwh: Optional[float] = None
    bono_social: Optional[bool] = None
    servicios_vinculados: Optional[bool] = None
    alquiler_contador: Optional[float] = None
    impuesto_electrico: Optional[float] = None
    iva: Optional[float] = None
    total_factura: Optional[float] = None
    estado_factura: Optional[str] = None
    cups: Optional[str] = None
    numero_factura: Optional[str] = None


class OfferSelection(BaseModel):
    """Modelo para recibir la oferta seleccionada por el usuario."""
    provider: str
    plan_name: str
    estimated_total: float
    saving_amount: float
    saving_percent: float
    commission: Optional[float] = None
    tag: Optional[str] = None
    breakdown: Optional[dict] = None


REQUIRED_FACTURA_FIELDS = [
    "atr",
    "consumo_p1_kwh",
    "consumo_p2_kwh",
    "consumo_p3_kwh",
    "potencia_p1_kw",
    "potencia_p2_kw",
    "total_factura",
]


def validate_factura_completitud(factura: Factura):
    """
    Valida que una factura tenga los campos minimos para comparar (2.0TD).
    Devuelve (is_valid: bool, errors: dict[field, str]).
    CUPS es OBLIGATORIO (no puede estar vacío).
    """
    errors = {}
    
    # Validación CUPS obligatoria
    if not factura.cups or not str(factura.cups).strip():
        errors["cups"] = "CUPS es obligatorio y no puede estar vacío"
    
    for field in REQUIRED_FACTURA_FIELDS:
        val = getattr(factura, field, None)
        # Para booleanos, solo consideramos ausente si es None (False es válido)
        if isinstance(val, bool):
            if val is None:
                errors[field] = "Campo obligatorio ausente"
        elif isinstance(val, str):
            if not val.strip():
                errors[field] = "Campo obligatorio ausente"
        else:
            if val is None:
                errors[field] = "Campo obligatorio ausente"
    return len(errors) == 0, errors


from app.utils.cups import normalize_cups, is_valid_cups


@router.post("/upload_v2")
@router.post("/upload")  # Alias para compatibilidad con frontend
async def process_factura(file: UploadFile, db: Session = Depends(get_db)):
    # --- LOGS DE DIAGNÓSTICO (OBJETIVO 1) ---
    print(f"\n🚀 [UPLOAD] Recibiendo archivo: {file.filename}")
    print(f"📁 Tipo: {file.content_type}")
    
    # 1. Leer el archivo
    file_bytes = await file.read()
    print(f"📊 Tamaño: {len(file_bytes)} bytes")
    
    # --- DEDUPLICACION POR HASH ---
    import hashlib
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    existing_by_hash = (
        db.query(Factura)
        .options(joinedload(Factura.cliente)) # Eager load cliente
        .filter(Factura.file_hash == file_hash)
        .first()
    )
    
    if existing_by_hash:
        client_info = None
        msg = "Esta factura ya fue subida anteriormente."
        if existing_by_hash.cliente:
            c = existing_by_hash.cliente
            client_info = {
                "id": c.id,
                "nombre": c.nombre,
                "estado": c.estado
            }
            msg = f"Factura duplicada. Pertenece al cliente {c.nombre}."
            
        raise HTTPException(
            status_code=409,
            detail={
                "status": "duplicate",
                "message": msg,
                "id": existing_by_hash.id,
                "client": client_info
            }
        )

    # 2. OCR y extraccion de datos
    from app.services.ocr import extract_data_from_pdf, build_raw_data_payload, merge_raw_data_audit
    ocr_data = extract_data_from_pdf(file_bytes)
    
    # --- LOGS DE DEBUG QA (TEST_MODE) ---
    import os
    if os.getenv("TEST_MODE") == "true":
        print(f"\n--- [DEBUG OCR] ---")
        print(f"Motor: {ocr_data.get('ocr_engine', 'Standard/Vision')}")
        print(f"Archivo: {file.filename}")
        print(f"Hash: {file_hash}")
        print(f"CUPS Detectado: {ocr_data.get('cups')}")
        print(f"Total Detectado: {ocr_data.get('total_factura')}")
        print(f"Cliente Detectado: {ocr_data.get('titular')}")
        print(f"-------------------\n")
    
    # --- NORMALIZACIÓN Y DEDUPLICACIÓN TRI-FACTOR ---
    cups_extraido = normalize_cups(ocr_data.get("cups"))
    # Validación estricta para persistencia: si no es válido, lo descartamos ahora
    if cups_extraido and not is_valid_cups(cups_extraido):
        print(f"[WEBHOOK] CUPS inválido detectado y descartado: {cups_extraido}")
        cups_extraido = None
    fecha_ocr = ocr_data.get("fecha")
    total_ocr = ocr_data.get("total_factura")
    
    if cups_extraido and fecha_ocr and total_ocr:
        # Buscamos duplicado exacto por datos
        duplicate = (
            db.query(Factura)
            .filter(Factura.cups == cups_extraido)
            .filter(Factura.fecha == fecha_ocr)
            .filter(Factura.total_factura == total_ocr)
            .first()
        )
        if duplicate:
             raise HTTPException(
                status_code=409,
                detail={
                    "status": "conflict",
                    "message": f"Factura duplicada detectada para el CUPS {cups_extraido} en la fecha {fecha_ocr}.",
                    "id": duplicate.id
                }
            )

    # --- DEDUPLICACION POR NUMERO FACTURA (Extra check) ---
    num_factura_ocr = ocr_data.get("numero_factura")
    if cups_extraido and num_factura_ocr:
        existing_by_num = (
            db.query(Factura)
            .filter(Factura.cups == cups_extraido)
            .filter(Factura.numero_factura == num_factura_ocr)
            .first()
        )
        if existing_by_num:
              raise HTTPException(
                status_code=409,
                detail={
                    "status": "conflict",
                    "message": f"Ya existe una factura con número {num_factura_ocr} para este CUPS.",
                    "id": existing_by_num.id
                }
            )

    # 3. Logica Upsert Cliente
    # Datos personales del OCR (solo para clientes nuevos)
    nombre_ocr = ocr_data.get("titular")
    email_ocr = ocr_data.get("email")
    dni_ocr = ocr_data.get("dni")
    direccion_ocr = ocr_data.get("direccion")
    telefono_ocr = ocr_data.get("telefono")
    provincia_ocr = ocr_data.get("provincia")
    
    cliente_db = None

    if cups_extraido:
        # Buscar cliente existente por CUPS (YA NORMALIZADO)
        cliente_db = db.query(Cliente).filter(Cliente.cups == cups_extraido).first()
        if not cliente_db:
            # Crear nuevo cliente si no existe, rellenando datos OCR
            cliente_db = Cliente(
                cups=cups_extraido,
                nombre=nombre_ocr,
                email=email_ocr,
                dni=dni_ocr,
                direccion=direccion_ocr,
                provincia=provincia_ocr,
                telefono=telefono_ocr,
                origen="factura_upload",
                estado="lead",
            )
            db.add(cliente_db)
            db.commit()
            db.refresh(cliente_db)
    else:
        # Caso sin CUPS: Crear cliente 'lead' sin CUPS
        cliente_db = Cliente(
            origen="factura_upload_no_cups",
            estado="lead",
        )
        db.add(cliente_db)
        db.commit()
        db.refresh(cliente_db)
        
    if cliente_db and cups_extraido:
        # Actualizar datos del cliente si faltan en BD y vienen del OCR
        updated = False
        if not cliente_db.nombre and nombre_ocr:
            cliente_db.nombre = nombre_ocr
            updated = True
        if not cliente_db.dni and dni_ocr:
            cliente_db.dni = dni_ocr
            updated = True
        if not cliente_db.direccion and direccion_ocr:
            cliente_db.direccion = direccion_ocr
            updated = True
        if not cliente_db.provincia and provincia_ocr:
            cliente_db.provincia = provincia_ocr
            updated = True
        if not cliente_db.telefono and telefono_ocr:
            cliente_db.telefono = telefono_ocr
            updated = True
        if not cliente_db.email and email_ocr:
            cliente_db.email = email_ocr
            updated = True
        
        if updated:
            db.commit()
            db.refresh(cliente_db)

    # 4. Crear factura vinculada
    # Ensure dias_facturados goes into parsed_fields/raw_data since no column exists
    raw_payload_str = build_raw_data_payload(
        ocr_data.get("raw_text"),
        extraction_summary=ocr_data.get("extraction_summary"),
    )
    # Merge parsed_fields into raw_data JSON for debugging/fallback
    try:
        payload_json = json.loads(raw_payload_str)
        if "parsed_fields" in ocr_data:
            payload_json["parsed_fields"] = ocr_data["parsed_fields"]
        if "dias_facturados" in ocr_data:
            payload_json["dias_facturados"] = ocr_data["dias_facturados"]
        raw_payload_str = json.dumps(payload_json, ensure_ascii=False)
    except:
        pass

    # Usamos el CUPS ya validado en el paso de deduplicación
    cups_final_db = cups_extraido
    
    # [CUPS-AUDIT] LOG #4: Persistence
    print(f"""
[CUPS-AUDIT] #4 - DATABASE PERSISTENCE
  factura_id: (pending commit)
  cups_ocr_input: {ocr_data.get('cups')}
  cups_final_db: {cups_final_db}
  atr: {ocr_data.get('atr')}
""")

    nueva_factura = Factura(
        filename=file.filename,
        cups=cups_final_db,
        consumo_kwh=ocr_data.get("consumo_kwh"),
        importe=ocr_data.get("importe"), # Base imponible fallback?
        total_factura=ocr_data.get("total_factura"), # Priority
        fecha=ocr_data.get("fecha"),
        fecha_inicio=ocr_data.get("fecha_inicio_consumo"),
        fecha_fin=ocr_data.get("fecha_fin_consumo"),
        raw_data=raw_payload_str,
        
        # FIX: Fallback ATR extraction
        atr=ocr_data.get("atr"),
        cliente_id=cliente_db.id if cliente_db else None,
        
        # Deduplicacion
        file_hash=file_hash,
        numero_factura=ocr_data.get("numero_factura"),
        
        # Nuevos campos mapeados
        potencia_p1_kw=ocr_data.get("potencia_p1_kw"),
        potencia_p2_kw=ocr_data.get("potencia_p2_kw"),
        consumo_p1_kwh=ocr_data.get("consumo_p1_kwh"),
        consumo_p2_kwh=ocr_data.get("consumo_p2_kwh"),
        consumo_p3_kwh=ocr_data.get("consumo_p3_kwh"),
        consumo_p4_kwh=ocr_data.get("consumo_p4_kwh"),
        consumo_p5_kwh=ocr_data.get("consumo_p5_kwh"),
        consumo_p6_kwh=ocr_data.get("consumo_p6_kwh"),
        bono_social=ocr_data.get("bono_social"),
        servicios_vinculados=ocr_data.get("servicios_vinculados"),
        alquiler_contador=ocr_data.get("alquiler_contador"),
        impuesto_electrico=ocr_data.get("impuesto_electrico"),
        iva=ocr_data.get("iva"),
    )

    es_valida, errors = validate_factura_completitud(nueva_factura)
    nueva_factura.estado_factura = "lista_para_comparar" if es_valida else "pendiente_datos"
    nueva_factura.raw_data = merge_raw_data_audit(
        nueva_factura.raw_data, missing_fields=list(errors.keys())
    )

    # [CUPS-AUDIT] PRUEBA IRREFUTABLE START
    try:
        logging.warning(f"""[CUPS-AUDIT] STEP 1 PERSISTENCE:
        cups_raw: {str(ocr_data.get('cups'))[:80]}
        cups_norm: {str(nueva_factura.cups)[:80]}
        cups_valid: {is_valid_cups(str(nueva_factura.cups)) if nueva_factura.cups else False}
        normalize_source: {inspect.getsourcefile(normalize_cups)}
        """)
    except Exception as e:
        print(f"[CUPS-AUDIT] Logger Error: {e}")
    # [CUPS-AUDIT] END

    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    return {
        "id": nueva_factura.id,
        "filename": nueva_factura.filename,
        "ocr_preview": ocr_data, # Use the clean dict from OCR
        "message": "Factura procesada y guardada correctamente",
    }


@router.get("/facturas")
def list_facturas(db: Session = Depends(get_db)):
    facturas = db.query(Factura).options(joinedload(Factura.cliente)).all()
    return facturas


@router.get("/facturas/{factura_id}")
def get_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).options(joinedload(Factura.cliente)).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura


@router.put("/facturas/{factura_id}")
def update_factura(factura_id: int, factura_update: FacturaUpdate, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    update_data = factura_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == 'cups' and value:
            norm = normalize_cups(value)
            if norm and is_valid_cups(norm):
                value = norm
            else:
                # Si es inválido, ¿lo rechazamos o lo dejamos null? 
                # El usuario pidió "cups_norm=None". 
                # Pero en un PUT explícito quizás deberíamos dar error?
                # Siguiendo la instrucción estricta "Persistir cups_norm (no el raw)" y "if ... not is_valid ... None"
                value = None
        if key == "atr" and value:
            from app.services.ocr import extract_atr
            normalized_atr = extract_atr(str(value))
            value = normalized_atr or str(value).strip().upper()
        setattr(factura, key, value)

    # Validacion de completitud
    es_valida, errors = validate_factura_completitud(factura)
    factura.estado_factura = "lista_para_comparar" if es_valida else "pendiente_datos"
    from app.services.ocr import merge_raw_data_audit
    factura.raw_data = merge_raw_data_audit(
        factura.raw_data, missing_fields=list(errors.keys())
    )

    # [CUPS-AUDIT] PRUEBA IRREFUTABLE START
    try:
        logging.warning(f"""[CUPS-AUDIT] STEP 2 UPDATE:
        factura_id: {factura.id}
        cups_final: {str(factura.cups)[:80]}
        cups_valid: {is_valid_cups(str(factura.cups)) if factura.cups else False}
        normalize_source: {inspect.getsourcefile(normalize_cups)}
        """)
    except Exception as e:
        print(f"[CUPS-AUDIT] Logger Error: {e}")
    # [CUPS-AUDIT] END

    db.commit()
    db.refresh(factura)

    return {
        "factura": factura,
        "is_valid": es_valida,
        "errors": errors,
        "missing_fields": list(errors.keys()),
        "estado_factura": factura.estado_factura,
    }


@router.post("/comparar/facturas/{factura_id}")
def comparar_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # Validar que la factura este completa (2.0TD)
    es_valida, errors = validate_factura_completitud(factura)
    if not es_valida:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "La factura no tiene datos suficientes para comparar. Completa los campos requeridos.",
                "estado_factura": factura.estado_factura,
                "errors": errors,
            },
        )
    
    # Validar que existe total_factura
    if factura.total_factura is None or factura.total_factura <= 0:
        raise HTTPException(
            status_code=400,
            detail="La factura no tiene un total válido para generar ofertas"
        )

    # Importar y ejecutar comparador
    from app.services.comparador import compare_factura
    
    try:
        result = compare_factura(factura, db)
        return result
    except DomainError as e:
        # P1 PRODUCCIÓN: Mapear errores de dominio a HTTP 422
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": e.message}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando ofertas: {str(e)}")


@router.post("/facturas/{factura_id}/seleccion")
def guardar_seleccion_oferta(factura_id: int, offer: OfferSelection, db: Session = Depends(get_db)):
    """
    ENTREGABLE 1: Guardar la oferta seleccionada por el usuario.
    - Persiste la oferta como JSON en la factura
    - Actualiza el estado a 'oferta_seleccionada'
    """
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Convertir oferta a JSON y guardar
    offer_dict = offer.dict()
    factura.selected_offer_json = json.dumps(offer_dict, ensure_ascii=False)
    factura.estado_factura = "oferta_seleccionada"
    
    db.commit()
    db.refresh(factura)
    
    return {
        "status": "ok",
        "message": "Oferta seleccionada guardada correctamente",
        "factura_id": factura.id,
        "estado": factura.estado_factura,
        "selected_offer": offer_dict
    }


@router.get("/facturas/{factura_id}/presupuesto.pdf")
def generar_presupuesto_pdf(factura_id: int, db: Session = Depends(get_db)):
    """
    ENTREGABLE 2: Generar PDF real con la oferta seleccionada.
    - Requiere que exista oferta seleccionada
    - Genera PDF con datos del cliente, CUPS, factura actual, oferta seleccionada
    - NO incluye comisión
    - Devuelve PDF para descarga
    """
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from datetime import datetime
    import os
    
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Validar que exista oferta seleccionada
    if not factura.selected_offer_json:
        raise HTTPException(
            status_code=400, 
            detail="No hay una oferta seleccionada para esta factura. Por favor, selecciona una oferta primero."
        )
    
    try:
        selected_offer = json.loads(factura.selected_offer_json)
    except:
        raise HTTPException(status_code=500, detail="Error al leer la oferta seleccionada")
    
    # Crear PDF en memoria
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#00095C'),  # Azul oscuro EnergyLuz
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0073EC'),  # Azul principal EnergyLuz
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Contenido del PDF
    story = []
    
    # Logo EnergyLuz (si existe)
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'energyluz_logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=5*cm, height=1*cm)
        logo.hAlign = 'CENTER'
        story.append(logo)
        story.append(Spacer(1, 0.3*cm))
    
    # Título
    story.append(Paragraph("PRESUPUESTO ENERGÉTICO", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Fecha
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    story.append(Paragraph(f"<b>Fecha:</b> {fecha_actual}", styles['Normal']))
    story.append(Spacer(1, 0.3*cm))
    
    # Información del cliente
    cliente_nombre = factura.cliente.nombre if factura.cliente else "Cliente"
    story.append(Paragraph("DATOS DEL CLIENTE", heading_style))
    
    cliente_data = [
        ["Cliente:", cliente_nombre],
        ["CUPS:", factura.cups or "No disponible"],
    ]
    cliente_table = Table(cliente_data, colWidths=[4*cm, 12*cm])
    cliente_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(cliente_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Factura actual
    story.append(Paragraph("SITUACIÓN ACTUAL", heading_style))
    current_data = [
        ["Total factura actual:", f"{factura.total_factura:.2f} €/mes"],
    ]
    current_table = Table(current_data, colWidths=[8*cm, 8*cm])
    current_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF2F2')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(current_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Oferta propuesta
    story.append(Paragraph("OFERTA PROPUESTA", heading_style))
    
    # Logo Comercializadora
    provider_name = selected_offer.get('provider', '').lower()
    logo_filename = None
    if 'iberdrola' in provider_name:
        logo_filename = 'logo_iberdrola.png'
    elif 'endesa' in provider_name:
        logo_filename = 'logo_endesa.png'
    elif 'naturgy' in provider_name:
        logo_filename = 'logo_naturgy.png'
        
    if logo_filename:
        com_logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', logo_filename)
        if os.path.exists(com_logo_path):
            try:
                # Ajustar tamaño (ancho 4cm, mantener ratio)
                com_logo = Image(com_logo_path, width=4*cm, height=1.5*cm, kind='proportional')
                com_logo.hAlign = 'LEFT'
                story.append(com_logo)
                story.append(Spacer(1, 0.2*cm))
            except:
                pass # Si falla la imagen, no romper el PDF

    oferta_data = [
        ["Comercializadora:", selected_offer.get('provider', 'N/A')],
        ["Tarifa:", selected_offer.get('plan_name', 'N/A')],
        ["Total estimado:", f"{selected_offer.get('estimated_total', 0):.2f} €/mes"],
        ["Ahorro mensual:", f"{selected_offer.get('saving_amount', 0):.2f} €"],
        ["Ahorro anual estimado:", f"{selected_offer.get('saving_amount', 0) * 12:.2f} €"],
    ]
    oferta_table = Table(oferta_data, colWidths=[8*cm, 8*cm])
    oferta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FDF4')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(oferta_table)
    story.append(Spacer(1, 1*cm))
    
    # Resumen de ahorro
    ahorro_anual = selected_offer.get('saving_amount', 0) * 12
    story.append(Paragraph("RESUMEN", heading_style))
    resumen_data = [
        ["AHORRO TOTAL ANUAL ESTIMADO:", f"{ahorro_anual:.2f} €"]
    ]
    resumen_table = Table(resumen_data, colWidths=[10*cm, 6*cm])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#16A34A')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(resumen_table)
    story.append(Spacer(1, 1*cm))
    
    # Nota al pie
    nota_style = ParagraphStyle(
        'Nota',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph(
        "Este presupuesto es un cálculo estimado basado en los datos de consumo proporcionados.<br/>Los ahorros reales pueden variar según el perfil de consumo.",
        nota_style
    ))
    story.append(Spacer(1, 0.5*cm))
    
    # Footer con contacto EnergyLuz
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#0073EC'),
        alignment=TA_CENTER
    )
    story.append(Paragraph(
        "<b>EnergyLuz</b> - Asesoramos nosotros, Ahorras tú<br/>"
        "📧 info@energyluz.es | 📞 646 229 534<br/>"
        "Especialistas en fotovoltaica y asesoramiento energético",
        footer_style
    ))
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    
    # Devolver como respuesta
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=presupuesto_factura_{factura_id}.pdf"
        }
    )


@router.delete("/facturas/{factura_id}")
async def delete_factura(factura_id: int, db: Session = Depends(get_db)):
    """
    Elimina una factura del sistema con lógica de protección.
    - Se permite borrar si la factura tiene errores críticos (sin CUPS, sin cliente).
    - Se restringe si es una factura válida y enlazada (para evitar fallos de integridad manual).
    """
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # Lógica de protección:
    # Si tiene CUPS y tiene Cliente, la consideramos "valiosa"
    if factura.cups and factura.cliente_id:
        # Solo permitimos borrar si es la única del cliente? O simplemente bloqueamos?
        # Por ahora bloqueamos según pedido usuario: "sino no se puede borrar"
        
        # Check if it has any comparisons (to avoid FK errors)
        comparativas_count = db.query(Comparativa).filter(Comparativa.factura_id == factura_id).count()
        
        if comparativas_count == 0:
             # Si no tiene comparativas, tal vez el usuario se equivocó al subirla 
             # y quiere borrarla aunque tenga CUPS? 
             # El usuario dijo: "sino no se puede borrar"
             raise HTTPException(
                status_code=403, 
                detail="No se puede eliminar una factura válida enlazada a un cliente. Elimine el cliente primero si desea limpiar el sistema."
            )

    # Si llegamos aquí es porque o no tiene CUPS o no tiene Cliente o es un error de OCR
    try:
        # Primero borrar comparativas asociadas (por si acaso)
        db.query(Comparativa).filter(Comparativa.factura_id == factura_id).delete()
        
        db.delete(factura)
        db.commit()
        return {"message": "Factura eliminada correctamente", "id": factura_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")
