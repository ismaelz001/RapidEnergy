# INFORME TÉCNICO-OPERATIVO: COMPARADOR ENERGÉTICO ACTUAL
**RapidEnergy/MecaEnergy CRM**  
**Fecha**: 02 Febrero 2026  
**Destinatario**: Asistente que implementará sistema de versionado de tarifas  
**Metodología**: Análisis directo del código fuente (sin especulación)

---

## A) RESUMEN EJECUTIVO (10 líneas máximo)

El comparador de RapidEnergy obtiene tarifas competidoras desde la tabla PostgreSQL `tarifas` (NO están hardcodeadas). Reconstruye el coste estructural de la factura actual mediante backsolving (IVA + IEE + Alquiler → Subtotal), calcula el coste de cada oferta competidora con las mismas reglas de impuestos, y persiste los resultados en tablas `comparativas` y `ofertas_calculadas`. Las comisiones se resuelven con sistema de prioridades (comisiones_cliente > comisiones_tarifa activa), usando prefetch para evitar N+1 queries. Soporta dos tipos ATR: 2.0TD (3 periodos energía + 2 potencia) y 3.0TD (6 periodos energía + 2 potencia en factura, replicados a 6 internamente). Las tarifas actuales NO tienen versionado temporal: si cambia un precio, se sobrescribe el registro (riesgo de inconsistencia histórica). El usuario selecciona una oferta en el panel, y el sistema persiste `selected_oferta_id` en la factura. El diseño permite agregar versionado sin romper compatibilidad: añadir columnas `vigente_desde/vigente_hasta` en `tarifas`, filtrar por fecha en la consulta SQL, y mantener registros históricos en vez de UPDATE.

---

## B) DIAGRAMA TEXTUAL DEL FLUJO (paso a paso numerado)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ FLUJO COMPLETO DEL COMPARADOR (Endpoint → Cálculo → Persistencia → Selección)  │
└─────────────────────────────────────────────────────────────────────────────────┘

1. ENDPOINT: POST /comparar/facturas/{factura_id}
   └─ Ruta: app/routes/webhook.py (línea 767)
   └─ Validaciones previas:
      • Factura existe en DB
      • STEP2 completado (validado_step2 = True)
      • ATR válido para el nivel de datos disponible

2. INFERENCIA ATR (si falta en OCR)
   └─ Si factura.atr está vacío:
      • potencia_p1_kw >= 15 → ATR = "3.0TD"
      • potencia_p1_kw < 15  → ATR = "2.0TD"

3. DETERMINACIÓN LÍNEA BASE
   └─ Si validado_step2=True → usar total_ajustado (post-ajustes comerciales)
   └─ Si no → usar total_factura (OCR directo)

4. VALIDACIÓN DE CAMPOS SEGÚN ATR
   └─ 2.0TD requiere: consumo_p1/p2/p3_kwh, potencia_p1/p2_kw
   └─ 3.0TD requiere: consumo_p1 a p6_kwh, potencia_p1/p2_kw (P3-P6 se replican de P2)

5. BACKSOLVING DEL SUBTOTAL ACTUAL
   └─ Total factura → restar IVA → restar IEE → restar Alquiler = Subtotal sin impuestos
   └─ Fórmula: subtotal_si = (total - iva) - iee - alquiler
   └─ Método: "backsolve_subtotal_si" (línea 620 comparador.py)

6. OBTENCIÓN DE TARIFAS COMPETIDORAS
   └─ Query SQL: `SELECT * FROM tarifas WHERE atr = :atr` (línea 640)
   └─ Origen: **Base de datos PostgreSQL** (tabla "tarifas")
   └─ Campos usados: energia_p1/p2/p3/p4/p5/p6_eur_kwh, potencia_p1/p2_eur_kw_dia

7. CÁLCULO DE OFERTAS (loop por cada tarifa)
   7.1. Coste Energía = Σ(consumo_pi × precio_pi) para i=1..6 (3.0TD) o 1..3 (2.0TD)
   7.2. Coste Potencia = periodo_dias × Σ(potencia_pi × precio_potencia_pi) para i=1..2
   7.3. Subtotal oferta = Coste Energía + Coste Potencia
   7.4. Reconstrucción total oferta:
        • IEE = subtotal × 5.11269632%
        • Base IVA = subtotal + IEE + alquiler
        • IVA = base × iva_porcentaje
        • TOTAL = base + IVA

