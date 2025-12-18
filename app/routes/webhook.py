from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.conn import get_db
from app.db.models import Factura
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/webhook", tags=["webhook"])


class FacturaUpdate(BaseModel):
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


REQUIRED_FACTURA_FIELDS = [
    "potencia_p1_kw",
    "potencia_p2_kw",
    "consumo_p1_kwh",
    "consumo_p2_kwh",
    "consumo_p3_kwh",
    "consumo_p4_kwh",
    "consumo_p5_kwh",
    "consumo_p6_kwh",
    "bono_social",
    "servicios_vinculados",
    "alquiler_contador",
    "impuesto_electrico",
    "iva",
    "total_factura",
]


def validate_factura_completitud(factura: Factura):
    """
    Valida que una factura tenga todos los campos energéticos críticos.
    Devuelve (is_valid: bool, errors: dict[field, str]).
    """
    errors = {}
    for field in REQUIRED_FACTURA_FIELDS:
        val = getattr(factura, field, None)
        # Para booleanos, solo consideramos ausente si es None (False es válido)
        if isinstance(val, bool):
            if val is None:
                errors[field] = "Campo obligatorio ausente"
        else:
            if val is None:
                errors[field] = "Campo obligatorio ausente"
    return len(errors) == 0, errors


@router.post("/upload")
async def upload_factura(file: UploadFile, db: Session = Depends(get_db)):
    # 1. Leer el archivo
    file_bytes = await file.read()
    
    # --- DEDUPLICACION POR HASH ---
    import hashlib
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    existing_by_hash = db.query(Factura).filter(Factura.file_hash == file_hash).first()
    if existing_by_hash:
        return {
            "status": "duplicate",
            "message": "Esta factura ya fue subida (detectado por hash).",
            "redirect_url": f"/facturas/{existing_by_hash.id}",
            "existing_factura": { # Keeping this for debug/advanced use but main UX uses top level keys
                 "id": existing_by_hash.id,
                 "cups": existing_by_hash.cups
            }
        }

    # 2. OCR y extraccion de datos
    from app.services.ocr import extract_data_from_pdf
    ocr_data = extract_data_from_pdf(file_bytes)
    
    # --- DEDUPLICACION POR NUMERO FACTURA ---
    cups_extraido = ocr_data.get("cups")
    num_factura_ocr = ocr_data.get("numero_factura")
    
    if cups_extraido and num_factura_ocr:
        existing_by_num = (
            db.query(Factura)
            .filter(Factura.cups == cups_extraido)
            .filter(Factura.numero_factura == num_factura_ocr)
            .first()
        )
        if existing_by_num:
            return {
                "status": "duplicate",
                "message": f"Esta factura ya existe para el CUPS {cups_extraido} con número {num_factura_ocr}.",
                "redirect_url": f"/facturas/{existing_by_num.id}"
            }

    # 3. Logica Upsert Cliente
    from app.db.models import Cliente

    # Datos personales del OCR (solo para clientes nuevos)
    nombre_ocr = ocr_data.get("titular")
    email_ocr = ocr_data.get("email")
    dni_ocr = ocr_data.get("dni")
    direccion_ocr = ocr_data.get("direccion")
    telefono_ocr = ocr_data.get("telefono")
    provincia_ocr = ocr_data.get("provincia") # New field
    cliente_db = None

    # Fallback dedupe: CUPS + filename (legacy)
    if cups_extraido:
        existing_factura = (
            db.query(Factura)
            .filter(Factura.cups == cups_extraido)
            .filter(Factura.filename == file.filename)
            .first()
        )
        if existing_factura:
             return {
                "status": "duplicate",
                "message": "Factura ya existente para este CUPS y nombre de archivo.",
                "redirect_url": f"/facturas/{existing_factura.id}"
            }

    if cups_extraido:
        # Buscar cliente existente por CUPS
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
    nueva_factura = Factura(
        filename=file.filename,
        cups=ocr_data.get("cups"),
        consumo_kwh=ocr_data.get("consumo_kwh"),
        importe=ocr_data.get("importe"),
        fecha=ocr_data.get("fecha"),
        fecha_inicio=ocr_data.get("fecha_inicio_consumo"),
        fecha_fin=ocr_data.get("fecha_fin_consumo"),
        raw_data=ocr_data.get("raw_text"),
        cliente_id=cliente_db.id if cliente_db else None,
        
        # Deduplicacion
        file_hash=file_hash,
        numero_factura=ocr_data.get("numero_factura"),
        
        # Nuevos campos mapeados para persistencia completa
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
        total_factura=ocr_data.get("total_factura"),
    )

    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    return {
        "id": nueva_factura.id,
        "filename": nueva_factura.filename,
        "ocr_preview": ocr_data,
        "message": "Factura procesada y guardada correctamente",
    }


@router.get("/facturas")
def list_facturas(db: Session = Depends(get_db)):
    facturas = db.query(Factura).all()
    return facturas


@router.get("/facturas/{factura_id}")
def get_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
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
        setattr(factura, key, value)

    # Validacion de completitud
    es_valida, errors = validate_factura_completitud(factura)
    factura.estado_factura = "lista_para_comparar" if es_valida else "pendiente_datos"

    db.commit()
    db.refresh(factura)

    if not es_valida:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Faltan campos obligatorios para comparar",
                "errors": errors,
                "estado_factura": factura.estado_factura,
            },
        )

    return factura


@router.post("/comparar/facturas/{factura_id}")
def comparar_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    es_valida, errors = validate_factura_completitud(factura)
    if not es_valida or factura.estado_factura != "lista_para_comparar":
        raise HTTPException(
            status_code=400,
            detail={
                "message": "La factura no está lista para comparar",
                "estado_factura": factura.estado_factura,
                "errors": errors,
            },
        )

    # Placeholder hasta implementar comparador real
    return {"message": "Comparación no implementada todavía", "estado_factura": factura.estado_factura}
