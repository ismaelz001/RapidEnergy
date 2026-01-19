# ✅ CHECKLIST FINAL — PASOS PARA PRODUCCIÓN

## 🎯 OBJETIVO
Aplicar los últimos 2 fixes críticos y validar que el sistema esté 100% operativo.

---

## 📋 CHECKLIST DE ACCIÓN INMEDIATA

### **PASO 1: Aplicar Migración SQL** [5-10 min]

- [ ] Abrir **Neon Dashboard** (https://console.neon.tech)
- [ ] Seleccionar proyecto RapidEnergy
- [ ] Click en **SQL Editor**
- [ ] Copiar contenido de `migration_ofertas_calculadas.sql`
- [ ] Pegar y ejecutar
- [ ] Verificar: `SELECT COUNT(*) FROM ofertas_calculadas;` → debe retornar `0`
- [ ] ✅ **Tabla creada correctamente**

**Archivo a ejecutar**:
```
E:\MecaEnergy\migration_ofertas_calculadas.sql
```

---

### **PASO 2: Commit y Deploy** [10 min]

- [ ] Verificar cambios pendientes:
  ```bash
  git status
  ```

- [ ] Agregar archivos modificados:
  ```bash
  git add app/routes/webhook.py
  git add app/services/ocr.py
  git add app/services/comparador.py
  git add app/db/models.py
  git add migration_ofertas_calculadas.sql
  git add docs/
  git add audit_e2e_test.py
  git add RESUMEN_AUDIT_E2E.md
  ```

- [ ] Commit con mensaje claro:
  ```bash
  git commit -m "FIX: P0-1 periodo_dias | P1-1 iva_porcentaje | P2-1 logging | P0-2 ofertas_calculadas model"
  ```

- [ ] Push a producción:
  ```bash
  git push origin main
  ```

- [ ] Esperar deploy automático en Render (2-3 min)

- [ ] Verificar logs en Render Dashboard:
  - ✅ "Deployment successful"
  - ✅ No errores de importación

---

### **PASO 3: Validación Post-Deploy** [15 min]

#### **3A: Test Manual — Subir Factura PDF**

- [ ] Ir a https://energy.rodorte.com/wizard (frontend)
- [ ] Subir factura PDF de prueba (ej: `Factura.pdf`)
- [ ] Verificar que pasa a paso 2 sin errores
- [ ] En paso 2, verificar que `periodo_dias` esté visible
- [ ] Completar datos faltantes (si los hay)
- [ ] Click en "Comparar ofertas"
- [ ] ✅ Verificar que se generan 9 ofertas
- [ ] ✅ Verificar que cada oferta tiene detalle con `periodo_dias`

#### **3B: Test Backend — Verificar Persistencia**

- [ ] Abrir Neon SQL Editor
- [ ] Ejecutar:
  ```sql
  SELECT id, factura_id, created_at 
  FROM comparativas 
  ORDER BY created_at DESC 
  LIMIT 5;
  ```
- [ ] ✅ Verificar que hay comparativas recientes

- [ ] Ejecutar:
  ```sql
  SELECT c.id, COUNT(o.id) as num_ofertas
  FROM comparativas c
  LEFT JOIN ofertas_calculadas o ON c.id = o.comparativa_id
  WHERE c.created_at > NOW() - INTERVAL '1 hour'
  GROUP BY c.id;
  ```
- [ ] ✅ Verificar que cada comparativa tiene ~9 ofertas

#### **3C: Test Automatizado** (OPCIONAL)

- [ ] Ejecutar test E2E local:
  ```bash
  python audit_e2e_test.py
  ```
- [ ] ✅ Verificar que PDFs procesanexitosamente
- [ ] ⚠️ Verificar si JPGs ya funcionan (si no, OK para MVP)

---

### **PASO 4: Debug JPG (Si es necesario)** [1-2h]

**SOLO si el MVP requiere soporte JPG inmediato**

- [ ] Revisar logs Render:
  - Filtrar por "Vision" o "500"
  - Copiar traceback completo

- [ ] Verificar env vars en Render:
  - `GOOGLE_CREDENTIALS` existe?
  - `GEMINI_API_KEY` existe?

- [ ] **Fix temporal**: Forzar Gemini para JPG
  - Editar `app/services/ocr.py` línea 876
  - Cambiar Vision fallback por Gemini universal
  - Ver `docs/FIXES_PROPUESTOS.md` sección "CRITICAL: Vision API"

- [ ] Re-deploy y re-test con `f1.jpg`

---

## 🎯 CRITERIOS DE ÉXITO

### **Mínimo para MVP** (CORE):
- ✅ PDFs se suben correctamente
- ✅ periodo_dias se extrae y persiste
- ✅ Comparador genera 9 ofertas
- ✅ ofertas_calculadas se persisten en DB
- ✅ Frontend muestra ofertas con detalle

### **Nice to Have** (PLUS):
- ⚠️ JPGs se procesan (Vision API funciona)
- ⚠️ iva_porcentaje se extrae de facturas que lo muestran
- ⚠️ Logs detallados en producción

---

## 📊 STATUS TRACKING

### **Bugs Críticos (P0)**:
- [x] P0-1: periodo_dias → ✅ FIXED
- [ ] P0-2: ofertas_calculadas → 🟡 PENDIENTE MIGRACIÓN SQL
- [ ] P0-3: Fallback fechas → ⚠️ NO CRÍTICO (skip para MVP)
- [ ] P0-4: JPG Vision API → ⚠️ INVESTIGAR (skip si MVP solo PDF)

### **Bugs Graves (P1)**:
- [x] P1-1: iva_porcentaje → ✅ FIXED
- [x] P1-5: impuesto_electrico → ✅ YA FUNCIONABA
- [x] P1-6: alquiler_contador → ✅ YA FUNCIONABA

### **Mejoras (P2)**:
- [x] P2-1: Logging → ✅ FIXED

---

## 🚨 TROUBLESHOOTING

### **Error: "table ofertas_calculadas does not exist"**
→ No ejecutaste la migración SQL (PASO 1)

### **Error: "PERIOD_REQUIRED" al comparar**
→ El fix P0-1 no está deployed. Re-check PASO 2.

### **Error: JPG retorna 500**
→ Esperado. Ver PASO 4 o skip JPG para MVP.

### **No se muestran ofertas en frontend**
→ Verificar que `ofertas_calculadas` se llenó (PASO 3B)

---

## 📞 SOPORTE

**Si algo falla**:
1. Revisar logs en Render Dashboard
2. Consultar `docs/AUDIT_E2E_REPORT.md` → Sección "Repro Steps"
3. Consultar `docs/FIXES_PROPUESTOS.md` → Sección "Troubleshooting"
4. Ejecutar test local: `python audit_e2e_test.py`

---

## ✅ APROBACIÓN PARA PRODUCCIÓN

Una vez completados los pasos 1, 2 y 3:

- [ ] Migración SQL aplicada
- [ ] Deploy exitoso
- [ ] PDFs se procesan correctamente
- [ ] Comparador genera ofertas
- [ ] ofertas_calculadas se persisten

**ENTONCES**:

🎉 **SISTEMA APROBADO PARA PRODUCCIÓN MVP**

---

**Fecha**: 2026-01-19  
**Auditor**: QA Senior Backend + Datos  
**Próxima revisión**: Después de aplicar PASO 1-3 (30 min)
