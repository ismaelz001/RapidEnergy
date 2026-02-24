# PLAN DE IMPLEMENTACIÓN: VERSIONADO DE TARIFAS + BORRAR CLIENTE
**RapidEnergy/MecaEnergy CRM**  
**Fecha**: 24 Febrero 2026  
**Autor**: Senior Engineer (FastAPI + SQLAlchemy + Next.js)

---

## ⚠️ HALLAZGOS CRÍTICOS

### 🔴 PROBLEMA 1: TABLAS DE VERSIONADO **NO ENCONTRADAS**
Las tablas `tarifa_versiones` y `tarifa_precios` **NO EXISTEN** en el código actual:
- ❌ No hay modelos en `app/db/models.py`
- ❌ No hay migraciones SQL en el workspace
- ❌ El usuario menciona que "ya están aplicadas" pero no hay evidencia en el código

**DECISIÓN DE DISEÑO**: Propongo **estructura de tablas** basada en los requisitos funcionales descritos + mejor práctica de versionado temporal.

### 🔴 PROBLEMA 2: COLUMNA `tarifa_version_id` NO EXISTE EN `ofertas_calculadas`
Según `app/db/models.py` línea 162, `OfertaCalculada` NO tiene:
```python
tarifa_version_id = Column(...)  # ← NO EXISTE
```

**PROPUESTA**: Incluir en el PATCH el cambio de modelo SQLAlchemy + migración SQL.

### ✅ CONFIRMADO: Frontend de clientes existe en `app/clientes/page.jsx` (Server Component)
- ✅ Tabla de clientes con Link a detalle
- ❌ NO tiene botón de borrado (solo "Ver detalle")
- ✅ Backend ya tiene endpoint `DELETE /api/clientes/{cliente_id}` (línea 160 clientes.py)
- ✅ Cliente tiene `cascade="all, delete-orphan"` en `facturas` y `casos` (modelos línea 60-62)

---

## 📋 RESUMEN DE CAMBIOS (12 BULLETS)

### TAREA 1: Versionado de Tarifas en Comparador
1. **Crear modelos SQLAlchemy** para `TarifaVersion` y `TarifaPrecio` (nuevo archivo `app/db/models_tarifas.py`)
2. **Añadir columna `tarifa_version_id`** a `OfertaCalculada` en `models.py`
3. **Modificar `compare_factura()`**: reemplazar query directa a `tarifas` por JOIN con `tarifa_versiones` filtrando vigencia
4. **Crear helper `_fetch_precios_versiones()`**: prefetch de `tarifa_precios` para todas las versiones vigentes (1 query)
5. **Adaptar lectura de precios**: sustituir `tarifa.get("energia_p1_eur_kwh")` por consulta al dict de precios
6. **Añadir `import re`** en `comparador.py` (falta para `_parse_date()`)
7. **Modificar `_insert_ofertas()`**: incluir `tarifa_version_id` en payload de INSERT
8. **Añadir migraciones SQL** (archivo `migrations/20260224_add_tarifa_versioning.sql`)

### TAREA 2: Botón Borrar Cliente
9. **Frontend**: Agregar columna con botón "Eliminar" (icono basura) en tabla de `clientes/page.jsx`
10. **Frontend**: Implementar modal de confirmación + llamada DELETE fetch
11. **Backend**: Agregar validación de permisos (solo dev/ceo) en endpoint DELETE existente
12. **Backend**: Implementar estrategia **hard delete con CASCADE** (ya existe en ORM)

---

## 🔧 TAREA 1: ADAPTAR COMPARADOR A VERSIONADO DE TARIFAS

### ARCHIVO 1: `app/db/models_tarifas.py` (NUEVO)

**⚠️ ESTADO**: NO ENCONTRADO - Propongo crearlo

```python
"""
Modelos de versionado de tarifas energéticas.
Separados del models.py principal para claridad.
"""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Date, Boolean, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.conn import Base


class TarifaVersion(Base):
    """
    Versión de una tarifa energética con vigencia temporal.
    Una tarifa puede tener múltiples versiones a lo largo del tiempo.
    """
    __tablename__ = "tarifa_versiones"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metadatos de la tarifa
    nombre = Column(String, nullable=False)  # ej: "Plan Solar"
    comercializadora = Column(String, nullable=False, index=True)  # ej: "Iberdrola"
    atr = Column(String, nullable=False, index=True)  # "2.0TD" o "3.0TD"
    tipo = Column(String, default="fija")  # "fija" o "indexada"
    
    # Versionado temporal
    vigente_desde = Column(Date, nullable=False, index=True)
    vigente_hasta = Column(Date, nullable=True, index=True)  # NULL = vigente actual
    version = Column(Integer, nullable=False, default=1)
    
    # Auditoría
    origen = Column(String, nullable=True)  # "manual", "excel_import", "ocr"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relaciones
    precios = relationship("TarifaPrecio", back_populates="version", cascade="all, delete-orphan")
    ofertas = relationship("OfertaCalculada", back_populates="tarifa_version")
    
    # Constraint: no puede haber dos versiones vigentes simultáneas de la misma tarifa
    __table_args__ = (
        UniqueConstraint('nombre', 'comercializadora', 'atr', 'vigente_desde', name='uq_tarifa_version_vigencia'),
    )


class TarifaPrecio(Base):
    """
    Precios de energía y potencia de una versión de tarifa.
    Permite modelar tarifas planas (24H) o discriminación horaria (P1-P6).
    """
    __tablename__ = "tarifa_precios"
    
    id = Column(Integer, primary_key=True, index=True)
    tarifa_version_id = Column(Integer, ForeignKey("tarifa_versiones.id"), nullable=False, index=True)
    
    # Tipo de precio
    tipo_periodo = Column(String, nullable=False)  # "energia" o "potencia"
    periodo_nombre = Column(String, nullable=False)  # "24H", "P1", "P2", ... "P6"
    
    # Valor del precio
    precio_eur_unidad = Column(Numeric(12, 6), nullable=False)  # €/kWh para energía, €/kW/día para potencia
    
    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación
    version = relationship("TarifaVersion", back_populates="precios")
    
    # Constraint: no duplicar periodo para una misma versión
    __table_args__ = (
        UniqueConstraint('tarifa_version_id', 'tipo_periodo', 'periodo_nombre', name='uq_tarifa_precio_periodo'),
    )
```

