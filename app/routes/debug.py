from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.utils.cups import normalize_cups, is_valid_cups, BLACKLIST
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.conn import get_db
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])


class CupsAuditRequest(BaseModel):
    text_input: str


@router.post("/cups-audit")
def audit_cups(request: CupsAuditRequest):
    """
    Endpoint de auditorÃ­a CUPS para debugging.
    Solo disponible con DEBUG=1 en variables de entorno.
    
    Simula exactamente el proceso de normalizaciÃ³n y validaciÃ³n
    que deberÃ­a ejecutarse en producciÃ³n.
    """
    if os.getenv("DEBUG") != "1":
        raise HTTPException(
            status_code=403,
            detail="Endpoint solo disponible con DEBUG=1 en environment"
        )
    
    candidate_raw = request.text_input
    
    # Paso 1: NormalizaciÃ³n
    candidate_clean = normalize_cups(candidate_raw)
    
    # Paso 2: Verificar blacklist (manual check para debugging)
    blacklist_hit = False
    matched_word = None
    text_upper = candidate_raw.upper()
    
    for word in BLACKLIST:
        if word in text_upper:
            blacklist_hit = True
            matched_word = word
            break
    
    # Paso 3: ValidaciÃ³n Mod529
    is_valid = False
    if candidate_clean:
        is_valid = is_valid_cups(candidate_clean)
    
    # Paso 4: DecisiÃ³n final
    final_cups = candidate_clean if (candidate_clean and is_valid) else None
    
    return {
        "candidate_raw": candidate_raw,
        "candidate_clean": candidate_clean,
        "blacklist_hit": blacklist_hit,
        "blacklist_word": matched_word,
        "length_check": len(candidate_clean) if candidate_clean else 0,
        "length_valid": 20 <= len(candidate_clean) <= 22 if candidate_clean else False,
        "is_valid_mod529": is_valid,
        "final_cups": final_cups,
        "rejection_reason": (
            f"Blacklist hit: {matched_word}" if blacklist_hit
            else "Invalid length" if candidate_clean and not (20 <= len(candidate_clean) <= 22)
            else "Failed Mod529" if candidate_clean and not is_valid
            else None if final_cups
            else "Normalization returned None"
        )
    }

# ============ RUTAS DE DEBUGGING PARA COMPARADOR ============

@router.get("/tarifas/stats")
def tarifas_stats(db: Session = Depends(get_db)):
    """
    Retorna estadÃ­sticas sobre las tarifas en la BD.
    Ãštil para debuggear problemas de comparador.
    
    Disponible en: GET /debug/tarifas/stats
    """
    try:
        # Total de tarifas por ATR
        result = db.execute(text("""
            SELECT atr, COUNT(*) as count FROM tarifas GROUP BY atr
        """))
        atr_stats = {row[0]: row[1] for row in result.fetchall()}
        
        # Muestras de precios por ATR
        atr_prices = {}
        for atr in ['2.0TD', '3.0TD']:
            result = db.execute(text(f"""
                SELECT 
                    MIN(energia_p1_eur_kwh) as min_ep1,
                    MAX(energia_p1_eur_kwh) as max_ep1,
                    AVG(energia_p1_eur_kwh) as avg_ep1,
                    MIN(potencia_p1_eur_kw_dia) as min_pp1,
                    MAX(potencia_p1_eur_kw_dia) as max_pp1,
                    AVG(potencia_p1_eur_kw_dia) as avg_pp1
                FROM tarifas 
                WHERE atr = '{atr}'
            """))
            row = result.fetchone()
            if row:
                atr_prices[atr] = {
                    'energia_p1': {'min': row[0], 'max': row[1], 'avg': row[2]},
                    'potencia_p1': {'min': row[3], 'max': row[4], 'avg': row[5]}
                }
        
        return {
            "status": "success",
            "tarifas_por_atr": atr_stats,
            "precios_muestra": atr_prices,
            "mensaje": "Usa esta informaciÃ³n para debuggear problemas de comparador"
        }
    except Exception as e:
        logger.error(f"Error en tarifas_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comparador/factura/{factura_id}")
def debug_comparador(factura_id: int, db: Session = Depends(get_db)):
    """
    Ejecuta el comparador en modo debug y retorna anÃ¡lisis detallado.
    
    Ãštil para investigar por quÃ© no hay ofertas o por quÃ© el ahorro es negativo.
    
    Disponible en: POST /debug/comparador/factura/{factura_id}
    """
    from app.db.models import Factura
    from app.services.comparador import compare_factura
    
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail=f"Factura {factura_id} no encontrada")
    
    try:
        # Ejecutar comparador con logging completo
        result = compare_factura(factura, db)
        
        # Enriquecer resultado con anÃ¡lisis
        analysis = {
            "factura_id": factura_id,
            "success": True,
            "ofertas_totales": len(result.get('offers', [])),
            "ofertas_con_ahorro": len([o for o in result.get('offers', []) if o.get('saving_amount_annual', 0) > 0]),
            "ofertas_sin_ahorro": len([o for o in result.get('offers', []) if o.get('saving_amount_annual', 0) <= 0]),
            "baseline_actual": result.get('current_total'),
            "baseline_method": result.get('baseline_method'),
            "inputs": {
                "atr": factura.atr,
                "total_factura": factura.total_factura,
                "consumo_total": (factura.consumo_p1_kwh or 0) + (factura.consumo_p2_kwh or 0) + (factura.consumo_p3_kwh or 0),
                "periodo_dias": factura.periodo_dias,
                "alquiler_contador": factura.alquiler_contador,
                "iva_porcentaje": factura.iva_porcentaje,
            }
        }
        
        # Si hay ofertas, mostrar las mejores y peores
        if result.get('offers'):
            offers_sorted = sorted(result['offers'], key=lambda x: x.get('saving_amount_annual', 0), reverse=True)
            analysis["mejores_ofertas"] = offers_sorted[:3]
            analysis["peores_ofertas"] = offers_sorted[-3:]
        else:
            analysis["mejores_ofertas"] = []
            analysis["peores_ofertas"] = []
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error en debug_comparador para factura {factura_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "tipo": type(e).__name__,
            "mensaje": "Ver logs del servidor para mÃ¡s detalles"
        })

