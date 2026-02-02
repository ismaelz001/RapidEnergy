# EVIDENCIA TECNICA: QA AUDIT COMPARADOR 2.0TD

## Factura 232 Iberdrola - Datos Crudos OCR vs Reales

### Extracto PDF Original (Pagina 2/4 - INFORMACION SOBRE CONSUMO)

```
Consumo total de esta factura:        263,14 kWh  
Consumo medio diario (30 dias):       1,30 EUR  

DETALLE DE FACTURA
─────────────────────────────────────────────────

ENERGIA
Potencia facturada Punta:   5 kW x 30 dias x 0,108192 EUR/kW/dia = 16,23 EUR
Potencia facturada Valle:   5 kW x 30 dias x 0,046548 EUR/kW/dia = 6,98 EUR
─────────────────────────────────────────────────
TOTAL POTENCIA                                     = 23,21 EUR

Energia consumida:          263,14 kWh x 0,17347 EUR/kWh = 45,65 EUR
Descuento sobre consumo 15%: 15% s/45,65 EUR    = -6,85 EUR
Compensacion excedentes:   -465,42 kWh x 0,07 EUR/kWh = -32,58 EUR

─────────────────────────────────────────────────
TOTAL ENERGIA (neto)                            = 6,22 EUR

CARGOS NORMATIVOS
Financiacion bono social fijo:  30 dias x 0,012742 EUR/dia = 0,38 EUR
Impuesto sobre electricidad:    5,11269632% s/29,81 EUR    = 1,52 EUR

SERVICIOS Y OTROS CONCEPTOS
Alquiler equipos medida:        30 dias x 0,02663014 EUR/dia = 0,80 EUR

─────────────────────────────────────────────────
BASE IVA (s/IVA)                                 = 32,13 EUR
IVA 21%                                         = 6,75 EUR
─────────────────────────────────────────────────
TOTAL IMPORTE FACTURA                           = 38,88 EUR

DESGLOSE CONSUMO DESAGREGADO (REAL - Pagina 2/4):
"Las lecturas desagregadas segun la tarifa de acceso, tomadas el 30/09/2025 son: 
  punta: 15.974,25 kWh;    <- OCR LEYO ESTO (NUMERO DE ACCUMULADO)
  llano: 3.609,47 kWh;     <- OCR LEYO ESTO
  valle 5.898,56 kWh       <- OCR LEYO ESTO

siendo estas lecturas reales. Sus consumos desagregados han sido 
  punta: 59 kWh;           <- REAL (diferencia del periodo)
  llano: 55,99 kWh;        <- REAL
  valle 166,72 kWh         <- REAL
"
```

### Analisis del Error OCR

```
OCR leyó:  Lectura total del contador (acumulada desde 2024)
Debería:   Consumo en el PERIODO (31/08/2025 - 30/09/2025)

P1 (Punta):
  Leida:   15.974,25 kWh (acumulada)
  Real:    59 kWh (consumo periodo)
  ERROR:   Factor 270.75x

P2 (Llano):
  Leida:   3.609,47 kWh (acumulada)
  Real:    55,99 kWh (consumo periodo)
  ERROR:   Factor 64.47x

P3 (Valle):
  Leida:   5.898,56 kWh (acumulada)
  Real:    166,72 kWh (consumo periodo)
  ERROR:   Factor 35.37x

Total consumo real periodo: 59 + 55.99 + 166.72 = 281.71 kWh (plausible)
Total consumo OCR malformado: 15974 + 3609 + 5898 = 25481 kWh (inverosimil 90x)
```

---

## Cálculo Verificable: Factura 232 con Datos REALES

### Input Data (Corregidos)

```
{"factura_232_corregida": {
  "cups": "ES0031103378680001TE",
  "consumo_p1_kwh": 59.0,
  "consumo_p2_kwh": 55.99,
  "consumo_p3_kwh": 166.72,
  "potencia_p1_kw": 5.0,
  "potencia_p2_kw": 5.0,
  "periodo_dias": 30,
  "iva_porcentaje": 0.21,
  "alquiler_contador": 2.10,
  "total_factura": 38.88
}}
```

### Cálculo Tarifa 9 (Plan Estable Iberdrola) - PASO A PASO

