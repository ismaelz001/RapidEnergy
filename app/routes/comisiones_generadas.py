"""
API de Comisiones Generadas
Gestión completa del ciclo de vida de comisiones: generar, listar, validar, pagar
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.conn import get_db
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
import logging

router = APIRouter(prefix="/api/comisiones", tags=["comisiones-generadas"])
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class ComisionGeneradaResponse(BaseModel):
    id: int
    factura_id: int
    cliente_id: int
    cliente_nombre: Optional[str]
    asesor_id: int
    asesor_nombre: Optional[str]
    comision_total_eur: float
    estado: str
    fecha_prevista_pago: Optional[date]
    fecha_pago: Optional[date]
    created_at: datetime
    # Datos adicionales
    tarifa_nombre: Optional[str]
    comercializadora: Optional[str]
    ahorro_anual: Optional[float]


class RepartoComisionResponse(BaseModel):
    id: int
    tipo_destinatario: str
    importe_eur: float
    porcentaje: Optional[float]
    estado_pago: str
    destinatario_nombre: Optional[str]
    destinatario_email: Optional[str]


class ComisionDetalleResponse(ComisionGeneradaResponse):
    repartos: List[RepartoComisionResponse] = []
    cups: Optional[str]


class PagarComisionRequest(BaseModel):
    fecha_pago: Optional[date] = Field(default=None, description="Fecha de pago (default: hoy)")


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/generar/{factura_id}")
def generar_comision_desde_factura(factura_id: int, db: Session = Depends(get_db)):
    """
    Genera registro de comisión cuando se selecciona una oferta
    
    Trigger automático o manual cuando:
    - facturas.selected_oferta_id se actualiza
    
    Comportamiento:
    - Extrae comision_eur de ofertas_calculadas
    - Crea registro en comisiones_generadas con estado='pendiente'
    - Fecha prevista pago = hoy + 30 días
    - Evita duplicados (ON CONFLICT DO NOTHING)
    """
    
    try:
        # Validar que la factura tenga oferta seleccionada
        query_validar = text("""
            SELECT 
                f.id,
                f.cliente_id,
                f.selected_oferta_id,
                c.comercial_id,
                c.company_id
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.id = :factura_id
              AND f.selected_oferta_id IS NOT NULL
        """)
        
        factura_data = db.execute(query_validar, {"factura_id": factura_id}).fetchone()
        
        if not factura_data:
            raise HTTPException(
                status_code=400,
                detail="Factura no encontrada o no tiene oferta seleccionada"
            )
        
        _, cliente_id, oferta_id, asesor_id, company_id = factura_data
        
        if not asesor_id:
            raise HTTPException(
                status_code=400,
                detail="Cliente no tiene asesor asignado (comercial_id es NULL)"
            )
        
        # Extraer datos de la oferta calculada
        query_oferta = text("""
            SELECT 
                tarifa_id,
                comision_eur,
                comision_source
            FROM ofertas_calculadas
            WHERE id = :oferta_id
        """)
        
        oferta_data = db.execute(query_oferta, {"oferta_id": oferta_id}).fetchone()
        
        if not oferta_data:
            raise HTTPException(status_code=404, detail="Oferta calculada no encontrada")
        
        tarifa_id, comision_eur, comision_source = oferta_data
        
        # Verificar si ya existe comisión para esta factura
        query_existe = text("""
            SELECT id FROM comisiones_generadas WHERE factura_id = :factura_id
        """)
        
        existe = db.execute(query_existe, {"factura_id": factura_id}).fetchone()
        
        if existe:
            logger.warning(f"[COMISION] Factura {factura_id} ya tiene comisión generada (id={existe[0]})")
            return {
                "status": "exists",
                "message": "Comisión ya generada previamente",
                "comision_id": existe[0]
            }
        
        # Calcular fecha prevista pago (hoy + 30 días)
        fecha_prevista = datetime.now().date()
        from datetime import timedelta
        fecha_prevista += timedelta(days=30)
        
        # Insertar comisión generada
        query_insert = text("""
            INSERT INTO comisiones_generadas (
                factura_id,
                cliente_id,
                company_id,
                asesor_id,
                oferta_id,
                tarifa_id,
                comision_total_eur,
                comision_source,
                estado,
                fecha_prevista_pago
            )
            VALUES (
                :factura_id,
                :cliente_id,
                :company_id,
                :asesor_id,
                :oferta_id,
                :tarifa_id,
                :comision_eur,
                :comision_source,
                'pendiente',
                :fecha_prevista
            )
            RETURNING id
        """)
        
        result = db.execute(query_insert, {
            "factura_id": factura_id,
            "cliente_id": cliente_id,
            "company_id": company_id,
            "asesor_id": asesor_id,
            "oferta_id": oferta_id,
            "tarifa_id": tarifa_id,
            "comision_eur": float(comision_eur),
            "comision_source": comision_source,
            "fecha_prevista": fecha_prevista
        })
        
        comision_id = result.scalar()
        
        db.commit()
        
        logger.info(f"[COMISION] ✅ Generada comision_id={comision_id} para factura_id={factura_id}, €{comision_eur}")
        
        return {
            "status": "created",
            "message": "Comisión generada correctamente",
            "comision_id": comision_id,
            "comision_eur": float(comision_eur),
            "estado": "pendiente",
            "fecha_prevista_pago": fecha_prevista.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[COMISION] Error generando comisión para factura {factura_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generando comisión: {str(e)}")


@router.get("/", response_model=List[ComisionGeneradaResponse])
def listar_comisiones(
    estado: Optional[str] = Query(None, description="Filtrar por estado: pendiente, validada, pagada, anulada"),
    asesor_id: Optional[int] = Query(None, description="Filtrar por asesor"),
    company_id: Optional[int] = Query(None, description="Filtrar por company (multi-tenant)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Listar comisiones con filtros opcionales
    """
    
    try:
        # Query base con joins
        query_base = """
            SELECT 
                cg.id,
                cg.factura_id,
                cg.cliente_id,
                c.nombre as cliente_nombre,
                cg.asesor_id,
                u.name as asesor_nombre,
                cg.comision_total_eur,
                cg.estado,
                cg.fecha_prevista_pago,
                cg.fecha_pago,
                cg.created_at,
                t.nombre as tarifa_nombre,
                t.comercializadora,
                oc.ahorro_anual
            FROM comisiones_generadas cg
            JOIN clientes c ON cg.cliente_id = c.id
            JOIN users u ON cg.asesor_id = u.id
            JOIN tarifas t ON cg.tarifa_id = t.id
            JOIN ofertas_calculadas oc ON cg.oferta_id = oc.id
            WHERE 1=1
        """
        
        params = {}
        
        # Filtros dinámicos
        if estado:
            query_base += " AND cg.estado = :estado"
            params["estado"] = estado
        
        if asesor_id:
            query_base += " AND cg.asesor_id = :asesor_id"
            params["asesor_id"] = asesor_id
        
        if company_id:
            query_base += " AND cg.company_id = :company_id"
            params["company_id"] = company_id
        
        query_base += " ORDER BY cg.created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = skip
        
        rows = db.execute(text(query_base), params).fetchall()
        
        comisiones = []
        for row in rows:
            comisiones.append(ComisionGeneradaResponse(
                id=row[0],
                factura_id=row[1],
                cliente_id=row[2],
                cliente_nombre=row[3],
                asesor_id=row[4],
                asesor_nombre=row[5],
                comision_total_eur=float(row[6]),
                estado=row[7],
                fecha_prevista_pago=row[8],
                fecha_pago=row[9],
                created_at=row[10],
                tarifa_nombre=row[11],
                comercializadora=row[12],
                ahorro_anual=float(row[13]) if row[13] else None
            ))
        
        return comisiones
        
    except Exception as e:
        logger.error(f"[COMISION] Error listando comisiones: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{comision_id}", response_model=ComisionDetalleResponse)
