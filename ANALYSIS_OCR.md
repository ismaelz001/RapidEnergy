### RESULTADO

#### A) Fallos detectados
- [x] **Persistencia incompleta Factura**: Se extraían casi 20 campos (potencias, consumos, impuestos) que se ignoraban al crear el objeto `Factura` en BD. (Archivo: `app/routes/webhook.py` líneas 132-140).
- [x] **Actualización Cliente**: Si el cliente ya existía (por CUPS), NO se actualizaban sus datos personales aunque vinieran nulos en BD y llenos en el OCR. (Archivo: `app/routes/webhook.py` línea 106).
- [x] **Regex Dirección**: La regex `direccion` fallaba con "Dirección" (con tilde) en la mayoría de facturas PDF. (Archivo: `app/services/ocr.py` línea 338).
- [x] **Detección Titular PDF**: La heurística de buscar el nombre cerca del DNI estaba restringida solo a imágenes, fallando en PDFs nativos (`pypdf`) donde el layout se conserva. (Archivo: `app/services/ocr.py` línea 292).
- [ ] **Periodo Consumo**: Se detectan fecha inicio/fin pero NO existen columnas en la tabla `Factura` para guardarlas (`fecha` sí, pero no el rango/intervalo).

#### B) Tabla resumen de cobertura (Estado PRE-FIX)
| Campo | OCR | Parse | Persistencia | OK / FALLA |
| :--- | :---: | :---: | :---: | :--- |
| **Cliente: Nombre** | Sí | Sí (mejorable) | **NO** (si ya existe) | **FALLA** |
| **Cliente: Dirección** | Sí | **No** (si lleva tilde) | **NO** (si ya existe) | **FALLA** |
| **Cliente: DNI/Telf** | Sí | Sí | **NO** (si ya existe) | **FALLA** |
| **Factura: Fechas** | Sí | Sí | **Parcial** (falta rango) | **FALLA** |
| **Potencia P1/P2** | Sí | Sí | **No** | **FALLA** |
| **Consumos P1-P6** | Sí | Sí | **No** | **FALLA** |
| **Importe Total** | Sí | Sí | Sí | **OK** |
| **Impuestos/Alquiler**| Sí | Sí | **No** | **FALLA** |

#### C) Cambios mínimos necesarios (REALIZADOS)
1.  **`app/services/ocr.py`**:
    *   Corrección regex dirección (`direcci[oó]n`).
    *   Habilitada búsqueda heurística de Titular (cerca de DNI) para PDFs digitales, no solo imágenes.
2.  **`app/routes/webhook.py`**:
    *   En `upload_factura`, añadido mapeo masivo de campos (`potencia_p*`, `consumo_p*`, `impuestos`, `bono_social`) al crear `Factura`.
    *   Añadida lógica de actualización (`if not cliente.campo and ocr.campo`) para completar datos de Clientes existentes.

#### D) Checklist post-fix
- [x] Subir PDF real → Cliente se crea o actualiza con todos los datos (Dirección, Nombre).
- [x] Subir imagen real → Factura guarda consumos por periodo y potencias.
- [x] Rellenado manual solo necesario si el OCR falla totalmente o el dato no existe.
