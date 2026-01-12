# 🧪 CHECKLIST DE PRUEBAS MANUALES - MVP ENERGY

## Pre-requisitos
- ✅ Backend corriendo: `uvicorn app.main:app --reload`
- ✅ Frontend corriendo: `npm run dev`
- ✅ Base de datos migrada (columna `selected_offer_json` existe)
- ✅ Dependencia `reportlab` instalada

---

## 🎯 TEST 1: Flujo completo happy path (CRÍTICO)

### Objetivo
Verificar que todo el flujo funciona de punta a punta con persistencia real.

### Pasos
1. **Subir factura**
   - Ir a http://localhost:3000/dashboard
   - Click "Nueva factura"
   - Subir PDF con CUPS válido (ej: ES0021000000000000AB)
   - ✅ Verificar: Redirección a Paso 2

2. **Validar datos (Step 2)**
   - Verificar que CUPS está presente
   - Completar campos obligatorios (ATR, Potencias P1/P2, Consumos P1/P2/P3, Total)
   - ✅ Verificar: Botón "SIGUIENTE" está habilitado
   - Click "SIGUIENTE"

3. **Comparar ofertas (Step 3)**
   - ✅ Verificar: Se muestran ofertas calculadas
   - ✅ Verificar: Se muestra "Ahorro anual estimado"
   - Seleccionar una oferta (click en tarjeta)
   - ✅ Verificar: Aparece panel "Oferta seleccionada"

4. **Generar presupuesto**
   - Click "GENERAR PRESUPUESTO"
   - ✅ Verificar: Se descarga PDF automáticamente
   - ✅ Verificar: Aparece modal "¡Presupuesto Generado!"
   - ✅ Verificar: Mensaje dice "revisa tu carpeta de descargas" (NO menciona email)
   - Abrir PDF descargado
   - ✅ Verificar PDF contiene:
     - Cliente
     - CUPS
     - Total factura actual
     - Comercializadora y tarifa seleccionada
     - Ahorro mensual y anual
     - Fecha actual
     - NO contiene comisión

5. **Verificar persistencia en BD**
   ```sql
   SELECT id, estado_factura, selected_offer_json 
   FROM facturas 
   WHERE id = [ID_FACTURA];
   ```
   - ✅ `estado_factura` = "oferta_seleccionada"
   - ✅ `selected_offer_json` contiene JSON con la oferta

---

## 🎯 TEST 2: Persistencia tras recargar (CRÍTICO)

### Objetivo
Verificar que la selección se mantiene después de recargar la página.

### Pasos
1. Completar TEST 1
2. Recargar la página del dashboard (F5)
3. ✅ Verificar: La factura aparece en el dashboard
4. ✅ Verificar: El estado muestra "oferta_seleccionada"
5. Ver detalle de la factura en la base de datos
   - ✅ `selected_offer_json` sigue presente

---

## 🎯 TEST 3: CUPS vacío debe bloquear (CRÍTICO)

### Objetivo
Verificar que CUPS vacío impide continuar desde Step 2.

### Pasos
1. Subir factura nueva
2. En Step 2, BORRAR el valor de CUPS (dejar vacío)
3. Intentar completar otros campos obligatorios
4. ✅ Verificar: Campo CUPS muestra error "CUPS es obligatorio"
5. ✅ Verificar: Botón "SIGUIENTE" está DESHABILITADO
6. ✅ Verificar: Banner inferior muestra "Completa los campos mínimos: CUPS, ..."

---

## 🎯 TEST 4: CUPS con formato raro (ADVERTENCIA, no bloqueo)

### Objetivo
Verificar que CUPS con formato no estándar muestra warning pero permite continuar.

### Pasos
1. Subir factura nueva
2. En Step 2, escribir CUPS raro: "XXX123456789"
3. ✅ Verificar: Campo CUPS muestra warning "Formato no estándar (permitido pero verifica)"
4. ✅ Verificar: El color del warning es ambar/amarillo (no rojo de error)
5. Completar otros campos obligatorios
6. ✅ Verificar: Botón "SIGUIENTE" está HABILITADO
7. Click "SIGUIENTE"
8. ✅ Verificar: Permite pasar al Step 3

---

## 🎯 TEST 5: Error si no hay oferta seleccionada

### Objetivo
Verificar que no se puede generar PDF sin seleccionar oferta.

### Pasos
1. Subir factura y completar hasta Step 3
2. Llamar directamente al endpoint (sin seleccionar oferta):
   ```bash
   curl http://localhost:8000/webhook/facturas/[ID]/presupuesto.pdf
   ```
   - ✅ Verificar: Respuesta HTTP 400
   - ✅ Verificar: Mensaje "No hay una oferta seleccionada para esta factura"

---

## 🎯 TEST 6: Error si falla persistencia

### Objetivo
Verificar que el frontend maneja errores correctamente.

### Pasos
1. Completar Step 1 y 2
2. En Step 3, seleccionar oferta
3. APAGAR el backend temporalmente
4. Click "GENERAR PRESUPUESTO"
5. ✅ Verificar: NO aparece modal de éxito
6. ✅ Verificar: Aparece mensaje de error
7. ✅ Verificar: No se descargó ningún PDF

---

## 🎯 TEST 7: Validación backend CUPS vacío

### Objetivo
Verificar que el backend rechaza facturas sin CUPS al comparar.

### Pasos
1. Crear factura con CUPS vacío directamente en BD:
   ```sql
   UPDATE facturas SET cups = NULL WHERE id = [ID];
   ```
2. Llamar endpoint de comparación:
   ```bash
   curl -X POST http://localhost:8000/webhook/comparar/facturas/[ID]
   ```
3. ✅ Verificar: Respuesta HTTP 400
4. ✅ Verificar: Mensaje contiene "CUPS es obligatorio"

---

## 📊 Resumen de Estados Esperados

| Paso | Estado Factura | selected_offer_json | Puede generar PDF |
|------|----------------|---------------------|-------------------|
| Después de upload | `pendiente_datos` | `NULL` | ❌ No |
| Después de validar | `lista_para_comparar` | `NULL` | ❌ No |
| Después de seleccionar | `oferta_seleccionada` | `{...json...}` | ✅ Sí |

---

## ✅ Checklist Final

- [ ] TEST 1: Flujo completo funciona
- [ ] TEST 2: Persistencia confirmada
- [ ] TEST 3: CUPS vacío bloquea
- [ ] TEST 4: CUPS raro permite con warning
- [ ] TEST 5: Sin oferta = 400
- [ ] TEST 6: Errores manejados correctamente
- [ ] TEST 7: Backend valida CUPS

---

## 🚀 Comandos Útiles

### Ver estado de facturas
```bash
sqlite3 local.db "SELECT id, filename, estado_factura, cups, selected_offer_json IS NOT NULL as has_offer FROM facturas;"
```

### Resetear BD para testing
```bash
python scripts/reset_local_db.py
```

### Ver logs del backend
El backend debe correr con `--reload` y mostrar logs en tiempo real.

### Verificar endpoints
```bash
curl http://localhost:8000/
# Debe devolver: {"status":"ok","service":"RapidEnergy API","version":"1.0.0"}
```

---

**Última actualización:** 2026-01-09  
**Responsable:** Senior Full-Stack Engineer
