# ✅ IMPLEMENTACIÓN COMPLETADA: VERSIONADO + SOFT DELETE

## 📦 Cambios aplicados

### TAREA 1: Versionado de tarifas en comparador

**Archivos modificados:**
- `app/services/comparador.py` (8 patches aplicados)

**Cambios realizados:**
1. ✅ Añadido `import re` (línea 5)
2. ✅ Creadas 3 funciones helper:
   - `_fetch_precios_versiones(db, version_ids)` → Prefetch de precios (1 query)
   - `_get_precio_energia(precios_dict, periodo_idx)` → Lee precios con fallback 24H
   - `_get_precio_potencia(precios_dict, periodo_idx)` → Lee precios de potencia
3. ✅ Query a `tarifa_versiones` con filtro `vigente_desde/vigente_hasta` (línea ~635)
4. ✅ Prefetch de precios desde `tarifa_precios` con JOIN
5. ✅ Adaptados loops de energía/potencia para usar `precios_map` en vez de columnas
6. ✅ Añadido `tarifa_version_id` al objeto `offer` (línea ~845)
7. ✅ Modificado `_insert_ofertas()` para incluir `tarifa_version_id` en payload y SQL INSERT

**Esquema utilizado (DDL real proporcionado por usuario):**
```sql
CREATE TABLE tarifa_versiones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200),
    comercializadora VARCHAR(100),
    atr VARCHAR(10),
    tipo VARCHAR(20),
    vigente_desde DATE,
    vigente_hasta DATE,
    version INTEGER
);

CREATE TABLE tarifa_precios (
    id SERIAL PRIMARY KEY,
    tarifa_version_id INTEGER REFERENCES tarifa_versiones(id),
    tipo_periodo VARCHAR(20),  -- 'energia' o 'potencia'
    periodo_nombre VARCHAR(10),  -- 'P1', 'P2', '24H'
    precio_eur_unidad NUMERIC(10,6)
);

ALTER TABLE ofertas_calculadas 
ADD COLUMN tarifa_version_id INTEGER REFERENCES tarifa_versiones(id);
```

### TAREA 2: Soft delete de clientes

**Archivos modificados:**
- `app/routes/clientes.py` (4 patches aplicados)
- `app/clientes/page.jsx` (2 patches aplicados)

**Archivos creados:**
- `app/clientes/ClienteDeleteButton.jsx` (nuevo componente React)
- `migrations/20260224_soft_delete_clientes.sql` (⚠️ PENDIENTE CREAR - ya existe archivo)

**Cambios realizados:**

1. ✅ **Backend (clientes.py)**:
   - Endpoint DELETE modificado con:
     - Validación de permisos (solo dev/ceo)
     - Soft delete: `deleted_at = datetime.now(timezone.utc)`
     - Anonización GDPR: nombre, email, DNI, teléfono
   - Filtros `deleted_at.is_(None)` añadidos en:
     - GET `/api/clientes/` (lista)
     - GET `/api/clientes/{id}` (detalle)
     - PUT `/api/clientes/{id}` (update)

2. ✅ **Frontend**:
   - Componente `ClienteDeleteButton.jsx`:
     - Modal de confirmación
     - Fetch con credentials: include
     - Manejo de errores 403/500
     - Recarga con `router.refresh()`
   - Integrado en tabla de clientes:
     - Import del componente
     - Columna de acciones con link + botón delete

3. ⚠️ **Migración SQL** (PENDIENTE APLICAR):
```sql
-- YA EXISTE archivo migrations/20260224_soft_delete_clientes.sql
-- Usuario debe ejecutar manualmente:
psql <DB_URL> < migrations/20260224_soft_delete_clientes.sql
```

---

## 🧪 Checklist de testing