8. NORMALIZACIÓN DE AHORROS
   └─ Factor = 30 / periodo_dias (normaliza a 30 días)
   └─ Ahorro mensual = (total_actual - total_oferta) × factor
   └─ Ahorro anual = ahorro_mensual × 12

9. RESOLUCIÓN DE COMISIONES (prefetch optimizado)
   9.1. Consultar comisiones_cliente WHERE cliente_id=X AND tarifa_id IN (...)
        • Orden: created_at DESC, id DESC (determinista)
        • Selección: Primera fila por tarifa_id (más reciente)
   9.2. Consultar comisiones_tarifa WHERE tarifa_id IN (...) AND vigente_hasta IS NULL
        • Orden: vigente_desde DESC, created_at DESC, id DESC
        • Selección: Primera fila por tarifa_id (activa más reciente)
   9.3. Prioridad: comisiones_cliente > comisiones_tarifa > 0.00 (manual)
   └─ Resultado: comision_eur + comision_source ("cliente"|"tarifa"|"manual")

10. PERSISTENCIA EN TRANSACCIÓN ÚNICA
    10.1. Crear registro en "comparativas"
          └─ Campos: factura_id, created_at, periodo_dias, current_total
          └─ Retorno: comparativa_id (RETURNING id en PostgreSQL)
    
    10.2. Borrar ofertas_calculadas previas (WHERE comparativa_id = X)
    
    10.3. Insertar ofertas_calculadas (bulk insert)
          └─ Campos por oferta:
             • comparativa_id, tarifa_id
             • coste_estimado, ahorro_mensual, ahorro_anual
             • comision_eur, comision_source
             • detalle_json (oferta completa en JSON)

11. RESPUESTA HTTP 200
    └─ JSON: {
         "comparativa_id": int,
         "ofertas": [
            {
              "plan_name": str,
              "estimated_total_periodo": float,
              "ahorro_mensual_equiv": float,
              "ahorro_anual_equiv": float,
              "comision_eur": str,
              "comision_source": str,
              "breakdown": {...},
              "tarifa_id": int
            }
         ]
       }

12. SELECCIÓN DE OFERTA (flujo posterior en Panel Comercial)
    12.1. Usuario selecciona una oferta en el frontend
    12.2. Frontend → POST /factura/{id}/seleccionar-oferta
    12.3. Backend actualiza factura:
          • facturas.selected_oferta_id = oferta_id (FK)
          • facturas.selected_at = now()
          • facturas.selected_by_user_id = user_id
    12.4. Se genera comision_generada (estado="pendiente")

┌─────────────────────────────────────────────────────────────────────────────────┐
│ FIN DEL FLUJO                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## C) TABLA DE ORIGEN DE DATOS

