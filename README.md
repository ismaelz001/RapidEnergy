# Energia CRM Frontend (MVP)

Frontend en Next.js 14 para el MVP del CRM de automatización de facturas energéticas.

## Stack

- Next.js 14 (App Router)
- React 18
- TailwindCSS
- Consumo de API externa (FastAPI) vía `NEXT_PUBLIC_API_URL`

## Rutas principales

- `/`              → Landing mínima
- `/login`         → Placeholder de login
- `/dashboard`     → Panel con KPIs (placeholders)
- `/facturas/upload` → Subida de factura + llamada a `/webhook/upload`
- `/facturas`      → Tabla de facturas (consume `/facturas` en FastAPI)

## Configuración

1. Copia el archivo de entorno:

   ```bash
   cp .env.local.example .env.local
   ```

2. Ajusta `NEXT_PUBLIC_API_URL` a la URL de tu backend FastAPI (por defecto `http://localhost:8000`).

3. Instala dependencias:

   ```bash
   npm install
   ```

4. Ejecuta en desarrollo:

   ```bash
   npm run dev
   ```

La app estará en `http://localhost:3000`.