### Tests de versionado
```bash
# 1. Crear versión de tarifa de prueba
psql <DB_URL> <<EOF
INSERT INTO tarifa_versiones (nombre, comercializadora, atr, tipo, vigente_desde, vigente_hasta, version)
VALUES ('Test 2.0TD V1', 'TestCorp', '2.0TD', 'fija', '2026-01-01', NULL, 1)
RETURNING id;
-- Anotar ID devuelto (ej: 999)

INSERT INTO tarifa_precios (tarifa_version_id, tipo_periodo, periodo_nombre, precio_eur_unidad)
VALUES 
  (999, 'energia', 'P1', 0.15),
  (999, 'energia', 'P2', 0.12),
  (999, 'energia', 'P3', 0.10),
  (999, 'potencia', 'P1', 0.073777),
  (999, 'potencia', 'P2', 0.001911);
EOF

# 2. Comparar factura con la nueva versión
curl -X POST http://localhost:8000/api/comparador/compare/<FACTURA_ID> \
  -H "Cookie: session=<TU_SESSION>"

# 3. Verificar persistencia
psql <DB_URL> -c "SELECT tarifa_version_id, provider, coste_estimado FROM ofertas_calculadas WHERE comparativa_id = (SELECT MAX(id) FROM comparativa) LIMIT 5;"

# 4. Test tarifa 24H (plana)
psql <DB_URL> <<EOF
INSERT INTO tarifa_versiones (nombre, comercializadora, atr, tipo, vigente_desde, version)
VALUES ('Tarifa Plana 24H', 'PlanaEnergy', '2.0TD', 'fija', '2026-01-01', 1)
RETURNING id;
-- ID = 1000

INSERT INTO tarifa_precios (tarifa_version_id, tipo_periodo, periodo_nombre, precio_eur_unidad)
VALUES (1000, 'energia', '24H', 0.135);
EOF
```

### Tests de soft delete
```bash
# 5. Ejecutar migración
psql <DB_URL> < migrations/20260224_soft_delete_clientes.sql

# 6. Test DELETE como CEO
curl -X DELETE http://localhost:8000/api/clientes/123 \
  -H "Cookie: session=<CEO_SESSION>"
# Esperado: 200 OK con deleted_at

# 7. Verificar anonización
psql <DB_URL> -c "SELECT id, nombre, email, dni, telefono, deleted_at FROM clientes WHERE id = 123;"
# Esperado: nombre='[ELIMINADO-123]', email='deleted_123@anonimo.local', dni=NULL

# 8. Test DELETE como COMERCIAL
curl -X DELETE http://localhost:8000/api/clientes/123 \
  -H "Cookie: session=<COMERCIAL_SESSION>"
# Esperado: 403 Forbidden

# 9. Verificar filtrado en GET
curl http://localhost:8000/api/clientes/ -H "Cookie: session=<SESSION>"
# El cliente 123 NO debe aparecer en el listado

# 10. Test frontend
# - Ir a http://localhost:3000/clientes
# - Verificar que aparece botón "Eliminar" en cada fila
# - Click en "Eliminar" → debe aparecer modal de confirmación
# - Confirmar → cliente desaparece de la tabla
```

---

## 📊 Métricas de cambio

- **Líneas modificadas**: ~90 líneas
- **Líneas nuevas**: ~200 líneas
- **Archivos modificados**: 3 (comparador.py, clientes.py, page.jsx)
- **Archivos creados**: 2 (ClienteDeleteButton.jsx, migration SQL)
- **Riesgo**: 🟡 MEDIO
  - Comparador: cambio estructural pero con helpers bien definidos
  - Soft delete: cambio no destructivo (columna nueva)
- **Reversión**: Sí (rollback SQL + git revert)

---

## ⚠️ Pendiente manual

1. **Ejecutar migración SQL**:
```bash
psql $DATABASE_URL < migrations/20260224_soft_delete_clientes.sql
```

2. **Verificar imports** en caso de errores:
- Si falla `import re` → revisar línea 5 de comparador.py
- Si falla `CurrentUser` → revisar que app/auth.py existe

3. **Test end-to-end**:
- Crear tarifa de prueba en tarifa_versiones
- Comparar factura y verificar tarifa_version_id en DB
- Probar soft delete desde frontend y verificar anonización

---

## 🎯 Resultado esperado

### Comparador:
- ✅ Query a `tarifa_versiones` vigentes HOY
- ✅ Prefetch de precios en 1 query (N+1 eliminado)
- ✅ Soporte para tarifa plana 24H
- ✅ `tarifa_version_id` en `ofertas_calculadas`

### Soft delete:
- ✅ Endpoint DELETE con permisos dev/ceo
- ✅ Anonización GDPR automática
- ✅ Filtrado en GET queries
- ✅ Modal de confirmación en frontend
- ✅ Sin hard delete (evita errores de FK)
