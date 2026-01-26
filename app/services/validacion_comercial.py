"""
Servicio de Validación Comercial (STEP 2)
Calcula totales ajustados y genera warnings comerciales
"""

from typing import Dict, List, Tuple
from app.schemas.validacion import (
    AjustesComerciales,
    TotalesCalculados,
    MetadatosStep2,
    ValidacionComercialResponse
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def calcular_totales(
    total_original: float,
    ajustes: AjustesComerciales
) -> TotalesCalculados:
    """
    Calcula el total ajustado aplicando todos los descuentos excluidos.
    
    Fórmula:
    total_ajustado = total_original 
                     + bono_social (si activo)
                     + descuento_comercial (si aplica)
                     + servicios_vinculados (si se excluyen)
                     - alquiler (si se excluye)
    """
    exclusiones = 0.0
    
    # 1. Bono Social (sumar descuento para ver precio sin ayuda)
    if ajustes.bono_social.activo:
        exclusiones += ajustes.bono_social.descuento_estimado
    
    # 2. Descuento Comercial (sumar para ver precio real)
    if ajustes.descuento_comercial.importe > 0:
        exclusiones += ajustes.descuento_comercial.importe
    
    # 3. Servicios Vinculados (sumar si se excluyen)
    if ajustes.servicios_vinculados.excluir:
        exclusiones += ajustes.servicios_vinculados.importe
    
    # 4. Alquiler (restar si se excluye, aunque normalmente se mantiene)
    if ajustes.alquiler_contador.excluir:
        exclusiones -= ajustes.alquiler_contador.importe_ajustado
    
    total_ajustado = total_original + exclusiones
    
    # Determinar método
    metodo = "ajuste_comercial_transparente" if exclusiones != 0 else "sin_ajustes"
    
    return TotalesCalculados(
        total_original=total_original,
        total_descuentos_excluidos=exclusiones,
        total_ajustado_comparable=total_ajustado,
        metodo=metodo
    )


def generar_warnings(
    ajustes: AjustesComerciales,
    totales: TotalesCalculados
) -> List[str]:
    """
    Genera warnings comerciales según los ajustes aplicados.
    
    Warnings:
    - Descuento comercial > 5€
    - Bono Social activado manualmente sin detección OCR
    - Total ajustado < 50% del total original (posible error)
    - Servicios vinculados > 10€ sin descripción
    """
    warnings = []
    
    # Warning 1: Descuento significativo
    if ajustes.descuento_comercial.importe > 5.0:
        warnings.append(
            f"⚠️ Descuento comercial significativo ({ajustes.descuento_comercial.importe:.2f} €). "
            "Asegúrate de que sea temporal o el cliente tendrá expectativas incorrectas."
        )
    
    # Warning 2: Bono Social manual sin OCR
    if ajustes.bono_social.activo and ajustes.bono_social.origen == "manual":
        warnings.append(
            "⚠️ Bono Social activado manualmente. Verificar con el cliente que realmente aplica."
        )
    
    # Warning 3: Total ajustado sospechosamente bajo
    if totales.total_ajustado_comparable < (totales.total_original * 0.5):
        warnings.append(
            f"🚨 ALERTA: Total ajustado ({totales.total_ajustado_comparable:.2f} €) es menos de la mitad del original "
            f"({totales.total_original:.2f} €). Revisar ajustes."
        )
    
    # Warning 4: Servicios sin descripción
    if ajustes.servicios_vinculados.importe > 10.0 and not ajustes.servicios_vinculados.descripcion:
        warnings.append(
            "ℹ️ Servicios vinculados > 10€ sin descripción. Añade descripción para claridad en el PDF."
        )
    
    # Warning 5: Bono Social sin descuento estimado
    if ajustes.bono_social.activo and ajustes.bono_social.descuento_estimado == 0:
        warnings.append(
            "⚠️ Bono Social activo pero sin descuento estimado. Calcular impacto para comparación justa."
        )
    
    return warnings


def generar_notas_pdf(ajustes: AjustesComerciales) -> Dict[str, str]:
    """
    Genera notas automáticas para el PDF según los ajustes aplicados.
    
    Returns:
        Dict con claves: 'metodologia', 'notas_pie', 'aviso_ahorro'
    """
    notas = {
        "metodologia": "",
        "notas_pie": [],
        "aviso_ahorro": ""
    }
    
    # Nota de metodología (se muestra entre Tabla 1 y Tabla 2)
    ajustes_texto = []
    
    if ajustes.bono_social.activo:
        ajustes_texto.append(
            f"⭐ Bono Social (-{ajustes.bono_social.descuento_estimado:.2f} €)\n"
            "   Tu factura incluye Bono Social, una ayuda pública que reduce\n"
            "   un 40% el coste de la energía. Para comparar ofertas de mercado\n"
            "   libre, excluimos este descuento."
        )
        notas["notas_pie"].append(
            "*Comparación realizada sin Bono Social para reflejar precios de mercado. "
            "Si eres beneficiario, consulta si puedes trasladar la ayuda a la nueva tarifa."
        )
    
    if ajustes.descuento_comercial.importe > 0:
        ajustes_texto.append(
            f"⚠️ Descuento Comercial Temporal (-{ajustes.descuento_comercial.importe:.2f} €)\n"
            f'   "{ajustes.descuento_comercial.descripcion}"\n'
            "   Tu tarifa actual tiene un descuento promocional que expirará.\n"
            "   Comparamos sin descuento para estimar tu coste real a largo plazo."
        )
        notas["notas_pie"].append(
            "*Tu tarifa actual incluye descuentos promocionales que expiran. "
            "El ahorro se calcula respecto al precio final sin descuento."
        )
    
    if ajustes.servicios_vinculados.excluir and ajustes.servicios_vinculados.importe > 0:
        desc = ajustes.servicios_vinculados.descripcion or "Servicios adicionales"
        ajustes_texto.append(
            f"ℹ️ Servicios Vinculados (-{ajustes.servicios_vinculados.importe:.2f} €)\n"
            f"   {desc}\n"
            "   Servicios extras no incluidos en la comparación estructural."
        )
        notas["notas_pie"].append(
            "*Servicios adicionales (seguros, mantenimiento, etc.) no incluidos en la comparación."
        )
    
    if ajustes.alquiler_contador.importe_original != ajustes.alquiler_contador.importe_ajustado:
        ajustes_texto.append(
            f"ℹ️ Alquiler Contador ({ajustes.alquiler_contador.importe_ajustado:.2f} €) - Ajustado\n"
            f"   Importe corregido desde {ajustes.alquiler_contador.importe_original:.2f} €."
        )
        notas["notas_pie"].append(
            f"*Alquiler del contador ajustado por el asesor. Importe original: {ajustes.alquiler_contador.importe_original:.2f} €"
        )
    
    # Construir texto de metodología
    if ajustes_texto:
        notas["metodologia"] = (
            "AJUSTES REALIZADOS:\n\n" + "\n\n".join(ajustes_texto)
        )
    else:
        notas["metodologia"] = "✓ Comparación directa (sin ajustes necesarios)"
    
    # Aviso en Tabla 3 (Ahorro)
    if ajustes.bono_social.activo:
        notas["aviso_ahorro"] = (
            "⚠️ IMPORTANTE: Este ahorro se calcula respecto al precio de mercado\n"
            "   sin ayudas públicas. Si mantienes el Bono Social en tu nueva tarifa,\n"
            "   tu ahorro real será diferente. Consulta con tu asesor."
        )
    elif ajustes.descuento_comercial.importe > 5.0:
        notas["aviso_ahorro"] = (
            "ℹ️ Tu tarifa actual tiene un descuento que expira. Este ahorro\n"
            "   refleja tu coste real comparado con el precio sin descuento."
        )
    
    return notas


def validar_factura_comercialmente(
    factura,
    ajustes: AjustesComerciales,
    modo: str = "asesor"
) -> Tuple[ValidacionComercialResponse, List[str]]:
    """
    Valida comercialmente una factura aplicando ajustes y generando warnings.
    
    Args:
        factura: Objeto Factura de la DB
        ajustes: Ajustes comerciales a aplicar
        modo: "asesor" o "cliente"
    
    Returns:
        Tupla (response, warnings)
    """
    # 1. Extraer base de factura (datos bloqueados)
    base_factura = {
        "total_original": float(factura.total_factura or 0.0),
        "consumos": {
            "p1_kwh": float(factura.consumo_p1_kwh or 0.0),
            "p2_kwh": float(factura.consumo_p2_kwh or 0.0),
            "p3_kwh": float(factura.consumo_p3_kwh or 0.0),
        },
        "potencias": {
            "p1_kw": float(factura.potencia_p1_kw or 0.0),
            "p2_kw": float(factura.potencia_p2_kw or 0.0),
        },
        "iva_porcentaje": float(factura.iva_porcentaje or 21.0),
        "impuesto_electrico": float(factura.impuesto_electrico or 0.0),
        "iva_importe": float(factura.iva or 0.0),
        "periodo_dias": int(factura.periodo_dias or 30),
    }
    
    # 2. Calcular totales
    totales = calcular_totales(base_factura["total_original"], ajustes)
    
    # 3. Generar warnings
    warnings = generar_warnings(ajustes, totales)
    
    # 4. Metadatos
    metadatos = MetadatosStep2(
        validado_por="asesor" if modo == "asesor" else "cliente",
        validado_at=datetime.now(),
        avisos_mostrados=warnings,
        modo=modo
    )
    
    # 5. Ready to compare?
    ready = (
        base_factura["total_original"] > 0 and
        totales.total_ajustado_comparable > 0 and
        base_factura["consumos"]["p1_kwh"] > 0
    )
    
    response = ValidacionComercialResponse(
        factura_id=factura.id,
        base_factura=base_factura,
        ajustes_comerciales=ajustes,
        totales_calculados=totales,
        metadatos_step2=metadatos,
        warnings=warnings,
        ready_to_compare=ready
    )
    
    return response, warnings
