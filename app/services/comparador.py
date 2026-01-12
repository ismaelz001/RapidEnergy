"""
Tariff comparison service for 2.0TD (MVP).
"""

from datetime import date, datetime
import json
import logging
import re
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
    start = _parse_date(getattr(factura, "fecha_inicio", None))
    end = _parse_date(getattr(factura, "fecha_fin", None))
    if start and end:
        delta = (end - start).days
        if delta > 0:
            return delta
    return 30


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


def _insert_ofertas(db, factura_id: int, comparativa_id: Optional[int], offers) -> bool:
    columns_info = _get_table_columns(db, "ofertas_calculadas")
    if not columns_info:
        return False

    required_columns = _missing_required_columns(columns_info, [])
    dialect_name = db.get_bind().dialect.name
    inserted = False
    warned = False

    for offer in offers:
        payload: Dict[str, Any] = {}

        if "comparativa_id" in columns_info and comparativa_id is not None:
            payload["comparativa_id"] = comparativa_id
        if "factura_id" in columns_info:
            payload["factura_id"] = factura_id
        if "tarifa_id" in columns_info and offer.get("tarifa_id") is not None:
            payload["tarifa_id"] = offer.get("tarifa_id")
        if "total_estimado" in columns_info:
            payload["total_estimado"] = offer.get("estimated_total")
        if "ahorro" in columns_info:
            payload["ahorro"] = offer.get("saving_amount")
        if "detalle_json" in columns_info:
            payload["detalle_json"] = json.dumps(offer.get("breakdown", {}))

        missing = [col for col in required_columns if col not in payload]
        if missing:
            if not warned:
                logger.warning(
                    "Ofertas insert skipped, missing required columns: %s",
                    ", ".join(missing),
                )
                warned = True
            continue

        sql = _build_insert_sql(
            "ofertas_calculadas", payload, columns_info, dialect_name
        )
        db.execute(text(sql), payload)
        inserted = True

    return inserted


def _persist_results(db, factura_id: int, offers) -> None:
    try:
        comparativa_id = _insert_comparativa(db, factura_id)
        inserted = _insert_ofertas(db, factura_id, comparativa_id, offers)
        if comparativa_id is not None or inserted:
            db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Comparator persistence failed: %s", exc)

