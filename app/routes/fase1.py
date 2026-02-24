"""
Endpoints para Snapshots y Alertas - Fase 1
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_
from datetime import date, datetime, timedelta
from typing import List, Optional
import json

from app.db.conn import get_db
from app.db.models import SnapshotMensual, AlertaRenovacion, TareaCliente, Cliente, User
from app.services.snapshot_service import ejecutar_snapshot_mensual, obtener_comparativa_mensual
from app.auth import get_current_user, CurrentUser, require_ceo

router = APIRouter(prefix="/api/fase1", tags=["fase1"])


# ===== SNAPSHOTS =====

@router.post("/snapshot/ejecutar")
def ejecutar_snapshot(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_ceo)
):
    """Ejecutar snapshot mensual manualmente (normalmente automático día 1)"""
    resultado = ejecutar_snapshot_mensual(db)
    return resultado


@router.get("/snapshot/comparativa")
def get_comparativa_mensual(
    meses: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Obtener comparativa de últimos N meses para gráficos"""
    return obtener_comparativa_mensual(db, meses)


@router.get("/snapshot/lista")
def get_snapshots(
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Listar snapshots recientes"""
    snapshots = db.query(SnapshotMensual).order_by(
        SnapshotMensual.periodo.desc(),
        SnapshotMensual.tipo
    ).limit(limit).all()
    
    return {
        'ok': True,
        'count': len(snapshots),
        'snapshots': [
            {
                'id': s.id,
                'periodo': s.periodo.isoformat(),
                'tipo': s.tipo,
                'total_registros': s.total_registros,
                'created_at': s.created_at.isoformat() if s.created_at else None
            }
            for s in snapshots
        ]
    }


@router.get("/snapshot/{snapshot_id}")
def get_snapshot_detalle(
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Ver detalle de un snapshot específico"""
    snapshot = db.query(SnapshotMensual).filter(
        SnapshotMensual.id == snapshot_id
    ).first()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")
    
    return {
        'ok': True,
        'snapshot': {
            'id': snapshot.id,
            'periodo': snapshot.periodo.isoformat(),
            'tipo': snapshot.tipo,
            'total_registros': snapshot.total_registros,
            'data': json.loads(snapshot.data),
            'created_at': snapshot.created_at.isoformat() if snapshot.created_at else None
        }
    }


# ===== ALERTAS RENOVACIÓN =====

@router.get("/alertas/renovacion")
def get_alertas_renovacion(
    estado: Optional[str] = Query(None),
    comercial_id: Optional[int] = Query(None),
    proximos_dias: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Listar alertas de renovación
    
    Filtros:
    - estado: pendiente, gestionada, renovada, perdida
    - comercial_id: filtrar por comercial
    - proximos_dias: alertas con renovación en X días
    """
    query = db.query(AlertaRenovacion).filter(
        AlertaRenovacion.deleted_at.is_(None)
    )
    
    # Filtrar por comercial (si no es dev, solo ve las suyas)
    if not current_user.is_dev():
        if current_user.is_comercial():
            query = query.filter(AlertaRenovacion.comercial_id == current_user.id)
        elif current_user.is_ceo():
            # CEO ve todas de su company
            query = query.join(Cliente).filter(Cliente.company_id == current_user.company_id)
    
    if estado:
        query = query.filter(AlertaRenovacion.estado == estado)
    
    if comercial_id:
        query = query.filter(AlertaRenovacion.comercial_id == comercial_id)
    
    if proximos_dias:
        fecha_limite = date.today() + timedelta(days=proximos_dias)
        query = query.filter(AlertaRenovacion.fecha_renovacion_estimada <= fecha_limite)
    
    alertas = query.order_by(AlertaRenovacion.fecha_alerta.asc()).all()
    
    return {
        'ok': True,
        'count': len(alertas),
        'alertas': [
            {
                'id': a.id,
                'cliente_id': a.cliente_id,
                'cliente_nombre': a.cliente.nombre if a.cliente else None,
                'comercial_id': a.comercial_id,
                'comercial_nombre': a.comercial.name if a.comercial else None,
                'fecha_contrato': a.fecha_contrato.isoformat(),
                'fecha_alerta': a.fecha_alerta.isoformat(),
                'fecha_renovacion_estimada': a.fecha_renovacion_estimada.isoformat(),
                'dias_hasta_renovacion': (a.fecha_renovacion_estimada - date.today()).days,
                'estado': a.estado,
                'prioridad': a.prioridad,
                'notas': a.notas,
                'created_at': a.created_at.isoformat() if a.created_at else None
            }
            for a in alertas
        ]
    }


@router.put("/alertas/renovacion/{alerta_id}")
def actualizar_alerta_renovacion(
    alerta_id: int,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    notas: Optional[str] = None,
    resultado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Actualizar estado de una alerta de renovación"""
    alerta = db.query(AlertaRenovacion).filter(
        AlertaRenovacion.id == alerta_id,
        AlertaRenovacion.deleted_at.is_(None)
    ).first()
    
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    # Permisos: solo el comercial asignado o CEO/dev
    if not current_user.is_dev():
        if current_user.is_comercial() and alerta.comercial_id != current_user.id:
            raise HTTPException(status_code=403, detail="Sin permisos para esta alerta")
    
    # Actualizar campos
    if estado:
        alerta.estado = estado
        if estado in ['gestionada', 'renovada', 'perdida']:
            alerta.gestionada_at = datetime.now()
    
    if prioridad:
        alerta.prioridad = prioridad
    
    if notas:
        alerta.notas = notas
    
    if resultado:
        alerta.resultado = resultado
    
    alerta.updated_at = datetime.now()
    
    db.commit()
    db.refresh(alerta)
    
    return {
        'ok': True,
        'message': 'Alerta actualizada',
        'alerta_id': alerta.id,
        'estado': alerta.estado
    }


# ===== TAREAS CLIENTES =====

@router.get("/tareas/semana")
def get_tareas_semana(
    semana_offset: int = Query(0, ge=0, le=4),  # 0=semana actual, 1=próxima, etc.
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Obtener tareas de la semana (para agenda semanal)
    
    semana_offset: 0 = semana actual, 1 = próxima semana, etc.
    """
    # Calcular rango de fechas de la semana
    hoy = date.today()
    dias_desde_lunes = hoy.weekday()  # 0=Lunes, 6=Domingo
    inicio_semana = hoy - timedelta(days=dias_desde_lunes) + timedelta(weeks=semana_offset)
    fin_semana = inicio_semana + timedelta(days=6)
    
    query = db.query(TareaCliente).filter(
        TareaCliente.deleted_at.is_(None),
        TareaCliente.estado.in_(['pendiente', 'en_proceso']),
        TareaCliente.fecha_programada.between(inicio_semana, fin_semana)
    )
    
    # Filtrar por comercial (si no es dev)
    if not current_user.is_dev():
        if current_user.is_comercial():
            query = query.filter(TareaCliente.comercial_id == current_user.id)
        elif current_user.is_ceo():
            query = query.join(Cliente).filter(Cliente.company_id == current_user.company_id)
    
    tareas = query.order_by(TareaCliente.fecha_programada, TareaCliente.prioridad.desc()).all()
    
    # Agrupar por día de la semana
    tareas_por_dia = {i: [] for i in range(7)}  # 0=Lunes, 6=Domingo
    
    for tarea in tareas:
        dia_semana = tarea.fecha_programada.weekday()
        tareas_por_dia[dia_semana].append({
            'id': tarea.id,
            'cliente_id': tarea.cliente_id,
            'cliente_nombre': tarea.cliente.nombre if tarea.cliente else None,
            'tipo': tarea.tipo,
            'titulo': tarea.titulo,
            'descripcion': tarea.descripcion,
            'fecha_programada': tarea.fecha_programada.isoformat(),
            'estado': tarea.estado,
            'prioridad': tarea.prioridad
        })
    
    return {
        'ok': True,
        'semana': {
            'inicio': inicio_semana.isoformat(),
            'fin': fin_semana.isoformat(),
            'offset': semana_offset
        },
        'tareas_por_dia': tareas_por_dia,
        'total_tareas': len(tareas)
    }


@router.put("/tareas/{tarea_id}")
def actualizar_tarea(
    tarea_id: int,
    estado: Optional[str] = None,
    notas_resultado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Actualizar estado de una tarea"""
    tarea = db.query(TareaCliente).filter(
        TareaCliente.id == tarea_id,
        TareaCliente.deleted_at.is_(None)
    ).first()
    
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Permisos
    if not current_user.is_dev():
        if current_user.is_comercial() and tarea.comercial_id != current_user.id:
            raise HTTPException(status_code=403, detail="Sin permisos para esta tarea")
    
    if estado:
        tarea.estado = estado
        if estado == 'completada':
            tarea.completada_at = datetime.now()
    
    if notas_resultado:
        tarea.notas_resultado = notas_resultado
    
    tarea.updated_at = datetime.now()
    
    db.commit()
    
    return {
        'ok': True,
        'message': 'Tarea actualizada',
        'tarea_id': tarea.id,
        'estado': tarea.estado
    }


# ===== DASHBOARD STATS =====

@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Stats consolidadas para dashboard principal"""
    
    # Alertas activas (próximos 90 días)
    fecha_limite = date.today() + timedelta(days=90)
    alertas_activas = db.query(AlertaRenovacion).filter(
        AlertaRenovacion.deleted_at.is_(None),
        AlertaRenovacion.estado.in_(['pendiente', 'gestionada']),
        AlertaRenovacion.fecha_renovacion_estimada <= fecha_limite
    ).count()
    
    # Tareas pendientes semana actual
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    tareas_semana = db.query(TareaCliente).filter(
        TareaCliente.deleted_at.is_(None),
        TareaCliente.estado.in_(['pendiente', 'en_proceso']),
        TareaCliente.fecha_programada.between(inicio_semana, fin_semana)
    ).count()
    
    # Clientes activos
    clientes_activos = db.query(Cliente).filter(
        Cliente.deleted_at.is_(None),
        Cliente.estado.in_(['contratado', 'activo'])
    ).count()
    
    return {
        'ok': True,
        'stats': {
            'alertas_activas': alertas_activas,
            'tareas_semana': tareas_semana,
            'clientes_activos': clientes_activos
        }
    }
