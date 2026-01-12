# 🔧 OCR REFACTORING PLAN - Extracción Perfecta

## Objetivo: Lectura 100% Precisa de Facturas

### Problemas Actuales (Bugs 1-4, 7):
- ❌ CUPS incorrecto (extrae texto footer)
- ❌ Titular NO se extrae (null siempre)
- ❌ Confunde lecturas con consumos
- ❌ Total incorrecto
- ❌ Dirección/Provincia no se extraen

---

## PLAN DE IMPLEMENTACIÓN

### FASE 1: Mejoras CUPS
**Problema:** Regex captura cualquier texto con ES + letras
**Fix:**
```python
# ANTES (línea 253):
cups_match = re.search(r"(ES[ \t0-9A-Z\-]{18,32})", raw_text, re.IGNORECASE)

# DESPUÉS:
# 1. Buscar CUPS en contexto específico
# 2. Validar formato ES + exactamente 18-20 dígitos/letras
# 3. Excluir footers/links (buscar cerca de "CUPS:", "Código CUPS")
```

### FASE 2: Añadir Extracción Titular
**Problema:** No se extrae titular
**Fix:**
```python
# Buscar patrones:
# - "Titular:", "Nombre:", "Cliente:", "Razón Social:"
# - Filtrar líneas con términos técnicos (CUPS, ATR, kWh)
# - Validar que NO empiece con ES + números (confusión con CUPS)
```

### FASE 3: Distinguir Lecturas vs Consumos
**Problema:** Extrae "Lectura Actual: 15974" como consumo
**Fix:**
```python
# Ignorar líneas con:
# - "Lectura Actual", "Lectura Anterior"
# - "Lectura Final", "Medida"
# Buscar explícitamente:
# - "Consumo Periodo", "Consumo kWh"
# - Calcular: lectura_actual - lectura_anterior
```

### FASE 4: Dirección y Provincia
**Problema:** No se extraen
**Fix:**
```python
# Buscar patrones:
# - "Dirección Suministro:", "Domicilio:"
# - Extraer línea completa
# - Provincia: detectar nombres de provincias españolas
```

---

## IMPLEMENTACIÓN STEP-BY-STEP

1. ✅ Crear función `extract_titular_robust()`
2. ✅ Mejorar función CUPS con contexto
3. ✅ Añadir validaciones post-extracción
4. ✅ Distinguir lecturas vs consumos
5. ✅ Extraer dirección y provincia
6. ✅ Tests con facturas reales

---

**Prioridad:** 🔴 CRÍTICA
**Tiempo estimado:** 45-60 min
**Impacto:** Diferenciador competitivo clave
