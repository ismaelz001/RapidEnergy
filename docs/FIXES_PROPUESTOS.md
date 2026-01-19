# 🔧 FIXES QUIRÚRGICOS — PRIORIDAD P0 Y P1

## ESTADO ACTUAL
- ✅ **P0-1 FIXED**: periodo_dias ahora se persiste correctamente
- 🟡 **P0-2 READY**: Migración SQL + modelo creados, pendiente aplicar
- ❌ **P0-4 ACTIVE**: Vision API JPG falla con HTTP 500
- ⚠️ **P1-1 PENDING**: iva_porcentaje no se extrae

---

## ⭐ FIX P1-1: Extracción de iva_porcentaje

### Archivo: `app/services/ocr.py`

**Ubicación**: Después de línea 677 (extracción actual de `iva`)

**Código a agregar**:

```python
# Línea 677 (ACTUAL):
result["iva"] = _extract_number([r"\biva\b[^0-9]{0,10}([\d.,]+)"])
detected["iva"] = result["iva"] is not None

# ⭐ AGREGAR DESPUÉS (línea 679):
# Extracción del porcentaje de IVA (21%, 10%, 4%)
iva_pct_patterns = [
    r"IVA\s+(21|10|4)\s*%",  # "IVA 21%"
    r"IVA\s+\(\s*(21|10|4)\s*%\s*\)",  # "IVA (21%)"
    r"tipo\s+(?:de\s+)?IVA[:\s]+(21|10|4)\s*%",  # "Tipo de IVA: 21%"
]
for pattern in iva_pct_patterns:
    iva_pct_match = re.search(pattern, full_text, re.IGNORECASE)
    if iva_pct_match:
        result["iva_porcentaje"] = float(iva_pct_match.group(1))
        detected["iva_porcentaje"] = True
        break

if "iva_porcentaje" not in detected:
    detected["iva_porcentaje"] = False
```

**Validación**:
- Si detecta "IVA 21%" → `iva_porcentaje = 21.0`
- Si detecta "IVA (10%)" → `iva_porcentaje = 10.0`
- Comparador usará este valor en línea 500 (comparador.py)

---

## 🔧 FIX P2-1: Mejorar logging en comparador

### Archivo: `app/services/comparador.py`

**Ubicación**: Línea 309-310

**Cambio**:

```python
# ANTES (línea 309-310):
except Exception as e:
    logger.error(f"Error persisting offers: {e}")
    return False

# DESPUÉS:
except Exception as e:
    logger.error(
        f"Error persisting offers (Comparativa {comparativa_id}, Factura {factura_id}): {e}",
        exc_info=True  # ⭐ CRITICAL: Esto incluye el traceback completo
    )
    return False
```

**Beneficio**: Los errores de persistencia ahora mostrarán traceback completo en logs.

---

## 🛠️ FIX P0-4: Debug Vision API (Investigación)

### **Paso 1**: Revisar logs del servidor

```bash
# En Render Dashboard:
# 1. Ir a tu servicio FastAPI
# 2. Click en "Logs"
# 3. Filtrar por "Vision" o "500"
# 4. Buscar traceback del error
```

### **Paso 2**: Verificar variable de entorno

```python
# Agregar en webhook.py línea 150 (justo antes del OCR):
import os
print(f"[DEBUG] GOOGLE_CREDENTIALS exists: {bool(os.getenv('GOOGLE_CREDENTIALS'))}")
print(f"[DEBUG] /etc/secrets exists: {os.path.exists('/etc/secrets')}")
```

### **Paso 3**: Test manual Vision API

**Crear archivo**: `test_vision_api.py`

```python
import os
from app.services.ocr import get_vision_client

# Test connection
client, logs = get_vision_client()
print(logs)

if client:
    print("✅ Vision client initialized successfully")
    print(f"Project: {client._credentials.project_id}")
else:
    print("❌ Vision client FAILED to initialize")
    print("Check GOOGLE_CREDENTIALS env var")
```

