import os
import json
import re
import io
import unicodedata
from google.oauth2 import service_account
from google.cloud import vision
import pypdf
import google.generativeai as genai
import logging
import traceback


def _shield_concepts(result: dict):
    """
    🛡️ Concept Shield: Protege contra la mezcla de conceptos (Potencia <-> Consumo).
    Si el consumo es idéntico a la potencia contratada (valor típico de kW como 3.3, 4.6), 
    es casi seguro un error de extracción.
    """
    import logging
    p1 = result.get("potencia_p1_kw")
    p2 = result.get("potencia_p2_kw")
    tot_c = result.get("consumo_kwh")
    
    # Valores de potencia contratada extremadamente comunes en España
    typical_powers = [2.3, 3.3, 3.45, 4.6, 5.5, 5.75, 6.9, 8.05, 9.2, 10.35, 11.5, 13.8, 14.49]
    
    for i in range(1, 7):
        c_alt = result.get(f"consumo_p{i}_kwh")
        if c_alt is None: continue
        
        # Si el consumo de un periodo es idéntico a P1 o P2 (que son constantes)
        is_collision = (p1 and abs(c_alt - p1) < 0.001) or (p2 and abs(c_alt - p2) < 0.001)
        
        if is_collision:
            # Si el consumo es muy bajo (< 15) O es un valor típico de potencia...
            is_suspicious = (c_alt < 15) or any(abs(c_alt - tp) < 0.01 for tp in typical_powers)
            
            # EXCEPCIÓN: Si el consumo total de la factura confirma que este valor es real (ej: total = sum(p1..p3))
            # No lo borramos. Pero si tot_c es 0 o null, desconfiamos.
            if tot_c and tot_c > 0 and abs(tot_c - c_alt) < 0.1:
                 # Si solo hay un periodo y coincide con el total, podría ser real
                 pass
            else:
                if is_suspicious:
                    logging.warning(f"🛡️ [ConceptShield] Colisión C{i}=Potencia ({c_alt}). Anulando C{i} por sospecha de mala extracción.")
                    result[f"consumo_p{i}_kwh"] = None
                    if "detected_por_ocr" in result: 
                        result["detected_por_ocr"][f"consumo_p{i}_kwh"] = False

    # Regla 3: Blindaje de Impuesto Eléctrico (No capturar el porcentaje 5.11)
    ie = result.get("impuesto_electrico")
    if ie and (abs(ie - 5.11) < 0.1 or abs(ie - 1.0511) < 0.01 or abs(ie - 0.0511) < 0.01):
        logging.warning(f"🛡️ [ConceptShield] El impuesto_electrico ({ie}) parece ser el tipo impositivo, no el importe. Limpiando.")
        result["impuesto_electrico"] = None

    return result


def normalize_text(raw: str) -> str:
    if raw is None:
        return ""
    text = unicodedata.normalize("NFKC", raw)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _parse_date_flexible(date_str):
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.lower().strip()
    
    # 1. DD/MM/YY, DD.MM.YYYY o DD-MM-YYYY
    match = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", date_str)
    if match:
        from datetime import date
        try:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if year < 100: year += 2000
            return date(year, month, day)
        except:
            return None
            
    # 2. DD de Mes de YYYY
    meses_map = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    meses_regex = "|".join(meses_map.keys())
    match = re.search(rf"(\d{{1,2}})\s+de\s+({meses_regex})\s+de\s+(\d{{2,4}})", date_str)
    if match:
        from datetime import date
        try:
            day, month_name, year = int(match.group(1)), match.group(2), int(match.group(3))
            if year < 100: year += 2000
            return date(year, meses_map[month_name], day)
        except:
            return None
    return None


def parse_es_number(value: str):
    if value is None:
        return None
    text = normalize_text(str(value))
    if not text:
        return None
    cleaned = re.sub(r"[^\d,.\-]", "", text)
    if cleaned in ("", "-", ".", ","):
        return None

    try:
        # SI el número tiene un punto pero NO coma, y tiene exactamente 3 dígitos tras el punto, 
        # es PROBABLEMENTE un separador de miles en España (ej: 15.974 para lecturas).
        # PERO si el número es pequeño (ej: 1.52 kWh), el punto es decimal.
        # Heurística: si el valor tras el punto tiene 3 dígitos y el total > 100, es miles.
        
        last_dot = cleaned.rfind(".")
        last_comma = cleaned.rfind(",")
        
        if last_dot != -1 and last_comma == -1:
            # Caso: 15.974 o 1.52
            parts = cleaned.split(".")
            if len(parts[-1]) == 3 and len(parts[0]) >= 1:
                val_temp = cleaned.replace(".", "")
                if float(val_temp) > 100: # Heurística de escala para España
                     cleaned = val_temp
        
        # Lógica estándar para el resto
        last_dot = cleaned.rfind(".")
        last_comma = cleaned.rfind(",")
        if last_dot != -1 and last_comma != -1:
            if last_comma > last_dot:
                cleaned = cleaned.replace(".", "")
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif last_comma != -1:
            cleaned = cleaned.replace(",", ".")
        else:
            # Solo queda el dot si existía, lo tratamos como decimal por defecto 
            # (a menos que lo hayamos limpiado arriba en la heurística)
            pass

        return float(cleaned)
    except Exception:
        return None


def extract_atr(text: str):
    if not text:
        return None
    normalized = normalize_text(text).upper()
    # Broaden the search
    if re.search(r"2\s*[.,]?\s*[0O]\s*TD", normalized) or "USO LUZ" in normalized:
        return "2.0TD"
    # Fallback: ATR phrase - allow up to 60 chars of any type including newline
    match = re.search(r"PEAJE[\s\S]{0,60}?([23]\.?[0O]\s*TD)", normalized, re.IGNORECASE)
    if match:
        return match.group(1).replace(" ", "").upper()
    return None


