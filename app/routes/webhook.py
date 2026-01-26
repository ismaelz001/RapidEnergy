from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.db.conn import get_db
from app.db.models import Factura, Cliente, Comparativa
from app.exceptions import DomainError
from pydantic import BaseModel
from typing import Optional
import json
import logging
import inspect


# Logger para el módulo
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


# ════════════════════════════════════════════════════════════
# HELPERS SEGUROS PARA PDF
# ════════════════════════════════════════════════════════════

def fmt_num(value, decimals=2, suffix="", fallback="No disponible"):
    """
    Formatea números de forma segura para el PDF.
    Si value es None/NaN, devuelve fallback.
    
    IMPORTANTE: Nunca devolver "—", siempre mensaje explicativo.
    """
    try:
        if value is None:
            return fallback
        num = float(value)
        if num != num:  # NaN
            return fallback
        s = f"{num:.{decimals}f}"
        return f"{s} {suffix}".strip() if suffix else s
    except (ValueError, TypeError):
        return fallback


def calcular_precio_medio_estructural(factura):
    """
    Calcula precio medio estructural SOLO con datos reales.
    
    Fórmula: (E_actual + P_actual) / kWh_total
    
    Si falta CUALQUIER dato, devuelve None.
    NO inventa, NO estima, NO reconstruye.
    
    Returns:
        float | None
    """
    # 1. Obtener E_actual y P_actual (solo si existen)
    e_actual = getattr(factura, 'coste_energia_actual', None)
    p_actual = getattr(factura, 'coste_potencia_actual', None)
    
    if e_actual is None or p_actual is None:
        return None  # Faltan datos baseline, no inventar
    
    # 2. Obtener kWh totales
    kwh_total = getattr(factura, 'consumo_kwh', None)
    
    if not kwh_total or kwh_total <= 0:
        # Fallback: sumar periodos
        consumos = [
            getattr(factura, f'consumo_p{i}_kwh', 0) or 0 
            for i in range(1, 7)
        ]
        kwh_total = sum(consumos)
    
    # 3. Validar divisor
    if not kwh_total or kwh_total <= 0:
        return None  # No hay consumo válido
    
    # 4. Calcular de forma segura
    try:
        precio = (float(e_actual) + float(p_actual)) / float(kwh_total)
        return precio
    except (ValueError, TypeError, ZeroDivisionError):
        return None


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
    iva_porcentaje: Optional[float] = None
    total_factura: Optional[float] = None
    coste_energia_actual: Optional[float] = None
    coste_potencia_actual: Optional[float] = None
    estado_factura: Optional[str] = None
    cups: Optional[str] = None
    numero_factura: Optional[str] = None
    periodo_dias: Optional[int] = None


class OfferSelection(BaseModel):
    """Modelo para recibir la oferta seleccionada por el usuario."""
    provider: str
    plan_name: str
    tarifa_id: Optional[int] = None
    estimated_total: float
    saving_amount: float
    saving_percent: float
    ahorro_estructural: Optional[float] = None
    precio_medio_estructural: Optional[float] = None
    coste_diario_estructural: Optional[float] = None
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
    "periodo_dias",
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


def _normalize_iva_porcentaje(value):
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    # Normalizar a decimal (ej: 0.21) por consistencia interna
    return parsed / 100 if parsed > 1 else parsed


