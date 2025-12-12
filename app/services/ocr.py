import os
import json
import re
from google.oauth2 import service_account
from google.cloud import vision

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

def extract_data_from_pdf(file_bytes: bytes) -> dict:
    client, auth_log = get_vision_client()
    if not client:
        return {
            "cups": None, "consumo_kwh": None, "importe": None, "fecha": None, 
            "raw_text": f"Error Configuración Credenciales:\n{auth_log}"
        }

    # Google Vision espera una imagen. Si es PDF, lo ideal es usar document_text_detection
    # con soporte para PDF (async), pero para un MVP sincrono rápido, 
    # Vision también acepta imágenes. Si el input es PDF real, Vision API requiere
    # usar async_batch_annotate_files con GCS.
    # 
    # TRUCO MVP: Si el 'file_bytes' que llega es un PDF, Vision API standard NO lo procesa directamente
    # en sync sin subirlo a GCS. Sin embargo, si el usuario sube **Imágenes** (JPG/PNG), funciona directo.
    # 
    # Si asumimos que el usuario puede subir PDF, necesitariamos convertirlo a imagen (pdf2image)
    # pero no tenemos poppler en Render.
    #
    # Por ahora, intentaremos enviarlo como 'content' a ver si Vision lo traga (si es imagen).
    # Si es PDF, fallará si no usamos la API especifica de archivos (que es más compleja).
    #
    # Para cumplir con "Sprint 2" simple, vamos a asumir que el contenido se envia como imagen
    # o usaremos el mime_type correcto si Vision lo soporta en sync (solo soporta imagenes en sync).

    image = vision.Image(content=file_bytes)
    
    try:
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if not texts:
            return {
                "cups": None, "consumo_kwh": None, "importe": None, "fecha": None, "raw_text": ""
            }

        # El primer elemento contiene todo el texto
        full_text = texts[0].description
        
        # --- PARSING ---
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
        # Buscamos "123,45 kWh" o "123.45 kWh"
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

    except Exception as e:
        print(f"Error en Vision API: {e}")
        return {
            "cups": None, "consumo_kwh": None, "importe": None, "fecha": None, 
            "raw_text": f"Error procesando OCR: {str(e)}\n\n--- DEBUG LOG ---\n{auth_log}"
        }