| Dato Requerido                | Origen                          | Campo/Tabla                                | Qué Usa                                                                 |
|-------------------------------|----------------------------------|-------------------------------------------|-------------------------------------------------------------------------|
| **Total factura actual**      | DB - Factura                     | `facturas.total_ajustado` o `total_factura` | Línea base para comparar ahorros                                        |
| **ATR (2.0TD vs 3.0TD)**      | DB - Factura (OCR) / Inferencia  | `facturas.atr` (prio 1) o lógica por potencia | Determinar número de periodos (3 vs 6) y consulta de tarifas           |
| **Consumos (P1-P6)**          | DB - Factura (OCR)               | `facturas.consumo_p1_kwh` ... `consumo_p6_kwh` | Multiplicar por precios de energía para calcular coste                  |
| **Potencias (P1-P2)**         | DB - Factura (OCR)               | `facturas.potencia_p1_kw`, `potencia_p2_kw` | Multiplicar por precios de potencia × periodo_dias                      |
| **Periodo días**              | DB - Factura (OCR)               | `facturas.periodo_dias` (obligatorio)     | Normalización y cálculo de coste potencia                               |
| **IVA porcentaje**            | DB - Factura (OCR/Usuario)       | `facturas.iva_porcentaje` (21%, 10%, 4%)  | Reconstruir totales con impuestos (igualar factura real)                |
| **IVA importe**               | DB - Factura (OCR)               | `facturas.iva`                            | Backsolving del subtotal sin impuestos                                  |
| **IEE importe**               | DB - Factura (OCR)               | `facturas.impuesto_electrico`             | Backsolving del subtotal sin impuestos                                  |
| **Alquiler contador**         | DB - Factura (OCR)               | `facturas.alquiler_contador`              | Sumar a base imponible (igual en actual y ofertas)                      |
| **Tarifas competidoras**      | **DB - Tabla "tarifas"**         | `SELECT * FROM tarifas WHERE atr = :atr`  | **NO HARDCODEADO**: Obtiene lista de tarifas desde PostgreSQL           |
| **Precio energía P1-P6**      | DB - Tabla "tarifas"             | `energia_p1_eur_kwh` ... `energia_p6_eur_kwh` | Calcular coste de energía por periodo (fallback a P1 si P2+ son NULL)  |
| **Precio potencia P1-P2**     | DB - Tabla "tarifas"             | `potencia_p1_eur_kw_dia`, `potencia_p2_eur_kw_dia` | Calcular coste de potencia (fallback BOE 2025 solo en 2.0TD)           |
| **IEE % (impuesto eléctrico)**| **HARDCODED** en código          | `0.0511269632` (5.11269632%)              | Calcular impuesto eléctrico para ofertas (línea 533 y 739)             |
| **Fallback BOE 2025**         | **HARDCODED** en código          | P1: `0.073777` €/kW/día, P2: `0.001911` €/kW/día | Solo para 2.0TD si tarifa no tiene precios de potencia (línea 713-718) |
| **Comisiones por cliente**    | DB - Tabla "comisiones_cliente"  | `SELECT comision_eur WHERE cliente_id=X AND tarifa_id=Y` | Prioridad 1: Comisión específica del cliente (línea 392-406)            |
| **Comisiones por tarifa**     | DB - Tabla "comisiones_tarifa"   | `SELECT comision_eur WHERE tarifa_id=X AND vigente_hasta IS NULL` | Prioridad 2: Comisión estándar de la tarifa (línea 409-425)            |
| **Oferta seleccionada**       | DB - Factura (Usuario)           | `facturas.selected_oferta_id` (FK)        | Qué oferta eligió el comercial (persiste en transacción separada)      |

### Observaciones Críticas:
1. **Tarifas NO están hardcodeadas**: Se obtienen dinámicamente de la tabla `tarifas` en PostgreSQL.
2. **Única constante hardcodeada**: Porcentaje de Impuesto Eléctrico (5.11269632%) usado para reconstruir totales.
3. **Fallback BOE 2025**: Solo para precios de potencia en 2.0TD si la tarifa no los tiene (regulado).
4. **Comisiones**: Sistema de prioridades con prefetch optimizado (evita N+1 queries).
5. **Versionado actual**: NO existe. Las tarifas se actualizan con UPDATE (sin historial).

---

## D) CHECKLIST DE CAMBIOS MÍNIMOS PARA VERSIONADO DE TARIFAS

Para implementar versionado temporal de tarifas sin romper el comparador actual:

### 1. ESQUEMA DE BASE DE DATOS
- [ ] **Agregar columnas a tabla `tarifas`**:
  ```sql
  ALTER TABLE tarifas ADD COLUMN vigente_desde DATE NOT NULL DEFAULT CURRENT_DATE;
  ALTER TABLE tarifas ADD COLUMN vigente_hasta DATE NULL;
  ALTER TABLE tarifas ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
  CREATE INDEX idx_tarifas_vigencia ON tarifas (atr, vigente_desde, vigente_hasta);
  ```

- [ ] **Crear tabla de auditoría** (opcional pero recomendado):
  ```sql
  CREATE TABLE tarifas_historial (
    id SERIAL PRIMARY KEY,
    tarifa_id INTEGER NOT NULL REFERENCES tarifas(id),
    cambio_tipo TEXT NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    campos_cambiados JSONB,
    usuario_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
  );
  ```

- [ ] **Modificar lógica de INSERT/UPDATE**:
  - Nuevas tarifas: `vigente_desde = fecha_activacion`, `vigente_hasta = NULL`, `version = 1`
  - Edición de tarifa activa:
    1. UPDATE tarifa actual → `vigente_hasta = NOW()`
    2. INSERT nuevo registro → `vigente_desde = NOW()`, `vigente_hasta = NULL`, `version++`
  - **NO borrar registros históricos** (mantener trazabilidad)

