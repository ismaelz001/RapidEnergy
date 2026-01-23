from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.conn import get_db
from datetime import datetime
import pandas as pd
import io
import logging

router = APIRouter(prefix="/webhook/comisiones", tags=["comisiones"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_comisiones(file: UploadFile, db: Session = Depends(get_db)):
    """
    Endpoint para subir comisiones masivamente desde archivo CSV o Excel.
    
    Formato esperado:
    - CSV o Excel (.xlsx)
    - Columnas mínimas: tarifa_id, comision_eur, vigente_desde, vigente_hasta (opcional)
    - Fecha formato: YYYY-MM-DD
    
    Comportamiento:
    - Solo INSERT, nunca UPDATE/DELETE (versionado histórico)
    - Validación: tarifa_id debe existir, comision_eur > 0
    """
    logger.info(f"[COMISIONES] Inicio import - archivo: {file.filename}, tamaño: {file.size} bytes")
    
    # Validar tipo de archivo
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo no válido")
    
    file_ext = file.filename.lower().split('.')[-1]
    if file_ext not in ['csv', 'xlsx']:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: {file_ext}. Solo se aceptan CSV o Excel (.xlsx)"
        )
    
    try:
        # Leer archivo a bytes
        contents = await file.read()
        logger.info(f"[COMISIONES] Archivo leído: {len(contents)} bytes")
        
        # Parsear según formato
        if file_ext == 'csv':
            df = pd.read_csv(io.BytesIO(contents))
        else:  # xlsx
            df = pd.read_excel(io.BytesIO(contents))
        
        logger.info(f"[COMISIONES] DataFrame creado: {len(df)} filas, columnas: {list(df.columns)}")
        
        # Validar columnas mínimas requeridas
        required_cols = ['tarifa_id', 'comision_eur', 'vigente_desde']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Faltan columnas requeridas: {missing_cols}. Esperadas: {required_cols}"
            )
        
        # Procesar filas
        importados = 0
        errores = []
        
        for idx, row in df.iterrows():
            fila_num = idx + 2  # +2 porque Excel/CSV empiezan en 1 y hay header
            
            try:
                # Extraer datos
                tarifa_id = int(row['tarifa_id'])
                comision_eur = float(row['comision_eur'])
                vigente_desde_str = str(row['vigente_desde'])
                vigente_hasta_str = str(row.get('vigente_hasta', '')) if 'vigente_hasta' in df.columns else None
                
                # Validación 1: comision_eur > 0
                if comision_eur <= 0:
                    errores.append({
                        "fila": fila_num,
                        "motivo": f"comision_eur debe ser > 0 (recibido: {comision_eur})"
                    })
                    logger.warning(f"[COMISIONES] Fila {fila_num} ERROR: comision_eur inválida")
                    continue
                
                # Validación 2: tarifa_id existe en DB
                tarifa_exists = db.execute(
                    text("SELECT id FROM tarifas WHERE id = :tarifa_id"),
                    {"tarifa_id": tarifa_id}
                ).fetchone()
                
                if not tarifa_exists:
                    errores.append({
                        "fila": fila_num,
                        "motivo": f"tarifa_id {tarifa_id} no existe en la base de datos"
                    })
                    logger.warning(f"[COMISIONES] Fila {fila_num} ERROR: tarifa_id={tarifa_id} no encontrada")
                    continue
                
                # Parsear fechas
                try:
                    vigente_desde = datetime.strptime(vigente_desde_str.split()[0], '%Y-%m-%d').date()
                except:
                    errores.append({
                        "fila": fila_num,
                        "motivo": f"vigente_desde inválida: {vigente_desde_str}. Formato esperado: YYYY-MM-DD"
                    })
                    logger.warning(f"[COMISIONES] Fila {fila_num} ERROR: fecha inválida")
                    continue
                
                vigente_hasta = None
                if vigente_hasta_str and vigente_hasta_str != 'nan' and vigente_hasta_str.strip():
                    try:
                        vigente_hasta = datetime.strptime(vigente_hasta_str.split()[0], '%Y-%m-%d').date()
                    except:
                        # Si vigente_hasta es opcional y falla, lo dejamos NULL
                        vigente_hasta = None
                
                # ⭐ VERSIONADO: Cerrar comisión vigente anterior de esta tarifa
                db.execute(
                    text("""
                        UPDATE comisiones_tarifa
                        SET vigente_hasta = :vigente_desde
                        WHERE tarifa_id = :tarifa_id AND vigente_hasta IS NULL
                    """),
                    {
                        "tarifa_id": tarifa_id,
                        "vigente_desde": vigente_desde
                    }
                )
                logger.info(f"[COMISIONES] Comisión anterior de tarifa_id={tarifa_id} cerrada hasta {vigente_desde}")
                
                # Insertar nueva comisión
                db.execute(
                    text("""
                        INSERT INTO comisiones_tarifa (tarifa_id, comision_eur, vigente_desde, vigente_hasta)
                        VALUES (:tarifa_id, :comision_eur, :vigente_desde, :vigente_hasta)
                    """),
                    {
                        "tarifa_id": tarifa_id,
                        "comision_eur": comision_eur,
                        "vigente_desde": vigente_desde,
                        "vigente_hasta": vigente_hasta
                    }
                )
                
                importados += 1
                logger.info(f"[COMISIONES] Fila {fila_num} OK - tarifa_id={tarifa_id}, comision={comision_eur}€")
                
            except ValueError as e:
                errores.append({
                    "fila": fila_num,
                    "motivo": f"Error de conversión de tipos: {str(e)}"
                })
                logger.error(f"[COMISIONES] Fila {fila_num} ERROR: {str(e)}")
            except Exception as e:
                errores.append({
                    "fila": fila_num,
                    "motivo": f"Error inesperado: {str(e)}"
                })
                logger.error(f"[COMISIONES] Fila {fila_num} ERROR: {str(e)}", exc_info=True)
        
        # Commit solo si hubo al menos 1 importación exitosa
        if importados > 0:
            db.commit()
            logger.info(f"[COMISIONES] Commit exitoso: {importados} filas importadas")
        else:
            db.rollback()
            logger.warning(f"[COMISIONES] Rollback: 0 filas importadas")
        
        return {
            "status": "ok" if importados > 0 else "warning",
            "importados": importados,
            "errores": errores,
            "total_filas": len(df)
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Error al parsear archivo: {str(e)}")
    except Exception as e:
        logger.error(f"[COMISIONES] Error general: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al procesar archivo: {str(e)}")


@router.get("/")
async def listar_comisiones(db: Session = Depends(get_db)):
    """
    Endpoint auxiliar para listar comisiones vigentes (debugging)
    """
    result = db.execute(
        text("""
            SELECT 
                ct.id,
                ct.tarifa_id,
                t.provider,
                t.plan_name,
                ct.comision_eur,
                ct.vigente_desde,
                ct.vigente_hasta
            FROM comisiones_tarifa ct
            JOIN tarifas t ON ct.tarifa_id = t.id
            WHERE ct.vigente_hasta IS NULL OR ct.vigente_hasta >= CURRENT_DATE
            ORDER BY t.provider, t.plan_name, ct.vigente_desde DESC
            LIMIT 50
        """)
    ).fetchall()
    
    comisiones = []
    for row in result:
        comisiones.append({
            "id": row[0],
            "tarifa_id": row[1],
            "provider": row[2],
            "plan_name": row[3],
            "comision_eur": float(row[4]) if row[4] else 0.0,
            "vigente_desde": str(row[5]) if row[5] else None,
            "vigente_hasta": str(row[6]) if row[6] else None
        })
    
    return {
        "status": "ok",
        "count": len(comisiones),
        "comisiones": comisiones
    }
