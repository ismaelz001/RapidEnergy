import os
import json
import re
import io
import unicodedata
from google.oauth2 import service_account
from google.cloud import vision
import pypdf
import google.generativeai as genai


def normalize_text(raw: str) -> str:
    if raw is None:
        return ""
    text = unicodedata.normalize("NFKC", raw)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def parse_es_number(value: str):
    if value is None:
        return None
    text = normalize_text(str(value))
    if not text:
        return None
    cleaned = re.sub(r"[^\d,.\-]", "", text)
    if cleaned in ("", "-", ".", ","):
        return None

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
        cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)
    except Exception:
        return None


def extract_atr(text: str):
    if not text:
        return None
    normalized = normalize_text(text).upper()
    if re.search(r"\b2\s*[.,]?\s*[0O]\s*TD\b", normalized):
        return "2.0TD"
    return None


def _extract_potencias_with_sources(text: str):
    if not text:
        return {"p1": None, "p2": None, "p1_source": None, "p2_source": None, "warnings": []}
    normalized = normalize_text(text)

    p1_patterns = [
        ("punta", r"potencia\s+(?:contratada\s+)?(?:en\s+)?punta[^0-9]{0,20}([\d.,]+)"),
        ("p1", r"potencia\s+(?:contratada\s+)?(?:en\s+)?p1[^0-9]{0,20}([\d.,]+)"),
        # Nuevos patrones permisivos (fix Naturgy): "ncia contratada...", "contratada en punta..."
        ("punta", r"(?:potencia|ncia)\s+(?:contratada\s+)?(?:en\s+)?punta[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)?"),
        ("punta", r"contratada\s+(?:en\s+)?punta[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)?"),
        # Fallbacks genéricos
        ("punta", r"\bpunta\b[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)"),
        ("p1", r"\bp1\b[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)"),
    ]
    p2_patterns = [
        ("valle", r"potencia\s+(?:contratada\s+)?(?:en\s+)?valle[^0-9]{0,20}([\d.,]+)"),
        ("p2", r"potencia\s+(?:contratada\s+)?(?:en\s+)?p2[^0-9]{0,20}([\d.,]+)"),
        # Nuevos patrones permisivos (fix Naturgy)
        ("valle", r"(?:potencia|ncia)\s+(?:contratada\s+)?(?:en\s+)?valle[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)?"),
        ("valle", r"contratada\s+(?:en\s+)?valle[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)?"),
        # Fallbacks genéricos
        ("valle", r"\bvalle\b[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)"),
        ("p2", r"\bp2\b[^0-9]{0,60}([\d.,]+)\s*(?:kw|k\s*w|k)"),
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
            "consumo_p6_kwh": None,
            "bono_social": None,
            "parsed_fields": {},
        }
        detected_pf = {}

        # 1. CUPS VALIDATION ROBUSTA
        # Buscamos candidatos que empiecen por ES y tengan longitud plausible
        # Normalizamos y pasamos el validador oficial.
        candidates = re.findall(r"(ES[A-Z0-9\-\s]{18,25})", raw_text, re.IGNORECASE)
        valid_cups_found = None
        
        for cand in candidates:
            # Normalizar
            norm = normalize_cups(cand)
            if not norm:
                continue
                
            # Validar Módulo 529
            if is_valid_cups(norm):
                valid_cups_found = norm
                break # Encontramos uno válido
        
        data["cups"] = valid_cups_found
        
        detected_pf["cups"] = data["cups"] is not None

        # 2. Fechas range (Multiple formats)
        # Format 1: 31 de agosto de 2025 a 30 de septiembre...
        meses = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
        rango_text = re.search(
            rf"(\d{{1,2}}\s+de\s+(?:{meses})\s+de\s+\d{{4}})\s+a\s+(\d{{1,2}}\s+de\s+(?:{meses})\s+de\s+\d{{4}})",
            raw_text,
            re.IGNORECASE,
        )
        if rango_text:
            data["fecha_inicio_consumo"] = rango_text.group(1)
            data["fecha_fin_consumo"] = rango_text.group(2)

        # Format 2: dd/mm/yyyy - dd/mm/yyyy or similar
        # "PERIODO DE FACTURACIÓN: 31/08/2025 - 30/09/2025"
        if not data["fecha_inicio_consumo"]:
            rango_fechas = re.search(
                r"(\d{2}[/-]\d{2}[/-]\d{4})\s*(?:-|al|a)\s*(\d{2}[/-]\d{2}[/-]\d{4})", 
                raw_text, 
                re.IGNORECASE
            )
            if rango_fechas:
                data["fecha_inicio_consumo"] = rango_fechas.group(1)
                data["fecha_fin_consumo"] = rango_fechas.group(2)
        
        detected_pf["fecha_inicio_consumo"] = data["fecha_inicio_consumo"] is not None
        detected_pf["fecha_fin_consumo"] = data["fecha_fin_consumo"] is not None

        # 2b. Dias Facturados
        # Allow extra spaces or chars between words
        dias_match = re.search(r"(?:dias|días|periodo)[^0-9\n]{0,30}facturad[oa]s?[^0-9\n]{0,10}[:]\s*(\d+)", raw_text, re.IGNORECASE)
        if not dias_match:
             # Very simple fallback: "DIAS FACTURADOS: 30"
             dias_match = re.search(r"DIAS\s+FACTURADOS\s*[:]\s*(\d+)", raw_text, re.IGNORECASE)

        if dias_match:
            try:
                data["dias_facturados"] = int(dias_match.group(1))
            except:
                pass
        
        # 3. Importe Factura (High Priority)
        # Look for explicit "TOTAL FACTURA" or "TOTAL A PAGAR" to avoid "Base Imponible"
        # BUG C FIX: TOTAL A PAGAR tiene máxima prioridad
        total_pagar_match = re.search(
            r"TOTAL\s+A\s+PAGAR[^0-9\n]{0,30}([\d.,]+)\s*(?:€|EUR)", 
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
        
        # Note: Added 'punta', 'llano', 'valle' keywords
        consume_patterns = {
            "p1": [r"consumo\s+en\s+P1\s*[:\-]?\s*([\d.,]+)", r"punta\s*[:\-]?\s*([\d.,]+)\s*kwh"],
            "p2": [r"consumo\s+en\s+P2\s*[:\-]?\s*([\d.,]+)", r"llano\s*[:\-]?\s*([\d.,]+)\s*kwh"],
            "p3": [r"consumo\s+en\s+P3\s*[:\-]?\s*([\d.,]+)", r"valle\s*[:\-]?\s*([\d.,]+)\s*kwh"],
            "p4": [r"consumo\s+en\s+P4\s*[:\-]?\s*([\d.,]+)", r"supervalle\s*[:\-]?\s*([\d.,]+)\s*kwh"], 
            "p5": [r"consumo\s+en\s+P5\s*[:\-]?\s*([\d.,]+)"],
            "p6": [r"consumo\s+en\s+P6\s*[:\-]?\s*([\d.,]+)"],
        }
        
        for p_key, patterns in consume_patterns.items():
            key = f"consumo_{p_key}_kwh"
            for pat in patterns:
                m = re.search(pat, raw_text, re.IGNORECASE)
                if m:
                    data[key] = parse_es_number(m.group(1))
                    break
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
        # Fallback regex
        cups_match = re.search(r"(ES[ \t0-9A-Z\-]{16,24})", full_text, re.IGNORECASE)
        if cups_match:
            raw_cups = cups_match.group(1).upper().splitlines()[0]
            cleaned_cups = re.sub(r"[\s\-]", "", raw_cups)
            valid_cups = re.search(r"ES[0-9A-Z]{18,24}", cleaned_cups)
            result["cups"] = valid_cups.group(0) if valid_cups else cleaned_cups

    atr_value = extract_atr(full_text)
    if atr_value:
        result["atr"] = atr_value
        extraction_summary["atr_source"] = "raw_text"
    elif structured.get("atr"):
        result["atr"] = structured.get("atr")
        extraction_summary["atr_source"] = "structured"

    detected = {}
    detected["atr"] = result["atr"] is not None

    potencias = _extract_potencias_with_sources(full_text)
    if potencias["p1"] is not None:
        result["potencia_p1_kw"] = potencias["p1"]
        extraction_summary["potencia_p1_source"] = potencias["p1_source"] or "raw_text"
    if potencias["p2"] is not None:
        result["potencia_p2_kw"] = potencias["p2"]
        extraction_summary["potencia_p2_source"] = potencias["p2_source"] or "raw_text"
    if potencias["warnings"]:
        extraction_summary["parse_warnings"].extend(potencias["warnings"])

    # Generic total consumption
    consumo_match = re.search(r"(\d+[.,]?\d*)\s*kWh", full_text, re.IGNORECASE)
    if consumo_match:
        result["consumo_kwh"] = parse_es_number(consumo_match.group(1))
        detected["consumo_kwh"] = result["consumo_kwh"] is not None
    else:
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
        [r"alquiler\s+contador[^0-9]{0,10}([\d.,]+)", r"contador\s+alquiler[^0-9]{0,10}([\d.,]+)"]
    )
    detected["alquiler_contador"] = result["alquiler_contador"] is not None

    result["impuesto_electrico"] = _extract_number(
        [r"impuesto\s+electrico[^0-9]{0,10}([\d.,]+)", r"impuesto\s+el[eé]ctrico[^0-9]{0,10}([\d.,]+)"]
    )
    detected["impuesto_electrico"] = result["impuesto_electrico"] is not None

    result["iva"] = _extract_number([r"\biva\b[^0-9]{0,10}([\d.,]+)"])
    detected["iva"] = result["iva"] is not None

    # Total Factura Final Consolidation
    if result["total_factura"] is None and structured.get("importe_factura") is not None:
         result["total_factura"] = structured.get("importe_factura")
    
    # Fallback to plain regex if still missing (already done in structured/matches above)
    if result["total_factura"] is None:
         result["total_factura"] = result.get("importe")

    detected["total_factura"] = result["total_factura"] is not None

    
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
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Preparar el archivo para Gemini
        mime_type = "application/pdf" if is_pdf else "image/jpeg"
        # Prompt optimizado para facturas eléctricas españolas
        prompt = """
        Extrae los siguientes campos de esta factura eléctrica española y devuélvelos en formato JSON estricto.
        Sé extremadamente preciso con el CUPS, el nombre del titular y el consumo por periodos.
        Los campos son:
        - cups: El código CUPS (ES + 18-20 caracteres).
        - titular: El nombre completo del cliente/titular.
        - dni: DNI o NIF del titular.
        - direccion: Dirección completa del suministro.
        - fecha_inicio_consumo: Fecha de inicio del periodo de facturación (DD/MM/YYYY).
        - fecha_fin_consumo: Fecha de fin del periodo de facturación (DD/MM/YYYY).
        - dias_facturados: Número de días del periodo.
        - importe_factura: Importe total de la factura con IVA (número).
        - atr: Peaje de acceso o tarifa (ej: 2.0TD).
        - potencia_p1_kw: Potencia contratada en P1 (punta).
        - potencia_p2_kw: Potencia contratada en P2 (valle).
        - consumo_p1_kwh: Consumo real en P1 (punta) en kWh.
        - consumo_p2_kwh: Consumo real en P2 (llano) en kWh.
        - consumo_p3_kwh: Consumo real en P3 (valle) en kWh.
        - bono_social: True/False si tiene bono social.
        - alquiler_contador: Importe del alquiler del contador.
        - impuesto_electrico: Importe del impuesto eléctrico.
        - iva: Importe del IVA.

        IMPORTANTE: Diferencia claramente entre 'Lectura del contador' (que suele ser un número grande acumulado) 
        y 'Consumo del periodo' (que es lo facturado en este mes). Queremos el CONSUMO DEL PERIODO.
        Si un campo no se encuentra, pon null.
        Solo devuelve el JSON, nada de texto adicional.
        """

        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": file_bytes}
        ])

        # Limpiar la respuesta para obtener solo el JSON
        text_response = response.text.strip()
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
        
        return result

    except Exception as e:
        print(f"Error en Gemini Extraction: {e}")
        return None

def extract_data_from_pdf(file_bytes: bytes) -> dict:
    is_pdf = file_bytes.startswith(b"%PDF")
    
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
