# QA Audit Factura #321 - Análisis de Errores

## Problemas Identificados

### 1. Error NoneType + int ✅ CORREGIDO

**Líneas problemáticas:**
- Línea 234 (ocr.py): `max(consumo_total * 0.10, 1.0)` - consumo_total podría ser None
- Línea 1448 (ocr.py): `if name_line_index + forward < len(raw_lines):` - name_line_index podría ser None

**Solución aplicada:**
- Línea 234: Agregado check `and consumo_total is not None` en la condición if
- Línea 1448: Agregado check `if name_line_index is not None:` antes de la operación suma

**Estado:** ✅ RESUELTO - El error `[Vision] ERROR: unsupported operand type(s) for +: 'NoneType' and 'int'` no debería ocurrir más.

---

### 2. CUPS se extrae pero llega como None a BD

**Observación:**
El log muestra:
```
[CUPS] CANDIDATE (STRICT): ES0022000008763779TF
[OK] VALID CUPS FOUND: ES0022000008763779TF
[FINAL] CUPS VALUE: ES0022000008763779TF
```

Pero luego:
```
[CUPS-AUDIT] #4 - DATABASE PERSISTENCE
  cups_ocr_input: None
  cups_final_db: None
```

**Análisis:** El CUPS se extrae correctamente en `parse_invoice_text()`, pero cuando se pasa a webhook.py línea 252, el valor es None. Esto sugiere que:
- O bien `ocr_data.get("cups")` retorna None después de parse_invoice_text
- O bien `normalize_cups()` falla y lo setea a None por inválido

**Próximos pasos:** Necesita debugging con credenciales de Google Vision API funcionales en Render.

---

### 3. Todos los consumos extraídos como 0 en imágenes

**Descripción:**
Cuando se procesa una imagen (Vision API), los consumos P1-P6 se extraen como 0:
```
consumo_p1_kwh: "0" (valor por defecto/vacío)
consumo_p2_kwh: "0" (valor por defecto/vacío)
consumo_p3_kwh: "0" (valor por defecto/vacío)
```

Pero la imagen visualmente muestra claramente los valores de consumo en la tabla.

**Causa probable:**
Vision API fragmenta el texto OCR, separando las etiquetas de período (P1, P2, P3) de sus valores numéricos.
La estrategia actual de extracción (línea 930-950) busca líneas que contengan AMBOS "P[1-6]" Y "kwh", pero estos pueden estar en líneas diferentes después de fragmentación.

**Ejemplos de fragmentación potencial:**
```
P1     123.45
kWh    Punta

↓ Vision API fragmenta a:
P1
123.45
kWh
Punta
```

Resultado: Línea "P1" no contiene "kWh", así que no se extrae.

**Solución recomendada:**
Mejorar `_extract_table_consumos()` o agregar estrategia de "búsqueda cross-línea" que busque P[1-6] y luego busque el número en líneas cercanas.

---

## Cambios Realizados

```python
# ocr.py línea 234
if suma_periodos > 0 and consumo_total is not None:  # ← Agregado check
    diferencia = abs(suma_periodos - consumo_total)
    tolerancia = max(float(consumo_total) * 0.10, 1.0)  # ← float() para seguridad

# ocr.py línea 1448  
if name_line_index is not None:  # ← Agregado check
    raw_lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
    for forward in range(1, 3):
        if name_line_index + forward < len(raw_lines):
            # ... resto del código
```

---

## Próximas Acciones

1. ✅ Error aritmético - RESUELTO
2. ⏳ Persistencia CUPS - Requiere debug con Vision API en producción
3. ⏳ Extracción consumos en imágenes - Requiere mejora de parsing para fragmentación

