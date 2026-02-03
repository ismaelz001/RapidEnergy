# 📋 ANÁLISIS Y PROPUESTA: PANEL CEO - EnergyLuz CRM

## 1️⃣ MAPA DE LA ESTRUCTURA ACTUAL

### Arquitectura detectada
- **Frontend:** Next.js 13+ (App Router)
- **Backend:** FastAPI + PostgreSQL (Neon)
- **Rutas existentes:**
  - `/` → Landing redirect
  - `/dashboard` → Panel principal con tabs (casos, tarifas, comisiones)
  - `/clientes` → Listado de clientes
  - `/facturas` → Gestión de facturas procesadas
  - `/wizard/[id]/step-1-factura` → Subir factura
  - `/wizard/[id]/step-2-validar` → Validación de datos
  - `/wizard/[id]/step-3-comparar` → Comparación de ofertas

### Navegación actual (Header horizontal)
```
[Logo EnergyLuz] | Dashboard | Clientes | Facturas | [+ Nueva Factura]
```

### Jerarquía de roles identificada
| Rol | Descripción | Acceso actual |
|-----|-------------|---------------|
| `dev` | Desarrollador/Super-admin | Sin restricciones (no asociado a company) |
| `ceo` | Director/Gestor de compañía | Acceso total a su company |
| `manager` | Gerente de equipo | (rol preparado, sin uso actual) |
| `comercial` | Asesor energético | Acceso limitado a sus clientes |

### 🔥 SISTEMA DE COMISIONES (YA IMPLEMENTADO PARCIALMENTE)

#### ✅ Lo que ya funciona:

**1. Configuración de comisiones por tarifa:**
- Tabla: `comisiones_tarifa`
- Endpoint: `POST /webhook/comisiones/upload` (CSV/Excel)
- Versionado temporal: `vigente_desde` / `vigente_hasta`
- Lógica: Cierra versión anterior automáticamente

**2. Comisiones custom por cliente:**
- Tabla: `comisiones_cliente`
- Prioridad superior a `comisiones_tarifa`
- Sin versionado (última por `created_at`)

**3. Cálculo automático en comparador:**
- Archivo: `app/services/comparador.py`
- Prefetch optimizado (evita N+1 queries)
- Persiste en: `ofertas_calculadas.comision_eur` + `comision_source`
- Source tracking: `tarifa` | `cliente` | `manual`

**4. Selección de oferta:**
- Endpoint: `POST /facturas/{id}/seleccion`
- Guarda FK: `facturas.selected_oferta_id` → `ofertas_calculadas.id`

#### ❌ Lo que falta implementar:

**5. Registro de comisiones generadas:**
- Tabla: `comisiones_generadas` (EXISTE pero no se usa)
- Campos: `factura_id`, `cliente_id`, `asesor_id`, `tarifa_id`, `oferta_id`, `comision_total_eur`, `estado`, `fecha_prevista_pago`
- Estados: `pendiente` → `validada` → `pagada` → `anulada`
- **FALTA:** Trigger/endpoint que cree registro cuando se selecciona oferta

**6. Sistema de repartos:**
- Tabla: `repartos_comision` (EXISTE pero no se usa)
- Divide comisión entre: Asesor / CEO / Colaborador externo
- Porcentajes configurables por destinatario
- **FALTA:** Lógica de split + endpoints

**7. Gestión de colaboradores:**
- Tabla: `colaboradores` (EXISTE)
- Multi-tenant por `company_id`
- Pueden recibir % de comisión sin ser users
- **FALTA:** CRUD completo

**8. Control de pagos:**
- Campo: `comisiones_generadas.fecha_pago`
- **FALTA:** Endpoint para marcar como pagada

**9. Estadísticas agregadas:**
- **FALTA:** Endpoint `/api/stats/ceo` con KPIs

### ❌ LO QUE FUNCIONA BIEN (NO TOCAR)
1. **Flujo wizard de 3 pasos** - Es el core del producto
2. **Header horizontal** - Navegación clara y espaciosa
3. **Sistema de cards** - Diseño consistente y limpio
4. **Paleta de colores** - Azul `#0073EC`, fondos dark, bordes sutiles
5. **Tabs en Dashboard** - Ya hay espacio reservado para "comisiones"
6. **Cálculo de comisiones** - Prefetch optimizado, source tracking perfecto

---

## 2️⃣ PROPUESTA DE ENCAJE DEL PANEL CEO

### 🎯 Ubicación en la navegación

**OPCIÓN RECOMENDADA: Añadir al header horizontal**

```
[Logo] | Dashboard | Clientes | Facturas | Gestión | [+ Nueva Factura]
                                            ↑
                                         NUEVO
```

**Rutas propuestas:**
```
/gestion → Landing (Redirect a /gestion/resumen)
/gestion/resumen → Dashboard ejecutivo con KPIs
/gestion/comisiones → Configuración + historial
/gestion/colaboradores → Asesores + colaboradores externos
/gestion/pagos → Control de comisiones pendientes/pagadas
```

### 📝 Copy del menú

