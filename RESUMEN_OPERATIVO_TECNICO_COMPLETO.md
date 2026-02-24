# RESUMEN OPERATIVO Y TÉCNICO - CRM/SaaS ASESORÍA ENERGÉTICA

**Fecha de generación:** 23 de febrero de 2026  
**Producto:** RapidEnergy / MecaEnergy CRM  
**Versión actual:** MVP Operativo  
**Propósito:** Documento base completo para continuación de desarrollo sin preguntas

---

## 1️⃣ OBJETIVO DEL PRODUCTO

### Problema que resuelve
- **Pain Point Principal:** Asesorías energéticas pierden 3-5 horas/semana introduciendo datos manualmente en Zoho/Excel desde facturas PDF, calculando ahorros a mano, y generando presupuestos en Word
- **Solución:** Sistema integral que automatiza desde la subida de factura hasta la generación del estudio comparativo en PDF, con gestión de pipeline comercial incluida

### Para quién
- **CEO/Director de Asesoría:** Panel de gestión con KPIs, control de comisiones, seguimiento de pipeline comercial
- **Comerciales/Asesores:** Wizard simplificado 3 pasos (subir factura → validar → comparar → enviar estudio)
- **Colaboradores externos:** Personas que traen clientes sin acceso al sistema pero que reciben comisión
- **Clientes finales:** Reciben PDF profesional con estudio comparativo tarifario transparente

### Flujo principal de negocio
```
LEAD → Subir Factura → OCR Extrae Datos → Asesor Valida → 
Comparar Tarifas → Seleccionar Mejor Oferta → Generar PDF → 
Cliente Acepta → Tramitar Contrato → Activar → 
COMISIÓN GENERADA → Revisión 10 Meses → Renovar/Baja
```

### Modelo de ingresos
- Comisión por activación de contrato energético
- Reparto configurable: Asesor / CEO / Colaborador externo
- Control de estados: Pendiente → Validada → Pagada → Anulada

---

## 2️⃣ ESTADO ACTUAL (LO QUE YA EXISTE)

### FRONTEND

**Stack:**
- Next.js 14.2.3 (App Router)
- React 18.3.1
- TailwindCSS 3.4.4
- Chart.js + react-chartjs-2 (gráficos)
- TypeScript configurado (tsconfig.json, next-env.d.ts)

**Rutas/Páginas principales:**
```
/                          → Redirect a /dashboard
/login                     → Pantalla de login (autenticación)
/dashboard                 → Panel principal con tabs (casos, tarifas, comisiones)
/clientes                  → Listado de clientes
/facturas                  → Gestión de facturas procesadas
/wizard/[id]/step-1-factura → Subir factura PDF
/wizard/[id]/step-2-validar → Validación comercial (STEP 2)
/wizard/[id]/step-3-comparar → Comparación de ofertas
/gestion                   → Panel CEO/Gestión (NUEVO)
  /gestion/resumen         → Dashboard ejecutivo con KPIs
  /gestion/comisiones      → Configuración + historial comisiones
  /gestion/colaboradores   → Gestión de asesores + colaboradores
  /gestion/pagos           → Control de comisiones pendientes/pagadas
  /gestion/casos           → Gestión de pipeline comercial
  /gestion/casos/[id]      → Detalle de caso individual
  /gestion/casos/nuevo     → Crear caso manual
```

**Componentes clave:**
- `app/layout.js` → Header horizontal con navegación (Dashboard | Clientes | Facturas | Gestión | + Nueva Factura)
- `app/components/` → Componentes reutilizables (cards, tables, forms)
- `app/context/` → Contextos React (autenticación, estado global)
- `app/dashboard/page.jsx` → Tabs con casos/tarifas/comisiones
- `app/gestion/*` → Módulo completo de gestión CEO (parcialmente implementado)

**Diseño:**
- Paleta: Azul primario `#0073EC`, fondos dark, bordes sutiles
- Sistema de cards consistente
- Header horizontal espacioso (no sidebar)
- Responsive (mobile-friendly)

### BACKEND/API

**Stack:**
- FastAPI (Python 3.10+)
- Uvicorn (servidor ASGI)
- SQLAlchemy 2.0.37 (ORM)
- PostgreSQL (Neon en producción, SQLite en local)
- python-dotenv (variables de entorno)

**Estructura:**
```
app/
├── main.py                    → Punto de entrada FastAPI
├── auth.py                    → Autenticación JWT/usuario actual
├── exceptions.py              → Excepciones custom (DomainError)
├── db/
│   ├── conn.py                → Configuración SQLAlchemy, get_db()
│   ├── models.py              → Modelos principales (Factura, Cliente, User, etc.)
│   └── models_casos.py        → Modelos de gestión (Caso, HistorialCaso)
├── routes/
│   ├── webhook.py             → Endpoints de facturas (upload, comparar, selección)
│   ├── casos.py               → CRUD de casos comerciales
│   ├── clientes.py            → CRUD de clientes
│   ├── users.py               → Gestión de usuarios
│   ├── colaboradores.py       → Gestión de colaboradores externos
│   ├── comisiones.py          → Configuración de comisiones por tarifa (upload CSV)
│   ├── comisiones_generadas.py → Gestión de comisiones generadas
│   └── stats.py               → Estadísticas y KPIs (parcial)
├── services/
│   ├── ocr.py                 → Extracción de datos con Google Vision + GPT-4o
│   ├── comparador.py          → Motor de cálculo de comparativas tarifarias
│   ├── pdf_generator.py       → Generación de estudios en PDF (ReportLab)
│   └── validacion_comercial.py → STEP 2: Validación de ajustes comerciales
└── utils/
    └── cups.py                → Normalización y validación de CUPS
```

**Endpoints clave YA creados:**

**Facturas:**
- `POST /webhook/upload` → Subir factura con OCR automático
- `GET /webhook/facturas` → Listar facturas (filtros: estado, comercial, cliente)
- `GET /webhook/facturas/{id}` → Obtener factura por ID
- `PUT /webhook/facturas/{id}` → Actualizar factura (completar datos OCR)
- `PUT /webhook/facturas/{id}/validar` → STEP 2: Validación comercial
- `POST /webhook/comparar/facturas/{id}` → Ejecutar comparador de tarifas
- `POST /webhook/facturas/{id}/seleccion` → Guardar oferta seleccionada
- `GET /webhook/facturas/{id}/presupuesto.pdf` → Descargar PDF del presupuesto

**Casos (CRM):**
- `GET /api/casos` → Listar casos (filtros: estado, asesor, company)
- `POST /api/casos` → Crear caso manual
- `GET /api/casos/{id}` → Detalle de caso
- `PUT /api/casos/{id}` → Actualizar caso
- `PUT /api/casos/{id}/estado` → Cambiar estado comercial (con validación de transiciones)

**Clientes:**
- `GET /clientes` → Listar clientes
- `GET /clientes/{id}` → Detalle cliente
- `PUT /clientes/{id}` → Actualizar cliente

**Comisiones:**
- `POST /webhook/comisiones/upload` → Subir comisiones por CSV/Excel (versionado temporal)
- `GET /api/comisiones_generadas` → Listar comisiones generadas (filtros: estado, asesor)
- `PUT /api/comisiones_generadas/{id}` → Actualizar comisión (marcar como pagada)

**Colaboradores:**
- `GET /api/colaboradores` → Listar colaboradores
- `POST /api/colaboradores` → Crear colaborador
- `PUT /api/colaboradores/{id}` → Actualizar colaborador

**Auth (parcial, sin JWT completo implementado todavía):**
- `get_current_user()` → Dependency para obtener usuario autenticado
- Sistema de roles: dev, ceo, manager, comercial

### BASE DE DATOS

**ORM:** SQLAlchemy 2.0
**Producción:** Neon PostgreSQL (desplegado)
**Local:** SQLite (`local.db`)

**Tablas/Modelos actuales:**

**1. Companies (Multi-tenant)**
```python
companies:
  - id (PK)
  - name (unique)
  - nif
  - created_at
```

**2. Users (Sistema de usuarios)**
```python
users:
  - id (PK)
  - email (unique, index)
  - name
  - role (dev | ceo | manager | comercial)
  - company_id (FK → companies, nullable para dev)
  - is_active (boolean)
  - created_at
```

**3. Clientes (Leads/Contactos)**
```python
clientes:
  - id (PK)
  - nombre
  - email
  - telefono
  - dni
  - cups (unique, index)
  - direccion
  - provincia
  - estado (lead | seguimiento | oferta_enviada | contratado | descartado)
  - origen (factura_upload | manual | web)
  - company_id (FK → companies, index)
  - comercial_id (FK → users)
  - created_at
  - updated_at
  
  # Relaciones:
  - facturas (1:N)
  - casos (1:N)
```

**4. Facturas (Facturas procesadas)**
```python
facturas:
  - id (PK)
  - filename
  - cups
  - cliente_id (FK → clientes)
  
  # Datos extraídos por OCR
  - consumo_kwh (total)
  - consumo_p1_kwh, consumo_p2_kwh, consumo_p3_kwh (periodos 2.0TD)
  - consumo_p4_kwh, consumo_p5_kwh, consumo_p6_kwh (periodos 3.0TD)
  - potencia_p1_kw, potencia_p2_kw
  - importe
  - fecha, fecha_inicio, fecha_fin
  - periodo_dias (calculado)
  - numero_factura
  - atr (2.0TD | 3.0TD)
  
  # Condiciones especiales
  - bono_social (boolean)
  - servicios_vinculados (boolean)
  - alquiler_contador (float)
  
  # Impuestos
  - impuesto_electrico (float)
  - iva (float)
  - iva_porcentaje (float)
  - total_factura (float)
  
  # Desglose estructural (baseline)
  - coste_energia_actual (float) - E_actual
  - coste_potencia_actual (float) - P_actual
  
  # STEP 2: Validación Comercial
  - ajustes_comerciales_json (text) - JSON con ajustes
  - total_ajustado (float) - "Cifra Reina"
  - validado_step2 (boolean)
  
  # Auditoría OCR
  - raw_data (text) - JSON con datos crudos OCR
  - file_hash (unique, index) - Deduplicación
  
  # Estado y selección
  - estado_factura (pendiente_datos | lista_para_comparar | oferta_seleccionada)
  - selected_oferta_id (FK → ofertas_calculadas)
  - selected_at (datetime)
  - selected_by_user_id (FK → users)
  - selected_offer_json (text) - DEPRECATED, usar selected_oferta_id
  
  # Relaciones:
  - cliente (N:1)
  - comparativas (1:N)
```

