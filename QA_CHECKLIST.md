# QA CHECKLIST & TEST PLAN

## 1. Verificación de Persistencia (Code Review)

### Campos extraídos y guardados en `Factura` (app/routes/webhook.py):
- **Identificación:** `filename`, `cups`, `file_hash`, `numero_factura`.
- **Fechas:** `fecha` (fecha factura), `fecha_inicio`, `fecha_fin`.
- **Económicos:** `importe` (total calculado/OCR), `total_factura`, `impuesto_electrico`, `alquiler_contador`, `iva`.
- **Energía:** `potencia_p1_kw`, `potencia_p2_kw`, `consumo_kwh` (total), `consumo_p1_kwh`...`p6`.
- **Flags:** `bono_social`, `servicios_vinculados`.
- **Debug:** `raw_data`.

### Campos actualizados en `Cliente` (si existen en OCR y son NULL en BD):
- `nombre`, `dni`, `direccion`, `telefono`, `email`.

**Estado:** ✅ IMPLEMENTADO CORRECTAMENTE.

---

## 2. Plan de Pruebas Manuales (Curl)

### Caso A: Subir PDF Nuevo (Happy Path)
```bash
# Debería devolver HTTP 200 y JSON con "message": "Factura procesada..."
curl -X POST "http://localhost:8000/webhook/upload" \
  -F "file=@/path/to/factura_nueva.pdf"
```

### Caso B: Subir MISMO PDF (Duplicate by Hash)
```bash
# Debería devolver JSON con "duplicate": true, "reason": "hash"
curl -X POST "http://localhost:8000/webhook/upload" \
  -F "file=@/path/to/factura_nueva.pdf"
```

### Caso C: Subir PDF distinto (mismo contenido semántico)
*Nota: Para probar esto, copia factura_nueva.pdf a factura_copia.pdf y edita un byte o metadalo si quieres cambiar hash, pero manteniendo texto OCR. O usa dos facturas reales del mismo mes.*
```bash
# Debería devolver JSON con "duplicate": true, "reason": "numero_factura" (si el OCR lee el número)
curl -X POST "http://localhost:8000/webhook/upload" \
  -F "file=@/path/to/factura_mismo_periodo.pdf"
```

### Caso E: Completado de Cliente
1. Crea un cliente dummy en BD con CUPS "ES0021000000000000AA" y nombre NULL.
2. Sube una factura que tenga ese CUPS y un nombre titular claro.
3. Consulta el cliente:
```bash
# El nombre debería haberse actualizado
curl "http://localhost:8000/clientes?cups=ES0021000000000000AA" 
```

---

## 3. Checklist de Resultados Esperados

- [ ] **Hash Dedupe:** Respuesta incluye `existing_factura` con ID y URL correctas.
- [ ] **Semantic Dedupe:** Si el hash cambia pero CUPS+Numero coinciden, detecta duplicado.
- [ ] **Fechas:** Tabla `facturas` tiene columnas `fecha_inicio` y `fecha_fin` rellenas (no NULL).
- [ ] **Edge Case:** Si OCR falla totalmente (img borrosa), devuelve error limpio o campos nulos, pero no 500.

## 4. Notas Importantes
- Asegúrate de haber ejecutado `migration_dedupe.sql` y `migration_dates.sql` en Neon antes de probar.
- Si el OCR no detecta el número de factura (regex compleja), el "Caso C" podría fallar (crear duplicado). Revisar `raw_data` si ocurre.