### 2. CÓDIGO DEL COMPARADOR (app/services/comparador.py)
- [ ] **Modificar query de tarifas** (línea 640):
  ```python
  # ANTES:
  result = db.execute(
      text("SELECT * FROM tarifas WHERE atr = :atr"),
      {"atr": atr}
  )
  
  # DESPUÉS:
  fecha_comparacion = date.today()  # O usar fecha_factura si es histórica
  result = db.execute(
      text("""
          SELECT * FROM tarifas 
          WHERE atr = :atr 
          AND vigente_desde <= :fecha
          AND (vigente_hasta IS NULL OR vigente_hasta >= :fecha)
      """),
      {"atr": atr, "fecha": fecha_comparacion}
  )
  ```

- [ ] **Agregar parámetro `fecha_comparacion`** a `compare_factura()`:
  ```python
  def compare_factura(factura, db, fecha_comparacion: date = None) -> Dict[str, Any]:
      if fecha_comparacion is None:
          fecha_comparacion = date.today()
      # Usar fecha_comparacion en la query de tarifas
  ```

- [ ] **Persistir fecha de comparación**:
  ```python
  # En tabla comparativas, agregar columna:
  fecha_comparacion = Column(Date, nullable=False)
  
  # Al insertar comparativa:
  payload["fecha_comparacion"] = fecha_comparacion
  ```

### 3. ENDPOINTS (app/routes/webhook.py)
- [ ] **Modificar endpoint de comparación** (línea 767):
  ```python
  @router.post("/comparar/facturas/{factura_id}")
  def comparar_factura_endpoint(
      factura_id: int,
      fecha_comparacion: Optional[date] = Query(None),  # Nuevo parámetro
      db: Session = Depends(get_db)
  ):
      # Si no se especifica, usar fecha de la factura o hoy
      if fecha_comparacion is None:
          fecha_comparacion = factura.fecha_fin or date.today()
      
      # Pasar fecha al comparador
      result = compare_factura(factura, db, fecha_comparacion)
  ```

### 4. PANEL DE GESTIÓN DE TARIFAS (nuevo)
- [ ] **Crear endpoints CRUD** (app/routes/tarifas.py):
  ```python
  POST   /tarifas              → Crear nueva tarifa
  GET    /tarifas              → Listar tarifas activas (vigente_hasta=NULL)
  GET    /tarifas/historial    → Listar todas las versiones
  PUT    /tarifas/{id}         → Editar tarifa (crea nueva versión)
  DELETE /tarifas/{id}         → Desactivar tarifa (vigente_hasta=NOW)
  POST   /tarifas/{id}/duplicar → Duplicar tarifa (copiar todos los campos)
  ```

- [ ] **Crear componentes frontend** (app/panel-ceo/):
  - Lista de tarifas con filtros (ATR, comercializadora, activo/inactivo)
  - Formulario de creación/edición con validación de campos por ATR
  - Vista de historial de versiones (timeline)
  - Importación desde Excel/CSV (mapeo de columnas)
  - Exportación a Excel/CSV (para auditoría)

### 5. IMPORTACIÓN MASIVA DE TARIFAS
- [ ] **Crear endpoint de importación**:
  ```python
  POST /tarifas/importar
  Content-Type: multipart/form-data
  Body: archivo_excel (columnas: nombre, comercializadora, atr, energia_p1_eur_kwh, ...)
  ```

- [ ] **Validaciones obligatorias**:
  - ATR válido (2.0TD o 3.0TD)
  - Precios no negativos
  - Precios de energía P1 siempre requeridos
  - Precios de potencia P1/P2 requeridos (fallback BOE solo si NULL)
  - Comercializadora válida
  - Nombre único por comercializadora+ATR+fecha

### 6. INTEGRACIÓN CON OCR (opcional pero poderoso)
- [ ] **Endpoint de OCR para tarifas**:
  ```python
  POST /tarifas/ocr
  Body: {
    "image_base64": "...",
    "comercializadora": "Iberdrola",
    "atr": "2.0TD"
  }
  Response: {
    "extracted_fields": {
      "nombre": "Plan Solar",
      "energia_p1_eur_kwh": 0.203,
      "energia_p2_eur_kwh": 0.123,
      ...
    },
    "confidence_scores": {...}
  }
  ```

- [ ] **UI de revisión OCR**:
  - Vista previa de imagen + formulario con campos extraídos
  - Resaltado de campos con baja confianza (< 80%)
  - Edición manual antes de confirmar creación

### 7. TESTS Y VALIDACIÓN
- [ ] **Test de compatibilidad hacia atrás**:
  ```python
  def test_comparador_con_tarifas_versionadas():
      # Crear 2 versiones de misma tarifa
      tarifa_v1 = crear_tarifa(energia_p1=0.15, vigente_desde="2024-01-01", vigente_hasta="2024-12-31")
      tarifa_v2 = crear_tarifa(energia_p1=0.18, vigente_desde="2025-01-01", vigente_hasta=None)
      
      # Comparar factura de 2024
      resultado_2024 = compare_factura(factura, db, fecha_comparacion=date(2024, 6, 15))
      assert resultado_2024["ofertas"][0]["energia_p1"] == 0.15  # Usa v1
      
      # Comparar factura de 2025
      resultado_2025 = compare_factura(factura, db, fecha_comparacion=date(2025, 6, 15))
      assert resultado_2025["ofertas"][0]["energia_p1"] == 0.18  # Usa v2
  ```

- [ ] **Test de importación CSV**:
  ```python
  def test_importar_tarifas_desde_excel():
      archivo = "tarifas_iberdrola_2025.xlsx"
      resultado = importar_tarifas(archivo, db)
      assert resultado["insertadas"] == 12
      assert resultado["errores"] == 0
  ```

### 8. DOCUMENTACIÓN
- [ ] **Actualizar README.md** con sección de gestión de tarifas
- [ ] **Crear guía de migración** para pasar de tarifas legacy a versionadas
- [ ] **Documentar API de importación** con ejemplos de Excel/CSV

---

## E) PREGUNTAS ABIERTAS Y ASPECTOS NO ENCONTRADOS

### 1. ¿CÓMO DECIDE EL COMPARADOR ENTRE "24H" vs "TRAMOS" (3P/6P)?
**Estado**: ✅ **ENCONTRADO** en código (línea 127-139 comparador.py)

**Lógica actual**:
```python
def _resolve_energy_prices(mapping):
    p1_price = _to_float(mapping.get("energia_p1_eur_kwh"))
    p2_price = _to_float(mapping.get("energia_p2_eur_kwh"))
    p3_price = _to_float(mapping.get("energia_p3_eur_kwh"))
    
    if p1_price is None:
        return None, None
    
    if p2_price is None and p3_price is None:
        return "24h", (p1_price, p1_price, p1_price)  # Tarifa plana
    
    if p2_price is not None and p3_price is not None:
        return "3p", (p1_price, p2_price, p3_price)
    
    return None, None
```

**Criterio**: Si una tarifa tiene solo `energia_p1_eur_kwh` (P2 y P3 son NULL), se considera tarifa plana 24h. Si tiene P1+P2+P3, es discriminación horaria (3 periodos). En 3.0TD, si tiene P1 a P6, son 6 periodos.

---

### 2. ¿SE CONTEMPLAN TARIFAS INDEXADAS (OMIE)?
**Estado**: ❌ **NO ENCONTRADO** en código

El comparador actual NO tiene soporte para tarifas indexadas al precio horario de OMIE. Todos los precios son fijos (`tipo='fija'` en tabla tarifas).

**Para implementar indexadas, se necesitaría**:
1. Columna `tipo` en tarifas: `'fija'` o `'indexada'`
2. Si `tipo='indexada'`, almacenar solo el **markup** sobre OMIE (ej: +0.05 €/kWh)
3. API externa para obtener precios OMIE históricos por hora
4. Mapeo de consumos horarios (P1-P6) a precios OMIE específicos del periodo
5. Cálculo: `coste_energia = Σ(consumo_pi × (precio_omie_pi + markup))`

**Recomendación**: Dejar para fase posterior (requiere integración con API OMIE).

---

### 3. ¿QUÉ PARTES ESTÁN HARDCODEADAS QUE DEBERÍAN IR A DB?
**Estado**: ✅ **ENCONTRADO** mediante análisis completo

**Hardcoded en código (app/services/comparador.py)**:
| Elemento                         | Ubicación (línea) | Valor Actual           | ¿Debería ir a DB?                  |
|----------------------------------|-------------------|------------------------|------------------------------------|
| Impuesto Eléctrico (IEE) %       | 533, 739          | `0.0511269632` (5.11%) | ✅ SÍ - Cambia anualmente por BOE   |
| Fallback BOE 2025 potencia P1    | 715               | `0.073777` €/kW/día    | ✅ SÍ - Es regulado pero cambia      |
| Fallback BOE 2025 potencia P2    | 717               | `0.001911` €/kW/día    | ✅ SÍ - Es regulado pero cambia      |
| IVA porcentaje default           | 752               | `0.21` (21%)           | ⚠️ OPCIONAL - Pero raro que cambie  |

**Recomendación**:
1. Crear tabla `parametros_regulados`:
   ```sql
   CREATE TABLE parametros_regulados (
     clave TEXT PRIMARY KEY,
     valor_numerico NUMERIC,
     vigente_desde DATE NOT NULL,
     vigente_hasta DATE,
     descripcion TEXT
   );
   
   INSERT INTO parametros_regulados VALUES
   ('iee_porcentaje', 0.0511269632, '2024-01-01', NULL, 'Impuesto Eléctrico 5.11%'),
   ('potencia_p1_boe_2025', 0.073777, '2025-01-01', '2025-12-31', 'ATR 2.0TD regulado'),
   ('potencia_p2_boe_2025', 0.001911, '2025-01-01', '2025-12-31', 'ATR 2.0TD regulado');
   ```

2. En comparador, obtener parámetros al inicio:
   ```python
   iee_pct = _get_parametro_regulado(db, 'iee_porcentaje', fecha_comparacion)
   boe_p1 = _get_parametro_regulado(db, 'potencia_p1_boe_2025', fecha_comparacion)
   ```

---

### 4. ¿EXISTEN ARCHIVOS SQL DE MIGRACIÓN O ESQUEMA INICIAL?
**Estado**: ✅ **ENCONTRADO** en `__archive__/dev_artifacts/2026-01-26/`

**Archivos relevantes**:
- `migration_iberdrola_verified.sql`: INSERT de 5 tarifas verificadas de Iberdrola (ene 2026)
- `migration_iberdrola_2026.sql`: INSERT masivo de 20+ tarifas desde Excel (histórico)

**Estructura de INSERT existente**:
```sql
INSERT INTO tarifas (
  nombre, comercializadora, atr, tipo,
  energia_p1_eur_kwh, energia_p2_eur_kwh, energia_p3_eur_kwh,
  energia_p4_eur_kwh, energia_p5_eur_kwh, energia_p6_eur_kwh,
  potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia,
  potencia_p3_eur_kw_dia, potencia_p4_eur_kw_dia,
  potencia_p5_eur_kw_dia, potencia_p6_eur_kw_dia,
  origen
) VALUES (
  'Plan Solar', 'Iberdrola', '2.0TD', 'fija',
  0.203, 0.123, 0.079, NULL, NULL, NULL,
  0.086301, 0.042466, NULL, NULL, NULL, NULL,
  'Manual Verified Enero 2026'
);
```

**Observación**: Las columnas `vigente_desde`, `vigente_hasta`, `version` NO existen en el esquema actual.

---

### 5. ¿CÓMO SE MAPEAN LAS COMERCIALIZADORAS?
**Estado**: ⚠️ **PARCIALMENTE ENCONTRADO**

**En tabla `tarifas`**:
- Columna `comercializadora` es TEXT libre (ej: "Iberdrola", "Endesa", "Naturgy")
- NO hay tabla `comercializadoras` con catálogo oficial

**En tabla `facturas`**:
- **NO hay columna `comercializadora`** (solo se extrae de la factura implícitamente)
- El OCR detecta la comercializadora del logo/texto, pero NO se persiste actualmente

**Recomendación**:
1. Crear tabla `comercializadoras`:
   ```sql
   CREATE TABLE comercializadoras (
     id SERIAL PRIMARY KEY,
     nombre TEXT UNIQUE NOT NULL,
     nif TEXT,
     activa BOOLEAN DEFAULT TRUE,
     logo_url TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Agregar FK en tarifas
   ALTER TABLE tarifas ADD COLUMN comercializadora_id INTEGER REFERENCES comercializadoras(id);
   ```