**5. Comparativas (Auditoría de comparaciones)**
```python
comparativas:
  - id (PK)
  - factura_id (FK → facturas)
  - created_at
  - periodo_dias
  - current_total
  - inputs_json (text) - Inputs usados
  - offers_json (text) - DEPRECATED
  - status (ok | error)
  - error_json (text)
  
  # Relaciones:
  - factura (N:1)
  - ofertas (1:N → ofertas_calculadas)
```

**6. OfertaCalculada (Ofertas persistidas)**
```python
ofertas_calculadas:
  - id (PK)
  - comparativa_id (FK → comparativas)
  - tarifa_id (int, no FK, referencia lógica)
  - coste_estimado (float)
  - ahorro_mensual (float)
  - ahorro_anual (float)
  - detalle_json (text) - Desglose completo
  - comision_eur (float) - Comisión calculada
  - comision_source (tarifa | cliente | manual)
  - created_at
  
  # Relaciones:
  - comparativa (N:1)
```

**7. ComisionGenerada (Comisiones por activaciones)**
```python
comisiones_generadas:
  - id (PK)
  - company_id (FK → companies)
  - factura_id (FK → facturas, nullable)
  - cliente_id (FK → clientes)
  - asesor_id (FK → users, index)
  - oferta_id (FK → ofertas_calculadas)
  - tarifa_id (bigint)
  - caso_id (FK → casos, nullable, index)
  - comision_total_eur (numeric 12,2)
  - comision_source (manual | tarifa | cliente)
  - estado (pendiente | validada | pagada | anulada | retenida | decomision)
  - fecha_prevista_pago (date)
  - fecha_pago (date)
  - created_at
  - updated_at
  
  # Relaciones:
  - factura (N:1)
  - cliente (N:1)
  - asesor (N:1 → users)
  - caso (N:1)
  - repartos (1:N → repartos_comision)
```

**8. RepartoComision (Split de comisiones)**
```python
repartos_comision:
  - id (PK)
  - comision_id (FK → comisiones_generadas, index)
  - tipo_destinatario (asesor | ceo | colaborador)
  - user_id (FK → users, nullable)
  - colaborador_id (FK → colaboradores, nullable)
  - importe_eur (numeric 12,2)
  - porcentaje (numeric 6,3)
  - estado_pago (pendiente | pagado | cancelado)
  - fecha_pago (date)
  - notas (text)
  - created_at
  
  # Relaciones:
  - comision (N:1)
  - user (N:1, nullable)
  - colaborador (N:1, nullable)
```

**9. Colaborador (Colaboradores externos sin login)**
```python
colaboradores:
  - id (PK)
  - company_id (FK → companies, index)
  - nombre
  - telefono
  - email
  - notas
  - created_at
  
  # Relaciones:
  - company (N:1)
```

**10. Caso (Pipeline comercial)**
```python
casos:
  - id (PK)
  - company_id (FK → companies, index)
  - cliente_id (FK → clientes, index)
  - asesor_user_id (FK → users, nullable)
  - colaborador_id (FK → colaboradores, nullable)
  - factura_id (FK → facturas, nullable)
  - comparativa_id (FK → comparativas, nullable)
  - oferta_id (FK → ofertas_calculadas, nullable)
  - tarifa_id (bigint, nullable)
  - cups (index)
  - servicio (luz | gas | luz+gas)
  - nueva_compania_text (text) - Comercializadora nueva
  - antigua_compania_text (text) - Comercializadora anterior
  - tarifa_nombre_text (text)
  - canal (web | telefono | presencial)
  - ahorro_estimado_anual (numeric 12,2)
  - notas (text)
  - estado_comercial (ver estados abajo, index)
  - origen (manual | factura_upload | web)
  - fecha_contacto (datetime)
  - fecha_propuesta (datetime)
  - fecha_firma (datetime)
  - fecha_activacion (datetime) - ⭐ Trigger para generar comisión
  - fecha_baja (datetime)
  - created_at
  - updated_at
  
  # Relaciones:
  - company (N:1)
  - cliente (N:1)
  - asesor (N:1 → users)
  - colaborador (N:1)
  - factura (N:1)
  - comparativa (N:1)
  - oferta (N:1)
  - comisiones (1:N → comisiones_generadas)
  - historial (1:N → historial_caso)
```

**11. HistorialCaso (Timeline de eventos)**
```python
historial_caso:
  - id (PK)
  - caso_id (FK → casos, index)
  - tipo_evento (cambio_estado | nota | email_enviado | documento_subido)
  - descripcion (text)
  - estado_anterior (text, nullable)
  - estado_nuevo (text, nullable)
  - metadata_json (text, JSONB en Postgres)
  - user_id (FK → users, nullable)
  - created_at
  
  # Relaciones:
  - caso (N:1)
  - user (N:1)
```

**12. Tablas de Comisiones (configuración)**
```python
comisiones_tarifa:
  - id (PK)
  - tarifa_id (int)
  - comision_eur (float)
  - vigente_desde (date)
  - vigente_hasta (date, nullable)
  - created_at
  
comisiones_cliente:
  - id (PK)
  - cliente_id (FK → clientes)
  - tarifa_id (int)
  - comision_eur (float)
  - prioridad_sobre_tarifa (boolean, default true)
  - created_at
```

**Enums importantes (CHECK constraints en DB):**
```python
# Roles
dev | ceo | manager | comercial

# Estados de Cliente
lead | seguimiento | oferta_enviada | contratado | descartado

# Estados de Factura
pendiente_datos | lista_para_comparar | oferta_seleccionada

# Estados de Caso (pipeline comercial)
lead → contactado → en_estudio → propuesta_enviada → 
negociacion → contrato_enviado → pendiente_firma → 
firmado → validado → activo → baja | cancelado | perdido

# Estados de Comisión
pendiente | validada | pagada | anulada | retenida | decomision
```

**Relaciones principales:**
- User → Clientes (1:N, comercial asignado)
- Cliente → Facturas (1:N)
- Cliente → Casos (1:N)
- Factura → Comparativas (1:N)
- Comparativa → OfertasCalculadas (1:N)
- Factura → OfertaCalculada (N:1, selected_oferta_id)
- Caso → ComisionGenerada (1:N)
- ComisionGenerada → RepartoComision (1:N)

### OCR (EXTRACCIÓN DE DATOS)

**Proveedores:**
- **Google Cloud Vision API** (principal, imágenes)
- **GPT-4o Vision** (OpenAI, fallback/complemento)
- **pypdf** (texto directo si PDF tiene capa de texto)

**Pipeline:**
1. Usuario sube PDF
2. Sistema convierte PDF → Imagen (pdf2image)
3. Envía a Vision API → Extrae texto completo
4. `app/services/ocr.py` aplica patrones regex para cada campo
5. Genera `raw_data` JSON (auditoría) + campos estructurados
6. Persiste en tabla `facturas`

**Campos que extrae (2.0TD):**
- ✅ CUPS (con normalización)
- ✅ Consumos P1, P2, P3 (kWh)
- ✅ Potencias P1, P2 (kW)
- ✅ Fechas (inicio, fin) → Calcula periodo_dias
- ✅ Total factura
- ✅ IVA (% y €)
- ✅ Impuesto eléctrico
- ✅ Bono social (detección booleana)
- ✅ Alquiler contador
- ✅ ATR (2.0TD vs 3.0TD)
- ✅ Número de factura
- ⏳ Dirección (70% precisión, mejorando)
- ⏳ Localidad (en desarrollo)
- ⏳ Titular (en desarrollo)

**Validaciones automáticas:**
- Normalización CUPS (formato estándar)
- Detección ATR por potencia si no viene en PDF
- Validación rangos (consumo 0-5000 kWh)
- Deduplicación por `file_hash`
- ConceptShield (previene mezcla de conceptos)

**Precisión actual:** ~71% campos correctos (objetivo 96%)

**Limitaciones conocidas:**
- Tablas gráficas (no extrae bien de imágenes/gráficos)
- PDFs escaneados sin OCR previo
- Facturas HC Energía (formato complejo)
- Consumos P4-P6 (3.0TD, menos probados)

### COMPARADOR (MOTOR DE CÁLCULO)

**Archivo:** `app/services/comparador.py`

**Inputs obligatorios:**
- Consumos P1, P2, P3 (kWh)
- Potencias P1, P2 (kW)
- Período (días)
- Total factura (o `total_ajustado` si pasó STEP 2)
- ATR (2.0TD o 3.0TD)

**Proceso:**
1. Valida completitud de datos
2. Si `validado_step2=true`, usa `total_ajustado`, sino `total_factura`
3. Calcula coste actual reconstruido (energía + potencia)
4. Para cada tarifa competidora (~3-5 tarifas hardcodeadas):
   - Aplica precios energía P1, P2, P3
   - Aplica precios potencia P1, P2
   - Suma impuestos (IVA 21%, Impuesto Eléctrico 5.11%)
   - Normaliza a 360 días (ahorro anual)
5. Calcula comisión (consulta `comisiones_tarifa` con versionado temporal)
6. Persiste en `comparativas` + `ofertas_calculadas`
7. Ordena por mayor ahorro anual

