# MVP CERRADO - ENERGY CRM

## Resumen de Entregables

Este documento resume los cambios implementados para cerrar el MVP de RapidEnergy con los 3 entregables solicitados:

### ✅ ENTREGABLE 1 — Persistencia de oferta seleccionada

**Backend:**
- ✅ Añadido campo `selected_offer_json` (TEXT) en tabla `facturas` (models.py)
- ✅ Migración SQL creada: `migration_offer_selection.sql`
- ✅ Endpoint **POST /webhook/facturas/{id}/seleccion**
  - Recibe oferta seleccionada
  - Persiste como JSON en `selected_offer_json`
  - Actualiza `estado_factura` = "oferta_seleccionada"
  - Devuelve confirmación con datos guardados

**Modelo Pydantic:**
- ✅ `OfferSelection` con validación de campos

### ✅ ENTREGABLE 2 — PDF real

**Backend:**
- ✅ Endpoint **GET /webhook/facturas/{id}/presupuesto.pdf**
  - Valida que exista oferta seleccionada (400 si no)
  - Genera PDF real usando ReportLab
  - Incluye: Cliente, CUPS, Total actual, Oferta (provider/plan/total/ahorro)
  - NO incluye comisión en el PDF
  - Devuelve `Content-Type: application/pdf` con descarga

**Dependencias:**
- ✅ Añadido `reportlab` a requirements.txt

### ✅ ENTREGABLE 3 — Conectar Step 3 (Frontend)

**API Client (lib/apiClient.js):**
- ✅ Función `selectOffer(facturaId, offer)` → POST persistencia
- ✅ Función `downloadPresupuestoPDF(facturaId)` → GET PDF blob

**Step 3 (app/wizard/[id]/step-3-comparar/page.jsx):**
- ✅ `handleGeneratePresupuesto` ahora es async y:
  1. Llama POST /seleccion para guardar oferta
  2. Llama GET /presupuesto.pdf para descargar
  3. Descarga automática del PDF
  4. Modal de éxito SOLO si ambos pasos son OK
- ✅ Manejo de errores real (no modal si falla)
- ✅ Eliminada referencia falsa a "email enviado"

### ✅ REGLA CUPS (obligatoria)

**Backend (webhook.py):**
- ✅ `validate_factura_completitud` ahora valida:
  - CUPS no puede estar vacío
  - Error claro: "CUPS es obligatorio y no puede estar vacío"
  - Bloquea transición a "lista_para_comparar"

**Frontend (step-2-validar/page.jsx):**
- ✅ CUPS añadido a `requiredFields`
- ✅ Campo marcado con asterisco (*)
- ✅ Error si vacío: "CUPS es obligatorio"
- ✅ Warning si formato raro: "Formato no estándar (permitido pero verifica)"
- ✅ Normalización on blur

### ✅ INFRA / LOCAL DB

**Gitignore:**
- ✅ `local.db` ya estaba en .gitignore

**Scripts:**
- ✅ `scripts/reset_local_db.py` ya existe con protección anti-prod

**README.md:**
- ✅ Documentado modo LOCAL (SQLite) vs PROD (Postgres)
- ✅ Variables de entorno necesarias
- ✅ Reglas CUPS
- ✅ Flujo completo MVP
- ✅ Endpoints documentados

---

## Archivos Modificados

### Backend (Python)
1. `app/db/models.py` → Añadido `selected_offer_json`
2. `app/routes/webhook.py` → 
   - Modelo `OfferSelection`
   - Validación CUPS obligatoria
   - Endpoint POST /seleccion
   - Endpoint GET /presupuesto.pdf
3. `requirements.txt` → Añadido `reportlab`

### Frontend (JavaScript/React)
4. `lib/apiClient.js` → Funciones `selectOffer` y `downloadPresupuestoPDF`
5. `app/wizard/[id]/step-3-comparar/page.jsx` → 
   - Flujo de generación real (async)
   - Descarga de PDF
   - Modal sin mensajes falsos
6. `app/wizard/[id]/step-2-validar/page.jsx` → 
   - CUPS obligatorio (required)
   - Validación mejorada

### Documentación
7. `README.md` → Documentación completa
8. `migration_offer_selection.sql` → Migración nueva

---

## Pruebas Manuales Requeridas

### Caso 1: Flujo completo happy path
1. Subir factura con CUPS válido
2. Validar datos en Step 2 (verificar que CUPS no puede estar vacío)
3. Comparar ofertas en Step 3
4. Seleccionar una oferta
5. Generar presupuesto → DEBE:
   - Guardar oferta en BD (selected_offer_json)
   - Descargar PDF real
   - Mostrar modal éxito SOLO después

### Caso 2: Recargar página después de selección
1. Completar flujo del Caso 1
2. Recargar dashboard
3. Verificar que la factura tiene `estado_factura = "oferta_seleccionada"`
4. Verificar que `selected_offer_json` está persistido

### Caso 3: Intentar continuar sin CUPS
1. Subir factura
2. En Step 2, dejar CUPS vacío
3. Intentar "Guardar y Continuar"
4. DEBE bloquearse con error claro: "CUPS es obligatorio"

### Caso 4: CUPS con formato raro
1. Subir factura
2. En Step 2, poner CUPS con formato raro (ej: "XXX123")
3. DEBE mostrar warning pero permitir continuar

### Caso 5: Intentar generar PDF sin selección
1. Llamar directamente GET /facturas/{id}/presupuesto.pdf sin haber seleccionado oferta
2. DEBE devolver 400: "No hay una oferta seleccionada"

---

## Comandos de Deployment

### Aplicar migración (LOCAL - SQLite)
```bash
sqlite3 local.db < migration_offer_selection.sql
```

### Aplicar migración (PROD - Neon)
Conectar a Neon SQL Editor y ejecutar:
```sql
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS selected_offer_json TEXT;
```

### Verificar migración
```sql
SELECT id, estado_factura, selected_offer_json 
FROM facturas 
WHERE selected_offer_json IS NOT NULL;
```

### Reinstalar dependencias (si cambia requirements.txt)
```bash
pip install -r requirements.txt
```

---

## Estado del MVP

🎉 **MVP CERRADO** con las siguientes capacidades reales:

1. ✅ Persistencia de selección de oferta
2. ✅ Generación de PDF real con datos reales
3. ✅ Validación estricta de CUPS (obligatorio no vacío)
4. ✅ Sin "éxitos falsos" (solo modal si hay persistencia + PDF)
5. ✅ Separación clara LOCAL vs PROD
6. ✅ Documentación completa

---

**Fecha:** 2026-01-09  
**Responsable:** Senior Full-Stack Engineer (Antigravity)
