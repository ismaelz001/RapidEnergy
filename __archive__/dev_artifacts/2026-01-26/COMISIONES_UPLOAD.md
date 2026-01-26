# ⭐ SISTEMA DE CARGA MASIVA DE COMISIONES

**Fecha**: 2026-01-20  
**Endpoint**: `POST /webhook/comisiones/upload`

---

## 📋 **FUNCIONALIDAD**

Permite subir comisiones masivamente desde archivos CSV o Excel.

### **Características**:
- ✅ Soporta CSV y Excel (.xlsx)
- ✅ **Cierre automático**: Al insertar nueva comisión, cierra automáticamente la anterior
- ✅ Versionado histórico completo (UPDATE vigente_hasta + INSERT nueva)
- ✅ Validación de tarifa_id (debe existir en DB)
- ✅ Validación de comision_eur > 0
- ✅ Logs detallados por fila
- ✅ Respuesta con errores específicos por fila

---

## 📁 **FORMATO DE ARCHIVO**

### **Columnas requeridas**:

| Columna | Tipo | Obligatorio | Formato | Ejemplo |
|---------|------|-------------|---------|---------|
| `tarifa_id` | INT | ✅ Sí | Número entero | 11 |
| `comision_eur` | FLOAT | ✅ Sí | > 0 | 50.00 |
| `vigente_desde` | DATE | ✅ Sí | YYYY-MM-DD | 2026-01-20 |
| `vigente_hasta` | DATE | ❌ No | YYYY-MM-DD o vacío | 2026-12-31 |

### **Ejemplo CSV**:
```csv
tarifa_id,comision_eur,vigente_desde,vigente_hasta
1,50.00,2026-01-01,2026-12-31
2,45.00,2026-01-01,
3,60.00,2026-01-15,2026-06-30
11,55.00,2026-01-20,
```

### **Ejemplo Excel** (.xlsx):
Mismo formato, primera fila = encabezados.

---

## 🚀 **USO**

### **Request**:

```bash
POST /webhook/comisiones/upload
Content-Type: multipart/form-data

Body:
- file: archivo.csv o archivo.xlsx
```

### **Response exitosa**:

```json
{
  "status": "ok",
  "importados": 4,
  "errores": [],
  "total_filas": 4
}
```

### **Response con errores parciales**:

```json
{
  "status": "ok",
  "importados": 3,
  "errores": [
    {
      "fila": 5,
      "motivo": "tarifa_id 999 no existe en la base de datos"
    }
  ],
  "total_filas": 4
}
```

### **Response con error total**:

```json
{
  "status": "warning",
  "importados": 0,
  "errores": [
    {
      "fila": 2,
      "motivo": "comision_eur debe ser > 0 (recibido: -10.0)"
    },
    {
      "fila": 3,
      "motivo": "vigente_desde inválida: 2026/01/01. Formato esperado: YYYY-MM-DD"
    }
  ],
  "total_filas": 2
}
```

---

## 🧪 **TEST LOCAL**

### **1. Con CURL**:

```bash
curl -X POST "http://localhost:8000/webhook/comisiones/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ejemplo_comisiones.csv"
```

### **2. Con Python**:

```python
import requests

url = "http://localhost:8000/webhook/comisiones/upload"
files = {"file": open("ejemplo_comisiones.csv", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

### **3. Con Postman**:

1. POST → `http://localhost:8000/webhook/comisiones/upload`
2. Body → form-data
3. Key: `file`, Type: File
4. Seleccionar archivo CSV/Excel
5. Send

---

## 📊 **VALIDACIONES**

### **Validación 1: Formato de archivo**
```
❌ archivo.pdf → Error 400: "Formato no soportado"
✅ archivo.csv → OK
✅ archivo.xlsx → OK
```

### **Validación 2: Columnas requeridas**
```
❌ Falta "tarifa_id" → Error 400: "Faltan columnas requeridas: ['tarifa_id']"
✅ Todas las columnas → OK
```

### **Validación 3: comision_eur > 0**
```
Fila 3: comision_eur = -10.00 → Error en fila 3
Fila 4: comision_eur = 0.00 → Error en fila 4
Fila 5: comision_eur = 50.00 → ✅ OK
```

### **Validación 4: tarifa_id existe**
```
Fila 2: tarifa_id = 999 (no existe) → Error en fila 2
Fila 3: tarifa_id = 11 (existe) → ✅ OK
```

