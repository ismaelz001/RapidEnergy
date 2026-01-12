# 📊 P1: COMPARADOR COHERENTE - EJEMPLO JSON RESPONSE

## Respuesta del endpoint POST /webhook/comparar/facturas/{id}

```json
{
  "factura_id": 123,
  "comparativa_id": 45,
  "periodo_dias": 60,
  "current_total": 156.80,
  "offers": [
    {
      "tarifa_id": 1,
      "provider": "Octopus Energy",
      "plan_name": "Tarifa Fija 2.0TD",
      "estimated_total_periodo": 142.50,
      "ahorro_periodo": 14.30,
      "ahorro_mensual_equiv": 7.21,
      "ahorro_anual_equiv": 86.73,
      "saving_percent": 9.12,
      "tag": "best_saving",
      "breakdown": {
        "periodo_dias": 60,
        "coste_energia": 95.20,
        "coste_potencia": 47.30,
        "modo_energia": "3p",
        "modo_potencia": "tarifa"
      }
    },
    {
      "tarifa_id": 2,
      "provider": "Holaluz",
      "plan_name": "Plan Verde 2.0TD",
      "estimated_total_periodo": 145.80,
      "ahorro_periodo": 11.00,
      "ahorro_mensual_equiv": 5.55,
      "ahorro_anual_equiv": 66.88,
      "saving_percent": 7.02,
      "tag": "balanced",
      "breakdown": {
        "periodo_dias": 60,
        "coste_energia": 98.50,
        "coste_potencia": 47.30,
        "modo_energia": "3p",
        "modo_potencia": "tarifa"
      }
    },
    {
      "tarifa_id": 3,
      "provider": "TotalEnergies",
      "plan_name": "Energía Sencilla",
      "estimated_total_periodo": 148.20,
      "ahorro_periodo": 8.60,
      "ahorro_mensual_equiv": 4.34,
      "ahorro_anual_equiv": 52.28,
      "saving_percent": 5.48,
      "tag": "balanced",
      "breakdown": {
        "periodo_dias": 60,
        "coste_energia": 100.90,
        "coste_potencia": 47.30,
        "modo_energia": "3p",
        "modo_potencia": "tarifa"
      }
    }
  ]
}
```

## Explicación de campos (NO NEGOCIABLE)

### Nivel raíz
- `factura_id`: ID de la factura comparada
- `comparativa_id`: ID de la comparativa guardada (auditoría)
- **`periodo_dias`**: Días reales del periodo de facturación
- `current_total`: Total actual de la factura (€)

### Por cada offer
- `estimated_total_periodo`: **Total estimado para el MISMO periodo de la factura** (60 días en este ejemplo)
- **`ahorro_periodo`**: Ahorro del periodo completo (current_total - estimated_total_periodo)
- **`ahorro_mensual_equiv`**: Equivalente mensual = ahorro_periodo * (30.437 / periodo_dias)
- **`ahorro_anual_equiv`**: Equivalente anual = ahorro_periodo * (365 / periodo_dias)
- `saving_percent`: Porcentaje de ahorro
- `tag`: best_saving / balanced / partial

### Breakdown
- **`periodo_dias`**: Confirma el periodo usado (debe coincidir con raíz)
- `coste_energia`: Coste energía del periodo
- `coste_potencia`: Coste potencia del periodo (usando periodo_dias)
- `modo_energia`: 3p / 24h
- `modo_potencia`: tarifa / sin_potencia

---

## ✅ FÓRMULAS EXACTAS (NO NEGOCIABLE)

```python
# Cálculo base (periodo completo)
coste_potencia = periodo_dias * ((P1 * precio_P1) + (P2 * precio_P2))
estimated_total_periodo = coste_energia + coste_potencia
ahorro_periodo = current_total - estimated_total_periodo

# Equivalentes consistentes
ahorro_mensual_equiv = ahorro_periodo * (30.437 / periodo_dias)
ahorro_anual_equiv = ahorro_periodo * (365 / periodo_dias)
```

**Ejemplos numéricos:**
- Periodo 60 días, ahorro periodo = 14.30€
  - Mensual equiv: 14.30 * (30.437/60) = 7.25€
  - Anual equiv: 14.30 * (365/60) = 86.99€

- Periodo 30 días, ahorro periodo = 10€
  - Mensual equiv: 10 * (30.437/30) = 10.15€
  - Anual equiv: 10 * (365/30) = 121.67€

---

## 🎨 CÓMO MOSTRAR EN UI

### Hero de Ahorro (Step3)
```
Ahorro anual estimado (60 días periodo)
         86€/año

Actual (60d): 156.80€  →  Nueva (60d): 142.50€

Comparativa #45 guardada
```

### Panel de selección
```
Oferta seleccionada: Octopus Energy - Tarifa Fija 2.0TD

El cliente ahorrará 86.73€ al año (7.21€/mes equiv.)
```

### Labels clave
- **NUNCA** "Ahorro mensual" sin "equiv." si el periodo no es 30
- **SIEMPRE** especificar periodo en paréntesis
- **NUNCA** mezclar descuentos promocionales con equivalentes

---

## 🔍 Verificación en BD

```sql
-- Ver última comparativa
SELECT 
  c.id,
  c.factura_id,
  c.periodo_dias,
  c.current_total,
  c.created_at,
  json_extract(c.offers_json, '$[0].provider') as mejor_oferta
FROM comparativas c
ORDER BY c.id DESC
LIMIT 1;

-- Ver todas las comparativas de una factura
SELECT * FROM comparativas WHERE factura_id = 123;
```

---

## 📋 CHECKLIST DE COHERENCIA

- [ ] `periodo_dias` presente en nivel raíz
- [ ] `periodo_dias` presente en cada offer.breakdown
- [ ] `estimated_total_periodo` refleja el periodo completo (NO mensual)
- [ ] `ahorro_periodo` = current_total - estimated_total_periodo
- [ ] `ahorro_mensual_equiv` ≈ ahorro_periodo * 0.507 (si periodo=60)
- [ ] `ahorro_anual_equiv` ≈ ahorro_periodo * 6.08 (si periodo=60)
- [ ] `comparativa_id` devuelto y registro existe en BD
- [ ] Labels UI incluyen "(Xd)" para claridad

---

**Fecha:** 2026-01-09  
**Objetivo:** Comparador auditable y matemáticamente coherente
