# 🚧 P1: COMPARADOR COHERENTE - CAMBIOS PENDIENTES

## ✅ COMPLETADO
1. ✅ Modelo Comparativa añadido a `models.py`
2. ✅ Campo `periodo_dias` añadido a Factura
3. ✅ Migración SQL creada
4. ✅ `periodo_dias` añadido a local.db

## ⚠️ PENDIENTE (Aplicar manualmente por problemas de caracteres)

### ARCHIVO: `app/routes/webhook.py`

#### Cambio 1: Validación de periodo (línea ~66)

**BUSCAR:**
```python
    # Validación CUPS obligatoria
    if not factura.cups or not str(factura.cups).strip():
        errors["cups"] = "CUPS es obligatorio y no puede estar vacío"
    
    for field in REQUIRED_FACTURA_FIELDS:
```

**REEMPLAZAR POR:**
```python
    # Validación CUPS obligatoria
    if not factura.cups or not str(factura.cups).strip():
        errors["cups"] = "CUPS es obligatorio y no puede estar vacío"
    
    # P1: Validación PERIODO obligatoria
    if not factura.periodo_dias:
        if not (factura.fecha_inicio and factura.fecha_fin):
            errors["periodo"] = "Periodo es obligatorio (dias o fechas inicio/fin)"
    
    for field in REQUIRED_FACTURA_FIELDS:
```

#### Cambio 2: Añadir periodo_dias al update (línea ~337)

**BUSCAR** el bloque del `FacturaUpdate` Pydantic model (línea ~12-43) y añadir:
```python
class FacturaUpdate(BaseModel):
    atr: Optional[str] = None
    # ... otros campos ...
    cups: Optional[str] = None
    numero_factura: Optional[str] = None
    periodo_dias: Optional[int] = None  # AÑADIR ESTA LÍNEA
```

#### Cambio 3: Guardar periodo_dias en upload (línea ~280)

**BUSCAR** donde se crea `nueva_factura` y añadir:
```python
nueva_factura = Factura(
    filename=file.filename,
    cups=normalize_cups(ocr_data.get("cups")),
    # ... otros campos ...
    iva=ocr_data.get("iva"),
    periodo_dias=ocr_data.get("dias_facturados"),  # AÑADIR ESTA LÍNEA
)
```

---

### ARCHIVO: `app/services/comparador.py`

#### Cambio 1: Importar Comparativa (línea ~1-12)
```python
from datetime import date, datetime
import json
import logging
import re
from typing import Dict, Any, Optional

from sqlalchemy import inspect, text
from app.db.models import Comparativa  # AÑADIR ESTA LÍNEA

logger = logging.getLogger(__name__)
```

#### Cambio 2: Modificar compare_factura para periodo real (línea ~303+)

**BUSCAR la función `compare_factura` entera** y reemplazar por:

