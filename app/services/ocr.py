import os
import json
import re
import io
from google.oauth2 import service_account
from google.cloud import vision
import pypdf

def get_vision_client():
    logs = ["DEBUG AUTH LOG:"]
    
    # 1. Prioridad: Archivo Secret de Render (Iterar todo el directorio por si acaso)
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
                    # logs.append(f"Trying to load: {fname}")
                    creds = service_account.Credentials.from_service_account_file(fpath)
                    logs.append(f"Success loading {fname}. Email: {creds.service_account_email}")
                    return vision.ImageAnnotatorClient(credentials=creds), "\n".join(logs)
                except Exception as e:
                    logs.append(f"Failed loading {fname}: {str(e)}")
        except Exception as e:
            logs.append(f"Error scanning secrets dir: {str(e)}")
    else:
        logs.append("Secrets dir /etc/secrets not found (local?)")

    # 2. Fallback: Variable de entorno
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        logs.append("Found GOOGLE_CREDENTIALS env var.")
        try:
            info = json.loads(creds_json)
            if 'private_key' in info:
                info['private_key'] = info['private_key'].replace('\\n', '\n')
            
            creds = service_account.Credentials.from_service_account_info(info)
            logs.append(f"Loaded from ENV. Email: {info.get('client_email')}")
            return vision.ImageAnnotatorClient(credentials=creds), "\n".join(logs)
        except Exception as e:
            logs.append(f"Error parsing ENV credentials: {str(e)}")
            return None, "\n".join(logs)

    logs.append("No credentials found in File or Env.")
    return None, "\n".join(logs)

def parse_invoice_text(full_text: str) -> dict:
    """Función auxiliar para parsear texto de factura (común para OCR y PDF)"""
    cups = None
    consumo = None
    importe = None
    fecha = None

    # 1. CUPS: ES seguido de 16-18 digitos/letras
    cups_match = re.search(r'(ES\\d{16,18}[A-Z0-9]{0,2})', full_text, re.IGNORECASE)
    if cups_match:
        cups = cups_match.group(1)

    # 2. Consumo: numero seguido de kWh
    # Normalizamos comas a puntos para float
    consumo_match = re.search(r'(\\d+[.,]?\\d*)\\s*kWh', full_text, re.IGNORECASE)
    if consumo_match:
        val_str = consumo_match.group(1).replace(',', '.')
        try:
            consumo = float(val_str)
        except:
            pass

    # 3. Importe: numero seguido de € o EUR
    importe_match = re.search(r'(\\d+[.,]?\\d*)\\s*(?:€|EUR)', full_text, re.IGNORECASE)
    if importe_match:
        val_str = importe_match.group(1).replace(',', '.')
        try:
            importe = float(val_str)
        except:
            pass
    
    # 4. Fecha: dd/mm/yyyy o dd-mm-yyyy
    fecha_match = re.search(r'(\\d{2}[/-]\\d{2}[/-]\\d{4})', full_text)
    if fecha_match:
        fecha = fecha_match.group(1)

    return {
        "cups": cups,
        "consumo_kwh": consumo,
        "importe": importe,
        "fecha": fecha,
        "raw_text": full_text
    }

def extract_data_from_pdf(file_bytes: bytes) -> dict:
    # 1. Detectar si es un PDF real usando magic bytes
    is_pdf = file_bytes.startswith(b'%PDF')
    
    # --- ESTRATEGIA A: PDF Digital (pypdf) ---
    if is_pdf:
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # Si hemos extraído texto sustancial, lo procesamos
            if len(full_text.strip()) > 50:
                print("PDF Digital detectado. Usando pypdf.")
                return parse_invoice_text(full_text)
            else:
                # Es un PDF escaneado (imágenes dentro)
                msg = "PDF Escaneado detectado. Por favor, sube una imagen (JPG/PNG) o usa un PDF original."
                return {
                    "cups": None, "consumo_kwh": None, "importe": None, "fecha": None, 
                    "raw_text": msg
                }
        except Exception as e:
            print(f"Error leyendo PDF con pypdf: {e}")
            # Si falla pypdf, podríamos intentar Vision, pero Vision Sync NO soporta PDF bytes.
            pass

    # --- ESTRATEGIA B: Imagen (Google Cloud Vision) ---
    # Si no es PDF, o si queremos intentar enviarlo como imagen a Vision 
    # (Vision detecta el tipo de archivo, si es PDF fallará/dará vacío).
    
    client, auth_log = get_vision_client()
    if not client:
        return {
            "cups": None, "consumo_kwh": None, "importe": None, "fecha": None, 
            "raw_text": f"Error Configuración Credenciales:\n{auth_log}"
        }

    image = vision.Image(content=file_bytes)
    
    try:
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if not texts:
            return {
                "cups": None, "consumo_kwh": None, "importe": None, "fecha": None, 
                "raw_text": "El OCR no detectó texto. Si es un PDF, asegúrate de subirlo como imagen (JPG/PNG)."
            }

        full_text = texts[0].description
        return parse_invoice_text(full_text)

    except Exception as e:
        print(f"Error en Vision API: {e}")
        return {
            "cups": None, "consumo_kwh": None, "importe": None, "fecha": None, 
            "raw_text": f"Error procesando OCR: {str(e)}\n\n--- DEBUG LOG ---\n{auth_log}"
        }
