# 🎯 EXACT CODE CHANGES - Copy-Paste Ready

**Para:** Developer ejecutando las fixes  
**Uso:** Copiar exactamente estas líneas y reemplazar en los archivos indicados

---

## FILE 1: `app/wizard/[id]/step-2-validar/page.jsx`

### CHANGE 1A: Line 77
**Search for:**
```javascript
periodo_dias: periodo_dias_calculado ?? '',  // ⭐ IMPORTANTE: persistir periodo
```

**Replace with:**
```javascript
periodo_dias: periodo_dias_calculado || 0,   // ✅ FIX: 0 if null (will be marked invalid)
```

---

### CHANGE 1B: Lines 87-89
**Search for:**
```javascript
          iva: data.iva ?? '',  // ⚠️ NO default 0 (evitar confusión con porcentaje)
          iva_porcentaje: data.iva_porcentaje != null
            ? (Number(data.iva_porcentaje) <= 1 ? Number(data.iva_porcentaje) * 100 : data.iva_porcentaje)
            : 21,  // Default 21%
          impuesto_electrico: data.impuesto_electrico ?? '',  // ⚠️ NO default 0
```

**Replace with:**
```javascript
          iva: data.iva ?? 0,  // ✅ FIX: 0 if null (number, not string)
          iva_porcentaje: data.iva_porcentaje != null
            ? (Number(data.iva_porcentaje) <= 1 ? Number(data.iva_porcentaje) * 100 : data.iva_porcentaje)
            : 21,  // Default 21%
          impuesto_electrico: data.impuesto_electrico ?? 0,  // ✅ FIX: 0 if null (number)
```

---

### CHANGE 1C: Line 315
**Search for:**
```javascript
  // P6: Validación estricta y de negocio
  const isValid = (val) => val !== null && val !== undefined && String(val).trim().length > 0;
```

**Replace with:**
```javascript
  // P6: Validación estricta y de negocio
  const isValid = (val) => {
    if (val === null || val === undefined) return false;
    if (typeof val === 'number') return val > 0;  // Para números, > 0 es válido
    return String(val).trim().length > 0;  // Para strings, no vacíos
  };
```

---

### CHANGE 1D: Line ~340-360
**Search for (ENTIRE FUNCTION):**
```javascript
  const buildPayload = (data) => {
    total_factura: parseNumberInput(data.total_factura),
    coste_energia_actual: parseNumberInput(data.coste_energia_actual),
    coste_potencia_actual: parseNumberInput(data.coste_potencia_actual),
    periodo_dias: Number.isFinite(parseInt(data.periodo_dias, 10))
      ? parseInt(data.periodo_dias, 10)
      : null,
  };
  
  console.log("%c [STEP2-PAYLOAD] ", "background: #10b981; color: #fff;", payload);
  return payload;
};
```

**Replace ENTIRE buildPayload with:**
```javascript
  // ✅ Helper function
  const parseNumberInput = (val) => {
    if (val === null || val === undefined || val === '') return 0;
    const parsed = parseFloat(val);
    return isNaN(parsed) ? 0 : parsed;
  };

  const buildPayload = (data) => {
    const payload = {
      cups: data.cups?.trim() || null,
      atr: data.atr?.trim() || null,
      total_factura: parseNumberInput(data.total_factura),
      periodo_dias: Number.isFinite(parseInt(data.periodo_dias, 10))
        ? parseInt(data.periodo_dias, 10)
        : null,
      cliente: data.cliente || null,
      consumo_total: parseNumberInput(data.consumo_total),
      potencia_p1: parseNumberInput(data.potencia_p1),
      potencia_p2: parseNumberInput(data.potencia_p2),
      consumo_p1: parseNumberInput(data.consumo_p1),
      consumo_p2: parseNumberInput(data.consumo_p2),
      consumo_p3: parseNumberInput(data.consumo_p3),
      consumo_p4: parseNumberInput(data.consumo_p4),
      consumo_p5: parseNumberInput(data.consumo_p5),
      consumo_p6: parseNumberInput(data.consumo_p6),
      iva: parseNumberInput(data.iva),  // ✅ FIX: number or 0, never string
      iva_porcentaje: data.iva_porcentaje ? parseFloat(data.iva_porcentaje) : 21,
      impuesto_electrico: parseNumberInput(data.impuesto_electrico),  // ✅ FIX: float or 0
      alquiler_contador: parseNumberInput(data.alquiler_contador),
      coste_energia_actual: parseNumberInput(data.coste_energia_actual),
      coste_potencia_actual: parseNumberInput(data.coste_potencia_actual),
    };
    
    // ✅ DEBUG LOG
    console.log(`%c [STEP2-PAYLOAD-NORMALIZED] `, "background: #10b981; color: #fff; padding: 2px 6px; border-radius: 3px;", {
      periodo_dias: { value: payload.periodo_dias, type: typeof payload.periodo_dias },
      iva: { value: payload.iva, type: typeof payload.iva },
      iva_porcentaje: { value: payload.iva_porcentaje, type: typeof payload.iva_porcentaje },
      impuesto_electrico: { value: payload.impuesto_electrico, type: typeof payload.impuesto_electrico },
      alquiler_contador: { value: payload.alquiler_contador, type: typeof payload.alquiler_contador },
    });
    
    return payload;
  };
```

