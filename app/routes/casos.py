from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.db.conn import get_db
from app.db.models import Caso, Cliente, User, HistorialCaso
from app.auth import get_current_user, CurrentUser
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/casos", tags=["casos"])

# Schemas
class CasoCreate(BaseModel):
    cliente_id: int
    asesor_user_id: Optional[int] = None
    colaborador_id: Optional[int] = None
    cups: Optional[str] = None
    servicio: str = "luz"
    canal: Optional[str] = None
    notas: Optional[str] = None
    estado_comercial: str = "lead"

class CasoUpdate(BaseModel):
    asesor_user_id: Optional[int] = None
    colaborador_id: Optional[int] = None
    cups: Optional[str] = None
    servicio: Optional[str] = None
    nueva_compania_text: Optional[str] = None
    antigua_compania_text: Optional[str] = None
    tarifa_nombre_text: Optional[str] = None
    canal: Optional[str] = None
    ahorro_estimado_anual: Optional[float] = None
    notas: Optional[str] = None
    oferta_id: Optional[int] = None
    tarifa_id: Optional[int] = None

class CambioEstado(BaseModel):
    estado_nuevo: str
    notas: Optional[str] = None

# Transiciones permitidas
TRANSICIONES = {
    "lead": ["contactado", "perdido", "cancelado"],
    "contactado": ["en_estudio", "perdido", "cancelado"],
    "en_estudio": ["propuesta_enviada", "perdido", "cancelado"],
    "propuesta_enviada": ["negociacion", "contrato_enviado", "perdido", "cancelado"],
    "negociacion": ["contrato_enviado", "propuesta_enviada", "perdido", "cancelado"],
    "contrato_enviado": ["pendiente_firma", "cancelado"],
    "pendiente_firma": ["firmado", "cancelado"],
    "firmado": ["validado", "cancelado"],
    "validado": ["activo", "cancelado"],
    "activo": ["baja"],
    "baja": [],
    "cancelado": [],
    "perdido": [],
}

@router.get("")
def listar_casos(
    estado: Optional[str] = None,
    asesor_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista casos con filtros según rol:
    - DEV: Ve todos los casos
    - CEO: Ve casos de su company_id
    - COMERCIAL: Ve solo sus propios casos
    """
    query = db.query(Caso).options(
        joinedload(Caso.cliente),
        joinedload(Caso.asesor),
        joinedload(Caso.colaborador)
    )
    
    # Filtros por rol
    if current_user.role == "comercial":
        # Comercial solo ve sus propios casos
        query = query.filter(Caso.asesor_user_id == current_user.id)
    elif current_user.role == "ceo":
        # CEO ve casos de su empresa
        if current_user.company_id:
            query = query.filter(Caso.company_id == current_user.company_id)
    # DEV no tiene filtros
    
    # Filtros adicionales opcionales
    if estado:
        query = query.filter(Caso.estado_comercial == estado)
    if asesor_i
    data: CasoCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea un caso. CEO/DEV pueden crear para cualquier asesor.
    Comercial solo puede crear casos asignados a sí mismo.
    """
    # Verificar que cliente existe
    cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")
    
    # Determinar company_id
    if current_user.role == "dev":
        company_id = 1  # Default para dev
    elif current_user.company_id:
        company_id = current_user.company_id
    else:
        raise HTTPException(400, "Usuario sin company_id asignado")
    
    # Si es comercial, forzar que sea el asesor
    if current_user.role == "comercial":
        data.asesor_user_id = current_user.id {"id": c.cliente.id, "nombre": c.cliente.nombre} if c.cliente else None,
        "cups": c.cups,
        "estado_comercial": c.estado_comercial,
        "asesor": {"id": c.asesor.id, "nombre": c.asesor.name} if c.asesor else None,
        "colaborador": {"id": c.colaborador.id, "nombre": c.colaborador.nombre} if c.colaborador else None,
        "ahorro_estimado_anual": float(c.ahorro_estimado_anual) if c.ahorro_estimado_anual else None,
        "nueva_compania_text": c.nueva_compania_text,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c in casos]

@router.post("")
def crear_caso(data: CasoCreate, db: Session = Depends(get_db)):
    # Verificar que cliente existe
    cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")
    
    # Company hardcoded por ahora (ajustar con auth)
    company_id = 1
    
    caso = Caso(
        company_id=company_id,
        cliente_id=data.cliente_id,
        asesor_user_id=data.asesor_user_id,
        colaborador_id=data.colaborador_id,
        cups=data.cups,
        servicio=data.servicio,
        canal=data.canal,
        notas=data.notas,
        estado_comercial=data.estado_comercial,
        origen="manual"
    )
    db.add(caso)
    db.flush()
    
    # Registrar en historial
    historial = HistorialCaso(
        caso_id=caso.id,
        tipo_evento="creacion",
        descripcion=f"Caso creado en estado {data.estado_comercial}",
        estado_nuevo=data.estado_comercial,
        user_id=data.asesor_user_id
    )
    db.add(historial)
    db.commit()
    db.refresh(caso)
    
    return {"id": caso.id, "mensaje": "Caso creado"}

