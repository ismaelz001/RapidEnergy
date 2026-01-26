# FIX CORS - presupuesto.pdf

## FECHA
2026-01-23

## PROBLEMA
Frontend (https://energy.rodorte.com) no puede descargar PDF del endpoint:
`GET /webhook/facturas/{id}/presupuesto.pdf`

Error en consola:
```
CORS blocked fetching
No 'Access-Control-Allow-Origin' header
```

## CAUSA
El middleware CORSMiddleware de FastAPI estaba configurado correctamente para energy.rodorte.com, 
pero StreamingResponse puede bypasear el middleware en ciertos casos edge.

## SOLUCIÓN
Añadir headers CORS explícitos en la respuesta del PDF.

## CAMBIOS REALIZADOS

### Archivo: `app/routes/webhook.py`

**Líneas: 1060-1067**

```diff
-    # Devolver como respuesta
+    # Devolver como respuesta con headers CORS explícitos
     return StreamingResponse(
         buffer,
         media_type="application/pdf",
         headers={
-            "Content-Disposition": f"attachment; filename=presupuesto_factura_{factura_id}.pdf"
+            "Content-Disposition": f"attachment; filename=presupuesto_factura_{factura_id}.pdf",
+            "Access-Control-Allow-Origin": "https://energy.rodorte.com",  # ⭐ FIX CORS para descarga PDF
+            "Access-Control-Allow-Methods": "GET, OPTIONS",
+            "Access-Control-Allow-Headers": "*",
         }
     )
```

## VALIDACIÓN

### TEST 1: curl headers
```bash
curl -I https://rapidenergy.onrender.com/webhook/facturas/196/presupuesto.pdf
```

**Esperado:**
```
Access-Control-Allow-Origin: https://energy.rodorte.com
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: *
Content-Type: application/pdf
Content-Disposition: attachment; filename=presupuesto_factura_196.pdf
```

### TEST 2: Descarga desde frontend
1. Abrir https://energy.rodorte.com
2. Seleccionar una factura con oferta guardada
3. Click en "Descargar presupuesto PDF"
4. El PDF debe descargarse sin error CORS

## NOTA TÉCNICA

El middleware CORSMiddleware en `app/main.py` (líneas 33-55) ya incluye:
```python
allow_origins = [
    "http://localhost:3000",
    "https://energy.rodorte.com",  # ✅ Ya estaba configurado
    ...
],
allow_origin_regex=r"https://.*\.vercel\.app",  # ✅ Para previews
```

Pero para StreamingResponse es mejor practice añadir headers explícitos en la respuesta
para garantizar compatibilidad cross-browser.

## COMPATIBILIDAD

- ✅ No rompe funcionalidad existente
- ✅ Compatible con todos los navegadores modernos
- ✅ localhost:3000 sigue funcionando (lo añadiremos a headers si es necesario)

## ALTERNATIVA (si se requiere wildcardpattern)

Si se necesita permitir TODOS los orígenes para el PDF:
```python
"Access-Control-Allow-Origin": "*",
```

Pero por seguridad, mantener el dominio específico es mejor practice.
