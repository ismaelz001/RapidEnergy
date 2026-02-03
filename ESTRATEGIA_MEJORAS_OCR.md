# 🎯 ESTRATEGIA DE MEJORAS OCR - Análisis Completo

## 📊 PROBLEMAS DETECTADOS POR FACTURA

### Factura #320 (Endesa - Factura.pdf)
**QA Audit mostró:**
```
✅ cups: "ES0031103294400001JA" 
✅ atr: "2.0TD" 
✅ total_factura: "41.64" 
❌ periodo_dias: "33" → REAL: 32 días (ERROR +1)
❌ cliente: "del contrato" → REAL: "ANTONIO RUIZ MORENO"
✅ consumo_total: "83.895" 
✅ potencia_p1: "3.9" 
✅ potencia_p2: "4" 
⚠️ consumo_p1-p6: "0" → NO EXTRAÍDOS
⚠️ impuesto_electrico: "" → Descartado por sanity (31.93 > 15%)
⚠️ alquiler_contador: "" → Descartado por sanity (21.28 > 10€)
```

**FIXES NECESARIOS:**
1. ✅ **Cliente:** DONE - Nueva estrategia robusta multi-formato
2. ❌ **Días facturados:** Revisar cálculo - está sumando +1 día extra
3. ❌ **Consumos por periodo:** No se extraen - necesita estrategia específica Endesa
4. ❌ **Impuesto eléctrico:** Sanity check demasiado estricto (descarta valor válido)
5. ❌ **Alquiler contador:** Sanity check demasiado estricto

---

### Factura #319 (HC Energía - Fra Agosto.pdf)
**QA Audit mostró:**
```
❌ cups: "" (NULL) 
❌ atr: "" (NULL)
✅ total_factura: "107"
⚠️ periodo_dias: "" (vacío)
❌ cliente: "" (NULL)
✅ consumo_total: "505"
✅ potencia_p1: "4.6"
⚠️ potencia_p2: "0" → REAL: Probablemente igual a P1
⚠️ consumo_p1-p6: "0" → NO EXTRAÍDOS
✅ iva: "21"
✅ impuesto_electrico: "5.11269632"
✅ alquiler_contador: "0.69"
```

**CAUSA:** Factura procesada ANTES del fix de fusión pypdf+Vision

**FIXES NECESARIOS:**
1. ✅ **Fusión pypdf+Vision:** DONE - Siempre prioriza pypdf
2. ✅ **Cliente:** DONE - Nueva estrategia captura "Vygantas Kaminskas"
3. ❌ **ATR:** No se extrae - necesita estrategia más flexible
4. ❌ **Días facturados:** Debe calcular desde fechas (05/08 → 01/09 = 27 días)
5. ❌ **Potencia P2:** Probablemente igual a P1 en tarifa 2.0TD

---

### Factura #317 (Iberdrola - JOSE ANTONIO)
**Test local mostró:**
```
✅ cups: "ES0031103378680001TE"
✅ titular: "JOSE ANTONIO RODRIGUEZ UROZ"
✅ atr: "2.0TD"
✅ consumo_kwh: 263.14
✅ potencia_p1/p2: 5.0 kW
✅ total_factura: 38.88
❌ consumo_p1: 59.0 → Descartado por incoherencia (suma ≠ total)
❌ consumo_p2: 55.99 → Descartado
❌ consumo_p3: 166.72 → Descartado
```

**CAUSA:** Sanity check detecta incoherencia: suma_periodos (281.71) ≠ consumo_total (263.14)

**ANÁLISIS:**
- Texto PDF línea 163: "consumos desagregados han sido punta: 59 kWh; llano: 55,99 kWh; valle 166,72 kWh"
- Suma: 59 + 55.99 + 166.72 = 281.71 kWh
- Total factura: 263.14 kWh
- **Diferencia: 18.57 kWh (7%)**

**DECISIÓN:** 
- ¿Son los consumos reales? → Probablemente SÍ
- ¿Es el total equivocado? → Necesita verificación manual
- **ACCIÓN:** Aumentar tolerancia del sanity check de 2% a 10%

---

### Factura #318 (Naturgy)
```
✅ titular: "ENCARNACIÓN LINARES LÓPEZ"
✅ cups: "ES0031103444766001FF"
✅ atr: "2.0TD"
✅ consumo_kwh: 304.0
✅ potencia_p1/p2: 3.3 kW
✅ total_factura: 64.08
❌ dias_facturados: 8 → Descartado por sanity (<15)
❌ consumos_p1-p3: Descartados por incoherencia
❌ alquiler_contador: 28.0 → Descartado (>10€)
❌ impuesto_electrico: 49.67 → Descartado (>15%)
```

