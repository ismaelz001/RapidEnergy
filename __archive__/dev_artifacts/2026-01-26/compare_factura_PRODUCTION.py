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
