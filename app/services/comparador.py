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


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        raw = raw.replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    raw = str(value).strip()
    if not raw:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    raw_norm = re.sub(r"\s+", " ", raw.lower())
    match = re.match(r"^(\d{1,2}) de ([a-z]+) de (\d{4})$", raw_norm)
    if not match:
        return None

    day = int(match.group(1))
    month_name = match.group(2)
    year = int(match.group(3))

    months = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "setiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }
    month = months.get(month_name)
    if not month:
        return None

    try:
        return date(year, month, day)
    except ValueError:
        return None


def _get_days(factura) -> int:
    """
    DEPRECATED: Usar periodo_dias directamente.
    Calcula días desde fechas o devuelve None si no hay fechas.
    P1: NO usa fallback a 30 días.
    """
    start = _parse_date(getattr(factura, "fecha_inicio", None))
    end = _parse_date(getattr(factura, "fecha_fin", None))
    if start and end:
        delta = (end - start).days
        if delta > 0:
            return delta
    return None  # P1: NO fallback


def _pick_value(mapping, keys, default):
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return value
    return default


def _resolve_energy_prices(mapping):
    p1_price = _to_float(mapping.get("energia_p1_eur_kwh"))
    p2_price = _to_float(mapping.get("energia_p2_eur_kwh"))
    p3_price = _to_float(mapping.get("energia_p3_eur_kwh"))

    if p1_price is None:
        return None, None

    if p2_price is None and p3_price is None:
        return "24h", (p1_price, p1_price, p1_price)

    if p2_price is not None and p3_price is not None:
        return "3p", (p1_price, p2_price, p3_price)

    return None, None


def _get_table_columns(db, table_name: str) -> Dict[str, Dict[str, Any]]:
    if table_name in _TABLE_COLUMNS_CACHE:
        return _TABLE_COLUMNS_CACHE[table_name]

    columns: Dict[str, Dict[str, Any]] = {}

    try:
        result = db.execute(
            text(
                "SELECT column_name, data_type, is_nullable, column_default "
                "FROM information_schema.columns "
                "WHERE table_schema = :schema AND table_name = :table"
            ),
            {"schema": "public", "table": table_name},
        )
        try:
            rows = result.mappings().all()
        except AttributeError:
            rows = [row._mapping for row in result.fetchall()]

        for row in rows:
            columns[row["column_name"]] = {
                "data_type": (row.get("data_type") or "").lower(),
                "is_nullable": row.get("is_nullable") == "YES",
                "default": row.get("column_default"),
            }
    except Exception:
        columns = {}

    if not columns:
        try:
            inspector = inspect(db.get_bind())
            if table_name in inspector.get_table_names():
                for col in inspector.get_columns(table_name):
                    columns[col["name"]] = {
                        "data_type": (str(col.get("type") or "")).lower(),
                        "is_nullable": bool(col.get("nullable", True)),
                        "default": col.get("default"),
                    }
        except Exception as exc:
            logger.warning("Could not inspect table %s: %s", table_name, exc)
            columns = {}

    _TABLE_COLUMNS_CACHE[table_name] = columns
    return columns


def _missing_required_columns(
    columns_info: Dict[str, Dict[str, Any]], provided_keys
) -> list:
    missing = []
    for name, info in columns_info.items():
        if name in provided_keys:
            continue
        if info.get("is_nullable") is False and not info.get("default"):
            missing.append(name)
    return missing


def _build_insert_sql(
    table_name: str,
    payload: Dict[str, Any],
    columns_info: Dict[str, Dict[str, Any]],
    dialect_name: str,
) -> str:
    columns = list(payload.keys())
    placeholders = []
    for col in columns:
        placeholder = f":{col}"
        if col == "detalle_json" and dialect_name == "postgresql":
            data_type = (columns_info.get(col) or {}).get("data_type")
            if data_type in ("json", "jsonb"):
                placeholder = f":{col}::{data_type}"
        placeholders.append(placeholder)

    columns_sql = ", ".join(columns)
    values_sql = ", ".join(placeholders)
    return f"INSERT INTO {table_name} ({columns_sql}) VALUES ({values_sql})"