def _extract_potencias_with_sources(text: str):
    if not text:
        return {"p1": None, "p2": None, "p1_source": None, "p2_source": None, "warnings": []}
    normalized = normalize_text(text)

    p1_patterns = [
        ("table", r"P1\s+P2\s+P3\s+P4\s+P5\s+P6\s+([\d.,]+)\s+([\d.,]+)"),
        ("punta", r"potencia\s+(?:contratada\s+)?(?:en\s+)?punta[^0-9]{0,20}([\d.,]+)"),
        ("p1", r"potencia\s+(?:contratada\s+)?(?:en\s+)?p1[^0-9]{0,20}([\d.,]+)"),
        ("contratada", r"potencia\s+contratada[^0-9]{0,30}\s+([\d.,]+)\s*kw"),
        ("punta", r"(?:potencia|ncia)\s+(?:contratada\s+)?(?:en\s+)?punta[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)?"),
        ("punta", r"contratada\s+(?:en\s+)?punta[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)?"),
        # Standalone
        ("punta", r"\bpunta\b[^0-9]{0,20}([\d.,]+)\s*k?w"),
        # Table labels
        ("grid", r"potencia\s*\(kw\)[^0-9]{0,20}([\d.,]+)"),
    ]
    p2_patterns = [
        ("valle", r"potencia\s+(?:contratada\s+)?(?:en\s+)?valle[^0-9]{0,20}([\d.,]+)"),
        ("p2", r"potencia\s+(?:contratada\s+)?(?:en\s+)?p2[^0-9]{0,20}([\d.,]+)"),
        ("valle", r"(?:potencia|ncia)\s+(?:contratada\s+)?(?:en\s+)?valle[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)?"),
        ("valle", r"contratada\s+(?:en\s+)?valle[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)?"),
        # Standalone
        ("valle", r"\bvalle\b[^0-9]{0,20}([\d.,]+)\s*k?w"),
    ]

    def _match(patterns):
        for source, pat in patterns:
            match = re.search(pat, normalized, re.IGNORECASE)
            if match:
                return parse_es_number(match.group(1)), source
        return None, None

    p1_value, p1_source = _match(p1_patterns)
    p2_value, p2_source = _match(p2_patterns)
    warnings = []

    generic_match = re.search(
        r"potencia\s+contratada[^0-9]{0,20}([\d.,]+)\s*k?w", normalized, re.IGNORECASE
    )
    if generic_match and p1_value is None and p2_value is None:
        warnings.append("Potencia detectada sin contexto punta/valle")

    return {
        "p1": p1_value,
        "p2": p2_value,
        "p1_source": p1_source,
        "p2_source": p2_source,
        "warnings": warnings,
    }


def extract_potencias(text: str):
    data = _extract_potencias_with_sources(text)
    return {"p1": data["p1"], "p2": data["p2"]}


def build_raw_data_payload(raw_text: str, extraction_summary: dict = None, missing_fields=None) -> str:
    payload = {"raw_text": raw_text}
    if extraction_summary is not None:
        payload["extraction_summary"] = extraction_summary
    if missing_fields is not None:
        payload["missing_fields"] = missing_fields
    return json.dumps(payload, ensure_ascii=False)


def merge_raw_data_audit(raw_data: str, missing_fields=None, extraction_summary: dict = None) -> str:
    if raw_data:
        try:
            payload = json.loads(raw_data)
        except Exception:
            payload = {"raw_text": raw_data}
    else:
        payload = {}

    if extraction_summary is not None:
        payload["extraction_summary"] = extraction_summary
    if missing_fields is not None:
        payload["missing_fields"] = missing_fields
    return json.dumps(payload, ensure_ascii=False)


def _empty_result(raw_text: str = None) -> dict:
    return {
        "cups": None,
        "consumo_kwh": None,
        "importe": None,
        "fecha": None,
        "fecha_inicio_consumo": None,
        "fecha_fin_consumo": None,
        "dias_facturados": None,  # Added field in result dict (even if not in DB, useful for raw_data)
        "titular": None,
        "dni": None,
        "direccion": None,
        "telefono": None,
        "atr": None,
        "potencia_p1_kw": None,
        "potencia_p2_kw": None,
        "consumo_p1_kwh": None,
        "consumo_p2_kwh": None,
        "consumo_p3_kwh": None,
        "consumo_p4_kwh": None,
        "consumo_p5_kwh": None,
        "consumo_p6_kwh": None,
        "bono_social": None,
        "servicios_vinculados": None,
        "alquiler_contador": None,
        "impuesto_electrico": None,
        "iva": None,
        "total_factura": None,
        "parsed_fields": {},
        "detected_por_ocr": {},
        "extraction_summary": {},
        "missing_fields": [],
        "raw_text": raw_text,
    }


def get_vision_client():
    logs = ["DEBUG AUTH LOG:"]

    secret_dir = "/etc/secrets"
    if os.path.exists(secret_dir):
        logs.append(f"Secrets dir found: {secret_dir}")
        try:
            files = os.listdir(secret_dir)
            logs.append(f"Files in secrets: {files}")
            for fname in files:
                fpath = os.path.join(secret_dir, fname)
                if os.path.isdir(fpath):
                    continue
                try:
                    creds = service_account.Credentials.from_service_account_file(fpath)
                    logs.append(f"Success loading {fname}. Email: {creds.service_account_email}")
                    return vision.ImageAnnotatorClient(credentials=creds), "\n".join(logs)
                except Exception as e:
                    logs.append(f"Failed loading {fname}: {str(e)}")
        except Exception as e:
            logs.append(f"Error scanning secrets dir: {str(e)}")
    else:
        logs.append("Secrets dir /etc/secrets not found (local?)")

    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        logs.append("Found GOOGLE_CREDENTIALS env var.")
        try:
            info = json.loads(creds_json)
            if "private_key" in info:
                info["private_key"] = info["private_key"].replace("\\n", "\n")

            creds = service_account.Credentials.from_service_account_info(info)
            logs.append(f"Loaded from ENV. Email: {info.get('client_email')}")
            return vision.ImageAnnotatorClient(credentials=creds), "\n".join(logs)
        except Exception as e:
            logs.append(f"Error parsing ENV credentials: {str(e)}")
            return None, "\n".join(logs)

    logs.append("No credentials found in File or Env.")
    return None, "\n".join(logs)


from app.utils.cups import normalize_cups, is_valid_cups