---

## FILE 2: `app/routes/webhook.py`

### CHANGE 2A: After imports (Line ~83)
**Add BEFORE the `class FacturaUpdate(BaseModel):` definition:**

```python
import logging
logger = logging.getLogger(__name__)

def _normalize_iva_porcentaje(value):
    """Normaliza IVA % a float [0-100]"""
    if value is None or value == '':
        return 21.0  # Default 21%
    try:
        val = float(value)
        if 0 < val <= 100:
            return val
        logger.warning(f"[STEP2-WARN] IVA % rechazado: {val} (fuera rango 0-100)")
        return None
    except (ValueError, TypeError):
        logger.warning(f"[STEP2-WARN] IVA % no convertible: {value}")
        return None


def _normalize_periodo_dias(value):
    """Normaliza periodo_dias a int [1-366]"""
    if value is None or value == '' or value == 0:
        logger.debug(f"[STEP2-WARN] periodo_dias nulo/cero: {value}")
        return None
    try:
        val = int(value)
        if 1 <= val <= 366:
            return val
        logger.warning(f"[STEP2-WARN] periodo_dias fuera rango: {val} (requiere 1-366)")
        return None
    except (ValueError, TypeError):
        logger.warning(f"[STEP2-WARN] periodo_dias no convertible a int: {value}")
        return None


def _normalize_numeric_field(name: str, value, min_val=0.0, max_val=9999.99):
    """Normaliza campos numéricos (IVA €, IEE, alquiler, etc)"""
    if value is None or value == '':
        return None
    try:
        val = float(value)
        if min_val <= val <= max_val:
            return val
        logger.warning(f"[STEP2-WARN] {name}={val} fuera rango [{min_val}, {max_val}]")
        return None
    except (ValueError, TypeError):
        logger.warning(f"[STEP2-WARN] {name}={value} no convertible a float")
        return None
```

---

### CHANGE 2B: Line ~512 (initial logging)
**Search for:**
```python
    logger.info(
        "🔍 [AUDIT STEP2] Payload recibido factura_id=%s: periodo_dias=%s, iva_porc=%s, iva_eur=%s, iee_eur=%s, alquiler=%s",
        factura_id,
        update_data.get("periodo_dias"),
        update_data.get("iva_porcentaje"),
        update_data.get("iva"),
        update_data.get("impuesto_electrico"),
        update_data.get("alquiler_contador")
    )
```

**Replace with:**
```python
    logger.info(
        "🔍 [AUDIT STEP2] Payload RECIBIDO factura_id=%s: periodo_dias=%s (type=%s), iva_porc=%s, iva_eur=%s (type=%s), iee_eur=%s (type=%s), alquiler=%s (type=%s)",
        factura_id,
        update_data.get("periodo_dias"),
        type(update_data.get("periodo_dias")).__name__,
        update_data.get("iva_porcentaje"),
        update_data.get("iva"),
        type(update_data.get("iva")).__name__,
        update_data.get("impuesto_electrico"),
        type(update_data.get("impuesto_electrico")).__name__,
        update_data.get("alquiler_contador"),
        type(update_data.get("alquiler_contador")).__name__,
    )
```

---

### CHANGE 2C: Line ~530 (normalization loop)
**Search for:**
```python
    for key, value in update_data.items():
        if key == 'cups' and value:
            norm = normalize_cups(value)
            if norm and is_valid_cups(norm):
                value = norm
            else:
                value = None
        if key == "atr" and value:
            from app.services.ocr import extract_atr
            normalized_atr = extract_atr(str(value))
            value = normalized_atr or str(value).strip().upper()
        if key == "iva_porcentaje":
            value = _normalize_iva_porcentaje(value)
        if key == "periodo_dias":
            value = _normalize_periodo_dias(value)
        setattr(factura, key, value)
```

