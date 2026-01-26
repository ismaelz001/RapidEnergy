"""
Schemas Pydantic para STEP 2: Validación Comercial
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class AjusteBonSocial(BaseModel):
    """Bono Social: Ayuda pública que reduce 40% coste energía"""
    activo: bool = Field(default=False, description="Si la factura tiene Bono Social")
    descuento_estimado: float = Field(default=0.0, ge=0, description="Descuento estimado en €")
    origen: Literal["ocr_auto", "manual"] = Field(default="ocr_auto")
    nota_pdf: Optional[str] = Field(default=None, description="Nota explicativa para PDF")


class AjusteAlquilerContador(BaseModel):
    """Alquiler equipo de medida"""
    importe_original: float = Field(default=0.0, ge=0, description="Importe del OCR")
    importe_ajustado: float = Field(default=0.0, ge=0, description="Importe corregido si aplica")
    excluir: bool = Field(default=False, description="Si se excluye de la comparación")
    origen: Literal["ocr", "manual"] = Field(default="ocr")
    nota_pdf: Optional[str] = None


class AjusteServiciosVinculados(BaseModel):
    """Servicios extras: seguros, mantenimiento, packs luz+gas"""
    descripcion: str = Field(default="", max_length=200)
    importe: float = Field(default=0.0, ge=0)
    excluir: bool = Field(default=False)
    origen: Literal["manual"] = Field(default="manual")
    nota_pdf: Optional[str] = None


class AjusteDescuentoComercial(BaseModel):
    """Descuentos promocionales temporales"""
    descripcion: str = Field(default="", max_length=200, description="Ej: 'Descuento 10% primer año'")
    importe: float = Field(default=0.0, ge=0)
    temporal: bool = Field(default=True, description="Si el descuento expira")
    origen: Literal["manual"] = Field(default="manual")
    nota_pdf: Optional[str] = None


class AjustesComerciales(BaseModel):
    """Conjunto de ajustes comerciales aplicables"""
    bono_social: AjusteBonSocial = Field(default_factory=AjusteBonSocial)
    alquiler_contador: AjusteAlquilerContador = Field(default_factory=AjusteAlquilerContador)
    servicios_vinculados: AjusteServiciosVinculados = Field(default_factory=AjusteServiciosVinculados)
    descuento_comercial: AjusteDescuentoComercial = Field(default_factory=AjusteDescuentoComercial)


class TotalesCalculados(BaseModel):
    """Totales calculados automáticamente"""
    total_original: float = Field(description="Total de la factura original")
    total_descuentos_excluidos: float = Field(description="Suma de todos los ajustes")
    total_ajustado_comparable: float = Field(description="Total final para comparar (cifra reina)")
    metodo: Literal["sin_ajustes", "ajuste_comercial_transparente"] = Field(default="sin_ajustes")


class MetadatosStep2(BaseModel):
    """Metadatos de auditoría"""
    validado_por: Literal["asesor", "auto", "cliente"] = Field(default="auto")
    validado_at: Optional[datetime] = None
    avisos_mostrados: List[str] = Field(default_factory=list, description="Warnings mostrados al asesor")
    modo: Literal["asesor", "cliente"] = Field(default="cliente")


class ValidacionComercialRequest(BaseModel):
    """Request body para PUT /facturas/{id}/validar"""
    ajustes_comerciales: AjustesComerciales
    modo: Literal["asesor", "cliente"] = Field(default="asesor")


class ValidacionComercialResponse(BaseModel):
    """Response completo de validación comercial"""
    factura_id: int
    base_factura: dict  # Datos bloqueados (consumos, potencias, IVA, etc)
    ajustes_comerciales: AjustesComerciales
    totales_calculados: TotalesCalculados
    metadatos_step2: MetadatosStep2
    warnings: List[str] = Field(default_factory=list, description="Warnings generados")
    ready_to_compare: bool = Field(description="Si está lista para comparar")


class FacturaUpdate(BaseModel):
    """Schema para updates parciales de factura (ya existente, extendido)"""
    # ... campos existentes ...
    
    # Nuevos campos para Step 2
    ajustes_comerciales_json: Optional[str] = Field(default=None, description="JSON de AjustesComerciales")
    total_ajustado: Optional[float] = Field(default=None, description="Total calculado post-ajustes")
    validado_step2: bool = Field(default=False, description="Si pasó por Step 2")
