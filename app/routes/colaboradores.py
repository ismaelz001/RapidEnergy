"""
API de Colaboradores Externos
Personas que reciben comisiones pero no tienen acceso al sistema
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.conn import get_db
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import logging

router = APIRouter(prefix="/api/colaboradores", tags=["colaboradores"])
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class CreateColaboradorRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    notas: Optional[str] = None
    company_id: int = Field(default=1, description="ID de la empresa")


class UpdateColaboradorRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    notas: Optional[str] = None
    is_active: Optional[bool] = None


class ColaboradorResponse(BaseModel):
    id: int
    company_id: int
    nombre: str
    email: Optional[str]
    telefono: Optional[str]
    notas: Optional[str]
    is_active: bool
    created_at: datetime


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("", response_model=ColaboradorResponse, status_code=201)
def crear_colaborador(payload: CreateColaboradorRequest, db: Session = Depends(get_db)):
    """
    Crear nuevo colaborador externo
    Solo para CEO/DEV
    """
    
    try:
        insert_query = text("""
            INSERT INTO colaboradores (company_id, nombre, email, telefono, notas, is_active, created_at)
            VALUES (:company_id, :nombre, :email, :telefono, :notas, true, NOW())
            RETURNING id, company_id, nombre, email, telefono, notas, is_active, created_at
        """)
        
        result = db.execute(insert_query, {
            "company_id": payload.company_id,
            "nombre": payload.nombre,
            "email": payload.email,
            "telefono": payload.telefono,
            "notas": payload.notas
        }).fetchone()
        
        db.commit()
        
        logger.info(f"[COLABORADORES] ✅ Colaborador creado: {payload.nombre}")
        
        return dict(result._mapping)
        
    except Exception as e:
        db.rollback()
        logger.error(f"[COLABORADORES] Error creando colaborador: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ColaboradorResponse])
def listar_colaboradores(
    company_id: Optional[int] = Query(None, description="Filtrar por empresa"),
    is_active: Optional[bool] = Query(None, description="Solo activos/inactivos"),
    db: Session = Depends(get_db)
):
    """
    Listar colaboradores con filtros opcionales
    """
    
    try:
        conditions = ["1=1"]
        params = {}
        
        if company_id:
            conditions.append("company_id = :company_id")
            params["company_id"] = company_id
        
        if is_active is not None:
            conditions.append("is_active = :is_active")
            params["is_active"] = is_active
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT 
                id,
                company_id,
                nombre,
                email,
                telefono,
                notas,
                is_active,
                created_at
            FROM colaboradores
            WHERE {where_clause}
            ORDER BY created_at DESC
        """)
        
        rows = db.execute(query, params).fetchall()
        
        return [dict(row._mapping) for row in rows]
        
    except Exception as e:
        logger.error(f"[COLABORADORES] Error listando: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{colaborador_id}", response_model=ColaboradorResponse)
def obtener_colaborador(colaborador_id: int, db: Session = Depends(get_db)):
    """
    Obtener detalle de un colaborador
    """
    
    try:
        query = text("""
            SELECT 
                id,
                company_id,
                nombre,
                email,
                telefono,
                notas,
                is_active,
                created_at
            FROM colaboradores
            WHERE id = :colaborador_id
        """)
        
        result = db.execute(query, {"colaborador_id": colaborador_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Colaborador no encontrado")
        
        return dict(result._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[COLABORADORES] Error obteniendo {colaborador_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{colaborador_id}", response_model=ColaboradorResponse)
def actualizar_colaborador(
    colaborador_id: int,
    payload: UpdateColaboradorRequest,
    db: Session = Depends(get_db)
):
    """
    Actualizar datos de colaborador
    """
    
    try:
        # Construir UPDATE dinámico
        updates = []
        params = {"colaborador_id": colaborador_id}
        
        if payload.nombre is not None:
            updates.append("nombre = :nombre")
            params["nombre"] = payload.nombre
        
        if payload.email is not None:
            updates.append("email = :email")
            params["email"] = payload.email
        
        if payload.telefono is not None:
            updates.append("telefono = :telefono")
            params["telefono"] = payload.telefono
        
        if payload.notas is not None:
            updates.append("notas = :notas")
            params["notas"] = payload.notas
        
        if payload.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = payload.is_active
        
        if not updates:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        update_clause = ", ".join(updates)
        
        query = text(f"""
            UPDATE colaboradores
            SET {update_clause}
            WHERE id = :colaborador_id
            RETURNING id, company_id, nombre, email, telefono, notas, is_active, created_at
        """)
        
        result = db.execute(query, params).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Colaborador no encontrado")
        
        db.commit()
        
        logger.info(f"[COLABORADORES] ✅ Colaborador {colaborador_id} actualizado")
        
        return dict(result._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[COLABORADORES] Error actualizando {colaborador_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{colaborador_id}")
def eliminar_colaborador(colaborador_id: int, db: Session = Depends(get_db)):
    """
    Desactivar colaborador (soft delete: is_active=false)
    """
    
    try:
        query = text("""
            UPDATE colaboradores
            SET is_active = false
            WHERE id = :colaborador_id
            RETURNING id, nombre
        """)
        
        result = db.execute(query, {"colaborador_id": colaborador_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Colaborador no encontrado")
        
        db.commit()
        
        logger.info(f"[COLABORADORES] ⚠️ Colaborador {colaborador_id} desactivado")
        
        return {
            "status": "ok",
            "message": f"Colaborador {result.nombre} desactivado correctamente",
            "colaborador_id": result.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[COLABORADORES] Error eliminando {colaborador_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