2. Agregar columna en facturas:
   ```sql
   ALTER TABLE facturas ADD COLUMN comercializadora_id INTEGER REFERENCES comercializadoras(id);
   ```

---

### 6. ¿SE VALIDA COHERENCIA DE PRECIOS (P1 > P2 > P3)?
**Estado**: ❌ **NO ENCONTRADO** en código

El comparador NO valida que los precios sean decrecientes por periodo (lógica horaria esperada: punta > llano > valle).

**Riesgo**: Tarifas mal ingresadas pueden generar ofertas absurdas (ej: P3 más caro que P1).

**Recomendación**: Agregar validación en endpoint de creación/edición de tarifas:
```python
def validar_coherencia_precios(tarifa):
    if tarifa.atr == "2.0TD":
        # Esperado: P1 (punta) ≥ P2 (llano) ≥ P3 (valle)
        if tarifa.energia_p1_eur_kwh < tarifa.energia_p2_eur_kwh:
            raise ValueError("Precio P1 (punta) debe ser ≥ P2 (llano)")
        if tarifa.energia_p2_eur_kwh < tarifa.energia_p3_eur_kwh:
            raise ValueError("Precio P2 (llano) debe ser ≥ P3 (valle)")
    # Similar para 3.0TD (6 periodos)
```

---

### 7. ¿EXISTE LÓGICA DE CACHÉ DE TARIFAS?
**Estado**: ❌ **NO ENCONTRADO** en código

El comparador consulta la tabla `tarifas` en cada comparación (línea 640). NO hay caché.

**Impacto en producción**:
- 100 comparaciones/día → 100 queries a tarifas (bajo impacto con índice)
- Con versionado, la query se complica (JOIN con fechas)

**Recomendación**: Implementar caché en Redis:
```python
@cached(ttl=3600, key_prefix="tarifas_activas")
def get_tarifas_activas(db, atr: str, fecha: date):
    # Query de tarifas vigentes
    return db.execute(...)
```

Invalidar caché al crear/editar tarifas.

---

### 8. ¿CÓMO SE GESTIONA LA DESACTIVACIÓN DE TARIFAS?
**Estado**: ⚠️ **PARCIALMENTE ENCONTRADO**

**Situación actual**:
- NO hay columna `activa` en tabla `tarifas`
- Las tarifas obsoletas se borran o se dejan (sin filtrar)

**Con versionado propuesto**:
- Desactivación = UPDATE `vigente_hasta = NOW()`
- Las tarifas históricas siguen visibles en comparaciones pasadas
- El comparador filtra solo `vigente_hasta IS NULL OR vigente_hasta >= fecha_comparacion`

**Recomendación**: Agregar flag adicional `publicada`:
```sql
ALTER TABLE tarifas ADD COLUMN publicada BOOLEAN DEFAULT TRUE;
```
- `publicada=FALSE` → Borrador (no aparece en comparador)
- `vigente_hasta IS NOT NULL` → Histórica (solo en comparaciones pasadas)
- `publicada=TRUE AND vigente_hasta IS NULL` → Activa (aparece en comparador)

---

### 9. ¿QUÉ PASA SI UNA FACTURA TIENE ATR NO SOPORTADO?
**Estado**: ✅ **ENCONTRADO** en código (línea 609 comparador.py)

```python
if atr not in ("2.0TD", "3.0TD"):
    raise DomainError("ATR_UNSUPPORTED", f"ATR {atr} no soportado")
```

**Comportamiento actual**: Lanza excepción HTTP 422 (error de dominio).

**ATRs existentes en España**: 2.0TD, 3.0TD, 6.1TD, 6.2TD, 6.3TD, 6.4TD (industria)

**Recomendación**: Documentar claramente que solo se soportan 2.0TD y 3.0TD (residencial/PYME).

---

### 10. ¿SE PERSISTE EL DETALLE COMPLETO DE CADA OFERTA?
**Estado**: ✅ **ENCONTRADO** en código (línea 427 comparador.py)

