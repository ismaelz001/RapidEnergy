from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session
from app.db.conn import get_db
from app.db.models import Factura

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post("/upload")
async def upload_factura(file: UploadFile, db: Session = Depends(get_db)):
    # Crear registro en BD
    nueva_factura = Factura(
        filename=file.filename,
        # De momento campos vacíos hasta tener OCR
        cups=None,
        consumo_kwh=None,
        importe=None
    )
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    return {
        "id": nueva_factura.id,
        "filename": nueva_factura.filename,
        "message": "Factura guardada correctamente en BD"
    }

@router.get("/facturas")
def list_facturas(db: Session = Depends(get_db)):
    facturas = db.query(Factura).all()
    return facturas
