# ✅ BUGS P0 - ESTADO FINAL

## 🎯 Resultado: 3/4 BUGS FIXED ✅

### ✅ BUG D: Dedupe UX (FIXED)
**Estado:** ✅ COMPLETADO
**Archivos modificados:**
- `app/wizard/[id]/step-1-factura/page.jsx`
  - Añadido import Link
  - Mejorado manejo de error 409 para parsear detalle JSON
  - Nuevo estado de "duplicate" con existing_id y client info
  - Banner con 2 CTAs: "Ir a validar" + "Volver al dashboard"

**Verificación:**
```bash
# Subir el mismo PDF 2 veces
# Debe mostrar banner con info de factura existente y botones
```

---

### ✅ BUG A: Step1 bloquea si OCR falla (FIXED)
**Estado:** ✅ COMPLETADO  
**Archivos modificados:**
- `app/wizard/[id]/step-1-factura/page.jsx`
  - Añadido estado `facturaId`
  - `setFacturaId(res.id)` siempre se ejecuta
  - Condición botón cambiada de `!ocrData` a `!facturaId`

**Verificación:**
```bash
# Subir PDF corrupto o sin texto
# Backend crea factura con estado="pendiente_datos"
# Frontend debe permitir click en "SIGUIENTE" y pasar a Step2
```

---

### ✅ BUG C: Parse + persistencia mal (FIXED)
**Estado:** ✅ COMPLETADO
**Archivos modificados:**
- `app/services/ocr.py` líneas 306-332
  - PRIORIDAD 1: `TOTAL A PAGAR` (máxima, nunca confunde)
  - PRIORIDAD 2: `TOTAL FACTURA` / `TOTAL IMPORTE FACTURA`
  - PRIORIDAD 3: `IMPORTE FACTURA` (fallback)
  - Evita confusión con "BASE IMPONIBLE"

**Verificación:**
```bash
# Subir factura Iberdrola con:
# - "BASE IMPONIBLE: 80€"
# - "TOTAL A PAGAR: 100€"
# Debe persistir total_factura = 100 (no 80)
```

---

### ⚠️ BUG B: OCR páginas corruptas (CÓDIGO LISTO, NO APLICADO)
**Estado:** ⚠️ CÓDIGO PREPARADO PERO NO INTEGRADO
**Motivo:** Problemas con caracteres especiales en replace_file_content

**Archivos afectados:**
- `app/services/ocr.py` líneas 704-720 (necesita reemplazo manual)

**Código preparado en:**
- `BUG_B_FIX_CODE.py` (archivo de referencia)

**Para aplicar manualmente:**
1. Añadir función `_score_page_quality()` en línea ~702
2. Modificar `extract_data_from_pdf()` para:
   - Extraer texto por página
   - Calcular quality score por página
   - Filtrar páginas con quality > 0.6
   - Si todas son malas, usar la mejor
   - Loggear páginas ignoradas

**Código exacto:**
```python
def _score_page_quality(text: str) -> float:
    """Score de calidad (0.0=basura, 1.0=perfecto)"""
    if not text or len(text) < 10:
        return 0.0
    
    printable = sum(1 for c in text if c.isprintable() or c.isspace())
    total = len(text)
    ratio = printable / total
    
    # Penalizar caracteres raros
    rare_chars = sum(1 for c in text if ord(c) > 127 and not c.isalpha())
    if rare_chars / total > 0.3:
        ratio *= 0.5
    
    return ratio
```

Luego en `extract_data_from_pdf` línea ~710, reemplazar el loop:
```python
# ANTES:
for page in reader.pages:
    text = page.extract_text()
    if text:
        full_text += text + "\n"

# DESPUÉS:
pages_text = []
for idx, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        quality = _score_page_quality(text)
        pages_text.append({"page": idx+1, "text": text, "quality": quality})
        print(f"Página {idx+1}: calidad={quality:.2f}")

useful_pages = [p for p in pages_text if p["quality"] > 0.6]
if not useful_pages and pages_text:
    useful_pages = [max(pages_text, key=lambda p: p["quality"])]
    print(f"⚠️ Usando mejor página: {useful_pages[0]['page']}")

full_text = "\n".join([p["text"] for p in useful_pages]) if useful_pages else ""
ignored = len(pages_text) - len(useful_pages) if pages_text else 0
if ignored > 0:
    print(f"📄 Útiles: {len(useful_pages)}/{len(pages_text)} (ignoradas: {ignored})")
```

---

## 📊 RESUMEN EJECUTIVO

### ✅ Completados (3/4):
- BUG D: Dedupe UX
- BUG A: Step1 no bloquea si OCR falla
- BUG C: Parse prioriza TOTAL A PAGAR

### ⚠️ Pendiente (1/4):
- BUG B: Scoring páginas (código listo en `BUG_B_FIX_CODE.py`)

### 📁 Archivos modificados:
1. `app/wizard/[id]/step-1-factura/page.jsx` ✅
2. `app/services/ocr.py` ✅ (parcial)

### 🧪 TESTS MANUALES OBLIGATORIOS

```bash
# Test 1: OCR falla pero continúa
1. Subir PDF vacío o corrupto
2. Verificar: Se crea factura
3. Verificar: Botón "SIGUIENTE" habilitado
4. Click "SIGUIENTE" → debe ir a Step2

# Test 2: Dedupe con info
1. Subir Iberdrola.pdf
2. Subir el MISMO archivo otra vez
3. Verificar: Banner "Factura ya registrada"
4. Verificar: Botones "Ir a validar" + "Volver"
5. Click "Ir a validar" → debe navegar a Step2 de factura existente

# Test 3: TOTAL A PAGAR correcto
1. Subir Iberdrola con BASE IMPONIBLE + TOTAL A PAGAR diferentes
2. Ir a Step2
3. Verificar: total_factura coincide con "TOTAL A PAGAR"  (NO base imponible)

# Test 4 (Pendiente BUG B):
1. Subir PDF con página 3 corrupta pero páginas 1-2 útiles
2. Verificar logs: debe ignorar página 3
3. Verificar: parsea datos de páginas útiles
```

---

## 🚨 ACCIÓN REQUERIDA USUARIO

**BUG B** necesita aplicación manual o usar editor de texto para reemplazar en `app/services/ocr.py`:

**Opción 1 (Recomendada):** Abrir `app/services/ocr.py` y:
1. Añadir función `_score_page_quality` en línea ~702
2. Modificar el bloque líneas 709-714 según código en `BUG_B_FIX_CODE.py`

**Opción 2:** Esperar siguiente sesión y aplicar con herramienta diferente

---

## 📦 ARCHIVOS DE REFERENCIA CREADOS

1. `BUGS_P0_ANALYSIS.md` - Análisis de causas raíz
2. `FIXES_P0_IMPLEMENTATION.md` - Guía completa de implementación
3. `BUG_B_FIX_CODE.py` - Código listo para BUG B
4. `BUG_P0_STATUS_FINAL.md` - Este documento

---

**Fecha:** 2026-01-09 19:20  
**Estado:** 3/4 BUGS FIXED ✅  
**Pendiente:** BUG B (código listo, aplicación manual)
