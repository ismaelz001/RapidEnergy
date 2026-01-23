# ✅ INFORME TIPOS DE COLUMNAS Y FIX REQUERIDO

## ✅ TIPOS DE COLUMNA CONFIRMADOS

### ofertas_calculadas (tabla existente):
```sql
-- migration_ofertas_calculadas.sql líneas 9-11
coste_estimado NUMERIC(10, 2),   -- ✅ Ya es NUMERIC
ahorro_mensual NUMERIC(10, 2),   -- ✅ Ya es NUMERIC  
ahorro_anual NUMERIC(10, 2),     -- ✅ Ya es NUMERIC

-- ❌ NO EXISTE comision_eur en la migración original
```

### comisiones_tarifa (NO hay migración):
```
❌ Tabla NO creada en migraciones disponibles
Asumiendo: comision_eur probablemente sea NUMERIC o DECIMAL
```

### comisiones_cliente (NO hay migración):
```
❌ Tabla NO creada en migraciones disponibles
Asumiendo: comision_eur probablemente sea NUMERIC o DECIMAL
```

---

## ⚠️ PROBLEMA DETECTADO

**ofertas_calculadas NO tiene columnas comision_eur ni comision_source**

El código está intentando INSERT con:
```python
INSERT INTO ofertas_calculadas 
(comparativa_id, tarifa_id, coste_estimado, ahorro_mensual, ahorro_anual, 
 comision_eur, comision_source, detalle_json)  # ❌ Columnas inexistentes
```

Pero la tabla solo tiene:
```sql
id, comparativa_id, tarifa_id, coste_estimado, ahorro_mensual, 
ahorro_anual, detalle_json, created_at
```

---

## ✅ DIFF MÍNIMO REQUERIDO

### 1. MIGRACIÓN SQL (CREAR PRIMERO)

```sql
-- migration_add_comision_columns.sql

-- Agregar columnas comision a ofertas_calculadas
ALTER TABLE ofertas_calculadas
ADD COLUMN IF NOT EXISTS comision_eur NUMERIC(10, 2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS comision_source VARCHAR(20) DEFAULT 'manual';

CREATE INDEX IF NOT EXISTS idx_ofertas_calc_comision_source 
ON ofertas_calculadas(comision_source);

COMMENT ON COLUMN ofertas_calculadas.comision_eur 
IS 'Comisión aplicable a esta oferta (prioridad: cliente > tarifa > manual)';

COMMENT ON COLUMN ofertas_calculadas.comision_source 
IS 'Origen de la comisión: cliente, tarifa, manual';
```

### 2. FIX CÓDIGO (comparador.py)

**ANTES** (línea 309, 333):
```python
comisiones_cliente_map = {row[0]: round(float(row[1]), 2) for row in rows}  # ❌ float + round
comisiones_tarifa_map = {row[0]: round(float(row[1]), 2) for row in rows}   # ❌ float + round
```

**DESPUÉS**:
```python
from decimal import Decimal

comisiones_cliente_map = {row[0]: Decimal(str(row[1])) for row in rows}  # ✅ Decimal directo
comisiones_tarifa_map = {row[0]: Decimal(str(row[1])) for row in rows}   # ✅ Decimal directo
```

**ANTES** (línea 344, 362):
```python
comision_eur = 0.0  # ❌ float
payload = {
    "comision_eur": round(comision_eur, 2),  # ❌ round float
}
```

**DESPUÉS**:
```python
comision_eur = Decimal('0.00')  # ✅ Decimal
payload = {
    "comision_eur": comision_eur,  # ✅ Decimal directo (SQLAlchemy lo maneja)
}
```

---

## 📋 FRAGMENTO CÓDIGO EXACTO (ACTUAL)

### Prefetch (líneas 275-335):
```python
# Prefetch comisiones_cliente
rows = db.execute(
    text("""
        WITH ranked AS (
            SELECT tarifa_id, comision_eur,
                ROW_NUMBER() OVER (...) as rn
            FROM comisiones_cliente
            WHERE cliente_id = :cid AND tarifa_id = ANY(:tids)
        )
        SELECT tarifa_id, comision_eur FROM ranked WHERE rn = 1
    """),
    {"cid": cliente_id, "tids": tarifa_ids}  # ✅ Binding correcto
).fetchall()
comisiones_cliente_map = {row[0]: round(float(row[1]), 2) for row in rows}  # ❌ AQUÍ
```

### Loop (líneas 337-375):
```python
for idx, offer in enumerate(offers):
    tid = offer.get("tarifa_id")
    if tid is None:
        logger.warning(...)
        continue
    
    comision_eur = 0.0  # ❌ float
    comision_source = "manual"
    
    if tid in comisiones_cliente_map:
        comision_eur = comisiones_cliente_map[tid]  # ❌ Asigna float
        comision_source = "cliente"
    elif tid in comisiones_tarifa_map:
        comision_eur = comisiones_tarifa_map[tid]  # ❌ Asigna float
        comision_source = "tarifa"
    
    offer["comision_eur"] = comision_eur  # Para JSON (OK con float)
    offer["comision_source"] = comision_source
    
    payload = {
        "comision_eur": round(comision_eur, 2),  # ❌ round float
        "comision_source": comision_source,
    }
    
    db.execute(stmt, payload)  # ✅ Binding correcto con :comision_eur
```

---

## ✅ BINDING tids (CORRECTO)

```python
{"cid": cliente_id, "tids": tarifa_ids}
# tarifa_ids = [1, 2, 3, 11, 22]  # Lista Python

# Postgres convierte automáticamente a ARRAY en ANY(:tids)
# SQLAlchemy con text() maneja esto correctamente
```

**✅ NO hay problema de tipado**

---

## ⚠️ RIESGOS SI NO SE MIGRA

### Si NO agregas columnas comision_eur y comision_source:
```
❌ INSERT fallará con: 
   column "comision_eur" of relation "ofertas_calculadas" does not exist
   
🔥 TODAS las comparaciones fallarán
```

### Si usas float() en vez de Decimal():
```
⚠️  DB almacena: 55.00 → Python lee: 55.0000000003
⚠️  Errores de precisión acumulativos en cálculos
⚠️  Problemas en reportes fiscales/contables
```

---

## 🚀 ORDEN DE APLICACIÓN

1. **Ejecutar migración SQL en Neon**:
   ```bash
   psql $DATABASE_URL < migration_add_comision_columns.sql
   ```

2. **Modificar comparador.py**:
   - Cambiar `float()` por `Decimal(str(...))`
   - Cambiar `0.0` por `Decimal('0.00')`
   - Eliminar `round(..., 2)`

3. **Deploy**

---

## ✅ DIFF MÍNIMO PARCHE

```python
# Línea 3 (imports)
from decimal import Decimal

# Línea 309
- comisiones_cliente_map = {row[0]: round(float(row[1]), 2) for row in rows}
+ comisiones_cliente_map = {row[0]: Decimal(str(row[1])) for row in rows}

# Línea 333
- comisiones_tarifa_map = {row[0]: round(float(row[1]), 2) for row in rows}
+ comisiones_tarifa_map = {row[0]: Decimal(str(row[1])) for row in rows}

# Línea 344
- comision_eur = 0.0
+ comision_eur = Decimal('0.00')

# Línea 359 (offer JSON - puede seguir siendo float)
  offer["comision_eur"] = float(comision_eur)  # Para JSON

# Línea 362
- "comision_eur": round(comision_eur, 2),
+ "comision_eur": comision_eur,
```

---

**STATUS**: ❌ **BLOQUEANTE - REQUIERE MIGRACIÓN SQL PRIMERO**