**Replace with:**
```python
    for key, value in update_data.items():
        if key == 'cups' and value:
            norm = normalize_cups(value)
            if norm and is_valid_cups(norm):
                value = norm
            else:
                value = None
        if key == "atr" and value:
            from app.services.ocr import extract_atr
            normalized_atr = extract_atr(str(value))
            value = normalized_atr or str(value).strip().upper()
        if key == "iva_porcentaje":
            value = _normalize_iva_porcentaje(value)
        if key == "periodo_dias":
            value = _normalize_periodo_dias(value)
        # ✅ NEW: Normalizar campos numéricos
        if key == "iva":
            value = _normalize_numeric_field("iva", value, min_val=0, max_val=500)
        if key == "impuesto_electrico":
            value = _normalize_numeric_field("impuesto_electrico", value, min_val=0, max_val=200)
        if key == "alquiler_contador":
            val = _normalize_numeric_field("alquiler_contador", value, min_val=0, max_val=50)
            if val and val > 1:
                logger.warning(f"[STEP2-WARN] alquiler_contador={val}€ > 1, asumiendo estimado para período")
            value = val
        
        setattr(factura, key, value)
```

---

### CHANGE 2D: Line ~570 (final logging)
**Search for:**
```python
    logger.info(
        "✅ [AUDIT STEP2] Guardado final factura_id=%s: periodo_dias=%s, iva_porc=%s, iva_eur=%s, iee_eur=%s, estado=%s",
        factura.id,
        factura.periodo_dias,
        factura.iva_porcentaje,
        factura.iva,
        factura.impuesto_electrico,
        factura.estado_factura
    )
```

**Replace with:**
```python
    logger.info(
        "✅ [AUDIT STEP2] Guardado FINAL factura_id=%s: periodo_dias=%s (type=%s, valid=%s), "
        "iva_porc=%s, iva_eur=%s (type=%s), iee_eur=%s (type=%s), alquiler=%s (type=%s), estado=%s",
        factura.id,
        factura.periodo_dias,
        type(factura.periodo_dias).__name__ if factura.periodo_dias else 'None',
        1 <= (factura.periodo_dias or 0) <= 366 if factura.periodo_dias else False,
        factura.iva_porcentaje,
        factura.iva,
        type(factura.iva).__name__ if factura.iva else 'None',
        factura.impuesto_electrico,
        type(factura.impuesto_electrico).__name__ if factura.impuesto_electrico else 'None',
        factura.alquiler_contador,
        type(factura.alquiler_contador).__name__ if factura.alquiler_contador else 'None',
        factura.estado_factura
    )
```

---

## FILE 3: `app/services/comparador.py`

### CHANGE 3A: Line 587 (after getting values)
**Search for:**
```python
    # ⭐ MÉTODO PO/NODOÁMBAR: Calcular subtotal sin impuestos de factura ACTUAL
    # mediante BACKSOLVE desde los importes totales (NO inventar precios)
    
    # Obtener valores de la factura
    total_factura = current_total  # Ya validado antes
    iva_importe = _to_float(getattr(factura, 'iva', None))
    iee_importe = _to_float(getattr(factura, 'impuesto_electrico', None))
    alquiler_importe = _to_float(getattr(factura, 'alquiler_contador', None)) or 0.0
```

**Replace with:**
```python
    # ⭐ MÉTODO PO/NODOÁMBAR: Calcular subtotal sin impuestos de factura ACTUAL
    # mediante BACKSOLVE desde los importes totales (NO inventar precios)
    
    # Obtener valores de la factura
    total_factura = current_total  # Ya validado antes
    iva_importe = _to_float(getattr(factura, 'iva', None))
    iee_importe = _to_float(getattr(factura, 'impuesto_electrico', None))
    alquiler_importe = _to_float(getattr(factura, 'alquiler_contador', None)) or 0.0
    
    # ✅ LOGGING DE DIAGNOSTICO
    logger.info(
        f"[PO-INPUTS] factura_id={factura.id}: iva={iva_importe} (raw_type={type(factura.iva).__name__ if factura.iva else 'None'}), "
        f"iee={iee_importe} (raw_type={type(factura.impuesto_electrico).__name__ if factura.impuesto_electrico else 'None'}), "
        f"alq={alquiler_importe}, periodo_dias={factura.periodo_dias}"
    )
```

---

### CHANGE 3B: Line ~595 (after iva_pct determination)
**Search for:**
```python
    # Determinar IVA %
    if hasattr(factura, 'iva_porcentaje') and factura.iva_porcentaje is not None:
        iva_pct_reconstruccion = float(factura.iva_porcentaje) / 100.0
    else:
        iva_pct_reconstruccion = 0.21  # 21% por defecto

    # BACKSOLVE: Calcular subtotal sin impuestos
    baseline_method = "backsolve_subtotal_si"
```

**Replace with:**
```python
    # Determinar IVA %
    if hasattr(factura, 'iva_porcentaje') and factura.iva_porcentaje is not None:
        iva_pct_reconstruccion = float(factura.iva_porcentaje) / 100.0
    else:
        iva_pct_reconstruccion = 0.21  # 21% por defecto

    # ✅ VALIDACION: Si periodo_dias es null/0, ABORTAR con error descriptivo
    if not factura.periodo_dias or factura.periodo_dias <= 0 or factura.periodo_dias > 366:
        from app.exceptions import DomainError
        raise DomainError(
            code="PERIOD_INVALID",
            message=f"periodo_dias inválido: {factura.periodo_dias}. Requiere valores 1-366. Completa Step 2 (validación obligatoria)."
        )

    # BACKSOLVE: Calcular subtotal sin impuestos
    baseline_method = "backsolve_subtotal_si"
```

