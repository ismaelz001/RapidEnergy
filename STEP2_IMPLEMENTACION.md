# IMPLEMENTACIÓN STEP 2: Validación Comercial

**Fecha:** 2026-01-26  
**Autor:** Antigravity AI  
**Estado:** ✅ Implementado (Pendiente Pruebas)

---

## 📋 RESUMEN EJECUTIVO

Se ha implementado el **STEP 2 - Validación Comercial**, una capa de transparencia que permite al asesor ajustar conceptos no comparables (Bono Social, descuentos temporales, servicios vinculados) antes de ejecutar el comparador.

**Cifra Reina:** El `total_ajustado` se convierte en la línea base real contra la que se comparan las ofertas.

**Principios:**
- ✅ Transparente: Todo ajuste queda documentado en el PDF
- ✅ Honesto: Warnings automáticos si hay ajustes significativos
- ✅ No invasivo: El motor de cálculo NO se toca
- ✅ Trazable: Auditoría completa en JSON

---

## 🏗️ ARQUITECTURA IMPLEMENTADA

### 1. MODELO DE DATOS

**Archivos:**
- `app/schemas/validacion.py` - Schemas Pydantic con validaciones
- `app/db/models.py` - Campos añadidos a tabla `facturas`

**Nuevos campos en `facturas`:**
```sql
ajustes_comerciales_json TEXT       -- JSON de AjustesComerciales
total_ajustado DOUBLE PRECISION     -- Total post-ajustes (cifra reina)
validado_step2 BOOLEAN DEFAULT FALSE -- Flag de validación
```

**Estructura JSON de ajustes:**
```json
{
  "bono_social": {
    "activo": true,
    "descuento_estimado": 12.50,
    "origen": "ocr_auto",
    "nota_pdf": "...textо explicativo..."
  },
  "descuento_comercial": {
    "importe": 4.50,
    "descripcion": "Descuento 10% primer año",
    "temporal": true,
    ...
  },
  "servicios_vinculados": {...},
  "alquiler_contador": {...}
}
```

---

### 2. SERVICIO DE NEGOCIO

**Archivo:** `app/services/validacion_comercial.py`

**Funciones principales:**
```python
calcular_totales(total_original, ajustes) -> TotalesCalculados
generar_warnings(ajustes, totales) -> List[str]
generar_notas_pdf(ajustes) -> Dict[str, str]
validar_factura_comercialmente(factura, ajustes, modo) -> Response
```

**Warnings Automáticos:**
- ⚠️ Descuento comercial > 5€
- ⚠️ Bono Social activado manualmente sin OCR
- 🚨 Total ajustado < 50% del original (posible error)
- ℹ️ Servicios > 10€ sin descripción

---

### 3. API ENDPOINT

**Archivo:** `app/routes/webhook.py`

**Endpoint:**
```
PUT /webhook/facturas/{factura_id}/validar
```

**Request Body:**
```json
{
  "ajustes_comerciales": {
    "bono_social": {"activo": true, "descuento_estimado": 12.50},
    "descuento_comercial": {"importe": 4.50, "descripcion": "..."},
    ...
  },
  "modo": "asesor"
}
```

**Response:**
```json
{
  "factura_id": 123,
  "base_factura": {...datos bloqueados...},
  "ajustes_comerciales": {...},
  "totales_calculados": {
    "total_original": 41.84,
    "total_descuentos_excluidos": 17.00,
    "total_ajustado_comparable": 58.84
  },
  "warnings": ["..."],
  "ready_to_compare": true
}
```

---

### 4. INTEGRACIÓN CON COMPARADOR

**Archivo:** `app/services/comparador.py`

**Cambio en `compare_factura()`:**
```python
# ANTES
current_total = factura.total_factura

# DESPUÉS
if factura.validado_step2 and factura.total_ajustado:
    current_total = factura.total_ajustado  # Usa cifra ajustada
else:
    current_total = factura.total_factura   # Fallback
```

**Logging:**
```
[STEP2] Usando total_ajustado=58.84 como línea base (factura_id=123)
```

---

### 5. INTEGRACIÓN CON PDF

**Archivo:** `app/services/pdf_generator.py`

**Sección Nueva: "Metodología de Comparación"**

Se inserta entre **Tabla 1** (Factura) y **Tabla 2** (Estudio Comparativo) si `factura.validado_step2 == True`.

**Contenido:**
```
METODOLOGÍA DE COMPARACIÓN
──────────────────────────────────────

Este estudio compara el coste estructural...

Total de tu factura original:   41.84 €
Ajustes aplicados:            +17.00 €
─────────────────────────────────────
Total usado para comparar:      58.84 €

AJUSTES REALIZADOS:

⭐ Bono Social (-12.50 €)
   Tu factura incluye Bono Social...

⚠️ Descuento Comercial Temporal (-4.50 €)
   "Descuento 10% primer año"
   ...
```

