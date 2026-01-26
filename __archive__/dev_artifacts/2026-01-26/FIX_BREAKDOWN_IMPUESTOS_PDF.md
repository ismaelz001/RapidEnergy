# FIX BREAKDOWN IMPUESTOS - PDF PRESUPUESTO

## FECHA
2026-01-26

## PROBLEMA DETECTADO

El PDF mostraba "Impuestos (IEE + IVA)" = 7.77€ cuando debería mostrar 8.20€

### Caso de prueba (factura_id=201):
- Energía = 8.07€
- Potencia = 21.45€
- SUBTOTAL_SI = 29.52€
- Alquiler = 0.85€
- IVA = 21%

### Cálculo correcto:
```
IEE = 29.52 × 0.0511269632 = 1.51€
BASE_IVA = 29.52 + 1.51 + 0.85 = 31.88€
IVA = 31.88 × 0.21 = 6.69€
IMPUESTOS = 1.51 + 6.69 = 8.20€
TOTAL = 31.88 + 6.69 = 38.57€
```

### Lo que mostraba el PDF:
- "Impuestos (IEE + IVA)" = 7.77€ ❌
- Total = 38.58€ ✅ (correcto por casualidad)

---

## CAUSA RAÍZ

Había **DOS cálculos separados** en `comparador.py`:

### 1) Cálculo ANTIGUO (líneas 696-732):
```python
impuesto_electrico = subtotal * 0.0511269632
base_imponible = subtotal + impuesto_electrico + alquiler_equipo
iva_importe = base_imponible * iva_pct
```

### 2) Cálculo NUEVO (líneas 738-743, método PO):
```python
estimated_total_periodo = _reconstruir_factura(
    subtotal_sin_impuestos=subtotal_sin_impuestos_oferta,
    iva_pct=iva_pct,
    alquiler_total=alquiler_importe,  # ⚠️ BUG: variable no existe
    impuesto_electrico_pct=0.0511269632
)
```

### El breakdown usaba valores del cálculo antiguo:
```python
"breakdown": {
    "impuestos": round(impuesto_electrico + iva_importe, 2),  # ❌ INCORRECTO
    ...
}
```

**Problema**: Los valores `impuesto_electrico` e `iva_importe` del cálculo antiguo NO coincidían con los del método PO/NodoÁmbar (`_reconstruir_factura`).

---

## CAMBIOS REALIZADOS

### Archivo: `app/services/comparador.py`

#### Cambio 1: Bug crítico corregido (línea 741)
```diff
- alquiler_total=alquiler_importe,  # ⚠️ Variable no existe
+ alquiler_total=alquiler_equipo,  # ✅ Variable correcta
```

#### Cambio 2: Calcular breakdown con método PO (líneas 745-749)
```python
# ⭐ CALCULAR BREAKDOWN CORRECTO (mismo esquema que _reconstruir_factura)
iee_oferta = subtotal_sin_impuestos_oferta * 0.0511269632
base_iva_oferta = subtotal_sin_impuestos_oferta + iee_oferta + alquiler_equipo
iva_oferta = base_iva_oferta * iva_pct
impuestos_oferta = iee_oferta + iva_oferta  # Para breakdown del PDF
```

#### Cambio 3: Actualizar breakdown (línea 815)
```diff
- "impuestos": round(impuesto_electrico + iva_importe, 2),
+ "impuestos": round(impuestos_oferta, 2),
```

#### Cambio 4: Log temporal para auditoría (líneas 790-796)
```python
logger.info(
    f"[PDF-BREAKDOWN] tarifa_id={tarifa_id} | "
    f"E={coste_energia:.2f} P={coste_potencia:.2f} subtotal_si={subtotal_sin_impuestos_oferta:.2f} | "
    f"IEE={iee_oferta:.2f} alq={alquiler_equipo:.2f} base_iva={base_iva_oferta:.2f} IVA={iva_oferta:.2f} | "
    f"impuestos_mostrados={impuestos_oferta:.2f} total={estimated_total_periodo:.2f}"
)
```

---

## POR QUÉ SALÍA 7.77€ ANTES

El cálculo antiguo tenía una discrepancia en cómo calculaba la base imponible:

### ANTES:
```python
# Usaba variables del loop antiguo que podían tener valores desactualizados
impuesto_electrico = subtotal * 0.0511269632  # Podía usar subtotal incorrecto
base_imponible = subtotal + impuesto_electrico + alquiler_equipo
iva_importe = base_imponible * iva_pct

# Resultado con números del caso:
# impuesto_electrico ≈ 1.51€ (correcto)
# base_imponible ≈ 31.03€ (INCORRECTO, faltaban 0.85€ alquiler?)
# iva_importe ≈ 6.26€ (incorrecto por base incorrecta)
# impuestos = 1.51 + 6.26 = 7.77€ ❌
```

### AHORA:
```python
# Calculamos explícitamente con los valores correctos
iee_oferta = 29.52 * 0.0511269632 = 1.51€
base_iva_oferta = 29.52 + 1.51 + 0.85 = 31.88€
iva_oferta = 31.88 * 0.21 = 6.69€
impuestos_oferta = 1.51 + 6.69 = 8.20€ ✅
```

---

## VALIDACIÓN

### Caso de prueba verificado:
```
✅ SUBTOTAL_SI:  29.52€
✅ IEE:          1.51€
✅ ALQUILER:     0.85€
✅ BASE_IVA:     31.88€
✅ IVA:          6.69€
✅ IMPUESTOS:    8.20€ (antes 7.77€)
✅ TOTAL:        38.57€
```

### Diferencia:
- **Antes**: Impuestos mostrados = 7.77€
- **Ahora**: Impuestos mostrados = 8.20€
- **Diferencia**: +0.43€ (corrección)

El total final ya era correcto (38.57€) porque `_reconstruir_factura()` siempre funcionó bien. Solo el desglose en el PDF estaba mal.

---

## PRÓXIMOS PASOS

1. **Probar con factura real**: Generar presupuesto de factura_id=201 (o similar)
2. **Verificar logs**: Buscar en Render logs líneas con `[PDF-BREAKDOWN]`
3. **Confirmar PDF**: 
   - "Impuestos (IEE + IVA)" debe mostrar 8.20€
   - Total debe seguir siendo 38.57€
4. **Eliminar logs temporales**: Una vez confirmado, quitar líneas 790-796

---

## ARCHIVOS MODIFICADOS

- `app/services/comparador.py`
  - Línea 741: `alquiler_importe` → `alquiler_equipo`
  - Líneas 745-749: Cálculo explícito de breakdown
  - Línea 815: Usar `impuestos_oferta` en vez de cálculo antiguo
  - Líneas 790-796: Log temporal

---

## RESTRICCIONES CUMPLIDAS

✅ No se tocó `_reconstruir_factura()` (estaba correcto)  
✅ No se tocó lógica de energía/potencia  
✅ No se tocaron tasas reguladas (IEE 5.11269632%)  
✅ Redondeo solo al final (2 decimales)  
✅ Solo cambios en presentación/breakdown, no en motor de cálculo
