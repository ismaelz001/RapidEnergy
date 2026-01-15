# 📝 LISTA DE ARCHIVOS MODIFICADOS - MVP ENERGY

## BACKEND (Python)

### Modificados
1. `app/db/models.py`
   - Añadido campo `selected_offer_json` (TEXT) en modelo Factura

2. `app/routes/webhook.py`
   - Modelo Pydantic `OfferSelection` para validación
   - Validación CUPS obligatoria en `validate_factura_completitud()`
   - Endpoint POST `/webhook/facturas/{id}/seleccion`
   - Endpoint GET `/webhook/facturas/{id}/presupuesto.pdf`

3. `requirements.txt`
   - Añadido `reportlab` para generación de PDFs

### Nuevos
4. `migration_offer_selection.sql`
   - Script SQL de migración para bd PostgreSQL

5. `scripts/apply_migration_offer.py`
   - Script Python para aplicar migración en SQLite de forma segura

---

## FRONTEND (JavaScript/React)

### Modificados
6. `lib/apiClient.js`
   - Función `selectOffer(facturaId, offer)` - POST selección
   - Función `downloadPresupuestoPDF(facturaId)` - GET PDF blob

7. `app/wizard/[id]/step-3-comparar/page.jsx`
   - `handleGeneratePresupuesto` ahora es async
   - Flujo real: persistir → descargar PDF → éxito
   - Modal solo se muestra si todo OK
   - Mensaje corregido (sin "email")

8. `app/wizard/[id]/step-2-validar/page.jsx`
   - CUPS añadido a `requiredFields`
   - Campo CUPS marcado como obligatorio (*)
   - Validación: error si vacío, warning si formato raro

---

## DOCUMENTACIÓN

### Reescritos
9. `README.md`
   - Documentación completa de setup local vs producción
   - Variables de entorno
   - Endpoints documentados
   - Flujo MVP
   - Reglas CUPS

### Nuevos
10. `MVP_DELIVERABLES.md`
    - Resumen de todos los entregables
    - Archivos modificados
    - Casos de prueba
    - Comandos deployment

11. `CHECKLIST_PRUEBAS_MVP.md`
    - 7 escenarios de prueba detallados
    - Comandos útiles
    - Checklist final

12. `RESUMEN_FINAL_MVP.md`
    - Resumen ejecutivo completo
    - Estado del MVP
    - Diferencias antes/después
    - Conclusiones

13. `LISTA_ARCHIVOS.md`
    - Este archivo

---

## RESUMEN ESTADÍSTICAS

- **Archivos modificados:** 8
- **Archivos nuevos:** 6
- **Total archivos tocados:** 14
- **Líneas backend añadidas:** ~250
- **Líneas frontend modificadas:** ~60
- **Líneas documentación:** ~800

---

## GIT COMMIT SUGERIDO

```bash
git add .
git commit -m "feat: MVP Energy cerrado - Persistencia + PDF real + CUPS obligatorio

ENTREGABLE 1: Persistencia oferta seleccionada
- Campo selected_offer_json en Factura
- Endpoint POST /facturas/{id}/seleccion
- Migración aplicada

ENTREGABLE 2: Generación PDF real
- Endpoint GET /facturas/{id}/presupuesto.pdf
- PDF profesional con ReportLab
- Sin comisión, solo datos cliente

ENTREGABLE 3: Conectar Step 3
- API client con selectOffer y downloadPresupuestoPDF
- Flujo async real en frontend
- Modal de éxito solo si persiste + PDF OK

REGLA CUPS: Obligatorio no vacío
- Validación backend y frontend
- Formato flexible (warning solo)
- Bloquea si vacío

INFRA:
- Documentación completa README
- Scripts migración seguros
- Checklist pruebas detallado"
```

---

## ARCHIVOS QUE NO SE TOCAN

❌ **NO modificar:**
- `app/services/ocr.py` (OCR intacto según especificación)
- `app/routes/clientes.py` (CRM intacto)
- Componentes UI (`Button.jsx`, `Input.jsx`, etc.)
- Step 1 del wizard (upload intacto)
- Tests existentes

✅ **Verificar antes de commit:**
- `local.db` está en `.gitignore` ✓
- `google_creds.json` está en `.gitignore` ✓
- `.env` está en `.gitignore` ✓

---

Fecha: 2026-01-09  
Responsable: Senior Full-Stack Engineer