@router.get("/{caso_id}")
def obtener_caso(caso_id: int, db: Session = Depends(get_db)):
    caso = db.query(Caso).options(
        joinedload(Caso.cliente),
        joinedload(Caso.asesor),
        joinedload(Caso.colaborador),
        joinedload(Caso.factura),
        joinedload(Caso.oferta),
        joinedload(Caso.historial)
    ).filter(Caso.id == caso_id).first()
    
    if not caso:
        raise HTTPException(404, "Caso no encontrado")
    
    return {
        "id": caso.id,
        "cliente": {
            "id": caso.cliente.id,
            "nombre": caso.cliente.nombre,
            "email": caso.cliente.email,
            "telefono": caso.cliente.telefono,
            "cups": caso.cliente.cups,
        } if caso.cliente else None,
        "cups": caso.cups,
        "servicio": caso.servicio,
        "estado_comercial": caso.estado_comercial,
        "asesor": {"id": caso.asesor.id, "nombre": caso.asesor.name} if caso.asesor else None,
        "colaborador": {"id": caso.colaborador.id, "nombre": caso.colaborador.nombre} if caso.colaborador else None,
        "nueva_compania_text": caso.nueva_compania_text,
        "antigua_compania_text": caso.antigua_compania_text,
        "tarifa_nombre_text": caso.tarifa_nombre_text,
        "canal": caso.canal,
        "ahorro_estimado_anual": float(caso.ahorro_estimado_anual) if caso.ahorro_estimado_anual else None,
        "notas": caso.notas,
        "origen": caso.origen,
        "factura_id": caso.factura_id,
        "oferta_id": caso.oferta_id,
        "fecha_contacto": caso.fecha_contacto.isoformat() if caso.fecha_contacto else None,
        "fecha_propuesta": caso.fecha_propuesta.isoformat() if caso.fecha_propuesta else None,
        "fecha_firma": caso.fecha_firma.isoformat() if caso.fecha_firma else None,
        "fecha_activacion": caso.fecha_activacion.isoformat() if caso.fecha_activacion else None,
        "fecha_baja": caso.fecha_baja.isoformat() if caso.fecha_baja else None,
        "created_at": caso.created_at.isoformat() if caso.created_at else None,
        "historial": [{
            "tipo_evento": h.tipo_evento,
            "descripcion": h.descripcion,
            "estado_anterior": h.estado_anterior,
            "estado_nuevo": h.estado_nuevo,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        } for h in sorted(caso.historial, key=lambda x: x.created_at, reverse=True)]
    }

@router.patch("/{caso_id}")
def actualizar_caso(caso_id: int, data: CasoUpdate, db: Session = Depends(get_db)):
    caso = db.query(Caso).filter(Caso.id == caso_id).first()
    if not caso:
        raise HTTPException(404, "Caso no encontrado")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(caso, key, value)
    
    caso.updated_at = datetime.utcnow()
    db.commit()
    
    return {"mensaje": "Caso actualizado"}

@router.post("/{caso_id}/cambiar-estado")
def cambiar_estado(caso_id: int, data: CambioEstado, db: Session = Depends(get_db)):
    caso = db.query(Caso).filter(Caso.id == caso_id).first()
    if not caso:
        raise HTTPException(404, "Caso no encontrado")
    
    estado_actual = caso.estado_comercial
    estado_nuevo = data.estado_nuevo
    
    # Validar transición
    if estado_nuevo not in TRANSICIONES.get(estado_actual, []):
        raise HTTPException(400, f"Transición no permitida: {estado_actual} → {estado_nuevo}")
    
    # Actualizar estado
    caso.estado_comercial = estado_nuevo
    caso.updated_at = datetime.utcnow()
    
    # Actualizar fechas según estado
    if estado_nuevo == "contactado":
        caso.fecha_contacto = datetime.utcnow()
    elif estado_nuevo == "propuesta_enviada":
        caso.fecha_propuesta = datetime.utcnow()
    elif estado_nuevo == "firmado":
        caso.fecha_firma = datetime.utcnow()
    elif estado_nuevo == "activo":
        caso.fecha_activacion = datetime.utcnow()
        # TODO: Generar comisión automáticamente
    elif estado_nuevo == "baja":
        caso.fecha_baja = datetime.utcnow()
    
    # Registrar en historial
    historial = HistorialCaso(
        caso_id=caso.id,
        tipo_evento="cambio_estado",
        descripcion=data.notas or f"Estado cambiado de {estado_actual} a {estado_nuevo}",
        estado_anterior=estado_actual,
        estado_nuevo=estado_nuevo,
        user_id=caso.asesor_user_id
    )
    db.add(historial)
    db.commit()
    
    return {"mensaje": f"Estado cambiado a {estado_nuevo}"}