| Antes | Después | Razón |
|-------|---------|-------|
| "Administración" ❌ | "Gestión" ✅ | Más cercano, menos corporativo |
| "Panel CEO" ❌ | "Gestión" ✅ | No mencionar roles en UI |
| "Configuración" ❌ | "Gestión" ✅ | Ya implica negocio, no ajustes técnicos |
| "Comisiones" ❌ | Dentro de "Gestión" ✅ | Agrupa funcionalidades admin |

### 🔐 Control de acceso en header

```javascript
// En app/layout.js línea 45+
const userRole = getUserRole(); // Función ficticia

<nav className="flex items-center gap-6">
  <a href="/dashboard">Dashboard</a>
  <a href="/clientes">Clientes</a>
  <a href="/facturas">Facturas</a>
  
  {/* 🆕 SOLO PARA CEO Y DEV */}
  {(userRole === 'ceo' || userRole === 'dev') && (
    <a href="/gestion">Gestión</a>
  )}
  
  <a href="/wizard/new/step-1-factura" className="btn-primary">
    + Nueva Factura
  </a>
</nav>
```

---

## 3️⃣ DISEÑO FUNCIONAL DE PANTALLAS

### 🏠 PANTALLA 1: `/gestion/resumen`

**Objetivo:** Vista ejecutiva en 10 segundos

**Componentes:**
```
┌─────────────────────────────────────────────┐
│ 📊 Resumen Ejecutivo                        │
├─────────────────────────────────────────────┤
│ [KPI Card] [KPI Card] [KPI Card] [KPI Card]│
│                                             │
│ Facturas     Ahorro      Comisiones  Asesores │
│ procesadas   generado    pendientes  activos  │
│    45         €12.4K      €890        3       │
│                                             │
│ 📈 Evolución últimos 30 días                │
│ [Gráfico líneas: Facturas, Ahorro, Comisión]│
│                                             │
│ 🔥 Actividad reciente (últimas 5)           │
│ • Factura #321 procesada - Ahorro €450      │
│ • Comisión #12 validada - Asesor Juan       │
│ • Oferta seleccionada - Cliente ACME SA     │
│                                             │
│ ⚠️  Alertas críticas                         │
│ • 3 ofertas seleccionadas sin comisión      │
│ • 2 comisiones validadas hace +30 días      │
└─────────────────────────────────────────────┘
```

**Datos (queries SQL necesarias):**
```sql
-- KPI 1: Facturas procesadas total
SELECT COUNT(*) FROM facturas WHERE estado_factura IN ('lista_para_comparar', 'oferta_seleccionada');

-- KPI 2: Ahorro total generado (suma de ofertas seleccionadas)
SELECT COALESCE(SUM(oc.ahorro_anual), 0) 
FROM facturas f
JOIN ofertas_calculadas oc ON f.selected_oferta_id = oc.id
WHERE f.selected_oferta_id IS NOT NULL;

-- KPI 3: Comisiones pendientes de pago
SELECT COALESCE(SUM(comision_total_eur), 0)
FROM comisiones_generadas
WHERE estado IN ('pendiente', 'validada');

-- KPI 4: Asesores activos
SELECT COUNT(*) FROM users WHERE role = 'comercial' AND is_active = true;

-- ALERTA: Ofertas sin comisión generada
SELECT COUNT(*) 
FROM facturas 
WHERE selected_oferta_id IS NOT NULL 
  AND id NOT IN (SELECT factura_id FROM comisiones_generadas);
```

**Acciones:**
- Links rápidos: "Ver todas las facturas" → `/facturas`
- "Revisar comisiones pendientes" → `/gestion/pagos?estado=pendiente`

**Roles:** `ceo`, `dev`

---

### 💰 PANTALLA 2: `/gestion/comisiones`

**Objetivo:** Configurar comisiones a 3 niveles: Tarifa general, Cliente específico, Historial

**Componentes:**
```
┌─────────────────────────────────────────────┐
│ 💸 Configuración de Comisiones              │
├─────────────────────────────────────────────┤
│ TABS: [General] [Por Cliente] [Historial]  │
│                                             │
│ === TAB 1: GENERAL (comisiones_tarifa) === │
│ [📤 Subir CSV/Excel]                        │
│   └─> Formato: tarifa_id, comision_eur,    │
│                 vigente_desde, vigente_hasta│
│                                             │
│ 📊 Comisiones activas por tarifa            │
│ [Filtros: Comercializadora | ATR]          │
│ ┌─────┬──────────────┬───────┬────────────┐│
│ │ ID  │ Tarifa       │ €/mes │ Vigencia   ││
│ ├─────┼──────────────┼───────┼────────────┤│
│ │ 45  │ Iberdrola 2.0│ 15.00 │ Desde 01/01││
│ │ 46  │ Endesa One   │ 18.50 │ Desde 15/01││
│ └─────┴──────────────┴───────┴────────────┘│
│                                             │
│ === TAB 2: POR CLIENTE (comisiones_cliente)│
│ [+ Añadir override]                         │
│   └─> Modal: Seleccionar cliente + tarifa  │
│                                             │
│ 📋 Overrides activos (prioridad sobre general)│
│ ┌────────────┬──────────────┬───────┐      │
│ │ Cliente    │ Tarifa       │ €/mes │      │
│ ├────────────┼──────────────┼───────┤      │
│ │ ACME SA    │ Iberdrola 2.0│ 20.00 │ [X] ││
│ └────────────┴──────────────┴───────┘      │
│                                             │
│ === TAB 3: HISTORIAL ===                    │
│ Versiones anteriores cerradas (vigente_hasta≠NULL)│
│ ┌─────┬──────────┬───────┬───────┬────────┐│
│ │ ID  │ Tarifa   │ €/mes │ Desde │ Hasta  ││
│ ├─────┼──────────┼───────┼───────┼────────┤│
│ │ 12  │ Endesa   │ 12.00 │ 01/23 │ 12/23  ││
│ └─────┴──────────┴───────┴───────┴────────┘│
└─────────────────────────────────────────────┘
```

