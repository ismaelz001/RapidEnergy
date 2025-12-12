from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.conn import get_db
from app.db.models import Cliente
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/clientes", tags=["clientes"])


# --- Pydantic Schemas ---
class ClienteBase(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    dni: Optional[str] = None
    cups: Optional[str] = None
    direccion: Optional[str] = None
    provincia: Optional[str] = None
    estado: Optional[str] = "lead"


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    provincia: Optional[str] = None
    estado: Optional[str] = None


class FacturaSummary(BaseModel):
    id: int
    filename: str
    importe: Optional[float]
    fecha: Optional[str]

    class Config:
        from_attributes = True


class ClienteDetail(ClienteBase):
    id: int
    facturas: List[FacturaSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True


# --- Endpoints ---
@router.put("/{cliente_id}", response_model=ClienteDetail)
def update_cliente(cliente_id: int, cliente_update: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    update_data = cliente_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(cliente, key, value)

    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/", response_model=List[ClienteDetail])
def get_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    clientes = db.query(Cliente).options(joinedload(Cliente.facturas)).offset(skip).limit(limit).all()
    return clientes


@router.get("/{cliente_id}", response_model=ClienteDetail)
def get_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).options(joinedload(Cliente.facturas)).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("/", response_model=ClienteDetail)
def create_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    # Verificar si CUPS ya existe
    if cliente.cups:
        exists = db.query(Cliente).filter(Cliente.cups == cliente.cups).first()
        if exists:
            raise HTTPException(status_code=400, detail="Ya existe un cliente con este CUPS")

    db_cliente = Cliente(
        nombre=cliente.nombre,
        email=cliente.email,
        telefono=cliente.telefono,
        dni=cliente.dni,
        cups=cliente.cups,
        direccion=cliente.direccion,
        provincia=cliente.provincia,
        estado=cliente.estado,
        origen="manual",
    )
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente
