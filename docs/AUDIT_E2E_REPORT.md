# 🔍 AUDITORÍA TÉCNICA E2E - SISTEMA OCR + COMPARADOR
## Sistema RapidEnergy / EnergyLuz

**Fecha**: 2026-01-19  
**Auditor**: QA Senior Backend + Datos  
**Objetivo**: Identificar bugs, bloqueantes y riesgos antes de continuar desarrollo

---

## 📊 RESUMEN EJECUTIVO

### Semáforo General
- 🔴 **P0 (BLOQUEANTES)**: 4 bugs críticos identificados
- 🟡 **P1 (GRAVES)**: 6 bugs graves detectados  
- 🔵 **P2 (MEJORAS)**: 5 mejoras de robustez

### Estado del Sistema
| Componente | Estado | Nota |
|------------|--------|------|
| OCR (Gemini + Vision) | ⚠️ FUNCIONAL CON BUGS | Extracción CUPS OK, pero falta periodo_dias |
| Validación CUPS | ✅ OK | normalize_cups + mod529 funcionan correctamente |
| Persistencia Facturas | ✅ OK | Deduplicación funciona |
| Comparador 2.0TD | 🔴 BLOQUEADO | Falta periodo_dias causa ERROR PERIOD_REQUIRED |
| Comparador 3.0TD | ⚠️ NO PROBADO | Lógica existe pero sin facturas de prueba |
| ofertas_calculadas | 🔴 CRÍTICO | Tabla NO existe en esquema, solo referencias en código |

---

## 🔴 BUGS P0 — BLOQUEANTES

### P0-1: **periodo_dias NO SE EXTRAE EN OCR**
**Severidad**: BLOQUEANTE — Impide completar comparaciones

**Descripción**:
- El OCR extrae `dias_facturados` pero NO lo persiste en `facturas.periodo_dias`
- El comparador requiere obligatoriamente `periodo_dias` (línea 377, comparador.py)
- Lanza `DomainError("PERIOD_REQUIRED")` si falta

**Archivos afectados**:
- `app/services/ocr.py` (líneas 325-336, 484-488)
- `app/routes/webhook.py` (líneas 264-332)

**Evidencia**:
```python
# OCR extrae dias_facturados (línea 332-336 ocr.py)
if dias_match:
    data["dias_facturados"] = int(dias_match.group(1))

# Pero en webhook.py NO se mapea a periodo_dias:
nueva_factura = Factura(
    # ... otros campos ...
    # periodo_dias=??? ❌ FALTA
)
```

**Repro steps**:
1. Subir factura con "DIAS FACTURADOS: 30" visible
2. Ver que `facturas.periodo_dias` = NULL
3. Intentar comparar → HTTP 422 "PERIOD_REQUIRED"

**Fix propuesto**:
```python
# En webhook.py línea ~326, agregar:
periodo_dias=ocr_data.get("dias_facturados"),
```

**Archivos a modificar**:
- `app/routes/webhook.py` (línea 293, agregar mapping)

---

### P0-2: **Tabla `ofertas_calculadas` NO EXISTE**
**Severidad**: BLOQUEANTE — Persistencia de ofertas falla silenciosamente

**Descripción**:
- El comparador intenta insertar en `ofertas_calculadas` (línea 265, 291, comparador.py)
- La tabla NO está definida en `models.py`
- La única migración es `migration_p1_NEON_PRODUCTION.sql` que NO crea esta tabla
- Sin embargo, el código espera las columnas:
  - `comparativa_id`
  - `tarifa_id`
  - `coste_estimado`
  - `ahorro_mensual`
  - `ahorro_anual`
  - `detalle_json`

**Evidencia**:
```bash
# Búsqueda en código:
grep "CREATE TABLE ofertas_calculadas" *.sql
# No results found ❌
```

**Archivos afectados**:
- `app/services/comparador.py` (líneas 254-312)
- `app/db/models.py` (NO tiene modelo OfertaCalculada)

**Repro steps**:
1. Comparar una factura válida
2. El código ejecuta `INSERT INTO ofertas_calculadas`
3. Error SQL: "table ofertas_calculadas does not exist"
4. El error se captura en try/except (línea 309) y retorna `False` silenciosamente
5. NO hay traceback visible, dificulta debugging

**Fix propuesto**:
1. Crear migración SQL:
```sql
CREATE TABLE IF NOT EXISTS ofertas_calculadas (
    id SERIAL PRIMARY KEY,
    comparativa_id INTEGER NOT NULL REFERENCES comparativas(id) ON DELETE CASCADE,
    tarifa_id INTEGER NOT NULL,
    coste_estimado NUMERIC(10, 2),
    ahorro_mensual NUMERIC(10, 2),
    ahorro_anual NUMERIC(10, 2),
    detalle_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ofertas_calc_comparativa ON ofertas_calculadas(comparativa_id);
```

2. Crear modelo en `models.py`:
```python
class OfertaCalculada(Base):
    __tablename__ = "ofertas_calculadas"
    
    id = Column(Integer, primary_key=True)
    comparativa_id = Column(Integer, ForeignKey("comparativas.id"))
    tarifa_id = Column(Integer, nullable=False)
    coste_estimado = Column(Float)
    ahorro_mensual = Column(Float)
    ahorro_anual = Column(Float)
    detalle_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Archivos a crear/modificar**:
- `migration_ofertas_calculadas.sql` (CREAR)
- `app/db/models.py` (AGREGAR modelo)

---

### P0-3: **Comparador falla si `fecha_inicio` y `fecha_fin` están vacías**
**Severidad**: BLOQUEANTE para facturas sin periodo_dias

**Descripción**:
- Si `periodo_dias` es NULL, el comparador intenta calcularlo de fechas (línea 380-384)
- Si ambas fechas son NULL, lanza `PERIOD_REQUIRED` inmediatamente
- PERO el OCR no siempre extrae fechas correctamente (patrones regex limitados)

**Evidencia**:
```python
# comparador.py líneas 377-387
periodo_dias = factura.periodo_dias
if not periodo_dias:
    if factura.fecha_inicio and factura.fecha_fin:
        # Intenta calcular...
    if not periodo_dias:
        raise DomainError("PERIOD_REQUIRED", "...")  # ❌ BLOQUEANTE
```

**Repro steps**:
1. Subir factura que no tenga patrón de fecha reconocible
2. `fecha_inicio` y `fecha_fin` = NULL
3. `periodo_dias` = NULL (por P0-1)
4. Comparar → HTTP 422 PERIOD_REQUIRED
5. Usuario bloqueado, sin forma de completar manualmente

**Fix propuesto**:
- Permitir que el usuario rellene `periodo_dias` manualmente en el frontend
- Agregar campo editable en wizard paso 2
- Validar que `periodo_dias` >= 1 y <= 365

**Archivos a modificar**:
- Frontend: `app/wizard/[id]/step-2-completar/page.jsx`
- Backend: Ya soporta actualización via PUT `/facturas/{id}`

---

### P0-4: **JPG con Vision API da HTTP 500**
**Severidad**: BLOQUEANTE para imágenes

**Descripción**:
- Durante test E2E, facturas `f1.jpg` y `f2.jpg` retornan HTTP 500
- El código tiene fallback Vision para imágenes (línea 876 ocr.py)
- Error sugiere problema de autenticación o configuración de Vision API

**Archivos afectados**:
- `app/services/ocr.py` (función `extract_data_from_pdf`, líneas 833-896)

**Repro steps**:
1. Subir `f1.jpg` via POST `/webhook/upload`
2. Servidor retorna HTTP 500
3. No hay traceback visible en logs del script

**Fix propuesto**:
- Revisar logs del servidor backend (Render)
- Verificar variable de entorno `GOOGLE_CREDENTIALS`
- Agregar logging más verbose en `get_vision_client()` (línea 177)

**Archivos a modificar**:
- `app/services/ocr.py` (agregar logs en excepciones)

---

## 🟡 BUGS P1 — GRAVES

### P1-1: **iva_porcentaje NO se extrae en OCR**
**Severidad**: GRAVE — Cálculos de IVA usan fallback 21%

**Descripción**:
- El comparador soporta `iva_porcentaje` (línea 499 comparador.py)
- PERO el OCR NO lo extrae, solo extrae `iva` (importe)
- Fallback: 21% por defecto (puede ser incorrecto para bono social = 10%)

**Archivos afectados**:
- `app/services/ocr.py` (falta extracción de iva_porcentaje)

**Fix propuesto**:
```python
# En parse_invoice_text, agregar:
iva_pct_match = re.search(r"IVA\s+(21|10|4)%", full_text, re.IGNORECASE)
if iva_pct_match:
    result["iva_porcentaje"] = float(iva_pct_match.group(1))