---

### ARCHIVO 2: `migrations/20260224_add_tarifa_versioning.sql` (NUEVO)

```sql
-- ============================================================
-- MIGRACIÓN: Sistema de versionado de tarifas
-- Fecha: 2026-02-24
-- Descripción: Crea tablas tarifa_versiones y tarifa_precios
--              + añade columna tarifa_version_id a ofertas_calculadas
-- ============================================================

-- 1. Crear tabla tarifa_versiones
CREATE TABLE tarifa_versiones (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    comercializadora TEXT NOT NULL,
    atr TEXT NOT NULL,
    tipo TEXT DEFAULT 'fija',
    vigente_desde DATE NOT NULL,
    vigente_hasta DATE,
    version INTEGER NOT NULL DEFAULT 1,
    origen TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Constraint: no duplicar vigencia
    CONSTRAINT uq_tarifa_version_vigencia UNIQUE (nombre, comercializadora, atr, vigente_desde)
);

-- Índices para performance
CREATE INDEX idx_tarifa_versiones_atr ON tarifa_versiones(atr);
CREATE INDEX idx_tarifa_versiones_comercializadora ON tarifa_versiones(comercializadora);
CREATE INDEX idx_tarifa_versiones_vigente_desde ON tarifa_versiones(vigente_desde);
CREATE INDEX idx_tarifa_versiones_vigente_hasta ON tarifa_versiones(vigente_hasta);

-- 2. Crear tabla tarifa_precios
CREATE TABLE tarifa_precios (
    id SERIAL PRIMARY KEY,
    tarifa_version_id INTEGER NOT NULL REFERENCES tarifa_versiones(id) ON DELETE CASCADE,
    tipo_periodo TEXT NOT NULL,  -- 'energia' o 'potencia'
    periodo_nombre TEXT NOT NULL,  -- '24H', 'P1', 'P2', ..., 'P6'
    precio_eur_unidad NUMERIC(12, 6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraint: no duplicar periodo para misma versión
    CONSTRAINT uq_tarifa_precio_periodo UNIQUE (tarifa_version_id, tipo_periodo, periodo_nombre)
);

-- Índice para queries frecuentes (prefetch de precios)
CREATE INDEX idx_tarifa_precios_version_id ON tarifa_precios(tarifa_version_id);

-- 3. Añadir columna tarifa_version_id a ofertas_calculadas
ALTER TABLE ofertas_calculadas 
ADD COLUMN tarifa_version_id INTEGER REFERENCES tarifa_versiones(id) ON DELETE SET NULL;

-- Índice para FK
CREATE INDEX idx_ofertas_calculadas_tarifa_version_id ON ofertas_calculadas(tarifa_version_id);

-- 4. Migrar datos de tarifas legacy (OPCIONAL - ejecutar solo si existe tabla 'tarifas')
-- NOTA: Esta sección requiere ajuste manual según estructura legacy
/*
INSERT INTO tarifa_versiones (nombre, comercializadora, atr, tipo, vigente_desde, vigente_hasta, version, origen)
SELECT 
    nombre,
    comercializadora,
    atr,
    tipo,
    COALESCE(vigente_desde, '2024-01-01'::DATE),  -- Asumir 2024 si NULL
    vigente_hasta,
    1,
    'migrated_from_legacy'
FROM tarifas
WHERE nombre IS NOT NULL;

-- Insertar precios de energía
INSERT INTO tarifa_precios (tarifa_version_id, tipo_periodo, periodo_nombre, precio_eur_unidad)
SELECT 
    tv.id,
    'energia',
    'P1',
    t.energia_p1_eur_kwh
FROM tarifas t
JOIN tarifa_versiones tv ON tv.nombre = t.nombre AND tv.comercializadora = t.comercializadora
WHERE t.energia_p1_eur_kwh IS NOT NULL;

-- Repetir para P2, P3, P4, P5, P6 y precios de potencia...
*/

COMMENT ON TABLE tarifa_versiones IS 'Versiones de tarifas energéticas con vigencia temporal';
COMMENT ON TABLE tarifa_precios IS 'Precios de energía/potencia por periodo (P1-P6 o 24H)';
```

---

### ARCHIVO 3: `app/db/models.py` (MODIFICAR)

