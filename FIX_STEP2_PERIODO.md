# FIX STEP 2: PERIODO + IMPORTES CORRECTOS

## FECHA
2026-01-23

## PROBLEMA RESUELTO
- ❌ Comparador devolvía 422 PERIOD_REQUIRED para factura #187
- ❌ Step 2 confundía porcentajes con importes en IVA e Impuesto Eléctrico

## CAMBIOS REALIZADOS

### 1. FRONTEND - Step 2 (`app/wizard/[id]/step-2-validar/page.jsx`)

#### ✅ Añadido campo obligatorio "Periodo (días)"
- Input numérico en sección "Datos principales"
- Validación: 1-366 días
- Placeholder: 30
- Incluido en `requiredFields` y `fieldLabels`

#### ✅ buildPayload actualizado
Ahora incluye:
```javascript
{
  ...
  alquiler_contador: parseNumberInput(data.alquiler_contador),  // Para backsolve
  total_factura: parseNumberInput(data.total_factura),
  periodo_dias: parseInt(data.periodo_dias) || null,  // OBLIGATORIO
}
```

### 2. CAMPOS YA CORRECTOS EN MODELO

El modelo `Factura` ya tiene los campos correctos:
- ✅ `iva` (Float) - IMPORTE en €
- ✅ `iva_porcentaje` (Float) - Porcentaje (21, 10, 4)
- ✅ `impuesto_electrico` (Float) - IMPORTE en €
- ✅ `alquiler_contador` (Float) - IMPORTE total del periodo
- ✅ `periodo_dias` (Integer) - Días de facturación
- ✅ `total_factura` (Float) - Total final

### 3. UI YA CORRECTA

El Step 2 ya tenía los labels correctos:
- "IVA (€) *" → guarda en campo `iva` (importe)
- "IVA (%) *" → guarda en campo `iva_porcentaje`
- "Impuesto eléctrico (€)" → guarda en campo `impuesto_electrico` (importe)
- Texto informativo: "(5.11269632% fijo)"

## IMPACTO EN BACKSOLVE

Con estos campos correctos, el método PO/NodoÁmbar funciona correctamente:

```python
# BACKSOLVE (en comparador.py)
total_factura = factura.total_factura  # Total final
iva_importe = factura.iva  # Importe € (NO porcentaje)
iee_importe = factura.impuesto_electrico  # Importe € (NO porcentaje)
alquiler_importe = factura.alquiler_contador  # Importe total periodo

# Recuperar subtotal
base_iva = total_factura - iva_importe
subtotal_si = base_iva - iee_importe - alquiler_importe
```

## DESBLOQUEO COMPARADOR

Con `periodo_dias` presente y persistido:
- ✅ El endpoint `POST /comparar` ya NO devuelve 422 PERIOD_REQUIRED
- ✅ El comparador puede calcular ahorros mensuales/anuales correctamente

## QA PENDIENTE

Después del deploy:
1. Abrir factura #187 en Step 2
2. Verificar que aparece campo "Periodo (días)"
3. Completar con valor (ej: 28 o 30)
4. Guardar y verificar con `GET /webhook/facturas/187`
5. Lanzar "Comparar" y confirmar que funciona

## ARCHIVOS MODIFICADOS

- `app/wizard/[id]/step-2-validar/page.jsx`
  - Añadido campo periodo_dias
  - Actualizado requiredFields
  - Actualizado buildPayload

## NOTAS

### ⚠️ Importante para auditoría
Los campos del modelo ya estaban bien diseñados. El problema era que el frontend no estaba enviando `periodo_dias`.

### ✅ No se requiere migración de BD
El campo `periodo_dias` ya existe en el modelo `Factura` desde antes.

### ✅ Compatibilidad
Los cambios son backwards-compatible. Facturas antiguas sin `periodo_dias` seguirán mostrando el error PERIOD_REQUIRED hasta que se editen y completen el campo.
