# 🔴 TECH LEAD AUDIT: Step2 "Periodo Obligatorio" + PDF Totales Absurdos

**Fecha:** 3 de febrero de 2026  
**Severidad:** P0 (Bloqueante) - Afecta comparación y presupuesto  
**Scope:** Frontend Step2 + Backend validación + Persistencia + Step3/PDF

---

## 1. CAUSA RAÍZ #1: "Periodo es obligatorio" aunque se rellene

### Diagnosis
**El problema está en TWO niveles:**

#### 1A. FRONTEND (Step2 validación visual)
**Archivo:** `app/wizard/[id]/step-2-validar/page.jsx` líneas 165-180 y 345-350

```javascript
// ❌ PROBLEMA: periodo_dias almacenado como STRING en formData (WizardContext)
const requiredFields = [
  'cups', 'atr', 'total_factura',
  'periodo_dias',  // ← AQUI SE REQUIERE
  ...
];

const isValid = (val) => val !== null && val !== undefined && String(val).trim().length > 0;
const missingFields = requiredFields.filter(key => !isValid(form[key]));

// buildPayload() convierte a número, pero formData sigue STRING
const buildPayload = (data) => ({
  ...
  periodo_dias: Number.isFinite(parseInt(data.periodo_dias, 10))
    ? parseInt(data.periodo_dias, 10)
    : null,  // ← PERO SI parseInt FALLA (entrada vacía), devuelve null
});
```

**Root Cause:**
- `handleChange('periodo_dias')` → `formData.periodo_dias = '30'` (string)
- `isValid(form.periodo_dias)` → chequea que `'30'.trim().length > 0` → ✅ true
- **PERO** cuando se carga la factura en `loadData()`, el merge defensivo tiene un problema:

```javascript
periodo_dias: periodo_dias_calculado ?? '',  // ← LÍNEA 77
```

Si `periodo_dias_calculado` es `null` o `undefined`, asigna `''` (string vacío).  
El user lo rellena, pero el `isValid()` NO lo detecta correctamente porque:

```javascript
// isValid NO reconoce números con ceros iniciales o edge cases
isValid('0')     // → false (número es cero)
isValid('00030') // → true (string)
isValid(30)      // → true (número)
isValid('')      // → false (vacío)
```

#### 1B. BACKEND (Schema + Validación)
**Archivo:** `app/routes/webhook.py` línea 535 y `app/schemas/validacion.py` línea 108

```python
class FacturaUpdate(BaseModel):
    periodo_dias: Optional[int] = None  # ← NULLABLE, OK
```

```python
# En update_factura(), el normalize()
def _normalize_periodo_dias(value):
    """Normaliza periodo_dias a int"""
    if value is None or value == '':
        return None
    try:
        val = int(value)
        if 1 <= val <= 366:
            return val
        return None  # RECHAZA si < 1 o > 366
    except (ValueError, TypeError):
        return None
```

**El problema:** Si el user pasa `periodo_dias=0` o `periodo_dias=367`, se rechaza silenciosamente.

---

## 2. CAUSA RAÍZ #2: PDF/Step3 Totales Absurdos (0.83€/mes, +1224€/año)

### Diagnosis
**Hay 3 problemas independientes que se combinan:**

#### 2A. IVA se guarda como STRING en lugar de FLOAT
**Evidencia:**
```
IVA(€)=21         ← Debería ser número, no "21" string
IVA(%)=21%        ← Correcto
```

**Causa:** En `loadData()` línea 87:
```javascript
iva: data.iva ?? '',  // ← DEFAULT '', NO 0
```

Cuando se actualiza:
```javascript
const payload = buildPayload(formData);
// ... pero buildPayload NO normaliza iva a float
```

No hay un parseNumberInput() o parseFloat() para IVA en buildPayload().

#### 2B. IEE (Impuesto Eléctrico) se guarda como string OR ignorado
**Evidencia:**
```
impuesto_electrico: data.impuesto_electrico ?? '',  // STRING VACÍO
```

