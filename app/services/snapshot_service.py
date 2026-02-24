"""
Servicio de Snapshots Mensuales
Ejecutar día 1 de cada mes a las 02:00 AM
"""
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import json
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.db.models import (
    SnapshotMensual, Cliente, Factura, 
    AlertaRenovacion, ComisionGenerada, Caso
)

logger = logging.getLogger(__name__)


def _get_primer_dia_mes_actual() -> date:
    """Retorna el día 1 del mes actual"""
    hoy = date.today()
    return date(hoy.year, hoy.month, 1)


def _serialize_for_json(data: Any) -> Any:
    """Convierte tipos no serializables a JSON"""
    if isinstance(data, (date, datetime)):
        return data.isoformat()
    if isinstance(data, dict):
        return {k: _serialize_for_json(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_serialize_for_json(item) for item in data]
    return data


def crear_snapshot_clientes_activos(db: Session, periodo: date) -> int:
    """
    Snapshot 1: Clientes activos del mes
    
    Guarda:
    - Total clientes activos
    - Nuevos del mes
    - Bajas del mes
    - Churn rate
    - Por estado
    """
    # Clientes activos (no eliminados)
    clientes_activos = db.query(Cliente).filter(
        Cliente.deleted_at.is_(None)
    ).all()
    
    # Clientes nuevos del mes
    inicio_mes = periodo
    fin_mes = periodo + relativedelta(months=1)
    clientes_nuevos = db.query(Cliente).filter(
        Cliente.deleted_at.is_(None),
        Cliente.created_at >= inicio_mes,
        Cliente.created_at < fin_mes
    ).count()
    
    # Bajas del mes (soft delete)
    clientes_bajas = db.query(Cliente).filter(
        Cliente.deleted_at.isnot(None),
        Cliente.deleted_at >= inicio_mes,
        Cliente.deleted_at < fin_mes
    ).count()
    
    # Por estado
    estados = {}
    for estado in ['lead', 'seguimiento', 'oferta_enviada', 'contratado', 'descartado']:
        count = db.query(Cliente).filter(
            Cliente.deleted_at.is_(None),
            Cliente.estado == estado
        ).count()
        estados[estado] = count
    
    # Churn rate
    total_activos = len(clientes_activos)
    churn_rate = (clientes_bajas / total_activos * 100) if total_activos > 0 else 0.0
    
    # Lista de clientes (IDs + datos básicos)
    clientes_data = []
    for c in clientes_activos[:100]:  # Limitar a 100 para no saturar
        clientes_data.append({
            'id': c.id,
            'nombre': c.nombre,
            'email': c.email,
            'estado': c.estado,
            'cups': c.cups,
            'created_at': c.created_at.isoformat() if c.created_at else None
        })
    
    snapshot_data = {
        'total_clientes': total_activos,
        'nuevos_mes': clientes_nuevos,
        'bajas_mes': clientes_bajas,
        'churn_rate': round(churn_rate, 2),
        'por_estado': estados,
        'clientes': clientes_data,
        'fecha_snapshot': datetime.now().isoformat()
    }
    
    # Guardar snapshot
    snapshot = SnapshotMensual(
        periodo=periodo,
        tipo='clientes_activos',
        data=json.dumps(_serialize_for_json(snapshot_data), ensure_ascii=False),
        total_registros=total_activos
    )
    db.add(snapshot)
    db.commit()
    
    logger.info(f"[SNAPSHOT] Clientes activos guardado: {total_activos} clientes, {clientes_nuevos} nuevos, {clientes_bajas} bajas")
    return snapshot.id


def crear_snapshot_comisiones_pendientes(db: Session, periodo: date) -> int:
    """
    Snapshot 2: Comisiones pendientes de liquidación
    
    Guarda:
    - Total comisiones pendientes
    - Total EUR pendientes
    - Por comercial
    - Por antigüedad
    """
    # Comisiones pendientes (estado != 'pagada')
    comisiones_pendientes = db.query(ComisionGenerada).filter(
        ComisionGenerada.estado.in_(['pendiente', 'liquidada'])
    ).all()
    
    total_eur_pendiente = sum(
        float(c.comision_eur or 0) for c in comisiones_pendientes
    )
    
    # Por comercial
    por_comercial = {}
    for c in comisiones_pendientes:
        if c.user_id:
            if c.user_id not in por_comercial:
                por_comercial[c.user_id] = {'count': 0, 'total_eur': 0.0}
            por_comercial[c.user_id]['count'] += 1
            por_comercial[c.user_id]['total_eur'] += float(c.comision_eur or 0)
    
    snapshot_data = {
        'total_comisiones': len(comisiones_pendientes),
        'total_eur_pendiente': round(total_eur_pendiente, 2),
        'por_comercial': por_comercial,
        'fecha_snapshot': datetime.now().isoformat()
    }
    
    snapshot = SnapshotMensual(
        periodo=periodo,
        tipo='comisiones_pendientes',
        data=json.dumps(_serialize_for_json(snapshot_data), ensure_ascii=False),
        total_registros=len(comisiones_pendientes)
    )
    db.add(snapshot)
    db.commit()
    
    logger.info(f"[SNAPSHOT] Comisiones pendientes: {len(comisiones_pendientes)} comisiones, {total_eur_pendiente:.2f}€")
    return snapshot.id


def crear_snapshot_renovaciones_proximas(db: Session, periodo: date) -> int:
    """
    Snapshot 3: Clientes con renovación próxima (próximos 90 días)
    
    Guarda:
    - Clientes con renovación en 90 días
    - Por urgencia
    - Por comercial
    """
    fecha_limite = periodo + relativedelta(days=90)
    
    alertas_proximas = db.query(AlertaRenovacion).filter(
        AlertaRenovacion.deleted_at.is_(None),
        AlertaRenovacion.estado.in_(['pendiente', 'gestionada']),
        AlertaRenovacion.fecha_renovacion_estimada <= fecha_limite
    ).all()
    
    # Por urgencia
    urgente = sum(1 for a in alertas_proximas if (a.fecha_renovacion_estimada - periodo).days <= 30)
    media = sum(1 for a in alertas_proximas if 30 < (a.fecha_renovacion_estimada - periodo).days <= 60)
    baja = len(alertas_proximas) - urgente - media
    
    snapshot_data = {
        'total_renovaciones': len(alertas_proximas),
        'urgente_30_dias': urgente,
        'media_60_dias': media,
        'baja_90_dias': baja,
        'fecha_snapshot': datetime.now().isoformat()
    }
    
    snapshot = SnapshotMensual(
        periodo=periodo,
        tipo='renovaciones_proximas',
        data=json.dumps(_serialize_for_json(snapshot_data), ensure_ascii=False),
        total_registros=len(alertas_proximas)
    )
    db.add(snapshot)
    db.commit()
    
    logger.info(f"[SNAPSHOT] Renovaciones próximas: {len(alertas_proximas)} alertas ({urgente} urgentes)")
    return snapshot.id


def ejecutar_snapshot_mensual(db: Session) -> Dict[str, Any]:
    """
    Ejecuta todos los snapshots del mes actual
    
    Ejecutar día 1 de cada mes a las 02:00 AM (cron job)
    """
    periodo = _get_primer_dia_mes_actual()
    
    logger.info(f"[SNAPSHOT] Iniciando snapshot mensual para periodo {periodo}")
    
    try:
        # Verificar si ya existe snapshot para este periodo
        existe = db.query(SnapshotMensual).filter(
            SnapshotMensual.periodo == periodo
        ).first()
        
        if existe:
            logger.warning(f"[SNAPSHOT] Ya existe snapshot para periodo {periodo}, cancelando")
            return {
                'ok': False,
                'message': f'Snapshot ya existe para periodo {periodo}',
                'periodo': periodo.isoformat()
            }
        
        # Ejecutar snapshots
        snapshot_ids = []
        
        # 1. Clientes activos
        id1 = crear_snapshot_clientes_activos(db, periodo)
        snapshot_ids.append(('clientes_activos', id1))
        
        # 2. Comisiones pendientes
        id2 = crear_snapshot_comisiones_pendientes(db, periodo)
        snapshot_ids.append(('comisiones_pendientes', id2))
        
        # 3. Renovaciones próximas
        id3 = crear_snapshot_renovaciones_proximas(db, periodo)
        snapshot_ids.append(('renovaciones_proximas', id3))
        
        logger.info(f"[SNAPSHOT] Snapshot mensual completado: {len(snapshot_ids)} tipos guardados")
        
        return {
            'ok': True,
            'message': f'Snapshot mensual completado para {periodo}',
            'periodo': periodo.isoformat(),
            'snapshots_creados': snapshot_ids
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"[SNAPSHOT] Error ejecutando snapshot mensual: {e}", exc_info=True)
        return {
            'ok': False,
            'message': f'Error: {str(e)}',
            'periodo': periodo.isoformat()
        }


def obtener_comparativa_mensual(db: Session, meses: int = 6) -> Dict[str, Any]:
    """
    Obtiene comparativa de últimos N meses
    
    Útil para gráficos de tendencias en dashboard
    """
    periodo_actual = _get_primer_dia_mes_actual()
    periodos = []
    
    for i in range(meses):
        p = periodo_actual - relativedelta(months=i)
        periodos.append(p)
    
    # Obtener snapshots de clientes activos
    snapshots = db.query(SnapshotMensual).filter(
        SnapshotMensual.tipo == 'clientes_activos',
        SnapshotMensual.periodo.in_(periodos)
    ).order_by(SnapshotMensual.periodo.desc()).all()
    
    datos_comparativa = []
    for s in snapshots:
        data = json.loads(s.data)
        datos_comparativa.append({
            'periodo': s.periodo.isoformat(),
            'total_clientes': data.get('total_clientes', 0),
            'nuevos_mes': data.get('nuevos_mes', 0),
            'bajas_mes': data.get('bajas_mes', 0),
            'churn_rate': data.get('churn_rate', 0)
        })
    
    return {
        'ok': True,
        'meses': meses,
        'datos': datos_comparativa
    }