def _normalize_periodo_dias(value):
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


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
        # ⭐ BLOQUE 1 CRM: Buscar cliente existente por CUPS (YA NORMALIZADO)
        cliente_db = db.query(Cliente).filter(Cliente.cups == cups_extraido).first()
        if cliente_db:
            logger.info(f"[DEDUPE] Cliente encontrado por CUPS={cups_extraido}, cliente_id={cliente_db.id}")
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
                comercial_id=None  # ⭐ BLOQUE 1 CRM: Asignar cuando haya auth
            )
            db.add(cliente_db)
            db.commit()
            db.refresh(cliente_db)
            logger.info(f"[DEDUPE] Cliente nuevo creado: cliente_id={cliente_db.id}, CUPS={cups_extraido}")
            
            # TODO: BLOQUE 1 CRM - DEDUPE SECUNDARIA (FASE 2)
            # Buscar clientes similares por nombre/dirección con ILIKE:
            # similar = db.query(Cliente).filter(Cliente.nombre.ilike(f"%{nombre_ocr}%")).first()
            # Si hay match, devolver suggested_cliente en response para que frontend decida
    else:
        # Caso sin CUPS: Crear cliente 'lead' sin CUPS
        cliente_db = Cliente(
            origen="factura_upload_no_cups",
            estado="lead",
            comercial_id=None  # ⭐ BLOQUE 1 CRM: Sin comercial
        )
        db.add(cliente_db)
        db.commit()
        db.refresh(cliente_db)
        logger.info(f"[DEDUPE] Cliente sin CUPS creado: cliente_id={cliente_db.id}")
        
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
        
        # ⭐ FIX P0-1: Mapear periodo_dias desde dias_facturados
        periodo_dias=ocr_data.get("dias_facturados"),
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
    logger.info(
        "🔍 [AUDIT STEP2] Payload recibido factura_id=%s: periodo_dias=%s, iva_porc=%s, iva_eur=%s, iee_eur=%s, alquiler=%s",
        factura_id,
        update_data.get("periodo_dias"),
        update_data.get("iva_porcentaje"),
        update_data.get("iva"),
        update_data.get("impuesto_electrico"),
        update_data.get("alquiler_contador")
    )
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
        if key == "iva_porcentaje":
            value = _normalize_iva_porcentaje(value)
        if key == "periodo_dias":
            value = _normalize_periodo_dias(value)
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

    logger.info(
        "✅ [AUDIT STEP2] Guardado final factura_id=%s: periodo_dias=%s, iva_porc=%s, iva_eur=%s, iee_eur=%s, estado=%s",
        factura.id,
        factura.periodo_dias,
        factura.iva_porcentaje,
        factura.iva,
        factura.impuesto_electrico,
        factura.estado_factura
    )

    return {
        "factura": factura,
        "is_valid": es_valida,
        "errors": errors,
        "missing_fields": list(errors.keys()),
        "estado_factura": factura.estado_factura,
    }


@router.put("/facturas/{factura_id}/validar")
def validar_comercialmente(
    factura_id: int, 
    request_body: dict,
    db: Session = Depends(get_db)
):
    """
    STEP 2: Validación Comercial
    Aplica ajustes comerciales (Bono Social, descuentos, servicios) antes de comparar.
    
    Body:
    {
        "ajustes_comerciales": {
            "bono_social": {"activo": true, "descuento_estimado": 12.50, ...},
            "descuento_comercial": {"importe": 4.50, "descripcion": "...", ...},
            ...
        },
        "modo": "asesor" | "cliente"
    }
    
    Returns:
    {
        "factura_id": int,
        "base_factura": {...},
        "ajustes_comerciales": {...},
        "totales_calculados": {
            "total_original": float,
            "total_descuentos_excluidos": float,
            "total_ajustado_comparable": float
        },
        "warnings": [str],
        "ready_to_compare": bool
    }
    """
    from app.schemas.validacion import ValidacionComercialRequest, AjustesComerciales
    from app.services.validacion_comercial import validar_factura_comercialmente
    
    # Obtener factura
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Parsear request
    try:
        # Intentar construir desde el request body
        if "ajustes_comerciales" in request_body:
            ajustes = AjustesComerciales(**request_body["ajustes_comerciales"])
        else:
            # Si viene vacío, usar defaults
            ajustes = AjustesComerciales()
        
        modo = request_body.get("modo", "asesor")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parseando ajustes: {str(e)}")
    
    # Validar comercialmente
    response, warnings = validar_factura_comercialmente(factura, ajustes, modo)
    
    # Persistir en la factura
    try:
        factura.ajustes_comerciales_json = response.ajustes_comerciales.model_dump_json()
        factura.total_ajustado = response.totales_calculados.total_ajustado_comparable
        factura.validado_step2 = True
        
        # Si está ready, actualizar estado
        if response.ready_to_compare:
            factura.estado_factura = "lista_para_comparar"
        
        db.commit()
        db.refresh(factura)
        
        logger.info(
            f"[STEP2] Factura {factura_id} validada: "
            f"total_original={response.totales_calculados.total_original:.2f} → "
            f"total_ajustado={response.totales_calculados.total_ajustado_comparable:.2f}"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"[STEP2] Error persistiendo validación: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error guardando validación: {str(e)}")
    
    return response.model_dump()