**Causa en backend (`comparador.py` línea 587):**
```python
iee_importe = _to_float(getattr(factura, 'impuesto_electrico', None))
# Si es '', _to_float('') devuelve None
```

El comparador espera un número, pero recibe string vacío.

#### 2C. Alquiler Contador Persistencia INCORRECTA
**Evidencia:** 21.28€ para 32 días (ABSURDO, debería ser ~0.85€)

**Root Cause:** El campo `alquiler_contador` en DB es un IMPORTE EN €, no una tasa diaria.

**Esperado:**
```
alquiler_contador_anual = 0.80 € (hardcoded)
alquiler_periodo = 0.80 € / 365 * 32 = 0.0700 €
```

**Real (Bug):**
- El user ve `21.28` en Step2 (probablemente porque OCR extrajo mal)
- Se guarda `21.28` directamente en DB como importe para TODO el período
- El comparador asume `alquiler_importe` = 21.28€ (para 32 días!!!)
- Cálculo: `ahorro_diario = (21.28 / 32) * 30 / 365 * 365 = ?` → ABSURDO

**Fix requerido:** Guardar alquiler como ESTIMADO por periodo, o convertir a tasa anual.

#### 2D. Periodo_dias NULL o STRING bloquea comparador
**Evidencia:** Error "422 PERIOD_REQUIRED" en Step3

**Causa:** `comparador.py` línea 527:
```python
dias_facturado = int(getattr(factura, 'periodo_dias', None))
# Si es None o '', falla con ValueError
```

---

## 3. CAUSA RAÍZ #3: Step3/PDF no usa valores persistidos, usa defaults

**Archivo:** `app/wizard/[id]/step-3-comparar/page.jsx`

```javascript
// ❌ RECARGA LOS DATOS EN LUGAR DE USAR LOS DE STEP2
const [formData, setFormData] = useState(null);

useEffect(() => {
  async function loadData() {
    const data = await getFactura(params.id);
    // ESPERA: ¿De dónde saca los nuevos valores? ¿De la DB o del Context?
    setFormData(data);  // ← RECARGA DESDE DB
  }
  loadData();
}, [params.id]);
```

**Problema:** Si los valores NO se guardaron correctamente en Step2, Step3 recibe garbage.

---

## 4. ROOT CAUSE SUMMARY (Prioridad)

| # | Causa | Ubicación | Severidad | Fix |
|---|-------|-----------|-----------|-----|
| 1A | `periodo_dias` = '' en loadData merge defensivo | Step2 line 77 | P0 | Default a `0` si no existe, luego validar |
| 1B | `isValid()` no detecta 0 como válido | Step2 line 315 | P0 | Cambiar isValid para números === 0 |
| 2A | IVA se guarda como string '' | Step2 line 87 + buildPayload | P0 | parseNumberInput() en buildPayload |
| 2B | IEE string vacío, no calcula | Step2 line 89 + backend | P0 | Validar que IEE sea float, no vacío |
| 2C | Alquiler_contador 21.28€ = ERROR | DB + comparador | P0 | Normalizar a tasa anual (0.80€) o período |
| 3 | Backend _normalize_periodo_dias rechaza silencios | webhook.py line 538 | P0 | Loguear rechazos + devolver error |
| 4 | Backsolve en comparador usa IVA string | comparador.py line 587 | P0 | Forzar _to_float() en todos los campos |

---

## 5. PATCHES EXACTOS (Frontend + Backend)

### PATCH 1: Frontend - Step2 (buildPayload + loadData + isValid)

**File:** `app/wizard/[id]/step-2-validar/page.jsx`