```
TARIFA PLAN ESTABLE (ID 9):
  energia_p1: 0.174875 EUR/kWh
  energia_p2: 0.174875 EUR/kWh
  energia_p3: 0.174875 EUR/kWh
  potencia_p1: 0.108192 EUR/kW/dia
  potencia_p2: 0.046548 EUR/kW/dia

1. POTENCIA
   P1: 5.0 kW × 0.108192 EUR/kW/dia × 30 dias = 16.2288 EUR
   P2: 5.0 kW × 0.046548 EUR/kW/dia × 30 dias = 6.9822 EUR
   Total potencia = 23.2110 EUR

2. CONSUMO
   P1: 59.0 kWh × 0.174875 EUR/kWh = 10.31763 EUR
   P2: 55.99 kWh × 0.174875 EUR/kWh = 9.79639 EUR
   P3: 166.72 kWh × 0.174875 EUR/kWh = 29.17269 EUR
   Total consumo = 49.28671 EUR

3. SUBTOTAL (energía + potencia, sin impuestos)
   = 23.2110 + 49.2867 = 72.4977 EUR

4. IMPUESTO ELECTRICO (5.11269632%)
   = 72.4977 × 0.0511269632 = 3.7049 EUR

5. BASE IVA
   = 72.4977 + 3.7049 + 2.10 (alquiler) = 78.3026 EUR

6. IVA (21%)
   = 78.3026 × 0.21 = 16.4436 EUR

7. TOTAL PERIODO (30 dias)
   = 78.3026 + 16.4436 = 94.7462 EUR

8. TOTAL ANUAL (360 dias)
   = (94.7462 / 30) × 360 = 1136.9544 EUR

9. AHORRO vs FACTURA ACTUAL
   Factura actual: 38.88 EUR (30 dias)
   Factura actual anualizada: (38.88 / 30) × 360 = 466.56 EUR
   Tarifa nueva: 1136.95 EUR (360 dias)
   
   AHORRO = 466.56 - 1136.95 = -670.39 EUR (COSTE MAYOR)
   % DIFERENCIA = (1136.95 - 466.56) / 466.56 × 100 = +143.6% MAS CARO
```

### Verificacion Cruzada

```
¿Cuanto deberia costar con OCR MALFORMADO?

Con consumos OCR (15974, 3609, 5898):
  Consumo total: 25481 kWh
  Coste consumo ≈ 25481 × 0.174875 ≈ 4458 EUR
  (+ potencia, impuestos, etc.)
  Total ESTIMADO: ~4600 EUR (imposible)

Con consumos REALES (59, 56, 167):
  Consumo total: 282 kWh (plausible)
  Coste consumo: 49.29 EUR (plausible)
  Total: 94.75 EUR (consistente con factura +145% premium)
```

---

## Tabla Comparativa Completa (CONSUMOS REALES)

```
FACTURA 232 (Consumos corregidos: P1=59, P2=56, P3=167 kWh)
Potencias: P1=5 kW, P2=5 kW
Periodo: 30 dias
Fecha: 31/08/2025 - 30/09/2025

┌─────┬──────────────┬──────────────────────────┬──────────┬────────┬─────────┬──────────┐
│ Rk  │ Tarifa ID    │ Plan                     │ Total €  │ Anual  │ Ahorro  │ % Dif    │
├─────┼──────────────┼──────────────────────────┼──────────┼────────┼─────────┼──────────┤
│  1  │ 3 (Naturgy)  │ Tarifa Noche Luz ECO    │ 70.54    │ 846.45 │ -379.89 │ -81.4%   │
│  2  │ 2 (Naturgy)  │ Tarifa Por Uso Luz      │ 73.51    │ 882.13 │ -415.57 │ -89.1%   │
│  3  │ 4 (Endesa)   │ Libre Promo 1er año     │ 74.91    │ 898.88 │ -432.32 │ -92.7%   │
│  4  │ 10 (Ibdrla)  │ Plan Especial Plus 15%  │ 85.36    │1024.31 │ -557.75 │ -119.5%  │
│  5  │ 9 (Ibdrla)   │ Plan Estable            │ 94.72    │1136.63 │ -670.07 │ -143.6%  │
├─────┴──────────────┴──────────────────────────┴──────────┴────────┴─────────┴──────────┤
│ FACTURA ACTUAL (Iberdrola con datos reales)                                              │
│ Periodo: 30 dias                                                                        │
│ Total: 38.88 EUR                                                                       │
│ Anual (360 dias): 466.56 EUR                                                           │
│                                                                                         │
│ CONCLUSION: Cliente mejor se queda con Iberdrola (actual). Todas las tarifas            │
│ competidoras son MAS CARAS (+80% a +143%). Motivo: bajo consumo (281 kWh/mes).        │
└──────────────────────────────────────────────────────────────────────────────────────────┘

NOTA TECNICA: "Ahorro" negativo = cliente pagaría MAS con tarifa nueva.
Ranking correcto (de menor a mayor coste):
  1. Factura actual: 38.88 EUR (MEJOR)
  2. Tarifa 3: 70.54 EUR (+81%)
  3. Tarifa 2: 73.51 EUR (+89%)
  ... etc
```

---

## Impacto del Error OCR si No Se Corrige

### Escenario: Comparador Usaría OCR Malformado

