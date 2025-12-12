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

    # 3. Lógica Upsert Cliente
    from app.db.models import Cliente
    cups_extraido = ocr_data.get("cups")
    cliente_db = None

    if cups_extraido:
        # Buscar cliente existente por CUPS
        cliente_db = db.query(Cliente).filter(Cliente.cups == cups_extraido).first()
        if not cliente_db:
            # Crear nuevo cliente si no existe
            cliente_db = Cliente(
                cups=cups_extraido,
                origen="factura_upload",
                estado="lead"
            )
            db.add(cliente_db)
            db.commit()
            db.refresh(cliente_db)
    else:
        # Caso sin CUPS: Crear cliente 'lead' sin CUPS (opcional, según reglas de negocio)
        # Por ahora creamos un cliente huérfano para no perder el lead
        cliente_db = Cliente(
            origen="factura_upload_no_cups",
            estado="lead"
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
        cliente_id=cliente_db.id if cliente_db else None
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
