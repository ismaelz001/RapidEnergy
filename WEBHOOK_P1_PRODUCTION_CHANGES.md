# P1 PRODUCCIÓN: Cambios necesarios en webhook.py

## PARTE 1: Imports (añadir al inicio)

```python
from app.exceptions import DomainError
```

## PARTE 2: FacturaUpdate (línea ~12-43)

BUSCAR:
```python
class FacturaUpdate(BaseModel):
    atr: Optional[str] = None
    # ... otros campos ...
```

AÑADIR:
```python
    periodo_dias: Optional[int] = None
```

## PARTE 3: Validación periodo (línea ~66, después de CUPS)

BUSCAR:
```python
    # Validación CUPS obligatoria
    if not factura.cups or not str(factura.cups).strip():
        errors["cups"] = "CUPS es obligatorio y no puede estar vacío"
    
    for field in REQUIRED_FACTURA_FIELDS:
```

REEMPLAZAR POR:
```python
    # Validación CUPS obligatoria
    if not factura.cups or not str(factura.cups).strip():
        errors["cups"] = "CUPS es obligatorio y no puede estar vacío"
    
    # P1: Validación PERIODO obligatoria (sin fallback)
    if not factura.periodo_dias:
        if not (factura.fecha_inicio and factura.fecha_fin):
            errors["periodo"] = "Periodo es obligatorio (días o fechas inicio/fin)"
    elif factura.periodo_dias <= 0:
        errors["periodo"] = "Periodo debe ser mayor a 0"
    
    for field in REQUIRED_FACTURA_FIELDS:
```

## PARTE 4: Guardar periodo_dias en upload (línea ~280)

BUSCAR donde se crea `nueva_factura` y AÑADIR:
```python
nueva_factura = Factura(
    filename=file.filename,
    cups=normalize_cups(ocr_data.get("cups")),
    # ... otros campos ...
    iva=ocr_data.get("iva"),
    periodo_dias=ocr_data.get("dias_facturados"),  # <-- AÑADIR
)
```

## PARTE 5: Endpoint compare con manejo de errores (línea ~570+)

BUSCAR:
```python
@router.post("/comparar/facturas/{factura_id}")
async def compare_factura_endpoint(...):
```

ENVOLVER con try/except:
```python
@router.post("/comparar/facturas/{factura_id}")
async def compare_factura_endpoint(factura_id: int, db: Session = Depends(get_db)):
    """P1 PRODUCCIÓN: Compara ofertas con manejo robusto de errores"""
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    try:
        result = compare_factura(factura, db)
        return result
    except DomainError as e:
        # Mapear errores de dominio a HTTP 422
        error_messages = {
            "PERIOD_REQUIRED": "Periodo es obligatorio (días o fechas inicio/fin)",
            "PERIOD_INVALID": "Periodo inválido",
            "TOTAL_INVALID": "Total factura inválido",
            "FIELDS_MISSING": e.message
        }
        raise HTTPException(
            status_code=422,
            detail={
                "code": e.code,
                "message": error_messages.get(e.code, e.message)
            }
        )
    except Exception as e:
        logger.error(f"Error inesperado al comparar factura {factura_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al comparar")
```