def parse_invoice_text(full_text: str, is_image: bool = False) -> dict:
    full_text = normalize_text(full_text)
    result = _empty_result(full_text)
    parsed_fields = {}
    extraction_summary = {
        "atr_source": None,
        "potencia_p1_source": None,
        "potencia_p2_source": None,
        "parse_warnings": [],
    }

    def parse_structured_fields(raw_text: str) -> dict:
        data = {
            "fecha_inicio_consumo": None,
            "fecha_fin_consumo": None,
            "dias_facturados": None,
            "importe_factura": None,
            "cups": None,
            "atr": None,
            "potencia_p1_kw": None,
            "potencia_p2_kw": None,
            "consumo_p1_kwh": None,
            "consumo_p2_kwh": None,
            "consumo_p3_kwh": None,
            "consumo_p4_kwh": None,
            "consumo_p5_kwh": None,
            "consumo_p6_kwh": None,
            "bono_social": None,
            "parsed_fields": {},
        }
        detected_pf = {}

        # 1. CUPS EXTRACTION - AGRESIVE FALLBACK (Ignoring MOD529 validation for now)
        valid_cups_found = None
        
        # Find ANY ES sequence and clean it aggressively
        # Most PDFs have CUPS as "ES XXXX XXXX XXXX XXXX XX" with spaces
        es_candidates = re.findall(r"ES[\s\-]*[\w\s\-]{15,50}", raw_text, re.IGNORECASE)
        
        for candidate in es_candidates:
            print(f"🔍 CUPS RAW CANDIDATE: {candidate}")
            
            # Aggressive cleaning: remove ALL non-alphanumeric except ES
            cleaned = re.sub(r'[\s\-]', '', candidate.upper())
            # Keep only first 22 chars (ES + 20 alphanumeric)
            cleaned = cleaned[:22] if len(cleaned) > 22 else cleaned
            
            print(f"🧹 CLEANED: {cleaned}")
            
            # Must start with ES and have at least 20 chars total
            if not cleaned.startswith("ES") or len(cleaned) < 20:
                print(f"❌ Too short or invalid format: {len(cleaned)} chars")
                continue
            
            # Try to validate with MOD529
            is_valid = is_valid_cups(cleaned)
            print(f"🔢 MOD529 Result: {is_valid}")
            
            if is_valid:
                valid_cups_found = cleaned
                print(f"✅ VALID CUPS FOUND: {cleaned}")
                break
            else:
                # Even if MOD529 fails, accept it if it looks like CUPS (ES + 20 alphanumeric)
                if len(cleaned) == 22 and cleaned.startswith("ES"):
                    print(f"⚠️ [WARNING] MOD529 failed but accepting as CUPS: {cleaned}")
                    valid_cups_found = cleaned
                    break
        
        data["cups"] = valid_cups_found
        print(f"🏁 FINAL CUPS VALUE: {valid_cups_found}")
        
        detected_pf["cups"] = data["cups"] is not None

        # 2. Fechas range (Multiple formats)
        # Format 1: 31 de agosto de 2025 a 30 de septiembre...
        meses = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
        rango_text = re.search(
            rf"(\d{{1,2}}[\s\w]{{1,8}}(?:{meses})[\s\w]{{1,8}}\d{{4}})[\s\S]{{0,100}}?\b(?:a|al|hasta)\b[\s\S]{{0,100}}?(\d{{1,2}}[\s\w]{{1,8}}(?:{meses})[\s\w]{{1,8}}\d{{4}})",
            raw_text,
            re.IGNORECASE,
        )
        if rango_text:
            data["fecha_inicio_consumo"] = rango_text.group(1)
            data["fecha_fin_consumo"] = rango_text.group(2)

        # Format 2: dd/mm/yyyy - dd/mm/yyyy or similar
        if not data["fecha_inicio_consumo"]:
            rango_fechas = re.search(
                r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})[\s\S]{0,50}?(?:-|al|a|hasta)[\s\S]{0,50}?(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})", 
                raw_text, 
                re.IGNORECASE
            )
            if rango_fechas:
                data["fecha_inicio_consumo"] = rango_fechas.group(1)
                data["fecha_fin_consumo"] = rango_fechas.group(2)
        
        detected_pf["fecha_inicio_consumo"] = data["fecha_inicio_consumo"] is not None
        detected_pf["fecha_fin_consumo"] = data["fecha_fin_consumo"] is not None

        # 2b. Dias Facturados (Improved - Multiple strategies)
        dias_facturados = None
        
        # Strategy 1: Look for explicit "días" keyword
        for ln in raw_text.splitlines():
            linea = normalize_text(ln)
            if not linea: 
                continue
            low = linea.lower()
            
            # Pattern: "30 dias" or "días: 30" 
            m = re.search(r"(?:d[íi]as[\s:]*(\d+)|(\d+)\s*d[íi]as)", low)
            if m:
                val = m.group(1) or m.group(2)
                try:
                    val_int = int(val)
                    # Sanity range for days (1-120)
                    if 1 <= val_int <= 120:
                        dias_facturados = val_int
                        break
                except:
                    continue
        
        # Strategy 2: Look for "Período" o "periodo" followed by dates or days
        if dias_facturados is None:
            periodo_match = re.search(
                r"(?i)per[íi]odo[\s\S]{0,100}?(\d{1,2})\s+(?:d[íi]as|days)",
                raw_text
            )
            if periodo_match:
                try:
                    val = int(periodo_match.group(1))
                    if 1 <= val <= 120:
                        dias_facturados = val
                except:
                    pass
        
        # Strategy 3: Calculate from date range if available
        if dias_facturados is None:
            # Look for "del XX de XXX al YY de YYY"
            date_range = re.search(
                r"del\s+(\d{1,2})\s+de\s+\w+\s+al\s+(\d{1,2})\s+de\s+(\w+)",
                raw_text,
                re.IGNORECASE
            )
            if date_range:
                try:
                    start_day = int(date_range.group(1))
                    end_day = int(date_range.group(2))
                    # Simple approximation: if different months, assume month boundaries
                    if end_day >= start_day:
                        dias_facturados = end_day - start_day + 1
                    else:
                        # Different months, estimate ~30 days per month
                        dias_facturados = (30 - start_day) + end_day + 1
                except:
                    pass

        if dias_facturados:
            try:
                data["dias_facturados"] = int(dias_facturados)
            except:
                pass
        
        # 3. Importe Factura (High Priority)
        # Look for explicit "TOTAL FACTURA" or "TOTAL A PAGAR" to avoid "Base Imponible"
        # BUG C FIX: TOTAL A PAGAR tiene máxima prioridad
        total_pagar_match = re.search(
            r"TOTAL[\s\S]{0,50}?A[\s\S]{0,50}?PAGAR[\s\S]{0,50}?([\d.,]+)\s*(?:€|EUR)", 
            raw_text, 
            re.IGNORECASE
        )
        if total_pagar_match:
            data["importe_factura"] = parse_es_number(total_pagar_match.group(1))
            detected_pf["importe_factura"] = True
        else:
            # Luego TOTAL IMPORTE FACTURA o TOTAL FACTURA
            high_prio_match = re.search(
                r"(?:TOTAL\s+IMPORTE\s+FACTURA|TOTAL\s+FACTURA)[^0-9\n]{0,20}([\d.,]+)\s*(?:€|EUR)", 
                raw_text, 
                re.IGNORECASE
            )
            if high_prio_match:
                data["importe_factura"] = parse_es_number(high_prio_match.group(1))
                detected_pf["importe_factura"] =True
            else:
                # Fallback to "IMPORTE FACTURA"
                importe_match = re.search(r"IMPORTE\s+FACTURA[:\s]*[\r\n\s]*([\d.,]+)", raw_text, re.IGNORECASE)
                if importe_match:
                    data["importe_factura"] = parse_es_number(importe_match.group(1))
                    detected_pf["importe_factura"] = data["importe_factura"] is not None
                else:
                    detected_pf["importe_factura"] = False

        data["atr"] = extract_atr(raw_text)
        detected_pf["atr"] = data["atr"] is not None

        # 5. Consumption (Expanded mapping)
        # P1 = Punta, P2 = Llano, P3 = Valle (Generic approach)

        filtered_keywords = ["lectura", "contador", "acumulada", "actual", "anterior", "potencia", "último año", "año anterior", "media"]
        consumo_lines = []
        for ln in raw_text.splitlines():
            clean = ln.strip()
            if not clean:
                continue
            lower = clean.lower()
            # [PATCH] Allow lines with "consumo" OR specific period keywords
            if "consumo" not in lower and not re.search(r"\b(p[1-6]|punta|llano|valle)\b", lower):
                continue
            if any(bad in lower for bad in filtered_keywords):
                continue
            consumo_lines.append(clean)

        consumo_source = "\n".join(consumo_lines) if consumo_lines else raw_text
        normalized_consumo_text = normalize_text(consumo_source)

        consume_patterns = {
            "p1": [
                # Consumo explícito P1 con kwh
                r"(?i)consumo\s+(?:de\s+)?(?:energía\s+)?.*?\bP1\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
                # P1 solo seguido de número y posible kwh
                r"(?i)\bP1\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
                # Punta (Spanish term for P1)
                r"(?i)\bpunta\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
                # Consumo punta explícito
                r"(?i)consumo\s+punta[\s\S]{0,50}?([\d.,]+)",
                # Número solo después de "P1:" o "Punta:"
                r"(?i)(?:P1|punta)\s*[:\-]?\s*([\d.,]+)",
                # Tabla format: "P1 XXX" (números grandes, típicamente > 50)
                r"\bP1\b\s+([\d.,]+)(?:\s|$)",
            ],
            "p2": [
                # Consumo explícito P2 con kwh
                r"(?i)consumo\s+(?:de\s+)?(?:energía\s+)?.*?\bP2\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
                # P2 solo seguido de número
                r"(?i)\bP2\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
                # Llano (Spanish term for P2)
                r"(?i)\bllano\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
                # Consumo llano explícito
                r"(?i)consumo\s+llano[\s\S]{0,50}?([\d.,]+)",
                # Número solo después de "P2:" o "Llano:"
                r"(?i)(?:P2|llano)\s*[:\-]?\s*([\d.,]+)",
                # Tabla format
                r"\bP2\b\s+([\d.,]+)(?:\s|$)",
            ],
            "p3": [
                # Consumo explícito P3 con kwh
                r"(?i)consumo\s+(?:de\s+)?(?:energía\s+)?.*?\bP3\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
                # P3 solo seguido de número
                r"(?i)\bP3\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
                # Valle (Spanish term for P3)
                r"(?i)\bvalle\b[\s\S]{0,100}?([\d.,]+)\s*(?:kwh)?",
                # Consumo valle explícito
                r"(?i)consumo\s+valle[\s\S]{0,50}?([\d.,]+)",
                # Número solo después de "P3:" o "Valle:"
                r"(?i)(?:P3|valle)\s*[:\-]?\s*([\d.,]+)",
                # Tabla format
                r"\bP3\b\s+([\d.,]+)(?:\s|$)",
            ],
            "p4": [
                r"(?i)consumo.*?P4.*?[:\-]?\s*([\d.,]+)",
                r"(?i)\bP4\b\s+([\d.,]+)",
            ],
            "p5": [
                r"(?i)consumo.*?P5.*?[:\-]?\s*([\d.,]+)",
                r"(?i)\bP5\b\s+([\d.,]+)",
            ],
            "p6": [
                r"(?i)consumo.*?P6.*?[:\-]?\s*([\d.,]+)",
                r"(?i)\bP6\b\s+([\d.,]+)",
            ],
        }

        for p_key, patterns in consume_patterns.items():
            key = f"consumo_{p_key}_kwh"
            value_found = None
            
            for pat in patterns:
                m = re.search(pat, normalized_consumo_text, re.IGNORECASE)
                if m:
                    try:
                        candidate = parse_es_number(m.group(1))
                        # Validación: consumos típicos son entre 0 y 5000 kWh por período
                        if candidate is not None and 0 < candidate <= 5000:
                            value_found = candidate
                            break
                    except:
                        continue
            
            data[key] = value_found
            detected_pf[key] = value_found is not None

        # IMPROVED FALLBACK: Search for consumo values in table-like structures
        # Common pattern in Spanish invoices: table with columns P1, P2, P3, etc.
        table_lines = []
        for ln in raw_text.splitlines():
            clean = ln.strip()
            # Lines que contienen P1, P2, P3 o números separados por espacios/tabs
            if re.search(r"\bP[1-6]\b|consumo|punta|llano|valle", clean, re.IGNORECASE):
                table_lines.append(clean)
        
        # Try to extract consumos from table lines when not found yet
        for p_num in range(1, 7):
            key = f"consumo_p{p_num}_kwh"
            if data[key] is not None:
                continue  # Ya fue encontrado
            
            # Buscar en líneas específicas
            period_names = {
                1: ["punta", "p1"],
                2: ["llano", "p2"],
                3: ["valle", "p3"],
                4: ["p4"],
                5: ["p5"],
                6: ["p6"],
            }
            
            for line in table_lines:
                line_lower = line.lower()
                # Check if this line contains the period label
                if not any(name in line_lower for name in period_names.get(p_num, [])):
                    continue
                
                # Try to extract a number from this line
                nums = re.findall(r"([\d.,]+)", line)
                for num_str in nums:
                    try:
                        val = parse_es_number(num_str)
                        if val is not None and 0 < val <= 5000:
                            data[key] = val
                            detected_pf[key] = True
                            break
                    except:
                        continue
                if data[key] is not None:
                    break

        # Final fallback for bare period lines (e.g. "P2: 18" with space/newline)
        # Only enable if we detected at least ONE consumo
        has_any_consumo = any(
            data.get(f"consumo_p{i}_kwh") is not None for i in range(1, 7)
        )
        if has_any_consumo:
            lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
            for ln in lines:
                low = ln.lower()
                if "potencia" in low or re.search(r"\bkw\b", low):
                    continue
                # Match "P1: 123" or "P1 123"
                m = re.match(r"^p\s*([1-6])\s*[:\-]?\s*([\d.,]+)\s*(?:kwh)?\b", low, re.IGNORECASE)
                if not m:
                    m = re.match(r"^p\s*([1-6])\s+([\d.,]+)\s*(?:kwh)?\b", low, re.IGNORECASE)
                if not m:
                    continue
                pnum = int(m.group(1))
                key = f"consumo_p{pnum}_kwh"
                if data.get(key) is None:
                    data[key] = parse_es_number(m.group(2))
                    detected_pf[key] = data[key] is not None

        bono = re.search(r"\bbono\s+social\b", raw_text, re.IGNORECASE)
        data["bono_social"] = True if bono else None
        detected_pf["bono_social"] = bono is not None

        data["parsed_fields"] = detected_pf
        return data

    structured = parse_structured_fields(full_text)
    parsed_fields.update(structured.get("parsed_fields", {}))

    # Merge strategies
    if structured.get("cups"):
        result["cups"] = structured.get("cups")
    else:
        # Fallback regex (Improved to capture full Iberdrola CUPS)
        cups_match = re.search(r"(ES[ \t0-9A-Z\-]{18,28})", full_text, re.IGNORECASE)
        if cups_match:
            raw_cups = cups_match.group(1).upper().splitlines()[0]
            cleaned_cups = re.sub(r"[\s\-]", "", raw_cups)
            # Re-verify Mod529 or at least length
            valid_cups = re.search(r"ES[0-9A-Z]{18,22}", cleaned_cups)
            result["cups"] = valid_cups.group(0) if valid_cups else cleaned_cups[:22]

    atr_value = extract_atr(full_text)
    if atr_value:
        result["atr"] = atr_value
        extraction_summary["atr_source"] = "raw_text"
    elif structured.get("atr"):
        result["atr"] = structured.get("atr")
        extraction_summary["atr_source"] = "structured"

    detected = {}
    detected["atr"] = result["atr"] is not None

    forced_period_missing = False

    def _invalidate_periodo():
        nonlocal forced_period_missing
        result["dias_facturados"] = None
        forced_period_missing = True

    def _check_periodo():
        nonlocal forced_period_missing
        val = result.get("dias_facturados")
        if val is None:
            return
        # Solo invalidar si es claramente imposible. Hay facturas de 60 días, trimestrales, etc.
        if not isinstance(val, int):
            try:
                val = int(val)
                result["dias_facturados"] = val
            except Exception:
                _invalidate_periodo()
                return
        if val <= 0 or val > 370:
            _invalidate_periodo()
        else:
            forced_period_missing = False

    potencias = _extract_potencias_with_sources(full_text)
    if potencias["p1"] is not None:
        result["potencia_p1_kw"] = potencias["p1"]
        extraction_summary["potencia_p1_source"] = potencias["p1_source"] or "raw_text"
    if potencias["p2"] is not None:
        result["potencia_p2_kw"] = potencias["p2"]
        extraction_summary["potencia_p2_source"] = potencias["p2_source"] or "raw_text"
    if potencias["warnings"]:
        extraction_summary["parse_warnings"].extend(potencias["warnings"])

    # Generic total consumption - VERY STRICT to avoid period-specific values
    consumo_match = re.search(r"(?i)(?:consumo\s+total|total\s+consumo|consumo\s+(?:facturado|del\s+periodo))[^0-9\n]{0,50}([\d.,]+)\s*kwh", full_text)
    
    if consumo_match:
        result["consumo_kwh"] = parse_es_number(consumo_match.group(1))
        detected["consumo_kwh"] = True
    else:
        result["consumo_kwh"] = None
        detected["consumo_kwh"] = False

    # Total Importe Strategy
    if structured.get("importe_factura"):
        # Highest priority from structured (explicit TOTAL FACTURA)
        result["importe"] = structured.get("importe_factura")
        detected["importe"] = True
    else:
        # Fallback strategy
        total_match = re.search(r"TOTAL.*?\s+(\d+[.,]?\d*)\s*(?:€|EUR)", full_text, re.IGNORECASE)
        if total_match:
            result["importe"] = parse_es_number(total_match.group(1))
            detected["importe"] = result["importe"] is not None
        
        if result["importe"] is None:
            # Find max money value
            matches = re.findall(r"(\d+[.,]?\d*)\s*(?:€|EUR)", full_text, re.IGNORECASE)
            if matches:
                vals = [parse_es_number(m) for m in matches]
                vals = [v for v in vals if v is not None]
                if vals:
                    result["importe"] = max(vals)
                    detected["importe"] = True

    if result["importe"] is None and structured.get("importe_factura") is not None:
        result["importe"] = structured.get("importe_factura")
        detected["importe"] = True
    if "importe" not in detected:
        detected["importe"] = False

    # Dates
    date_matches = re.findall(r"(\d{4}[/-]\d{2}[/-]\d{2}|\d{2}[/-]\d{2}[/-]\d{4})", full_text)
    if date_matches:
        result["fecha"] = date_matches[0]
        detected["fecha"] = True
    
    # Prefer structured start/end
    if structured.get("fecha_inicio_consumo"):
        result["fecha_inicio_consumo"] = structured.get("fecha_inicio_consumo")
    if structured.get("fecha_fin_consumo"):
        result["fecha_fin_consumo"] = structured.get("fecha_fin_consumo")

    if structured.get("dias_facturados"):
         if "parsed_fields" not in result:
             result["parsed_fields"] = {}
         result["parsed_fields"]["dias_facturados"] = structured.get("dias_facturados")
         result["dias_facturados"] = structured.get("dias_facturados") # Add to root too

    _check_periodo()

    # Extraer Numero de Factura
    num_fact_match = re.search(
        r"(?:n[º°].?|num\.?|numero|número)\s*(?:de)?\s*factura\s*[:\-]?\s*([A-Z0-9\-\/]{3,30})", 
        full_text, 
        re.IGNORECASE
    )
    if num_fact_match:
        result["numero_factura"] = num_fact_match.group(1).strip()
    else:
        # Fallback simple: busca "Factura: XXXXX"
        simple_match = re.search(r"factura\s*[:]\s*([A-Z0-9\-\/]{3,30})", full_text, re.IGNORECASE)
        result["numero_factura"] = simple_match.group(1).strip() if simple_match else None


    def _is_valid_name(candidate: str) -> bool:
        if not candidate:
            return False
        cleaned = candidate.strip(" :,-\t\r\n")
        if not cleaned:
            return False
        if re.search(r"\d", cleaned):
            return False
        # Extended keywords filter as requested
        keywords = [
            "dni", "cif", "nif", "direccion", "dirección", "telefono", "teléfono", "email", "cups", 
            "importe", "factura", "comercializadora", "regulada", "grupo", "s.a", "sl", 
            "naturgy", "endesa", "iberdrola", "repsol", "energia", "energy", "gas", "power",
            # New technical keywords
            "consumo", "periodo", "punta", "valle", "kwh", "kw", "acumulado", "estimado", "media", "potencia"
        ]
        if any(k.lower() in cleaned.lower() for k in keywords):
            return False
        if len(cleaned.split()) < 2:
            return False
        if len(cleaned.split()) > 6: # Heuristic: Name too long likely noise
             return False
        return True

    def _clean_name(candidate: str) -> str:
        if not candidate:
            return None
        candidate = re.sub(r"\s{2,}", " ", candidate)
        return candidate.strip(" :,-\t\r\n")

    def _is_address_candidate(line: str) -> bool:
        if not line:
            return False
        text = line.lower()
        # Extended address exclusion terms
        if any(k in text for k in ["cups", "dni", "nif", "cif", "factura", "importe", "potencia", "suministro", "punto de suministro", "contrato"]):
            return False
        if len(line.strip()) < 6:
            return False
        has_letter = re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", line)
        has_number = re.search(r"\d", line)
        return bool(has_letter and has_number)

    titular = None
    name_line_index = None

    # Logic to find Titular near DNI (Heuristic)
    # Applied to both Image and PDF text to improve coverage
    raw_lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
    label_keywords = {"titular", "dni", "cif", "nif", "telefono", "teléfono", "email", "direccion", "dirección", "cups"}
    filtered_lines = []
    
    # Pre-filter lines just in case (though we use raw_lines for scanning)
    dni_pattern = re.compile(r"\b\d{8}[A-Z]\b", re.IGNORECASE)
    dni_indices_raw = []
    for idx, ln in enumerate(raw_lines):
        if dni_pattern.search(ln.replace(" ", "")):
            dni_indices_raw.append(idx)
            
    for idx in dni_indices_raw:
        found = False
        for back in range(1, 4):
            if idx - back >= 0:
                candidate = _clean_name(raw_lines[idx - back])
                if _is_valid_name(candidate):
                    titular = candidate
                    name_line_index = idx - back
                    found = True
                    break
        if found:
            break

    if not titular:
        titular_block_match = re.search(
            r"(titular|nombre del titular)\s*[:\-]?\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ ,.'´`-]{3,80})",
            full_text,
            re.IGNORECASE,
        )
        if titular_block_match:
            linea = _clean_name(titular_block_match.group(2))
            if _is_valid_name(linea):
                titular = linea

    result["titular"] = titular

    match_dni = re.search(r"(?:dni|cif|nif)?\s*[:\-]?\s*([0-9]{8}[A-Z])", full_text, re.IGNORECASE)
    if match_dni:
        result["dni"] = re.sub(r"\s+", "", match_dni.group(1)).strip()

    # Updated regex to handle "Dirección" with accent
    dir_patterns = [
        r"direcci[oó]n(?:\s+de\s+suministro)?\s*[:\-]?\s*([A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ ,.'´`-]{5,120})",
        r"domicilio\s*[:\-]?\s*([A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ ,.'´`-]{5,120})",
    ]
    for pattern in dir_patterns:
        match_dir = re.search(pattern, full_text, re.IGNORECASE)
        if match_dir:
            result["direccion"] = match_dir.group(1).strip()
            break
            
    # Enable heuristic search for Address/Name for both Image and PDF (text)
    # The 'is_image' check was preventing this logic for digital PDFs where pypdf returns lines.
    if result["direccion"] is None and name_line_index is not None:
        raw_lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
        for forward in range(1, 3):
            if name_line_index + forward < len(raw_lines):
                candidate_dir = raw_lines[name_line_index + forward]
                if _is_address_candidate(candidate_dir):
                    result["direccion"] = candidate_dir.strip()
                    break

    match_tel = re.search(
        r"(?:tel(?:efono)?|phone)?[^\d]{0,12}(\b[6789]\d{2}[.\s\-]?\d{3}[.\s\-]?\d{3}\b)",
        full_text,
        re.IGNORECASE,
    )
    if match_tel:
        telefono = re.sub(r"[.\s\-]", "", match_tel.group(1))
        if not telefono.startswith(("800", "900", "901", "902", "905")):
            result["telefono"] = telefono
            detected["telefono"] = True
        else:
            detected["telefono"] = False
    else:
        detected["telefono"] = False

    def _extract_number(patterns):
        for pat in patterns:
            m = re.search(pat, full_text, re.IGNORECASE)
            if m:
                val = parse_es_number(m.group(1))
                if val is not None:
                    return val
                continue
        return None

    if result["potencia_p1_kw"] is None:
        result["potencia_p1_kw"] = _extract_number(
            [r"potencia\s*p1[^0-9]{0,10}([\d.,]+)\s*k?w", r"potencia\s+punta[^0-9]{0,10}([\d.,]+)\s*k?w"]
        )
    if result["potencia_p2_kw"] is None:
        result["potencia_p2_kw"] = _extract_number(
            [r"potencia\s*p2[^0-9]{0,10}([\d.,]+)\s*k?w", r"potencia\s+valle[^0-9]{0,10}([\d.,]+)\s*k?w"]
        )
    detected["potencia_p1_kw"] = result["potencia_p1_kw"] is not None
    detected["potencia_p2_kw"] = result["potencia_p2_kw"] is not None

    for field in [
        "consumo_p1_kwh", "consumo_p2_kwh", "consumo_p3_kwh",
        "consumo_p4_kwh", "consumo_p5_kwh", "consumo_p6_kwh"
    ]:
        if result.get(field) is None and structured.get(field) is not None:
             result[field] = structured.get(field)
             detected[field] = True
    
    bono_match = re.search(r"\bbono\s+social\b", full_text, re.IGNORECASE)
    result["bono_social"] = True if bono_match else None
    detected["bono_social"] = bono_match is not None

    sv_match = re.search(r"\bservicios\s+vinculados\b", full_text, re.IGNORECASE)
    result["servicios_vinculados"] = True if sv_match else None
    detected["servicios_vinculados"] = sv_match is not None

    result["alquiler_contador"] = _extract_number(
        [
            r"alquiler\s+(?:de\s+)?(?:equipos|contador|medida)[^0-9]{0,20}([\d.,]+)", 
            r"equipos\s+de\s+medida[^0-9]{0,20}([\d.,]+)",
            r"contador\s+alquiler[^0-9]{0,10}([\d.,]+)"
        ]
    )
    detected["alquiler_contador"] = result["alquiler_contador"] is not None

    result["impuesto_electrico"] = _extract_number(
        [
            r"impuesto\s+.*?\b([\d.,]+)\s*€\s*$",
            r"impuesto\s+(?:sobre\s+la\s+)?electricidad[^0-9]{0,40}([\d.,]+)",
            r"impuesto\s+el[eé]ctrico[^0-9]{0,40}([\d.,]+)"
        ]
    )
    detected["impuesto_electrico"] = result["impuesto_electrico"] is not None

    result["iva"] = _extract_number([r"\biva\b[^0-9]{0,10}([\d.,]+)"])
    detected["iva"] = result["iva"] is not None

    # ⭐ IVA SIEMPRE AL 21% (Fiscalidad actual española)
    result["iva_porcentaje"] = 21.0
    detected["iva_porcentaje"] = True
    
    if "iva_porcentaje" not in detected:
        detected["iva_porcentaje"] = False

    # Total Factura Final Consolidation
    if result["total_factura"] is None and structured.get("importe_factura") is not None:
         result["total_factura"] = structured.get("importe_factura")
    
    # Fallback to plain regex if still missing (already done in structured/matches above)
    if result["total_factura"] is None:
         result["total_factura"] = result.get("importe")

    detected["total_factura"] = result["total_factura"] is not None

    
    # Limpiar titular de etiquetas comunes
    if result.get("titular"):
        for prefix in ["Nombre:", "Cliente:", "Titular:", "NOMBRE:", "CLIENTE:", "TITULAR:"]:
            if result["titular"].startswith(prefix):
                result["titular"] = result["titular"][len(prefix):].strip()

    if result["direccion"]:
        # Intento simple de extraer provincia de la direccion
        provincias = [
            "Álava", "Albacete", "Alicante", "Almería", "Asturias", "Ávila", "Badajoz", "Barcelona", "Burgos", "Cáceres",
            "Cádiz", "Cantabria", "Castellón", "Ciudad Real", "Córdoba", "Cuenca", "Girona", "Granada", "Guadalajara",
            "Guipúzcoa", "Huelva", "Huesca", "Illes Balears", "Jaén", "La Rioja", "Las Palmas", "León", "Lleida", "Lugo",
            "Madrid", "Málaga", "Murcia", "Navarra", "Ourense", "Palencia", "Pontevedra", "Salamanca", "Santa Cruz de Tenerife",
            "Segovia", "Sevilla", "Soria", "Tarragona", "Teruel", "Toledo", "Valencia", "Valladolid", "Vizcaya", "Zamora", "Zaragoza",
            "A Coruña", "Ceuta", "Melilla"
        ]
        addr_lower = result["direccion"].lower()
        for prov in provincias:
            if prov.lower() in addr_lower:
                result["provincia"] = prov
                break
        if "provincia" not in result:
             result["provincia"] = None
    else:
        result["provincia"] = None

    # [PATCH BUG B] Periodo_dias calculated from Dates (PRIMARY SOURCE)
    if result.get("fecha_inicio_consumo") and result.get("fecha_fin_consumo"):
        d_ini = _parse_date_flexible(result["fecha_inicio_consumo"])
        d_fin = _parse_date_flexible(result["fecha_fin_consumo"])
        if d_ini and d_fin:
            dias = (d_fin - d_ini).days + 1
            if dias > 0:
                result["dias_facturados"] = dias
                result["detected_por_ocr"]["dias_facturados"] = True
                
    # If still None, ensure it is flagged (logic implied by final check)
    if result.get("dias_facturados") is None:
         pass

    _check_periodo()

    # [PATCH BUG C] Guardia de consumos absurdos
    sum_periodos = sum([result.get(f"consumo_p{i}_kwh") or 0 for i in range(1, 4)])
    consumo_tot = result.get("consumo_kwh")
    
    # Solo limpiamos si sum_periodos es significativamente distinta del total O absurdamente alta
    has_crazy_sum = (consumo_tot and consumo_tot > 0 and sum_periodos > consumo_tot * 3)
    has_absurdly_huge_sum = (sum_periodos > 2000)
    
    # EXCEPCIÓN: Si sum_periodos es 0, no es "absurda", es simplemente "missing"
    if (has_crazy_sum or has_absurdly_huge_sum) and sum_periodos > 0:
        import logging
        logging.warning(f"🛡️ [OCR] Coherencia fallida (P1+P2+P3={sum_periodos}, Total={consumo_tot}). Seteando consumos a NULL para corrección manual.")
        for i in range(1, 7):
            result[f"consumo_p{i}_kwh"] = None
            result["detected_por_ocr"][f"consumo_p{i}_kwh"] = False
    
    # [PATCH BUG E] Monetary Guards
    if result.get("alquiler_contador") and result["alquiler_contador"] > 10:
        import logging
        logging.warning(f"🛡️ [OCR] Alquiler contador {result['alquiler_contador']} > 10. Descartando por sospechoso.")
        result["alquiler_contador"] = None

    if result.get("impuesto_electrico") and result.get("total_factura"):
        # If tax > 15% of total, it's garbage (should be 5% max usually)
        if result["impuesto_electrico"] > result["total_factura"] * 0.15:
             logging.warning(f"🛡️ [OCR] Impuesto eléctrico {result['impuesto_electrico']} > 15% de total {result['total_factura']}. Descartando.")
             result["impuesto_electrico"] = None

    # [PATCH BUG D] Concept Shield
    result = _shield_concepts(result)

    # Fallback: total consumption from period sums when total is missing
    sum_periodos_actual = sum([result.get(f"consumo_p{i}_kwh") or 0 for i in range(1, 7)])
    has_periodos = any(result.get(f"consumo_p{i}_kwh") is not None for i in range(1, 7))
    if result.get("consumo_kwh") is None and has_periodos and sum_periodos_actual > 0:
        result["consumo_kwh"] = sum_periodos_actual
        detected["consumo_kwh"] = True



    # --- Normalización final (fechas + limpieza de conceptos) ---
    def _date_to_iso(d):
        try:
            return d.isoformat()
        except Exception:
            return None

    # Normalizar fechas a ISO (YYYY-MM-DD) para consistencia DB/deduplicación
    for k in ("fecha", "fecha_inicio_consumo", "fecha_fin_consumo"):
        v = result.get(k)
        if isinstance(v, str):
            d = _parse_date_flexible(v)
            if d:
                result[k] = _date_to_iso(d)
        else:
            if v is not None:
                try:
                    result[k] = _date_to_iso(v)
                except Exception:
                    pass

    # Aplicar blindaje contra mezcla de conceptos (potencia/consumo, IEE 5.11, etc.)
    result = _shield_concepts(result)

    # --- QA logs solo en TEST_MODE ---
    if os.getenv("TEST_MODE") == "true":
        print(f"--- [QA AUDIT] Backend Extraction Summary ---")
        print(f"✅ cups: {result.get('cups')}")
        print(f"✅ atr: {result.get('atr')}")
        print(f"✅ total_factura: {result.get('total_factura')}")
        print(f"✅ periodo_dias: {result.get('dias_facturados')}")
        print(f"✅ consumo_total: {result.get('consumo_kwh')}")
        print(f"✅ sum_periodos: {sum_periodos_actual}")
        print(f"----------------------------------------------")

    required_fields = [
        "atr",
        "potencia_p1_kw",
        "potencia_p2_kw",
        "consumo_p1_kwh",
        "consumo_p2_kwh",
        "consumo_p3_kwh",
        "total_factura",
    ]
    missing_fields = []
    for field in required_fields:
        val = result.get(field)
        if isinstance(val, str):
            if not val.strip():
                missing_fields.append(field)
        elif val is None:
            missing_fields.append(field)

    if forced_period_missing and result.get("dias_facturados") is None and "periodo_dias" not in missing_fields:
        missing_fields.append("periodo_dias")

    result["parsed_fields"] = parsed_fields
    result["detected_por_ocr"] = detected
    result["extraction_summary"] = extraction_summary
    result["missing_fields"] = missing_fields


    return result



