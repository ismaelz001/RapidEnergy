# 🔍 CUPS AUDIT REPORT - Diagnóstico Crítico
**Fecha:** 2026-01-12  
**Objetivo:** Localizar origen de valores basura en campo CUPS (ej: "ESUMENDELAFACTURA")

---

## A) MAPA DE FLUJO COMPLETO

### 1. Diagrama Simplificado

```
┌─────────────────────────────────────────────────────────────────┐
│ UPLOAD REQUEST                                                   │
│  POST /webhook/upload_v2                                         │
│  File: factura.pdf                                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ OCR ENGINE (app/services/ocr.py::extract_data_from_pdf)         │
│                                                                   │
│  1. ¿GEMINI_API_KEY presente? → extract_data_with_gemini()      │
│     └─ Línea 824-829: Prioridad Gemini 1.5 Flash               │
│     └─ Línea 799-806: normalize_cups() + is_valid_cups() ✅    │
│                                                                   │
│  2. Si falla/no existe → pypdf.PdfReader()                       │
│     └─ Línea 832-843: parse_invoice_text(full_text)             │
│     └─ Línea 258-282: CUPS validation con normalize_cups() ✅   │
│                                                                   │
│  3. Output: ocr_data dict                                        │
│     └─ ocr_data["cups"] = None | "ES0022..." | "ESUMEN..." ⚠️  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ WEBHOOK NORMALIZATION (app/routes/webhook.py::process_factura)  │
│                                                                   │
│  Línea 154: cups_extraido = normalize_cups(ocr_data["cups"])    │
│             ⚠️ USA FUNCIÓN LOCAL (sin blacklist)                │
│                                                                   │
│  Línea 281: Factura(cups=normalize_cups(ocr_data["cups"]))     │
│             ⚠️ SEGUNDA LLAMADA a función incorrecta              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ DATABASE COMMIT                                                  │
│  db.add(nueva_factura)                                           │
│  db.commit() → CUPS BASURA PERSISTIDO ❌                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## B) TABLA DE REFERENCIAS CUPS (Exhaustiva)

| Archivo | Línea | Función | Rol | Escribe CUPS | Valida CUPS | Notas |
|---------|-------|---------|-----|--------------|-------------|-------|
| **app/utils/cups.py** | 6 | `normalize_cups()` | ✅ Normalización + Blacklist | No | Sí | **IMPLEMENTACIÓN CORRECTA** |
| **app/utils/cups.py** | 33 | `is_valid_cups()` | Validación Mod529 | No | Sí | Algoritmo oficial |
| **app/routes/webhook.py** | 84 | `normalize_cups()` | ⚠️ Normalización PARCIAL | No | **NO** | **SIN BLACKLIST (BUG)** |
| **app/routes/webhook.py** | 154 | (llamada) | Asigna `cups_extraido` | No | No | Usa función local defectuosa |
| **app/routes/webhook.py** | 281 | (llamada) | **PERSISTENCIA** | **SÍ** | No | **ESCRIBE A BD SIN VALIDAR** |
| **app/routes/webhook.py** | 355 | (llamada) | Update manual | Sí | No | Endpoint PUT |
| **app/services/ocr.py** | 220 | `from app.utils.cups import...` | Importa versión correcta | No | No | ✅ Importación correcta |
| **app/services/ocr.py** | 264 | (llamada) | Normaliza candidatos | No | Sí | Dentro de `parse_structured_fields` |
| **app/services/ocr.py** | 271 | `is_valid_cups()` | Valida con Mod529 | No | Sí | ✅ Validación activa |
| **app/services/ocr.py** | 799 | (llamada Gemini) | Normaliza output Gemini | No | Sí | ✅ Doble verificación |
| **app/services/ocr.py** | 802 | `is_valid_cups()` | Valida output Gemini | No | Sí | ✅ Filtro final |

### Regex Detectados (ES*)

| Archivo | Línea | Regex | Propósito | Validado después? |
|---------|-------|-------|-----------|-------------------|
| app/services/ocr.py | 258 | `(ES[A-Z0-9\-\s]{18,25})` | Buscar candidatos | ✅ Sí (normalize + is_valid) |
| app/utils/cups.py | 49 | `^ES(\d{16})([A-Z]{2})(\d[FPCRXYZ])?$` | Validación estricta Mod529 | N/A (es el validador) |

### Blacklist

**Ubicación:** `app/utils/cups.py` línea 4  
```python
BLACKLIST = ["FACTURA", "RESUMEN", "TOTAL", "CLIENTE", "SUMINISTRO", "TELEFONO", "ELECTRICIDAD"]
```

**Efecto:**
- ✅ Rechaza "ESUMENDELAFACTURA" (contiene "FACTURA")
- ✅ Rechaza "ESUMERESUMENDELCONTRATO" (contiene "RESUMEN")
- ✅ Rechaza "ESTOTAL123..." (contiene "TOTAL")

**PROBLEMA:** Esta blacklist solo se aplica en `app/utils/cups.py::normalize_cups()`, NO en `app/routes/webhook.py::normalize_cups()`.

---

## C) CONCLUSIÓN: CAUSA RAÍZ

### ❌ **BUG #1: Función Duplicada Sin Blacklist**

**Archivo:** `app/routes/webhook.py` líneas 84-91

```python
def normalize_cups(cups: str) -> str:
    """Normaliza CUPS: uppercase, quita espacios/guiones/puntos. NO rechaza nada."""
    if not cups:
        return None
    import re
    cleaned = cups.strip().upper()
    cleaned = re.sub(r'[\s\-.]', '', cleaned)  # Solo limpia
    return cleaned if cleaned else None         # ❌ NO HAY BLACKLIST