**Acciones:**
- **Subir CSV** → Endpoint ya existe: `POST /webhook/comisiones/upload`
- **Validar preview** → Mostrar filas antes de confirmar
- **Añadir override cliente** → Crear registro en `comisiones_cliente`
- **Eliminar override** → DELETE (soft con fecha)

**Backend:**
- ✅ Ya existe: `POST /webhook/comisiones/upload`
- ✅ Ya existe: `GET /webhook/comisiones/` (listar)
- ❌ Falta: `POST /api/comisiones/cliente` (crear override)
- ❌ Falta: `DELETE /api/comisiones/cliente/{id}` (eliminar override)

**Roles:** `ceo`, `dev`

---

### 👥 PANTALLA 3: `/gestion/colaboradores`

**Objetivo:** Gestionar 2 tipos: Asesores (users) + Colaboradores externos (no-users)

**Componentes:**
```
┌─────────────────────────────────────────────┐
│ 👤 Equipo y Colaboradores                   │
├─────────────────────────────────────────────┤
│ TABS: [Asesores] [Colaboradores Externos]  │
│                                             │
│ === TAB 1: ASESORES (users.role=comercial)│
│ [+ Añadir Asesor]                           │
│                                             │
│ 📊 Asesores activos                         │
│ ┌─────────────────────────────────────────┐│
│ │ 🟢 Juan Pérez                            ││
│ │ juan@energyluz.com                      ││
│ │ 12 clientes | €1,240 en comisiones      ││
│ │ [Ver detalle] [Desactivar]              ││
│ └─────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────┐│
│ │ 🟢 María López                           ││
│ │ maria@energyluz.com                     ││
│ │ 8 clientes | €890 en comisiones         ││
│ │ [Ver detalle] [Desactivar]              ││
│ └─────────────────────────────────────────┘│
│                                             │
│ 🔴 Asesores inactivos (colapsado)          │
│                                             │
│ === TAB 2: COLABORADORES EXTERNOS ===       │
│ [+ Añadir Colaborador]                      │
│                                             │
│ 📋 Colaboradores (sin acceso al sistema)   │
│ ┌───────────────┬──────────────┬─────────┐ │
│ │ Nombre        │ Contacto     │ Comis.  │ │
│ ├───────────────┼──────────────┼─────────┤ │
│ │ Pedro García  │ 600123456    │ €350    │ │
│ │ Ana Martín    │ ana@ext.com  │ €120    │ │
│ └───────────────┴──────────────┴─────────┘ │
└─────────────────────────────────────────────┘
```

**Acciones:**
- **Crear asesor:** INSERT en `users` con `role='comercial'`
- **Desactivar asesor:** UPDATE `is_active=false` (no DELETE)
- **Ver detalle:** Modal con clientes asignados + comisiones del periodo
- **Crear colaborador:** INSERT en `colaboradores`

**Backend a crear:**
```python
# app/routes/users.py (NUEVO)
POST   /api/users → Crear user con role=comercial
PATCH  /api/users/{id} → Actualizar is_active, name, email
GET    /api/users/{id}/stats → {clientes_count, comisiones_pendientes, comisiones_pagadas}

# app/routes/colaboradores.py (NUEVO)
POST   /api/colaboradores → Crear colaborador externo
GET    /api/colaboradores → Listar por company_id
PATCH  /api/colaboradores/{id} → Actualizar datos
DELETE /api/colaboradores/{id} → Soft delete
```

**Roles:** `ceo`, `dev`

---

### 💳 PANTALLA 4: `/gestion/pagos`

**Objetivo:** Gestionar comisiones desde estado pendiente hasta pagada

