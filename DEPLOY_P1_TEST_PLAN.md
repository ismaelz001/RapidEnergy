# 🚀 DEPLOY P1 PRODUCCIÓN - PLAN DE PRUEBAS

## 📦 CAMBIOS DEPLOYADOS

### Backend
- ✅ DomainError (errores con códigos)
- ✅ compare_factura SIN fallback a 30 días
- ✅ HTTP 422 para PERIOD_REQUIRED, PERIOD_INVALID
- ✅ Equivalentes: ahorro_mensual_equiv, ahorro_anual_equiv
- ✅ Auditoría en tabla comparativas (JSONB)

### Database (Neon)
- ✅ Campo periodo_dias en facturas
- ✅ Tabla comparativas creada
- ✅ Índices de performance

### Frontend
- ✅ Bug fixes P0
- ✅ dedupe UX mejorado
- ✅ step1 no bloquea si OCR falla

---

## 🧪 TESTS A REALIZAR EN PRODUCCIÓN

### Test 1: Periodo Obligatorio ❌ → HTTP 422
**Endpoint:** `POST https://mecaenergy-backend.onrender.com/webhook/comparar/facturas/{id}`

**Factura:** Una sin `periodo_dias` y sin fechas

**Resultado esperado:**
```json
HTTP 422
{
  "detail": {
    "code": "PERIOD_REQUIRED",
    "message": "Periodo es obligatorio (días o fechas inicio/fin)"
  }
}
```

**Verificación:**
- [ ] Status code es 422
- [ ] Response tiene `code: "PERIOD_REQUIRED"`
- [ ] Frontend puede capturar el error

---

### Test 2: Comparar con periodo ✅ → HTTP 200
**Endpoint:** `POST https://mecaenergy-backend.onrender.com/webhook/comparar/facturas/{id}`

**Factura:** Una con `periodo_dias = 60` o con fechas

**Resultado esperado:**
```json
HTTP 200
{
  "factura_id": 123,
  "comparativa_id": 1,
  "periodo_dias": 60,
  "current_total": 156.80,
  "offers": [
    {
      "provider": "Octopus Energy",
      "estimated_total_periodo": 142.50,
      "ahorro_periodo": 14.30,
      "ahorro_mensual_equiv": 7.21,
      "ahorro_anual_equiv": 86.73,
      "breakdown": {
        "periodo_dias": 60,
        ...
      }
    }
  ]
}
```

**Verificación:**
- [ ] Status code es 200
- [ ] Response tiene `comparativa_id`
- [ ] Response tiene `periodo_dias`
- [ ] Offers tienen `ahorro_mensual_equiv` y `ahorro_anual_equiv`
- [ ] `breakdown.periodo_dias` coincide con raíz

---

### Test 3: Auditoría en BD 💾
**SQL en Neon:**
```sql
-- Ver última comparativa
SELECT 
  id,
  factura_id,
  periodo_dias,
  current_total,
  inputs_json->>'cups' as cups,
  jsonb_array_length(offers_json) as num_offers,
  status,
  created_at
FROM comparativas 
ORDER BY id DESC 
LIMIT 1;
```

**Verificación:**
- [ ] Registro existe
- [ ] `inputs_json` tiene datos correctos (JSONB)
- [ ] `offers_json` tiene array de offers (JSONB)
- [ ] `periodo_dias` guardado correctamente

---

### Test 4: Equivalentes matemáticos 🧮
**Verificación manual:**

Para un periodo de 60 días:
```
ahorro_periodo = 14.30€

ahorro_mensual_equiv = 14.30 * (30.437 / 60)
                     = 14.30 * 0.5073
                     ≈ 7.25€

ahorro_anual_equiv = 14.30 * (365 / 60)
                   = 14.30 * 6.083
                   ≈ 87.0€
```

**Verificación:**
- [ ] Los números son coherentes
- [ ] Mensual ≈ periodo / 2 (para 60 días)
- [ ] Anual ≈ periodo * 6 (para 60 días)

---

## 🔍 VERIFICACIÓN LOGS RENDER

**Qué buscar en logs:**
```
✅ "Application startup complete"
✅ Sin errores de importación
✅ Sin errores SQL
```

**Errores comunes a verificar:**
```
❌ "ModuleNotFoundError: No module named 'app.exceptions'"
❌ "no such table: comparativas"
❌ "DomainError is not defined"
```

---

## 📊 CHECKLIST DEPLOY

- [ ] Commit created
- [ ] Push to main
- [ ] Render detecta deploy
- [ ] Build completo sin errores
- [ ] App reiniciada
- [ ] Logs OK
- [ ] Test 1: HTTP 422 funciona
- [ ] Test 2: HTTP 200 con periodo
- [ ] Test 3: comparativa en BD
- [ ] Test 4: Equivalentes correctos

---

## 🎯 CRITERIOS DE ÉXITO

✅ **ÉXITO TOTAL:**
- Todos los tests pasan
- No hay errores en logs
- Comparativas se guardan en BD
- Frontend puede manejar HTTP 422

⚠️ **ÉXITO PARCIAL:**
- Tests 1 y 2 pasan
- Test 3 tiene problemas de BD
- Frontend funciona pero hay warnings

❌ **FALLO:**
- App no arranca
- Errores en imports
- Tests 1 o 2 fallan

---

**Siguiente paso:** Esperar a que commit termine y hacer push
