# 📊 Peajes y Cargos Regulados BOE 2025 - Tarifa 2.0TD

> **Fuente oficial:** BOE - CNMC y Ministerio para la Transición Ecológica  
> **Vigencia:** 1 de enero de 2025  
> **Aplicación:** Todas las comercializadoras (valores regulados)

---

## 🔋 PEAJES DE ACCESO (CNMC - Resolución 4 dic 2024)

### Término de Potencia 2.0TD

| Periodo | €/kW año | €/kW día | Descripción |
|---------|----------|----------|-------------|
| **P1** (Punta) | 22.958932 | **0.062889** | Horario punta (10-14h y 18-22h laborables) |
| **P2** (Valle) | 0.442165 | **0.001211** | Resto de horas |

**Cálculo:** Valor anual / 365 días

---

## ⚡ CARGOS DEL SISTEMA (Orden TED/1487/2024, 26 dic)

### Término de Potencia 2.0TD - Segmento 1 (Doméstico)

| Periodo | €/kW año | €/kW día | Descripción |
|---------|----------|----------|-------------|
| **P1** (Punta) | 3.974324 | **0.010888** | Financiación renovables, bono social, etc. |
| **P2** (Valle) | 0.255597 | **0.000700** | Resto de horas |

**Cálculo:** Valor anual / 365 días

---

## 💰 TOTAL REGULADO (Peajes + Cargos)

### Precio TOTAL de Potencia 2.0TD para 2025

| Periodo | Peaje | Cargo | **TOTAL** | Uso |
|---------|-------|-------|-----------|-----|
| **P1** | 0.062889 | 0.010888 | **0.073777** €/kW·día | Usar en tarifas sin precio potencia |
| **P2** | 0.001211 | 0.000700 | **0.001911** €/kW·día | Usar en tarifas sin precio potencia |

---

## 📋 APLICACIÓN EN EL COMPARADOR

### Caso 1: Tarifa CON precios de potencia (Endesa, Naturgy)
```python
# Usar los valores de la tarifa directamente
potencia_p1_price = tarifa.get("potencia_p1_eur_kw_dia")  # Ej: 0.090214
potencia_p2_price = tarifa.get("potencia_p2_eur_kw_dia")  # Ej: 0.090214
```

### Caso 2: Tarifa SIN precios de potencia (Iberdrola)
```python
# Usar valores regulados BOE 2025
if potencia_p1_price is None:
    potencia_p1_price = 0.073777  # Peajes + Cargos P1
    potencia_p2_price = 0.001911  # Peajes + Cargos P2
    modo_potencia = "boe_2025_regulado"
```

---

## 🎯 ACTUALIZACIÓN RECOMENDADA

### Modificar `comparador.py` líneas 421-424:

**ANTES (valores inventados):**
```python
if potencia_p1_price is None:
    potencia_p1_price = 0.10  # ❌ Valor inventado
    potencia_p2_price = 0.04  # ❌ Valor inventado
    modo_potencia = "boe_fallback"
```

**DESPUÉS (valores oficiales BOE 2025):**
```python
if potencia_p1_price is None:
    potencia_p1_price = 0.073777  # ✅ Peajes + Cargos BOE 2025
    potencia_p2_price = 0.001911  # ✅ Peajes + Cargos BOE 2025
    modo_potencia = "boe_2025_regulado"
```

---

## 📊 COMPARACIÓN: Antes vs Después

### Impacto en factura tipo (30 días, 4.6kW P1 + 4.6kW P2)

| Concepto | Fallback Antiguo | BOE 2025 Oficial | Diferencia |
|----------|------------------|------------------|------------|
| **Potencia P1** | 30×4.6×0.10 = 13.80€ | 30×4.6×0.073777 = 10.18€ | **-3.62€** |
| **Potencia P2** | 30×4.6×0.04 = 5.52€ | 30×4.6×0.001911 = 0.26€ | **-5.26€** |
| **TOTAL** | **19.32€** | **10.44€** | **-8.88€** ✅ |

**Conclusión:** El fallback antiguo **sobreestimaba** el coste de potencia en ~9€/mes, haciendo que las tarifas sin precio de potencia (como Iberdrola) parecieran más caras de lo que realmente son.

---

## ✅ PRÓXIMOS PASOS

1. ✅ Actualizar fallback en `comparador.py` con valores BOE 2025
2. ✅ Actualizar JSON de Iberdrola con estos valores
3. ✅ Recalcular comparativas existentes
4. ✅ Actualizar documentación del motor de cálculo

---

## 📚 Referencias Oficiales

- **Peajes 2025:** CNMC - Resolución 4 diciembre 2024 (RAP/DE/009/24)
- **Cargos 2025:** Orden TED/1487/2024, 26 diciembre (BOE-A-2024-27289)
- **Circular metodología:** CNMC Circular 1/2025, 5 febrero 2025