def _insert_comparativa(db, factura_id: int) -> Optional[int]:
    columns_info = _get_table_columns(db, "comparativas")
    if not columns_info:
        return None

    payload: Dict[str, Any] = {}
    if "factura_id" in columns_info:
        payload["factura_id"] = factura_id

    missing = _missing_required_columns(columns_info, payload.keys())
    if missing:
        logger.warning(
            "Comparativas insert skipped, missing required columns: %s",
            ", ".join(missing),
        )
        return None

    dialect_name = db.get_bind().dialect.name
    if payload:
        sql = _build_insert_sql("comparativas", payload, columns_info, dialect_name)
        if "id" in columns_info and dialect_name == "postgresql":
            sql += " RETURNING id"
        result = db.execute(text(sql), payload)
    else:
        sql = "INSERT INTO comparativas DEFAULT VALUES"
        if "id" in columns_info and dialect_name == "postgresql":
            sql += " RETURNING id"
        result = db.execute(text(sql))

    comparativa_id = None
    if "id" in columns_info and dialect_name == "postgresql":
        row = result.fetchone()
        if row is not None:
            try:
                comparativa_id = row._mapping.get("id")
            except Exception:
                comparativa_id = row[0]

    return comparativa_id


def _insert_ofertas(db, factura_id: int, comparativa_id: int, offers) -> bool:
    """
    Persiste ofertas en 'ofertas_calculadas' siguiendo esquema estricto Neon.
    Borra ofertas previas del mismo comparativa_id.
    """
    if comparativa_id is None:
        return False
        
    try:
        # 1. Clean previous for this comparison
        db.execute(
            text("DELETE FROM ofertas_calculadas WHERE comparativa_id = :cid"),
            {"cid": comparativa_id}
        )
        
        # 2. Insert new
        count = 0
        is_postgres = db.get_bind().dialect.name == "postgresql"
        
        logger.info(f"[OFERTAS] _insert_ofertas ENTER: comparativa_id={comparativa_id}, received {len(offers)} offers")
        
        # ⭐ PREFETCH: Obtener cliente_id y todas las comisiones (evita N+1 queries)
        factura_row = db.execute(
            text("SELECT cliente_id FROM facturas WHERE id = :fid"),
            {"fid": factura_id}
        ).fetchone()
        cliente_id = factura_row[0] if factura_row else None
        
        # Extraer todos los tarifa_id de las ofertas
        tarifa_ids = [o.get("tarifa_id") for o in offers if o.get("tarifa_id") is not None]
        
        # Prefetch comisiones_cliente (selecciona MÁS RECIENTE por vigente_desde DESC, created_at DESC)
        comisiones_cliente_map = {}
        if cliente_id and tarifa_ids:
            rows = db.execute(
                text("""
                    WITH ranked AS (
                        SELECT 
                            tarifa_id,
                            comision_eur,
                            ROW_NUMBER() OVER (
                                PARTITION BY tarifa_id 
                                ORDER BY 
                                    COALESCE(vigente_desde, '1900-01-01') DESC,
                                    COALESCE(created_at, '1900-01-01 00:00:00') DESC
                            ) as rn
                        FROM comisiones_cliente
                        WHERE cliente_id = :cid AND tarifa_id = ANY(:tids)
                    )
                    SELECT tarifa_id, comision_eur
                    FROM ranked
                    WHERE rn = 1
                """),
                {"cid": cliente_id, "tids": tarifa_ids}
            ).fetchall()
            comisiones_cliente_map = {row[0]: Decimal(str(row[1])) for row in rows}
        
        # Prefetch comisiones_tarifa activas (selecciona MÁS RECIENTE vigente)
        comisiones_tarifa_map = {}
        if tarifa_ids:
            rows = db.execute(
                text("""
                    WITH ranked AS (
                        SELECT 
                            tarifa_id,
                            comision_eur,
                            ROW_NUMBER() OVER (
                                PARTITION BY tarifa_id 
                                ORDER BY vigente_desde DESC, created_at DESC
                            ) as rn
                        FROM comisiones_tarifa
                        WHERE tarifa_id = ANY(:tids) AND vigente_hasta IS NULL
                    )
                    SELECT tarifa_id, comision_eur
                    FROM ranked
                    WHERE rn = 1
                """),
                {"tids": tarifa_ids}
            ).fetchall()
            comisiones_tarifa_map = {row[0]: Decimal(str(row[1])) for row in rows}
        
        logger.info(f"[COMISION] Prefetch: cliente_id={cliente_id}, {len(comisiones_cliente_map)} cliente, {len(comisiones_tarifa_map)} tarifa")
        
        for idx, offer in enumerate(offers):
            tid = offer.get("tarifa_id")
            if tid is None:
                logger.warning(f"[OFERTAS] Skipping offer {idx+1} (no tarifa_id): {offer.get('plan_name', 'unknown')}")
                continue
            
            # ⭐ RESOLUCIÓN DE COMISIÓN (usando diccionarios prefetcheados)
            comision_eur = Decimal("0.00")
            comision_source = "manual"
            
            # Prioridad 1: Comisión por cliente específico
            if tid in comisiones_cliente_map:
                comision_eur = comisiones_cliente_map[tid]
                comision_source = "cliente"
            # Prioridad 2: Comisión por tarifa activa
            elif tid in comisiones_tarifa_map:
                comision_eur = comisiones_tarifa_map[tid]
                comision_source = "tarifa"
            # Prioridad 3: Manual (0.0) - ya es el default
            
            logger.debug(f"[COMISION] factura_id={factura_id} tarifa_id={tid} comision={comision_eur:.2f} source={comision_source}")  # DEBUG no INFO
            
            # Agregar comisión al offer JSON
            offer["comision_eur"] = str(comision_eur)  # JSON exacto, sin artefactos
            offer["comision_source"] = comision_source
                
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
            
            logger.debug(f"[OFERTAS] Inserting offer {idx+1}/{len(offers)}: tarifa_id={tid}, coste={payload['coste_estimado']}, comision={comision_eur:.2f}")  # DEBUG
            
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
                logger.debug(f"[OFERTAS] ✅ Offer {idx+1} inserted successfully")  # DEBUG
            except Exception as insert_error:
                logger.error(
                    f"[OFERTAS] ❌ FAILED inserting offer {idx+1}: {insert_error}\nPayload: {payload}",
                    exc_info=True
                )
                raise
            
        logger.info(f"Inserted {count} offers for comparativa_id={comparativa_id}")
        return count > 0
        
    except Exception as e:
        # ⭐ FIX P2-1: Logging mejorado con traceback completo
        logger.error(
            f"Error persisting offers (Comparativa {comparativa_id}, Factura {factura_id}): {e}",
            exc_info=True  # Incluye traceback completo en logs
        )
        # No re-raise para no romper el flujo principal del comparador
        return False