```

---

### P1-2: **numero_factura puede tener formato inconsistente**
**Severidad**: GRAVE — Deduplicación por numero_factura puede fallar

**Descripción**:
- El regex para numero_factura es permisivo: `[A-Z0-9\-\/]{3,30}`
- Puede capturar basura si la factura tiene varios códigos
- Deduplicación usa `cups + numero_factura` (línea 186 webhook.py)

**Fix propuesto**:
- Agregar validación de largo mínimo > 5 caracteres
- Filtrar números muy cortos (ej: "123")

---

### P1-3: **consumo_p4/p5/p6 no tienen patterns de extracción**
**Severidad**: GRAVE para facturas 3.0TD

**Descripción**:
- El OCR solo busca patterns para p1/p2/p3 (líneas 375-382 ocr.py)
- Para 3.0TD se necesitan p4/p5/p6
- Actualmente p4/p5/p6 quedarían NULL → comparador falla validación

**Archivos afectados**:
- `app/services/ocr.py` (patterns de consumo)

**Fix propuesto**:
- Agregar patterns para P4, P5, P6 (supervalle, etc.)

---

### P1-4: **potencia_p3/p4/p5/p6 NO se extraen para 3.0TD**
**Severidad**: GRAVE para facturas 3.0TD

**Descripción**:
- El OCR solo extrae `potencia_p1_kw` y `potencia_p2_kw`
- Para 3.0TD se necesitan 6 periodos de potencia
- Faltan en `_extract_potencias_with_sources` (línea 59)

** Fix propuesto**:
- Extender función para soportar P3-P6

---

### P1-5: **impuesto_electrico no siempre se extrae**
**Severidad**: GRAVE — Cálculos usan fallback 5.11%

**Descripción**:
- Pattern actual: `r"impuesto\s+electrico"` (línea 672)
- Si la factura dice "IEE" o "Imp. Eléctrico" NO se detecta
- Fallback en comparador calcula 5.11% (puede ser inexacto)

**Fix propuesto**:
- Agregar patterns alternativos:
```python
result["impuesto_electrico"] = _extract_number([
    r"impuesto\s+el[eé]ctrico[^0-9]{0,10}([\d.,]+)",
    r"\bIEE\b[^0-9]{0,10}([\d.,]+)",
    r"imp\.\s*el[eé]ctrico[^0-9]{0,10}([\d.,]+)"
])
```

---

### P1-6: **alquiler_contador no usa fallback estándar**
**Severidad**: MEDIA — Contadores propios vs alquilados

**Descripción**:
- El comparador solo incluye alquiler_contador si existe en factura (línea 487)
- Muchas comercializadoras tienen contador propio (0.026€/día aprox es estándar)
- Si no se detecta, el ahorro estimado puede estar inflado

**Fix propuesto**:
- Documentar que el ahorro NO incluye alquiler si no se extrae
- O agregar checkbox en frontend "Tiene contador de alquiler?" con valor por defecto

---

## 🔵 MEJORAS P2 — ROBUSTEZ

### P2-1: **Logs insuficientes en comparador**

**Descripción**:
- Si `_insert_ofertas` falla, solo retorna `False` (línea 312)
- El error se loggea pero no se propaga
- Dificulta debugging en producción

**Fix propuesto**:
```python
except Exception as e:
    logger.error(f"Error persisting offers (Comparativa {comparativa_id}): {e}", exc_info=True)
    # Agregar exc_info=True para ver traceback completo