```python
def compare_factura(factura, db) -> Dict[str, Any]:
    """P1: Compara ofertas usando el periodo REAL de la factura"""
    current_total = _to_float(getattr(factura, "total_factura", None))
    if current_total is None or current_total <= 0:
        raise ValueError("La factura no tiene un total valido para comparar")

    required_fields = [
        "consumo_p1_kwh",
        "consumo_p2_kwh",
        "consumo_p3_kwh",
        "potencia_p1_kw",
        "potencia_p2_kw",
    ]
    missing = [
        field
        for field in required_fields
        if _to_float(getattr(factura, field, None)) is None
    ]
    if missing:
        raise ValueError(
            "La factura no tiene datos suficientes para comparar: "
            + ", ".join(missing)
        )

    # P1: PERIODO OBLIGATORIO
    periodo_dias = factura.periodo_dias
    if not periodo_dias:
        # Intentar calcular de fechas
        periodo_dias = _get_days(factura)
        if periodo_dias == 30:  # Fallback usado
            raise ValueError("Periodo de facturación no especificado. Añádelo en Step2.")
    
    consumo_p1 = _to_float(factura.consumo_p1_kwh) or 0.0
    consumo_p2 = _to_float(factura.consumo_p2_kwh) or 0.0
    consumo_p3 = _to_float(factura.consumo_p3_kwh) or 0.0
    potencia_p1 = _to_float(factura.potencia_p1_kw) or 0.0
    potencia_p2 = _to_float(factura.potencia_p2_kw) or 0.0

    result = db.execute(
        text("SELECT * FROM tarifas WHERE atr = :atr"),
        {"atr": "2.0TD"},
    )
    try:
        tarifas = result.mappings().all()
    except AttributeError:
        tarifas = [row._mapping for row in result.fetchall()]

    offers = []
    for tarifa in tarifas:
        modo_energia, prices = _resolve_energy_prices(tarifa)
        if modo_energia is None:
            continue

        p1_price, p2_price, p3_price = prices
        coste_energia = (
            (consumo_p1 * p1_price)
            + (consumo_p2 * p2_price)
            + (consumo_p3 * p3_price)
        )

        potencia_p1_price = _to_float(tarifa.get("potencia_p1_eur_kw_dia"))
       potencia_p2_price = _to_float(tarifa.get("potencia_p2_eur_kw_dia"))
        if potencia_p1_price is None or potencia_p2_price is None:
            coste_potencia = 0.0
            modo_potencia = "sin_potencia"
        else:
            coste_potencia = periodo_dias * (  # P1: USA PERIODO REAL
                (potencia_p1 * potencia_p1_price)
                + (potencia_p2 * potencia_p2_price)
            )
            modo_potencia = "tarifa"

        estimated_total_periodo = coste_energia + coste_potencia
        ahorro_periodo = current_total - estimated_total_periodo
        
        # P1: EQUIVALENTES CONSISTENTES
        ahorro_mensual_equiv = ahorro_periodo * (30.437 / periodo_dias)
        ahorro_anual_equiv = ahorro_periodo * (365 / periodo_dias)
        
        saving_percent = (
            (ahorro_periodo / current_total) * 100 if current_total > 0 else 0.0
        )

        tarifa_id = tarifa.get("id") or tarifa.get("tarifa_id")
        provider = _pick_value(
            tarifa,
            [
                "comercializadora",
                "provider",
                "empresa",
                "compania",
                "nombre_comercializadora",
                "nombre_comercializador",
                "brand",
            ],
            "Proveedor desconocido",
        )
        plan_name = _pick_value(
            tarifa,
            ["nombre", "plan_name", "plan", "tarifa", "nombre_tarifa", "nombre_plan"],
            "Tarifa 2.0TD",
        )

        offer = {
            "tarifa_id": tarifa_id,
            "provider": provider,
            "plan_name": plan_name,
            "estimated_total_periodo": round(estimated_total_periodo, 2),  # P1
            "ahorro_periodo": round(ahorro_periodo, 2),  # P1
            "ahorro_mensual_equiv": round(ahorro_mensual_equiv, 2),  # P1
            "ahorro_anual_equiv": round(ahorro_anual_equiv, 2),  # P1
            "saving_percent": round(saving_percent, 2),
            "tag": "balanced",
            "breakdown": {
                "periodo_dias": int(periodo_dias),  # P1
                "coste_energia": round(coste_energia, 2),
                "coste_potencia": round(coste_potencia, 2),
                "modo_energia": modo_energia,
                "modo_potencia": modo_potencia,
            },
        }

        offers.append(offer)

    completas = [item for item in offers if item["breakdown"]["modo_potencia"] == "tarifa"]
    parciales = [item for item in offers if item["breakdown"]["modo_potencia"] != "tarifa"]

    completas.sort(key=lambda item: item["estimated_total_periodo"])
    parciales.sort(key=lambda item: item["estimated_total_periodo"])

    for item in parciales:
        item["tag"] = "partial"

    if completas:
        max_saving = max(item["ahorro_periodo"] for item in completas)  # P1
        for item in completas:
            if item["ahorro_periodo"] == max_saving:
                item["tag"] = "best_saving"
            else:
                item["tag"] = "balanced"

    offers = completas + parciales

    # P1: PERSISTIR COMPARATIVA (AUDITORÍA)
    try:
        inputs_snapshot = {
            "cups": factura.cups,
            "atr": factura.atr,
            "potencia_p1": factura.potencia_p1_kw,
            "potencia_p2": factura.potencia_p2_kw,
            "consumo_p1": factura.consumo_p1_kwh,
            "consumo_p2": factura.consumo_p2_kwh,
            "consumo_p3": factura.consumo_p3_kwh,
        }
        
        comparativa = Comparativa(
            factura_id=factura.id,
            periodo_dias=periodo_dias,
            current_total=current_total,
            inputs_json=json.dumps(inputs_snapshot),
            offers_json=json.dumps(offers),
            status="ok"
        )
        db.add(comparativa)
        db.commit()
        db.refresh(comparativa)
        comparativa_id = comparativa.id
    except Exception as e:
        logger.error(f"Error persistiendo comparativa: {e}")
        comparativa_id = None

    _persist_results(db, factura.id, offers)

    return {
        "factura_id": factura.id,
        "comparativa_id": comparativa_id,  # P1
        "periodo_dias": periodo_dias,  # P1
        "current_total": round(current_total, 2),
        "offers": offers,
    }
```

---

### ARCHIVO: `app/wizard/[id]/step-2-validar/page.jsx`

#### Cambio: Añadir campo periodo_dias (después de total_factura)

**BUSCAR** en el formulario (aprox línea 400) y AÑADIR:

