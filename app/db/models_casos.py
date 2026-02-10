"""
Modelos SQLAlchemy para Módulo CRM - Sistema de Casos
✅ ACTUALIZADO según schema real ejecutado en Neon (10/feb/2026)
Añadir estos modelos a app/db/models.py
"""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, BigInteger, Numeric, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.conn import Base


# ═══════════════════════════════════════════════════════════
# MODELO NUEVO: Caso
# ═══════════════════════════════════════════════════════════

class Caso(Base):
    """
    Caso comercial: Representa un contrato/servicio energético en seguimiento.
    Un Cliente puede tener múltiples casos (distintos CUPS/contratos).
    ✅ SEGÚN SCHEMA REAL EJECUTADO EN NEON
    """
    __tablename__ = "casos"
    
    # Identificación
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Multi-tenant
    company_id = Column(BigInteger, ForeignKey("companies.id"), nullable=False, index=True)
    
    # Relaciones principales
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    asesor_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)  # Usuario CON LOGIN
    colaborador_id = Column(BigInteger, ForeignKey("colaboradores.id"), nullable=True, index=True)  # Externo SIN LOGIN
    
    # Relaciones con flujo de factura/comparativa/oferta
    factura_id = Column(Integer, ForeignKey("facturas.id"), nullable=True, index=True)
    comparativa_id = Column(Integer, ForeignKey("comparativas.id"), nullable=True)
    oferta_id = Column(BigInteger, ForeignKey("ofertas_calculadas.id"), nullable=True)
    tarifa_id = Column(BigInteger, ForeignKey("tarifas.id"), nullable=True)
    
    # Datos del contrato
    cups = Column(String, nullable=True, index=True)
    servicio = Column(Text, default="luz")  # "luz", "gas", "luz+gas"
    
    # Comercializadoras (texto libre, NO FK a companies)
    nueva_compania_text = Column(Text, nullable=True)  # Ej: "Repsol", "Endesa"
    antigua_compania_text = Column(Text, nullable=True)  # Comercializadora anterior
    tarifa_nombre_text = Column(Text, nullable=True)  # Nombre de la tarifa seleccionada
    
    # Canal de adquisición
    canal = Column(Text, nullable=True)  # "web", "telefono", "presencial", etc.
    
    # Ahorro
    ahorro_estimado_anual = Column(Numeric(12, 2), nullable=True)
    
    # Notas
    notas = Column(Text, nullable=True)
    
    # Pipeline comercial (CHECK constraint en DB)
    estado_comercial = Column(Text, nullable=False, default="lead", index=True)
    # Estados válidos: lead, contactado, en_estudio, propuesta_enviada, negociacion,
    #                  contrato_enviado, pendiente_firma, firmado, validado, activo,
    #                  cancelado, perdido, baja
    
    # Origen del caso
    origen = Column(Text, nullable=False, default="manual")  # "manual", "factura_upload", "web", etc.
    
    # Fechas del pipeline
    fecha_contacto = Column(DateTime(timezone=True), nullable=True)
    fecha_propuesta = Column(DateTime(timezone=True), nullable=True)
    fecha_firma = Column(DateTime(timezone=True), nullable=True)
    fecha_activacion = Column(DateTime(timezone=True), nullable=True)  # ⭐ Trigger comisión
    fecha_baja = Column(DateTime(timezone=True), nullable=True)
    
    # Auditoría
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    company = relationship("Company")
    cliente = relationship("Cliente", back_populates="casos")
    asesor = relationship("User", foreign_keys=[asesor_user_id])
    ✅ SEGÚN SCHEMA REAL EJECUTADO EN NEON
    """
    __tablename__ = "historial_caso"
    
    id = Column(BigInteger, primary_key=True, index=True)
    caso_id = Column(BigInteger, ForeignKey("casos.id"), nullable=False, index=True)
    
    # Evento
    tipo_evento = Column(Text, nullable=False)  # "cambio_estado", "nota", "email_enviado", etc.
    descripcion = Column(Text, nullable=False)
    
    # Cambio de estado (si aplica)
    estado_anterior = Column(Text, nullable=True)
    estado_nuevo = Column(Text, nullable=True)
    
    # Metadata
    metadata_json = Column(JSONB, nullable=True)  # ⚠️ JSONB, no Text
    
    # Auditoría
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user_id = Column(Bigteger, primary_key=True, index=True)
    caso_id = Column(BigInteger, ForeignKey("casos.id"), nullable=False, index=True)
    
    # Evento
    tipo_evento = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    
    # Cambio de estado (si aplica)
    estado_anterior = Column(String, nullable=True)
    estado_nuevo = Column(String, nullable=True)
    
    # Metadata
    metadata_json = Column(Text, nullable=True)
    
    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relaciones
    caso = relationship("Caso", back_populates="historial")
    user = relationship("User")


# ═══════════════════════════════════════════════════════════
# MODIFICACIONES A MODELOS EXISTENTES
# ═══════════════════════════════════════════════════════════

⚠️ MODIFICACIONES REQUERIDAS EN MODELOS EXISTENTES (app/db/models.py):

1. En Cliente (AÑADIR relación inversa):
    casos = relationship("Caso", back_populates="cliente", cascade="all, delete-orphan")

2. En ComisionGenerada (AÑADIR columna y relación):
    # Columna (ya existe en DB tras migración):
    caso_id = Column(BigInteger, ForeignKey("casos.id"), nullable=True, index=True)
    
    # Relación:
    caso = relationship("Caso", back_populates="comisiones")
    
    # Estados válidos según CHECK constraint en DB:
    # estado = Column(Text, nullable=False, default="pendiente", index=True)
    # Valores: pendiente, validada, pagada, anulada, retenida, decomision

3. En RepartoComision (verificar tipos):
    # Campos según schema real:
    id = Column(BigInteger, ...)
    comision_id = Column(BigInteger,  (según CHECK constraint en DB)"""
    LEAD = "lead"
    CONTACTADO = "contactado"
    EN_ESTUDIO = "en_estudio"
    PROPUESTA_ENVIADA = "propuesta_enviada"
    NEGOCIACION = "negociacion"
    CONTRATO_ENVIADO = "contrato_enviado"  # ⭐ NUEVO
    PENDIENTE_FIRMA = "pendiente_firma"    # ⭐ NUEVO
    FIRMADO = "firmado"
    VALIDADO = "validado"                  # ⭐ NUEVOn(Text, ...)  # 'pendiente', 'pagado', 'cancelado'
    # pendiente, validada, pagada, anulada, retenida, decomision