### **Validación 5: Formato de fecha**
```
vigente_desde = "2026-01-20" → ✅ OK
vigente_desde = "2026/01/20" → ❌ Error
vigente_desde = "20-01-2026" → ❌ Error
vigente_hasta = "" (vacío) → ✅ OK (NULL)
```

---

## 🔍 **LOGS**

### **Estructura de logs**:

```
[COMISIONES] Inicio import - archivo: comisiones.csv, tamaño: 1024 bytes
[COMISIONES] Archivo leído: 1024 bytes
[COMISIONES] DataFrame creado: 4 filas, columnas: ['tarifa_id', 'comision_eur', 'vigente_desde', 'vigente_hasta']
[COMISIONES] Fila 2 OK - tarifa_id=1, comision=50.0€
[COMISIONES] Fila 3 OK - tarifa_id=2, comision=45.0€
[COMISIONES] Fila 4 ERROR: tarifa_id=999 no encontrada
[COMISIONES] Fila 5 OK - tarifa_id=11, comision=55.0€
[COMISIONES] Commit exitoso: 3 filas importadas
```

---

## 🗄️ **ESTRUCTURA DB**

### **Tabla: `comisiones_tarifa`**:

```sql
CREATE TABLE comisiones_tarifa (
    id SERIAL PRIMARY KEY,
    tarifa_id INTEGER NOT NULL REFERENCES tarifas(id),
    comision_eur DECIMAL(10,2) NOT NULL,
    vigente_desde DATE NOT NULL,
    vigente_hasta DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **Comportamiento**:
- ✅ **Solo INSERT**: Nunca se hace UPDATE ni DELETE
- ✅ **Versionado histórico**: Múltiples filas por tarifa_id con fechas diferentes
- ✅ **Vigencia**: Se puede consultar qué comisión aplica en una fecha específica

### **Ejemplo de consulta vigente**:

```sql
SELECT * FROM comisiones_tarifa
WHERE tarifa_id = 11
  AND vigente_desde <= CURRENT_DATE
  AND (vigente_hasta IS NULL OR vigente_hasta >= CURRENT_DATE)
ORDER BY vigente_desde DESC
LIMIT 1;
```

---

## 📝 **ENDPOINT AUXILIAR**

### **GET /webhook/comisiones/**

Lista las comisiones vigentes (debugging).

**Response**:
```json
{
  "status": "ok",
  "count": 3,
  "comisiones": [
    {
      "id": 1,
      "tarifa_id": 11,
      "provider": "Iberdrola",
      "plan_name": "Plan Solar",
      "comision_eur": 55.0,
      "vigente_desde": "2026-01-20",
      "vigente_hasta": null
    }
  ]
}
```

---

## ⚠️ **CASOS EDGE**

### **1. Archivo vacío**:
```
Error 400: "El archivo está vacío"
```

### **2. Archivo corrupto**:
```
Error 400: "Error al parsear archivo: ..."
```

### **3. Tipos incorrectos**:
```
tarifa_id = "abc" → Error en fila: "Error de conversión de tipos: invalid literal for int()"
```

### **4. Duplicados en archivo**:
```
✅ Permitido - Se insertan ambos (versionado histórico)
```

### **5. Comisión ya existe en DB**:
```
✅ Permitido - Se inserta nueva versión (versionado)
```

---

## 🚀 **DEPLOY**

### **Dependencias necesarias**:

Agregar a `requirements.txt`:
```
pandas==2.1.0
openpyxl==3.1.2  # Para soporte Excel
```

### **Instalar**:
```bash
pip install pandas openpyxl
```

### **Commit**:
```bash
git add app/routes/comisiones.py app/main.py ejemplo_comisiones.csv
git commit -m "FEATURE: Carga masiva de comisiones desde CSV/Excel"
git push origin main
```

---

## ✅ **CHECKLIST FINAL**

- [x] Endpoint `/webhook/comisiones/upload` creado
- [x] Soporte CSV y Excel
- [x] Validación tarifa_id existe
- [x] Validación comision_eur > 0
- [x] Versionado histórico (solo INSERT)
- [x] Logs detallados
- [x] Response con errores por fila
- [x] Endpoint GET auxiliar creado
- [x] Archivo de ejemplo generado
- [x] Documentación completa
- [ ] Dependencias pandas/openpyxl instaladas
- [ ] Test E2E con archivo real

---

**Status**: ✅ **READY TO TEST**  
**Implementado por**: Senior Backend Engineer  
**Fecha**: 2026-01-20