**ANTES** (línea 162):
```python
class OfertaCalculada(Base):
    """⭐ FIX P0-2: Ofertas persistidas generadas por el comparador"""
    __tablename__ = "ofertas_calculadas"
    
    id = Column(Integer, primary_key=True, index=True)
    comparativa_id = Column(Integer, ForeignKey("comparativas.id"), nullable=False)
    tarifa_id = Column(Integer, nullable=False)
    coste_estimado = Column(Float, nullable=True)
    ahorro_mensual = Column(Float, nullable=True)
    ahorro_anual = Column(Float, nullable=True)
    detalle_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación: Una oferta pertenece a una comparativa
    comparativa = relationship("Comparativa", back_populates="ofertas")
```

**DESPUÉS**:
```python
class OfertaCalculada(Base):
    """⭐ FIX P0-2: Ofertas persistidas generadas por el comparador"""
    __tablename__ = "ofertas_calculadas"
    
    id = Column(Integer, primary_key=True, index=True)
    comparativa_id = Column(Integer, ForeignKey("comparativas.id"), nullable=False)
    tarifa_id = Column(Integer, nullable=False)  # Legacy: mantener por compatibilidad
    tarifa_version_id = Column(Integer, ForeignKey("tarifa_versiones.id"), nullable=True)  # ⭐ NUEVO
    coste_estimado = Column(Float, nullable=True)
    ahorro_mensual = Column(Float, nullable=True)
    ahorro_anual = Column(Float, nullable=True)
    comision_eur = Column(Numeric(12, 2), nullable=True, default=0.00)  # ⭐ AÑADIDO (ya existe en comparador)
    comision_source = Column(Text, nullable=True)  # ⭐ AÑADIDO (cliente/tarifa/manual)
    detalle_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    comparativa = relationship("Comparativa", back_populates="ofertas")
    tarifa_version = relationship("TarifaVersion", back_populates="ofertas")  # ⭐ NUEVO
```

**IMPORTANTE**: Añadir import al inicio del archivo:
```python
# En línea ~1 de models.py, después de los imports existentes
from app.db.models_tarifas import TarifaVersion, TarifaPrecio  # ⭐ NUEVO
```

---

### ARCHIVO 4: `app/services/comparador.py` (MODIFICAR - PARTE 1: Imports y Helpers)

**ANTES** (línea 1):
```python
"""
Tariff comparison service for 2.0TD (MVP).
"""

from datetime import date, datetime
from decimal import Decimal
import json
import logging
from typing import Dict, Any, Optional

from sqlalchemy import inspect, text
from app.exceptions import DomainError
from app.db.models import Comparativa

logger = logging.getLogger(__name__)
_TABLE_COLUMNS_CACHE: Dict[str, Dict[str, Any]] = {}
```

**DESPUÉS**:
```python
"""
Tariff comparison service for 2.0TD (MVP).
"""

from datetime import date, datetime
from decimal import Decimal
import json
import logging
import re  # ⭐ AÑADIDO: faltaba para _parse_date()
from typing import Dict, Any, Optional

from sqlalchemy import inspect, text
from app.exceptions import DomainError
from app.db.models import Comparativa
from app.db.models_tarifas import TarifaVersion, TarifaPrecio  # ⭐ AÑADIDO

logger = logging.getLogger(__name__)
_TABLE_COLUMNS_CACHE: Dict[str, Dict[str, Any]] = {}
```

---

**NUEVO HELPER** (insertar después de `_resolve_energy_prices`, línea ~145):

```python
def _fetch_precios_versiones(db, version_ids: list) -> Dict[int, Dict[str, Any]]:
    """
    Prefetch de precios de energía y potencia para múltiples versiones de tarifas.
    
    Args:
        db: SQLAlchemy session
        version_ids: Lista de tarifa_version_id
    
    Returns:
        Dict con estructura:
        {
            version_id: {
                'energia': {'P1': 0.15, 'P2': 0.12, 'P3': 0.10, '24H': None},
                'potencia': {'P1': 0.08, 'P2': 0.04},
                'cuota_mes': None  # Para futuras tarifas con cuota fija
            }
        }
    """
    if not version_ids:
        return {}
    
    # Query única para todos los precios
    result = db.execute(
        text("""
            SELECT 
                tarifa_version_id,
                tipo_periodo,
                periodo_nombre,
                precio_eur_unidad
            FROM tarifa_precios
            WHERE tarifa_version_id = ANY(:version_ids)
            ORDER BY tarifa_version_id, tipo_periodo, periodo_nombre
        """),
        {"version_ids": version_ids}
    )
    
    rows = result.fetchall()
    
    # Construir diccionario anidado
    precios_map = {}
    for row in rows:
        vid = row[0]
        tipo = row[1]  # 'energia' o 'potencia'
        periodo = row[2]  # 'P1', 'P2', '24H', etc.
        precio = float(row[3])
        
        if vid not in precios_map:
            precios_map[vid] = {
                'energia': {},
                'potencia': {},
                'cuota_mes': None
            }
        
        precios_map[vid][tipo][periodo] = precio
    
    logger.info(f"[VERSIONADO] Prefetched precios para {len(precios_map)} versiones de tarifas")
    return precios_map


def _get_precio_energia(precios_dict: Dict, periodo_idx: int) -> Optional[float]:
    """
    Obtiene precio de energía para un periodo (1-6) desde dict de precios.
    Soporta:
    - Discriminación horaria: P1, P2, P3, P4, P5, P6
    - Tarifa plana: 24H (devuelve mismo precio para todos los periodos)
    - Fallback legacy: si solo existe P1, lo usa como tarifa plana
    
    Args:
        precios_dict: {'P1': 0.15, 'P2': 0.12, ...} o {'24H': 0.14}
        periodo_idx: 1-6 (índice del periodo)
    
    Returns:
        Precio en €/kWh o None si no hay datos
    """
    if not precios_dict:
        return None
    
    # Prioridad 1: Tarifa plana 24H
    if '24H' in precios_dict:
        return precios_dict['24H']
    
    # Prioridad 2: Precio específico del periodo
    periodo_key = f'P{periodo_idx}'
    if periodo_key in precios_dict:
        return precios_dict[periodo_key]
    
    # Prioridad 3: Fallback a P1 (tarifa legacy con solo P1)
    if periodo_idx > 1 and 'P1' in precios_dict and len(precios_dict) == 1:
        logger.debug(f"[VERSIONADO] Fallback: usando P1 como tarifa plana para periodo {periodo_idx}")
        return precios_dict['P1']
    
    return None


def _get_precio_potencia(precios_dict: Dict, periodo_idx: int, atr: str) -> Optional[float]:
    """
    Obtiene precio de potencia para un periodo desde dict de precios.
    
    Args:
        precios_dict: {'P1': 0.08, 'P2': 0.04, ...}
        periodo_idx: 1-6 (índice del periodo)
        atr: "2.0TD" o "3.0TD"
    
    Returns:
        Precio en €/kW/día o None (activará fallback BOE 2025 en 2.0TD)
    """
    if not precios_dict:
        return None
    
    periodo_key = f'P{periodo_idx}'
    return precios_dict.get(periodo_key)
```