"""


# ═══════════════════════════════════════════════════════════
# ENUMS (app/db/enums.py o directamente en código)
# ═══════════════════════════════════════════════════════════

from enum import Enum

class EstadoComercialCaso(str, Enum):
    """Estados del pipeline comercial"""
    LEAD = "lead"
    CONTACTADO = "contactado"
    EN_ESTUDIO = "en_estudio"
    PROPUESTA_ENVIADA = "propuesta_enviada"
    NEGOCIACION = "negociacion"
    FIRMADO = "firmado"
    ACTIVO = "activo"
    BAJA = "baja"
    CANCELADO = "cancelado"
    PERDIDO = "perdido"
contrato_enviado", "perdido", "cancelado"],
    "negociacion": ["contrato_enviado", "propuesta_enviada", "perdido", "cancelado"],
    "contrato_enviado": ["pendiente_firma", "cancelado"],
    "pendiente_firma": ["firmado", "cancelado"],
    "firmado": ["validado", "cancelado"],
    "validado": ["activo", "cancelado"],  # ⚠️ Solo CEO puede mover a ACTIVO
    "activo": ["baja"],  # ⭐ TRIGGER: Genera comisión automáticamente
    "baja": [],  # Estado terminal
    "cancelado": [],  # Estado terminal
    "perdido": [],  # Estado terminalda"
    ANULADA = "anulada"
    RETENIDA = "retenida"
    DECOMISION = "decomision"


# ═══════════════════════════════════════════════════════════
# TRANSICIONES DE ESTADO PERMITIDAS
# ═══════════════════════════════════════════════════════════

TRANSICIONES_PERMITIDAS = {
    "lead": ["contactado", "perdido", "cancelado"],
    "contactado": ["en_estudio", "perdido", "cancelado"],
    "en_estudio": ["propuesta_enviada", "perdido", "cancelado"],
    "propuesta_enviada": ["negociacion", "firmado", "perdido", "cancelado"],
    "negociacion": ["firmado", "propuesta_enviada", "perdido", "cancelado"],
    "firmado": ["activo", "cancelado"],
    "activo": ["baja"],
    "baja": [],
    "cancelado": [],
    "perdido": [],
}

def puede_cambiar_estado(estado_actual: str, estado_nuevo: str) -> bool:
    """Valida si la transición de estado es permitida"""
    return estado_nuevo in TRANSICIONES_PERMITIDAS.get(estado_actual, [])