---

## 🔧 PLAN DE ACCIÓN PRIORIZADO

### 1. DÍAS FACTURADOS (CRÍTICO)
**Problema:** 
- Endesa: Extrae 33 en vez de 32
- Naturgy: Extrae 8 (descartado)
- HC Energía: No extrae

**Estrategias actuales (3):**
1. Buscar "X días" explícito
2. Buscar en "Periodo" seguido de días
3. **Calcular desde fechas inicio/fin** ← MÁS CONFIABLE

**FIX:**
```python
# PRIORIDAD 1: Calcular desde fechas (más preciso)
if fecha_inicio and fecha_fin:
    dias = (fecha_fin - fecha_inicio).days + 1  # +1 incluye ambos días
    
# PRIORIDAD 2: Buscar "X días" explícito
# PRIORIDAD 3: Patrón "Periodo: X días"
```

**PROBLEMA DETECTADO:**
El cálculo actual hace `(fin - inicio).days + 1` pero a veces las facturas dicen "del 17/09 al 19/10" y eso son 33 días (incl. inicio y fin), pero el PDF dice "32 días". 

**¿Por qué?** Porque las eléctricas cuentan 24h completas, no días naturales.

**SOLUCIÓN:** NO sumar +1, usar `.days` directo.

---

### 2. CONSUMOS POR PERIODO (MEDIO)
**Problema:** No se extraen en 3/4 facturas

**Análisis patrones:**
- **Iberdrola:** Línea larga "consumos desagregados han sido punta: 59 kWh; llano: 55,99 kWh; valle 166,72 kWh"
- **Endesa:** No visible en primeras 50 líneas
- **Naturgy:** No visible en primeras 50 líneas
- **HC Energía:** No visible

**Estrategias actuales:**
1. `_extract_table_consumos()` - Busca secciones "CONSUMOS DESAGREGADOS"
2. Regex patterns prioritarios (punta/llano/valle, P1/P2/P3)
3. Table lines con "kwh" keyword
4. Fallback líneas "P1: 123"

**FIX NECESARIO:**
- Mejorar regex para capturar frase larga de Iberdrola
- Buscar en TODO el texto, no solo primeras 100 líneas
- Pattern específico: `(punta|llano|valle|p[1-6])[:\s]+(\d+[.,]?\d*)\s*kwh`

---

### 3. SANITY CHECKS (CRÍTICO)
**Problema:** Descarta valores válidos

**Casos detectados:**
1. **Alquiler contador > 10€:** Endesa 21.28€, Naturgy 28€ → Descartados
   - **FIX:** Aumentar límite a 30€ (algunas facturas sí cobran más)
   
2. **Impuesto eléctrico > 15% total:** Endesa 31.93€ (77% del total!)
   - **FIX:** Cambiar lógica - validar que sea ~5.11% del importe energía, no del total
   
3. **Incoherencia consumos:** Tolerancia 2% demasiado estricta
   - **FIX:** Aumentar a 10% (hay pérdidas, estimaciones, etc.)

---

### 4. ATR FALTANTE (MEDIO)
**Problema:** HC Energía no extrae ATR

**Patrones actuales:**
```python
r"2\s*[.,]?\s*[0O]\s*TD"
r"USO LUZ"
r"PEAJE[\s\S]{0,60}?([23]\.?[0O]\s*TD)"
```

**FIX:**
- Ampliar búsqueda a todo el documento
- Añadir patterns: "tarifa 2.0", "acceso 2.0TD", "peaje 2.0"

---

### 5. POTENCIA P2 FALTANTE (BAJO)
**Problema:** HC Energía no extrae P2

**Análisis:** 
- En tarifa 2.0TD con solo P1 visible, P2 suele ser igual
- **FIX:** Si `atr == "2.0TD"` y `potencia_p2 is None` y `potencia_p1 is not None`:
  ```python
  result["potencia_p2_kw"] = result["potencia_p1_kw"]
  ```

---

## ✅ FIXES COMPLETADOS
1. ✅ **Extracción titular:** Estrategia multi-formato robusta (4/4 facturas)
2. ✅ **Fusión pypdf+Vision:** Siempre prioriza pypdf (protege CUPS)
3. ✅ **Import openai:** Eliminado (no usado)

---

## 📝 PRÓXIMOS PASOS
1. Arreglar cálculo días facturados (quitar +1)
2. Ajustar sanity checks (tolerancias más realistas)
3. Mejorar extracción consumos por periodo
4. Ampliar búsqueda ATR
5. Fallback potencia P2 = P1 en 2.0TD
6. Commitear + testear en producción
