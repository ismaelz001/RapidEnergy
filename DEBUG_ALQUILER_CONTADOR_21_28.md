# 🔎 INVESTIGACIÓN SECUNDARIA: Alquiler Contador 21.28€

**Fecha:** 3 febrero 2026  
**Estado:** INVESTIGACIÓN ABIERTA (requiere data específica)  
**Prioridad:** P1 (después de P0 fixes)

---

## 🎯 El Symptoma

Usuario ve en Step2:
```
Alquiler contador: 21.28€ (para período de 32 días)
```

Debería ser:
```
Alquiler contador: 0.85€ (0.80€/mes ≈ 0.70€ en 32 días)
```

**Multiplicador:** 21.28 / 0.85 ≈ **25x mayor** (ABSURDO)

---

## 🔍 Posibles Causas (Hipótesis)

### 1️⃣ OCR EXTRAE MAL (PROBABLE)
**Síntoma:** OCR interpreta datos de factura como alquiler.

**Ejemplos:**
- Factura muestra: "Servicios: 21.28€"
- OCR entiende: Esto es "Alquiler"
- Resultado: alquiler_contador = 21.28

**Verificar en:** `app/services/ocr.py` línea 1640-1650

```python
result["alquiler_contador"] = _extract_number([
    r"alquiler\s+(?:de\s+)?(?:equipos|contador|medida)[^0-9]{0,20}([\d.,]+)",
    r"equipos\s+de\s+medida[^0-9]{0,20}([\d.,]+)",
    r"contador\s+alquiler[^0-9]{0,10}([\d.,]+)"
])
```

**Problema:** Estas regex son DEMASIADO AMPLIAS. Si ve "Servicios de medida" y "21.28", puede confundir.

---

### 2️⃣ FRONTEND CONFUNDE UNIDADES
**Síntoma:** User rellena manualmente en Step2.

```javascript
// En Step2, el label podría ser confuso
label: "Alquiler contador (€)"  // ← ¿Es mensual o para TODO el período?
placeholder: "Ej: 0.85"  // ← Espera 0.85, pero user ve 21.28 en factura
```

Si la factura original muestra "Alquiler: 21.28€ (trimestral)" o algo similar, user lo copia directamente.

---

### 3️⃣ UNIDADES INCORRECTAS EN FACTURA ORIGINAL
**Síntoma:** Factura antigua con tarifas diferentes.

Ejemplo Endesa 2024:
```
Alquiler contador: 21.28€ / AÑO
```

Pero OCR **ignora el "/ AÑO"** y extrae solo `21.28`.

---

### 4️⃣ CONFUSIÓN CON PORCENTAJES (RARO)
**Síntoma:** Alquiler expresado como % que OCR interpreta como €.

```
"Alquiler: 2.128% del consumo" → OCR: "2.128" → UI: 2.128€ (OK)
"Alquiler: 212.8% base" → OCR: "212.8" → UI: 212.8€ (ERROR)
```

Pero 21.28 no casaría con 212.8, así que es menos probable.

---

## 🧪 Debugging Steps

### A. Localizar factura problemática

```bash
# En la DB, buscar alquiler_contador = 21.28 o similar
SELECT id, numero_factura, alquiler_contador, periodo_dias, raw_data 
FROM facturas 
WHERE alquiler_contador > 5 AND alquiler_contador < 50
LIMIT 5;

# Anotar ID de factura (ej: 327, 328, 330)
```

---

### B. Inspecionar raw_data (OCR output)

```bash
curl -X GET https://rapidenergy.onrender.com/webhook/facturas/[ID_PROBLEMÁTICA]

# Buscar en respuesta JSON el campo: "raw_data"
# Dentro de raw_data, buscar:
#   - "alquiler_contador": 21.28
#   - Líneas de texto que contengan "21.28" o "alquiler"
#   - Detectar si OCR lo marcó como "detected_por_ocr": true
```

Ejemplo respuesta esperada:
```json
{
  "id": 327,
  "numero_factura": "FAC-2025-001",
  "alquiler_contador": 21.28,
  "raw_data": {
    "parsed_fields": {
      "alquiler_contador": {
        "value": 21.28,
        "source": "ocr_regex_pattern_2",  // ← Aquí está el problema
        "pattern_matched": "alquiler\s+(?:de\s+)?(?:equipos|contador|medida)[^0-9]{0,20}([\d.,]+)",
        "raw_text": "Alquiler de servicios de medida: 21.28€"  // ← AQUÍ VES QUÉ LEYÓ
      }
    },
    "detected_por_ocr": {
      "alquiler_contador": true
    }
  }
}
```

