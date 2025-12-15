import os
import json
import re
import io
from google.oauth2 import service_account
from google.cloud import vision
import pypdf


def _empty_result(raw_text: str = None) -> dict:
    return {
        "cups": None,
        "consumo_kwh": None,
        "importe": None,
        "fecha": None,
        "fecha_inicio_consumo": None,
        "fecha_fin_consumo": None,
        "titular": None,
        "dni": None,
        "direccion": None,
        "telefono": None,
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
        "raw_text": raw_text,
    }


def get_vision_client():
    logs = ["DEBUG AUTH LOG:"]

    # 1. Prioridad: archivo en /etc/secrets (Render)
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

    # 2. Fallback: variable de entorno
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


def parse_invoice_text(full_text: str, is_image: bool = False) -> dict:
    """Parsea texto de factura proveniente de OCR/PDF para obtener campos clave."""
    result = _empty_result(full_text)
    parsed_fields = _empty_result().get("parsed_fields", {})

    def _to_float(val_str: str):
        try:
            return float(val_str.replace(",", "."))
        except Exception:
            return None

    def parse_structured_fields(raw_text: str) -> dict:
        """
        Intenta extraer campos energéticos de forma conservadora.
        Reglas:
        - Solo etiquetas/patrones claros.
        - No se infiere si hay duda: se devuelve None.
        """
        data = {
            "fecha_inicio_consumo": None,
            "fecha_fin_consumo": None,
            "importe_factura": None,
            "cups": None,
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

        # CUPS
        cups_match = re.search(r"(ES[A-Z0-9]{16,24})", raw_text, re.IGNORECASE)
        if cups_match:
            data["cups"] = cups_match.group(1)
            detected_pf["cups"] = True
        else:
            detected_pf["cups"] = False

        # Fechas de consumo: "4 de julio de 2024 a 5 de agosto de 2024"
        meses = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
        rango = re.search(
            rf"(\d{{1,2}}\s+de\s+(?:{meses})\s+de\s+\d{{4}})\s+a\s+(\d{{1,2}}\s+de\s+(?:{meses})\s+de\s+\d{{4}})",
            raw_text,
            re.IGNORECASE,
        )
        if rango:
            data["fecha_inicio_consumo"] = rango.group(1)
            data["fecha_fin_consumo"] = rango.group(2)
            detected_pf["fecha_inicio_consumo"] = True
            detected_pf["fecha_fin_consumo"] = True
        else:
            detected_pf["fecha_inicio_consumo"] = False
            detected_pf["fecha_fin_consumo"] = False

        # Importe factura: etiqueta explicita
        importe_match = re.search(r"IMPORTE\s+FACTURA[:\s]*[\r\n\s]*([\d.,]+)", raw_text, re.IGNORECASE)
        if importe_match:
            data["importe_factura"] = _to_float(importe_match.group(1))
            detected_pf["importe_factura"] = data["importe_factura"] is not None
        else:
            detected_pf["importe_factura"] = False

        # Potencia contratada
        pot_p1 = re.search(r"potencia\s+(?:contratada\s+en\s+)?p1|punta[^0-9]{0,10}([\d.,]+)\s*k?w", raw_text, re.IGNORECASE)
        if pot_p1:
            data["potencia_p1_kw"] = _to_float(pot_p1.group(1))
            detected_pf["potencia_p1_kw"] = data["potencia_p1_kw"] is not None
        else:
            detected_pf["potencia_p1_kw"] = False

        pot_p2 = re.search(r"potencia\s+(?:contratada\s+en\s+)?p2|valle[^0-9]{0,10}([\d.,]+)\s*k?w", raw_text, re.IGNORECASE)
        if pot_p2:
            data["potencia_p2_kw"] = _to_float(pot_p2.group(1))
            detected_pf["potencia_p2_kw"] = data["potencia_p2_kw"] is not None
        else:
            detected_pf["potencia_p2_kw"] = False

        # Consumos por periodo: "Consumo en P1: 17 kWh"
        for p in range(1, 7):
            m = re.search(rf"Consumo\s+en\s+P{p}\s*[:\-]?\s*([\d.,]+)\s*kWh", raw_text, re.IGNORECASE)
            key = f"consumo_p{p}_kwh"
            if m:
                data[key] = _to_float(m.group(1))
                detected_pf[key] = data[key] is not None
            else:
                detected_pf[key] = False

        # Bono social: presencia de la etiqueta
        bono = re.search(r"\bbono\s+social\b", raw_text, re.IGNORECASE)
        data["bono_social"] = True if bono else None
        detected_pf["bono_social"] = bono is not None

        data["parsed_fields"] = detected_pf
        return data

    # Estructurado conservador
    structured = parse_structured_fields(full_text)
    parsed_fields.update(structured.get("parsed_fields", {}))

    # 1. CUPS
    cups_match = re.search(r"(ES[A-Z0-9]{16,24})", full_text, re.IGNORECASE)
    if cups_match:
        result["cups"] = cups_match.group(1)
    elif structured.get("cups"):
        result["cups"] = structured.get("cups")

    detected = {}

    # 2. Consumo
    consumo_match = re.search(r"(\d+[.,]?\d*)\s*kWh", full_text, re.IGNORECASE)
    if consumo_match:
        val_str = consumo_match.group(1).replace(",", ".")
        try:
            result["consumo_kwh"] = float(val_str)
            detected["consumo_kwh"] = True
        except Exception:
            pass
    else:
        detected["consumo_kwh"] = False

    # 3. Importe
    total_match = re.search(r"TOTAL.*?\s+(\d+[.,]?\d*)\s*(?:\u20ac|EUR)", full_text, re.IGNORECASE)
    if total_match:
        val_str = total_match.group(1).replace(",", ".")
        try:
            result["importe"] = float(val_str)
            detected["importe"] = True
        except Exception:
            pass
    if result["importe"] is None:
        matches = re.findall(r"(\d+[.,]?\d*)\s*(?:\u20ac|EUR)", full_text, re.IGNORECASE)
        if matches:
            try:
                vals = [float(m.replace(",", ".")) for m in matches]
                result["importe"] = max(vals)
                detected["importe"] = True
            except Exception:
                pass
    if result["importe"] is None and structured.get("importe_factura") is not None:
        result["importe"] = structured.get("importe_factura")
        detected["importe"] = True
    if "importe" not in detected:
        detected["importe"] = False

    # 4. Fecha
    date_matches = re.findall(r"(\d{4}[/-]\d{2}[/-]\d{2}|\d{2}[/-]\d{2}[/-]\d{4})", full_text)
    if date_matches:
        result["fecha"] = date_matches[0]
        detected["fecha"] = True
    else:
        detected["fecha"] = False
    # Fechas de consumo
    if structured.get("fecha_inicio_consumo"):
        result["fecha_inicio_consumo"] = structured.get("fecha_inicio_consumo")
    if structured.get("fecha_fin_consumo"):
        result["fecha_fin_consumo"] = structured.get("fecha_fin_consumo")

    # --- Nuevos campos (Sprint 3B) ---
    # 5. Titular (tolerando saltos de linea y separadores)
    def _is_valid_name(candidate: str) -> bool:
        if not candidate:
            return False
        cleaned = candidate.strip(" :,-\t\r\n")
        if not cleaned:
            return False
        # Sin numeros, sin keywords y al menos dos palabras
        if re.search(r"\d", cleaned):
            return False
        keywords = [
            "dni",
            "cif",
            "nif",
            "direccion",
            "dirección",
            "telefono",
            "teléfono",
            "email",
            "cups",
            "importe",
            "factura",
            "comercializadora",
            "regulada",
            "grupo",
            "s.a",
            "sl",
            "naturgy",
            "endesa",
            "iberdrola",
            "repsol",
            "energia",
            "energy",
            "gas",
            "power",
        ]
        if any(k.lower() in cleaned.lower() for k in keywords):
            return False
        if len(cleaned.split()) < 2:
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
        if any(k in text for k in ["cups", "dni", "nif", "cif", "factura", "importe", "potencia"]):
            return False
        if len(line.strip()) < 6:
            return False
        # Requiere letras y algun numero (tipico de direcciones)
        has_letter = re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", line)
        has_number = re.search(r"\d", line)
        return bool(has_letter and has_number)

    titular = None
    name_line_index = None

    if is_image:
        # Tratamiento especial para imagenes sin estructura
        raw_lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
        label_keywords = {"titular", "dni", "cif", "nif", "telefono", "teléfono", "email", "direccion", "dirección", "cups"}
        filtered_lines = []
        for ln in raw_lines:
            ln_stripped = ln.strip(" :.-").lower()
            if ln_stripped in label_keywords:
                continue
            filtered_lines.append(ln)

        # Buscar nombre contextual: lineas alrededor de un DNI
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

        # Sin nombre fiable -> None

    # Si no es imagen o necesitamos etiquetas, solo aceptamos etiqueta explicita
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

    # 6. DNI/CIF (patron exacto 8 numeros + letra)
    match_dni = re.search(r"(?:dni|cif|nif)?\s*[:\-]?\s*([0-9]{8}[A-Z])", full_text, re.IGNORECASE)
    if match_dni:
        result["dni"] = re.sub(r"\s+", "", match_dni.group(1)).strip()

    # 7. Direccion de suministro (solo si etiqueta explicita)
    dir_patterns = [
        r"direccion(?:\s+de\s+suministro)?\s*[:\-]?\s*([A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ ,.'´`-]{5,120})",
        r"domicilio\s*[:\-]?\s*([A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ ,.'´`-]{5,120})",
    ]
    for pattern in dir_patterns:
        match_dir = re.search(pattern, full_text, re.IGNORECASE)
        if match_dir:
            result["direccion"] = match_dir.group(1).strip()
            break
    # Fallback direccion: si imagen y tenemos linea de nombre, tomar siguientes 1-2 lineas como direccion si parecen direccion
    if is_image and result["direccion"] is None and name_line_index is not None:
        raw_lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
        for forward in range(1, 3):
            if name_line_index + forward < len(raw_lines):
                candidate_dir = raw_lines[name_line_index + forward]
                if _is_address_candidate(candidate_dir):
                    result["direccion"] = candidate_dir.strip()
                    break

    # 8. Telefono (9 digitos, con o sin separadores)
    match_tel = re.search(
        r"(?:tel(?:efono)?|phone)?[^\d]{0,12}(\b[6789]\d{2}[.\s\-]?\d{3}[.\s\-]?\d{3}\b)",
        full_text,
        re.IGNORECASE,
    )
    if match_tel:
        telefono = re.sub(r"[.\s\-]", "", match_tel.group(1))
        # Excluir numeros de atencion (800/900/901/902/905)
        if not telefono.startswith(("800", "900", "901", "902", "905")):
            result["telefono"] = telefono
            detected["telefono"] = True
        else:
            detected["telefono"] = False
    else:
        detected["telefono"] = False

    # --- Campos energeticos adicionales (solo si aparecen de forma explicita) ---
    def _extract_number(patterns):
        for pat in patterns:
            m = re.search(pat, full_text, re.IGNORECASE)
            if m:
                val = m.group(1).replace(",", ".")
                try:
                    return float(val)
                except Exception:
                    continue
        return None

    # Potencia contratada
    result["potencia_p1_kw"] = _extract_number(
        [r"potencia\s*p1[^0-9]{0,10}([\d.,]+)\s*k?w", r"potencia\s+punta[^0-9]{0,10}([\d.,]+)\s*k?w"]
    )
    result["potencia_p2_kw"] = _extract_number(
        [r"potencia\s*p2[^0-9]{0,10}([\d.,]+)\s*k?w", r"potencia\s+valle[^0-9]{0,10}([\d.,]+)\s*k?w"]
    )
    detected["potencia_p1_kw"] = result["potencia_p1_kw"] is not None
    detected["potencia_p2_kw"] = result["potencia_p2_kw"] is not None

    # Consumos por periodo
    for periodo in ["p1", "p2", "p3", "p4", "p5", "p6"]:
        val = _extract_number(
            [rf"consumo\s*{periodo}[^0-9]{{0,10}}([\d.,]+)\s*kwh", rf"{periodo}\s*consumo[^0-9]{{0,10}}([\d.,]+)\s*kwh"]
        )
        result[f"consumo_{periodo}_kwh"] = val
        detected[f"consumo_{periodo}_kwh"] = val is not None

    # Bono social (solo si se menciona explicitamente)
    bono_match = re.search(r"\bbono\s+social\b", full_text, re.IGNORECASE)
    result["bono_social"] = True if bono_match else None
    detected["bono_social"] = bono_match is not None

    # Servicios vinculados (solo si etiqueta explicita)
    sv_match = re.search(r"\bservicios\s+vinculados\b", full_text, re.IGNORECASE)
    result["servicios_vinculados"] = True if sv_match else None
    detected["servicios_vinculados"] = sv_match is not None

    # Alquiler contador
    result["alquiler_contador"] = _extract_number(
        [r"alquiler\s+contador[^0-9]{0,10}([\d.,]+)", r"contador\s+alquiler[^0-9]{0,10}([\d.,]+)"]
    )
    detected["alquiler_contador"] = result["alquiler_contador"] is not None

    # Impuesto electrico
    result["impuesto_electrico"] = _extract_number(
        [r"impuesto\s+electrico[^0-9]{0,10}([\d.,]+)", r"impuesto\s+el[eé]ctrico[^0-9]{0,10}([\d.,]+)"]
    )
    detected["impuesto_electrico"] = result["impuesto_electrico"] is not None

    # IVA
    result["iva"] = _extract_number([r"\biva\b[^0-9]{0,10}([\d.,]+)"])
    detected["iva"] = result["iva"] is not None

    # Total factura (solo si etiqueta explicita)
    result["total_factura"] = _extract_number(
        [
            r"\btotal\s+factura[^0-9]{0,10}([\d.,]+)",
            r"\bimporte\s+total[^0-9]{0,10}([\d.,]+)",
            r"\btotal\s+importe[^0-9]{0,10}([\d.,]+)",
        ]
    )
    detected["total_factura"] = result["total_factura"] is not None

    # Relleno conservador con campos estructurados
    for field in [
        "potencia_p1_kw",
        "potencia_p2_kw",
        "consumo_p1_kwh",
        "consumo_p2_kwh",
        "consumo_p3_kwh",
        "consumo_p4_kwh",
        "consumo_p5_kwh",
        "consumo_p6_kwh",
    ]:
        if result.get(field) is None and structured.get(field) is not None:
            result[field] = structured.get(field)
            detected[field] = True

    if result.get("bono_social") is None and structured.get("bono_social") is not None:
        result["bono_social"] = structured.get("bono_social")
        detected["bono_social"] = True

    result["parsed_fields"] = parsed_fields
    result["detected_por_ocr"] = detected

    return result


def extract_data_from_pdf(file_bytes: bytes) -> dict:
    # 1. Detectar si es un PDF real usando magic bytes
    is_pdf = file_bytes.startswith(b"%PDF")

    # --- Estrategia A: PDF digital (pypdf) ---
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
            # Si falla pypdf, podriamos intentar Vision, pero Vision Sync no soporta PDF bytes.
            pass

    # --- Estrategia B: Imagen (Google Cloud Vision) ---
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
