# 📄 P1 PRODUCCIÓN - DIFFS POR ARCHIVO

## ARCHIVO 1: app/exceptions.py (NUEVO)

```diff
+ """
+ Excepciones de dominio para MECAENERGY CRM.
+ """
+ 
+ class DomainError(Exception):
+     """Error de dominio/negocio con código específico"""
+     def __init__(self, code: str, message: str = None):
+         self.code = code
+         self.message = message or code
+         super().__init__(self.message)
```

---

## ARCHIVO 2: app/services/comparador.py

### DIFF - Imports (línea ~11)

```diff
  from sqlalchemy import inspect, text
+ from app.exceptions import DomainError
+ from app.db.models import Comparativa
  
  logger = logging.getLogger(__name__)
```

### DIFF - Función compare_factura (REEMPLAZAR ENTERA línea 305-440)

**ANTES:**
```python
def compare_factura(factura, db) -> Dict[str, Any]:
    current_total = _to_float(getattr(factura, "total_factura", None))
    if current_total is None or current_total <= 0:
        raise ValueError("La factura no tiene un total valido para comparar")
    
    # ... validaciones ...
    
    dias = _get_days(factura)  # ❌ FALLBACK A 30!!!
    
    # ... cálculos ...
    
    potencia_p1_price = _to_float(tarifa.get("potencia_p1_eur_kw_dia"))
   potencia_p2_price = _to_float(...)  # ❌ MAL INDENTADO
    
    coste_potencia = dias * (...)
    
    return {
        "factura_id": factura.id,
        "current_total": round(current_total, 2),
        "offers": offers,  # ❌ Sin periodo_dias, sin comparativa_id
    }
```

**DESPUÉS:**
```python
def compare_factura(factura, db) -> Dict[str, Any]:
    """P1 PRODUCCIÓN: Sin fallback, con DomainError"""
    current_total = _to_float(getattr(factura, "total_factura", None))
    if current_total is None or current_total <= 0:
        raise DomainError("TOTAL_INVALID", "Total inválido")  # ✅ DomainError
    
    # ... validaciones con DomainError ...
    
    # ✅ PERIODO OBLIGATORIO SIN FALLBACK
    periodo_dias = factura.periodo_dias
    if not periodo_dias:
        if factura.fecha_inicio and factura.fecha_fin:
            start = _parse_date(factura.fecha_inicio)
            end = _parse_date(factura.fecha_fin)
            if start and end:
                periodo_dias = (end - start).days
        
        if not periodo_dias:
            raise DomainError("PERIOD_REQUIRED", "Periodo obligatorio")
    
    if not isinstance(periodo_dias, int) or periodo_dias <= 0:
        raise DomainError("PERIOD_INVALID", "Periodo inválido")
    
    # ... cálculos ...
    
    # ✅ INDENTACIÓN CORRECTA
    potencia_p1_price = _to_float(tarifa.get("potencia_p1_eur_kw_dia"))
    potencia_p2_price = _to_float(tarifa.get("potencia_p2_eur_kw_dia"))
    
    coste_potencia = periodo_dias * (...)  # ✅ periodo real
    
    # ✅ EQUIVALENTES
    ahorro_periodo = current_total - estimated_total_periodo
    ahorro_mensual_equiv = ahorro_periodo * (30.437 / periodo_dias)
    ahorro_anual_equiv = ahorro_periodo * (365 / periodo_dias)
    
    # ✅ AUDITORÍA
    comparativa = Comparativa(...)
    db.add(comparativa)
    db.commit()
    
    return {
        "factura_id": factura.id,
        "comparativa_id": comparativa_id,  # ✅ NUEVO
        "periodo_dias": periodo_dias,       # ✅ NUEVO
        "current_total": round(current_total, 2),
        "offers": offers,  # Con ahorro_mensual_equiv, ahorro_anual_equiv
    }
```

---

## ARCHIVO 3: app/routes/webhook.py

### DIFF 1 - Import (línea ~1)

```diff
  from fastapi import APIRouter, UploadFile, Depends, HTTPException
  from sqlalchemy.orm import Session, joinedload
  from app.db.conn import get_db
  from app.db.models import Factura, Cliente
+ from app.exceptions import DomainError
  from pydantic import BaseModel
```

### DIFF 2 - FacturaUpdate (línea ~30)

```diff
  class FacturaUpdate(BaseModel):
      # ... otros campos ...
      cups: Optional[str] = None
      numero_factura: Optional[str] = None
+     periodo_dias: Optional[int] = None  # ✅ NUEVO
```

### DIFF 3 - Validación periodo (línea ~66)

