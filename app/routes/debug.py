from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.cups import normalize_cups, is_valid_cups, BLACKLIST
import os

router = APIRouter(prefix="/debug", tags=["debug"])


class CupsAuditRequest(BaseModel):
    text_input: str


@router.post("/cups-audit")
def audit_cups(request: CupsAuditRequest):
    """
    Endpoint de auditoría CUPS para debugging.
    Solo disponible con DEBUG=1 en variables de entorno.
    
    Simula exactamente el proceso de normalización y validación
    que debería ejecutarse en producción.
    """
    if os.getenv("DEBUG") != "1":
        raise HTTPException(
            status_code=403,
            detail="Endpoint solo disponible con DEBUG=1 en environment"
        )
    
    candidate_raw = request.text_input
    
    # Paso 1: Normalización
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
    
    # Paso 3: Validación Mod529
    is_valid = False
    if candidate_clean:
        is_valid = is_valid_cups(candidate_clean)
    
    # Paso 4: Decisión final
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