**Outputs:**
- Comparativa (registro de auditoría)
- Lista de OfertasCalculadas con:
  - Proveedor
  - Plan
  - Coste estimado anual
  - Ahorro mensual/anual
  - Ahorro %
  - Desglose (energía, potencia, impuestos)
  - Comisión (€ + source)

**Fórmulas (reglas PO):**
- **P0:** Normalización a 30 días
- **P1:** Período obligatorio (error si falta)
- **Regla ATR:** Validación según tipo de suministro

**Motor de cálculo:**
```
COSTE POTENCIA = (P1_kW × P1_€/kW/día + P2_kW × P2_€/kW/día) × periodo_dias
COSTE ENERGÍA = (P1_kWh × P1_€/kWh + P2_kWh × P2_€/kWh + P3_kWh × P3_€/kWh)
SUBTOTAL = COSTE POTENCIA + COSTE ENERGÍA
IEE = SUBTOTAL × 0.0511269632
BASE IMPONIBLE = SUBTOTAL + IEE
IVA = BASE IMPONIBLE × 0.21
TOTAL = BASE IMPONIBLE + IVA
```

**Limitaciones:**
- Tarifas hardcodeadas (no API dinámica de precios)
- Solo 2.0TD probado a fondo (3.0TD experimental)
- No simula multi-período (solo extrapola período de factura)

### GENERACIÓN DE PDF (ESTUDIOS)

**Archivo:** `app/services/pdf_generator.py`
**Librería:** ReportLab 4.3.0

**Trigger:** `GET /webhook/facturas/{id}/presupuesto.pdf`

**Contenido del PDF:**
1. **Header:** Logo + datos empresa
2. **Tabla 1:** Desglose factura actual
   - Consumos P1, P2, P3
   - Potencias P1, P2
   - Período días
   - Total factura
3. **Sección Metodología** (solo si `validado_step2=true`):
   - Explica ajustes realizados (Bono Social, descuentos, servicios)
   - Muestra total original vs total ajustado
   - Notas explicativas por ajuste
4. **Tabla 2:** Estudio Comparativo
   - Tarifa actual vs oferta seleccionada
   - Ahorro mensual
   - Ahorro anual
   - Ahorro %
5. **Tabla 3:** Desglose de cálculos
   - Coste energía
   - Coste potencia
   - Impuestos
   - Total
6. **Footer:** Datos contacto proveedor, plazo activación

**Formato:**
- Streaming directo (no guarda en disco)
- Profesional (tablas, colores corporativos)
- Transparente (muestra fórmulas si STEP 2)

### GESTIÓN DE COLABORADORES

**Estado:** ✅ Implementado (CRUD completo)

**Tabla:** `colaboradores`
**Endpoints:**
- `GET /api/colaboradores` → Listar
- `POST /api/colaboradores` → Crear
- `PUT /api/colaboradores/{id}` → Actualizar
- `DELETE /api/colaboradores/{id}` → Eliminar (soft delete o hard)

**Multi-tenant:** Sí (por `company_id`)

**Uso:**
- Personas que traen clientes pero NO tienen acceso al sistema
- Pueden recibir % de comisión en `repartos_comision`
- Asociados a casos en `casos.colaborador_id`

### ESTADO DE DESPLIEGUE

**Frontend:**
- **Plataforma:** Vercel
- **Dominio:** DESCONOCIDO (verificar en dashboard Vercel)
- **Variables env:** `NEXT_PUBLIC_API_URL` (apunta a backend Render)
- **Build:** `npm run build` (Next.js)
- **Deploy:** Automático desde GitHub branch main

**Backend:**
- **Plataforma:** Render (Web Service)
- **URL:** `https://rapidenergy.onrender.com` (ejemplo, verificar)
- **Variables env:**
  - `DATABASE_URL` (Neon Postgres)
  - `GOOGLE_APPLICATION_CREDENTIALS` (path a JSON)
  - `OPENAI_API_KEY` (para GPT-4o Vision)
- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Deploy:** Automático desde GitHub branch main

**Base de datos:**
- **Plataforma:** Neon (PostgreSQL serverless)
- **Conexión:** `DATABASE_URL` con SSL require + channel_binding
- **Migraciones:** MANUAL (SQLAlchemy no usa Alembic todavía)
- **Backup:** DESCONOCIDO (verificar configuración Neon)

**Secrets/Credenciales:**
- Google Cloud Service Account JSON (Vision API)
- OpenAI API Key
- Database URL (Neon)
- Todos en `_secrets_stash/` (NO en git)

**Dominios:**
- Frontend: DESCONOCIDO (Vercel auto-genera, verificar custom domain)
- Backend: Render auto-genera URL `.onrender.com`

---

## 3️⃣ FLUJO DE TRABAJO ACTUAL (END-TO-END)

### FLUJO A: Crear caso manual (sin factura)

**Actor:** CEO o Asesor

1. Ir a `/gestion/casos/nuevo`
2. Rellenar formulario:
   - Seleccionar cliente existente o crear nuevo
   - CUPS (opcional)
   - Asesor asignado
   - Colaborador (si aplica)
   - Canal (web, teléfono, presencial)
   - Notas
3. `POST /api/casos` → Caso creado en estado `lead`
4. Se registra en `historial_caso` (tipo_evento: creacion)

**Pantalla:** `/gestion/casos/[id]`
**Módulo:** Backend `app/routes/casos.py`

### FLUJO B: Subir factura → OCR → validar → comparativa → PDF (COMPLETO)

**Actor:** Asesor o Cliente (si es autoservicio)

**Paso 1: Subir factura**
- Pantalla: `/wizard/new/step-1-factura`
- Usuario selecciona archivo PDF
- `POST /webhook/upload` → Sube factura
- Backend:
  1. Convierte PDF → Imagen
  2. Envía a Vision API
  3. Extrae texto completo
  4. `ocr.py` aplica patrones regex
  5. Genera `raw_data` JSON + campos estructurados
  6. Si CUPS nuevo → crea Cliente automáticamente (estado `lead`)
  7. Si CUPS existe → asigna factura a cliente existente
  8. Calcula `file_hash` para deduplicación
  9. Persiste en `facturas` con estado `pendiente_datos`
- Frontend:
  - Muestra campos extraídos
  - Permite corregir/completar datos
  - Si falta algún campo obligatorio → estado `pendiente_datos`
  - Si todo OK → estado `lista_para_comparar`
- `PUT /webhook/facturas/{id}` → Actualiza campos manualmente

**Paso 2: Validación comercial (STEP 2) - OPCIONAL**
- Pantalla: `/wizard/[id]/step-2-validar`
- Asesor identifica conceptos no comparables:
  - ☑️ Bono Social (descuento ~40%)
  - ☑️ Descuentos comerciales temporales
  - ☑️ Servicios vinculados (seguros, mantenimiento)
  - ☑️ Alquiler contador (si debe excluirse)
- Rellena formulario con:
  - Importe de cada ajuste
  - Descripción
  - Si es permanente o temporal
- `PUT /webhook/facturas/{id}/validar` → Valida factura
- Backend:
  1. `validacion_comercial.py` calcula `total_ajustado` (Cifra Reina)
  2. Genera warnings automáticos si ajustes son sospechosos
  3. Persiste en `ajustes_comerciales_json`
  4. Marca `validado_step2=true`
- Frontend:
  - Muestra warnings si los hay
  - Muestra "Total ajustado: XX.XX €"
  - Permite continuar a comparación

**Paso 3: Comparar ofertas**
- Pantalla: `/wizard/[id]/step-3-comparar`
- Usuario hace clic en "Comparar tarifas"
- `POST /webhook/comparar/facturas/{id}` → Ejecuta comparador
- Backend:
  1. `comparador.py` valida completitud de datos
  2. Usa `total_ajustado` si pasó STEP 2, sino `total_factura`
  3. Calcula coste actual reconstruido
  4. Para cada tarifa competidora:
     - Calcula coste estimado
     - Calcula ahorro mensual/anual
     - Consulta comisión (con versionado temporal)
  5. Persiste en `comparativas` + `ofertas_calculadas`
  6. Devuelve lista de ofertas ordenadas por ahorro
- Frontend:
  - Muestra tabla comparativa (3-5 ofertas)
  - Ordenadas por mayor ahorro anual
  - Muestra: Proveedor, Plan, Coste anual, Ahorro anual, Ahorro %
  - Botón "Seleccionar" en cada oferta

**Paso 4: Seleccionar oferta y generar PDF**
- Usuario hace clic en "Seleccionar" en una oferta
- `POST /webhook/facturas/{id}/seleccion` → Guarda selección
- Backend:
  1. Guarda FK `selected_oferta_id`
  2. Guarda timestamp `selected_at`
  3. Guarda `selected_by_user_id`
  4. Cambia `estado_factura` a `oferta_seleccionada`
- Frontend:
  - Muestra botón "Descargar estudio PDF"
- Usuario hace clic en "Descargar estudio PDF"
- `GET /webhook/facturas/{id}/presupuesto.pdf` → Genera PDF
- Backend:
  1. `pdf_generator.py` genera PDF con ReportLab
  2. Incluye sección Metodología si `validado_step2=true`
  3. Streaming directo (no guarda en disco)
- Frontend:
  - Descarga PDF automáticamente

**Pantallas involucradas:**
- `/wizard/new/step-1-factura`
- `/wizard/[id]/step-2-validar` (opcional)
- `/wizard/[id]/step-3-comparar`

**Módulos involucrados:**
- Backend: `app/routes/webhook.py` (orquestación)
- Backend: `app/services/ocr.py` (extracción)
- Backend: `app/services/validacion_comercial.py` (STEP 2)
- Backend: `app/services/comparador.py` (cálculo)
- Backend: `app/services/pdf_generator.py` (PDF)

### FLUJO C: Cliente acepta → tramitación → activación

**Actor:** Asesor