```diff
  # Validación CUPS obligatoria
  if not factura.cups or not str(factura.cups).strip():
      errors["cups"] = "CUPS es obligatorio y no puede estar vacío"
  
+ # P1: Validación PERIODO obligatoria
+ if not factura.periodo_dias:
+     if not (factura.fecha_inicio and factura.fecha_fin):
+         errors["periodo"] = "Periodo es obligatorio (días o fechas)"
+ elif factura.periodo_dias <= 0:
+     errors["periodo"] = "Periodo debe ser mayor a 0"
  
  for field in REQUIRED_FACTURA_FIELDS:
```

### DIFF 4 - Upload guardar periodo (línea ~280)

```diff
  nueva_factura = Factura(
      filename=file.filename,
      cups=normalize_cups(ocr_data.get("cups")),
      # ... otros campos ...
      iva=ocr_data.get("iva"),
+     periodo_dias=ocr_data.get("dias_facturados"),  # ✅ NUEVO
  )
```

### DIFF 5 - Endpoint compare con manejo errores (línea ~570)

**ANTES:**
```python
@router.post("/comparar/facturas/{factura_id}")
async def compare_factura_endpoint(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    result = compare_factura(factura, db)  # ❌ Sin try/except
    return result
```

**DESPUÉS:**
```python
@router.post("/comparar/facturas/{factura_id}")
async def compare_factura_endpoint(factura_id: int, db: Session = Depends(get_db)):
    """P1 PRODUCCIÓN: Con manejo robusto de errores"""
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    try:
        result = compare_factura(factura, db)
        return result
    except DomainError as e:
        # ✅ Mapear a HTTP 422
        error_map = {
            "PERIOD_REQUIRED": "Periodo es obligatorio (días o fechas)",
            "PERIOD_INVALID": "Periodo inválido",
            "TOTAL_INVALID": "Total factura inválido",
            "FIELDS_MISSING": e.message
        }
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": error_map.get(e.code, e.message)}
        )
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail="Error interno")
```

---

## ARCHIVO 4: app/db/models.py (Ya aplicado✅)

```diff
  class Factura(Base):
      # ... campos existentes ...
      total_factura = Column(Float, nullable=True)
+     periodo_dias = Column(Integer, nullable=True)  # ✅ YA HECHO
      estado_factura = Column(String, default="pendiente_datos")

+ class Comparativa(Base):  # ✅ YA HECHO
+     __tablename__ = "comparativas"
+     id = Column(Integer, primary_key=True, index=True)
+     factura_id = Column(Integer, ForeignKey("facturas.id"))
+     periodo_dias = Column(Integer, nullable=True)
+     current_total = Column(Float, nullable=True)
+     inputs_json = Column(Text, nullable=True)
+     offers_json = Column(Text, nullable=True)
+     status = Column(String, default="ok")
+     created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## SQL: migration_p1_NEON_PRODUCTION.sql

```sql
-- ✅ EJECUTAR EN NEON SQL EDITOR

ALTER TABLE facturas 
ADD COLUMN IF NOT EXISTS periodo_dias INTEGER;

CREATE TABLE IF NOT EXISTS comparativas (
    id SERIAL PRIMARY KEY,
    factura_id INTEGER NOT NULL REFERENCES facturas(id) ON DELETE CASCADE,
    periodo_dias INTEGER NOT NULL,
    current_total NUMERIC(10, 2),
    inputs_json JSONB,
    offers_json JSONB,
    status VARCHAR(20) DEFAULT 'ok',
    error_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comparativas_factura_id ON comparativas(factura_id);
CREATE INDEX IF NOT EXISTS idx_comparativas_created_at ON comparativas(created_at DESC);
```

---

## 📊 RESUMEN DE Cambios

| Archivo | Líneas Añadidas | Líneas Eliminadas | Complejidad |
|---------|----------------|-------------------|-------------|
| exceptions.py | +11 | 0 | Baja |
| comparador.py | +200 | -135 | Alta |
| webhook.py | +35 | -5 | Media |
| models.py | +20 | 0 | Baja |
| **TOTAL** | **~266** | **~140** | **Media-Alta** |

---

## ⚡ CAMBIOS CRÍTICOS

1. ❌ **ELIMINADO:** Fallback a 30 días
2. ✅ **AÑADIDO:** DomainError con códigos
3. ✅ **AÑADIDO:** HTTP 422 para errores de dominio
4. ✅ **CORREGIDO:** Indentación potencia_p2_price
5. ✅ **AÑADIDO:** Persistencia Comparativa
6. ✅ **AÑADIDO:** Equivalentes mensual/anual
7. ✅ **AÑADIDO:** periodo_dias en response

---

**Fecha:** 2026-01-09  
**Tipo:** Producción-ready  
**Backward compatible:** ⚠️ NO (lanza 422 si falta periodo)
