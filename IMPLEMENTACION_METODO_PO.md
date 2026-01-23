# IMPLEMENTACIÓN MÉTODO PO/NODOÁMBAR - COMPARADOR DE TARIFAS

## FECHA
2026-01-23

## OBJETIVO
Alinear el cálculo de ahorro del comparador energético con el método exacto usado por el PO/NodoÁmbar, eliminando el error conceptual de comparar la factura original contra ofertas calculadas.

## PROBLEMA ANTERIOR

❌ **Método INCORRECTO** (antes):
```python
ahorro = total_factura_original - estimated_total_nueva_oferta
```

**Problemas:**
- Usaba el total real de la factura como baseline
- Comparaba "manzanas con naranjas" (factura real vs cálculo reconstruido)
- Diferentes metodologías entre actual y nuevas ofertas

## SOLUCIÓN IMPLEMENTADA

✅ **Método CORRECTO** (ahora - BACKSOLVE):
```python
# 1. Recuperar subtotal sin impuestos de factura actual "hacia atrás"
base_iva = total_factura - iva_importe
subtotal_si_actual = base_iva - iee_importe - alquiler_importe

# 2. Reconstruir factura actual con la MISMA lógica que ofertas
total_actual_reconstruido = _reconstruir_factura(
    subtotal_sin_impuestos=subtotal_si_actual,
    iva_pct=...,
    alquiler_total=...,
    impuesto_electrico_pct=0.0511269632
)

# 3. Reconstruir cada oferta
total_oferta_reconstruido = _reconstruir_factura(...)

# 4. Comparar las dos reconstrucciones
ahorro = total_actual_reconstruido - total_oferta_reconstruido
```

## CAMBIOS REALIZADOS

### 1. Nueva función `_reconstruir_factura()` (líneas ~418-456)

Implementa el esquema PO/NodoÁmbar SIMPLIFICADO:

```python
def _reconstruir_factura(
    subtotal_sin_impuestos: float,
    iva_pct: float,
    alquiler_total: float = 0.0,
    impuesto_electrico_pct: float = 0.0511269632
) -> float:
    """
    1. Impuesto eléctrico = subtotal × 5.11269632%
    2. Base IVA = subtotal + IEE + alquiler
    3. IVA = base_IVA × iva_pct
    4. TOTAL = base_IVA + IVA
    """
```

**Nota importante:** Esta función **NO calcula** energía ni potencia. Solo totaliza desde un subtotal ya calculado.

### 2. BACKSOLVE del subtotal sin impuestos (líneas ~527-590)

**ANTES del loop de ofertas**, se calcula el subtotal sin impuestos de la factura actual mediante ingeniería inversa:

```python
# Obtener importes de la factura
total_factura = factura.total_factura
iva_importe = factura.iva
iee_importe = factura.impuesto_electrico  
alquiler_importe = factura.alquiler_contador

# BACKSOLVE
base_iva = total_factura - iva_importe
subtotal_si_actual = base_iva - iee_importe - alquiler_importe
```

**Validaciones:**
- Si `iva_importe` es None, se calcula desde `iva_porcentaje`
- Si `subtotal_si_actual < 0` o muy bajo → fallback a `current_total`

### 3. Reconstrucción de tarifa actual (líneas ~566-590)

```python
total_actual_reconstruido = _reconstruir_factura(
    subtotal_sin_impuestos=subtotal_si_actual,  # Del backsolve
    iva_pct=iva_pct_reconstruccion,
    alquiler_total=alquiler_importe,  # Importe total (no diario)
    impuesto_electrico_pct=0.0511269632
)
```

### 4. Reconstrucción de ofertas (dentro del loop)

Para cada oferta se calcula:
```python
# Energía + Potencia (como antes)
subtotal_sin_impuestos_oferta = coste_energia + coste_potencia

# Reconstruir con la MISMA función
estimated_total_periodo = _reconstruir_factura(
    subtotal_sin_impuestos=subtotal_sin_impuestos_oferta,
    iva_pct=iva_pct,
    alquiler_total=alquiler_importe,  # Mismo alquiler que factura actual
    impuesto_electrico_pct=0.0511269632
)
```

### 5. Cálculo de ahorro CORREGIDO

```python
# Si backsolve tuvo éxito
if baseline_method == "backsolve_subtotal_si":
    ahorro_periodo = total_actual_reconstruido - estimated_total_periodo
# Si hubo que usar fallback
else:
    ahorro_periodo = current_total - estimated_total_periodo
```

### 6. Metadata ampliada en respuesta

```python
{
    "current_total": ...,  # Total original (OCR)
    "total_actual_reconstruido": ...,  # Total reconstruido
    "subtotal_si_actual": ...,  # Subtotal recuperado
    "baseline_method": "backsolve_subtotal_si" | "fallback_current_total",
    "metodo_calculo": "PO/NodoAmbar" | "Fallback",
    "diff_vs_current_total": ...,  # Diferencia entre reconstruido y original
    ...
}
```

## LOGGING INCORPORADO

```
[PO] Backsolve: total=XX iva_imp=YY base_iva=ZZ iee=AA alq=BB subtotal_si=CC
[PO] Factura actual reconstruida: XX€ vs original: YY€ (diff: ZZ€) method=backsolve_subtotal_si
```

## FORTALEZAS DEL MÉTODO

✅ **NO inventa precios**: Usa solo importes reales de la factura
✅ **Comparación justa**: Ambas facturas reconstruidas con misma lógica
✅ **Trazable**: Logs muestran cada paso del backsolve
✅ **Robusto**: Fallback automático si faltan datos
✅ **Alineado con PO**: Mismo razonamiento que NodoÁmbar

## LIMITACIONES CONOCIDAS

⚠️ **Precisión del backsolve**: Si la factura original incluye conceptos no modelados (descuentos especiales, ajustes, batería virtual), el subtotal recuperado puede diferir ligeramente.

**Solución futura**: Añadir campos `energia_sin_impuestos`, `potencia_sin_impuestos`, `descuento_energia` al modelo `Factura` para evitar backsolve.

## CASOS ESPECIALES

### Alquiler contador
- Se usa el importe **total** del periodo (no se calcula diario)
- Si no existe en factura: 0

### IVA
- Prioridad 1: Usar `iva_porcentaje` de factura
- Fallback: 21%

### Impuesto eléctrico
- Constante: 5.11269632% sobre subtotal sin impuestos

## VALIDACIÓN

✅ Código compila sin errores
✅ Mantiene compatibilidad con API existente
✅ Sigue especificaciones PO (sin inventar precios)
✅ Logging completo para auditoría

## ARCHIVOS MODIFICADOS

- `app/services/comparador.py` (único archivo modificado)

## PRÓXIMOS PASOS RECOMENDADOS

1. **Probar con facturas reales** y comparar contra NodoÁmbar
2. **Analizar diff_vs_current_total**: Si sistemáticamente >5%, investigar si faltan conceptos
3. **Considerar añadir campos** `energia_si`, `potencia_si`, `otros_conceptos_si` al modelo para evitar backsolve
4. **Documentar** qué hacer cuando `baseline_method == "fallback_current_total"`
