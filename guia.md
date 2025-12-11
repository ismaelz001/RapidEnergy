# RapidEnergy — Guía de Proyecto, Estado Actual y Plan de Acción

Este documento sirve como guía única del proyecto RapidEnergy. Resume qué se ha construido, qué falta, prioridades, y cómo avanzar sin perder el foco. Es el documento maestro de referencia para el desarrollo del MVP.

---

# 🟦 1. OBJETIVO PRINCIPAL DEL PROYECTO

Construir una plataforma web que automatice el negocio energético:

1. Subir factura (PDF/imagen)
2. Leerla automáticamente (OCR)
3. Extraer datos relevantes (CUPS, consumo, importe…)
4. Comparar proveedores y seleccionar la mejor oferta
5. Generar contrato y enviarlo para alta
6. Registrar comisiones y gestionar clientes
7. Panel CRM completo para comerciales

Todo accesible desde web (no app de momento).

---

# 🟩 2. ESTADO ACTUAL DEL PROYECTO

## ✔️ 2.1. Infraestructura
- Frontend → Next.js 14 (Vercel)
- Backend → FastAPI (Render)
- Base de datos → Neon PostgreSQL

## ✔️ 2.2. Backend
- FastAPI estructurado y funcionando
- Endpoint `/` operativo
- Endpoint `/webhook/upload` creado (sin OCR real aún)
- Conexión Neon lista (archivo conn.py correcto)
- Proyecto ya desplegado en Render

## ✔️ 2.3. Frontend
- Dashboard funcional
- Subida de factura con envío al backend
- Tabla de facturas lista para conectar
- Estilo SaaS con Tailwind
- Arquitectura preparada para features futuras

## ✔️ 2.4. Repositorios
- Backend subido a GitHub
- Frontend subido a GitHub
- Deploys activos

## ✔️ 2.5. Documentación
- README backend listo
- README frontend listo
- Este archivo → guía general del proyecto

---

# 🟥 3. QUÉ FALTA (LISTA CRÍTICA)

## 🔥 Backend (prioridad alta)
1. Crear modelo `Factura` en SQLAlchemy
2. Crear tabla en Neon
3. Guardar facturas al subirlas
4. Endpoint `GET /facturas`
5. Conectar frontend a BD real
6. Implementar OCR REAL
7. Parsing de datos energéticos

## 🟧 Backend (futuro inmediato)
8. Algoritmo comparador de tarifas
9. Modelo `Cliente`
10. Modelo `Contrato`
11. Módulo de comisiones
12. Envío de contratos a proveedores

## 🟨 Frontend
13. UI de facturas reales conectada
14. Vista detalle factura
15. Vista cliente
16. Vista ofertas
17. Panel de comisiones

---

# 🟦 4. PLAN DE ACCIÓN — SPRINTS

## 🔵 **SPRINT 1 — Backend funcional mínimo (3–5 días)**
- Crear modelo `Factura` en SQLAlchemy
- Crear migración / tabla en Neon
- Guardar factura en BD tras subida
- Implementar OCR básico (CUPS, consumo, importe)
- Endpoint `GET /facturas`
- Probar integración backend ↔ frontend

**Resultado:**  
Backend funcional que almacena facturas reales y las devuelve al frontend.

---

## 🔵 **SPRINT 2 — Frontend conectado a datos reales (2–3 días)**
- Conectar tabla `/facturas` a endpoint real
- Mostrar datos parseados en UI
- Mejorar página de subida
- Implementar estados (cargando, error, éxito)

**Resultado:**  
Frontend mostrando facturas reales desde Neon.

---

## 🔵 **SPRINT 3 — Comparador de tarifas (5–7 días)**
- Base de datos interna de tarifas (mock)
- Cálculo automático según consumo
- Reglas básicas por proveedor
- Generación de propuesta para cliente

**Resultado:**  
RapidEnergy genera automáticamente una oferta energética realista.

---

## 🔵 **SPRINT 4 — Gestión de clientes y contratos (7–10 días)**
- Modelo `Cliente`
- Modelo `Contrato`
- Enlace factura → cliente
- Generación de documento de contrato
- Envío por email/WhatsApp
- Registro de comisiones básicas

**Resultado:**  
Primera versión del CRM energético completo.

---

# 🟦 5. ROADMAP GENERAL

## Fase 1 — MVP Técnico
- OCR
- Guardado BD
- Comparador
- UI básica
- Flujo factura → oferta

## Fase 2 — CRM Comercial
- Clientes
- Contratos
- Comisiones
- Historial de cambios
- Estados por proveedor

## Fase 3 — Automatización
- Envío automático a comercializadoras
- Firma digital
- Notificaciones a clientes
- Pipeline automático de onboarding

## Fase 4 — Producto SaaS
- Multiusuario
- Panel administrador
- Varios equipos comerciales
- API propia para integradores

---

# 🟦 6. PRIORIZACIÓN ACTUAL (LO QUE TOCA AHORA MISMO)

1. Crear tabla Factura en Neon  
2. Crear modelo SQLAlchemy  
3. Guardar datos al subir factura  
4. Hacer OCR real  
5. Mostrar facturas reales en el frontend  

Hasta que esto no esté hecho, NO avanzamos al comparador ni al CRM.

---

# 🟧 7. MÉTRICAS DE ÉXITO DEL MVP

- Subo factura → se procesa sin fallos  
- Datos clave extraídos correctamente  
- Se almacenan en Neon  
- Puedo ver listado de facturas reales  
- Panel web usable para demos  

Si esto funciona → estamos listos para monetizar con comerciales pequeños.

---

# 🟢 8. SIGUIENTE ACCIÓN INMEDIATA

Implementar **modelo Factura + endpoint GET /facturas** y conectarlo al frontend.

---

# 📞 Contacto y propiedad

RapidEnergy — Proyecto MVP de automatización energética  
Arquitectura: FastAPI + Next.js + Neon + Render