---

### C. Verificar patrón problemático

Si el patrón era:
```
raw_text: "Alquiler de servicios de medida: 21.28€"
```

Entonces OCR correctamente extrajo 21.28, pero **está incorrecta en la factura original**.

**Siguiente paso:** Abrir PDF factura original → buscar "Alquiler" → anotar valor real.

---

## 🔧 Solución (por hipótesis)

### SI es OCR que confunde servicios con alquiler:
```python
# En ocr.py, hacer patrón MÁS ESPECÍFICO

# ❌ ANTES (demasiado amplio)
r"alquiler\s+(?:de\s+)?(?:equipos|contador|medida)[^0-9]{0,20}([\d.,]+)"

# ✅ DESPUÉS (rechaza "servicios de medida")
r"alquiler\s+(?:del\s+)?(?:contador|equipos)\b[^0-9]{0,10}([\d.,]+)"
# Notar: ya NO matchea "servicios de medida"
```

---

### SI es factura con alquiler anual que no normaliza:
```python
# En comparador.py, cuando usa alquiler_contador:

alquiler_valor = factura.alquiler_contador

# ✅ Normalizar si es MUY ALTO
if alquiler_valor and alquiler_valor > 5:
    # Asumir que es ANUAL, convertir a diario
    logger.warning(f"[ALQUILER] Valor={alquiler_valor}€ alto, asumiendo es anual")
    alquiler_diario = alquiler_valor / 365.25
else:
    alquiler_diario = alquiler_valor / factura.periodo_dias  # Si ya es por período
```

---

### SI es confusión de unidades en Step2:
```javascript
// En Step2, añadir label clarísimo

<label htmlFor="alquiler_contador" className="label text-white">
  Alquiler contador <span className="text-xs text-blue-300">(€/mes)</span>
  <span className="text-xs text-blue-400 ml-1">*</span>
</label>
<Input
  id="alquiler_contador"
  type="number"
  step="0.01"
  value={form.alquiler_contador || ''}
  placeholder="Ej: 0.80 (típicamente 0.70€-2.50€/mes)"
  // ✅ Ayuda visible
  hint="Valor mensual. Si es anual, divide entre 12 primero."
/>
```

---

## 📊 Hipótesis Ranking (Probabilidad)

| Hipótesis | Probabilidad | Evidencia | Fix Tiempo |
|-----------|-------------|----------|-----------|
| 1. OCR confunde "servicios" | 60% | Raw text "servicios de medida" | 15 min |
| 2. Factura original es anual | 25% | Valor 21.28 = 1.77€/mes (plausible) | 20 min |
| 3. User rellena mal en Step2 | 10% | Confusión de unidades (manual) | 5 min (UI) |
| 4. Porcentaje mal convertido | 5% | Muy raro, no encaja números | - |

---

## 🎯 Próximos Pasos

**AHORA (P0):**
1. ✅ Aplicar PATCHES_IMPLEMENTABLES_STEP2 (arriba en issues principales)
2. ✅ Deploy + validar que periodo_dias funciona

**DESPUÉS (P1, 1-2 días):**
1. Localizar factura con alquiler_contador = 21.28
2. Inspeccionar raw_data para ver qué OCR extrajo
3. Abrir PDF original para verificar valor real
4. Si es OCR, ajustar regex (option 1 arriba)
5. Si es factura anual, normalizar en comparador (option 2)

**OPCIONAL (P2, según impacto):**
- Mejorar UI de Step2 con hints/unidades claras (option 3)
- Añadir validación: alquiler > 5€ = warning "Parece anual"

---

## 📁 Archivos relacionados

- `app/services/ocr.py` línea 1640-1650 (patrones alquiler)
- `app/services/comparador.py` línea ~365 (uso alquiler en cálculo)
- `app/wizard/[id]/step-2-validar/page.jsx` línea ~600 (UI alquiler)

---

## ⚠️ Nota Importante

**Esta investigación requiere DATA REAL para confirmar causas.** Los pasos de debugging arriba permitirán identificar exactamente cuál de las 4 hipótesis es correcta. No es bloqueante para el fix P0 de periodo_dias/IVA/IEE.

---

**Estado:** ABIERTO - Esperar datos de debugging para confirmar causa.  
**Owner:** Tech Lead (después de P0 fixes).
