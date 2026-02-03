"""
API de Usuarios (Comerciales/Asesores)
Gestión de comerciales: crear, listar, editar, desactivar, estadísticas
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.conn import get_db
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import logging

router = APIRouter(prefix="/api/users", tags=["users"])
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="comercial", pattern="^(comercial|manager|ceo)$")
    company_id: Optional[int] = Field(default=1, description="ID de la empresa")


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    company_id: Optional[int]
    is_active: bool
    created_at: datetime


class UserStatsResponse(BaseModel):
    user_id: int
    user_name: str
    clientes_count: int
    facturas_procesadas: int
    comisiones_pendientes: float
    comisiones_validadas: float
    comisiones_pagadas: float
    comisiones_total: float


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("", response_model=UserResponse, status_code=201)
def crear_comercial(payload: CreateUserRequest, db: Session = Depends(get_db)):
    """
    Crear nuevo comercial/asesor
    Solo para CEO/DEV
    """
    
    try:
        # Verificar si el email ya existe
        check_query = text("SELECT id FROM users WHERE email = :email")
        existing = db.execute(check_query, {"email": payload.email}).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        
        # Insertar nuevo user
        insert_query = text("""
            INSERT INTO users (email, name, role, company_id, is_active, created_at)
            VALUES (:email, :name, :role, :company_id, true, NOW())
            RETURNING id, email, name, role, company_id, is_active, created_at
        """)
        
        result = db.execute(insert_query, {
            "email": payload.email,
            "name": payload.name,
            "role": payload.role,
            "company_id": payload.company_id
        }).fetchone()
        
        db.commit()
        
        logger.info(f"[USERS] ✅ Comercial creado: {payload.email} ({payload.name})")
        
        return dict(result._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[USERS] Error creando comercial: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[UserResponse])
def listar_comerciales(
    role: Optional[str] = Query(None, description="Filtrar por rol"),
    is_active: Optional[bool] = Query(None, description="Solo activos/inactivos"),
    db: Session = Depends(get_db)
):
    """
    Listar comerciales con filtros opcionales
    """
    
    try:
        conditions = ["1=1"]
        params = {}
        
        if role:
            conditions.append("role = :role")
            params["role"] = role
        
        if is_active is not None:
            conditions.append("is_active = :is_active")
            params["is_active"] = is_active
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT 
                id,
                email,
                name,
                role,
                company_id,
                is_active,
                created_at
            FROM users
            WHERE {where_clause}
            ORDER BY created_at DESC
        """)
        
        rows = db.execute(query, params).fetchall()
        
        return [dict(row._mapping) for row in rows]
        
    except Exception as e:
        logger.error(f"[USERS] Error listando comerciales: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
def obtener_comercial(user_id: int, db: Session = Depends(get_db)):
    """
    Obtener detalle de un comercial
    """
    
    try:
        query = text("""
            SELECT 
                id,
                email,
                name,
                role,
                company_id,
                is_active,
                created_at
            FROM users
            WHERE id = :user_id
        """)
        
        result = db.execute(query, {"user_id": user_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return dict(result._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[USERS] Error obteniendo comercial {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{user_id}", response_model=UserResponse)
def actualizar_comercial(
    user_id: int,
    payload: UpdateUserRequest,
    db: Session = Depends(get_db)
):
    """
    Actualizar datos de comercial (nombre, email, estado activo/inactivo)
    """
    
    try:
        # Construir UPDATE dinámico
        updates = []
        params = {"user_id": user_id}
        
        if payload.name is not None:
            updates.append("name = :name")
            params["name"] = payload.name
        
        if payload.email is not None:
            # Verificar si el email ya existe en otro usuario
            check_query = text("SELECT id FROM users WHERE email = :email AND id != :user_id")
            existing = db.execute(check_query, {"email": payload.email, "user_id": user_id}).fetchone()
            
            if existing:
                raise HTTPException(status_code=400, detail="Email ya registrado")
            
            updates.append("email = :email")
            params["email"] = payload.email
        
        if payload.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = payload.is_active
        
        if not updates:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        update_clause = ", ".join(updates)
        
        query = text(f"""
            UPDATE users
            SET {update_clause}
            WHERE id = :user_id
            RETURNING id, email, name, role, company_id, is_active, created_at
        """)
        
        result = db.execute(query, params).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        db.commit()
        
        logger.info(f"[USERS] ✅ Comercial {user_id} actualizado")
        
        return dict(result._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[USERS] Error actualizando comercial {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
def obtener_stats_comercial(user_id: int, db: Session = Depends(get_db)):
    """
    Estadísticas de un comercial: clientes, facturas, comisiones
    """
    
    try:
        query = text("""
            SELECT 
                u.id as user_id,
                u.name as user_name,
                COUNT(DISTINCT c.id) as clientes_count,
                COUNT(DISTINCT f.id) as facturas_procesadas,
                COALESCE(SUM(CASE WHEN cg.estado = 'pendiente' THEN cg.comision_total_eur ELSE 0 END), 0) as comisiones_pendientes,
                COALESCE(SUM(CASE WHEN cg.estado = 'validada' THEN cg.comision_total_eur ELSE 0 END), 0) as comisiones_validadas,
                COALESCE(SUM(CASE WHEN cg.estado = 'pagada' THEN cg.comision_total_eur ELSE 0 END), 0) as comisiones_pagadas,
                COALESCE(SUM(CASE WHEN cg.estado IN ('pendiente', 'validada', 'pagada') THEN cg.comision_total_eur ELSE 0 END), 0) as comisiones_total
            FROM users u
            LEFT JOIN clientes c ON c.comercial_id = u.id
            LEFT JOIN facturas f ON f.cliente_id = c.id
            LEFT JOIN comisiones_generadas cg ON cg.comercial_id = u.id
            WHERE u.id = :user_id
            GROUP BY u.id, u.name
        """)
        
        result = db.execute(query, {"user_id": user_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return dict(result._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[USERS] Error obteniendo stats {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
def desactivar_comercial(user_id: int, db: Session = Depends(get_db)):
    """
    Desactivar comercial (soft delete: is_active=false)
    No se eliminan datos, solo se marca como inactivo
    """
    
    try:
        query = text("""
            UPDATE users
            SET is_active = false
            WHERE id = :user_id
            RETURNING id, name
        """)
        
        result = db.execute(query, {"user_id": user_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        db.commit()
        
        logger.info(f"[USERS] ⚠️ Comercial {user_id} desactivado")
        
        return {
            "status": "ok",
            "message": f"Comercial {result.name} desactivado correctamente",
            "user_id": result.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[USERS] Error desactivando comercial {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
