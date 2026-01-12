# 🚨 BUG REPORT CRÍTICO - Factura Real Iberdrola (ID 25)

## Fecha: 2026-01-12 08:25 UTC
## Factura: `E:\MecaEnergy\facturas\Factura Iberdrola.pdf`

---

## 🔴 BUGS CRÍTICOS ENCONTRADOS

### BUG 1: OCR - CUPS Incorrecto ❌ CRÍTICO
**Problema:** 
- **Extraído:** `ESVEROCANJEARTUSALDOHACIEN`
- **Correcto:** `ES0031103378680001TE`
- **Causa:** OCR captura texto del footer del PDF ("Puedes ver o canjear tu saldo haciendo clic aquí")

**Impacto:** Sistema no puede identificar punto de suministro correctamente

### BUG 2: OCR - Confunde Lecturas con Consumos ❌ CRÍTICO
**Problema:**
- **Extraído P1:** `15974.25 kWh` (Lectura acumulada del contador)
- **Correcto P1:** `59.00 kWh` (Consumo del periodo)
- **Resultado:** Costes astronómicos (€30,000/año), ahorros negativos absurdos

**Impacto:** Comparador muestra datos completamente inválidos

### BUG 3: OCR - Nombre Cliente No Extraído ❌ ALTO
**Problema:**
- **Extraído:** `null`
- **Correcto:** `JOSE ANTONIO RODRIGUEZ UROZ`
- **Presente en PDF:** Sí, visible 3 veces

**Impacto:** Perfil de cliente incompleto

### BUG 4: OCR - Total Factura Incorrecto ❌ CRÍTICO
**Problema:**
- **Extraído:** `25` (probablemente de una fecha)
- **Correcto:** `263,14 EUR` o `38.88 EUR` (según periodo)

**Impacto:** Baseline de comparación inválido

### BUG 5: Backend P1 - NO VALIDA PERIODO ❌ CRÍTICO P1
**Problema:**
- Factura 25 tiene `periodo_dias: null`
- Backend **NO devuelve HTTP 422 PERIOD_REQUIRED**
- Backend usa fallback de 30 días → **VIOLA SPEC P1**

**Evidencia:**
```javascript
// Step 44 - Called: POST /webhook/comparar/facturas/25
// Response: HTTP 200 (debería ser 422)
// Backend usó default de 30 días
```

**Impacto:** P1 NO FUNCIONA como especificado

### BUG 6: Frontend - URL Incorrecta Comparador ❌ CRÍTICO
**Problema:**
- **Frontend llama:** `POST /webhook/comparar/25`
- **Backend espera:** `POST /webhook/comparar/facturas/25`
- **Resultado:** HTTP 404 - Comparador nunca carga en UI

**Evidencia:**
```javascript
// Step 32 - Frontend call
status: 404
body: {"detail": "Not Found"}
```

**Impacto:** Step 3 se queda en "Calculando..." forever o muestra NaN

---

## ✅ VERIFICACIÓN CON DATOS CORRECTOS

**Step 47:** Actualicé manualmente Factura 25 con datos correctos:
```javascript
{
  cups: 'ES0031103378680001TE',
  titular: 'JOSE ANTONIO RODRIGUEZ UROZ',
  consumo_p1_kwh: 59,
  consumo_p2_kwh: 55.99,
  consumo_p3_kwh: 166.72,
  total_factura: 38.88,
  periodo_dias: 30,
  atr: '2.0TD'
}
```

**Resultado:** 
- ✅ Comparador devuelve HTTP 200
- ✅ Ofertas calculadas correctamente
- ✅ Lógica backend funciona SI los datos son correctos

**Conclusión:** El backend funciona, pero OCR + Frontend tienen bugs críticos

---

## 📊 DATOS EXTRAÍDOS vs CORRECTOS

| Campo | OCR Extraído | Valor Correcto | Estado |
|-------|--------------|----------------|--------|
| CUPS | `ESVEROCANJEARTUSALDOHACIEN` | `ES0031103378680001TE` | ❌ |
| Cliente | `null` | `JOSE ANTONIO RODRIGUEZ UROZ` | ❌ |
| Consumo P1 | `15974.25` | `59.00` | ❌ |
| Consumo P2 | `15915.27` | `55.99` | ❌ |
| Consumo P3 | `15748.55` | `166.72` | ❌ |
| Total | `25` | `263.14` | ❌ |
| Periodo | `null` | `30` | ❌ |

**Score OCR:** 0/7 campos correctos = 0% accuracy

---

## 🔧 FIXES REQUERIDOS

### FIX 1: OCR - Regex CUPS (URGENTE)
```python
# app/services/ocr.py
# Mejorar regex para CUPS:
# - Ignorar texto con palabras ("ver", "canjear", "saldo")
# - Buscar pattern específico: ES + 16-20 dígitos/letras
```

### FIX 2: OCR - Distinguir Lecturas vs Consumos (URGENTE)
```python
# Buscar labels específicos:
# - "Consumo periodo" o "Consumo kWh"
# - Ignorar "Lectura actual" o "Lectura anterior"
# - Calcular: consumo = lectura_actual - lectura_anterior
```

### FIX 3: Frontend - URL Comparador (URGENTE)
```javascript
// app/wizard/[id]/step-3-comparar/page.jsx
// CAMBIAR:
- fetch(`/webhook/comparar/${id}`)
+ fetch(`/webhook/comparar/facturas/${id}`)
```

### FIX 4: Backend - Validar Periodo P1 (URGENTE)
```python
# app/services/comparador.py - compare_factura()
# Eliminar fallback, lanzar error:
if not periodo_dias:
    if not (factura.fecha_inicio and factura.fecha_fin):
        raise DomainError("PERIOD_REQUIRED")
```

### FIX 5: OCR - Extracción Cliente
```python
# Buscar patrones:
# - Después de "Titular:", "Nombre:", "Cliente:"
# - Formato: NOMBRE APELLIDO1 APELLIDO2
# - Filtrar términos técnicos
```

---

## 🧪 TESTS DE VALIDACIÓN

Después de los fixes, re-probar con:
1. `Factura Iberdrola.pdf`
2. `factura Naturgy.pdf`
3. Verificar campos extraídos
4. Verificar comparador con/sin periodo

---

## 📌 PRIORIDAD

**P0 (Bloqueante):**
- ❌ BUG 2: Lecturas vs Consumos
- ❌ BUG 5: Validación Periodo P1  
- ❌ BUG 6: URL Frontend

**P1 (Alto):**
- ❌ BUG 1: CUPS
- ❌ BUG 4: Total Factura
- ❌ BUG 3: Nombre Cliente

---

**Estado:** Sistema NO FUNCIONAL con facturas reales
**Requiere:** Fixes en OCR, Frontend y Backend