**Después de enviar PDF al cliente:**

1. Cliente responde (acepta o rechaza)
2. Asesor va a `/gestion/casos/[id]` (o lo busca desde `/gestion/casos`)
3. Si el caso se creó automáticamente desde factura → estado `en_estudio`
4. Asesor cambia estado manualmente:
   - `en_estudio` → `propuesta_enviada`
   - `propuesta_enviada` → `contrato_enviado`
   - `contrato_enviado` → `pendiente_firma`
   - `pendiente_firma` → `firmado`
   - `firmado` → `validado` (solo CEO puede)
   - `validado` → `activo` (solo CEO puede)
5. `PUT /api/casos/{id}/estado` → Cambia estado
6. Backend:
   - Valida transición permitida (`TRANSICIONES` dict)
   - Si transición no permitida → Error 400
   - Actualiza `estado_comercial`
   - Registra en `historial_caso` (tipo_evento: cambio_estado)
   - **⚠️ FALTA:** Cuando estado → `activo`, crear registro en `comisiones_generadas`

**Estados de rechazo:**
- `perdido` (cliente no interesado)
- `cancelado` (cancelación por cualquier motivo)

**Pantalla:** `/gestion/casos/[id]`
**Módulo:** Backend `app/routes/casos.py`

### FLUJO D: Seguimiento y revisión (10 meses)

**Estado:** ❌ NO implementado todavía

**Concepto:**
- Cuando un caso pasa a `activo`, se marca `fecha_activacion`
- Sistema debe generar alerta/tarea automática a los 10 meses
- Asesor recibe notificación para:
  - Contactar cliente
  - Revisar si sigue satisfecho
  - Ofrecer renovación o cambio de tarifa
  - Evitar que cliente se vaya a competencia

**Requisitos pendientes:**
- Sistema de tareas/alertas (tabla `tareas` o similar)
- Notificaciones (email, push, badge en UI)
- Filtro en `/gestion/casos` para "Próximos a revisar"
- Workflow de renovación (similar a caso nuevo)

---

## 4️⃣ PIPELINE / ETAPAS DEL CASO

### Lista exacta de etapas (campo `estado_comercial`)

```
lead                → Cliente potencial, primer contacto
contactado          → Ya se habló con el cliente
en_estudio          → Analizando factura/situación
propuesta_enviada   → PDF enviado al cliente
negociacion         → Cliente está evaluando/negociando
contrato_enviado    → Contrato firmado por asesoría, enviado a cliente
pendiente_firma     → Esperando firma del cliente
firmado             → Cliente firmó contrato
validado            → CEO validó contrato (revisión interna)
activo              → Contrato activado con comercializadora (⚠️ TRIGGER COMISIÓN)
baja                → Cliente dio de baja el servicio
cancelado           → Caso cancelado (por cualquier motivo)
perdido             → Cliente no interesado / perdido a competencia
```

### Transiciones permitidas (reglas de negocio)

```python
TRANSICIONES = {
    "lead": ["contactado", "perdido", "cancelado"],
    "contactado": ["en_estudio", "perdido", "cancelado"],
    "en_estudio": ["propuesta_enviada", "perdido", "cancelado"],
    "propuesta_enviada": ["negociacion", "contrato_enviado", "perdido", "cancelado"],
    "negociacion": ["contrato_enviado", "propuesta_enviada", "perdido", "cancelado"],
    "contrato_enviado": ["pendiente_firma", "cancelado"],
    "pendiente_firma": ["firmado", "cancelado"],
    "firmado": ["validado", "cancelado"],
    "validado": ["activo", "cancelado"],  # Solo CEO
    "activo": ["baja"],
    "baja": [],  # Estado terminal
    "cancelado": [],  # Estado terminal
    "perdido": [],  # Estado terminal
}
```

### Campos obligatorios por etapa

**lead:**
- cliente_id ✅
- cups (recomendado, no obligatorio)
- asesor_user_id (recomendado)

**contactado:**
- fecha_contacto ✅

**propuesta_enviada:**
- oferta_id (FK a oferta seleccionada) ✅
- ahorro_estimado_anual ✅
- fecha_propuesta ✅

**contrato_enviado:**
- nueva_compania_text ✅
- tarifa_nombre_text ✅

**firmado:**
- fecha_firma ✅

**activo:**
- fecha_activacion ✅
- ⚠️ **TRIGGER:** Crear registro en `comisiones_generadas` (NO IMPLEMENTADO)

**baja:**
- fecha_baja ✅
- notas (razón de baja, recomendado)

### Estados "perdidos" (no interesa)

- **perdido:** Cliente no interesado, se fue a competencia, no responde
- **cancelado:** Cancelación por asesoría (error, duplicado, etc.)

**Diferencia:**
- `perdido` = Cliente decide no continuar
- `cancelado` = Asesoría/CEO decide cerrar caso

---

## 5️⃣ DATOS Y CAMPOS CLAVE (MODELO DE NEGOCIO)

### Campos del Cliente (tabla `clientes`)

**Identificación:**
- nombre (text)
- email (text)
- telefono (text)
- dni / CIF (text) - Mismo campo `dni`, admite ambos formatos

**Tipo de cliente:**
- DESCONOCIDO si hay campo `tipo_cliente` (particular | empresa)
- Inferido por formato de `dni`:
  - NIF: 8 dígitos + letra (particular)
  - CIF: letra + 7 dígitos + dígito/letra (empresa)

**Suministro:**
- cups (text, unique, index) - Identificador único del punto de suministro
- direccion (text)
- provincia (text)

**Estado y origen:**
- estado (lead | seguimiento | oferta_enviada | contratado | descartado)
- origen (factura_upload | manual | web)

**Multi-tenant:**
- company_id (FK → companies)
- comercial_id (FK → users) - Asesor asignado

### Campos del Suministro/CUPS (tabla `facturas` o `casos`)

**En `facturas`:**
- cups (text, único por factura)
- direccion → DESCONOCIDO si existe en `facturas` o solo en `clientes`

**En `casos`:**
- cups (text, index)
- servicio (luz | gas | luz+gas)
- antigua_compania_text (text) - Comercializadora anterior
- nueva_compania_text (text) - Comercializadora nueva

**Datos técnicos (en `facturas`):**
- atr (2.0TD | 3.0TD) - Tipo de peaje
- potencia_p1_kw, potencia_p2_kw (float)
- consumo_p1_kwh, consumo_p2_kwh, consumo_p3_kwh (float)
- consumo_p4_kwh, consumo_p5_kwh, consumo_p6_kwh (float, para 3.0TD)
- periodo_dias (int)

**Distribuidora:**
- DESCONOCIDO si hay campo `distribuidora_text` en alguna tabla
- Se puede inferir de CUPS (4 primeros caracteres tras ES)

### Datos de Factura (tabla `facturas`)

**Período y fechas:**
- fecha_inicio (text, formato YYYY-MM-DD)
- fecha_fin (text, formato YYYY-MM-DD)
- periodo_dias (int, calculado)
- fecha (text) - Fecha de emisión

**Consumos (kWh):**
- consumo_kwh (float) - Total (legacy)
- consumo_p1_kwh, consumo_p2_kwh, consumo_p3_kwh (float) - 2.0TD
- consumo_p4_kwh, consumo_p5_kwh, consumo_p6_kwh (float) - 3.0TD

**Potencias (kW):**
- potencia_p1_kw (float) - Punta
- potencia_p2_kw (float) - Valle

**Importes:**
- total_factura (float) - Total sin ajustar
- total_ajustado (float) - "Cifra Reina" post-STEP 2
- importe (float) - DEPRECATED, usar total_factura

**Impuestos:**
- impuesto_electrico (float, €)
- iva (float, €)
- iva_porcentaje (float, 0-100) - Ejemplo: 21.0

**Condiciones especiales:**
- bono_social (boolean)
- servicios_vinculados (boolean)
- alquiler_contador (float, €)

**Desglose estructural (baseline):**
- coste_energia_actual (float) - E_actual
- coste_potencia_actual (float) - P_actual

**STEP 2 (validación comercial):**
- ajustes_comerciales_json (text, JSON):
```json
{
  "bono_social": {
    "activo": true,
    "descuento_estimado": 12.50,
    "origen": "ocr_auto",
    "nota_pdf": "Tu factura incluye Bono Social..."
  },
  "descuento_comercial": {
    "importe": 4.50,
    "descripcion": "Descuento 10% primer año",
    "temporal": true
  },
  "servicios_vinculados": {
    "importe": 2.00,
    "descripcion": "Seguro hogar"
  },
  "alquiler_contador": {
    "importe": 0.80,
    "excluir": true
  }
}
```
- validado_step2 (boolean)

**Auditoría:**
- raw_data (text, JSON) - Datos crudos OCR
- file_hash (text, unique) - SHA256 del archivo

**Estado:**
- estado_factura (pendiente_datos | lista_para_comparar | oferta_seleccionada)

**Selección:**
- selected_oferta_id (FK → ofertas_calculadas)
- selected_at (datetime)
- selected_by_user_id (FK → users)

### Comparativa (tabla `comparativas` + `ofertas_calculadas`)

**Comparativa (auditoría):**
- factura_id (FK → facturas)
- created_at (datetime)
- periodo_dias (int)
- current_total (float)
- inputs_json (text, JSON) - Inputs usados
- status (ok | error)
- error_json (text, JSON si error)

**OfertaCalculada:**
- comparativa_id (FK → comparativas)
- tarifa_id (int) - Referencia lógica (no FK)
- coste_estimado (float) - Coste anual
- ahorro_mensual (float)
- ahorro_anual (float)
- detalle_json (text, JSON):
```json
{
  "proveedor": "Repsol",
  "plan": "Precio Fijo 12 meses",
  "coste_energia": 123.45,
  "coste_potencia": 45.67,
  "subtotal": 169.12,
  "impuesto_electrico": 8.65,
  "base_imponible": 177.77,
  "iva": 37.33,
  "total": 215.10,
  "comision_eur": 50.00,
  "comision_source": "tarifa"
}
```
- comision_eur (float)
- comision_source (tarifa | cliente | manual)
- created_at (datetime)

