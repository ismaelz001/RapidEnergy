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
        
        # Prefetch comisiones_cliente (ORDER BY determinista)
        # ESQUEMA REAL: NO tiene vigente_desde, solo created_at + id
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
                                ORDER BY created_at DESC, id DESC
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
        
        # Prefetch comisiones_tarifa activas (ORDER BY determinista)
        # ESQUEMA REAL: SÍ tiene vigente_desde/vigente_hasta
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
                                ORDER BY vigente_desde DESC, created_at DESC, id DESC
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




def _reconstruir_factura(
    subtotal_sin_impuestos: float,
    iva_pct: float,
    alquiler_total: float = 0.0,
    impuesto_electrico_pct: float = 0.0511269632
) -> float:
    """
    Reconstruye el total de una factura siguiendo el método PO/NodoÁmbar.
    
    ESQUEMA OBLIGATORIO:
    1. Subtotal sin impuestos (energía + potencia, ya calculado)
    2. Impuesto eléctrico = subtotal × 5.11269632%
    3. Alquiler contador (importe total del periodo)
    4. Base IVA = subtotal + IEE + alquiler
    5. IVA = base_IVA × iva_pct
    6. TOTAL = base_IVA + IVA
    
    Args:
        subtotal_sin_impuestos: Coste energía + potencia antes de impuestos
        iva_pct: Porcentaje IVA (ej: 0.21 para 21%)
        alquiler_total: Importe total alquiler del periodo (default 0)
        impuesto_electrico_pct: Porcentaje IEE (default 5.11269632%)
    
    Returns:
        Total factura reconstruida
    """
    # 1. Impuesto eléctrico
    impuesto_electrico = subtotal_sin_impuestos * impuesto_electrico_pct
    
    # 2. Base IVA
    base_iva = subtotal_sin_impuestos + impuesto_electrico + alquiler_total
    
    # 3. IVA
    iva = base_iva * iva_pct
    
    # 4. TOTAL
    total = base_iva + iva
    
    return total