@router.post("/comparar/facturas/{factura_id}")
def comparar_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # ⭐ CAMBIO 3: VALIDACIÓN PREVIA SEGÚN ATR
    atr = getattr(factura, "atr", None)
    if not atr or not atr.strip():
        # Inferir ATR por potencia si no hay OCR
        potencia_p1 = factura.potencia_p1_kw or 0.0
        atr = "3.0TD" if potencia_p1 >= 15 else "2.0TD"
    else:
        atr = atr.strip().upper()
    
    # Validación específica por ATR
    if atr == "3.0TD":
        # Para 3.0TD: exigir consumos P1-P6 + potencias P1-P2
        required_consumos = ["consumo_p1_kwh", "consumo_p2_kwh", "consumo_p3_kwh",
                              "consumo_p4_kwh", "consumo_p5_kwh", "consumo_p6_kwh"]
        required_potencias = ["potencia_p1_kw", "potencia_p2_kw"]
        
        missing = []
        for field in required_consumos + required_potencias:
            val = getattr(factura, field, None)
            if val is None:
                missing.append(field)
        
        if missing:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Factura 3.0TD incompleta: faltan {', '.join(missing)}",
                    "atr": "3.0TD",
                    "missing_fields": missing,
                }
            )
    else:
        # Para 2.0TD: usar validación existente
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
    factura.selected_offer_json = json.dumps(offer_dict, ensure_ascii=False)  # Mantener backward compat
    factura.estado_factura = "oferta_seleccionada"
    
    # ⭐ BLOQUE 1 CRM: Persistir selección con FK
    # Buscar el ID real en ofertas_calculadas (no confundir con tarifa_id)
    from app.db.models import OfertaCalculada, Comparativa
    
    tarifa_id_seleccionada = offer_dict.get("tarifa_id")
    
    # Obtener la última comparativa de esta factura
    ultima_comparativa = (
        db.query(Comparativa)
        .filter(Comparativa.factura_id == factura_id)
        .order_by(Comparativa.created_at.desc())
        .first()
    )
    
    if ultima_comparativa and tarifa_id_seleccionada:
        # Buscar la oferta calculada correspondiente
        oferta_calculada = (
            db.query(OfertaCalculada)
            .filter(OfertaCalculada.comparativa_id == ultima_comparativa.id)
            .filter(OfertaCalculada.tarifa_id == tarifa_id_seleccionada)
            .first()
        )
        
        if oferta_calculada:
            factura.selected_oferta_id = oferta_calculada.id  # ID real de ofertas_calculadas
            logger.info(f"[SELECT] Factura {factura_id} → oferta_calculada.id={oferta_calculada.id} (tarifa_id={tarifa_id_seleccionada})")
        else:
            logger.warning(f"[SELECT] No se encontró oferta_calculada para tarifa_id={tarifa_id_seleccionada}")
            factura.selected_oferta_id = None
    else:
        factura.selected_oferta_id = None
    
    factura.selected_at = func.now()
    factura.selected_by_user_id = None  # TODO: Asignar current_user.id cuando haya auth
    
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
    PDF con estructura EXACTA: Tabla 1, Tabla 2, Tabla 3 + modelo Patricia Vázquez
    """
    from fastapi.responses import StreamingResponse
    from app.services.pdf_generator import generar_pdf_presupuesto
    
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if not factura.selected_offer_json:
        raise HTTPException(status_code=400, detail="No hay una oferta seleccionada.")
    
    try:
        selected_offer = json.loads(factura.selected_offer_json)
    except:
        raise HTTPException(status_code=500, detail="Error al leer la oferta seleccionada")
    
    try:
        # Generar PDF usando el servicio especializado
        buffer = generar_pdf_presupuesto(factura, selected_offer, db)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=presupuesto_energyluz_{factura_id}.pdf",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"Error generando PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF: {str(e)}")


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
