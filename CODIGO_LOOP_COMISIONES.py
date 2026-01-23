# CÓDIGO COMPLETO PARA REEMPLAZAR EN comparador.py
# Líneas ~275-317 (el loop for completo)

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
                
            try:
                db.execute(stmt, payload)
                count += 1
                logger.info(f"[OFERTAS] ✅ Offer {idx+1} inserted successfully")
            except Exception as insert_error:
                logger.error(
                    f"[OFERTAS] ❌ FAILED inserting offer {idx+1}: {insert_error}\nPayload: {payload}",
                    exc_info=True
                )
                raise