---

### ARCHIVO 5: `app/services/comparador.py` (MODIFICAR - PARTE 2: compare_factura)

**BLOQUE A CAMBIAR** (línea ~635 - query de tarifas):

**ANTES**:
```python
    result = db.execute(
        text("SELECT * FROM tarifas WHERE atr = :atr"),
        {"atr": atr},
    )
    try:
        tarifas = result.mappings().all()
    except AttributeError:
        tarifas = [row._mapping for row in result.fetchall()]
```

**DESPUÉS**:
```python
    # ⭐ VERSIONADO: Obtener versiones vigentes HOY + prefetch de precios
    fecha_comparacion = date.today()
    
    result = db.execute(
        text("""
            SELECT 
                tv.id as tarifa_version_id,
                tv.nombre,
                tv.comercializadora,
                tv.atr,
                tv.tipo,
                tv.version,
                tv.vigente_desde,
                tv.vigente_hasta
            FROM tarifa_versiones tv
            WHERE tv.atr = :atr
              AND tv.vigente_desde <= :fecha
              AND (tv.vigente_hasta IS NULL OR tv.vigente_hasta >= :fecha)
            ORDER BY tv.comercializadora, tv.nombre
        """),
        {"atr": atr, "fecha": fecha_comparacion}
    )
    
    try:
        tarifas = result.mappings().all()
    except AttributeError:
        tarifas = [row._mapping for row in result.fetchall()]
    
    if not tarifas:
        logger.warning(f"[VERSIONADO] No hay tarifas vigentes para ATR={atr} en fecha={fecha_comparacion}")
        return {
            "ok": False,
            "error_code": "NO_TARIFAS_VIGENTES",
            "message": f"No hay tarifas disponibles para {atr} en la fecha actual",
            "factura_id": factura.id,
            "comparativa_id": None,
            "ofertas": []
        }
    
    # Prefetch de precios para todas las versiones vigentes
    version_ids = [t['tarifa_version_id'] for t in tarifas]
    precios_map = _fetch_precios_versiones(db, version_ids)
    
    logger.info(f"[VERSIONADO] Encontradas {len(tarifas)} tarifas vigentes para {atr}")
```

---

**BLOQUE B A CAMBIAR** (línea ~665 - inicio del loop de ofertas):

**ANTES**:
```python
    offers = []
    for tarifa in tarifas:
        # LOGICA DE PRECIOS ENERGÍA DINÁMICA (soporta 2.0TD y 3.0TD)
        # Para 2.0TD: P1, P2, P3
        # Para 3.0TD: P1, P2, P3, P4, P5, P6
        
        # Obtener precios de energía según número de periodos
        precios_energia = []
        for i in range(1, num_periodos_energia + 1):
            precio = _to_float(tarifa.get(f"energia_p{i}_eur_kwh"))
            
            # Fallback: Si P2+ son null, usar P1 (tarifa plana 24h)
            if precio is None and i > 1:
                precio = _to_float(tarifa.get("energia_p1_eur_kwh"))
            
            precios_energia.append(precio)
        
        # Validar que al menos P1 tenga precio
        if precios_energia[0] is None:
            continue  # Tarifa rota sin precio de energía
```

**DESPUÉS**:
```python
    offers = []
    for tarifa in tarifas:
        # ⭐ VERSIONADO: Obtener precios desde tarifa_precios en vez de columnas tarifas
        version_id = tarifa['tarifa_version_id']
        precios_version = precios_map.get(version_id)
        
        if not precios_version:
            logger.warning(f"[VERSIONADO] Skipping tarifa version_id={version_id}: sin precios en tarifa_precios")
            continue
        
        # LOGICA DE PRECIOS ENERGÍA DINÁMICA (soporta 2.0TD y 3.0TD)
        precios_energia = []
        for i in range(1, num_periodos_energia + 1):
            precio = _get_precio_energia(precios_version['energia'], i)
            precios_energia.append(precio)
        
        # Validar que al menos P1 tenga precio
        if precios_energia[0] is None:
            logger.warning(
                f"[VERSIONADO] Skipping tarifa {tarifa['nombre']}/{tarifa['comercializadora']}: "
                f"sin precio energía P1"
            )
            continue
```

