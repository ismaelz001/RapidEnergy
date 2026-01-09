from app.services.ocr import (
    extract_atr,
    extract_potencias,
    parse_es_number,
    parse_invoice_text,
)


def test_parse_es_number():
    assert parse_es_number("4,6") == 4.6
    assert parse_es_number("1.234,56") == 1234.56
    assert parse_es_number("1 234,56 EUR") == 1234.56


def test_extract_atr_variants():
    text = "Peaje acceso 2,0 td con otra referencia 2.OTD"
    assert extract_atr(text) == "2.0TD"


def test_extract_potencias_punta_valle():
    text = "Potencia contratada en punta: 4,6 kW\nPotencia contratada en valle: 4,6 kW"
    potencias = extract_potencias(text)
    assert potencias["p1"] == 4.6
    assert potencias["p2"] == 4.6


def test_parse_invoice_text_atr_potencias():
    raw_text = (
        "Peaje acceso 2.0TD\n"
        "Potencia contratada en punta: 4,6 kW\n"
        "Potencia contratada en valle: 4,6 kW\n"
        "Consumo en P1: 10 kWh\n"
        "Consumo en P2: 12 kWh\n"
        "Consumo en P3: 5 kWh\n"
        "Total factura: 26,87 EUR\n"
    )
    parsed = parse_invoice_text(raw_text)
    assert parsed["atr"] == "2.0TD"
    assert parsed["potencia_p1_kw"] == 4.6
    assert parsed["potencia_p2_kw"] == 4.6


def test_total_factura_fallback_importe_factura():
    raw_text = "IMPORTE FACTURA: 26,87 EUR"
    parsed = parse_invoice_text(raw_text)

def test_regression_naturgy_pvpc_truncated():
    # Use realistic text including specific keywords for extraction source validation
    raw_text = (
        "2.0TD\n"
        "OTRAS COSAS...\n"
        "ncia contratada en punta: 4,6 kW\n"
        "Potencia contratada en valle: 4,6 kW\n"
        "Consumo en P1: 17 kWh\n"
        "P2: 18\n"
        "P3: 32\n"
        "IMPORTE FACTURA: 26,87 €"
    )
    parsed = parse_invoice_text(raw_text)
    assert parsed["atr"] == "2.0TD"
    assert parsed["potencia_p1_kw"] == 4.6
    assert parsed["potencia_p2_kw"] == 4.6
    # Fallback to structured detection (IMPORTE FACTURA)
    assert parsed["total_factura"] == 26.87