### Contratación (campos en `casos`)

**Documentos:**
- DESCONOCIDO si hay tabla `documentos_caso` o similar
- DESCONOCIDO si hay campo `documentos_urls_json`

**Firma:**
- fecha_firma (datetime) - Cuando cliente firmó
- DESCONOCIDO si hay integración con plataforma de firma electrónica

**Fechas del ciclo:**
- fecha_contacto (datetime)
- fecha_propuesta (datetime)
- fecha_firma (datetime)
- fecha_activacion (datetime) - Cuando se activa con comercializadora
- fecha_baja (datetime) - Si cliente da de baja

**Datos de contratación:**
- nueva_compania_text (text) - Ej: "Repsol"
- tarifa_nombre_text (text) - Ej: "Precio Fijo 12 meses"
- tarifa_id (bigint) - FK lógica a tabla tarifas (si existe)
- oferta_id (FK → ofertas_calculadas)

### Comisiones (tu comisión, comisión colaborador, reglas)

**ComisionGenerada (tabla `comisiones_generadas`):**
- company_id (FK → companies)
- factura_id (FK → facturas, nullable)
- cliente_id (FK → clientes)
- asesor_id (FK → users) - Quien generó la venta
- oferta_id (FK → ofertas_calculadas)
- tarifa_id (bigint)
- caso_id (FK → casos, nullable)
- comision_total_eur (numeric 12,2) - Comisión total antes de repartir
- comision_source (manual | tarifa | cliente)
  - `tarifa`: Comisión estándar desde `comisiones_tarifa`
  - `cliente`: Comisión custom desde `comisiones_cliente` (prioridad)
  - `manual`: Ingresada manualmente por CEO
- estado (pendiente | validada | pagada | anulada | retenida | decomision)
  - `pendiente`: Recién creada, esperando validación
  - `validada`: CEO validó, lista para pagar
  - `pagada`: Ya pagada
  - `anulada`: Cancelada (cliente se dio de baja antes de activar, etc.)
  - `retenida`: Retenida temporalmente (conflicto, auditoría)
  - `decomision`: Comisión devuelta (cliente revirtió contrato)
- fecha_prevista_pago (date)
- fecha_pago (date)
- created_at (datetime)
- updated_at (datetime)

**RepartoComision (tabla `repartos_comision`):**
- comision_id (FK → comisiones_generadas)
- tipo_destinatario (asesor | ceo | colaborador)
- user_id (FK → users, nullable) - Si destinatario es usuario con login
- colaborador_id (FK → colaboradores, nullable) - Si destinatario es colaborador externo
- importe_eur (numeric 12,2) - Parte de la comisión
- porcentaje (numeric 6,3) - % del total (ej: 70.000 = 70%)
- estado_pago (pendiente | pagado | cancelado)
- fecha_pago (date)
- notas (text)
- created_at (datetime)

**Configuración de comisiones:**

**comisiones_tarifa (tabla):**
- tarifa_id (int)
- comision_eur (float)
- vigente_desde (date)
- vigente_hasta (date, nullable)
- created_at (datetime)

**Versionado:** Permite cambiar comisiones a futuro sin perder histórico
- Cuando se sube CSV nuevo, sistema cierra versión anterior (asigna `vigente_hasta`)
- Query busca comisión vigente en fecha de comparativa

**comisiones_cliente (tabla):**
- cliente_id (FK → clientes)
- tarifa_id (int)
- comision_eur (float)
- prioridad_sobre_tarifa (boolean, default true)
- created_at (datetime)

**Prioridad:** Si existe comisión custom en `comisiones_cliente`, esa prevalece sobre `comisiones_tarifa`

**Endpoint para subir comisiones:**
- `POST /webhook/comisiones/upload` → Acepta CSV/Excel
- Formato:
```csv
tarifa_id,comision_eur,vigente_desde
1,50.00,2026-01-01
2,75.00,2026-01-01
```

**Reglas de negocio:**
1. Comisión se calcula al generar oferta (`ofertas_calculadas.comision_eur`)
2. Comisión se guarda al seleccionar oferta (FK `selected_oferta_id`)
3. **⚠️ FALTA:** Cuando caso pasa a `activo`, crear registro en `comisiones_generadas`
4. **⚠️ FALTA:** Cuando se crea `comisiones_generadas`, aplicar split en `repartos_comision`
5. CEO puede marcar comisión como `validada` → `pagada`

**Split de comisiones (ejemplo):**
```
Comisión total: 100€
- Asesor: 70€ (70%)
- CEO: 20€ (20%)
- Colaborador: 10€ (10%)
```

**⚠️ FALTA IMPLEMENTAR:**
- Lógica de split automático (configuración de porcentajes por rol)
- Trigger para crear `comisiones_generadas` cuando caso → `activo`
- Endpoints para gestión de repartos (`GET /api/repartos`, `PUT /api/repartos/{id}`)
- Dashboard de comisiones pendientes/pagadas para asesor

---

## 6️⃣ PROBLEMAS ACTUALES / BLOQUEOS

### Lo que duele (pérdida de tiempo / errores)

**1. OCR Imperfecto (71% precisión)**
- **Problema:** Consumos P1, P2, P3 a veces se leen mal (error 270x, 64x, 35x)
- **Impacto:** Comparador calcula ahorros completamente ficticios si no se validan
- **Workaround:** Asesor debe revisar SIEMPRE en step-1
- **Solución sugerida:** 
  - Validación automática: bloquear si consumo > 1000 kWh/período
  - Hacer STEP 2 obligatorio
  - Mejorar patrones regex para tablas gráficas

**2. Direcciones y localidades no se extraen bien**
- **Problema:** OCR lee direcciones incompletas o con CP pegado
- **Impacto:** Cliente ve dirección mal en PDF, pierde confianza
- **Solución sugerida:**
  - Mejorar lógica de extracción línea por línea
  - Pattern para CP + Ciudad + Provincia
  - Limpiar CP del final de direcciones
  - Objetivo: 96% precisión (plan en PLAN_96_PERCENT.md)

**3. Facturas sin pasar STEP 2**
- **Problema:** Comparador puede usar `total_factura` directo (incluye Bono Social, descuentos temporales)
- **Impacto:** Ahorros inflados artificialmente, cliente insatisfecho al activar
- **Solución sugerida:** Hacer STEP 2 obligatorio en wizard

**4. No hay sistema de tareas/alertas**
- **Problema:** Asesor olvida revisar casos a los 10 meses
- **Impacto:** Clientes se van a competencia sin que asesoría lo sepa
- **Solución sugerida:**
  - Tabla `tareas` con alertas automáticas
  - Notificaciones (email, badge en UI)
  - Filtro "Próximos a revisar" en `/gestion/casos`

**5. Comisiones NO se generan automáticamente**
- **Problema:** Cuando caso pasa a `activo`, NO se crea registro en `comisiones_generadas`
- **Impacto:** CEO debe crear comisiones manualmente → pérdida tiempo, olvidos
- **Solución sugerida:**
  - Trigger en `PUT /api/casos/{id}/estado` cuando `estado_nuevo = activo`
  - Crear registro en `comisiones_generadas` con estado `pendiente`
  - Copiar comisión de `ofertas_calculadas.comision_eur`

**6. Split de comisiones no implementado**
- **Problema:** Tabla `repartos_comision` existe pero no se usa
- **Impacto:** No se puede repartir comisión entre asesor/CEO/colaborador automáticamente
- **Solución sugerida:**
  - Configuración de porcentajes por rol (tabla `configuracion_repartos` o similar)
  - Lógica de split al crear `comisiones_generadas`
  - Endpoints CRUD para repartos

**7. No hay estadísticas/KPIs en panel CEO**
- **Problema:** CEO no puede ver en dashboard:
  - Facturas procesadas total
  - Ahorro total generado
  - Comisiones pendientes/pagadas
  - Asesores activos
  - Evolución últimos 30 días
- **Impacto:** CEO pierde visibilidad del negocio
- **Solución sugerida:** 
  - Endpoint `GET /api/stats/ceo` (parcialmente en `app/routes/stats.py`)
  - Implementar queries SQL para KPIs (están documentadas en INFORME_PANEL_CEO_COMPLETO.md)
  - Frontend en `/gestion/resumen` con Chart.js

**8. Dependencia de Zoho/GHL/Excel**
- **Problema:** Asesorías siguen usando herramientas externas en paralelo
- **Impacto:** Doble trabajo, datos desincronizados
- **Causa:** CRM interno no tiene funcionalidades completas (tareas, documentos, firma, email)
- **Solución a largo plazo:** 
  - Sistema de tareas integrado
  - Gestión de documentos por caso
  - Integración email/WhatsApp
  - Integración firma electrónica

**9. Sin control de acceso fino (roles)**
- **Problema:** Roles existen (dev, ceo, comercial) pero control de acceso es parcial
- **Impacto:** Comercial puede ver casos de otros comerciales (filtrado manual en endpoints)
- **Solución sugerida:**
  - Middleware de permisos por rol
  - Filtrado automático en queries por `company_id` y `comercial_id`
  - Endpoints específicos para cada rol

**10. Migraciones manuales (sin Alembic)**
- **Problema:** Cambios de schema requieren SQL manual
- **Impacto:** Riesgo de olvidar migración, desincronización local/producción
- **Solución sugerida:** Adoptar Alembic (SQLAlchemy migrations)

---

## 7️⃣ REQUISITOS DEL MVP DE "GESTIÓN" (PRIORIDAD ABSOLUTA)

### Lo que DEBE existir sí o sí en el panel interno