def extract_data_with_gemini(file_bytes: bytes, is_pdf: bool = True) -> dict:
    """
    Extracción premium usando Gemini 1.5 Flash.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")  # Reverted to 1.5 Flash for multimodal stability

        # Preparar el archivo para Gemini
        mime_type = "application/pdf" if is_pdf else "image/jpeg"
        # Prompt optimizado para facturas eléctricas españolas (Blindaje de Consumos)
        prompt = """
        Extrae los siguientes campos de esta factura eléctrica española en formato JSON estricto.
        
        REGLA CRÍTICA DE CONCEPTOS:
        - NUNCA uses los valores de 'Potencia Contratada' (kW) como 'Consumo' (kWh). Son conceptos distintos.
        - La Potencia (kW) suele ser un número pequeño y fijo (ej: 3.3, 4.6, 5.5, 9.2).
        - El Consumo (kWh) es la energía gastada. Si ves que un número se repite en ambos sitios, prioriza asignarlo a Potencia y deja el Consumo como null si no estás seguro.
        - Diferencia claramente entre 'Lectura del contador' (número grande acumulado) y 'Consumo del periodo' (lo facturado este mes). 
        - Queremos el CONSUMO REAL DEL PERIODO.
        - REGLA DE ORO: La suma de (consumo_p1 + consumo_p2 + consumo_p3) DEBE coincidir con el consumo total del periodo.
        
        Campos:
        - cups: ES + 18-20 caracteres (Suele empezar por ES00).
        - titular: Nombre completo del cliente.
        - dni: DNI/NIF/CIF.
        - direccion: Dirección de suministro.
        - fecha_inicio_consumo, fecha_fin_consumo (DD/MM/YYYY)
        - dias_facturados: Número de días total del periodo (int).
        - importe_factura: Total factura con impuestos e IVA (número).
        - atr: Peaje de acceso (ej: 2.0TD o 3.0TD).
        - potencia_p1_kw, potencia_p2_kw: Potencia contratada en kW (ej: 4.6).
        - consumo_p1_kwh, consumo_p2_kwh, consumo_p3_kwh: Energía consumida en kWh (SOLO CONSUMO, NO LECTURAS).
        - bono_social (bool), alquiler_contador (float - importe en €), impuesto_electrico (float - importe en €, NO el porcentaje), iva (float - importe en €).
        
        IMPORTANTE: Si la factura tiene varias páginas, procésalas todas. 
        Si un campo no está, pon null. Solo devuelve el JSON puro.
        """

        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": file_bytes}
        ])

        # Limpiar la respuesta para obtener solo el JSON
        text_response = response.text.strip()
        print(f"DEBUG: Gemini raw response: {text_response[:200]}...") # Log partial response
        if text_response.startswith("```json"):
            text_response = text_response.split("```json")[1].split("```")[0].strip()
        elif text_response.startswith("```"):
             text_response = text_response.split("```")[1].split("```")[0].strip()

        data = json.loads(text_response)
        
        # Mapear a la estructura de resultado esperada
        result = _empty_result("Extraído con Gemini 1.5 Flash")
        result["ocr_engine"] = "gemini-1.5-flash"
        
        # Poblar campos básicos
        for key in data:
            if key in result:
                result[key] = data[key]
            elif key == "importe_factura":
                result["total_factura"] = data[key]
        
        # Asegurar que cups esté normalizado y limpio
        # Asegurar que cups esté normalizado y limpio
        if result.get("cups"):
            cand = str(result["cups"])
            norm = normalize_cups(cand)
            
            # Validar con algoritmo oficial
            if norm and is_valid_cups(norm):
                result["cups"] = norm
            else:
                print(f"[GEMINI CHECK] CUPS rechazado (inválido): {cand}")
                result["cups"] = None
                if "cups" not in result["missing_fields"]:
                     result["missing_fields"].append("cups")

        # Completar metadatos
        result["parsed_fields"] = {k: v is not None for k, v in data.items()}
        result["detection_method"] = "gemini-1.5-flash"

        # [PATCH P0] Saneado post-Gemini
        if result.get("iva_porcentaje") is None:
            result["iva_porcentaje"] = 21.0
        
        # Fallback periodo_dias (Bug B)
        if result.get("dias_facturados") is None and result.get("fecha_inicio_consumo") and result.get("fecha_fin_consumo"):
            d_ini = _parse_date_flexible(result["fecha_inicio_consumo"])
            d_fin = _parse_date_flexible(result["fecha_fin_consumo"])
            if d_ini and d_fin:
                dias = (d_fin - d_ini).days + 1
                if dias > 0:
                    result["dias_facturados"] = dias
                    print(f"[GEMINI] Calculado periodo_dias fallback: {dias}")

        # [PATCH BUG D] Concept Shield
        result = _shield_concepts(result)

        return result

    except Exception as e:
        logging.error(f"❌ Error en Gemini Extraction: {str(e)}")
        logging.error(traceback.format_exc())
        return None

def extract_data_from_pdf(file_bytes: bytes) -> dict:
    is_pdf = file_bytes.startswith(b"%PDF")
    
    # [CUPS-AUDIT] LOG #1: Motor OCR previsto
    import os
    gemini_key_present = bool(os.getenv("GEMINI_API_KEY"))
    app_version = os.getenv("APP_VERSION", "unknown")
    print(f"""
