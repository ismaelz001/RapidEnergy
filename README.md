# RapidEnergy Backend (FastAPI + Neon + Render)

Backend oficial del MVP RapidEnergy, una plataforma para automatizar el análisis de facturas energéticas, extraer datos mediante OCR y preparar información para estudios tarifarios. Backend desplegado en Render, conectado a Neon PostgreSQL y consumido por el frontend en Vercel.

## Arquitectura

[Vercel - Frontend Next.js] → (HTTPS) → [Render - Backend FastAPI] → (PostgreSQL) → [Neon - Database]

## Stack Tecnológico

- Python 3.10+
- FastAPI
- Uvicorn
- SQLAlchemy
- Neon PostgreSQL
- Render
- pytesseract / Pillow / pdf2image
- python-dotenv

## Estructura del Proyecto

MecaEnergy/
├── app/
│   ├── main.py
│   ├── routes/
│   │   └── webhook.py
│   ├── db/
│   │   └── conn.py
│   └── services/
├── requirements.txt
├── render.yaml
└── README.md

## Configuración

### Variables de entorno

Crear archivo `.env` en local (no subir a GitHub):

DATABASE_URL="postgresql://<user>:<password>@<host>.neon.tech/<db>?sslmode=require&channel_binding=require"

En Render: Dashboard → Environment → Add Variable

### Instalación local

pip install -r requirements.txt

### Ejecutar en local

uvicorn app.main:app --reload

Backend disponible en: http://localhost:8000

## Deploy en Render

1. Subir repo a GitHub  
2. Render → New Web Service → seleccionar repo  

### Build Command

pip install -r requirements.txt

### Start Command

uvicorn app.main:app --host 0.0.0.0 --port $PORT

### Variables de entorno

DATABASE_URL=postgresql://...

Render generará una URL pública del tipo:

https://rapidenergy.onrender.com

Usar esa URL en el frontend como NEXT_PUBLIC_API_URL.

## Endpoints actuales (MVP)

### GET `/`

{
  "status": "ok",
  "service": "RapidEnergy API",
  "version": "1.0.0"
}

### POST `/webhook/upload`

Subida de factura en multipart/form-data.

Ejemplo de respuesta:

{
  "filename": "factura.pdf",
  "message": "Factura recibida correctamente (MVP)"
}

## Próximas fases del backend

- OCR avanzado
- Parsing por proveedor
- Modelo Factura en SQLAlchemy
- CRUD en Neon
- Endpoint /facturas
- Algoritmo de recomendación tarifaria
- Sistema de comisiones
- Envío automático de ofertas

## Contacto

RapidEnergy — Backend MVP  
Arquitectura FastAPI + Neon + Render.
