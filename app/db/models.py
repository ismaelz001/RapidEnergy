from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, BigInteger, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.conn import Base


# ⭐ BLOQUE 1 MVP CRM: Companies y Users
class Company(Base):
    """Empresas (multi-tenant)"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    nif = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación: Una company tiene muchos usuarios
    users = relationship("User", back_populates="company")


class User(Base):
    """Usuarios del sistema (dev, ceo, comercial)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # dev, ceo, comercial
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)  # NULL para dev
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación: Un usuario pertenece a una company
    company = relationship("Company", back_populates="users")
    # Relación: Un comercial tiene muchos clientes
    clientes = relationship("Cliente", back_populates="comercial", foreign_keys="Cliente.comercial_id")


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
    
    # ⭐ Multi-tenant y asignación
    company_id = Column(BigInteger, ForeignKey("companies.id"), nullable=True, index=True)
    comercial_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación: Un cliente tiene muchas facturas
    facturas = relationship("Factura", back_populates="cliente", cascade="all, delete-orphan")
    # Relación: Un cliente pertenece a una company y un comercial
    company = relationship("Company")
    comercial = relationship("User", back_populates="clientes", foreign_keys=[comercial_id])
    # Relación: Un cliente tiene muchos casos
    casos = relationship("Caso", back_populates="cliente", cascade="all, delete-orphan")

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
    iva_porcentaje = Column(Float, nullable=True)  # Porcentaje IVA (21, 10, 4)
    total_factura = Column(Float, nullable=True)
    
    # ⭐ MÉTODO PO: Desglose estructural de la factura ACTUAL (Línea base)
    coste_energia_actual = Column(Float, nullable=True)   # E_actual
    coste_potencia_actual = Column(Float, nullable=True)  # P_actual
    
    # P1: Periodo de facturación (obligatorio para comparar)
    periodo_dias = Column(Integer, nullable=True)

    # Estado
    estado_factura = Column(String, default="pendiente_datos")
    
    # ⭐ STEP 2: Validación Comercial
    ajustes_comerciales_json = Column(Text, nullable=True)  # JSON de AjustesComerciales
    total_ajustado = Column(Float, nullable=True)  # Total calculado post-ajustes (cifra reina)
    validado_step2 = Column(Boolean, default=False)  # Si pasó por Step 2
    
    # ⭐ BLOQUE 1 MVP CRM: Selección de oferta (FK en vez de JSON)
    selected_offer_json = Column(Text, nullable=True)  # Deprecated, usar selected_oferta_id
    selected_oferta_id = Column(BigInteger, ForeignKey("ofertas_calculadas.id"), nullable=True)
    selected_at = Column(DateTime(timezone=True), nullable=True)
    selected_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
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
    ofertas = relationship("OfertaCalculada", back_populates="comparativa", cascade="all, delete-orphan")


class OfertaCalculada(Base):
    """⭐ FIX P0-2: Ofertas persistidas generadas por el comparador"""
    __tablename__ = "ofertas_calculadas"
    
    id = Column(Integer, primary_key=True, index=True)
    comparativa_id = Column(Integer, ForeignKey("comparativas.id"), nullable=False)
    tarifa_id = Column(Integer, nullable=False)
    coste_estimado = Column(Float, nullable=True)
    ahorro_mensual = Column(Float, nullable=True)
    ahorro_anual = Column(Float, nullable=True)
    detalle_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación: Una oferta pertenece a una comparativa
    comparativa = relationship("Comparativa", back_populates="ofertas")


