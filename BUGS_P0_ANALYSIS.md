# 🐛 FIXES P0 - WIZARD ESTABILIZACIÓN

## Estado: EN PROGRESO

### BUG A: Step1 bloquea si OCR falla
**Causa raíz identificada:**
- Step1 página línea 69: `nextDisabled={!ocrData}`
- Si OCR falla, `ocrData` queda null → botón bloqueado
- Backend ya crea factura incluso si OCR falla

**Fix necesario:**
- Cambiar condición a: `nextDisabled={!facturaId}`  
- Backend debe devolver siempre `{id, ocr_status}` incluso si falla

### BUG B: OCR marca "imposible leer" por páginas corruptas
**Causa raíz identificada:**
- `extract_data_from_pdf()` línea 698-703 procesa todas las páginas juntas
- No hay scoring de calidad por página
- Una página corrupta contamina todo el texto

**Fix necesario:**
- Extraer texto POR PÁGINA
- Calcular ratio de caracteres no-imprimibles por página
- Ignorar páginas con >40% basura si hay páginas útiles  
- Solo marcar failed si TODAS son basura

### BUG C: Parse + persistencia mal
**Causa raíz identificada:**
- Línea 636-642 ocr.py: `total_factura` usa fallback a `importe` que puede ser base imponible
- Prioridad regex correcta pero puede fallar en Iberdrola
- Consumos P1/P2/P3 mapeo punta/llano/valle ya existe pero puede necesitar ajuste

**Fix necesario:**
- Mejorar regex "TOTAL A PAGAR" vs "BASE IMPONIBLE"
- Asegurar que persistencia no sobrescribe con NULL
- Verificar que normalize_cups se aplica antes de guardar

### BUG D: Dedupe UX
**Causa raíz identificada:**
- Backend ya hace dedupe (webhook.py 107-133)
- Respuesta 409 tiene datos pero frontend Step1 no los muestra bien

**Fix necesario:**
- Frontend: mostrar banner con existing_factura_id
- CTAs: "Ver factura" + "Ir a validar"

---

Implementando...