---

**BLOQUE C A CAMBIAR** (línea ~688 - precios de potencia):

**ANTES**:
```python
        # LOGICA DE PRECIOS POTENCIA DINÁMICA (soporta 2.0TD y 3.0TD)
        # Para 2.0TD: P1, P2 (con fallback BOE 2025 si null)
        # Para 3.0TD: P1, P2, P3, P4, P5, P6 (sin fallback, deben estar completos)
        
        precios_potencia = []
        tiene_precios_potencia = True
        
        for i in range(1, num_periodos_potencia + 1):
            precio = _to_float(tarifa.get(f"potencia_p{i}_eur_kw_dia"))
            
            # Fallback BOE 2025 SOLO para 2.0TD (P1 y P2)
            if precio is None and atr == "2.0TD":
                if i == 1:
                    precio = 0.073777  # BOE 2025 P1
                elif i == 2:
                    precio = 0.001911  # BOE 2025 P2
                tiene_precios_potencia = False  # Marca que usó fallback
            
            precios_potencia.append(precio or 0.0)
```

**DESPUÉS**:
```python
        # LOGICA DE PRECIOS POTENCIA DINÁMICA (soporta 2.0TD y 3.0TD)
        precios_potencia = []
        tiene_precios_potencia = True
        
        for i in range(1, num_periodos_potencia + 1):
            precio = _get_precio_potencia(precios_version['potencia'], i, atr)
            
            # Fallback BOE 2025 SOLO para 2.0TD (P1 y P2) si no hay precio en tarifa_precios
            if precio is None and atr == "2.0TD":
                if i == 1:
                    precio = 0.073777  # BOE 2025 P1
                elif i == 2:
                    precio = 0.001911  # BOE 2025 P2
                tiene_precios_potencia = False  # Marca que usó fallback
            
            precios_potencia.append(precio or 0.0)
```

---

**BLOQUE D A CAMBIAR** (línea ~830 - construcción del objeto offer):

**ANTES**:
```python
        # Mapeo de nombres
        tarifa_id = tarifa.get("id") or tarifa.get("tarifa_id")
        provider = _pick_value(
            tarifa,
            ["comercializadora", "provider", "empresa", "brand"],
            "Proveedor genérico",
        )
        plan_name = _pick_value(
            tarifa,
            ["nombre", "plan_name", "plan", "tarifa"],
            "Tarifa 2.0TD",
        )
```

**DESPUÉS**:
```python
        # ⭐ VERSIONADO: Mapeo de nombres desde dict de versiones
        tarifa_version_id = version_id  # Ya lo tenemos del loop
        tarifa_id_legacy = tarifa.get("id") or tarifa.get("tarifa_id")  # Para compatibilidad
        provider = tarifa.get("comercializadora") or "Proveedor genérico"
        plan_name = tarifa.get("nombre") or "Tarifa 2.0TD"
```

---

**BLOQUE E A CAMBIAR** (línea ~845 - objeto offer final):

**ANTES**:
```python
        offer = {
            "tarifa_id": tarifa_id,
            "provider": provider,
            "plan_name": plan_name,
```

**DESPUÉS**:
```python
        offer = {
            "tarifa_id": tarifa_id_legacy,  # ⭐ Legacy: mantener por compatibilidad frontend
            "tarifa_version_id": tarifa_version_id,  # ⭐ NUEVO
            "provider": provider,
            "plan_name": plan_name,
```

---

### ARCHIVO 6: `app/services/comparador.py` (MODIFICAR - PARTE 3: _insert_ofertas)

**ANTES** (línea ~430):
```python
            payload = {
                "comparativa_id": comparativa_id,
                "tarifa_id": tid,
                "coste_estimado": offer.get("estimated_total_periodo"),
                "ahorro_mensual": offer.get("ahorro_mensual_equiv"),
                "ahorro_anual": offer.get("ahorro_anual_equiv"),
                "comision_eur": comision_eur,  # Decimal directo para DB
                "comision_source": comision_source,
                "detalle_json": json.dumps(offer, ensure_ascii=False)
            }
```

**DESPUÉS**:
```python
            payload = {
                "comparativa_id": comparativa_id,
                "tarifa_id": tid,  # ⭐ Legacy: mantener por compatibilidad
                "tarifa_version_id": offer.get("tarifa_version_id"),  # ⭐ NUEVO
                "coste_estimado": offer.get("estimated_total_periodo"),
                "ahorro_mensual": offer.get("ahorro_mensual_equiv"),
                "ahorro_anual": offer.get("ahorro_anual_equiv"),
                "comision_eur": comision_eur,  # Decimal directo para DB
                "comision_source": comision_source,
                "detalle_json": json.dumps(offer, ensure_ascii=False)
            }
```

