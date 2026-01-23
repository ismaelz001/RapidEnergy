# 🔴 BUG ROOT CAUSE + FIX — ofertas_calculadas vacía

## ✅ CAUSA RAÍZ IDENTIFICADA

**Archivo**: `app/services/comparador.py`  
**Líneas**: 613, 620, 329

### **PROBLEMA EXACTO**:

**DOBLE COMMIT EN TRANSACCIONES SEPARADAS**:

```python
# ❌ ANTES (CÓDIGO ROTO):

# Línea 613: COMMIT #1 (guarda comparativas)
db.commit()

# Línea 620: Llama a función separada
_persist_results(db, factura.id, offers, comparativa_id)

# Línea 329 (dentro de _persist_results): COMMIT #2 (intenta guardar ofertas)
if inserted:
    db.commit()  # ← SOLO si inserted=True
```

**POR QUÉ FALLA**:

1. Después del **primer commit** (línea 613), la transacción de `comparativas` está cerrada
2. `_persist_results` inicia una **NUEVA transacción separada** 
3. Si `_insert_ofertas` retorna `False` → **NO HAY COMMIT** (línea 328-329)
4. Ofertas se pierden porque nunca se hizo commit
5. Si hay error, el `rollback()` en línea 331 **NO AFECTA** a comparativas (ya committed)

---

## ✅ SOLUCIÓN APLICADA

**UNA SOLA TRANSACCIÓN UNIFICADA**:

```python
# ✅ AHORA (CÓDIGO CORRECTO):

try:
    # 1. Crear comparativa
    comparativa = Comparativa(...)
    db.add(comparativa)
    db.flush()  # ← Solo flush, NO commit
    comparativa_id = comparativa.id
    
    # 2. Insertar ofertas (MISMA transacción)
    inserted = _insert_ofertas(db, factura.id, comparativa_id, offers)
    
    if not inserted:
        comparativa.status = "error"
    
    # 3. COMMIT ÚNICO
    db.commit()  # ← Guarda ambos: comparativa + ofertas

except Exception as e:
    db.rollback()  # ← Revierte TODO si falla
```

---

## 📋 CAMBIOS APLICADOS

### **1. comparador.py líneas 586-643**:

**ANTES**:
- Dos commits separados
- _persist_results hace commit condicional
- Sin logs detallados

**DESPUÉS**:
- Un solo commit unificado
- Logs `[OFERTAS]` en cada paso
- Error handling con rollback completo
- Marca comparativa como "error" si ofertas fallan

### **2. comparador.py líneas 318-332** (ELIMINADOS):

**Función `_persist_results` BORRADA** → Ya no se necesita

---

## 🧪 CHECKLIST DE VERIFICACIÓN

### **PASO 1: Deploy del fix**

```bash
git add app/services/comparador.py
git commit -m "FIX CRÍTICO: Transacción unificada para comparativas + ofertas_calculadas"
git push origin main
```

### **PASO 2: Ejecutar comparación de prueba**

1. Subir factura PDF
2. Comparar ofertas
3. Verificar logs en Render:

```
[OFERTAS] ENTER persistence for factura_id=XXX
[OFERTAS] Comparativa created with id=YYY
[OFERTAS] Inserted 9 offers for comparativa_id=YYY
[OFERTAS] Transaction committed successfully for comparativa_id=YYY
```

### **PASO 3: Verificar en Neon SQL**

#### **3A: Verificar última comparativa**

```sql
SELECT 
    id,
    factura_id,
    periodo_dias,
    current_total,
    status,
    created_at
FROM comparativas
ORDER BY created_at DESC
LIMIT 1;
```

**Esperado**: `status='ok'`, `created_at` reciente

#### **3B: Contar ofertas insertadas**

```sql
SELECT 
    c.id AS comparativa_id,
    c.factura_id,
    c.created_at,
    COUNT(o.id) AS num_ofertas
FROM comparativas c
LEFT JOIN ofertas_calculadas o ON c.id = o.comparativa_id
WHERE c.created_at > NOW() - INTERVAL '1 hour'
GROUP BY c.id, c.factura_id, c.created_at
ORDER BY c.created_at DESC;
```

**Esperado**: `num_ofertas = 9` para cada comparativa reciente

#### **3C: Ver ofertas insertadas con detalle**

```sql
SELECT 
    o.id,
    o.comparativa_id,
    o.tarifa_id,
    o.coste_estimado,
    o.ahorro_mensual,
    o.ahorro_anual,
    o.detalle_json->>'plan_name' AS plan_name,
    o.created_at
FROM ofertas_calculadas o
WHERE o.comparativa_id = (
    SELECT id FROM comparativas ORDER BY created_at DESC LIMIT 1
)
ORDER BY o.coste_estimado ASC;
```

**Esperado**: 9 filas con datos completos

#### **3D: Verificar integridad JSON**

```sql
SELECT 
    id,
    tarifa_id,
    jsonb_typeof(detalle_json) AS json_type,
    detalle_json->'tarifa_id' AS tarifa_id_json,
    detalle_json->>'plan_name' AS plan_name
FROM ofertas_calculadas
WHERE comparativa_id = (SELECT id FROM comparativas ORDER BY created_at DESC LIMIT 1)
LIMIT 3;
```

**Esperado**: `json_type='object'`, datos válidos en JSON

---

## 🚨 TROUBLESHOOTING

### **Si ofertas_calculadas sigue vacía**:

1. **Verificar logs Render**:
   - Buscar `[OFERTAS] ENTER`
   - Si NO aparece → El comparador no se está ejecutando
   - Si aparece pero NO hay `Transaction committed` → Hay excepción

2. **Verificar excepción**:
   ```bash
   # En Render logs, buscar:
   [OFERTAS] ROLLBACK
   ```
   - Si aparece, revisar el traceback completo

3. **Verificar que tabla existe**:
   ```sql
   SELECT COUNT(*) FROM ofertas_calculadas;
   ```
   - Si error "relation does not exist" → Ejecutar `migration_ofertas_calculadas.sql`

### **Si comparativas tiene status='error'**:

```sql
SELECT id, factura_id, status, error_json 
FROM comparativas 
WHERE status='error' 
ORDER BY created_at DESC 
LIMIT 5;
```

- Revisar `error_json` para ver causa exacta

---

## 📊 IMPACTO ESPERADO

### **ANTES del fix**:
- `comparativas`: ✅ Se llenaba (offers_json guardado)
- `ofertas_calculadas`: ❌ Siempre 0 filas

### **DESPUÉS del fix**:
- `comparativas`: ✅ Se llena (igual que antes)
- `ofertas_calculadas`: ✅ 9 filas por comparativa

---

## ✅ VALIDACIÓN FINAL

**Test E2E**:
1. Subir factura → `POST /webhook/upload`
2. Comparar → `POST /webhook/comparar/facturas/{id}`
3. Ejecutar queries SQL 3B y 3C
4. ✅ Confirmar 9 ofertas insertadas
5. ✅ Confirmar logs `[OFERTAS] Transaction committed`

**Tiempo estimado**: 5-10 minutos (deploy + test + SQL)

---

**Fix aplicado por**: Senior Backend Engineer  
**Fecha**: 2026-01-19 07:25:00 CET  
**Status**: ✅ READY TO DEPLOY
