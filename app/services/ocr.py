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
        "titular": None,
        "dni": None,
        "direccion": None,
        "telefono": None,
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


def parse_invoice_text(full_text: str) -> dict:
    """Parsea texto de factura proveniente de OCR/PDF para obtener campos clave."""
    result = _empty_result(full_text)

    # 1. CUPS
    cups_match = re.search(r"(ES[A-Z0-9]{16,24})", full_text, re.IGNORECASE)
    if cups_match:
        result["cups"] = cups_match.group(1)

    # 2. Consumo
    consumo_match = re.search(r"(\d+[.,]?\d*)\s*kWh", full_text, re.IGNORECASE)
    if consumo_match:
        val_str = consumo_match.group(1).replace(",", ".")
        try:
            result["consumo_kwh"] = float(val_str)
        except Exception:
            pass

    # 3. Importe
    total_match = re.search(r"TOTAL.*?\s+(\d+[.,]?\d*)\s*(?:\u20ac|EUR)", full_text, re.IGNORECASE)
    if total_match:
        val_str = total_match.group(1).replace(",", ".")
        try:
            result["importe"] = float(val_str)
        except Exception:
            pass
    if result["importe"] is None:
        matches = re.findall(r"(\d+[.,]?\d*)\s*(?:\u20ac|EUR)", full_text, re.IGNORECASE)
        if matches:
            try:
                vals = [float(m.replace(",", ".")) for m in matches]
                result["importe"] = max(vals)
            except Exception:
                pass

    # 4. Fecha
    date_matches = re.findall(r"(\d{4}[/-]\d{2}[/-]\d{2}|\d{2}[/-]\d{2}[/-]\d{4})", full_text)
    if date_matches:
        result["fecha"] = date_matches[0]

    # --- Nuevos campos (Sprint 3B) ---
    # 5. Titular (tolerando saltos de linea y separadores)
    def _is_valid_name(candidate: str) -> bool:
        if not candidate:
            return False
        cleaned = candidate.strip()
        if not cleaned:
            return False
        # descartar si contiene numeros o keywords de otros campos
        if re.search(r"\d", cleaned):
            return False
        keywords = ["dni", "cif", "nif", "direccion", "dirección", "telefono", "teléfono", "email"]
        if any(k.lower() in cleaned.lower() for k in keywords):
            return False
        # requerir al menos dos palabras
        if len(cleaned.split()) < 2:
            return False
        return True

    def _clean_name(candidate: str) -> str:
        if not candidate:
            return None
        # eliminar etiquetas potenciales y caracteres de puntuacion extremos
        candidate = re.sub(r"(?:^[:\-|\s]+|[:\-|\s]+$)", "", candidate)
        candidate = candidate.strip(":- \t\r\n")
        return candidate.strip()

    titular = None

    # Primero, intentar capturar linea del titular y la siguiente
    titular_block_match = re.search(
        r"(titular|nombre del titular)\s*[:\-]?\s*(.*)", full_text, re.IGNORECASE
    )
    if titular_block_match:
        # Resto de linea tras la etiqueta
        linea = titular_block_match.group(2).strip()
        if not linea:
            # si la misma linea no tiene contenido, tomar siguiente linea completa
            lines = full_text.splitlines()
            start_idx = None
            for idx, line in enumerate(lines):
                if re.search(r"(titular|nombre del titular)", line, re.IGNORECASE):
                    start_idx = idx
                    break
            if start_idx is not None and start_idx + 1 < len(lines):
                linea = lines[start_idx + 1].strip()
        linea = _clean_name(linea)
        if _is_valid_name(linea):
            titular = linea

    # Fallback: patrones genericos sin depender de saltos exactos
    if not titular:
        titular_patterns = [
            r"(?:titular|nombre del titular)\s*[:\-]?\s*([^\n\r]{3,80})",
            r"(?:cliente|nombre)\s*[:\-]?\s*([^\n\r]{3,80})",
        ]
        for pattern in titular_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                candidate = _clean_name(match.group(1))
                if _is_valid_name(candidate):
                    titular = candidate
                    break

    result["titular"] = titular

    # 6. DNI/CIF (permitiendo guiones o espacios)
    match_dni = re.search(r"(?:dni|cif|nif)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\s\-]{6,15})", full_text, re.IGNORECASE)
    if match_dni:
        result["dni"] = re.sub(r"\s+", "", match_dni.group(1)).strip()

    # 7. Direccion de suministro
    dir_patterns = [
        r"direccion(?:\s+de\s+suministro)?\s*[:\-]?\s*([^\n\r]{5,120})",
        r"domicilio\s*[:\-]?\s*([^\n\r]{5,120})",
    ]
    for pattern in dir_patterns:
        match_dir = re.search(pattern, full_text, re.IGNORECASE)
        if match_dir:
            result["direccion"] = match_dir.group(1).strip()
            break

    # 8. Telefono (9 digitos, con o sin separadores)
    match_tel = re.search(
        r"(?:tel(?:efono)?|phone)?[^\d]{0,12}(\b[6789]\d{2}[.\s\-]?\d{3}[.\s\-]?\d{3}\b)",
        full_text,
        re.IGNORECASE,
    )
    if match_tel:
        result["telefono"] = re.sub(r"[.\s\-]", "", match_tel.group(1))

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
        return parse_invoice_text(full_text)

    except Exception as e:
        print(f"Error en Vision API: {e}")
        return _empty_result(f"Error procesando OCR: {str(e)}\n\n--- DEBUG LOG ---\n{auth_log}")