**Componentes:**
```
┌─────────────────────────────────────────────┐
│ 💳 Control de Comisiones y Pagos            │
├─────────────────────────────────────────────┤
│ FILTROS: [Pendientes: 12] [Validadas: 8]   │
│          [Pagadas: 45] [Anuladas: 2]        │
│                                             │
│ 📊 Comisiones por estado                    │
│ ┌────────┬──────────┬────────┬───────┬─────┐│
│ │Factura │Cliente   │Asesor  │€Total │Estado│
│ ├────────┼──────────┼────────┼───────┼─────┤│
│ │#321    │ACME SA   │Juan P. │450.00 │[Validar]││
│ │#318    │Energías X│María L.│320.50 │[Pagar]  ││
│ │#315    │Corp Ltd  │Juan P. │180.00 │Pagada   ││
│ └────────┴──────────┴────────┴───────┴─────┘│
│                                             │
│ CLIC EN FILA → Modal detalle:               │
│ ┌─────────────────────────────────────────┐│
│ │ Factura #321 - ACME SA                  ││
│ │                                         ││
│ │ Oferta seleccionada: Iberdrola 2.0 TD   ││
│ │ Ahorro anual: €540                      ││
│ │ Comisión total: €450 (source: tarifa)   ││
│ │                                         ││
│ │ 💰 Reparto:                              ││
│ │ • Asesor (Juan P.): €300 (67%)          ││
│ │ • CEO: €100 (22%)                       ││
│ │ • Colaborador (María): €50 (11%)        ││
│ │                                         ││
│ │ [Validar comisión] [Marcar como pagada] ││
│ └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

**Flujo de estados:**
```
pendiente → validada → pagada
    ↓                      ↓
  anulada              anulada
```

**Acciones:**
- **Validar:** `estado = 'validada'` (aprobación CEO)
- **Marcar como pagada:** `estado = 'pagada'`, `fecha_pago = NOW()`
- **Anular:** `estado = 'anulada'` (con motivo)
- **Ver reparto:** Consultar `repartos_comision` (si existe)

**Backend a crear:**
```python
# app/routes/comisiones_generadas.py (NUEVO)
GET    /api/comisiones → Listar con filtros (estado, asesor_id, fecha)
GET    /api/comisiones/{id} → Detalle + repartos
PATCH  /api/comisiones/{id}/validar → estado='validada'
PATCH  /api/comisiones/{id}/pagar → estado='pagada', fecha_pago
PATCH  /api/comisiones/{id}/anular → estado='anulada'

# ⭐ CRÍTICO: Trigger automático
# Crear comisiones_generadas cuando facturas.selected_oferta_id se actualiza
```

**Roles:** `ceo`, `dev`

---

## 4️⃣ PRIORIZACIÓN

### P0 - IMPLEMENTAR AHORA (Sprint 1: 8-10h)

| Tarea | Esfuerzo | Impacto | Backend necesario |
|-------|----------|---------|-------------------|
| **1. Sistema auth básico** | 🟢 30min | Crítico | Hook `useAuth()` con localStorage |
| **2. Link "Gestión" en header** | 🟢 15min | Alto | Ninguno |
| **3. `/gestion/resumen` (KPIs)** | 🟡 2h | Alto | ✅ Solo queries (tablas existen) |
| **4. `/gestion/comisiones` UI** | 🟡 2h | Alto | ✅ Backend ya existe |
| **5. `/gestion/pagos` básico** | 🟡 2-3h | Alto | ❌ Crear endpoints `comisiones_generadas` |
| **6. Trigger auto comisión** | 🟡 1h | Crítico | ❌ Endpoint + lógica en selección |

**Total P0:** ~8-10 horas

**Dependencias críticas P0:**
```python
# app/routes/comisiones_generadas.py (NUEVO)
@router.post("/generar")
def generar_comision_desde_factura(factura_id: int):
    """Trigger manual o automático al seleccionar oferta"""
    # 1. Obtener factura + oferta seleccionada
    # 2. Extraer comision_eur de ofertas_calculadas
    # 3. INSERT en comisiones_generadas
    # 4. (Opcional) Crear repartos_comision automáticos
    
@router.get("/")
def listar_comisiones(estado: str = None, asesor_id: int = None):
    """Listar con filtros para /gestion/pagos"""
    
@router.patch("/{id}/validar")
def validar_comision(id: int):
    """estado = 'validada'"""
    
@router.patch("/{id}/pagar")
def marcar_pagada(id: int, fecha_pago: date = None):
    """estado = 'pagada', fecha_pago"""

# app/routes/stats.py (NUEVO)
@router.get("/ceo")
def get_ceo_stats(company_id: int = None):
    """KPIs para /gestion/resumen"""
    return {
        "facturas_procesadas": ...,
        "ahorro_total_eur": ...,
        "comisiones_pendientes_eur": ...,
        "asesores_activos": ...,
        "alertas": [...]
    }