**1. Listado de casos (`/gestion/casos`)**
- ✅ Tabla con columnas:
  - ID caso
  - Cliente (nombre + CUPS)
  - Estado comercial (con badge de color)
  - Asesor asignado
  - Colaborador (si aplica)
  - Ahorro estimado (€)
  - Fecha creación
  - Última actualización
- ✅ Filtros:
  - Por estado (dropdown multi-select)
  - Por asesor (dropdown)
  - Por fecha creación (date range)
  - Por cliente (búsqueda texto)
- ✅ Búsqueda global (cliente, CUPS, ID)
- ✅ Paginación (50 casos/página)
- ✅ Orden por columna (click en header)
- ✅ Botón "Crear caso manual" → `/gestion/casos/nuevo`

**2. Vista detalle de caso (`/gestion/casos/[id]`)**
- ✅ Información general (card):
  - Cliente (link a `/clientes/[id]`)
  - CUPS
  - Servicio (luz/gas)
  - Asesor (link a perfil)
  - Colaborador
  - Estado actual (grande, con badge)
  - Fechas del ciclo (contacto, propuesta, firma, activación)
- ✅ Cambio de estado:
  - Dropdown con estados permitidos (según transiciones)
  - Botón "Cambiar estado" → Modal con confirmación + nota opcional
  - Validación: Solo transiciones permitidas
- ✅ Datos comerciales (card):
  - Comercializadora anterior
  - Comercializadora nueva
  - Tarifa seleccionada
  - Ahorro estimado anual
  - Canal de adquisición
- ✅ Factura asociada (card):
  - Si existe: Mostrar resumen + link a `/facturas/[id]`
  - Si no existe: Botón "Subir factura"
- ✅ Oferta seleccionada (card):
  - Si existe: Mostrar desglose oferta
  - Si no existe: Mensaje "Sin oferta seleccionada"
- ⏳ Timeline de eventos (card):
  - Lista cronológica de eventos (`historial_caso`)
  - Tipo evento + descripción + usuario + timestamp
  - Orden: Más reciente primero
- ⏳ Notas internas (card):
  - Campo texto para añadir nota
  - Botón "Guardar nota"
  - Historial de notas (quién, cuándo, texto)
- ❌ Adjuntos/documentos:
  - NO implementado todavía
- ❌ Tareas pendientes:
  - NO implementado todavía

**3. Crear caso manual (`/gestion/casos/nuevo`)**
- ✅ Formulario con campos:
  - Cliente (dropdown buscable o botón "Crear cliente nuevo")
  - CUPS (opcional, validación formato)
  - Asesor asignado (dropdown, default: usuario actual)
  - Colaborador (dropdown, opcional)
  - Canal (dropdown: web, teléfono, presencial, otros)
  - Servicio (radio: luz, gas, luz+gas)
  - Notas (textarea)
- ✅ Validaciones:
  - Cliente obligatorio
  - CUPS formato correcto (si se rellena)
- ✅ Al guardar:
  - `POST /api/casos` → Crea caso en estado `lead`
  - Redirige a `/gestion/casos/[id]`

**4. Dashboard resumen (`/gestion/resumen`)**
- ⏳ KPI Cards (4 cards horizontales):
  - Facturas procesadas (total)
  - Ahorro generado (suma ofertas seleccionadas)
  - Comisiones pendientes (suma estado pendiente+validada)
  - Asesores activos (count usuarios activos rol comercial)
- ❌ Gráfico evolución últimos 30 días (Chart.js):
  - Líneas: Facturas procesadas, Ahorro generado, Comisiones generadas
  - Eje X: Días
  - Eje Y: Cantidad/€
- ⏳ Actividad reciente (últimas 5 acciones):
  - Factura procesada
  - Oferta seleccionada
  - Caso cambió estado
  - Comisión validada
- ⏳ Alertas críticas:
  - Ofertas seleccionadas sin comisión generada
  - Comisiones validadas hace +30 días sin pagar
  - Casos estancados en mismo estado >7 días

**5. Gestión de comisiones (`/gestion/comisiones`)**
- ⏳ Tabs:
  - **Configuración:** Subir CSV de comisiones por tarifa
  - **Generadas:** Listado de comisiones generadas (filtros: estado, asesor, fecha)
- ⏳ Tab Configuración:
  - Botón "Subir CSV"
  - Preview de datos antes de importar
  - Tabla con comisiones actuales (tarifa_id, comisión, vigente desde/hasta)
- ⏳ Tab Generadas:
  - Tabla: ID, Caso, Cliente, Asesor, Tarifa, Comisión €, Estado, Fecha prevista pago
  - Filtros: Estado, Asesor, Fecha creación
  - Acciones: Ver detalle, Marcar como validada, Marcar como pagada
- ❌ Tab Repartos:
  - NO implementado todavía
  - Futuro: Listado de repartos por comisión

**6. Gestión de colaboradores (`/gestion/colaboradores`)**
- ✅ Listado de colaboradores (tabla):
  - Nombre
  - Teléfono
  - Email
  - Notas
  - Acciones (editar, eliminar)
- ✅ Botón "Añadir colaborador" → Modal con formulario
- ✅ Editar colaborador → Modal con formulario
- ✅ Eliminar colaborador → Confirmación

**7. Control de pagos (`/gestion/pagos`)**
- ❌ NO implementado todavía
- Futuro:
  - Listado de comisiones pendientes de pago
  - Filtros: Asesor, Fecha prevista
  - Acción: Marcar como pagada (fecha pago, nota)
  - Listado de pagos realizados (histórico)

**8. Alertas y notificaciones**
- ❌ NO implementado todavía
- Futuro:
  - Badge en header con número de alertas
  - Dropdown con lista de alertas
  - Tipos de alerta:
    - Caso estancado
    - Comisión pendiente +30 días
    - Revisión 10 meses (caso activo)
    - Oferta sin comisión
  - Link a acción correspondiente

**9. Control de acceso por rol**
- ⏳ Parcialmente implementado:
  - CEO: Ve todo de su company
  - Comercial: Ve solo sus casos (filtrado manual en endpoints)
  - Dev: Ve todo sin restricciones
- ❌ Falta:
  - Middleware automático de permisos
  - UI: Ocultar secciones según rol (ej: `/gestion` solo para CEO/dev)
  - Validación consistente en todos los endpoints

**10. Audit logs / historial de cambios**
- ✅ Tabla `historial_caso` (timeline por caso)
- ❌ NO hay audit logs globales (tabla `audit_logs` para todo el sistema)
- Futuro:
  - Registrar: Login, cambios en clientes, facturas, comisiones, configuración
  - Pantalla `/gestion/auditoria` (solo dev)

### Lo que NO se va a hacer todavía (fuera de MVP)

**Integraciones externas:**
- ❌ Zoho CRM (sincronización bidireccional)
- ❌ Power BI (exportación datos)
- ❌ Email/WhatsApp (envío automático desde plataforma)
- ❌ Firma electrónica (DocuSign, etc.)
- ❌ Pasarela de pago (cobro comisiones online)

**Funcionalidades avanzadas:**
- ❌ Sistema de tareas/calendario integrado
- ❌ Gestión de documentos por caso (upload, storage)
- ❌ Chat interno entre asesor-CEO
- ❌ Reportes personalizados (drag-and-drop)
- ❌ Multi-idioma (solo español por ahora)
- ❌ Modo oscuro/claro (solo modo oscuro por ahora)
- ❌ App móvil nativa

**Comparador avanzado:**
- ❌ API dinámica de precios (ahora hardcodeados)
- ❌ Simulación multi-período (proyección 12 meses)
- ❌ Comparación luz + gas simultánea
- ❌ Simulación con cambio de potencia
- ❌ Integración con CNMC para validar tarifas

---

## 8️⃣ INTEGRACIONES DESEADAS (SI APLICA)

### Fase 1 (MVP): NINGUNA
- Todo interno, sin integraciones

### Fase 2 (Post-MVP):

**Zoho CRM:**
- **Objetivo:** Exportar casos/clientes a Zoho para seguimiento comercial
- **Dirección:** Unidireccional (CRM interno → Zoho)
- **Trigger:** Manual (botón "Exportar a Zoho") o automático (webhook cuando caso → activo)
- **Campos a exportar:** Cliente, CUPS, estado, asesor, ahorro, fechas
- **Prioridad:** BAJA (solo si cliente lo requiere)

**Power BI / Metabase:**
- **Objetivo:** Dashboards ejecutivos para CEO con datos históricos
- **Dirección:** Unidireccional (DB → Power BI)
- **Método:** Conexión directa a Neon (read-only user)
- **Dashboards sugeridos:**
  - Evolución mensual (facturas, ahorros, comisiones)
  - Desglose por asesor (rendimiento)
  - Análisis de pipeline (embudos de conversión)
  - Análisis de tarifas más rentables
- **Prioridad:** MEDIA (CEO quiere visualización avanzada)

**Email automatizado:**
- **Objetivo:** Enviar PDF automáticamente al cliente tras selección de oferta
- **Proveedor:** SendGrid o AWS SES
- **Trigger:** Automático tras `POST /webhook/facturas/{id}/seleccion`
- **Template:** Email con PDF adjunto + link a landing de firma
- **Prioridad:** ALTA (ahorra tiempo manual)

**WhatsApp Business API:**
- **Objetivo:** Enviar notificaciones por WhatsApp (más efectivo que email)
- **Proveedor:** Twilio o WhatsApp Cloud API
- **Casos de uso:**
  - Confirmar recepción de factura
  - Notificar estudio listo
  - Recordar firma pendiente
  - Confirmar activación
- **Prioridad:** MEDIA (después de email)

**Firma electrónica:**
- **Objetivo:** Cliente firma contrato digitalmente
- **Proveedor:** DocuSign, SignRequest, o similar
- **Flujo:**
  1. Asesor genera contrato desde plantilla
  2. Sistema envía a cliente por email/WhatsApp
  3. Cliente firma en móvil/web
  4. Webhook actualiza caso a estado `firmado`