[CUPS-AUDIT] #1 - OCR ENGINE SELECTION
  Motor previsto: {'GEMINI-1.5-FLASH' if gemini_key_present else 'PYPDF/VISION'}
  GEMINI_API_KEY presente: {gemini_key_present}
  APP_VERSION: {app_version}
  Tipo archivo: {'PDF' if is_pdf else 'IMAGE'}
""")
    
    # INTENTAR GEMINI PRIMERO (Premium)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("Intentando extracción premium con Gemini 1.5 Flash...")
        gemini_result = extract_data_with_gemini(file_bytes, is_pdf=is_pdf)
        if gemini_result:
            return gemini_result
        print("Fallo Gemini, reintentando con método tradicional...")

    if is_pdf:
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            if len(full_text.strip()) > 50:
                print("PDF digital detectado. Usando pypdf.")
                return parse_invoice_text(full_text)
            else:
                msg = "PDF escaneado detectado. Por favor, sube una imagen (JPG/PNG) o usa un PDF original."
                return _empty_result(msg)
        except Exception as e:
            print(f"Error leyendo PDF con pypdf: {e}")
            pass

    client, auth_log = get_vision_client()
    if not client:
        return _empty_result(f"Error configuracion credenciales:\n{auth_log}")

    image = vision.Image(content=file_bytes)

    try:
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if not texts:
            return _empty_result(
                "El OCR no detecto texto. Si es un PDF, asegurate de subirlo como imagen (JPG/PNG)."
            )

        full_text = texts[0].description
        return parse_invoice_text(full_text, is_image=True)

    except Exception as e:
        print(f"Error en Vision API: {e}")
        return _empty_result(f"Error procesando OCR: {str(e)}\n\n--- DEBUG LOG ---\n{auth_log}")