# ⭐ _persist_results ELIMINADA - ahora todo se hace en una sola transacción en compare_factura


def compare_factura(factura, db) -> Dict[str, Any]:
    """
    P1 PRODUCCIÓN: Compara ofertas usando el periodo REAL de la factura.
    NO usa fallback a 30 días. Lanza DomainError si falta periodo.
    """
    current_total = _to_float(getattr(factura, "total_factura", None))
    if current_total is None or current_total <= 0:
        raise DomainError("TOTAL_INVALID", "La factura no tiene un total válido para comparar")

    # ⭐ CAMBIO 1: DETERMINACIÓN DE ATR (PRIORIDAD AL OCR)
    # 1) Si factura.atr viene del OCR, usarlo TAL CUAL
    # 2) SOLO si factura.atr es NULL/vacío, inferir por potencia
    
    atr_from_ocr = getattr(factura, "atr", None)
    if atr_from_ocr and atr_from_ocr.strip():
        # Prioridad 1: ATR detectado por OCR
        atr = atr_from_ocr.strip().upper()
        logger.info(f"[3.0TD] ATR tomado de OCR: {atr} (factura_id={factura.id})")
    else:
        # Prioridad 2: Inferir por potencia (heurística)
        potencia_p1 = _to_float(getattr(factura, "potencia_p1_kw", None)) or 0.0
        if potencia_p1 >= 15:
            atr = "3.0TD"
            logger.info(f"[3.0TD] ATR inferido por potencia (P1={potencia_p1}): {atr} (factura_id={factura.id})")
        else:
            atr = "2.0TD"
            logger.info(f"[3.0TD] ATR inferido por potencia (P1={potencia_p1}): {atr} (factura_id={factura.id})")
    
    # Configurar periodos según ATR
    if atr == "3.0TD":
        num_periodos_energia = 6
        num_periodos_potencia = 2  # ⭐ CAMBIO 2: Solo P1/P2 en factura
    else:  # 2.0TD
        num_periodos_energia = 3
        num_periodos_potencia = 2
    
    # ⭐ CAMBIO 2: VALIDACIÓN DE CAMPOS SEGÚN ATR
    if atr == "2.0TD":
        required_fields = [
            "consumo_p1_kwh", "consumo_p2_kwh", "consumo_p3_kwh",
            "potencia_p1_kw", "potencia_p2_kw",
        ]
    else:  # 3.0TD
        # ⭐ SOLO consumos P1-P6 + potencias P1-P2
        # NO exigimos potencias P3-P6 (no existen en tabla facturas)
        required_fields = [
            "consumo_p1_kwh", "consumo_p2_kwh", "consumo_p3_kwh",
            "consumo_p4_kwh", "consumo_p5_kwh", "consumo_p6_kwh",
            "potencia_p1_kw", "potencia_p2_kw",  # ⭐ Solo P1/P2
        ]
    
    missing = [
        field
        for field in required_fields
        if _to_float(getattr(factura, field, None)) is None
    ]
    if missing:
        raise DomainError(
            "FIELDS_MISSING",
            f"La factura {atr} no tiene datos suficientes para comparar: " + ", ".join(missing)
        )

    # P1: PERIODO OBLIGATORIO (SIN FALLBACK)
    periodo_dias = factura.periodo_dias
    if not periodo_dias:
        # Intentar calcular de fechas
        if factura.fecha_inicio and factura.fecha_fin:
            start = _parse_date(factura.fecha_inicio)
            end = _parse_date(factura.fecha_fin)
            if start and end:
                periodo_dias = (end - start).days
        
        if not periodo_dias:
            raise DomainError("PERIOD_REQUIRED", "Periodo es obligatorio (días o fechas inicio/fin)")
    
    # Validar que periodo sea válido
    if not isinstance(periodo_dias, int) or periodo_dias <= 0:
        raise DomainError("PERIOD_INVALID", "Periodo inválido")

    # LEER CONSUMOS Y POTENCIAS DINÁMICAMENTE
    consumos = []
    for i in range(1, num_periodos_energia + 1):
        consumos.append(_to_float(getattr(factura, f"consumo_p{i}_kwh", None)) or 0.0)
    
    # ⭐ CAMBIO 4: POTENCIAS EN 3.0TD
    potencias = []
    if atr == "3.0TD":
        # En 3.0TD: solo tenemos potencia_p1 y potencia_p2 en la factura
        # Replicamos P2 para P3-P6 internamente (solo para cálculos)
        p1 = _to_float(getattr(factura, "potencia_p1_kw", None)) or 0.0
        p2 = _to_float(getattr(factura, "potencia_p2_kw", None)) or 0.0
        potencias = [p1, p2, p2, p2, p2, p2]  # P1, P2, P3=P2, P4=P2, P5=P2, P6=P2
        logger.info(f"[3.0TD] Potencias replicadas: P1={p1}, P2-P6={p2} (factura_id={factura.id})")
    else:
        # En 2.0TD: leemos P1 y P2 normalmente
        for i in range(1, num_periodos_potencia + 1):
            potencias.append(_to_float(getattr(factura, f"potencia_p{i}_kw", None)) or 0.0)

    result = db.execute(
        text("SELECT * FROM tarifas WHERE atr = :atr"),
        {"atr": atr},  # Usa el ATR detectado automáticamente (2.0TD o 3.0TD)
    )
    try:
        tarifas = result.mappings().all()
    except AttributeError:
        tarifas = [row._mapping for row in result.fetchall()]

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
        
        # Calcular coste de energía
        coste_energia = sum(
            consumos[i] * (precios_energia[i] or 0.0)
            for i in range(num_periodos_energia)
        )
        modo_energia = f"{num_periodos_energia}p_dinamico"

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
        
        # Calcular coste de potencia
        coste_potencia = periodo_dias * sum(
            potencias[i] * precios_potencia[i]
            for i in range(num_periodos_potencia)
        )
        
        # Determinar modo de potencia
        if tiene_precios_potencia:
            modo_potencia = "tarifa"
        else:
            modo_potencia = "boe_2025_regulado"

        # TOTALIZACIÓN CON IMPUESTOS (Para igualar factura real)
        subtotal = coste_energia + coste_potencia
        
        # ===== IMPUESTO ELÉCTRICO (IEE) =====
        # PRIORIDAD 1: Usar valor real de la factura si existe
        if hasattr(factura, 'impuesto_electrico') and factura.impuesto_electrico is not None:
            impuesto_electrico = float(factura.impuesto_electrico)
            modo_iee = "factura_real"
        else:
            # FALLBACK: Calcular con porcentaje fijo 5.11269632%
            impuesto_electrico = subtotal * 0.0511269632
            modo_iee = "calculado_5.11%"
        
        # ===== ALQUILER CONTADOR =====
        # PRIORIDAD 1: Usar valor real de la factura si existe
        # PRIORIDAD 2: Si NO está en factura, NO lo incluimos (asumimos que no aplica)
        if hasattr(factura, 'alquiler_contador') and factura.alquiler_contador is not None:
            alquiler_equipo = float(factura.alquiler_contador)
            modo_alquiler = "factura_real"
        else:
            # NO incluir alquiler si no está en la factura
            alquiler_equipo = 0.0
            modo_alquiler = "no_aplica"
        
        base_imponible = subtotal + impuesto_electrico + alquiler_equipo
        
        # ===== IVA =====
        # PRIORIDAD 1: Usar el valor que viene de la factura (seleccionado por el usuario o extraído)
        if hasattr(factura, 'iva_porcentaje') and factura.iva_porcentaje is not None:
            iva_pct = float(factura.iva_porcentaje) / 100.0
            modo_iva = f"usuario_{int(factura.iva_porcentaje)}%"
        else:
            # FALLBACK: 21% por defecto (Estándar actual)
            iva_pct = 0.21
            modo_iva = "defecto_21%"
        
        iva_importe = base_imponible * iva_pct
        
        estimated_total_periodo = base_imponible + iva_importe
        
        # Cálculo Ahorro
        ahorro_periodo = current_total - estimated_total_periodo
        
        # Proyecciones
        ahorro_mensual_equiv = ahorro_periodo * (30.437 / periodo_dias)
        ahorro_anual_equiv = ahorro_periodo * (365 / periodo_dias)
        
        saving_percent = (
            (ahorro_periodo / current_total) * 100 if current_total > 0 else 0.0
        )

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

        offer = {
            "tarifa_id": tarifa_id,
            "provider": provider,
            "plan_name": plan_name,
            "estimated_total": round(estimated_total_periodo, 2),  # Frontend expects this
            "saving_amount": round(ahorro_periodo, 2),  # Frontend expects this
            "estimated_total_periodo": round(estimated_total_periodo, 2),
            "ahorro_periodo": round(ahorro_periodo, 2),
            "ahorro_mensual_equiv": round(ahorro_mensual_equiv, 2),
            "ahorro_anual_equiv": round(ahorro_anual_equiv, 2),
            "saving_percent": round(saving_percent, 2),
            "commission": 0,  # TODO: Add commission logic if needed
            "tag": "balanced",
            "breakdown": {
                "periodo_dias": int(periodo_dias),
                "coste_energia": round(coste_energia, 2),
                "coste_potencia": round(coste_potencia, 2),
                "impuestos": round(impuesto_electrico + iva_importe, 2),
                "alquiler_contador": round(alquiler_equipo, 2),
                "modo_energia": modo_energia,
                "modo_potencia": modo_potencia,
                "modo_iee": modo_iee,
                "modo_iva": modo_iva,
                "modo_alquiler": modo_alquiler,
            },
        }

        offers.append(offer)

    completas = [item for item in offers if item["breakdown"]["modo_potencia"] == "tarifa"]
    parciales = [item for item in offers if item["breakdown"]["modo_potencia"] != "tarifa"]

    completas.sort(key=lambda item: item["estimated_total_periodo"])
    parciales.sort(key=lambda item: item["estimated_total_periodo"])

    for item in parciales:
        item["tag"] = "partial"

    if completas:
        max_saving = max(item["ahorro_periodo"] for item in completas)
        for item in completas:
            if item["ahorro_periodo"] == max_saving:
                item["tag"] = "best_saving"
            else:
                item["tag"] = "balanced"

    offers = completas + parciales

    # ⭐ FIX CRÍTICO: PERSISTIR COMPARATIVA + OFERTAS EN UNA SOLA TRANSACCIÓN
    comparativa_id = None
    try:
        logger.info(f"[OFERTAS] ENTER persistence for factura_id={factura.id}")
        
        # 1. Crear comparativa
        inputs_snapshot = {
            "cups": factura.cups,
            "atr": atr,
        }
        
        for i in range(1, num_periodos_energia + 1):
            inputs_snapshot[f"consumo_p{i}"] = getattr(factura, f"consumo_p{i}_kwh", None)
        
        for i in range(1, num_periodos_potencia + 1):
            inputs_snapshot[f"potencia_p{i}"] = getattr(factura, f"potencia_p{i}_kw", None)
        
        comparativa = Comparativa(
            factura_id=factura.id,
            periodo_dias=periodo_dias,
            current_total=current_total,
            inputs_json=json.dumps(inputs_snapshot),
            offers_json=json.dumps(offers),
            status="ok"
        )
        db.add(comparativa)
        db.flush()  # ⭐ FLUSH (no COMMIT) para obtener ID sin cerrar transacción
        comparativa_id = comparativa.id
        
        logger.info(f"[OFERTAS] Comparativa created with id={comparativa_id}")
        
        # 2. Insertar ofertas_calculadas (dentro de la MISMA transacción)
        logger.info(f"[OFERTAS] comparativa_id={comparativa_id} offers_count={len(offers)}")
        logger.info(f"[OFERTAS] tarifa_ids={[o.get('tarifa_id') for o in offers][:20]}")
        inserted = _insert_ofertas(db, factura.id, comparativa_id, offers)
        
        if not inserted:
            logger.error(f"[OFERTAS] ZERO offers inserted for comparativa_id={comparativa_id}")
            comparativa.status = "error"
            comparativa.error_json = json.dumps({"error": "No offers inserted"})
        
        # 3. COMMIT ÚNICO para ambas operaciones
        db.commit()
        logger.info(f"[OFERTAS] Transaction committed successfully for comparativa_id={comparativa_id}")
        
    except Exception as e:
        db.rollback()  # ⭐ ROLLBACK INMEDIATO
        logger.error(
            f"[OFERTAS] ROLLBACK - Error persisting comparativa+offers for factura_id={factura.id}: {e}",
            exc_info=True
        )
        
        # ⭐ FIX BUG 2: Actualizar comparativa en NUEVA transacción
        if comparativa_id:
            try:
                # Usar ORM en vez de text() después de rollback
                comp = db.query(Comparativa).filter(Comparativa.id == comparativa_id).first()
                if comp:
                    comp.status = "error"
                    comp.error_json = json.dumps({"error": str(e)})
                    db.commit()
            except Exception as update_error:
                logger.warning(f"[OFERTAS] Could not update comparativa status: {update_error}")
                db.rollback()

    return {
        "factura_id": factura.id,
        "comparativa_id": comparativa_id,
        "periodo_dias": periodo_dias,
        "current_total": round(current_total, 2),
        "offers": offers,
    }