class ComisionGenerada(Base):
    """Comisiones generadas al seleccionar ofertas"""
    __tablename__ = "comisiones_generadas"
    
    id = Column(BigInteger, primary_key=True, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id"), nullable=False)
    factura_id = Column(Integer, ForeignKey("facturas.id"), nullable=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    asesor_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    oferta_id = Column(BigInteger, ForeignKey("ofertas_calculadas.id"), nullable=False)
    tarifa_id = Column(BigInteger, nullable=False)
    caso_id = Column(BigInteger, ForeignKey("casos.id"), nullable=True, index=True)
    comision_total_eur = Column(Numeric(12, 2), nullable=False)
    comision_source = Column(Text, nullable=False, default="manual")
    estado = Column(Text, nullable=False, default="pendiente", index=True)  # pendiente, validada, pagada, anulada, retenida, decomision
    fecha_prevista_pago = Column(Date, nullable=True)
    fecha_pago = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    factura = relationship("Factura")
    cliente = relationship("Cliente")
    asesor = relationship("User", foreign_keys=[asesor_id])
    caso = relationship("Caso", back_populates="comisiones")
    repartos = relationship("RepartoComision", back_populates="comision", cascade="all, delete-orphan")


class RepartoComision(Base):
    """Desglose de repartos de una comisión"""
    __tablename__ = "repartos_comision"
    
    id = Column(BigInteger, primary_key=True, index=True)
    comision_id = Column(BigInteger, ForeignKey("comisiones_generadas.id"), nullable=False, index=True)
    tipo_destinatario = Column(Text, nullable=False)  # asesor, ceo, colaborador
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)
    colaborador_id = Column(BigInteger, ForeignKey("colaboradores.id"), nullable=True, index=True)
    importe_eur = Column(Numeric(12, 2), nullable=False, default=0.00)
    porcentaje = Column(Numeric(6, 3), nullable=True)
    estado_pago = Column(Text, nullable=False, default="pendiente")
    fecha_pago = Column(Date, nullable=True)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    comision = relationship("ComisionGenerada", back_populates="repartos")
    user = relationship("User", foreign_keys=[user_id])
    colaborador = relationship("Colaborador", foreign_keys=[colaborador_id])


class Colaborador(Base):
    """Colaboradores externos (personas que reciben comisión sin acceso al sistema)"""
    __tablename__ = "colaboradores"
    
    id = Column(BigInteger, primary_key=True, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id"), nullable=False, index=True)
    nombre = Column(Text, nullable=False)
    telefono = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación
    company = relationship("Company")


class Caso(Base):
    """Caso comercial: contrato energético en seguimiento"""
    __tablename__ = "casos"
    
    id = Column(BigInteger, primary_key=True, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id"), nullable=False, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    asesor_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)
    colaborador_id = Column(BigInteger, ForeignKey("colaboradores.id"), nullable=True, index=True)
    factura_id = Column(Integer, ForeignKey("facturas.id"), nullable=True, index=True)
    comparativa_id = Column(Integer, ForeignKey("comparativas.id"), nullable=True)
    oferta_id = Column(BigInteger, ForeignKey("ofertas_calculadas.id"), nullable=True)
    tarifa_id = Column(BigInteger, nullable=True)
    cups = Column(String, nullable=True, index=True)
    servicio = Column(Text, default="luz")
    nueva_compania_text = Column(Text, nullable=True)
    antigua_compania_text = Column(Text, nullable=True)
    tarifa_nombre_text = Column(Text, nullable=True)
    canal = Column(Text, nullable=True)
    ahorro_estimado_anual = Column(Numeric(12, 2), nullable=True)
    notas = Column(Text, nullable=True)
    estado_comercial = Column(Text, nullable=False, default="lead", index=True)
    origen = Column(Text, nullable=False, default="manual")
    fecha_contacto = Column(DateTime(timezone=True), nullable=True)
    fecha_propuesta = Column(DateTime(timezone=True), nullable=True)
    fecha_firma = Column(DateTime(timezone=True), nullable=True)
    fecha_activacion = Column(DateTime(timezone=True), nullable=True)
    fecha_baja = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    company = relationship("Company")
    cliente = relationship("Cliente", back_populates="casos")
    asesor = relationship("User", foreign_keys=[asesor_user_id])
    colaborador = relationship("Colaborador", foreign_keys=[colaborador_id])
    factura = relationship("Factura", foreign_keys=[factura_id])
    comparativa = relationship("Comparativa", foreign_keys=[comparativa_id])
    oferta = relationship("OfertaCalculada", foreign_keys=[oferta_id])
    comisiones = relationship("ComisionGenerada", back_populates="caso")
    historial = relationship("HistorialCaso", back_populates="caso", cascade="all, delete-orphan")


class HistorialCaso(Base):
    """Timeline de eventos de un caso"""
    __tablename__ = "historial_caso"
    
    id = Column(BigInteger, primary_key=True, index=True)
    caso_id = Column(BigInteger, ForeignKey("casos.id"), nullable=False, index=True)
    tipo_evento = Column(Text, nullable=False)
    descripcion = Column(Text, nullable=False)
    estado_anterior = Column(Text, nullable=True)
    estado_nuevo = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON as text for compatibility
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relaciones
    caso = relationship("Caso", back_populates="historial")
    user = relationship("User")
