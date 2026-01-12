# CUPS TELEMETRY PATCH
# Añade 4 logs estratégicos sin cambiar lógica de negocio

## LOG #1: Antes de llamar al motor OCR
**Archivo:** `app/services/ocr.py`
**Función:** `extract_data_from_pdf()`
**Línea:** ~820 (antes de línea 824)

```python
def extract_data_from_pdf(file_bytes: bytes) -> dict:
    import os
    is_pdf = file_bytes.startswith(b"%PDF")
    
    # [CUPS-AUDIT] LOG #1: Motor OCR previsto
    gemini_key_present = bool(os.getenv("GEMINI_API_KEY"))
    app_version = os.getenv("APP_VERSION", "unknown")
    print(f"""
[CUPS-AUDIT] #1 - OCR ENGINE SELECTION
  Motor previsto: {'GEMINI-1.5-FLASH' if gemini_key_present else 'PYPDF/VISION'}
  GEMINI_API_KEY presente: {gemini_key_present}
  APP_VERSION: {app_version}
  Tipo archivo: {'PDF' if is_pdf else 'IMAGE'}
""")
    
    # INTENTAR GEMINI PRIMERO (Premium)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        ...
```

---

## LOG #2: Resultado crudo del OCR
**Archivo:** `app/services/ocr.py`
**Función:** `parse_structured_fields()` dentro de `parse_invoice_text()`
**Línea:** ~280 (después de detectar CUPS)

```python
def parse_structured_fields(raw_text: str) -> dict:
    ...
    for cand in candidates:
        print(f"🔍 CUPS CANDIDATE: {cand}")
        norm = normalize_cups(cand)
        ...
    
    # [CUPS-AUDIT] LOG #2: Context del match
    if valid_cups_found:
        # Buscar contexto (200 chars alrededor)
        match_idx = raw_text.find(valid_cups_found[:10])  # Buscar primeros 10 chars
        if match_idx >= 0:
            context_start = max(0, match_idx - 100)
            context_end = min(len(raw_text), match_idx + 100)
            context = raw_text[context_start:context_end]
        else:
            context = raw_text[:200]  # Primeros 200 si no encuentra match
    else:
        context = raw_text[:200]
    
    print(f"""
[CUPS-AUDIT] #2 - OCR RAW RESULT
  Total texto OCR: {len(raw_text)} chars
  CUPS detectado: {valid_cups_found}
  Contexto (200 chars): {context}
  Candidatos encontrados: {len(candidates)}
""")
```

---

## LOG #3: Paso de parseo CUPS
**Archivo:** `app/services/ocr.py`
**Función:** `parse_structured_fields()` (loop de candidatos)
**Línea:** ~264-278 (modificar loop existente)

```python
for cand in candidates:
    # Ya existe: print(f"🔍 CUPS CANDIDATE: {cand}")
    
    # [CUPS-AUDIT] LOG #3: Validación paso a paso
    norm = normalize_cups(cand)
    
    # Verificar blacklist manualmente para logging
    from app.utils.cups import BLACKLIST
    blacklist_hit = False
    blacklist_word = None
    for word in BLACKLIST:
        if word in cand.upper():
            blacklist_hit = True
            blacklist_word = word
            break
    
    print(f"""
[CUPS-AUDIT] #3 - CUPS PARSING
  candidate_raw: {cand}
  candidate_clean: {norm}
  regex_usado: (ES[A-Z0-9\\-\\s]{{18,25}})
  blacklist_hit: {blacklist_hit}
  blacklist_word: {blacklist_word if blacklist_hit else 'N/A'}
  longitud_normalizado: {len(norm) if norm else 0}
  longitud_valida: {20 <= len(norm) <= 22 if norm else False}
""")
    
    # Validar Módulo 529
    is_valid = is_valid_cups(norm) if norm else False
    print(f"🔢 VALIDATION RESULT: {is_valid}")
    ...
```

---

## LOG #4: Persistencia
**Archivo:** `app/routes/webhook.py`
**Función:** `process_factura()` (endpoint `/upload_v2`)
**Línea:** ~281 (antes de crear Factura)

```python
# 4. Crear factura vinculada
cups_final_db = normalize_cups(ocr_data.get("cups"))

# [CUPS-AUDIT] LOG #4: Persistencia
print(f"""
[CUPS-AUDIT] #4 - DATABASE PERSISTENCE
  factura_id: (pending commit)
  cups_ocr_input: {ocr_data.get('cups')}
  cups_final_db: {cups_final_db}
  missing_fields: {ocr_data.get('missing_fields', [])}
  atr: {ocr_data.get('atr')}
  total_factura: {ocr_data.get('total_factura')}
""")

nueva_factura = Factura(
    filename=file.filename,
    cups=cups_final_db,  # ← valor que se escribe
    ...
)

db.add(nueva_factura)
db.commit()
db.refresh(nueva_factura)

print(f"[CUPS-AUDIT] #4 - COMMITTED factura_id={nueva_factura.id}")
```

---

## IMPORTANTE: NO imprimir API keys

En todos los logs, usar:
- `bool(os.getenv("GEMINI_API_KEY"))` en lugar del valor
- Limitar texto OCR a 200 caracteres
- NO incluir `file_bytes` completo

## Prefijo obligatorio

Todos los logs deben comenzar con `[CUPS-AUDIT]` para facilitar filtrado en Render.