```python
payload = {
    "comparativa_id": comparativa_id,
    "tarifa_id": tid,
    "coste_estimado": offer.get("estimated_total_periodo"),
    "ahorro_mensual": offer.get("ahorro_mensual_equiv"),
    "ahorro_anual": offer.get("ahorro_anual_equiv"),
    "comision_eur": comision_eur,
    "comision_source": comision_source,
    "detalle_json": json.dumps(offer, ensure_ascii=False)  # ⭐ COMPLETO
}
```

**Contenido de `detalle_json`**:
```json
{
  "plan_name": "Plan Solar",
  "comercializadora": "Iberdrola",
  "tarifa_id": 42,
  "estimated_total_periodo": 87.53,
  "ahorro_mensual_equiv": 12.34,
  "ahorro_anual_equiv": 148.08,
  "breakdown": {
    "coste_energia": 45.23,
    "coste_potencia": 18.67,
    "subtotal": 63.90,
    "impuesto_electrico": 3.27,
    "alquiler_contador": 0.80,
    "base_iva": 67.97,
    "iva": 14.27,
    "total": 82.24
  },
  "precios_usados": {
    "energia_p1_eur_kwh": 0.203,
    "energia_p2_eur_kwh": 0.123,
    "energia_p3_eur_kwh": 0.079,
    "potencia_p1_eur_kw_dia": 0.086301,
    "potencia_p2_eur_kw_dia": 0.042466
  },
  "comision_eur": "15.50",
  "comision_source": "tarifa"
}
```

**Conclusión**: El detalle completo está persistido. Esto permite reconstruir ofertas históricas incluso si las tarifas cambian.

---

## CONCLUSIONES Y RECOMENDACIONES FINALES

### ✅ PUNTOS FUERTES DEL DISEÑO ACTUAL
1. **Tarifas en DB**: Fácil de extender con versionado (solo agregar columnas)
2. **Comisiones con prioridades**: Sistema flexible y auditable
3. **Persistencia completa**: `detalle_json` permite reconstruir ofertas históricas
4. **Separación clara**: Comparativa (auditoría) vs Ofertas (datos individuales)
5. **Prefetch de comisiones**: Evita N+1 queries (optimización crítica en producción)

### ⚠️ RIESGOS IDENTIFICADOS
1. **Sin versionado**: Actualizar una tarifa sobrescribe datos (comparaciones históricas inconsistentes)
2. **IEE hardcodeado**: Cambio de BOE requiere deploy de código (debería ser configurable)
3. **Sin validación de coherencia**: Tarifas con precios ilógicos pueden persistirse
4. **Sin caché**: Consultas repetidas a tarifas en cada comparación (bajo impacto hoy, escalable con Redis)
5. **Comercializadoras sin normalizar**: Texto libre puede generar duplicados ("Iberdrola" vs "IBERDROLA")

### 🎯 PRIORIDADES PARA REDISEÑO (MVP)
1. **FASE 1 (Crítico)**:
   - Agregar versionado (`vigente_desde`, `vigente_hasta`, `version`)
   - Modificar query del comparador para filtrar por fecha
   - Crear endpoint de listado de tarifas activas

2. **FASE 2 (Gestión)**:
   - Panel CRUD de tarifas (crear, editar, desactivar, duplicar)
   - Importación desde Excel/CSV (mapeo de columnas)
   - Validación de coherencia de precios

3. **FASE 3 (Avanzado)**:
   - OCR de tarifas desde imágenes (folletos comerciales)
   - Auditoría de cambios (historial de versiones)
   - Caché en Redis para tarifas activas

### 📋 REQUISITOS NO NEGOCIABLES
- **Compatibilidad hacia atrás**: Las comparaciones existentes deben seguir funcionando
- **Sin pérdida de datos**: NO borrar tarifas, marcarlas como inactivas (`vigente_hasta`)
- **Determinismo**: Mismo input + misma fecha → mismo resultado (crucial para auditoría)
- **Trazabilidad**: Cada cambio debe quedar registrado (quién, cuándo, qué)

---

**FIN DEL INFORME**  
Documento generado por análisis directo del código fuente (sin especulación).  
Para cualquier duda técnica, consultar:
- [app/services/comparador.py](app/services/comparador.py) (motor de cálculo)
- [app/routes/webhook.py](app/routes/webhook.py) (endpoint de comparación)
- [app/db/models.py](app/db/models.py) (esquema de base de datos)