def obtener_detalle_comision(comision_id: int, db: Session = Depends(get_db)):
    """
    Detalle completo de comisión incluyendo repartos
    """
    
    try:
        # Datos principales
        query_main = text("""
            SELECT 
                cg.id,
                cg.factura_id,
                cg.cliente_id,
                c.nombre as cliente_nombre,
                cg.asesor_id,
                u.name as asesor_nombre,
                cg.comision_total_eur,
                cg.estado,
                cg.fecha_prevista_pago,
                cg.fecha_pago,
                cg.created_at,
                t.nombre as tarifa_nombre,
                t.comercializadora,
                oc.ahorro_anual,
                f.cups
            FROM comisiones_generadas cg
            JOIN clientes c ON cg.cliente_id = c.id
            JOIN users u ON cg.asesor_id = u.id
            JOIN tarifas t ON cg.tarifa_id = t.id
            JOIN facturas f ON cg.factura_id = f.id
            JOIN ofertas_calculadas oc ON cg.oferta_id = oc.id
            WHERE cg.id = :comision_id
        """)
        
        row = db.execute(query_main, {"comision_id": comision_id}).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Comisión no encontrada")
        
        comision = ComisionDetalleResponse(
            id=row[0],
            factura_id=row[1],
            cliente_id=row[2],
            cliente_nombre=row[3],
            asesor_id=row[4],
            asesor_nombre=row[5],
            comision_total_eur=float(row[6]),
            estado=row[7],
            fecha_prevista_pago=row[8],
            fecha_pago=row[9],
            created_at=row[10],
            tarifa_nombre=row[11],
            comercializadora=row[12],
            ahorro_anual=float(row[13]) if row[13] else None,
            cups=row[14]
        )
        
        # Repartos (si existen)
        query_repartos = text("""
            SELECT 
                rc.id,
                rc.tipo_destinatario,
                rc.importe_eur,
                rc.porcentaje,
                rc.estado_pago,
                COALESCE(u.name, col.nombre) as destinatario_nombre,
                COALESCE(u.email, col.email) as destinatario_email
            FROM repartos_comision rc
            LEFT JOIN users u ON rc.user_id = u.id
            LEFT JOIN colaboradores col ON rc.colaborador_id = col.id
            WHERE rc.comision_id = :comision_id
            ORDER BY rc.importe_eur DESC
        """)
        
        rows_repartos = db.execute(query_repartos, {"comision_id": comision_id}).fetchall()
        
        for row_rep in rows_repartos:
            comision.repartos.append(RepartoComisionResponse(
                id=row_rep[0],
                tipo_destinatario=row_rep[1],
                importe_eur=float(row_rep[2]),
                porcentaje=float(row_rep[3]) if row_rep[3] else None,
                estado_pago=row_rep[4],
                destinatario_nombre=row_rep[5],
                destinatario_email=row_rep[6]
            ))
        
        return comision
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMISION] Error obteniendo detalle {comision_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{comision_id}/validar")
def validar_comision(comision_id: int, db: Session = Depends(get_db)):
    """
    Validar comisión (estado pendiente → validada)
    Requiere permisos de CEO/DEV
    """
    
    try:
        query = text("""
            UPDATE comisiones_generadas
            SET estado = 'validada',
                updated_at = NOW()
            WHERE id = :comision_id
              AND estado = 'pendiente'
            RETURNING id, estado
        """)
        
        result = db.execute(query, {"comision_id": comision_id}).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=400,
                detail="Comisión no encontrada o no está en estado 'pendiente'"
            )
        
        db.commit()
        
        logger.info(f"[COMISION] ✅ Comisión {comision_id} validada")
        
        return {
            "status": "ok",
            "message": "Comisión validada correctamente",
            "comision_id": result[0],
            "estado": result[1]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[COMISION] Error validando {comision_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{comision_id}/pagar")
def marcar_comision_pagada(
    comision_id: int,
    payload: PagarComisionRequest,
    db: Session = Depends(get_db)
):
    """
    Marcar comisión como pagada (estado validada → pagada)
    Requiere permisos de CEO/DEV
    """
    
    try:
        fecha_pago = payload.fecha_pago or datetime.now().date()
        
        query = text("""
            UPDATE comisiones_generadas
            SET estado = 'pagada',
                fecha_pago = :fecha_pago,
                updated_at = NOW()
            WHERE id = :comision_id
              AND estado = 'validada'
            RETURNING id, estado, fecha_pago
        """)
        
        result = db.execute(query, {
            "comision_id": comision_id,
            "fecha_pago": fecha_pago
        }).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=400,
                detail="Comisión no encontrada o no está en estado 'validada'"
            )
        
        db.commit()
        
        logger.info(f"[COMISION] ✅ Comisión {comision_id} marcada como pagada (fecha: {fecha_pago})")
        
        return {
            "status": "ok",
            "message": "Comisión marcada como pagada",
            "comision_id": result[0],
            "estado": result[1],
            "fecha_pago": result[2].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[COMISION] Error marcando pago {comision_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{comision_id}/anular")
def anular_comision(comision_id: int, db: Session = Depends(get_db)):
    """
    Anular comisión (cualquier estado → anulada)
    Requiere permisos de CEO/DEV
    """
    
    try:
        query = text("""
            UPDATE comisiones_generadas
            SET estado = 'anulada',
                updated_at = NOW()
            WHERE id = :comision_id
              AND estado != 'pagada'
            RETURNING id, estado
        """)
        
        result = db.execute(query, {"comision_id": comision_id}).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=400,
                detail="Comisión no encontrada o ya está pagada (no se puede anular)"
            )
        
        db.commit()
        
        logger.info(f"[COMISION] ⚠️ Comisión {comision_id} anulada")
        
        return {
            "status": "ok",
            "message": "Comisión anulada",
            "comision_id": result[0],
            "estado": result[1]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[COMISION] Error anulando {comision_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{comision_id}", response_model=ComisionDetalleResponse)
def obtener_detalle_comision(comision_id: int, db: Session = Depends(get_db)):
    """
    Obtener detalle completo de una comisión incluyendo repartos
    """
    
    try:
        # Consulta principal con datos de comisión
        query_comision = text("""
            SELECT 
                cg.id,
                cg.factura_id,
                cg.cliente_id,
                c.nombre as cliente_nombre,
                cg.comercial_id as asesor_id,
                u.name as asesor_nombre,
                cg.comision_total_eur,
                cg.estado,
                cg.fecha_prevista_pago,
                cg.fecha_pago,
                cg.fecha_generacion as created_at,
                cg.tarifa_id,
                c.cups,
                oc.ahorro_anual
            FROM comisiones_generadas cg
            LEFT JOIN clientes c ON cg.cliente_id = c.id
            LEFT JOIN users u ON cg.comercial_id = u.id
            LEFT JOIN facturas f ON cg.factura_id = f.id
            LEFT JOIN ofertas_calculadas oc ON f.selected_oferta_id = oc.id
            WHERE cg.id = :comision_id
        """)
        
        comision = db.execute(query_comision, {"comision_id": comision_id}).fetchone()
        
        if not comision:
            raise HTTPException(status_code=404, detail="Comisión no encontrada")
        
        # Consulta de repartos (si existen)
        query_repartos = text("""
            SELECT 
                rc.id,
                rc.receptor_tipo as tipo_destinatario,
                rc.importe_eur,
                rc.porcentaje,
                'pagado' as estado_pago,
                COALESCE(u.name, col.nombre) as destinatario_nombre,
                COALESCE(u.email, col.email) as destinatario_email
            FROM repartos_comision rc
            LEFT JOIN users u ON rc.receptor_tipo = 'comercial' AND rc.receptor_id = u.id
            LEFT JOIN colaboradores col ON rc.receptor_tipo = 'colaborador' AND rc.receptor_id = col.id
            WHERE rc.comision_generada_id = :comision_id
            ORDER BY rc.importe_eur DESC
        """)
        
        repartos_raw = db.execute(query_repartos, {"comision_id": comision_id}).fetchall()
        repartos = [dict(row._mapping) for row in repartos_raw]
        
        # Construir respuesta
        result = dict(comision._mapping)
        result['repartos'] = repartos
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COMISION] Error obteniendo detalle {comision_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/csv")
def exportar_comisiones_csv(
    estado: Optional[str] = Query(None),
    comercial_id: Optional[int] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Exportar comisiones a CSV con filtros aplicados
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    try:
        # Construir query con filtros
        conditions = ["1=1"]
        params = {}
        
        if estado:
            conditions.append("cg.estado = :estado")
            params["estado"] = estado
        
        if comercial_id:
            conditions.append("cg.comercial_id = :comercial_id")
            params["comercial_id"] = comercial_id
        
        if fecha_desde:
            conditions.append("cg.fecha_generacion >= :fecha_desde")
            params["fecha_desde"] = fecha_desde
        
        if fecha_hasta:
            conditions.append("cg.fecha_generacion <= :fecha_hasta")
            params["fecha_hasta"] = fecha_hasta
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT 
                cg.id,
                cg.factura_id,
                c.nombre as cliente,
                u.name as asesor,
                cg.comision_total_eur,
                cg.estado,
                cg.fecha_generacion,
                cg.fecha_prevista_pago,
                cg.fecha_pago
            FROM comisiones_generadas cg
            LEFT JOIN clientes c ON cg.cliente_id = c.id
            LEFT JOIN users u ON cg.comercial_id = u.id
            WHERE {where_clause}
            ORDER BY cg.fecha_generacion DESC
        """)
        
        rows = db.execute(query, params).fetchall()
        
        # Generar CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['ID', 'Factura', 'Cliente', 'Asesor', 'Comisión (€)', 'Estado', 'Fecha Generación', 'Fecha Prevista', 'Fecha Pago'])
        
        # Datos
        for row in rows:
            writer.writerow([
                row.id,
                row.factura_id,
                row.cliente or 'N/A',
                row.asesor or 'N/A',
                f"{row.comision_total_eur:.2f}",
                row.estado,
                row.fecha_generacion.strftime('%Y-%m-%d') if row.fecha_generacion else '',
                row.fecha_prevista_pago.strftime('%Y-%m-%d') if row.fecha_prevista_pago else '',
                row.fecha_pago.strftime('%Y-%m-%d') if row.fecha_pago else ''
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=comisiones_export.csv"}
        )
        
    except Exception as e:
        logger.error(f"[COMISION] Error exportando CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