```

### ✅ **Versión Correcta (NO usada en webhook)**

**Archivo:** `app/utils/cups.py` líneas 6-31

```python
def normalize_cups(text: str) -> str | None:
    if not text:
        return None
    
    cleaned = text.upper()
    cleaned = re.sub(r"[\s\-\.\n]", "", cleaned)
    
    # ✅ CHECK BLACKLIST
    for bad_word in BLACKLIST:
        if bad_word in cleaned:
            return None  # ← RECHAZA BASURA
            
    # ✅ VALIDAR LONGITUD
    if len(cleaned) < 20 or len(cleaned) > 22:
        return None
    
    return cleaned
```

---

## D) FLUJO DE DATOS REAL (Con Bug)

### Escenario: Factura con "RESUMEN DE LA FACTURA" en el texto

1. **OCR Gemini devuelve:**
   ```json
   {
     "cups": "ESUMENDELAFACTURA"  // ← Match parcial de "RESUMEN DE LA FACTURA"
   }
   ```
   (Nota: Gemini SÍ aplica `normalize_cups` + `is_valid_cups` líneas 799-806, pero si el output de Gemini ya viene contaminado con este valor, sigue adelante)

2. **Webhook línea 154:**
   ```python
   cups_extraido = normalize_cups(ocr_data.get("cups"))
   # normalize_cups("ESUMENDELAFACTURA") → "ESUMENDELAFACTURA" ❌
   # (sin rechazo, sin blacklist)
   ```

3. **Persistencia línea 281:**
   ```python
   nueva_factura = Factura(
       cups=normalize_cups(ocr_data.get("cups")),  # ← "ESUMENDELAFACTURA"
       ...
   )
   db.add(nueva_factura)
   db.commit()  # ❌ BASURA GUARDADA
   ```

---

## E) VERIFICACIÓN: Motor OCR Usado

**Prioridad de motores** (líneas 820-843 de `ocr.py`):

1. **Gemini 1.5 Flash** (si `GEMINI_API_KEY` presente)
   - Línea 824-829
   - Aplica validación CUPS (líneas 799-806) ✅
   - PERO: si Gemini extrae "ESUMEN..." del PDF, lo pasa al webhook

2. **pypdf + parse_invoice_text()** (fallback)
   - Línea 832-843
   - Aplica validación CUPS (líneas 258-282) ✅
   - Busca candidatos con regex, normaliza, valida Mod529

3. **Google Vision** (solo si falla pypdf en imágenes)
   - Línea 851+
   - También usa `parse_invoice_text()` ✅

**Conclusión:** Los **3 motores SÍ validan correctamente** el CUPS en `ocr.py`, pero el **webhook re-normaliza con función defectuosa** antes de guardar.

---

## F) CAUSA FINAL

### La respuesta es **#5 de tu lista**:

> ✅ **HAY DOS PARSEOS DISTINTOS y el INCORRECTO es el que ESCRIBE a BD**

**Detalle:**
1. `ocr.py` usa `app.utils.cups.normalize_cups` (CON blacklist, CON validación longitud)
2. `webhook.py` redefine `normalize_cups` localmente (SIN blacklist, SIN validación)
3. El valor que se guarda en BD es el output de la función #2 (defectuosa)

### ¿Por qué ocurrió esto?

Probablemente un **refactor incompleto**:
- Se creó `app/utils/cups.py` con la lógica correcta
- `ocr.py` se actualizó para importarla
- `webhook.py` nunca se refactorizó, mantuvo su versión local antigua

---

## G) LÍNEAS EXACTAS DE ESCRITURA A BD

| Línea | Código | Función Local Usada |
|-------|--------|---------------------|
| 154 | `cups_extraido = normalize_cups(...)` | ❌ Sí (local webhook) |
| 281 | `Factura(cups=normalize_cups(...))` | ❌ Sí (local webhook) |
| 355 | `value = normalize_cups(value)` (PUT update) | ❌ Sí (local webhook) |

**CONFIRMACIÓN:** Las 3 llamadas en `webhook.py` usan la función local defectuosa definida en línea 84.

---

## H) PRÓXIMOS PASOS (Recomendaciones)

### 1. **FIX INMEDIATO (P0)**

**Archivo:** `app/routes/webhook.py`

```diff
- def normalize_cups(cups: str) -> str:
-     """Normaliza CUPS: uppercase, quita espacios/guiones/puntos. NO rechaza nada."""
-     if not cups:
-         return None
-     import re
-     cleaned = cups.strip().upper()
-     cleaned = re.sub(r'[\s\-.]', '', cleaned)
-     return cleaned if cleaned else None
```

Reemplazar con:

```python
# Importar al principio del archivo
from app.utils.cups import normalize_cups