```jsx
// Después del campo total_factura
<div>
  <label htmlFor="periodo_dias" className="label text-white">
    Periodo de facturación (días) <span className="text-xs text-blue-400 ml-1">*</span>
  </label>
  <div className="flex gap-2 mb-2">
    <button
      type="button"
      onClick={() => updateFormData({ periodo_dias: 30 })}
      className={`px-3 py-1 rounded text-sm ${form.periodo_dias === 30 ? 'bg-azul-control text-white' : 'bg-white/10 text-gris-secundario'}`}
    >
      Mensual (30)
    </button>
    <button
      type="button"
      onClick={() => updateFormData({ periodo_dias: 60 })}
      className={`px-3 py-1 rounded text-sm ${form.periodo_dias === 60 ? 'bg-azul-control text-white' : 'bg-white/10 text-gris-secundario'}`}
    >
      Bimensual (60)
    </button>
  </div>
  <Input
    id="periodo_dias"
    name="periodo_dias"
    type="number"
    value={form.periodo_dias || ''}
    onChange={handleChange}
    validated={isValid(form.periodo_dias)}
    placeholder="30"
  />
  <p className="text-xs text-gris-secundario mt-1">
    Si no lo sabes, pon 30 (mensual) o 60 (bimensual)
  </p>
</div>
```

Y añadir `periodo_dias` a `requiredFields`:
```javascript
const requiredFields = [
  'cups',
  'atr',
  'potencia_p1',
  'potencia_p2',
  'consumo_p1',
  'consumo_p2',
  'consumo_p3',
  'total_factura',
  'periodo_dias'  // AÑADIR
];
```

---

### ARCHIVO: `app/wizard/[id]/step-3-comparar/page.jsx`

#### Cambio: Mostrar periodo y equivalentes

**BUSCAR** el Hero de ahorro (línea ~153) y MODIFICAR:

```jsx
{/* Hero de ahorro - P1: MOSTRAR EQUIVALENTES */}
<div className="bg-gradient-to-r from-[#14532D]/30 to-[#16A34A]/5 border border-[#16A34A]/30 rounded-2xl p-8 text-center shadow-lg shadow-green-900/10">
  <span className="text-sm font-bold tracking-widest text-[#16A34A] uppercase mb-1 block">
    Ahorro anual estimado ({result.periodo_dias || 30} días periodo)
  </span>
  <div className="flex items-baseline justify-center gap-2 mb-4">
    <h2 className="text-6xl font-black text-[#16A34A] tracking-tighter drop-shadow-sm">
      {(bestOffer?.ahorro_anual_equiv || 0).toFixed(0)}
    </h2>
    <span className="text-2xl font-bold text-[#16A34A]/80">€/año</span>
  </div>
  
  <div className="inline-flex items-center gap-4 text-sm text-[#94A3B8] bg-[#020617]/50 rounded-full px-4 py-2 border border-white/5">
    <div>
      <span className="text-gray-500 mr-1">Actual ({result.periodo_dias}d):</span>
      <span className="text-white font-mono line-through opacity-70">{currentTotalDisplay.toFixed(2)}€</span>
    </div>
    <div className="text-white">→</div>
    <div>
      <span className="text-gray-500 mr-1">Nueva ({result.periodo_dias}d):</span>
      <span className="text-[#16A34A] font-bold font-mono">
        {bestOffer && Number.isFinite(bestOffer.estimated_total_periodo) ? bestOffer.estimated_total_periodo.toFixed(2) : '---'}€
      </span>
    </div>
  </div>
  
  {result.comparativa_id && (
    <div className="mt-4 text-xs text-gris-secundario">
      Comparativa #{result.comparativa_id} guardada
    </div>
  )}
</div>
```

Y en el panel de selección (línea ~213):
```jsx
<p className="text-gris-texto">
  El cliente ahorrará <span className="font-bold text-verde-ahorro">
    {(selectedOffer.ahorro_anual_equiv || 0).toFixed(0)}€ al año
  </span> ({(selectedOffer.ahorro_mensual_equiv || 0).toFixed(2)}€/mes equiv.)
</p>
```

---

## 📋 RESUMEN DE ARCHIVOS A MODIFICAR

1. ✅ `app/db/models.py` - HECHO
2. ⚠️ `app/routes/webhook.py` - 3 cambios pendientes
3. ⚠️ `app/services/comparador.py` - 2 cambios pendientes
4. ⚠️ `app/wizard/[id]/step-2-validar/page.jsx` - 1 cambio pendiente
5. ⚠️ `app/wizard/[id]/step-3-comparar/page.jsx` - 2 cambios pendientes

---

## 🧪 TESTS DESPUÉS DE APLICAR

```bash
# Test 1: Periodo obligatorio
1. Subir factura
2. Step2: NO poner periodo
3. Intentar "SIGUIENTE" → debe bloquearse
4. Poner periodo_dias = 30
5. "SIGUIENTE" → debe permitir

# Test 2: Comparador con periodo real
1. Completar Step1 y Step2 con periodo_dias = 60
2. Step3: Ver ofertas
3. Verificar en JSON response:
   - periodo_dias: 60
   - ahorro_periodo (para 60 días)
   - ahorro_mensual_equiv (equivalente a 30 días)
   - ahorro_anual_equiv (equivalente a 365 días)

# Test 3: Comparativa persistida
1. Completar flujo hasta Step3
2. Verificar en BD:
   SELECT * FROM comparativas ORDER BY id DESC LIMIT 1;
   - Debe tener factura_id, periodo_dias, current_total, offers_json
3. Frontend debe mostrar "Comparativa #{id} guardada"
```

---

**Estado:** Modelos y migraciones hechas. Código listo pero pendiente de aplicación manual.
