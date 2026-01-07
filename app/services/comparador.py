"""
Servicio de comparación de tarifas energéticas.
Versión 1: Ofertas hardcoded para MVP demo.
"""

from typing import List, Dict, Any


def compare_factura(factura) -> Dict[str, Any]:
    """
    Genera 3 ofertas mock basadas en la factura actual.
    
    Args:
        factura: Objeto Factura de SQLAlchemy con al menos .total_factura
    
    Returns:
        Dict con factura_id, current_total, y lista de ofertas
    """
    
    # Validar que existe total_factura
    current_total = factura.total_factura
    if current_total is None or current_total <= 0:
        raise ValueError("La factura no tiene un total válido para comparar")
    
    # Proveedores mock con descuentos fijos (deterministas)
    # Descuento = porcentaje sobre el total actual
    providers = [
        {
            "provider": "Endesa Energía XXI",
            "plan_name": "Tarifa Plana 24h",
            "discount_percent": 15.0,  # Mejor ahorro
            "commission_percent": 3.0,
            "tag": "best_saving"
        },
        {
            "provider": "Iberdrola One Luz",
            "plan_name": "Plan Equilibrio",
            "discount_percent": 12.0,  # Balanceado
            "commission_percent": 4.5,
            "tag": "balanced"
        },
        {
            "provider": "Naturgy Gas y Luz",
            "plan_name": "Más Ahorro Plus",
            "discount_percent": 10.0,  # Mejor comisión
            "commission_percent": 6.0,
            "tag": "best_commission"
        }
    ]
    
    offers = []
    
    for provider_data in providers:
        # Calcular ahorro basado en descuento
        discount_amount = current_total * (provider_data["discount_percent"] / 100)
        estimated_total = current_total - discount_amount
        
        # Calcular comisión sobre el ahorro anual (estimamos x12 meses)
        annual_saving = discount_amount * 12
        commission = annual_saving * (provider_data["commission_percent"] / 100)
        
        offer = {
            "provider": provider_data["provider"],
            "plan_name": provider_data["plan_name"],
            "estimated_total": round(estimated_total, 2),
            "saving_amount": round(discount_amount, 2),
            "saving_percent": round(provider_data["discount_percent"], 2),
            "commission": round(commission, 2),
            "tag": provider_data["tag"]
        }
        
        offers.append(offer)
    
    return {
        "factura_id": factura.id,
        "current_total": round(current_total, 2),
        "offers": offers
    }