# ELIMINAR la función local (líneas 84-91)
```

### 2. **Verificación adicional (P1)**

Añadir log de auditoría en línea 281:

```python
cups_final = normalize_cups(ocr_data.get("cups"))
print(f"[CUPS-AUDIT] OCR_IN={ocr_data.get('cups')} → NORMALIZED={cups_final}")
nueva_factura = Factura(cups=cups_final, ...)
```

### 3. **Reparar datos históricos (P2)**

Ejecutar script de limpieza en BD:

```sql
UPDATE facturas 
SET cups = NULL 
WHERE cups LIKE '%FACTURA%' 
   OR cups LIKE '%RESUMEN%' 
   OR cups LIKE '%TOTAL%';
```

---

## I) ENTREGA EJECUTABLE

Crear endpoint de debug (como solicitaste en punto D):

**Archivo:** `app/routes/debug.py` (nuevo)

```python
from fastapi import APIRouter
from app.utils.cups import normalize_cups, is_valid_cups

router = APIRouter(prefix="/debug/cups-audit", tags=["debug"])

@router.post("/")
def audit_cups(text_input: str):
    """
    Endpoint de auditoría CUPS.
    Requiere DEBUG=1 en env.
    """
    import os
    if os.getenv("DEBUG") != "1":
        return {"error": "Endpoint solo disponible con DEBUG=1"}
    
    # Simular proceso actual
    candidate_raw = text_input
    candidate_clean = normalize_cups(candidate_raw)
    
    # Verificar blacklist
    from app.utils.cups import BLACKLIST
    blacklist_hit = False
    matched_word = None
    for word in BLACKLIST:
        if word in candidate_raw.upper():
            blacklist_hit = True
            matched_word = word
            break
    
    # Validar
    is_valid = is_valid_cups(candidate_clean) if candidate_clean else False
    
    return {
        "candidate_raw": candidate_raw,
        "candidate_clean": candidate_clean,
        "blacklist_hit": blacklist_hit,
        "blacklist_word": matched_word,
        "is_valid_mod529": is_valid,
        "final_cups": candidate_clean if is_valid else None
    }
```

**Test:**

```bash
curl -X POST http://localhost:8000/debug/cups-audit \
  -H "Content-Type: application/json" \
  -d '{"text_input": "ESUMENDELAFACTURA"}'
```

**Output Esperado:**

```json
{
  "candidate_raw": "ESUMENDELAFACTURA",
  "candidate_clean": null,
  "blacklist_hit": true,
  "blacklist_word": "FACTURA",
  "is_valid_mod529": false,
  "final_cups": null
}
```

---