def compare_factura(factura, db) -> Dict[str, Any]:
    """
    P1 PRODUCCIÓN: Compara ofertas usando el periodo REAL de la factura.
    NO usa fallback a 30 días. Lanza DomainError si falta periodo.
    """
    current_total = _to_float(getattr(factura, "total_factura", None))
    if current_total is None or current_total <= 0:
        raise DomainError("TOTAL_INVALID", "La factura no tiene un total válido para comparar")

    required_fields = [
        "consumo_p1_kwh",
        "consumo_p2_kwh",
        "consumo_p3_kwh",
        "potencia_p1_kw",
        "potencia_p2_kw",
    ]
    missing = [
        field
        for field in required_fields
        if _to_float(getattr(factura, field, None)) is None
    ]
    if missing:
        raise DomainError(
            "FIELDS_MISSING",
            "La factura no tiene datos suficientes para comparar: " + ", ".join(missing)
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

    consumo_p1 = _to_float(factura.consumo_p1_kwh) or 0.0
    consumo_p2 = _to_float(factura.consumo_p2_kwh) or 0.0
    consumo_p3 = _to_float(factura.consumo_p3_kwh) or 0.0
    potencia_p1 = _to_float(factura.potencia_p1_kw) or 0.0
    potencia_p2 = _to_float(factura.potencia_p2_kw) or 0.0

    result = db.execute(
        text("SELECT * FROM tarifas WHERE atr = :atr"),
        {"atr": "2.0TD"},
    )
    try:
        tarifas = result.mappings().all()
    except AttributeError:
        tarifas = [row._mapping for row in result.fetchall()]

    offers = []
    for tarifa in tarifas:
        modo_energia, prices = _resolve_energy_prices(tarifa)
        if modo_energia is None:
            continue

        p1_price, p2_price, p3_price = prices
        coste_energia = (
            (consumo_p1 * p1_price)
            + (consumo_p2 * p2_price)
            + (consumo_p3 * p3_price)
        )

        # P1: INDENTACIÓN CORRECTA
        potencia_p1_price = _to_float(tarifa.get("potencia_p1_eur_kw_dia"))
        potencia_p2_price = _to_float(tarifa.get("potencia_p2_eur_kw_dia"))
        
        if potencia_p1_price is None or potencia_p2_price is None:
            coste_potencia = 0.0
            modo_potencia = "sin_potencia"
        else:
            # P1: USA PERIODO REAL (SIN FALLBACK)
            coste_potencia = periodo_dias * (
                (potencia_p1 * potencia_p1_price)
                + (potencia_p2 * potencia_p2_price)
            )
            modo_potencia = "tarifa"

        estimated_total_periodo = coste_energia + coste_potencia
        ahorro_periodo = current_total - estimated_total_periodo
        
        # P1: EQUIVALENTES CONSISTENTES
        ahorro_mensual_equiv = ahorro_periodo * (30.437 / periodo_dias)
        ahorro_anual_equiv = ahorro_periodo * (365 / periodo_dias)
        
        saving_percent = (
            (ahorro_periodo / current_total) * 100 if current_total > 0 else 0.0
        )

        tarifa_id = tarifa.get("id") or tarifa.get("tarifa_id")
        provider = _pick_value(
            tarifa,
            [
                "comercializadora",
                "provider",
                "empresa",
                "compania",
                "nombre_comercializadora",
                "nombre_comercializador",
                "brand",
            ],
            "Proveedor desconocido",
        )
        plan_name = _pick_value(
            tarifa,
            ["nombre", "plan_name", "plan", "tarifa", "nombre_tarifa", "nombre_plan"],
            "Tarifa 2.0TD",
        )

        offer = {
            "tarifa_id": tarifa_id,
            "provider": provider,
            "plan_name": plan_name,
            "estimated_total_periodo": round(estimated_total_periodo, 2),
            "ahorro_periodo": round(ahorro_periodo, 2),
            "ahorro_mensual_equiv": round(ahorro_mensual_equiv, 2),
            "ahorro_anual_equiv": round(ahorro_anual_equiv, 2),
            "saving_percent": round(saving_percent, 2),
            "tag": "balanced",
            "breakdown": {
                "periodo_dias": int(periodo_dias),
                "coste_energia": round(coste_energia, 2),
                "coste_potencia": round(coste_potencia, 2),
                "modo_energia": modo_energia,
                "modo_potencia": modo_potencia,
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

    # P1: PERSISTIR COMPARATIVA (AUDITORÍA)
    comparativa_id = None
    try:
        inputs_snapshot = {
            "cups": factura.cups,
            "atr": factura.atr,
            "potencia_p1": factura.potencia_p1_kw,
            "potencia_p2": factura.potencia_p2_kw,
            "consumo_p1": factura.consumo_p1_kwh,
            "consumo_p2": factura.consumo_p2_kwh,
            "consumo_p3": factura.consumo_p3_kwh,
        }
        
        comparativa = Comparativa(
            factura_id=factura.id,
            periodo_dias=periodo_dias,
            current_total=current_total,
            inputs_json=json.dumps(inputs_snapshot),
            offers_json=json.dumps(offers),
            status="ok"
        )
        db.add(comparativa)
        db.commit()
        db.refresh(comparativa)
        comparativa_id = comparativa.id
    except Exception as e:
        logger.error(f"Error persistiendo comparativa: {e}")
        # No fallar si falla la auditoría, pero loggear

    _persist_results(db, factura.id, offers)

    return {
        "factura_id": factura.id,
        "comparativa_id": comparativa_id,
        "periodo_dias": periodo_dias,
        "current_total": round(current_total, 2),
        "offers": offers,
    }