**ANTES** (línea ~443 - SQL INSERT):
```python
            # SQL explícito con CAST para JSONB en Postgres
            if is_postgres:
                stmt = text("""
                    INSERT INTO ofertas_calculadas 
                    (comparativa_id, tarifa_id, coste_estimado, ahorro_mensual, ahorro_anual, comision_eur, comision_source, detalle_json)
                    VALUES 
                    (:comparativa_id, :tarifa_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, :comision_eur, :comision_source, CAST(:detalle_json AS jsonb))
                """)
            else:
                stmt = text("""
                    INSERT INTO ofertas_calculadas 
                    (comparativa_id, tarifa_id, coste_estimado, ahorro_mensual, ahorro_anual, comision_eur, comision_source, detalle_json)
                    VALUES 
                    (:comparativa_id, :tarifa_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, :comision_eur, :comision_source, :detalle_json)
                """)
```

**DESPUÉS**:
```python
            # ⭐ VERSIONADO: Incluir tarifa_version_id en INSERT
            # SQL explícito con CAST para JSONB en Postgres
            if is_postgres:
                stmt = text("""
                    INSERT INTO ofertas_calculadas 
                    (comparativa_id, tarifa_id, tarifa_version_id, coste_estimado, ahorro_mensual, ahorro_anual, comision_eur, comision_source, detalle_json)
                    VALUES 
                    (:comparativa_id, :tarifa_id, :tarifa_version_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, :comision_eur, :comision_source, CAST(:detalle_json AS jsonb))
                """)
            else:
                stmt = text("""
                    INSERT INTO ofertas_calculadas 
                    (comparativa_id, tarifa_id, tarifa_version_id, coste_estimado, ahorro_mensual, ahorro_anual, comision_eur, comision_source, detalle_json)
                    VALUES 
                    (:comparativa_id, :tarifa_id, :tarifa_version_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, :comision_eur, :comision_source, :detalle_json)
                """)
```

---

## 🗑️ TAREA 2: BOTÓN BORRAR CLIENTE

### ARCHIVO 7: `app/routes/clientes.py` (MODIFICAR)

**ANTES** (línea 160):
```python
@router.delete("/{cliente_id}")
def delete_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    try:
        db.delete(cliente)
        db.commit()
        return {"message": "Cliente eliminado correctamente", "id": cliente_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}")
```

**DESPUÉS**:
```python
@router.delete("/{cliente_id}")
def delete_cliente(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)  # ⭐ AÑADIDO: validación de permisos
):
    """
    Elimina un cliente y todas sus dependencias (facturas, casos, comisiones).
    
    Permisos:
    - DEV: puede borrar cualquier cliente
    - CEO: solo clientes de su company
    - COMERCIAL: NO PERMITIDO (riesgo de perder comisiones)
    
    Estrategia: HARD DELETE con CASCADE
    - Cliente tiene cascade="all, delete-orphan" en facturas y casos (models.py línea 60-62)
    - Al borrar cliente se borran automáticamente:
      * Facturas del cliente (y sus comparativas + ofertas por cascade)
      * Casos del cliente (y su historial por cascade)
      * Comisiones generadas (FK a cliente con ON DELETE CASCADE en DB)
    """
    # ⭐ VALIDACIÓN DE PERMISOS
    if not current_user.is_dev() and not current_user.is_ceo():
        raise HTTPException(
            status_code=403, 
            detail="No tienes permisos para eliminar clientes. Contacta con tu CEO o soporte."
        )
    
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # ⭐ VALIDACIÓN: CEO solo puede borrar clientes de su company
    if current_user.is_ceo():
        if cliente.company_id != current_user.company_id:
            raise HTTPException(
                status_code=403,
                detail="No puedes eliminar clientes de otras empresas"
            )
    
    # Contar dependencias para logging
    num_facturas = len(cliente.facturas) if cliente.facturas else 0
    num_casos = len(cliente.casos) if cliente.casos else 0
    
    try:
        logger.info(
            f"[DELETE] Cliente {cliente_id} será eliminado con {num_facturas} facturas "
            f"y {num_casos} casos por user_id={current_user.id} ({current_user.role})"
        )
        
        db.delete(cliente)
        db.commit()
        
        return {
            "message": "Cliente eliminado correctamente",
            "id": cliente_id,
            "facturas_eliminadas": num_facturas,
            "casos_eliminados": num_casos
        }
    except Exception as e:
        db.rollback()
        logger.error(f"[DELETE] Error eliminando cliente {cliente_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}")
```

**⚠️ IMPORTANTE**: Añadir import al inicio del archivo:
```python
# En línea ~12 de clientes.py, después de imports existentes
import logging

logger = logging.getLogger(__name__)
```

---

### ARCHIVO 8: `app/clientes/page.jsx` (MODIFICAR - Frontend)

**ANTES** (línea 30):
```jsx
          <thead>
            <tr className="border-b border-white/8 text-[#F1F5F9]">
              <th className="py-2 text-left">ID</th>
              <th className="py-2 text-left">Nombre</th>
              <th className="py-2 text-left">CUPS</th>
              <th className="py-2 text-left">Telefono</th>
              <th className="py-2 text-left">Estado</th>
              <th className="py-2 text-left">Facturas</th>
              <th className="py-2 text-left"></th>
            </tr>
          </thead>
```