---

## FILE 4: `app/wizard/[id]/step-3-comparar/page.jsx`

### CHANGE 4A: Line ~50-80 (loadData useEffect)
**Search for:**
```javascript
  useEffect(() => {
    async function loadData() {
      if (!params.id || params.id === 'new') return;
      try {
        setLoading(true);
        const { getFactura } = await import('@/lib/apiClient');
        const data = await getFactura(params.id);
        
        if (!data) {
          setError("No se ha encontrado la factura");
          return;
        }
        
        setFormData(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
      }
    }
    loadData();
  }, [params.id]);
```

**Replace with:**
```javascript
  useEffect(() => {
    async function loadData() {
      if (!params.id || params.id === 'new') return;
      try {
        setLoading(true);
        const { getFactura } = await import('@/lib/apiClient');
        const data = await getFactura(params.id);
        
        if (!data) {
          setError("❌ No se ha encontrado la factura");
          return;
        }
        
        // ✅ VALIDACIÓN CRÍTICA
        const periodo = data.periodo_dias;
        if (!periodo || periodo <= 0 || periodo > 366) {
          setError(`❌ PERIODO INVÁLIDO: ${periodo}. Vuelve a Step 2 para completar (obligatorio).`);
          setLoading(false);
          return;
        }
        
        if (!data.iva && data.iva !== 0) {
          setError("❌ IVA no validado. Vuelve a Step 2.");
          setLoading(false);
          return;
        }
        
        if (!data.consumo_kwh) {
          setError("❌ Consumo no validado. Vuelve a Step 2.");
          setLoading(false);
          return;
        }
        
        setFormData(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
      }
    }
    loadData();
  }, [params.id]);
```

---

### CHANGE 4B: handleCompare function
**Search for:**
```javascript
  const handleCompare = async () => {
    if (!formData) return;
    
    try {
      // ... comparación code ...
```

**Replace with:**
```javascript
  const handleCompare = async () => {
    if (!formData) return;
    
    // ✅ LOG CRÍTICO PRE-COMPARACIÓN
    console.log(`%c [STEP3] Iniciando comparación con:`, "background: #f59e0b; color: #fff; font-weight: bold; padding: 2px 6px; border-radius: 3px;", {
      factura_id: params.id,
      periodo_dias: { value: formData.periodo_dias, type: typeof formData.periodo_dias },
      consumo_kwh: formData.consumo_kwh,
      potencia_p1_kw: formData.potencia_p1_kw,
      potencia_p2_kw: formData.potencia_p2_kw,
      iva: { value: formData.iva, type: typeof formData.iva },
      iva_porcentaje: formData.iva_porcentaje,
      impuesto_electrico: { value: formData.impuesto_electrico, type: typeof formData.impuesto_electrico },
      total_factura: formData.total_factura,
    });
    
    try {
      // ... comparación code ...
```

---

### CHANGE 4C: Catch block del comparar
**Search for:**
```javascript
    } catch (error) {
      setError(error.message || "Error generando comparación");
    }
```

**Replace with:**
```javascript
    } catch (error) {
      // ✅ MOSTRAR ERROR DESCRIPTIVO (no genérico)
      let errorMsg = error.message || "Error generando comparación";
      
      if (error.data?.code === "PERIOD_INVALID") {
        errorMsg = `❌ ${error.data.message}`;
      } else if (errorMsg.includes("PERIOD_REQUIRED")) {
        errorMsg = "❌ PERIODO OBLIGATORIO (Step 2): Vuelve atrás para completar.";
      }
      
      setError(errorMsg);
      console.error(`[STEP3] Comparación fallida:`, errorMsg);
    }
```

---

## ✅ Verification After Each Change

```bash
# After each file change:
npm run build  # For frontend changes
python -m pytest tests/ -q  # For backend changes

# Check for console errors:
# Frontend: No TypeScript/syntax errors
# Backend: No import/type errors
```

---

## 🎯 Order of Execution

1. **FILE 2** (backend normalizadores) - foundation
2. **FILE 1** (frontend) - main UI fixes
3. **FILE 3** (comparador) - validation gate
4. **FILE 4** (step3) - error handling

---

**Total changes:** 13 edits across 4 files  
**Estimated time:** 2h 40min (including testing)  
**Risk:** Low (no schema changes, backward compatible)

---

*Ready to copy-paste. No additional context needed.*