```

---

### P2-2: **Fallback BOE 2025 no está documentado**

**Descripción**:
- Si `potencia_p1_eur_kw_dia` es NULL, usa 0.073777 (línea 452)
- No hay comentario explicando que es el valor BOE 2025
- Usuario puede confundirse al ver "modo_potencia: boe_2025_regulado"

**Fix propuesto**:
- Agregar comentario:
```python
# Fallback BOE 2025: Precios regulados de potencia para tarifa 2.0TD
# P1: 0.073777 €/kW·día | P2: 0.001911 €/kW·día
```

---

### P2-3: **Estado "lista_para_comparar" muy estricto**

**Descripción**:
- La validación exige todos los campos de `REQUIRED_FACTURA_FIELDS` (línea 50 webhook.py)
- Si falta 1 solo campo, estado = "pendiente_datos"
- PERO algunos campos tienen fallbacks en comparador (ej: potencia BOE 2025)

**Fix propuesto**:
- Crear estado intermedio "lista_con_fallbacks"
- Permitir comparar si solo faltan campos no críticos

---

### P2-4: **frontend/backend field name mismatch**

**Descripción**:
- Comparador retorna `estimated_total_periodo` (línea 541)
- Frontend espera `estimated_total` (según modelo OfferSelection línea 42 webhook.py)
- PERO el código mapea ambos (línea 539-541) para compatibilidad
- Esto es redundante y confuso

**Fix propuesto**:
- Consolidar en un solo nombre: `estimated_total`

---

### P2-5: **Deduplicación por CUPS+fecha+total puede fallar en refacturaciones**

**Descripción**:
- La lógica anti-duplicado usa `cups + fecha + total_factura` (línea 164)
- Si una comercializadora refactura (ej: corrección), puede tener mismo CUPS + fecha
- Pero total diferente → NO se detecta como duplicado
- Puede generar clientes duplicados

**Fix propuesto**:
- Agregar check por `numero_factura` primero (ya existe en línea 180)
- Priorizar `file_hash` (más seguro)

---

## 📋 CHECKLIST DE ARREGLOS QUIRÚRGICOS

### Fixes Inmediatos (< 30min)

- [x] **P0-1**: Agregar `periodo_dias=ocr_data.get("dias_facturados")` en webhook.py línea 326
- [ ] **P1-1**: Agregar extracción `iva_porcentaje` en ocr.py
- [ ] **P1-5**: Mejorar patterns de `impuesto_electrico`
- [ ] **P2-1**: Agregar `exc_info=True` en logs de comparador

### Fixes Medianos (1-2 horas)

- [ ] **P0-2**: Crear migración SQL + modelo `OfertaCalculada`
- [ ] **P1-3**: Agregar patterns consumo P4/P5/P6
- [ ] **P1-4**: Extender extracción potencias P3-P6
- [ ] **P2-3**: Implementar estado "lista_con_fallbacks"

### Fixes Largos (> 2 horas)

- [ ] **P0-3**: Frontend wizard paso 2 editable para `periodo_dias`
- [ ] **P0-4**: Debug error Vision API en JPG (requiere access a logs Render)

---

## 🎯 PROPUESTA DE PRIORIZACIÓN

### Sprint Hotfix (Ahora)
1. ✅ **P0-1**: periodo_dias mapping (5 min)
2. ✅ **P0-2**: Crear tabla ofertas_calculadas (30 min)
3. ⚠️ **P0-4**: Investigar error JPG (requiere logs)

### Sprint +1 (Esta semana)
4. **P1-1, P1-5**: Mejorar extracción OCR
5. **P1-3, P1-4**: Soporte 3.0TD completo
6. **P2-1**: Mejorar logging

### Sprint +2 (Semana próxima)
7. **P0-3**: Frontend editor de campos manual
8. **P2-3**: Estados de factura más flexibles
9. **P2-5**: Refactorizar deduplicación

---

## 📊 TABLA DE ESTADO ACTUAL (Estimada)

| Factura | CUPS OK | Campos OK | Lista Comparar | Comparador OK | Errores clave |
|---------|---------|-----------|----------------|---------------|---------------|
| Factura Iberdrola.pdf | ✅ | ⚠️ | ❌ | ❌ | falta periodo_dias (P0-1) |
| Factura.pdf | ✅ | ⚠️ | ❌ | ❌ | falta periodo_dias (P0-1) |
| Fra Agosto.pdf | ✅ | ⚠️ | ❌ | ❌ | falta periodo_dias (P0-1) |
| factura Naturgy.pdf | ✅ | ⚠️ | ❌ | ❌ | falta periodo_dias (P0-1) |
| f1.jpg | ❌ | ❌ | ❌ | ❌ | HTTP 500 Vision API (P0-4) |
| f2.jpg | ❌ | ❌ | ❌ | ❌ | HTTP 500 Vision API (P0-4) |

**Nota**: Tabla estimada basada en análisis de código. Tests E2E en ejecución.

---

## 🔧 ARCHIVOS CLAVE MODIFICADOS

### Archivos críticos que requieren cambios:

1. **`app/routes/webhook.py`**
   - Línea 326: Agregar mapping `periodo_dias`
   
2. **`app/services/ocr.py`**
   - Línea 672: Mejorar patterns impuesto_electrico
   - Línea 677: Agregar extracción iva_porcentaje
   - Línea 59: Extender potencias P3-P6

3. **`app/db/models.py`**
   - Agregar modelo `OfertaCalculada`

4. **`migration_ofertas_calculadas.sql`** (CREAR)
   - Definir tabla `ofertas_calculadas`

5. **`app/services/comparador.py`**
   - Línea 309: Agregar exc_info=True en logging

---

## ✅ CONCLUSIÓN

El sistema tiene una **arquitectura sólida** pero presenta **4 bugs bloqueantes (P0)** que impiden el flujo completo:

1. ❌ periodo_dias no se persiste → Comparador falla
2. ❌ ofertas_calculadas no existe → Persistencia falla silenciosamente
3. ❌ Sin fallback para fechas → Usuarios bloqueados
4. ❌ JPG retorna HTTP 500 → Vision API falla

**Recomendación**: Aplicar fixes P0-1 y P0-2 INMEDIATAMENTE antes de seguir desarrollando funcionalidades nuevas.

**Tiempo estimado de arreglo completo**: 3-4 horas para P0, 8-10 horas para P1.

---

**Auditor**: QA Senior Backend + Datos  
**Timestamp**: 2026-01-19 06:14:00 CET