```diff
--- ANTES: Línea 77
+++ DESPUÉS: Línea 77
- periodo_dias: periodo_dias_calculado ?? '',  // ⭐ PROBLEMA: '' si null
+ periodo_dias: periodo_dias_calculado || 0,   // ✅ FIX: 0 si null (es inválido pero numérico)

--- ANTES: Línea 87-89
+++ DESPUÉS: Línea 87-89
- iva: data.iva ?? '',  // ⚠️ STRING VACÍO
- iva_porcentaje: data.iva_porcentaje != null ? ... : 21,
- impuesto_electrico: data.impuesto_electrico ?? '',  // ⚠️ STRING VACÍO
+ iva: data.iva ?? 0,  // ✅ FIX: 0 si null (número)
+ iva_porcentaje: data.iva_porcentaje != null ? ... : 21,
+ impuesto_electrico: data.impuesto_electrico ?? 0,  // ✅ FIX: 0 si null (número)

--- ANTES: Línea 315 (isValid)
+++ DESPUÉS: Línea 315
- const isValid = (val) => val !== null && val !== undefined && String(val).trim().length > 0;
+ const isValid = (val) => {
+   if (val === null || val === undefined) return false;
+   if (typeof val === 'number') return val > 0;  // Para números, > 0 es válido
+   return String(val).trim().length > 0;  // Para strings, no vacíos
+ };

--- ANTES: Línea 346 (buildPayload - parseNumberInput)
+++ DESPUÉS: Línea 346
- // El buildPayload ya hace parseInt para periodo_dias
- // PERO NO TRATA IVA NI IEE
+ // Función helper
+ const parseNumberInput = (val) => {
+   if (val === null || val === undefined || val === '') return 0;
+   const parsed = parseFloat(val);
+   return isNaN(parsed) ? 0 : parsed;
+ };
+
+ // En buildPayload:
  const payload = {
    ...
-   iva: Number.isFinite(parseInt(data.iva, 10)) ? parseInt(data.iva, 10) : null,
+   iva: parseNumberInput(data.iva),  // ✅ FIX: number or 0, never string
    iva_porcentaje: data.iva_porcentaje ? parseFloat(data.iva_porcentaje) : 21,
-   impuesto_electrico: Number.isFinite(parseInt(data.impuesto_electrico, 10)) 
-     ? parseInt(data.impuesto_electrico, 10) : null,
+   impuesto_electrico: parseNumberInput(data.impuesto_electrico),  // ✅ FIX: float or 0
    periodo_dias: Number.isFinite(parseInt(data.periodo_dias, 10))
      ? parseInt(data.periodo_dias, 10)
      : null,
  };
+ console.log(`%c [STEP2-PAYLOAD-NORMALIZED] `, "background: #10b981; color: #fff;", {
+   periodo_dias: payload.periodo_dias,
+   iva: typeof payload.iva, "=>", payload.iva,
+   iva_porcentaje: payload.iva_porcentaje,
+   impuesto_electrico: typeof payload.impuesto_electrico, "=>", payload.impuesto_electrico,
+ });
```

### PATCH 2: Backend - Webhook (normalizadores + logging)

**File:** `app/routes/webhook.py`

