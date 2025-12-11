from fastapi import APIRouter, UploadFile

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post("/upload")
async def upload_factura(file: UploadFile):
    # En el MVP, simplemente devolvemos que la factura llega bien
    return {
        "filename": file.filename,
        "message": "Factura recibida correctamente (MVP)"
    }
