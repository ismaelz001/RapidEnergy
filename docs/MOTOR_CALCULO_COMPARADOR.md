# 🔋 Motor de Cálculo - Comparador MecaEnergy

> **Versión:** 1.0  
> **Fecha:** 2026-01-13  
> **Archivo fuente:** `app/services/comparador.py`

---

## 📥 1. Variables de Entrada (Factura del Cliente)

| Variable | Símbolo | Unidad | Origen | Ejemplo |
|----------|---------|--------|--------|---------|
| Consumo Punta | `consumo_p1` | kWh | Factura OCR | 50 |
| Consumo Llano | `consumo_p2` | kWh | Factura OCR | 80 |
| Consumo Valle | `consumo_p3` | kWh | Factura OCR | 120 |
| Potencia contratada P1 | `potencia_p1` | kW | Factura OCR | 4.6 |
| Potencia contratada P2 | `potencia_p2` | kW | Factura OCR | 4.6 |
| Días del periodo | `periodo_dias` | días | Factura OCR | 30 |
| Total factura actual | `total_factura` | € | Factura OCR | 75.50 |

---

## 💰 2. Variables de Tarifa (BBDD tabla `tarifas`)

| Variable | Símbolo | Unidad | Endesa | Iberdrola | Naturgy |
|----------|---------|--------|--------|-----------|---------|
| Precio energía P1 | `precio_e1` | €/kWh | 0.1059 | 0.127394 | 0.120471 |
| Precio energía P2 | `precio_e2` | €/kWh | 0.1059 | 0.127394 | null (=P1) |
| Precio energía P3 | `precio_e3` | €/kWh | 0.1059 | 0.127394 | null (=P1) |
| Precio potencia P1 | `precio_pot1` | €/kW·día | 0.090214 | **⚠️ null** | 0.111815 |
| Precio potencia P2 | `precio_pot2` | €/kW·día | 0.090214 | **⚠️ null** | 0.033933 |

---

## ⚙️ 3. Constantes del Sistema (Hardcodeadas)

| Constante | Símbolo | Valor | Porcentaje | Notas |
|-----------|---------|-------|------------|-------|
| Impuesto Eléctrico | `IEE` | 0.051127 | 5.1127% | Puede variar por decreto (0.5% en crisis) |
| IVA doméstico | `IVA_DOM` | 0.10 | 10% | Si potencia_p1 < 10kW |
| IVA comercial | `IVA_COM` | 0.21 | 21% | Si potencia_p1 ≥ 10kW |
| Alquiler contador | `ALQ` | 0.0266 | €/día | ~0.80€/mes |
| Fallback potencia P1 | `FB_POT1` | 0.073777 | €/kW·día | **BOE 2025** (peajes + cargos regulados) |
| Fallback potencia P2 | `FB_POT2` | 0.001911 | €/kW·día | **BOE 2025** (peajes + cargos regulados) |

---

## 🧮 4. Fórmulas de Cálculo

### Paso 1: Coste de Energía
```
COSTE_ENERGIA = (consumo_p1 × precio_e1) + (consumo_p2 × precio_e2) + (consumo_p3 × precio_e3)
```

### Paso 2: Coste de Potencia
```
COSTE_POTENCIA = periodo_dias × [(potencia_p1 × precio_pot1) + (potencia_p2 × precio_pot2)]
```

### Paso 3: Subtotal
```
SUBTOTAL = COSTE_ENERGIA + COSTE_POTENCIA
```

### Paso 4: Impuesto Eléctrico (IEE 5.1127%)
```
IMPUESTO_ELECTRICO = SUBTOTAL × 0.051127
```

### Paso 5: Alquiler Contador
```
ALQUILER = periodo_dias × 0.0266
```

### Paso 6: Base Imponible
```
BASE_IMPONIBLE = SUBTOTAL + IMPUESTO_ELECTRICO + ALQUILER
```

### Paso 7: IVA
```
Si potencia_p1 < 10kW:
    IVA = BASE_IMPONIBLE × 0.10
Sino:
    IVA = BASE_IMPONIBLE × 0.21
```

### Paso 8: Total Estimado
```
TOTAL_ESTIMADO = BASE_IMPONIBLE + IVA
```

### Paso 9: Cálculo de Ahorro
```
AHORRO_PERIODO   = total_factura - TOTAL_ESTIMADO
AHORRO_MENSUAL   = AHORRO_PERIODO × (30.437 / periodo_dias)
AHORRO_ANUAL     = AHORRO_PERIODO × (365 / periodo_dias)
PORCENTAJE       = (AHORRO_PERIODO / total_factura) × 100
```

---

## 📐 5. Fórmula Completa (Una sola expresión)

```
TOTAL = ((E + P) × 1.051127 + A) × (1 + IVA)

Donde:
  E   = Σ(consumo_pX × precio_eX)                    para X = 1,2,3
  P   = periodo_dias × Σ(potencia_pX × precio_potX)  para X = 1,2
  A   = periodo_dias × 0.0266
  IVA = 0.10 si potencia_p1 < 10 sino 0.21
```

---

## 📊 6. Ejemplo Numérico Completo

**Datos de entrada:**
- Consumo: P1=50kWh, P2=80kWh, P3=120kWh
- Potencia: P1=4.6kW, P2=4.6kW  
- Periodo: 30 días
- Tarifa Endesa Libre Promo: e1=e2=e3=0.1059, pot1=pot2=0.0902

| Paso | Concepto | Fórmula | Resultado |
|------|----------|---------|-----------|
| 1 | Coste Energía | (50×0.1059)+(80×0.1059)+(120×0.1059) | **26.48€** |
| 2 | Coste Potencia | 30×[(4.6×0.0902)+(4.6×0.0902)] | **24.89€** |
| 3 | Subtotal | 26.48 + 24.89 | **51.37€** |
| 4 | Impuesto Eléctrico | 51.37 × 0.051127 | **2.63€** |
| 5 | Alquiler Contador | 30 × 0.0266 | **0.80€** |
| 6 | Base Imponible | 51.37 + 2.63 + 0.80 | **54.80€** |
| 7 | IVA (10%) | 54.80 × 0.10 | **5.48€** |
| 8 | **TOTAL ESTIMADO** | 54.80 + 5.48 | **60.28€** |

---

## ⚠️ 7. Puntos Pendientes para PO

| # | Pregunta | Estado |
|---|----------|--------|
| 1 | **Precios potencia Iberdrola** (P1 y P2 €/kW·día) | ❌ Falta dato |
| 2 | ¿Usar IEE 5.11% normal o 0.5% crisis? | ❓ Por confirmar |
| 3 | ¿Aplicar descuentos comerciales (ej: 10% primer año Endesa)? | ❓ Por confirmar |
| 4 | ¿Mostrar permanencia y penalizaciones? | ❓ Por confirmar |

---

## 🔗 8. Archivos Relacionados

- Motor principal: `app/services/comparador.py`
- Modelo de datos: `app/db/models.py`
- Tarifas en BBDD: tabla `tarifas` (ATR='2.0TD')