```diff
--- ANTES: Línea 515-540
+++ DESPUÉS: Línea 515-540

+ import logging
+ logger = logging.getLogger(__name__)

  def _normalize_iva_porcentaje(value):
    """Normaliza IVA % a float [0-100]"""
    if value is None or value == '':
      return 21.0  # Default 21%
    try:
      val = float(value)
      if 0 < val <= 100:
        return val
-     return 21.0  # Reject silently
+     logger.warning(f"[STEP2] IVA % rechazado: {val} (fuera rango)")
+     return None  # ✅ FIX: devolver None para que frontend lo vea
    except (ValueError, TypeError):
      return None
  
  def _normalize_periodo_dias(value):
    """Normaliza periodo_dias a int [1-366]"""
    if value is None or value == '' or value == 0:
-     return None
+     logger.warning(f"[STEP2] periodo_dias rechazado: {value} (nulo o cero)")
+     return None  # ✅ FIX: loguear el rechazo
    try:
      val = int(value)
      if 1 <= val <= 366:
        return val
-     return None  # Reject silently
+     logger.warning(f"[STEP2] periodo_dias rechazado: {val} (fuera rango 1-366)")
+     return None  # ✅ FIX: loguear
    except (ValueError, TypeError):
+     logger.warning(f"[STEP2] periodo_dias rechazado: {value} (no convertible a int)")
      return None

+ def _normalize_numeric_field(name: str, value, min_val=0.0, max_val=9999.99):
+   """Normaliza campos numéricos (IVA €, IEE, alquiler, etc)"""
+   if value is None or value == '':
+     return None  # Permitir nulos
+   try:
+     val = float(value)
+     if min_val <= val <= max_val:
+       return val
+     logger.warning(f"[STEP2] {name}={val} fuera rango [{min_val}, {max_val}]")
+     return None
+   except (ValueError, TypeError):
+     logger.warning(f"[STEP2] {name}={value} no es número")
+     return None

  @router.put("/facturas/{factura_id}")
  def update_factura(factura_id: int, factura_update: FacturaUpdate, db: Session = Depends(get_db)):
    # ... existing code ...
    
    logger.info(
-     "🔍 [AUDIT STEP2] Payload recibido factura_id=%s: periodo_dias=%s, iva_porc=%s, iva_eur=%s, iee_eur=%s, alquiler=%s",
+     "🔍 [AUDIT STEP2] Payload RECIBIDO factura_id=%s: periodo_dias=%s (type=%s), iva_porc=%s, iva_eur=%s (type=%s), iee_eur=%s (type=%s), alquiler=%s",
      factura_id,
      update_data.get("periodo_dias"),
+     type(update_data.get("periodo_dias")).__name__,
      update_data.get("iva_porcentaje"),
      update_data.get("iva"),
+     type(update_data.get("iva")).__name__,
      update_data.get("impuesto_electrico"),
+     type(update_data.get("impuesto_electrico")).__name__,
      update_data.get("alquiler_contador")
    )
    
    for key, value in update_data.items():
      # ... existing CUPS/ATR normalization ...
      if key == "iva_porcentaje":
        value = _normalize_iva_porcentaje(value)
      if key == "periodo_dias":
        value = _normalize_periodo_dias(value)
+     if key == "iva":
+       value = _normalize_numeric_field("iva", value, min_val=0, max_val=500)
+     if key == "impuesto_electrico":
+       value = _normalize_numeric_field("impuesto_electrico", value, min_val=0, max_val=200)
+     if key == "alquiler_contador":
+       # ALQUILER: si viene > 1, asumir que es estimación para el período
+       # Si viene < 1, es tasa diaria (raro)
+       val = _normalize_numeric_field("alquiler_contador", value, min_val=0, max_val=50)
+       if val and val > 1:
+         # Convertir a tasa anual estándar si es muy alto
+         logger.warning(f"[STEP2] alquiler_contador={val}€ > 1, asumiendo es estimado para período")
+       value = val
      setattr(factura, key, value)

    # ... existing completitud validation ...
    
    logger.info(
-     "✅ [AUDIT STEP2] Guardado final factura_id=%s: periodo_dias=%s, iva_porc=%s, iva_eur=%s, iee_eur=%s, estado=%s",
+     "✅ [AUDIT STEP2] Guardado FINAL factura_id=%s: periodo_dias=%s (type=%s, valid=%s), iva_porc=%s, iva_eur=%s (type=%s), iee_eur=%s (type=%s), alquiler=%s, estado=%s",
      factura.id,
      factura.periodo_dias,
+     type(factura.periodo_dias).__name__ if factura.periodo_dias else 'None',
+     1 <= (factura.periodo_dias or 0) <= 366,
      factura.iva_porcentaje,
      factura.iva,
+     type(factura.iva).__name__ if factura.iva else 'None',
      factura.impuesto_electrico,
+     type(factura.impuesto_electrico).__name__ if factura.impuesto_electrico else 'None',
+     factura.alquiler_contador,
      factura.estado_factura
    )
```

### PATCH 3: Backend - Comparador (Forzar tipos numéricos)

**File:** `app/services/comparador.py` línea 587

