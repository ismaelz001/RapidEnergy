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


@router.post("/upload")
async def upload_factura(file: UploadFile, db: Session = Depends(get_db)):
    # 1. Leer el archivo
    file_bytes = await file.read()

    # 2. OCR y extraccion de datos
    from app.services.ocr import extract_data_from_pdf

    ocr_data = extract_data_from_pdf(file_bytes)

    # 3. Logica Upsert Cliente
    from app.db.models import Cliente

    cups_extraido = ocr_data.get("cups")
    nombre_ocr = ocr_data.get("nombre") or ocr_data.get("titular")
    email_ocr = ocr_data.get("email")
    dni_ocr = ocr_data.get("dni")
    direccion_ocr = ocr_data.get("direccion")
    telefono_ocr = ocr_data.get("telefono")
    cliente_db = None

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
            nombre=nombre_ocr,
            email=email_ocr,
            dni=dni_ocr,
            direccion=direccion_ocr,
            telefono=telefono_ocr,
            origen="factura_upload_no_cups",
            estado="lead",
        )
        db.add(cliente_db)
        db.commit()
        db.refresh(cliente_db)

    # 4. Crear factura vinculada
    nueva_factura = Factura(
        filename=file.filename,
        cups=ocr_data["cups"],
        consumo_kwh=ocr_data["consumo_kwh"],
        importe=ocr_data["importe"],
        fecha=ocr_data["fecha"],
        raw_data=ocr_data["raw_text"],
        cliente_id=cliente_db.id if cliente_db else None,
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

    db.commit()
    db.refresh(factura)
    return factura
