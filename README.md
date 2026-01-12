# RapidEnergy Backend (FastAPI + Neon + Render)

Backend oficial del MVP RapidEnergy, una plataforma para automatizar el análisis de facturas energéticas, extraer datos mediante OCR y preparar información para estudios tarifarios. Backend desplegado en Render, conectado a Neon PostgreSQL y consumido por el frontend en Vercel.

## Arquitectura

[Vercel - Frontend Next.js] → (HTTPS) → [Render - Backend FastAPI] → (PostgreSQL) → [Neon - Database]

## Stack Tecnológico

- Python 3.10+
- FastAPI
- Uvicorn
- SQLAlchemy
- Neon PostgreSQL (Producción)
- SQLite (Desarrollo Local)
- Render
- pytesseract / Pillow / pdf2image
- python-dotenv
- reportlab (Generación de PDFs)

## Estructura del Proyecto

```
MecaEnergy/
├── app/
│   ├── main.py
│   ├── routes/
│   │   ├── webhook.py
│   │   └── clientes.py
│   ├── db/
│   │   ├── models.py
│   │   └── conn.py
│   └── services/
│       ├── ocr.py
│       └── comparador.py
├── scripts/
│   └── reset_local_db.py
├── requirements.txt
├── render.yaml
└── README.md
```

## Configuración

### Variables de entorno necesarias

#### Modo LOCAL (desarrollo con SQLite)
Para desarrollo local usando SQLite, NO definir `DATABASE_URL`. El sistema usará automáticamente `local.db`.

```bash
# .env (local)
# DATABASE_URL no definido = SQLite automático
GOOGLE_APPLICATION_CREDENTIALS=./google_creds.json
TEST_MODE=true
```

#### Modo PRODUCCIÓN (Postgres en Neon)
Para producción con PostgreSQL (Neon/Render):

```bash
# .env (producción) o Render Environment Variables
DATABASE_URL="postgresql://<user>:<password>@<host>.neon.tech/<db>?sslmode=require&channel_binding=require"
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google_creds.json
```

### Instalación local

```bash
pip install -r requirements.txt
```

### Ejecutar en local

```bash
uvicorn app.main:app --reload
```

Backend disponible en: http://localhost:8000

### Base de datos local

El proyecto usa **SQLite** por defecto en desarrollo local (`local.db`). Este archivo está en `.gitignore` y NUNCA debe subirse a GitHub.

#### Resetear base de datos local

```bash
python scripts/reset_local_db.py
```

⚠️ **IMPORTANTE**: Este script tiene protección anti-producción. Solo permite resetear si detecta SQLite o localhost. Si intentas ejecutarlo con `DATABASE_URL` apuntando a Neon/Render, se bloqueará.

## Deploy en Render

1. Subir repo a GitHub  
2. Render → New Web Service → seleccionar repo  

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Variables de entorno en Render

```
DATABASE_URL=postgresql://...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/secret/file
```

Render generará una URL pública del tipo:

```
https://rapidenergy.onrender.com
```

Usar esa URL en el frontend como `NEXT_PUBLIC_API_URL`.

## Endpoints principales

### Facturas

- **POST** `/webhook/upload` - Subir factura con OCR
- **GET** `/webhook/facturas` - Listar facturas
- **GET** `/webhook/facturas/{id}` - Obtener factura por ID
- **PUT** `/webhook/facturas/{id}` - Actualizar factura
- **POST** `/webhook/comparar/facturas/{id}` - Comparar ofertas

### Presupuestos (MVP)

- **POST** `/webhook/facturas/{id}/seleccion` - Guardar oferta seleccionada
- **GET** `/webhook/facturas/{id}/presupuesto.pdf` - Descargar PDF del presupuesto

### Clientes

- **GET** `/clientes` - Listar clientes
- **GET** `/clientes/{id}` - Obtener cliente por ID
- **PUT** `/clientes/{id}` - Actualizar cliente

## Flujo MVP completo

1. **Upload** → Subir factura PDF
2. **OCR** → Extracción automática de datos (CUPS, ATR, consumos, potencia)
3. **Validar** → Paso 2: Completar/corregir datos críticos
4. **Comparar** → Paso 3: Ver ofertas calculadas
5. **Seleccionar** → Elegir oferta y guardar persistentemente
6. **PDF** → Generar y descargar presupuesto real

## Reglas CUPS

- **CUPS es OBLIGATORIO** (no puede estar vacío para pasar a comparación)
- **Formato flexible** (permite formatos no estándar con warning, pero no bloquea)
- Normalización automática: trim, uppercase, remove spaces/dashes/dots

## Próximas fases del backend

- Sistema de comisiones con cálculo real
- Envío automático de ofertas por email
- Integración con APIs de comercializadoras
- Webhooks para seguimiento de cambios

## Contacto

RapidEnergy — Backend MVP  
Arquitectura FastAPI + Neon + Render.
