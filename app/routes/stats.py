"""
Stats API para Panel CEO
Endpoints de estadísticas agregadas y KPIs ejecutivos
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.db.conn import get_db
from typing import Optional
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/api/stats", tags=["stats"])
logger = logging.getLogger(__name__)


@router.get("/ceo")
def get_ceo_stats(
    company_id: Optional[int] = Query(None, description="Filtrar por company (para CEO)"),
    db: Session = Depends(get_db)
):
    """
    KPIs ejecutivos para dashboard /gestion/resumen
    
    Returns:
        - facturas_procesadas: Total facturas en estados avanzados
        - ahorro_total_eur: Suma ahorro anual de ofertas seleccionadas
        - comisiones_pendientes_eur: Suma comisiones pendientes/validadas
        - comisiones_pendientes_count: Cantidad comisiones sin pagar
        - asesores_activos: Cantidad comerciales activos
        - alertas: Lista de alertas críticas
    """
    
    try:
        # KPI 1: Facturas procesadas (que llegaron a comparar o tienen oferta)
        query_facturas = text("""
            SELECT COUNT(*) as count
            FROM facturas
            WHERE estado_factura IN ('lista_para_comparar', 'oferta_seleccionada')
        """)
        facturas_procesadas = db.execute(query_facturas).scalar() or 0
        
        # KPI 2: Ahorro total generado (suma ofertas seleccionadas)
        query_ahorro = text("""
            SELECT COALESCE(SUM(oc.ahorro_anual), 0) as total
            FROM facturas f
            JOIN ofertas_calculadas oc ON f.selected_oferta_id = oc.id
            WHERE f.selected_oferta_id IS NOT NULL
        """)
        ahorro_total_eur = float(db.execute(query_ahorro).scalar() or 0)
        
        # KPI 3: Comisiones pendientes de pago
        query_comisiones = text("""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(comision_total_eur), 0) as total
            FROM comisiones_generadas
            WHERE estado IN ('pendiente', 'validada')
        """)
        if company_id:
            query_comisiones = text("""
                SELECT 
                    COUNT(*) as count,
                    COALESCE(SUM(comision_total_eur), 0) as total
                FROM comisiones_generadas
                WHERE estado IN ('pendiente', 'validada')
                  AND company_id = :company_id
            """)
            result_comisiones = db.execute(query_comisiones, {"company_id": company_id}).fetchone()
        else:
            result_comisiones = db.execute(query_comisiones).fetchone()
        
        comisiones_pendientes_count = result_comisiones[0] if result_comisiones else 0
        comisiones_pendientes_eur = float(result_comisiones[1] if result_comisiones else 0)
        
        # KPI 4: Asesores activos
        query_asesores = text("""
            SELECT COUNT(*) as count
            FROM users
            WHERE role = 'comercial' AND is_active = true
        """)
        if company_id:
            query_asesores = text("""
                SELECT COUNT(*) as count
                FROM users
                WHERE role = 'comercial' 
                  AND is_active = true
                  AND company_id = :company_id
            """)
            asesores_activos = db.execute(query_asesores, {"company_id": company_id}).scalar() or 0
        else:
            asesores_activos = db.execute(query_asesores).scalar() or 0
        
        # ALERTAS
        alertas = []
        
        # Alerta 1: Ofertas seleccionadas sin comisión generada
        query_sin_comision = text("""
            SELECT COUNT(*) as count
            FROM facturas f
            WHERE f.selected_oferta_id IS NOT NULL
              AND f.id NOT IN (SELECT factura_id FROM comisiones_generadas)
        """)
        ofertas_sin_comision = db.execute(query_sin_comision).scalar() or 0
        if ofertas_sin_comision > 0:
            alertas.append({
                "tipo": "warning",
                "mensaje": f"{ofertas_sin_comision} ofertas seleccionadas sin comisión generada",
                "accion": "/gestion/pagos",
                "prioridad": "alta"
            })
        
        # Alerta 2: Comisiones validadas hace más de 30 días sin pagar
        query_validadas_antiguas = text("""
            SELECT COUNT(*) as count
            FROM comisiones_generadas
            WHERE estado = 'validada'
              AND created_at < CURRENT_DATE - INTERVAL '30 days'
        """)
        validadas_antiguas = db.execute(query_validadas_antiguas).scalar() or 0
        if validadas_antiguas > 0:
            alertas.append({
                "tipo": "warning",
                "mensaje": f"{validadas_antiguas} comisiones validadas hace +30 días sin pagar",
                "accion": "/gestion/pagos?estado=validada",
                "prioridad": "media"
            })
        
        # Alerta 3: Tarifas sin comisión configurada (si hay ofertas)
        query_tarifas_sin_comision = text("""
            SELECT COUNT(DISTINCT oc.tarifa_id) as count
            FROM ofertas_calculadas oc
            LEFT JOIN comisiones_tarifa ct ON oc.tarifa_id = ct.tarifa_id 
                AND ct.vigente_hasta IS NULL
            WHERE ct.id IS NULL
            LIMIT 1
        """)
        tarifas_sin_comision = db.execute(query_tarifas_sin_comision).scalar() or 0
        if tarifas_sin_comision > 0:
            alertas.append({
                "tipo": "info",
                "mensaje": f"{tarifas_sin_comision} tarifas sin comisión configurada",
                "accion": "/gestion/comisiones",
                "prioridad": "baja"
            })
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "kpis": {
                "facturas_procesadas": facturas_procesadas,
                "ahorro_total_eur": round(ahorro_total_eur, 2),
                "comisiones_pendientes_eur": round(comisiones_pendientes_eur, 2),
                "comisiones_pendientes_count": comisiones_pendientes_count,
                "asesores_activos": asesores_activos
            },
            "alertas": alertas
        }
        
    except Exception as e:
        logger.error(f"[STATS] Error obteniendo stats CEO: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


@router.get("/actividad-reciente")
def get_actividad_reciente(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Últimas actividades para feed en dashboard
    """
    
    try:
        # Últimas facturas con oferta seleccionada
        query = text("""
            SELECT 
                f.id as factura_id,
                f.estado_factura,
                c.nombre as cliente_nombre,
                f.created_at,
                oc.ahorro_anual
            FROM facturas f
            LEFT JOIN clientes c ON f.cliente_id = c.id
            LEFT JOIN ofertas_calculadas oc ON f.selected_oferta_id = oc.id
            WHERE f.estado_factura = 'oferta_seleccionada'
            ORDER BY f.created_at DESC
            LIMIT :limit
        """)
        
        rows = db.execute(query, {"limit": limit}).fetchall()
        
        actividades = []
        for row in rows:
            actividades.append({
                "tipo": "factura",
                "factura_id": row[0],
                "descripcion": f"Factura #{row[0]} procesada",
                "cliente": row[2] or "Sin nombre",
                "ahorro": f"€{round(float(row[4] or 0), 2)}" if row[4] else "N/A",
                "fecha": row[3].isoformat() if row[3] else None
            })
        
        return {
            "status": "ok",
            "actividades": actividades
        }
        
    except Exception as e:
        logger.error(f"[STATS] Error obteniendo actividad reciente: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evolucion")
def get_evolucion_temporal(
    dias: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """
    Evolución temporal para gráficos (últimos N días)
    """
    
    try:
        query = text("""
            SELECT 
                DATE(created_at) as fecha,
                COUNT(*) as facturas_dia
            FROM facturas
            WHERE created_at >= CURRENT_DATE - INTERVAL ':dias days'
              AND estado_factura IN ('lista_para_comparar', 'oferta_seleccionada')
            GROUP BY DATE(created_at)
            ORDER BY fecha ASC
        """)
        
        rows = db.execute(query, {"dias": dias}).fetchall()
        
        series = []
        for row in rows:
            series.append({
                "fecha": row[0].isoformat() if row[0] else None,
                "facturas": row[1]
            })
        
        return {
            "status": "ok",
            "periodo_dias": dias,
            "series": series
        }
        
    except Exception as e:
        logger.error(f"[STATS] Error obteniendo evolución: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
