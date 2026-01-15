# 📋 Plan de Implementación - Soporte Tarifas 3.0TD

> **Fecha:** 2026-01-15  
> **Objetivo:** Ampliar el comparador para soportar tarifas comerciales/industriales 3.0TD (15-450 kW)

---

## 🎯 1. RESUMEN EJECUTIVO

### ¿Qué es 3.0TD?
- **Tarifa comercial/industrial** para potencias entre **15 kW y 450 kW**
- Tiene **6 periodos** de energía y potencia (vs 3 periodos en 2.0TD)
- Misma lógica de cálculo que 2.0TD, solo más periodos

### Ventaja de implementación
✅ **El modelo de datos YA está preparado** - La tabla `facturas` ya tiene campos `consumo_p4/p5/p6` y `potencia_p3/p4/p5/p6`  
✅ **Detección automática** - Si `potencia_p1 >= 15kW` → buscar tarifas 3.0TD  
✅ **Reutilización de código** - Mismas fórmulas, solo iterar sobre 6 periodos en vez de 3

---

## 📊 2. COMPARATIVA 2.0TD vs 3.0TD

| Concepto | 2.0TD (Doméstico) | 3.0TD (Comercial) |
|----------|-------------------|-------------------|
| **Potencia** | < 15 kW | 15 - 450 kW |
| **Periodos energía** | P1, P2, P3 | P1, P2, P3, P4, P5, P6 |
| **Periodos potencia** | P1, P2 | P1, P2, P3, P4, P5, P6 |
| **Campos factura** | 3 consumos + 2 potencias | 6 consumos + 6 potencias |
| **IVA** | 10% (< 10kW) o 21% | 21% siempre |
| **Impuesto Eléctrico** | 5.1127% | 5.1127% (igual) |

---

## 🔧 3. CAMBIOS NECESARIOS EN EL CÓDIGO

### 3.1. Modificar `compare_factura()` en `comparador.py`

#### **Cambio 1: Detección automática de ATR**
```python
# ANTES (línea 379-382):
result = db.execute(
    text("SELECT * FROM tarifas WHERE atr = :atr"),
    {"atr": "2.0TD"},
)

# DESPUÉS:
# Detectar ATR según potencia
potencia_p1 = _to_float(factura.potencia_p1_kw) or 0.0
if potencia_p1 >= 15:
    atr = "3.0TD"
else:
    atr = "2.0TD"

result = db.execute(
    text("SELECT * FROM tarifas WHERE atr = :atr"),
    {"atr": atr},
)
```

#### **Cambio 2: Validación de campos según ATR**
```python
# ANTES (línea 338-354):
required_fields = [
    "consumo_p1_kwh",
    "consumo_p2_kwh",
    "consumo_p3_kwh",
    "potencia_p1_kw",
    "potencia_p2_kw",
]

# DESPUÉS:
if atr == "2.0TD":
    required_fields = [
        "consumo_p1_kwh", "consumo_p2_kwh", "consumo_p3_kwh",
        "potencia_p1_kw", "potencia_p2_kw",
    ]
else:  # 3.0TD
    required_fields = [
        "consumo_p1_kwh", "consumo_p2_kwh", "consumo_p3_kwh",
        "consumo_p4_kwh", "consumo_p5_kwh", "consumo_p6_kwh",
        "potencia_p1_kw", "potencia_p2_kw", "potencia_p3_kw",
        "potencia_p4_kw", "potencia_p5_kw", "potencia_p6_kw",
    ]
```

#### **Cambio 3: Cálculo dinámico de energía y potencia**
```python
# ANTES (línea 373-377):
consumo_p1 = _to_float(factura.consumo_p1_kwh) or 0.0
consumo_p2 = _to_float(factura.consumo_p2_kwh) or 0.0
consumo_p3 = _to_float(factura.consumo_p3_kwh) or 0.0
potencia_p1 = _to_float(factura.potencia_p1_kw) or 0.0
potencia_p2 = _to_float(factura.potencia_p2_kw) or 0.0

# DESPUÉS:
# Leer consumos según ATR
consumos = []
potencias = []
num_periodos = 6 if atr == "3.0TD" else 3

for i in range(1, num_periodos + 1):
    consumos.append(_to_float(getattr(factura, f"consumo_p{i}_kwh", None)) or 0.0)

# Potencia: 2.0TD solo tiene P1/P2, 3.0TD tiene P1-P6
num_periodos_pot = 6 if atr == "3.0TD" else 2
for i in range(1, num_periodos_pot + 1):
    potencias.append(_to_float(getattr(factura, f"potencia_p{i}_kw", None)) or 0.0)
```