```
Si comparador uso consumos OCR (15974, 3609, 5898):

TARIFA 9 (Plan Estable) con datos MALFORMADOS:
  Consumo total: 25481 kWh (vs 282 real - factor 90x)
  Coste estimado: ~4600 EUR (vs 94.74 real - factor 48x)
  "Ahorro" vs factura: 4600 - 38.88 = 4561 EUR
  % "Ahorro": 11726% (FRAUDULENTO)

CLIENTE VERIA:
  "Puedes ahorrar 4561 EUR / año (11726%)"
  
REALIDAD:
  Cliente pagaría 94.74 EUR (coste real) vs 38.88 EUR actual
  Perder: 55.86 EUR adicionales / mes (FRAUDE TOTAL)

RIESGO:
  - Cliente contrata basado en "ahorro" ficticio
  - Descubre error al mes 1 de nuevo contrato (vinculante 1-2 años)
  - RECLAMO LEGAL: fraude en oferta, daños y perjuicios
  - REGULATORIO: CNMC investiga; sanciones financieras ~5-10% facturacion
  - REPUTACIONAL: "CRM Mecaenergy engaña clientes con ofertas falsas"
```

---

## Test de Regresion (Propuesto)

### test_ocr_factura_232_malformada

```python
import pytest
from app.services.ocr import extract_ocr
from app.services.comparador import compare_factura
from app.exceptions import DomainError

def test_ocr_debe_detectar_consumos_malformados():
    """
    Factura 232 Iberdrola: OCR leyo 15974, 3609, 5898 (acumulados).
    Deberia detectar como malformado y bloquear.
    """
    # Simular OCR malformado
    ocr_output = {
        "consumo_p1_kwh": 15974.25,  # ERROR OCR
        "consumo_p2_kwh": 3609.47,   # ERROR OCR
        "consumo_p3_kwh": 5898.56,   # ERROR OCR
        "potencia_p1_kw": 5.0,       # OK
        "potencia_p2_kw": 5.0,       # OK
        "total_factura": 38.88,
        "periodo_dias": 30,
    }
    
    # Debe rechazar
    from app.routes.webhook import validar_consumos
    with pytest.raises(DomainError) as exc:
        validar_consumos(ocr_output)
    
    assert exc.value.code == "OCR_CONSUMO_SUSPICIOUS"
    assert "15974" in str(exc.value)

def test_comparador_calcula_correcto_con_datos_reales():
    """
    Tarifa 9 vs Factura 232 con consumos REALES (59, 56, 167).
    Debe calcular total 94.74 EUR (30 dias).
    """
    factura = {
        "id": 232,
        "consumo_p1_kwh": 59.0,       # REAL
        "consumo_p2_kwh": 55.99,      # REAL
        "consumo_p3_kwh": 166.72,     # REAL
        "potencia_p1_kw": 5.0,
        "potencia_p2_kw": 5.0,
        "periodo_dias": 30,
        "total_factura": 38.88,
        "iva_porcentaje": 0.21,
        "alquiler_contador": 2.10,
        "validado_step2": True,
        "total_ajustado": 38.88,
    }
    
    tarifa_9 = {
        "tarifa_id": 9,
        "nombre": "Plan Estable",
        "energia": {"p1": 0.174875, "p2": 0.174875, "p3": 0.174875},
        "potencia": {"p1": 0.108192, "p2": 0.046548},
    }
    
    from app.services.comparador import calcular_tarifa
    result = calcular_tarifa(factura, tarifa_9)
    
    # Verificar totales con 2 decimales precision
    assert abs(result["total_periodo"] - 94.74) < 0.01
    assert abs(result["total_anual_360"] - 1136.88) < 0.01

def test_comparador_rechaza_sin_step2():
    """
    Factura 232 sin Step2 debe ser rechazada.
    Bloquea hasta que asesor complete Step2.
    """
    factura_dict = {
        "id": 232,
        "consumo_p1_kwh": 59.0,
        "validado_step2": False,  # SIN STEP2
        "total_ajustado": None,
    }
    
    from app.services.comparador import compare_factura
    from app.db.models import Factura
    
    factura = Factura(**factura_dict)
    db = MagicMock()
    
    with pytest.raises(DomainError) as exc:
        compare_factura(factura, db)
    
    assert exc.value.code == "STEP2_REQUIRED"
```

---

## Ficheros Generados

```
/f:\MecaEnergy/
├─ QA_AUDIT_COMPARADOR_SIMPLE.py          [Script de auditoria simplificado]
├─ QA_AUDIT_REPORT_20260202.md             [Este documento - Reporte completo]
├─ QA_AUDIT_EVIDENCIA_TECNICA.md           [Evidencia tecnica (este fichero)]
└─ factura_232.json                        [Datos JSON factura original]
```

---

## Resumen Ejecutivo para CEO

**HALLAZGO CRITICO:** Comparador funcional pero OCR produce datos 270x malformados.

**RIESGO:** Si no valida OCR, cliente ve "ahorros" ficticiamente altos → contrata basado en fraude → legal reclamo.

**SOLUCION:** P0 Urgente - Validar consumos > 1000 kWh antes comparador.

**IMPACTO:** Prevenir fraude regulatorio + sanciones CNMC + proteger reputacion.

---

**Auditoria Completada:** 02/02/2026  
**Estado:** ✅ LISTO PARA DESARROLLO  
**Siguiente Paso:** Implementar P0 + P1 fixes (Sprint 1-2)