**DESPUÉS**:
```jsx
          <thead>
            <tr className="border-b border-white/8 text-[#F1F5F9]">
              <th className="py-2 text-left">ID</th>
              <th className="py-2 text-left">Nombre</th>
              <th className="py-2 text-left">CUPS</th>
              <th className="py-2 text-left">Telefono</th>
              <th className="py-2 text-left">Estado</th>
              <th className="py-2 text-left">Facturas</th>
              <th className="py-2 text-left">Acciones</th>
            </tr>
          </thead>
```

**ANTES** (línea 57):
```jsx
                  <td className="py-3 text-right">
                    <Link href={`/clientes/${c.id}`} className="text-emerald-400 hover:text-emerald-300">
                      Ver detalle
                    </Link>
                  </td>
```

**DESPUÉS**:
```jsx
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <Link href={`/clientes/${c.id}`} className="text-emerald-400 hover:text-emerald-300">
                        Ver detalle
                      </Link>
                      <ClienteDeleteButton clienteId={c.id} clienteNombre={c.nombre} />
                    </div>
                  </td>
```

---

### ARCHIVO 9: `app/clientes/ClienteDeleteButton.jsx` (NUEVO - Client Component)

```jsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ClienteDeleteButton({ clienteId, clienteNombre }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const router = useRouter();

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/clientes/${clienteId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Error al eliminar cliente");
      }

      const data = await res.json();
      
      // Mostrar toast de éxito
      alert(
        `✅ Cliente eliminado correctamente\n\n` +
        `${data.facturas_eliminadas || 0} facturas eliminadas\n` +
        `${data.casos_eliminados || 0} casos eliminados`
      );
      
      // Refrescar página
      router.refresh();
      setIsModalOpen(false);
    } catch (err) {
      alert(`❌ Error: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      {/* Botón eliminar */}
      <button
        onClick={() => setIsModalOpen(true)}
        className="text-red-400 hover:text-red-300 transition-colors"
        title="Eliminar cliente"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
          />
        </svg>
      </button>

      {/* Modal de confirmación */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#0F172A] rounded-[16px] p-6 max-w-md w-full mx-4 border border-white/10">
            <h3 className="text-lg font-semibold text-white mb-2">
              ¿Eliminar cliente?
            </h3>
            <p className="text-sm text-slate-400 mb-4">
              Estás a punto de eliminar a{" "}
              <span className="text-white font-medium">{clienteNombre || `Cliente #${clienteId}`}</span>.
            </p>
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
              <p className="text-xs text-red-300">
                ⚠️ <strong>Acción irreversible</strong>: Se eliminarán todas las facturas, casos y comisiones asociadas.
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setIsModalOpen(false)}
                disabled={isDeleting}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition disabled:opacity-50"
              >
                {isDeleting ? "Eliminando..." : "Eliminar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

---

**MODIFICAR** `app/clientes/page.jsx` para importar el componente:

**ANTES** (línea 1):
```jsx
import Link from "next/link";
import { listClientes } from "@/lib/apiClient";

export const dynamic = "force-dynamic";
```

**DESPUÉS**:
```jsx
import Link from "next/link";
import { listClientes } from "@/lib/apiClient";
import ClienteDeleteButton from "./ClienteDeleteButton";

export const dynamic = "force-dynamic";
```

---

## ✅ CHECKLIST FINAL DE PRUEBAS MANUALES

### TAREA 1: Versionado de Tarifas

#### Test 1: Migración de base de datos
```bash
# 1. Aplicar migración SQL
psql -U usuario -d mecaenergy -f migrations/20260224_add_tarifa_versioning.sql

# 2. Verificar tablas creadas
SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'tarifa_%';
# Esperado: tarifa_versiones, tarifa_precios

# 3. Verificar columna en ofertas_calculadas
\d ofertas_calculadas
# Esperado: columna "tarifa_version_id"
```

#### Test 2: Crear tarifa versionada de prueba
```sql
-- Insertar versión de tarifa
INSERT INTO tarifa_versiones (nombre, comercializadora, atr, tipo, vigente_desde, version)
VALUES ('Plan Test 2.0TD', 'Test Energy', '2.0TD', 'fija', '2026-02-01', 1)
RETURNING id;

-- Anotar el ID devuelto (ej: 999)

-- Insertar precios de energía (discriminación horaria)
INSERT INTO tarifa_precios (tarifa_version_id, tipo_periodo, periodo_nombre, precio_eur_unidad)
VALUES 
(999, 'energia', 'P1', 0.150),
(999, 'energia', 'P2', 0.120),
(999, 'energia', 'P3', 0.095);

-- Insertar precios de potencia
INSERT INTO tarifa_precios (tarifa_version_id, tipo_periodo, periodo_nombre, precio_eur_unidad)
VALUES 
(999, 'potencia', 'P1', 0.085),
(999, 'potencia', 'P2', 0.042);
```

#### Test 3: Comparar factura 2.0TD con tarifa versionada
```bash
# Usar Postman o curl
curl -X POST "http://localhost:8000/comparar/facturas/321" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"

# Verificar respuesta:
# - offers[0].tarifa_version_id debe existir
# - offers[0].estimated_total debe calcularse correctamente
# - Log: "[VERSIONADO] Encontradas X tarifas vigentes"
```

#### Test 4: Verificar persistencia con tarifa_version_id
```sql
-- Después de comparar factura, verificar ofertas_calculadas
SELECT 
    oc.id,
    oc.tarifa_id,
    oc.tarifa_version_id,
    tv.nombre as tarifa_nombre,
    tv.comercializadora,
    oc.coste_estimado
FROM ofertas_calculadas oc
LEFT JOIN tarifa_versiones tv ON tv.id = oc.tarifa_version_id
WHERE oc.comparativa_id = (SELECT MAX(id) FROM comparativas)
ORDER BY oc.coste_estimado;

-- Esperado: tarifa_version_id NOT NULL en todas las filas nuevas
```

#### Test 5: Tarifa plana 24H
```sql
-- Crear tarifa con precio único 24H
INSERT INTO tarifa_versiones (nombre, comercializadora, atr, vigente_desde, version)
VALUES ('Plan 24H Flat', 'Test Energy', '2.0TD', '2026-02-01', 1)
RETURNING id;

-- Anotar ID (ej: 1000)

-- Insertar precio 24H
INSERT INTO tarifa_precios (tarifa_version_id, tipo_periodo, periodo_nombre, precio_eur_unidad)
VALUES (1000, 'energia', '24H', 0.135);

-- Comparar factura → debe usar mismo precio para P1, P2, P3
```

---

### TAREA 2: Borrar Cliente

#### Test 6: Borrar cliente SIN facturas/casos (limpio)
```bash
# 1. Crear cliente de prueba
curl -X POST "http://localhost:8000/api/clientes" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Cliente Test Delete",
    "email": "delete@test.com"
  }'

# Anotar ID (ej: 555)

# 2. Borrar desde frontend
# Ir a /clientes
# Buscar "Cliente Test Delete"
# Pulsar icono basura
# Confirmar modal
# Verificar: toast de éxito "0 facturas eliminadas, 0 casos eliminados"
```

#### Test 7: Borrar cliente CON facturas y casos
```sql
-- 1. Verificar cliente con dependencias
SELECT 
    c.id,
    c.nombre,
    COUNT(DISTINCT f.id) as num_facturas,
    COUNT(DISTINCT cas.id) as num_casos
FROM clientes c
LEFT JOIN facturas f ON f.cliente_id = c.id
LEFT JOIN casos cas ON cas.cliente_id = c.id
WHERE c.id = 123  -- ID cliente real con facturas
GROUP BY c.id, c.nombre;

-- 2. Borrar desde frontend (icono basura)
-- 3. Verificar: toast muestra "X facturas eliminadas, Y casos eliminados"

-- 4. Confirmar cascada en DB
SELECT COUNT(*) FROM facturas WHERE cliente_id = 123;  -- Debe ser 0
SELECT COUNT(*) FROM casos WHERE cliente_id = 123;      -- Debe ser 0
```

#### Test 8: Permisos - COMERCIAL no puede borrar
```bash
# Login como COMERCIAL
# Ir a /clientes
# Intentar borrar cliente
# Esperado: HTTP 403 "No tienes permisos para eliminar clientes"
```

#### Test 9: Permisos - CEO solo borra clientes de su company
```bash
# Login como CEO de company_id=1
# Intentar borrar cliente con company_id=2
# Esperado: HTTP 403 "No puedes eliminar clientes de otras empresas"
```

#### Test 10: Permisos - DEV puede borrar cualquier cliente
```bash
# Login como DEV (company_id=NULL)
# Borrar cliente de cualquier company
# Esperado: HTTP 200 OK
```

---

## 📝 NOTAS FINALES

### ⚠️ LIMITACIONES Y DECISIONES DE DISEÑO

1. **Tablas NO ENCONTRADAS**: He propuesto estructura completa de `tarifa_versiones` y `tarifa_precios` basándome en mejores prácticas. Si el usuario tiene otra estructura, debe adaptar los queries.

2. **Compatibilidad hacia atrás**: Se mantiene `tarifa_id` legacy en `ofertas_calculadas` para no romper frontend existente que lea ese campo.

3. **Estrategia de borrado**: HARD DELETE con CASCADE automático (ya configurado en ORM). No implemento soft delete porque requiere más cambios (columna `deleted_at`, filtros en todos los queries, etc).

4. **Sin toast library**: Frontend usa `alert()` nativo. Para producción, recomiendo integrar `react-hot-toast` o `sonner`.

5. **Fallback BOE 2025**: Se mantiene en código para compatibilidad con tarifas legacy sin precios de potencia. Considerar mover a tabla `parametros_regulados` en futuro.

---

### 📊 MÉTRICAS ESTIMADAS

- **Líneas de código modificadas**: ~150
- **Líneas de código nuevo**: ~350
- **Archivos modificados**: 4
- **Archivos nuevos**: 5
- **Queries SQL nuevas**: 3 (tarifa_versiones + tarifa_precios + prefetch)
- **Riesgo de regresión**: BAJO (cambios aislados, compatibilidad hacia atrás)

---

### 🚀 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

1. Aplicar migración SQL (`20260224_add_tarifa_versioning.sql`)
2. Crear `models_tarifas.py`
3. Modificar `models.py` (añadir columnas + import)
4. Modificar `comparador.py` (helpers + compare_factura + _insert_ofertas)
5. Crear tarifa versionada de prueba en DB
6. Test comparador con Postman
7. Modificar backend `clientes.py` (permisos)
8. Crear `ClienteDeleteButton.jsx`
9. Modificar `clientes/page.jsx` (import + botón)
10. Test borrar cliente desde UI

---

**FIN DEL PLAN**

¿Necesitas aclaraciones sobre algún PATCH específico o quieres que genere código adicional?
