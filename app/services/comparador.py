"""
Tariff comparison service for 2.0TD (MVP).
"""

from datetime import date, datetime
import re
from typing import Dict, Any, Optional

from sqlalchemy import text


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


def compare_factura(factura, db) -> Dict[str, Any]:
    current_total = _to_float(getattr(factura, "total_factura", None))
    if current_total is None or current_total <= 0:
        raise ValueError("La factura no tiene un total valido para comparar")

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
        raise ValueError(
            "La factura no tiene datos suficientes para comparar: "
            + ", ".join(missing)
        )

    dias = _get_days(factura)

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

        potencia_p1_price = _to_float(tarifa.get("potencia_p1_eur_kw_dia"))
        potencia_p2_price = _to_float(tarifa.get("potencia_p2_eur_kw_dia"))
        if potencia_p1_price is None or potencia_p2_price is None:
            coste_potencia = 0.0
            modo_potencia = "sin_potencia"
        else:
            coste_potencia = dias * (
                (potencia_p1 * potencia_p1_price)
                + (potencia_p2 * potencia_p2_price)
            )
            modo_potencia = "tarifa"

        estimated_total = coste_energia + coste_potencia
        saving_amount = current_total - estimated_total
        saving_percent = (
            (saving_amount / current_total) * 100 if current_total > 0 else 0.0
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
            "estimated_total": round(estimated_total, 2),
            "saving_amount": round(saving_amount, 2),
            "saving_percent": round(saving_percent, 2),
            "tag": "balanced",
            "breakdown": {
                "dias": int(dias),
                "coste_energia": round(coste_energia, 2),
                "coste_potencia": round(coste_potencia, 2),
                "modo_energia": modo_energia,
                "modo_potencia": modo_potencia,
            },
        }

        offers.append(offer)

    completas = [item for item in offers if item["breakdown"]["modo_potencia"] == "tarifa"]
    parciales = [item for item in offers if item["breakdown"]["modo_potencia"] != "tarifa"]

    completas.sort(key=lambda item: item["estimated_total"])
    parciales.sort(key=lambda item: item["estimated_total"])

    for item in parciales:
        item["tag"] = "partial"

    if completas:
        max_saving = max(item["saving_amount"] for item in completas)
        for item in completas:
            if item["saving_amount"] == max_saving:
                item["tag"] = "best_saving"
            else:
                item["tag"] = "balanced"

    offers = completas + parciales

    # TODO: Persist comparativas/ofertas_calculadas once models are wired.

    return {
        "factura_id": factura.id,
        "current_total": round(current_total, 2),
        "offers": offers,
    }