---

## 📊 FLUJO COMPLETO

```
1. Usuario sube factura
   ↓
2. OCR extrae datos
   ↓
3. STEP 1: Validación de completitud (existente)
   ↓
4. STEP 2: Validación Comercial (NUEVO ⭐)
   - Asesor revisa/ajusta conceptos no comparables
   - PUT /facturas/{id}/validar
   - Sistema calcula total_ajustado
   - Genera warnings si aplica
   ↓
5. Comparador usa total_ajustado como línea base
   ↓
6. PDF muestra metodología + ajustes aplicados
```

---

## 🧪 TESTING REQUERIDO

### Casos de Prueba Obligatorios:

1. **Sin ajustes (baseline)**
   - Validar factura sin modificar nada
   - Verificar: `total_ajustado == total_factura`
   - PDF NO debe mostrar sección de metodología

2. **Con Bono Social**
   - Activar Bono Social con `descuento_estimado=12.50`
   - Verificar: `total_ajustado = total_original + 12.50`
   - PDF debe mostrar explicación de Bono Social

3. **Con Descuento > 5€**
   - Añadir descuento comercial de 10€
   - Verificar: Warning generado
   - Verificar: Total ajustado correcto

4. **Warnings de Seguridad**
   - Total ajustado < 50% original → Warning crítico
   - Servicios > 10€ sin descripción → Warning info

5. **Comparador Integration**
   - Factura validada en Step 2 → Comparador usa `total_ajustado`
   - Factura NO validada → Comparador usa `total_factura`

6. **PDF Generation**
   - Factura con ajustes → PDF muestra metodología
   - Factura sin ajustes → PDF normal (sin metodología)

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deploy (Bloqueante):

- [ ] **Migración SQL**: Ejecutar `migrations/step2_validacion_comercial.sql` en Neon
- [ ] **Test Schemas**: Validar que Pydantic parsea JSON correctamente
- [ ] **Test Endpoint**: `PUT /facturas/{id}/validar` responde 200
- [ ] **Test Comparador**: Logs muestran `[STEP2] Usando total_ajustado=...`
- [ ] **Test PDF**: Sección "Metodología" aparece si `validado_step2=True`

### Post-Deploy (Nice-to-Have):

- [ ] **Analytics**: Trackear % de facturas que pasan por Step 2
- [ ] **A/B Testing**: Copy de warnings (optimizar conversión)
- [ ] **Dashboard Asesor**: Vista de facturas pendientes de validación

---

## 📁 ARCHIVOS MODIFICADOS/CREADOS

### Creados:
```
app/schemas/validacion.py           (272 líneas)
app/services/validacion_comercial.py (243 líneas)
migrations/step2_validacion_comercial.sql (52 líneas)
STEP2_IMPLEMENTACION.md              (Este documento)
```

### Modificados:
```
app/db/models.py                     (+3 campos en Factura)
app/routes/webhook.py                (+91 líneas, nuevo endpoint)
app/services/comparador.py           (+11 líneas, integración)
app/services/pdf_generator.py        (+73 líneas, metodología)
```

**Total:** ~750 líneas de código nuevo/modificado

---

## 🔧 CONFIGURACIÓN REQUERIDA

### Base de Datos (Neon):
```bash
psql $DATABASE_URL < migrations/step2_validacion_comercial.sql
```

### Variables de Entorno:
No se requieren nuevas variables.

### Dependencias:
No se requieren nuevas dependencias (usa Pydantic existente).

---

## 📞 SOPORTE

**Errores Comunes:**

1. **`column "ajustes_comerciales_json" does not exist`**
   - Solución: Ejecutar migración SQL en Neon

2. **`model_dump_json() not found`**
   - Solución: Actualizar Pydantic a v2.x (ya debería estar)

3. **PDF no muestra metodología**
   - Verificar: `factura.validado_step2 == True`
   - Verificar: `factura.ajustes_comerciales_json` no es NULL

---

## 🎯 PRÓXIMOS PASOS

1. **Frontend (Pendiente):**
   - Crear interfaz del Step 2 en React
   - Implementar toggle Modo Asesor / Modo Cliente
   - Mostrar warnings en tiempo real

2. **Optimizaciones:**
   - Cachear cálculos de ajustes
   - Pre-detectar Bono Social con ML (OCR mejorado)
   - Templates de ajustes frecuentes

3. **Analytics:**
   - Dashboard de ajustes más comunes
   - Tasa de conversión Step 2 → Comparación
   - Tiempo promedio en Step 2

---

**FIN DEL DOCUMENTO**

Implementación lista para testing. Requiere ejecutar migración SQL en Neon antes de usar el endpoint.