- **Prioridad:** ALTA (elimina papel, acelera proceso)

**Pasarela de pago (futuro lejano):**
- **Objetivo:** Cobrar comisiones online (si modelo de negocio cambia)
- **Proveedor:** Stripe, Redsys
- **Prioridad:** BAJA (no aplica si comisiones son B2B)

### Fase 3 (Largo plazo):

**Google Calendar / Outlook:**
- **Objetivo:** Sincronizar tareas/citas con calendario
- **Prioridad:** BAJA

**Slack / Teams:**
- **Objetivo:** Notificaciones en canal de equipo
- **Prioridad:** BAJA

---

## 9️⃣ RESTRICCIONES Y PREFERENCIAS

### Idioma
- **UI:** Español (España)
- **Código:** Inglés (nombres de variables, funciones, comentarios)
- **Documentación:** Español (España)

### RGPD / Privacidad
- **Aplicable:** SÍ (clientes en España)
- **Requisitos:**
  - Consentimiento explícito para tratar datos (formulario con checkbox)
  - Política de privacidad (link en footer)
  - Derecho de acceso, rectificación, supresión (email a DPO)
  - Cifrado en tránsito (HTTPS) ✅
  - Cifrado en reposo (Neon DB cifrado) ✅
  - Logs de acceso a datos sensibles (audit logs) ⏳
  - Anonimización al eliminar clientes (soft delete + anonimizar campos) ❌
- **Estado:** Parcialmente implementado
- **Prioridad:** ALTA (requisito legal)

### Multi-colaborador / Multi-tenant
- **Modelo:** Multi-tenant (1 base de datos, N companies)
- **Aislamiento:** Por `company_id` en todas las tablas principales
- **Roles:** dev (super-admin), ceo (admin company), manager (futuro), comercial (usuario)
- **Control de acceso:** 
  - Dev: Todo sin restricciones
  - CEO: Todo de su company
  - Manager: Todo de su equipo (futuro)
  - Comercial: Solo sus casos/clientes
- **Estado:** ✅ Implementado (parcialmente, falta middleware automático)

### Control de acceso / Audit logs
- **Audit logs:** ⏳ Parcialmente implementado
  - `historial_caso` (timeline por caso) ✅
  - Audit logs globales ❌
- **Requisitos futuros:**
  - Registrar: Login, logout, cambios en datos sensibles, cambios de configuración
  - Retención: 1 año mínimo (RGPD)
  - Acceso: Solo dev/CEO
  - Inmutabilidad: No editable, solo insert
- **Prioridad:** MEDIA (importante para auditorías)

### Estilo de desarrollo (stack decidido)

**Frontend:**
- Next.js 14+ (App Router, NO Pages Router)
- React 18+ (hooks, NO class components)
- TailwindCSS (utility-first, NO CSS modules)
- TypeScript (NO JavaScript puro en nuevos archivos)
- Chart.js + react-chartjs-2 (gráficos)

**Backend:**
- FastAPI (Python 3.10+)
- SQLAlchemy 2.0 (ORM, NO raw SQL salvo casos excepcionales)
- Pydantic (validación, schemas)
- NO usar Flask, NO usar Django

**Base de datos:**
- PostgreSQL (Neon en producción, SQLite en local)
- Migraciones: MANUAL por ahora (adoptar Alembic en futuro)
- Naming: snake_case (tablas y columnas)

**Despliegue:**
- Frontend: Vercel (NO Netlify, NO otros)
- Backend: Render (NO Heroku, NO Railway)
- DB: Neon (NO Supabase, NO RDS)

**Testing:**
- Backend: pytest (tests en carpeta raíz, ej: `test_all_fixes.py`)
- Frontend: NO hay tests todavía (adoptar Jest + React Testing Library en futuro)
- NO usar unittest, NO usar mocha

**Code Style:**
- Python: PEP 8, formatear con Black (si se adopta)
- TypeScript: ESLint configurado en `eslint-config-next`
- Commits: Mensajes descriptivos en español o inglés

### Qué NO tocar / Decisiones ya tomadas