```

---

### P1 - MEJORA POSTERIOR (Sprint 2: 6-8h)

| Tarea | Esfuerzo | Razón |
|-------|----------|-------|
| `/gestion/colaboradores` (users) | 🟡 2h | Gestión equipo |
| Colaboradores externos (tabla colaboradores) | 🟡 2h | Splits comisión |
| Sistema de repartos automáticos | 🟡 2-3h | Dividir comisión |
| Overrides comisión por cliente | 🟡 1h | Casos especiales |
| Gráficos en resumen | 🟢 1h | Mejora UX |

---

### P2 - OPTIMIZACIONES (Sprint 3+)

| Funcionalidad | Razón |
|---------------|-------|
| Notificaciones comisión generada | Email/SMS a asesor |
| Export Excel comisiones | Contabilidad |
| Historial de cambios | Auditoría |
| Reglas de reparto configurables | CEO configura % por rol |
| Dashboard por asesor | Self-service comerciales |

---

### ❌ NO METER AHORA (Fuera de scope)

| Funcionalidad | Razón |
|---------------|-------|
| Integración bancaria | Complejidad extrema |
| Facturación automática | Requiere validación legal |
| Sistema de anticipos | Lógica financiera compleja |
| Multi-moneda | No aplica (solo EUR) |
| Comisiones por cliente recurrente | YAGNI - modelo actual es one-time |

---

## 5️⃣ REGLAS UX CLARAS

### ❌ ANTI-PATRONES A EVITAR

| Anti-patrón | Por qué | Alternativa |
|-------------|---------|-------------|
| Sidebar lateral completo | Añade complejidad | Mantener header horizontal |
| Mega-menú dropdown en "Gestión" | Oculta opciones | Tabs dentro de `/gestion` |
| KPIs sin contexto | "€1,200" ¿es bueno? | Añadir vs. mes anterior: +15% ↑ |
| Tablas interminables sin paginación | Laggy en 100+ filas | Pagination + limit 20 por defecto |
| Modales anidados | Confuso | Max 1 nivel de modal |

### ✅ PRINCIPIOS DE SIMPLIFICACIÓN

1. **1 acción principal por pantalla**  
   Ej: En `/gestion/comisiones` → Subir CSV es lo único destacado

2. **Filtros colapsados por defecto**  
   Solo mostrar si hay +50 items

3. **Empty states con acción**  
   "No hay comisiones configuradas" → [Subir ahora]

4. **Feedback inmediato**  
   Upload CSV → Mostrar preview ANTES de confirmar

5. **Deshacer destructivo**  
   Si borras un comercial → Toast con "Deshacer" 5 seg

### 🎯 EVITAR SOBRECARGA AL CEO

| Problema | Solución |
|----------|----------|
| 50 notificaciones al día | Solo alertas críticas: "Tarifa sin comisión" |
| Muchos números sin acción | KPI debe tener link: "€450 pendientes" → Ver desglose |
| Gráficos sin insight | Añadir texto: "Tu mejor mes fue Enero (+€500)" |
| Decisiones técnicas en UI | No mostrar IDs de BD, usar nombres legibles |

---

## 6️⃣ IMPLEMENTACIÓN PASO A PASO

### Fase 1: Setup autenticación (30 min)

```javascript
// 🆕 lib/auth.js
export function getUserRole() {
  // TODO: Integrar con backend real
  // Por ahora hardcodear: return 'ceo';
  return localStorage.getItem('user_role') || 'comercial';
}

export function canAccessGestion(role) {
  return ['ceo', 'dev'].includes(role);
}
```

### Fase 2: Crear estructura de rutas (15 min)

```
app/
  gestion/
    page.jsx → Redirect a /gestion/resumen
    layout.jsx → Tabs: Resumen | Comisiones | Colaboradores
    resumen/
      page.jsx
    comisiones/
      page.jsx
    colaboradores/
      page.jsx
```

### Fase 3: Layout con tabs (1h)

```jsx
// app/gestion/layout.jsx
"use client";
import { useState } from 'react';
import { getUserRole, canAccessGestion } from '@/lib/auth';
import { useRouter } from 'next/navigation';

export default function GestionLayout({ children }) {
  const router = useRouter();
  const role = getUserRole();

  // 🔒 Protección de ruta
  if (!canAccessGestion(role)) {
    router.push('/dashboard');
    return null;
  }

  const tabs = [
    { id: 'resumen', label: 'Resumen', href: '/gestion/resumen' },
    { id: 'comisiones', label: 'Comisiones', href: '/gestion/comisiones' },
    { id: 'colaboradores', label: 'Colaboradores', href: '/gestion/colaboradores' },
  ];

  return (
    <div className="flex flex-col gap-8">
      {/* Tabs idénticos a dashboard/page.jsx línea 85-98 */}
      <div className="flex flex-col gap-6 border-b border-[rgba(255,255,255,0.08)]">
        <h1 className="text-3xl font-bold text-white tracking-tight">Gestión</h1>
        <div className="flex items-center gap-8 translate-y-[1px]">
          {tabs.map((tab) => (
            <a key={tab.id} href={tab.href} className="tab">
              {tab.label}
            </a>
          ))}
        </div>
      </div>
      {children}
    </div>
  );
}
```

### Fase 4: Pantalla resumen (2h)

```jsx
// app/gestion/resumen/page.jsx
"use client";
import { useEffect, useState } from 'react';

