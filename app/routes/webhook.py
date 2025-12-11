from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session
from app.db.conn import get_db
from app.db.models import Factura

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post("/upload")
async def upload_factura(file: UploadFile, db: Session = Depends(get_db)):
    # 1. Leer el archivo
    file_bytes = await file.read()

    # 2. OCR y extracción de datos
    from app.services.ocr import extract_data_from_pdf
    ocr_data = extract_data_from_pdf(file_bytes)

    # 3. Crear registro en BD con datos extraídos
    nueva_factura = Factura(
        filename=file.filename,
        cups=ocr_data["cups"],
        consumo_kwh=ocr_data["consumo_kwh"],
        importe=ocr_data["importe"],
        fecha=ocr_data["fecha"],
        raw_data=ocr_data["raw_text"]
    )
    
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    return {
        "id": nueva_factura.id,
        "filename": nueva_factura.filename,
        "ocr_preview": ocr_data,
        "message": "Factura procesada y guardada correctamente"
    }

@router.get("/facturas")
def list_facturas(db: Session = Depends(get_db)):
    facturas = db.query(Factura).all()
    return facturas
