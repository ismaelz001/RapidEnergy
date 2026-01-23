# DIFF para app/services/comparador.py
# Resolución de comisiones en _insert_ofertas

## CAMBIOS EN LA FUNCIÓN _insert_ofertas (líneas ~275-317)

### ANTES:
```python
for idx, offer in enumerate(offers):
    tid = offer.get("tarifa_id")
    if tid is None:
        logger.warning(f"[OFERTAS] Skipping offer {idx+1} (no tarifa_id): {offer.get('plan_name', 'unknown')}")
        continue
        
    payload = {
        "comparativa_id": comparativa_id,
        "tarifa_id": tid,
        "coste_estimado": offer.get("estimated_total_periodo"),
        "ahorro_mensual": offer.get("ahorro_mensual_equiv"),
        "ahorro_anual": offer.get("ahorro_anual_equiv"),
        "detalle_json": json.dumps(offer, ensure_ascii=False)
    }
    
    logger.info(f"[OFERTAS] Inserting offer {idx+1}/{len(offers)}: tarifa_id={tid}, coste={payload['coste_estimado']}")
    
    # SQL explícito con CAST para JSONB en Postgres
    if is_postgres:
        stmt = text("""
            INSERT INTO ofertas_calculadas 
            (comparativa_id, tarifa_id, coste_estimado, ahorro_mensual, ahorro_anual, detalle_json)
            VALUES 
            (:comparativa_id, :tarifa_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, CAST(:detalle_json AS jsonb))
        """)
    else:
        stmt = text("""
            INSERT INTO ofertas_calculadas 
            (comparativa_id, tarifa_id, coste_estimado, ahorro_mensual, ahorro_anual, detalle_json)
            VALUES 
            (:comparativa_id, :tarifa_id, :coste_estimado, :ahorro_mensual, :ahorro_anual, :detalle_json)
        """)
```

### DESPUÉS:
```python
for idx, offer in enumerate(offers):
    tid = offer.get("tarifa_id")
    if tid is None:
        logger.warning(f"[OFERTAS] Skipping offer {idx+1} (no tarifa_id): {offer.get('plan_name', 'unknown')}")
        continue
    
    # ⭐ RESOLUCIÓN DE COMISIÓN (prioridad: cliente > tarifa activa > manual)
    comision_eur = 0.0
    comision_source = "manual"
    cliente_id = None
    
    # Obtener cliente_id de la factura
    factura_row = db.execute(
        text("SELECT cliente_id FROM facturas WHERE id = :fid"),
        {"fid": factura_id}
    ).fetchone()
    
    if factura_row:
        cliente_id = factura_row[0]
    
    # Prioridad 1: Comisión por cliente específico
    if cliente_id:
        comision_cliente = db.execute(
            text("""
                SELECT comision_eur FROM comisiones_cliente
                WHERE cliente_id = :cid AND tarifa_id = :tid
                LIMIT 1
            """),
            {"cid": cliente_id, "tid": tid}
        ).fetchone()
        
        if comision_cliente:
            comision_eur = float(comision_cliente[0])
            comision_source = "cliente"
            logger.info(f"[COMISION] factura_id={factura_id} tarifa_id={tid} comision={comision_eur} source={comision_source}")
    
    # Prioridad 2: Comisión por tarifa activa
    if comision_source == "manual":
        comision_tarifa = db.execute(
            text("""
                SELECT comision_eur FROM comisiones_tarifa
                WHERE tarifa_id = :tid AND vigente_hasta IS NULL
                ORDER BY vigente_desde DESC
                LIMIT 1
            """),
            {"tid": tid}
        ).fetchone()
        
        if comision_tarifa:
            comision_eur = float(comision_tarifa[0])
            comision_source = "tarifa"
            logger.info(f"[COMISION] factura_id={factura_id} tarifa_id={tid} comision={comision_eur} source={comision_source}")
    
    # Prioridad 3: Manual (0.0) - ya está por defecto
    if comision_source == "manual":
        logger.info(f"[COMISION] factura_id={factura_id} tarifa_id={tid} comision={comision_eur} source={comision_source}")
    
    # Agregar comisión al offer JSON
    offer["comision_eur"] = comision_eur
    offer["comision_source"] = comision_source
        
    payload = {
        "comparativa_id": comparativa_id,
        "tarifa_id": tid,
        "coste_estimado": offer.get("estimated_total_periodo"),
        "ahorro_mensual": offer.get("ahorro_mensual_equiv"),
        "ahorro_anual": offer.get("ahorro_anual_equiv"),
        "comision_eur": comision_eur,  # ⭐ Nueva columna
        "comision_source": comision_source,  # ⭐ Nueva columna
        "detalle_json": json.dumps(offer, ensure_ascii=False)  # Incluye comision en JSON
    }
    
    logger.info(f"[OFERTAS] Inserting offer {idx+1}/{len(offers)}: tarifa_id={tid}, coste={payload['coste_estimado']}, comision={comision_eur}")
    
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

---

## RESUMEN DE CAMBIOS:

1. **Resolución de comisión** (líneas +280-325):
   - Obtiene `cliente_id` de la factura
   - Busca en `comisiones_cliente` (prioridad 1)
   - Busca en `comisiones_tarifa` activa (prioridad 2)
   - Default a 0.0 con source="manual" (prioridad 3)

2. **Agregar a JSON** (líneas +326-327):
   - `offer["comision_eur"] = comision_eur`
   - `offer["comision_source"] = comision_source`

3. **Persistir en DB** (líneas +332-334):
   - Agregar `comision_eur` y `comision_source` al payload
   - Modificar INSERT para incluir nuevas columnas

4. **Logs** (líneas +303, +316, +320):
   - `[COMISION] factura_id=X tarifa_id=Y comision=Z source=S`

---

## EJEMPLO DE LOG:

```
[OFERTAS] _insert_ofertas ENTER: comparativa_id=44, received 9 offers
[COMISION] factura_id=184 tarifa_id=11 comision=55.0 source=tarifa
[OFERTAS] Inserting offer 1/9: tarifa_id=11, coste=35.11, comision=55.0
[OFERTAS] ✅ Offer 1 inserted successfully
[COMISION] factura_id=184 tarifa_id=3 comision=0.0 source=manual
[OFERTAS] Inserting offer 2/9: tarifa_id=3, coste=37.5, comision=0.0
[OFERTAS] ✅ Offer 2 inserted successfully
...
```

---

## DEPENDENCIAS (ya existen):

- ✅ Columnas `comision_eur` y `comision_source` en `ofertas_calculadas`
- ✅ Tablas `comisiones_cliente` y `comisiones_tarifa`
- ✅ Relación factura -> cliente

---

## APLICAR CAMBIO:

**Archivo**: `app/services/comparador.py`  
**Función**: `_insert_ofertas`  
**Líneas**: ~275-317 (reemplazar el loop completo)
