from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.conn import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    dni = Column(String, nullable=True)
    cups = Column(String, unique=True, index=True, nullable=True)
    direccion = Column(String, nullable=True)
    provincia = Column(String, nullable=True)
    estado = Column(String, default="lead")
    origen = Column(String, default="factura_upload")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación: Un cliente tiene muchas facturas
    facturas = relationship("Factura", back_populates="cliente", cascade="all, delete-orphan")

class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    cups = Column(String, nullable=True)
    consumo_kwh = Column(Float, nullable=True)
    importe = Column(Float, nullable=True)
    fecha = Column(String, nullable=True)
    fecha_inicio = Column(String, nullable=True)
    fecha_fin = Column(String, nullable=True)
    raw_data = Column(Text, nullable=True)
    
    # Deduplicacion
    file_hash = Column(String, unique=True, index=True, nullable=True)
    numero_factura = Column(String, nullable=True)
    atr = Column(String, nullable=True)


    # Potencia
    potencia_p1_kw = Column(Float, nullable=True)
    potencia_p2_kw = Column(Float, nullable=True)

    # Consumos por periodo
    consumo_p1_kwh = Column(Float, nullable=True)
    consumo_p2_kwh = Column(Float, nullable=True)
    consumo_p3_kwh = Column(Float, nullable=True)
    consumo_p4_kwh = Column(Float, nullable=True)
    consumo_p5_kwh = Column(Float, nullable=True)
    consumo_p6_kwh = Column(Float, nullable=True)

    # Condiciones
    bono_social = Column(Boolean, default=False)
    servicios_vinculados = Column(Boolean, default=False)
    alquiler_contador = Column(Float, nullable=True)

    # Impuestos y totales
    impuesto_electrico = Column(Float, nullable=True)
    iva = Column(Float, nullable=True)
    total_factura = Column(Float, nullable=True)
    
    # P1: Periodo de facturación (obligatorio para comparar)
    periodo_dias = Column(Integer, nullable=True)

    # Estado
    estado_factura = Column(String, default="pendiente_datos")
    
    # Oferta seleccionada (Persistencia para MVP)
    selected_offer_json = Column(Text, nullable=True)
    
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    
    # Relación: Una factura pertenece a un cliente
    cliente = relationship("Cliente", back_populates="facturas")
    comparativas = relationship("Comparativa", back_populates="factura", cascade="all, delete-orphan")


class Comparativa(Base):
    """P1: Auditoría de comparaciones de ofertas"""
    __tablename__ = "comparativas"
    
    id = Column(Integer, primary_key=True, index=True)
    factura_id = Column(Integer, ForeignKey("facturas.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Inputs de la comparación
    periodo_dias = Column(Integer, nullable=True)
    current_total = Column(Float, nullable=True)
    inputs_json = Column(Text, nullable=True)
    
    # Resultados
    offers_json = Column(Text, nullable=True)
    status = Column(String, default="ok")
    error_json = Column(Text, nullable=True)
    
    factura = relationship("Factura", back_populates="comparativas")