```diff
  # Obtener valores de la factura
  total_factura = current_total
  iva_importe = _to_float(getattr(factura, 'iva', None))
  iee_importe = _to_float(getattr(factura, 'impuesto_electrico', None))
  alquiler_importe = _to_float(getattr(factura, 'alquiler_contador', None)) or 0.0
  
+ # ✅ LOGGING DE DIAGNOSTICO
+ logger.info(
+   f"[PO-INPUTS] factura_id={factura.id}: iva={iva_importe} (type={type(factura.iva).__name__}), "
+   f"iee={iee_importe} (type={type(factura.impuesto_electrico).__name__}), "
+   f"alq={alquiler_importe}, periodo={factura.periodo_dias}"
+ )
  
  # Determinar IVA %
  if hasattr(factura, 'iva_porcentaje') and factura.iva_porcentaje is not None:
    iva_pct_reconstruccion = float(factura.iva_porcentaje) / 100.0
  else:
    iva_pct_reconstruccion = 0.21
  
+ # ✅ VALIDACION: Si periodo_dias es null/0, ABORTAR con error descriptivo
+ if not factura.periodo_dias or factura.periodo_dias <= 0 or factura.periodo_dias > 366:
+   raise DomainError(
+     code="PERIOD_INVALID",
+     message=f"periodo_dias inválido: {factura.periodo_dias}. Requiere valores 1-366 (Step 2 obligatorio)."
+   )
  
  # BACKSOLVE: Calcular subtotal
  baseline_method = "backsolve_subtotal_si"
  
  if iva_importe is not None and iva_importe > 0:
    # ... resto igual ...
```

### PATCH 4: Frontend - Step3 (validación antes de comparar)

**File:** `app/wizard/[id]/step-3-comparar/page.jsx`

```diff
  useEffect(() => {
    async function loadData() {
      // ...
      const data = await getFactura(params.id);
      
+     // ✅ VALIDACIÓN CRÍTICA
+     const periodo = data.periodo_dias;
+     if (!periodo || periodo <= 0 || periodo > 366) {
+       setError(`❌ Periodo inválido: ${periodo}. Vuelve a Step 2 para completar.`);
+       return;
+     }
+     
+     if (!data.iva) {
+       setError("❌ IVA no validado. Vuelve a Step 2.");
+       return;
+     }
+     
+     if (!data.consumo_kwh) {
+       setError("❌ Consumo no validado. Vuelve a Step 2.");
+       return;
+     }
      
      setFormData(data);
    }
    loadData();
  }, [params.id]);
  
  // En el botón "Comparar":
  const handleCompare = async () => {
    if (!formData) return;
    
+   // ✅ LOG CRÍTICO
+   console.log(`%c [STEP3] Iniciando comparación con:`, "background: #f59e0b; color: #fff; font-weight: bold;", {
+     periodo_dias: formData.periodo_dias,
+     consumo_kwh: formData.consumo_kwh,
+     potencia_p1_kw: formData.potencia_p1_kw,
+     iva: formData.iva,
+     impuesto_electrico: formData.impuesto_electrico,
+     total_factura: formData.total_factura,
+   });
    
    try {
      const result = await comparar(params.id, { ...formData });
      // ...
    } catch (error) {
      // ✅ MOSTRAR ERROR DESCRIPTIVO (no genérico)
      if (error.data?.code === "PERIOD_INVALID") {
        setError(`❌ ${error.data.message}`);
      } else {
        setError(error.message);
      }
    }
  };
```

---

## 6. VALIDATION CHECKLIST POST-FIX

### ✅ Step 1: Validación Frontend

```bash
1. Abrir /wizard/[id]/step-2-validar con factura que tiene periodo_dias=32
2. Verificar:
   - [ ] Campo "Periodo (días)" visible con valor "32"
   - [ ] isValid() devuelve true (botón SIGUIENTE no está disabled)
   - [ ] Console muestra: [STEP2-PAYLOAD-NORMALIZED] { periodo_dias: 32, ... }
   - [ ] NO hay "Periodo es obligatorio" en rojo
3. Rellenar manualmente:
   - [ ] Cambiar período a "45"
   - [ ] Verificar que guarda (AutoSave Status: "saved")
4. Recarga la página (F5):
   - [ ] Período sigue siendo "45"
   - [ ] No es "0" ni vacío
```

### ✅ Step 2: Validación Backend