export default function ResumenPage() {
  const [kpis, setKpis] = useState(null);

  useEffect(() => {
    // TODO: Llamar a GET /api/stats/ceo
    setKpis({
      facturas_procesadas: 45,
      ahorro_total_eur: 12450,
      comision_pendiente_eur: 890,
      comerciales_activos: 3,
    });
  }, []);

  if (!kpis) return <div>Cargando...</div>;

  const kpiCards = [
    { label: 'Facturas procesadas', value: kpis.facturas_procesadas, icon: '📄' },
    { label: 'Ahorro generado', value: `€${kpis.ahorro_total_eur}`, icon: '💰' },
    { label: 'Comisión pendiente', value: `€${kpis.comision_pendiente_eur}`, icon: '⏳' },
    { label: 'Comerciales activos', value: kpis.comerciales_activos, icon: '👥' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {kpiCards.map((kpi, i) => (
        <div key={i} className="card">
          <div className="text-3xl mb-2">{kpi.icon}</div>
          <div className="text-2xl font-bold text-white">{kpi.value}</div>
          <div className="text-sm text-[#94A3B8]">{kpi.label}</div>
        </div>
      ))}
    </div>
  );
}
```

### Fase 5: Pantalla comisiones (1h)

```jsx
// app/gestion/comisiones/page.jsx
"use client";
import { useState } from 'react';

export default function ComisionesPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('https://rapidenergy.onrender.com/webhook/comisiones/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      alert(`✅ Importadas ${data.importados} comisiones`);
    } catch (err) {
      alert('❌ Error al subir archivo');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-bold text-white mb-4">Subir comisiones (CSV/Excel)</h3>
        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={(e) => setFile(e.target.files[0])}
          className="mb-4"
        />
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="btn-primary"
        >
          {uploading ? 'Subiendo...' : 'Cargar archivo'}
        </button>
      </div>

      <div className="card">
        <h3 className="text-lg font-bold text-white mb-4">Formato esperado</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-2">tarifa_id</th>
              <th className="text-left py-2">comision_eur</th>
              <th className="text-left py-2">vigente_desde</th>
              <th className="text-left py-2">vigente_hasta</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-white/5 text-[#94A3B8]">
              <td className="py-2">45</td>
              <td className="py-2">15.00</td>
              <td className="py-2">2026-01-01</td>
              <td className="py-2">2026-12-31</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## 📊 CHECKLIST DE IMPLEMENTACIÓN P0

### Backend (4-5h)

```
□ Crear app/routes/stats.py con endpoint GET /api/stats/ceo
  └─> Queries: facturas, ahorro, comisiones, asesores, alertas

□ Crear app/routes/comisiones_generadas.py con:
  └─> POST /api/comisiones/generar (trigger automático)
  └─> GET /api/comisiones (listar con filtros)
  └─> PATCH /api/comisiones/{id}/validar
  └─> PATCH /api/comisiones/{id}/pagar
  └─> GET /api/comisiones/{id} (detalle + repartos)

□ Modificar POST /facturas/{id}/seleccion
  └─> Añadir llamada automática a generar_comision_desde_factura()

□ Registrar routers en app/main.py
  └─> app.include_router(stats_router)
  └─> app.include_router(comisiones_generadas_router)

□ Testear endpoints con curl/Postman
```

### Frontend (4-5h)

```
□ Crear lib/auth.js con getUserRole() + canAccessGestion()
  └─> Hardcode temporal: return 'ceo'

□ Modificar app/layout.js
  └─> Añadir link "Gestión" con condicional role

□ Crear estructura app/gestion/
  ├─> layout.jsx (tabs + protección rol)
  ├─> page.jsx (redirect a /resumen)
  ├─> resumen/page.jsx (4 KPI cards + alertas)
  ├─> comisiones/page.jsx (upload CSV + tabla activas + tabs)
  └─> pagos/page.jsx (tabla filtrable + modal detalle)

□ Crear lib/apiClient.js funciones:
  └─> getCeoStats()
  └─> listComisiones(filtros)
  └─> validarComision(id)
  └─> marcarComisionPagada(id, fecha)

□ Revisar responsive mobile (col-span adaptativos)

□ Testear flujo completo CEO end-to-end
```

### Testing P0

```
□ Crear factura + seleccionar oferta → Ver comisión generada
□ Filtrar comisiones por estado en /gestion/pagos
□ Validar comisión → Ver cambio de estado
□ Marcar como pagada → Ver fecha_pago actualizada
□ Subir CSV comisiones → Ver nuevas tarifas activas
□ Verificar KPIs en /gestion/resumen reflejan cambios
□ Probar acceso con role='comercial' → Debe bloquear /gestion
□ Verificar links entre pantallas funcionan correctamente
```

---

## 🎯 RESULTADO ESPERADO P0

Después de implementar el P0 tendrás:

✅ **Panel CEO funcional** con navegación clara  
✅ **Comisiones automáticas** al seleccionar oferta  
✅ **Control de estados** pendiente → validada → pagada  
✅ **KPIs ejecutivos** en tiempo real  
✅ **Upload CSV operativo** (ya existía, solo UI)  
✅ **Protección por roles** sin autenticación completa  
✅ **Base sólida** para P1 (colaboradores, repartos)

**Tiempo estimado total:** 8-10 horas de desarrollo limpio.

---

## 📦 ANEXO: QUERIES SQL PARA IMPLEMENTACIÓN

### KPIs Dashboard (`/api/stats/ceo`)

```sql
-- 1. Facturas procesadas (que llegaron a comparar o tienen oferta)
SELECT COUNT(*) as facturas_procesadas
FROM facturas
WHERE estado_factura IN ('lista_para_comparar', 'oferta_seleccionada');

-- 2. Ahorro total generado (suma ofertas seleccionadas)
SELECT COALESCE(SUM(oc.ahorro_anual), 0) as ahorro_total_eur
FROM facturas f
JOIN ofertas_calculadas oc ON f.selected_oferta_id = oc.id
WHERE f.selected_oferta_id IS NOT NULL;

-- 3. Comisiones pendientes de pago (estado pendiente o validada)
SELECT 
    COUNT(*) as comisiones_pendientes_count,
    COALESCE(SUM(comision_total_eur), 0) as comisiones_pendientes_eur
FROM comisiones_generadas
WHERE estado IN ('pendiente', 'validada');

-- 4. Asesores activos (comerciales habilitados)
SELECT COUNT(*) as asesores_activos
FROM users
WHERE role = 'comercial' 
  AND is_active = true
  AND company_id = :company_id; -- Si es CEO filtrar por company

-- 5. ALERTA: Ofertas seleccionadas sin comisión generada
SELECT COUNT(*) as alertas_sin_comision
FROM facturas f
WHERE f.selected_oferta_id IS NOT NULL
  AND f.id NOT IN (SELECT factura_id FROM comisiones_generadas);

-- 6. Evolución últimos 30 días (para gráfico)
SELECT 
    DATE(created_at) as fecha,
    COUNT(*) as facturas_dia
FROM facturas
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
  AND estado_factura IN ('lista_para_comparar', 'oferta_seleccionada')
GROUP BY DATE(created_at)
ORDER BY fecha ASC;

-- 7. Actividad reciente (últimas 5 acciones)
SELECT 
    'factura' as tipo,
    f.id as referencia_id,
    c.nombre as detalle,
    f.created_at as fecha
FROM facturas f
LEFT JOIN clientes c ON f.cliente_id = c.id
WHERE f.estado_factura = 'oferta_seleccionada'
ORDER BY f.created_at DESC
LIMIT 5;
```

### Listar comisiones con filtros (`/api/comisiones`)

```sql
-- Query base con filtros opcionales
SELECT 
    cg.id,
    cg.factura_id,
    cg.cliente_id,
    c.nombre as cliente_nombre,
    cg.asesor_id,
    u.name as asesor_nombre,
    cg.comision_total_eur,
    cg.estado,
    cg.fecha_prevista_pago,
    cg.fecha_pago,
    cg.created_at,
    -- Datos de la tarifa
    t.nombre as tarifa_nombre,
    t.comercializadora,
    -- Ahorro de la oferta
    oc.ahorro_anual
FROM comisiones_generadas cg
JOIN clientes c ON cg.cliente_id = c.id
JOIN users u ON cg.asesor_id = u.id
JOIN tarifas t ON cg.tarifa_id = t.id
JOIN ofertas_calculadas oc ON cg.oferta_id = oc.id
WHERE 1=1
  -- Filtros opcionales
  AND (:estado IS NULL OR cg.estado = :estado)
  AND (:asesor_id IS NULL OR cg.asesor_id = :asesor_id)
  AND (:company_id IS NULL OR cg.company_id = :company_id)
  AND (:fecha_desde IS NULL OR cg.created_at >= :fecha_desde)
  AND (:fecha_hasta IS NULL OR cg.created_at <= :fecha_hasta)
ORDER BY cg.created_at DESC
LIMIT :limit OFFSET :offset;
```

### Detalle comisión con repartos (`/api/comisiones/{id}`)

```sql
-- Datos principales comisión
SELECT 
    cg.*,
    c.nombre as cliente_nombre,
    u.name as asesor_nombre,
    u.email as asesor_email,
    t.nombre as tarifa_nombre,
    t.comercializadora,
    f.cups,
    oc.ahorro_anual,
    oc.ahorro_mensual
FROM comisiones_generadas cg
JOIN clientes c ON cg.cliente_id = c.id
JOIN users u ON cg.asesor_id = u.id
JOIN tarifas t ON cg.tarifa_id = t.id
JOIN facturas f ON cg.factura_id = f.id
JOIN ofertas_calculadas oc ON cg.oferta_id = oc.id
WHERE cg.id = :comision_id;

-- Repartos asociados
SELECT 
    rc.id,
    rc.tipo_destinatario,
    rc.importe_eur,
    rc.porcentaje,
    rc.estado_pago,
    rc.fecha_pago,
    -- Si es user
    u.name as user_nombre,
    u.email as user_email,
    -- Si es colaborador
    col.nombre as colaborador_nombre,
    col.telefono as colaborador_telefono
FROM repartos_comision rc
LEFT JOIN users u ON rc.user_id = u.id
LEFT JOIN colaboradores col ON rc.colaborador_id = col.id
WHERE rc.comision_id = :comision_id
ORDER BY rc.importe_eur DESC;
```

### Generar comisión automáticamente (trigger)

```sql
-- Paso 1: Extraer datos de la oferta seleccionada
WITH oferta_data AS (
    SELECT 
        f.id as factura_id,
        f.cliente_id,
        f.selected_oferta_id,
        c.comercial_id as asesor_id,
        c.company_id,
        oc.tarifa_id,
        oc.comision_eur,
        oc.comision_source
    FROM facturas f
    JOIN clientes c ON f.cliente_id = c.id
    JOIN ofertas_calculadas oc ON f.selected_oferta_id = oc.id
    WHERE f.id = :factura_id
      AND f.selected_oferta_id IS NOT NULL
)
-- Paso 2: Insertar comisión generada
INSERT INTO comisiones_generadas (
    factura_id,
    cliente_id,
    company_id,
    asesor_id,
    oferta_id,
    tarifa_id,
    comision_total_eur,
    comision_source,
    estado,
    fecha_prevista_pago
)
SELECT 
    factura_id,
    cliente_id,
    company_id,
    asesor_id,
    selected_oferta_id,
    tarifa_id,
    comision_eur,
    comision_source,
    'pendiente',
    CURRENT_DATE + INTERVAL '30 days' -- Pago en 30 días
FROM oferta_data
ON CONFLICT DO NOTHING; -- Evitar duplicados
```

### Validar/Pagar comisión

```sql
-- Validar
UPDATE comisiones_generadas
SET estado = 'validada',
    updated_at = NOW()
WHERE id = :comision_id
  AND estado = 'pendiente';

-- Marcar como pagada
UPDATE comisiones_generadas
SET estado = 'pagada',
    fecha_pago = :fecha_pago,
    updated_at = NOW()
WHERE id = :comision_id
  AND estado = 'validada';

-- Anular
UPDATE comisiones_generadas
SET estado = 'anulada',
    updated_at = NOW()
WHERE id = :comision_id;
```

### Stats por asesor (`/api/users/{id}/stats`)

```sql
-- Resumen asesor
SELECT 
    u.id,
    u.name,
    u.email,
    COUNT(DISTINCT c.id) as clientes_count,
    COUNT(DISTINCT f.id) as facturas_procesadas,
    COALESCE(SUM(CASE WHEN cg.estado = 'pendiente' THEN cg.comision_total_eur ELSE 0 END), 0) as comisiones_pendientes,
    COALESCE(SUM(CASE WHEN cg.estado = 'validada' THEN cg.comision_total_eur ELSE 0 END), 0) as comisiones_validadas,
    COALESCE(SUM(CASE WHEN cg.estado = 'pagada' THEN cg.comision_total_eur ELSE 0 END), 0) as comisiones_pagadas,
    COALESCE(SUM(CASE WHEN cg.estado IN ('pendiente', 'validada', 'pagada') THEN cg.comision_total_eur ELSE 0 END), 0) as comisiones_total
FROM users u
LEFT JOIN clientes c ON c.comercial_id = u.id
LEFT JOIN facturas f ON f.cliente_id = c.id
LEFT JOIN comisiones_generadas cg ON cg.asesor_id = u.id
WHERE u.id = :user_id
GROUP BY u.id, u.name, u.email;
```

---

## 📦 RESUMEN EJECUTIVO PARA COPIAR/PEGAR

### Estructura actual
- CRM energético Next.js + FastAPI con 4 roles: dev/ceo/manager/comercial
- Navegación: Header horizontal (Dashboard | Clientes | Facturas)
- Sistema comisiones parcialmente implementado:
  - ✅ Upload CSV a `comisiones_tarifa` (versionado)
  - ✅ Cálculo automático en comparador → `ofertas_calculadas.comision_eur`
  - ❌ FALTA: Generación `comisiones_generadas` al seleccionar oferta
  - ❌ FALTA: Gestión pagos/estados
  - ❌ FALTA: Sistema repartos

### Propuesta
**Añadir sección "Gestión" al header** (visible solo para CEO/DEV) con:

1. **`/gestion/resumen`** → 4 KPIs + alertas críticas
2. **`/gestion/comisiones`** → 3 tabs: General (CSV) | Por cliente | Historial
3. **`/gestion/pagos`** → Tabla filtrable (pendiente/validada/pagada) + detalle repartos
4. **`/gestion/colaboradores`** → 2 tabs: Asesores (users) | Externos (colaboradores)

### Prioridad P0 (8-10h)

**Backend (4-5h):**
- `app/routes/stats.py` → GET /api/stats/ceo
- `app/routes/comisiones_generadas.py` → CRUD completo
- Trigger automático al seleccionar oferta

**Frontend (4-5h):**
- Hook `useAuth()` + protección rutas
- Layout `/gestion` con tabs
- 3 pantallas: resumen, comisiones, pagos
- Integración API

### Reglas UX
- ❌ NO sidebar, NO mega-menús, NO rediseñar existente
- ✅ Tabs horizontales, 1 acción/pantalla, empty states claros
- ✅ Mantener paleta actual (#0073EC, dark backgrounds)
- ✅ Aprovechar tablas `comisiones_generadas` y `repartos_comision` ya creadas

### Implementación
- Usar queries SQL del ANEXO para KPIs
- Reutilizar diseño de [dashboard/page.jsx](app/dashboard/page.jsx) para tabs
- Backend comisiones upload ya funciona: `/webhook/comisiones/upload`
- Comparador ya calcula comisiones correctamente en [comparador.py](app/services/comparador.py#L285-L390)