def compare_factura(factura, db) -> Dict[str, Any]:
    """
    P1 PRODUCCIÓN: Compara ofertas usando el periodo REAL de la factura.
    NO usa fallback a 30 días. Lanza DomainError si falta periodo.
    
    ⭐ STEP 2 INTEGRATION: Si la factura pasó por validación comercial,
    usa total_ajustado en vez de total_factura como línea base.
    """
    # Prioridad 1: Total ajustado (si pasó por Step 2)
    # Prioridad 2: Total factura (si no hay Step 2)
    if getattr(factura, "validado_step2", False) and getattr(factura, "total_ajustado", None):
        current_total = _to_float(factura.total_ajustado)
        logger.info(f"[STEP2] Usando total_ajustado={current_total:.2f} como línea base (factura_id={factura.id})")
    else:
        current_total = _to_float(getattr(factura, "total_factura", None))
        logger.info(f"[STEP2] Usando total_factura={current_total:.2f} como línea base (factura_id={factura.id})")
    
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
        {"atr": atr},
    )
    try:
        tarifas = result.mappings().all()
    except AttributeError:
        tarifas = [row._mapping for row in result.fetchall()]
    
    # ⭐ MÉTODO PO/NODOÁMBAR: Calcular subtotal sin impuestos de factura ACTUAL
    # mediante BACKSOLVE desde los importes totales (NO inventar precios)
    
    # Obtener valores de la factura
    total_factura = current_total  # Ya validado antes
    iva_importe = _to_float(getattr(factura, 'iva', None))
    iee_importe = _to_float(getattr(factura, 'impuesto_electrico', None))
    alquiler_importe = _to_float(getattr(factura, 'alquiler_contador', None)) or 0.0
    
    # 🔍 LOGGING: Tipos de inputs para debugging
    logger.info(
        f"[PO-INPUTS] factura_id={factura.id}: iva={iva_importe} (raw_type={type(getattr(factura, 'iva', None)).__name__}), "
        f"iee={iee_importe} (raw_type={type(getattr(factura, 'impuesto_electrico', None)).__name__}), "
        f"alquiler={alquiler_importe} (raw_type={type(getattr(factura, 'alquiler_contador', None)).__name__}), "
        f"periodo_dias={getattr(factura, 'periodo_dias', None)} (raw_type={type(getattr(factura, 'periodo_dias', None)).__name__})"
    )
    
    # Determinar IVA %
    if hasattr(factura, 'iva_porcentaje') and factura.iva_porcentaje is not None:
        iva_pct_reconstruccion = float(factura.iva_porcentaje) / 100.0
    else:
        iva_pct_reconstruccion = 0.21  # 21% por defecto
    
    # ✅ VALIDACIÓN: periodo_dias obligatorio para cálculos de comparador
    periodo_dias = getattr(factura, 'periodo_dias', None)
    if not periodo_dias or periodo_dias <= 0:
        logger.error(f"[PO-ERROR] factura_id={factura.id}: periodo_dias inválido ({periodo_dias}), no se puede calcular comparador")
        raise DomainError(
            "PERIOD_INVALID",
            "El período de facturación (días) es obligatorio y debe ser mayor a 0 para calcular el comparador"
        )
    
    # BACKSOLVE: Calcular subtotal sin impuestos
    baseline_method = "backsolve_subtotal_si"
    
    if iva_importe is not None and iva_importe > 0:
        # Método principal: usar importes directos
        base_iva = total_factura - iva_importe
        iee_used = iee_importe if iee_importe is not None else 0.0
        subtotal_si_actual = base_iva - iee_used - alquiler_importe
        
        logger.info(
            f"[PO] Backsolve: total={total_factura:.2f} iva_imp={iva_importe:.2f} "
            f"base_iva={base_iva:.2f} iee={iee_used:.2f} alq={alquiler_importe:.2f} "
            f"subtotal_si={subtotal_si_actual:.2f}"
        )
    else:
        # Fallback: calcular IVA desde porcentaje
        base_iva = total_factura / (1 + iva_pct_reconstruccion)
        iva_importe = total_factura - base_iva
        iee_used = iee_importe if iee_importe is not None else 0.0
        subtotal_si_actual = base_iva - iee_used - alquiler_importe
        
        logger.info(
            f"[PO] Backsolve (desde %): total={total_factura:.2f} iva_pct={iva_pct_reconstruccion} "
            f"base_iva={base_iva:.2f} iee={iee_used:.2f} alq={alquiler_importe:.2f} "
            f"subtotal_si={subtotal_si_actual:.2f}"
        )
    
    # Validación: si subtotal resultante es negativo o muy bajo, usar fallback
    if subtotal_si_actual < 0 or subtotal_si_actual < (total_factura * 0.3):
        logger.warning(
            f"[PO] Subtotal backsolve sospechoso ({subtotal_si_actual:.2f}€), "
            f"activando fallback a current_total"
        )
        baseline_method = "fallback_current_total"
        total_actual_reconstruido = current_total
    else:
        # Reconstruir factura actual con la MISMA lógica que ofertas
        total_actual_reconstruido = _reconstruir_factura(
            subtotal_sin_impuestos=subtotal_si_actual,
            iva_pct=iva_pct_reconstruccion,
            alquiler_total=alquiler_importe,
            impuesto_electrico_pct=0.0511269632
        )
        
        diff_vs_original = abs(total_actual_reconstruido - current_total)
        logger.info(
            f"[PO] Factura actual reconstruida: {total_actual_reconstruido:.2f}€ "
            f"vs original: {current_total:.2f}€ (diff: {diff_vs_original:.2f}€) "
            f"method={baseline_method}"
        )




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
        
        # ⭐ MÉTODO PO: Calcular subtotal sin impuestos para esta oferta
        subtotal_sin_impuestos_oferta = coste_energia + coste_potencia
        
        # Reconstruir total de oferta con la MISMA función que la actual
        estimated_total_periodo = _reconstruir_factura(
            subtotal_sin_impuestos=subtotal_sin_impuestos_oferta,
            iva_pct=iva_pct,
            alquiler_total=alquiler_equipo,  # Usar mismo alquiler que factura actual
            impuesto_electrico_pct=0.0511269632
        )
        
        # ⭐ CALCULAR BREAKDOWN CORRECTO (mismo esquema que _reconstruir_factura)
        iee_oferta = subtotal_sin_impuestos_oferta * 0.0511269632
        base_iva_oferta = subtotal_sin_impuestos_oferta + iee_oferta + alquiler_equipo
        iva_oferta = base_iva_oferta * iva_pct
        impuestos_oferta = iee_oferta + iva_oferta  # Para breakdown del PDF
        
        # ⭐ MÉTODO PO: Comparar reconstrucción actual vs reconstrucción oferta
        # Calculamos el ahorro ESTRUCTURAL (Sin impuestos ni alquileres)
        subtotal_actual = subtotal_si_actual if baseline_method != "fallback_current_total" else (current_total / 1.25) # estimacion si falla
        ahorro_estructural = subtotal_actual - subtotal_sin_impuestos_oferta
        
        # Ahorro con impuestos (para el total de la factura)
        if baseline_method == "fallback_current_total":
            ahorro_periodo = current_total - estimated_total_periodo
        else:
            ahorro_periodo = total_actual_reconstruido - estimated_total_periodo
        
        # ⭐ CÁLCULOS NORMALIZADOS (Regla P0: Normalización a 30 días)
        # total_30 = total_periodo * (30 / dias)
        # ahorro_anual = (total_30_actual - total_30_oferta) * 12
        factor_normalizacion = 30.0 / float(periodo_dias)
        
        # Cifra reina: Ahorro anual normalizado (360 días)
        ahorro_anual_norm = ahorro_periodo * factor_normalizacion * 12.0
        ahorro_mensual_norm = ahorro_periodo * factor_normalizacion
        
        # Flag de comparabilidad estructural
        # Se considera comparable si existen coste_energia_actual y coste_potencia_actual
        b_e = getattr(factura, 'coste_energia_actual', None)
        b_p = getattr(factura, 'coste_potencia_actual', None)
        is_structural_comparable = (b_e is not None and b_p is not None)

        # El porcentaje de ahorro se calcula sobre el total de referencia
        total_referencia = total_actual_reconstruido if baseline_method != "fallback_current_total" else current_total
        saving_percent = (ahorro_periodo / total_referencia * 100) if total_referencia > 0 else 0.0

        # PRECIO MEDIO ESTRUCTURAL (E+P / kWh)
        total_kwh = sum(consumos)
        precio_medio_estructural = (subtotal_sin_impuestos_oferta / total_kwh) if total_kwh > 0 else 0.0

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

        # ⭐ DEBUG: Logs especiales para factura 287
        if factura.id == 287:
            logger.warning(f"[DEBUG-287] Oferta {provider}/{plan_name}: periodo={periodo_dias}d, consumos={consumos}, potencias={potencias}")
            logger.warning(f"[DEBUG-287] coste_energia={coste_energia:.4f}, coste_potencia={coste_potencia:.4f}, total_est={estimated_total_periodo:.2f}")
        
        offer = {
            "tarifa_id": tarifa_id,
            "provider": provider,
            "plan_name": plan_name,
            "estimated_total": round(estimated_total_periodo, 2),
            "estimated_total_periodo": round(estimated_total_periodo, 2), # Requerido para sorting
            "saving_amount": round(ahorro_periodo, 2),  # ahorro en el periodo factura
            "ahorro_periodo": round(ahorro_periodo, 2), # Requerido para tags
            "saving_amount_annual": round(ahorro_anual_norm, 2), # CIFRA REINA
            "saving_amount_monthly": round(ahorro_mensual_norm, 2),
            "is_structural_comparable": is_structural_comparable,
            "saving_percent": round(saving_percent, 2),
            "commission": 0,
            "tag": "balanced",
            "breakdown": {
                "periodo_dias": int(periodo_dias),
                "consumo_p1": round(consumos[0], 2),
                "consumo_p2": round(consumos[1], 2),
                "consumo_p3": round(consumos[2], 2),
                "consumo_p4": round(consumos[3], 2) if len(consumos) > 3 else 0,
                "consumo_p5": round(consumos[4], 2) if len(consumos) > 4 else 0,
                "consumo_p6": round(consumos[5], 2) if len(consumos) > 5 else 0,
                "potencia_p1": round(potencias[0], 4),
                "potencia_p2": round(potencias[1], 4),
                "coste_energia": round(coste_energia, 2),
                "coste_potencia": round(coste_potencia, 2),
                "impuestos": round(impuestos_oferta, 2),
                "alquiler_contador": round(alquiler_equipo, 2),
                "modo_energia": modo_energia,
                "modo_potencia": modo_potencia,
                "is_structural_comparable": is_structural_comparable,
                "precio_medio_estructural": round(precio_medio_estructural, 4) if is_structural_comparable else None,
                "ahorro_estructural": round(ahorro_estructural, 2) if is_structural_comparable else None,
            },
        }

        offers.append(offer)

    completas = [item for item in offers if item["breakdown"]["modo_potencia"] == "tarifa"]
    parciales = [item for item in offers if item["breakdown"]["modo_potencia"] != "tarifa"]

    # Ordenar por precio total estimado
    completas.sort(key=lambda item: item["estimated_total"])
    parciales.sort(key=lambda item: item["estimated_total"])

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
            # ⭐ FIX: Rollback de la transacción fallida ANTES de intentar actualizar
            db.rollback()
            # Crear nueva transacción limpia para guardar el estado de error
            try:
                comp = db.query(Comparativa).filter(Comparativa.id == comparativa_id).first()
                if comp:
                    comp.status = "error"
                    comp.error_json = json.dumps({"error": "No offers inserted"})
                    db.commit()
                    logger.info(f"[OFERTAS] Error status saved for comparativa_id={comparativa_id}")
            except Exception as update_error:
                logger.warning(f"[OFERTAS] Could not update comparativa status: {update_error}")
                db.rollback()
            
            # 🔧 AJUSTE P0: Devolver 200 OK con ok:false (no 422)
            # El frontend todavía no maneja 422, así que usamos response estructurado
            return {
                "ok": False,
                "error_code": "ZERO_OFFERS",
                "message": "No se pudieron generar ofertas. Posible problema con comisiones o tarifas.",
                "factura_id": factura.id,
                "comparativa_id": comparativa_id,
            }
        else:
            # 3. COMMIT ÚNICO para ambas operaciones (solo si hubo inserción exitosa)
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

    # DETERMINAR EL "BASELINE" REAL PARA LA UI
    # Si hemos reconstruido la factura (IVA 21%), ese debe ser el baseline visual
    # para que la resta (Baseline - Oferta) coincida con lo que el usuario ve.
    ui_current_total = total_actual_reconstruido if baseline_method == "backsolve_subtotal_si" else current_total

    return {
        "factura_id": factura.id,
        "comparativa_id": comparativa_id,
        "periodo_dias": periodo_dias,
        "current_total": round(ui_current_total, 2),  # ← Baseline alineado para la UI
        "total_actual_reconstruido": round(total_actual_reconstruido, 2) if baseline_method != "fallback_current_total" else None,
        "subtotal_si_actual": round(subtotal_si_actual, 2) if baseline_method != "fallback_current_total" else None,
        "coste_energia_actual": getattr(factura, 'coste_energia_actual', None),
        "coste_potencia_actual": getattr(factura, 'coste_potencia_actual', None),
        "baseline_method": baseline_method,
        "metodo_calculo": "PO/NodoAmbar" if baseline_method == "backsolve_subtotal_si" else "Fallback",
        "diff_vs_current_total": round(abs(total_actual_reconstruido - current_total), 2) if baseline_method != "fallback_current_total" else 0.0,
        "offers": offers,
    }
