# PLAN DE ACCIÓN: 71% → 96% ACCURACY

## Estado Actual
- Total tests: 49 campos
- ✅ Passed: 35 (71.4%)
- ❌ Failed: 14 (28.6%)

## Objetivo: 96% = 47/49 tests (permitir solo 2 fallos)
Necesitamos arreglar **12 de los 14 fallos actuales**

---

## ANÁLISIS DE FALLOS (14 tests)

### GRUPO A: DIRECCIONES (4 fallos) - PRIORIDAD ALTA
1. **Iberdrola dirección**: 
   - OCR: "C/ GALICIA, 7 04430 INSTINCION" (incluye CP)
   - GT: "C/ GALICIA, 7"
   - FIX: Limpiar código postal pegado

2. **Naturgy dirección**:
   - OCR: "21 04738 Vícar Almería" (falta calle)
   - GT: "VELAZQUEZ 21"
   - FIX: Capturar línea ANTERIOR cuando siguiente solo tiene número

3. **Endesa dirección**:
   - OCR: "Contrato de mercado libre: Tarifa One Luz" (texto basura)
   - GT: "AV CAMARA DE COMERCIO 43 4 C"
   - PROBLEMA: GT es DIFERENTE a lo que está en el PDF (PDF dice "ESTACION 9...")
   - FIX: Validar si GT está mal o si hay 2 direcciones en PDF

4. **HC Energía dirección**:
   - OCR: "Adra Almería" (incompleto)
   - GT: "Calle Minerva 35 - 2 C"
   - FIX: Capturar línea correcta (está en línea 108: "Calle Minerva 35 - 2 C 04770")

### GRUPO B: LOCALIDADES (4 fallos) - PRIORIDAD ALTA
5-8. **Todas las localidades**: OCR=None
   - FIX: Mejorar pattern para capturar "CP + Ciudad + Provincia"

### GRUPO C: ALQUILER IBERDROLA (1 fallo) - PRIORIDAD MEDIA
9. **Alquiler Iberdrola**:
   - OCR: 2.10€ 
   - GT: 0.8€
   - PROBLEMA: Extrae % en vez de valor absoluto
   - FIX: Buscar pattern "30 días x 0,02663014 €/día 0,80 €" - capturar último número

### GRUPO D: HC ENERGÍA (3 fallos) - PRIORIDAD BAJA (sin Vision API)
10. Cliente HC: None (pypdf parcial)
11. Días HC: None (pypdf parcial)
12. Consumo HC: None (pypdf parcial)
   - FIX: Requiere Vision API O mejorar pypdf extraction

### GRUPO E: FECHAS NATURGY (2 fallos) - PRIORIDAD MEDIA
13-14. **Fechas Naturgy incorrectas**:
   - Extrae fechas de otra sección del PDF
   - FIX: Validar contexto de fechas extraídas

---

## PLAN DE IMPLEMENTACIÓN (Orden de Prioridad)

### FASE 1: ARREGLAR DIRECCIONES (4 tests) ⏱ 30min
**Objetivo**: Pasar de 35/49 → 39/49 (79.6%)

Estrategia línea por línea:
```python
# Encontrar "Dirección de suministro:"
# 1. Capturar texto DESPUÉS del : en misma línea
# 2. Si no hay texto o es <10 chars, siguiente línea
# 3. Si siguiente línea es solo número, buscar calle en línea ANTERIOR
# 4. Limpiar CP del final (regex: \s+\d{5}.*$)
```

### FASE 2: ARREGLAR LOCALIDADES (4 tests) ⏱ 20min
**Objetivo**: Pasar de 39/49 → 43/49 (87.8%)

Estrategia:
```python
# Después de extraer dirección, buscar en siguientes 1-3 líneas:
# Pattern: ^\d{5}\s+[A-Z][a-záéíóú]+\s+[A-Z][a-záéíóú]+
# Ejemplo: "04430 INSTINCION (ALMERIA)"
```

### FASE 3: ARREGLAR ALQUILER (1 test) ⏱ 15min
**Objetivo**: Pasar de 43/49 → 44/49 (89.8%)

Estrategia:
```python
# Pattern mejorado:
r"alquiler\s+(?:de\s+)?(?:equipo|contador).*?(\d+)\s+días?\s+x\s+([\d.,]+).*?([\d.,]+)\s*€"
# Capturar TERCER número (valor total, no tarifa diaria ni porcentaje)
```

### FASE 4: ARREGLAR FECHAS NATURGY (2 tests) ⏱ 20min
**Objetivo**: Pasar de 44/49 → 46/49 (93.9%)

Estrategia:
```python
# Validar que fechas extraídas:
# 1. Estén en sección "período de consumo" (no footer/header)
# 2. Rango sea 15-60 días (no 7 días = fecha equivocada)
# 3. Buscar pattern específico "del X de MES al Y de MES"
```

### FASE 5: HC ENERGÍA PYPDF (3 tests) ⏱ 30min
**Objetivo**: Pasar de 46/49 → 49/49 (100%) o quedarnos en 47/49 (96%)

Estrategia:
```python
# Mejorar extracción pypdf HC Energía:
# 1. Cliente: buscar "Datos del titular" + siguiente línea
# 2. Días: recalcular con fechas corregidas
# 3. Consumo: buscar pattern "Consumo total" o tabla consumos
```

---

## MÉTRICAS DE ÉXITO

| Fase | Tests Pass | Accuracy | Status |
|------|-----------|----------|--------|
| Inicial | 35/49 | 71.4% | ❌ Actual |
| Fase 1 | 39/49 | 79.6% | 🎯 Direcciones |
| Fase 2 | 43/49 | 87.8% | 🎯 Localidades |
| Fase 3 | 44/49 | 89.8% | 🎯 Alquiler |
| Fase 4 | 46/49 | 93.9% | 🎯 Fechas |
| Fase 5 | 47-49/49 | 96-100% | ✅ OBJETIVO |

---

## NOTAS IMPORTANTES

1. **Endesa dirección**: Verificar primero si GT está mal (puede que PDF tenga dirección diferente a la real)

2. **HC Energía**: Si no logramos 96% con Fases 1-4, necesitamos Fase 5. Si llegamos a 94% (46/49), podemos aceptarlo como "suficientemente bueno" para producción.

3. **Testing continuo**: Después de cada fase, ejecutar `test_all_fields_complete.py` para validar.

4. **Rollback plan**: Si alguna fase rompe tests que funcionaban, hacer rollback inmediato.

---

## TIEMPO ESTIMADO TOTAL
**2 horas** (115 minutos)

¿Comenzamos con Fase 1 (Direcciones)?