**NO cambiar:**
1. Stack tecnológico (Next.js + FastAPI + Neon)
2. Header horizontal (NO sidebar)
3. Paleta de colores (azul #0073EC)
4. Wizard de 3 pasos (core del producto)
5. Sistema de cards (diseño consistente)
6. Estructura de tablas principales (Cliente, Factura, Caso, Comisión)
7. Flujo de OCR → Validar → Comparar → PDF
8. Fórmulas del comparador (PO ya validado)

**NO hacer (sin consultar CEO):**
1. Cambiar precios/tarifas hardcodeadas (sin conexión API)
2. Modificar lógica de comisiones (sin aprobación)
3. Eliminar funcionalidades existentes
4. Cambiar nombres de endpoints (rompe frontend)
5. Migrar a otra plataforma (Vercel, Render, Neon son definitivos)

---

## 🔟 PRÓXIMOS PASOS SUGERIDOS (MUY CONCRETOS)

### Orden de prioridad para terminar MVP de gestión

**PRIORIDAD 1: Completar funcionalidades críticas (1-2 semanas)**

1. **Implementar generación automática de comisiones**
   - Archivo: `app/routes/casos.py`
   - Modificar: `PUT /api/casos/{id}/estado`
   - Cuando `estado_nuevo == "activo"`:
     - Crear registro en `comisiones_generadas`
     - Copiar comisión de `ofertas_calculadas.comision_eur` (si existe)
     - Estado inicial: `pendiente`
     - Fecha prevista pago: `fecha_activacion + 30 días`
   - Registrar evento en `historial_caso`

2. **Implementar lógica de split de comisiones**
   - Crear tabla `configuracion_repartos` (o usar JSON en `companies`)
   - Campos: `company_id`, `role`, `porcentaje`
   - Al crear `comisiones_generadas`:
     - Consultar configuración de repartos
     - Crear registros en `repartos_comision`
     - Split asesor / CEO / colaborador según porcentajes
   - Endpoints:
     - `GET /api/configuracion_repartos` → Obtener configuración actual
     - `PUT /api/configuracion_repartos` → Actualizar porcentajes

3. **Endpoint de estadísticas CEO**
   - Archivo: `app/routes/stats.py` (ya existe parcialmente)
   - Implementar: `GET /api/stats/ceo`
   - Queries SQL (documentadas en INFORME_PANEL_CEO_COMPLETO.md):
     - KPI 1: Facturas procesadas total
     - KPI 2: Ahorro total generado
     - KPI 3: Comisiones pendientes
     - KPI 4: Asesores activos
     - Evolución últimos 30 días (group by fecha)
     - Actividad reciente (últimas 5 acciones)
     - Alertas críticas (ofertas sin comisión, comisiones estancadas)
   - Respuesta JSON con todos los datos
   - Caché: 5 minutos (usar `@lru_cache` o Redis en futuro)

4. **Frontend `/gestion/resumen`**
   - Archivo: `app/gestion/resumen/page.jsx` (crear)
   - Consumir endpoint `GET /api/stats/ceo`
   - Renderizar:
     - 4 KPI cards
     - Gráfico Chart.js (líneas, últimos 30 días)
     - Tabla actividad reciente
     - Tabla alertas críticas (con links a acciones)
   - Botón refrescar (re-fetch datos)

5. **Timeline de eventos en detalle de caso**
   - Archivo: `app/gestion/casos/[id]/page.jsx` (modificar)
   - Query: `GET /api/casos/{id}/historial`
   - Endpoint: `app/routes/casos.py` (crear)
   - Renderizar lista cronológica:
     - Icono por tipo de evento
     - Descripción
     - Usuario que realizó acción
     - Timestamp relativo ("hace 2 horas")
   - Orden: Más reciente primero

6. **Sistema de notas internas en casos**
   - Backend:
     - Crear endpoint `POST /api/casos/{id}/nota`
     - Request: `{ "nota": "Texto..." }`
     - Crear registro en `historial_caso` con `tipo_evento="nota"`
   - Frontend:
     - Card "Notas" en `/gestion/casos/[id]`
     - Textarea + botón "Guardar nota"
     - Al guardar → POST → Actualizar timeline

7. **Validación OCR mejorada (bloqueo de consumos sospechosos)**
   - Archivo: `app/services/ocr.py`
   - Después de extraer consumos P1, P2, P3:
     - Si `consumo_px > 1000 kWh` → Warning + marcar campo como `sospechoso`
     - Si `consumo_px > 5000 kWh` → Error, bloquear factura con estado `error_ocr`
   - Archivo: `app/routes/webhook.py` (`POST /webhook/upload`)
   - Si factura en estado `error_ocr` → Devolver HTTP 422 con detalles
   - Frontend: Mostrar error + permitir corrección manual

8. **Hacer STEP 2 obligatorio en wizard**
   - Archivo: Frontend wizard (determinar archivo exacto)
   - Modificar flujo:
     - step-1 → step-2 (obligatorio) → step-3
     - Eliminar botón "Saltar validación comercial"
   - Backend: Modificar `POST /webhook/comparar/facturas/{id}`
   - Validar: Si `validado_step2 == false` → Error 400 "Debes completar STEP 2 primero"

9. **Mejorar OCR: direcciones y localidades (Plan 96%)**
   - Archivo: `app/services/ocr.py`
   - Implementar mejoras documentadas en `PLAN_96_PERCENT.md`:
     - **Fase 1:** Arreglar direcciones (limpiar CP, buscar línea anterior)
     - **Fase 2:** Arreglar localidades (pattern CP + Ciudad + Provincia)
     - **Fase 3:** Arreglar alquiler (capturar tercer número)
     - **Fase 4:** Validar fechas (contexto)
   - Ejecutar tests: `python test_all_fields_complete.py`
   - Objetivo: 96% precisión (47/49 tests)

10. **Control de acceso automático en endpoints**
    - Crear middleware: `app/auth.py` → `require_role(role)`
    - Decorador: `@require_role("ceo")` en endpoints de gestión
    - Validación automática:
      - CEO: Solo su `company_id`
      - Comercial: Solo sus casos (`asesor_user_id`)
      - Dev: Sin restricciones
    - Aplicar en todos los endpoints de `/api/casos`, `/api/comisiones_generadas`, etc.

**PRIORIDAD 2: Completar pantallas de gestión (1 semana)**

11. **Tab "Generadas" en `/gestion/comisiones`**
    - Archivo: `app/gestion/comisiones/page.jsx` (modificar)
    - Query: `GET /api/comisiones_generadas?estado={estado}&asesor_id={asesor_id}`
    - Tabla con columnas:
      - ID, Caso (link), Cliente, Asesor, Tarifa, Comisión €, Estado, Fecha prevista pago
    - Filtros: Estado (dropdown), Asesor (dropdown), Fecha creación (date range)
    - Acciones:
      - Ver detalle (modal con repartos)
      - Marcar como validada (solo CEO)
      - Marcar como pagada (solo CEO, modal con fecha pago)

12. **Modal de repartos en comisión**
    - Cuando CEO hace clic en "Ver detalle" de comisión:
    - Modal muestra:
      - Comisión total
      - Tabla de repartos:
        - Destinatario (nombre), Tipo (asesor/CEO/colaborador), Importe €, %, Estado pago
      - Total repartido (debe = comisión total)
      - Botón "Marcar todos como pagados" (batch update)

13. **Pantalla `/gestion/pagos`**
    - Archivo: `app/gestion/pagos/page.jsx` (crear)
    - Tab 1: "Pendientes"
      - Query: `GET /api/repartos_comision?estado_pago=pendiente`
      - Tabla: Comisión ID, Caso, Cliente, Destinatario, Importe, Fecha prevista
      - Acción: Marcar como pagado (modal con fecha pago + nota)
    - Tab 2: "Pagados"
      - Query: `GET /api/repartos_comision?estado_pago=pagado`
      - Tabla: Comisión ID, Caso, Destinatario, Importe, Fecha pago
      - Solo lectura

14. **Sistema de alertas básico**
    - Backend:
      - Crear endpoint `GET /api/alertas`
      - Queries:
        - Ofertas sin comisión: `SELECT * FROM facturas WHERE selected_oferta_id IS NOT NULL AND id NOT IN (SELECT factura_id FROM comisiones_generadas)`
        - Comisiones estancadas: `SELECT * FROM comisiones_generadas WHERE estado='validada' AND created_at < NOW() - INTERVAL '30 days'`
        - Casos estancados: `SELECT * FROM casos WHERE estado_comercial NOT IN ('activo', 'baja', 'cancelado', 'perdido') AND updated_at < NOW() - INTERVAL '7 days'`
      - Respuesta: Lista de alertas con tipo, mensaje, link a acción
    - Frontend:
      - Badge en header con número de alertas
      - Dropdown con lista de alertas
      - Click en alerta → Redirige a acción

15. **Endpoints de repartos**
    - `GET /api/repartos_comision` → Listar repartos (filtros: estado_pago, user_id, colaborador_id)
    - `PUT /api/repartos_comision/{id}` → Actualizar reparto (marcar como pagado)
    - `POST /api/repartos_comision/batch_pago` → Marcar múltiples repartos como pagados

**PRIORIDAD 3: Audit logs y mejoras UX (1 semana)**

16. **Audit logs globales**
    - Crear tabla `audit_logs`:
      - id, company_id, user_id, entity_type, entity_id, action, old_value, new_value, created_at
    - Trigger en SQLAlchemy:
      - Después de INSERT/UPDATE/DELETE en tablas sensibles
      - Registrar cambio en `audit_logs`
    - Endpoint: `GET /api/audit_logs` (solo dev/CEO)
    - Frontend: `/gestion/auditoria` (solo dev)

17. **Anonimización al eliminar clientes (RGPD)**
    - Modificar: `DELETE /clientes/{id}`
    - En vez de hard delete:
      - Soft delete: `deleted_at = NOW()`
      - Anonimizar: `nombre = "Cliente eliminado #{id}"`, `email = null`, `telefono = null`, `dni = null`
      - Mantener `cups` para integridad referencial
    - Endpoint adicional: `DELETE /clientes/{id}/hard` (solo dev, con confirmación)

18. **Filtro de estado con badges de color**
    - Frontend: `/gestion/casos`
    - Badges con colores según estado:
      - `lead`: gris
      - `contactado`: azul claro
      - `en_estudio`: azul
      - `propuesta_enviada`: amarillo
      - `negociacion`: naranja
      - `firmado`: verde claro
      - `activo`: verde
      - `perdido`: rojo
      - `cancelado`: gris oscuro
    - Aplicar en:
      - Tabla de casos
      - Detalle de caso (badge grande)

19. **Paginación y ordenamiento en tablas**
    - Backend:
      - Todos los endpoints de listado deben aceptar: `skip`, `limit`, `order_by`, `order_dir`
      - Ejemplo: `GET /api/casos?skip=50&limit=50&order_by=created_at&order_dir=desc`
    - Frontend:
      - Componente reutilizable `<Pagination>`
      - Componente reutilizable `<Table>` con ordenamiento por columna
      - Aplicar en: Casos, Comisiones, Colaboradores, Clientes

20. **Sistema de tareas básico (futuro)**
    - Crear tabla `tareas`:
      - id, company_id, caso_id, user_id, tipo, descripcion, fecha_vencimiento, completada, created_at
    - Tipos:
      - `revision_10_meses` (automática)
      - `llamar_cliente` (manual)
      - `enviar_documento` (manual)
    - Trigger: Cuando caso → `activo`, crear tarea `revision_10_meses` con `fecha_vencimiento = fecha_activacion + 10 meses`
    - Endpoint: `GET /api/tareas?user_id={user_id}&completada=false`
    - Frontend:
      - Badge en header con número de tareas pendientes
      - Pantalla `/gestion/tareas` (listado con filtros)
      - Card "Tareas" en detalle de caso

---

## 📚 DOCUMENTOS TÉCNICOS CLAVE PARA CONSULTAR

- **README.md** → Stack, despliegue, configuración local
- **INFORME_PANEL_CEO_COMPLETO.md** → Especificación completa panel CEO (KPIs, queries SQL, wireframes)
- **INFORME_ANALISIS_CONCEPTUAL_CRM.md** → Flujo end-to-end, módulos funcionales, modelo de negocio
- **QA_AUDIT_REPORT_20260202.md** → Auditoría de precisión OCR, problemas detectados
- **STEP2_IMPLEMENTACION.md** → Especificación completa de validación comercial (STEP 2)
- **PLAN_96_PERCENT.md** → Plan para mejorar OCR de 71% a 96% precisión
- **DEPLOY_COMPLETADO.md** → Estado de despliegue, mejoras OCR, checklist
- **app/db/models.py** → Modelos SQLAlchemy (tablas principales)
- **app/db/models_casos.py** → Modelos de gestión (Caso, HistorialCaso)
- **app/services/comparador.py** → Motor de cálculo de comparativas (fórmulas PO)
- **app/services/ocr.py** → Extracción de datos con Vision API
- **app/services/pdf_generator.py** → Generación de estudios en PDF
- **app/services/validacion_comercial.py** → STEP 2: Validación de ajustes comerciales

---

## 🎯 RESUMEN EJECUTIVO (PARA OTRO ASISTENTE)

### Qué es
CRM/SaaS para asesorías energéticas que automatiza:
1. Extracción de datos de facturas PDF (OCR)
2. Comparación de tarifas eléctricas
3. Generación de estudios en PDF
4. Gestión de pipeline comercial
5. Control de comisiones

### Stack
- Frontend: Next.js 14 + React 18 + TailwindCSS + Chart.js (Vercel)
- Backend: FastAPI + SQLAlchemy + Python 3.10+ (Render)
- DB: PostgreSQL en Neon (producción), SQLite (local)
- OCR: Google Vision + GPT-4o Vision
- PDF: ReportLab

### Estado actual
- ✅ Wizard 3 pasos funcional (subir → validar → comparar)
- ✅ OCR 71% precisión (objetivo 96%)
- ✅ Comparador con fórmulas validadas
- ✅ STEP 2 (validación comercial) implementado
- ✅ Multi-tenant (companies, roles, permisos básicos)
- ✅ CRUD casos, clientes, colaboradores
- ⏳ Panel CEO parcialmente implementado
- ❌ Comisiones NO se generan automáticamente
- ❌ Split de comisiones NO implementado
- ❌ Estadísticas/KPIs NO implementados
- ❌ Sistema de tareas/alertas NO implementado

### Prioridad absoluta
1. Generar comisiones automáticamente cuando caso → `activo`
2. Implementar split de comisiones (asesor/CEO/colaborador)
3. Endpoint estadísticas CEO + frontend `/gestion/resumen`
4. Completar pantallas de gestión (comisiones, pagos)
5. Mejorar OCR (direcciones, localidades → 96%)

### No tocar
- Stack tecnológico (Next.js + FastAPI + Neon)
- Wizard de 3 pasos
- Fórmulas del comparador
- Estructura de tablas principales
- Header horizontal (no sidebar)

### Contacto
- CEO/Product Owner: DESCONOCIDO (verificar en CREDENCIALES_PRUEBA.md o similar)
- Repositorio: https://github.com/ismaelz001/RapidEnergy.git

---

**FIN DEL DOCUMENTO**

Este documento debe ser suficiente para que otro asistente pueda continuar el desarrollo sin preguntas. Si falta algo, está marcado como "DESCONOCIDO" y debe consultarse con el CEO o verificarse en el código/base de datos directamente.