#### **Cambio 4: Bucle de cálculo dinámico**
```python
# ANTES (línea 408-431):
coste_energia = (
    (consumo_p1 * p1_price)
    + (consumo_p2 * p2_price)
    + (consumo_p3 * p3_price)
)

coste_potencia = periodo_dias * (
    (potencia_p1 * potencia_p1_price)
    + (potencia_p2 * potencia_p2_price)
)

# DESPUÉS:
# Calcular energía dinámicamente
coste_energia = 0.0
for i in range(num_periodos):
    precio = _to_float(tarifa.get(f"energia_p{i+1}_eur_kwh"))
    if precio is None:
        precio = _to_float(tarifa.get("energia_p1_eur_kwh")) or 0.0  # Fallback a P1
    coste_energia += consumos[i] * precio

# Calcular potencia dinámicamente
coste_potencia = 0.0
for i in range(num_periodos_pot):
    precio = _to_float(tarifa.get(f"potencia_p{i+1}_eur_kw_dia"))
    if precio is None and i < 2:  # Fallback solo para P1/P2
        precio = 0.10 if i == 0 else 0.04
    if precio:
        coste_potencia += potencias[i] * precio

coste_potencia *= periodo_dias
```

---

## 🗄️ 4. ESTRUCTURA DE TARIFAS 3.0TD EN BBDD

### Ejemplo de tarifa 3.0TD:
```json
{
  "nombre": "Tarifa 3.0TD Comercial",
  "comercializadora": "Endesa",
  "atr": "3.0TD",
  "tipo": "fija",
  "energia_p1_eur_kwh": 0.145,
  "energia_p2_eur_kwh": 0.130,
  "energia_p3_eur_kwh": 0.115,
  "energia_p4_eur_kwh": 0.110,
  "energia_p5_eur_kwh": 0.105,
  "energia_p6_eur_kwh": 0.095,
  "potencia_p1_eur_kw_dia": 0.120,
  "potencia_p2_eur_kw_dia": 0.110,
  "potencia_p3_eur_kw_dia": 0.100,
  "potencia_p4_eur_kw_dia": 0.090,
  "potencia_p5_eur_kw_dia": 0.080,
  "potencia_p6_eur_kw_dia": 0.070
}
```

---

## ✅ 5. CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Backend (Comparador)
- [ ] Modificar `compare_factura()` para detectar ATR automáticamente
- [ ] Adaptar validación de campos según ATR
- [ ] Hacer cálculo de energía/potencia dinámico (bucles)
- [ ] Ajustar IVA (21% siempre para 3.0TD)
- [ ] Actualizar tests unitarios

### Fase 2: Base de Datos
- [ ] Obtener tarifas 3.0TD de comercializadoras (Endesa, Iberdrola, Naturgy)
- [ ] Insertar tarifas en tabla `tarifas` con `atr = '3.0TD'`
- [ ] Verificar que todos los campos P1-P6 estén completos

### Fase 3: Frontend (Wizard)
- [ ] Modificar formulario Step 1 para mostrar P4/P5/P6 si potencia >= 15kW
- [ ] Añadir validación condicional de campos
- [ ] Actualizar UI para mostrar "Tarifa 3.0TD" en resultados

### Fase 4: Testing
- [ ] Probar con factura real 3.0TD (potencia >= 15kW)
- [ ] Verificar que solo muestre tarifas 3.0TD
- [ ] Comparar cálculos con factura real del cliente

---

## 🚨 6. PENDIENTES ACTUALES (ANTES DE 3.0TD)

### Iberdrola 2.0TD - Falta completar
```json
{
  "nombre": "Plan Especial plus 15%TE 1p",
  "comercializadora": "Iberdrola",
  "atr": "2.0TD",
  "potencia_p1_eur_kw_dia": null,  // ❌ FALTA
  "potencia_p2_eur_kw_dia": null   // ❌ FALTA
}
```

**Acción:** Pedir al PO los precios de potencia oficiales de Iberdrola.

---

## 📅 7. ESTIMACIÓN DE TIEMPO

| Tarea | Tiempo estimado |
|-------|-----------------|
| Modificar comparador (backend) | 2-3 horas |
| Obtener e insertar tarifas 3.0TD | 1-2 horas |
| Adaptar frontend (wizard) | 2-3 horas |
| Testing y ajustes | 1-2 horas |
| **TOTAL** | **6-10 horas** |

---

## 🎯 8. PRÓXIMOS PASOS

1. **Confirmar con PO:** ¿Tenemos tarifas 3.0TD de las comercializadoras?
2. **Completar Iberdrola 2.0TD** (precios potencia)
3. **Implementar soporte 3.0TD** siguiendo este plan
4. **Probar con factura real** de cliente con potencia >= 15kW

---

¿Quieres que empiece con la implementación del código o prefieres primero conseguir las tarifas 3.0TD?