**Ejecutar**:
```bash
python test_vision_api.py
```

### **Paso 4**: Fix probable

Si el problema es credentials:

```python
# En ocr.py, línea 214, cambiar:
except Exception as e:
    logs.append(f"Error parsing ENV credentials: {str(e)}")
    return None, "\n".join(logs)

# A:
except Exception as e:
    logs.append(f"Error parsing ENV credentials: {str(e)}")
    # ⭐ Agregar traceback para debugging
    import traceback
    logs.append(f"Traceback: {traceback.format_exc()}")
    return None, "\n".join(logs)
```

---

## 📋 CHECKLIST DE APLICACIÓN

### **Inmediato (antes de deploy)**:
- [ ] Aplicar FIX P1-1 (iva_porcentaje) en `ocr.py`
- [ ] Aplicar FIX P2-1 (logging) en `comparador.py`
- [ ] Ejecutar migración SQL:
  ```bash
  # En Neon SQL Editor
  \i migration_ofertas_calculadas.sql
  ```

### **Deploy**:
- [ ] Commit cambios:
  ```bash
  git add app/routes/webhook.py app/services/ocr.py app/services/comparador.py app/db/models.py
  git commit -m "FIX: P0-1 periodo_dias, P1-1 iva_porcentaje, P2-1 logging"
  git push origin main
  ```
- [ ] Esperar deploy automático en Render
- [ ] Verificar logs: "Deployment successful"

### **Validación Post-Deploy**:
- [ ] Re-ejecutar test E2E:
  ```bash
  python audit_e2e_test.py
  ```
- [ ] Verificar que JPGs ya no retornan 500
- [ ] Verificar que `ofertas_calculadas` se persisten
- [ ] Verificar que `iva_porcentaje` se extrae en facturas con IVA visible

---

## 🚨 CRITICAL: Vision API Troubleshooting

Si el FIX P0-4 persiste después de verificar credentials:

### **Opción A**: Forzar uso de Gemini para JPG

```python
# En ocr.py, línea 850 (función extract_data_from_pdf):

# ANTES:
if is_pdf:
    # Usar Gemini
    gemini_data = extract_data_with_gemini(file_bytes, is_pdf=True)
    ...
else:
    # Usar Vision para JPG ← AQUÍ FALLA
    gemini_data = extract_data_with_gemini(file_bytes, is_pdf=False)

# DESPUÉS (forzar Gemini siempre):
# ⭐ TEMPORAL FIX: Usar Gemini para todo mientras se arregla Vision
gemini_data = extract_data_with_gemini(file_bytes, is_pdf=is_pdf)
if gemini_data:
    return gemini_data
# Si Gemini falla, intentar Vision como fallback solo para PDF
if is_pdf:
    # Vision fallback...
```

### **Opción B**: Actualizar librería google-cloud-vision

```bash
# En requirements.txt, cambiar:
google-cloud-vision==3.0.0  # O la versión actual

# A:
google-cloud-vision==3.7.2  # Latest stable
```

---

## 📊 IMPACTO ESPERADO POST-FIXES

| Fix | Impacto | Beneficio |
|-----|---------|-----------|
| P0-1 ✅ | periodo_dias persiste | ✅ Comparador funciona sin PERIOD_REQUIRED |
| P0-2 🟡 | ofertas_calculadas existe | ✅ Persistencia de ofertas funciona |
| P0-4 ❌ | Vision API JPG funciona | ✅ 100% facturas procesables (PDF + JPG) |
| P1-1  | iva_porcentaje se extrae | ✅ Cálculos correcto para bono social (10%) |
| P2-1 | Logging mejorado | ✅ Debugging más fácil en producción |

**Estimado de tiempo total**: 2-3 horas (incluyendo deploy y validación)

---

**Fecha**: 2026-01-19  
**Auditor**: QA Senior Backend + Datos  
**Status**: ✅ READY TO IMPLEMENT
