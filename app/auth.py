"""
Sistema de autenticación mock para desarrollo
TODO: Reemplazar con JWT/OAuth real en producción
"""

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.conn import get_db
from app.db.models import User
from typing import Optional

class CurrentUser:
    """Usuario actual obtenido del header X-User-Id"""
    def __init__(self, id: int, email: str, name: str, role: str, company_id: Optional[int]):
        self.id = id
        self.email = email
        self.name = name
        self.role = role
        self.company_id = company_id
    
    def is_dev(self) -> bool:
        return self.role == "dev"
    
    def is_ceo(self) -> bool:
        return self.role in ["dev", "ceo"]
    
    def is_comercial(self) -> bool:
        return self.role == "comercial"
    
    def can_access_gestion(self) -> bool:
        """Puede acceder al panel de gestión"""
        return self.role in ["dev", "ceo"]
    
    def can_manage_payments(self) -> bool:
        """Puede gestionar pagos de comisiones"""
        return self.role in ["dev", "ceo"]


def get_current_user(
    x_user_id: Optional[int] = Header(None),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Obtiene el usuario actual desde el header X-User-Id
    
    En desarrollo, el frontend envía X-User-Id en cada request
    En producción, esto se reemplazará por JWT
    """
    if not x_user_id:
        # Por defecto dev (para testing)
        return CurrentUser(
            id=1,
            email="ismael@rodorte.com",
            name="Ismael Rodríguez",
            role="dev",
            company_id=None
        )
    
    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    
    return CurrentUser(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        company_id=user.company_id
    )


def require_ceo(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Requiere rol CEO o DEV"""
    if not current_user.is_ceo():
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requiere rol CEO o DEV")
    return current_user


def require_dev(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Requiere rol DEV"""
    if not current_user.is_dev():
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requiere rol DEV")
    return current_user