```bash
1. Llamar PUT /facturas/{id} con payload:
   {
     "periodo_dias": 32,
     "iva": 7.50,
     "iva_porcentaje": 21,
     "impuesto_electrico": 5.11,
     "alquiler_contador": 0.85
   }
2. Verificar logs en stdout:
   - [ ] [AUDIT STEP2] Payload RECIBIDO: periodo_dias=32 (type=int), ...
   - [ ] [AUDIT STEP2] Guardado FINAL: periodo_dias=32 (type=int, valid=True), ...
   - [ ] NO hay "rechazado" warnings
3. GET /webhook/facturas/{id}:
   - [ ] periodo_dias: 32 (número, no string)
   - [ ] iva: 7.50 (número)
   - [ ] impuesto_electrico: 5.11 (número)
   - [ ] estado_factura: "lista_para_comparar"
```

### ✅ Step 3: Validación Comparador

```bash
1. Step 3 debería:
   - [ ] NO mostrar error "Periodo inválido"
   - [ ] NO mostrar error "IVA no validado"
   - [ ] Console muestra: [STEP3] Iniciando comparación con { periodo_dias: 32, ... }
2. Llamar POST /comparar:
   - [ ] Logs: [PO-INPUTS] factura_id=X: iva=7.50 (type=float), iee=5.11, ...
   - [ ] NO hay error "PERIOD_INVALID"
   - [ ] Se generan 9 ofertas
3. PDF:
   - [ ] Totales son LÓGICOS (no 0.83€/mes)
   - [ ] Ahorros anuales son realistas (5-20€ típicamente)
   - [ ] Alquiler contador: ~0.80€-2.50€/mes (no 21€)
```

---

## 7. CAUSA SECUNDARIA: Alquiler Contador 21.28€ (INVESTIGACIÓN PENDIENTE)

**¿De dónde viene 21.28€?**

1. ❓ ¿OCR extrae mal el alquiler? Buscar en `ocr.py` línea 1640-1650
2. ❓ ¿El user lo rellena manualmente y confunde con importe mensual?
3. ❓ ¿Es una tasa %. (21.28% de algo)?

**Recomendación:** Buscar factura con alquiler=21.28 y debuggear:
```python
# En comparador.py, añadir
logger.warning(f"[ALQUILER-DEBUG] factura_id={factura.id}: alquiler_raw={factura.alquiler_contador}, "
               f"days={factura.periodo_dias}, alquiler_daily={factura.alquiler_contador / factura.periodo_dias if factura.periodo_dias else '?'}")
```

---

## 8. TIMELINE RECOMENDADO

| Tarea | Tiempo | Prioridad |
|-------|--------|-----------|
| Patch 1 (Frontend buildPayload + isValid) | 30 min | P0 |
| Patch 2 (Backend normalizadores) | 30 min | P0 |
| Patch 3 (Comparador logging + validación) | 20 min | P0 |
| Testing manual (3 checklist) | 45 min | P0 |
| Deploy a Render | 10 min | P0 |
| **TOTAL** | **2h 15min** | - |

---

## 9. COMANDOS POST-DEPLOY

```bash
# Verificar logs en Render
heroku logs --tail -a rapidenergy

# Test manual con IDs de facturas reales
curl -X GET https://rapidenergy.onrender.com/webhook/facturas/328
# Verificar periodo_dias, iva, impuesto_electrico son NÚMEROS

# Comparar en Step3
POST https://rapidenergy.onrender.com/comparar
Body: { "factura_id": 328 }
# Esperar respuesta con 9 ofertas, sin error "PERIOD_INVALID"
```

---

## 10. NEXT: Causa Terciaria "0.83€/mes"

Si después de los patches aún genera 0.83€/mes:
```
Buscar en PDF generator cómo calcula ahorro_mensual:
  ahorro_mensual = ahorro_período × (30.437 / periodo_dias)
  
Con periodo_dias=32:
  ahorro_período debe ser ~27€ para llegar a 0.83€/mes
  
Eso significa comparador calculó ahorro = 27€ (POSIBLE si tarifas son bajas)
  
Solución: Validar que tarifas en BD no son cero.
```

---

**FIN DEL ANÁLISIS**
