# AUDITORÍA COMPLETA OCR Y PERSISTENCIA

## 1️⃣ AUDITORÍA OCR (`app/services/ocr.py`)

### Detección campos básicos
| Campo | PDF Digital (pypdf) | Imagen (Vision) | Estado |
| :--- | :---: | :---: | :--- |
| **Titular** | ⚠️ Fallaba (corregido) | ✅ OK | **FIXED** (Heurística prox. DNI habilitada para ambos) |
| **DNI/NIF** | ✅ OK | ✅ OK | **OK** |
| **Dirección** | ⚠️ Fallaba tildes | ✅ OK | **FIXED** (Regex ampliada a `direcci[oó]n`) |
| **Teléfono** | ✅ OK | ✅ OK | **OK** |
| **CUPS** | ✅ OK | ✅ OK | **OK** |

### Detección campos energéticos (Factura)
| Campo | Regex / Heurística | Estado |
| :--- | :--- | :--- |
| **Fechas (factura, inicio, fin)** | `fecha` (OK), `rango` (OK) | **OK** (Persistencia faltaba) |
| **Potencia P1 / P2** | Regex "P1/Punta", "P2/Valle" | **OK** |
| **Consumo P1-P6** | Regex iterativa `P{n}` | **OK** |
| **Importe Total** | Regex múltiple (fallback MAX) | **OK** |
| **Impuestos/Conceptos** | Regex específica (Bono, Alquiler, IVA) | **OK** |

## 2️⃣ AUDITORÍA DE PERSISTENCIA (`app/routes/webhook.py`)

**Problema Detectado:**
El OCR extraía correctamente **20+ campos** que el webhook **ignoraba** al instanciar `Factura`.

**Campos que NO se guardaban (Antes):**
- Potencias (P1, P2)
- Consumos desglosados (P1..P6)
- Fechas de inicio/fin consumo
- Conceptos (Bono social, Alquiler, Impuestos)

**Corrección Aplicada:**
Se ha actualizado `upload_factura` para mapear explícitamente TODOS estos campos del dict `ocr_data` al modelo `Factura`.

## 3️⃣ COBERTURA CLIENTE

**Lógica Anterior:**
- Si el cliente existía por CUPS → **IGNORABAMOS** los datos del OCR.
- Resultado: Clientes antiguos se quedaban con datos incompletos (NULL) aunque la nueva factura los trajera.

**Nueva Lógica (Implementada):**
- Si cliente existe (`cups` coincide):
  - Iteramos campos nulos en BD: `nombre`, `dni`, `direccion`, `telefono`, `email`.
  - Si en BD es `NULL` y en OCR existe dato → **ACTUALIZAMOS**.
- **Seguridad:** NO sobrescribimos datos existentes (si BD tiene teléfono, respetamos el de BD).

## 4️⃣ CAMBIOS REALIZADOS (Checklist)

### A) Modelo (`app/db/models.py`)
- [x] Añadidas columnas `fecha_inicio` y `fecha_fin` a tabla `Factura`.

### B) Webhook (`app/routes/webhook.py`)
- [x] Mapeo masivo de campos OCR → `Factura` (potencias, consumos, impuestos).
- [x] Mapeo de fechas inicio/fin → `Factura`.
- [x] Lógica de actualización de datos de Cliente (rellenado de huecos).

### C) OCR (`app/services/ocr.py`)
- [x] Ajuste Regex Dirección (`direcci[oó]n`).
- [x] Habilitado escaneo heurístico de titular para PDFs digitales (antes solo img).

## 5️⃣ CHECKLIST POST-FIX

1.  **Subir PDF nuevo con cliente nuevo**: Verificar que se crea Cliente con Nombre+DNI+Dirección.
2.  **Subir PDF de cliente existente incompleto**: Verificar que se rellena su Dirección/Nombre si faltaba.
3.  **Verificar Tabla Facturas**: Deben aparecer rellenas las columnas `potencia_p1_kw`, `consumo_p1_kwh`, `fecha_inicio`, `fecha_fin`, etc.
4.  **Comparador**: Al tener estos datos, el comparador ya no debería fallar por "datos faltantes".
