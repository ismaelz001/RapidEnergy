import requests
import json

API_URL = "https://rapidenergy.onrender.com/webhook/upload_v2"
FACTURA_PATH = "e:/MecaEnergy/temp_facturas/facturas/f1.jpg"

print("=== ANÁLISIS COMPLETO DE EXTRACCIÓN OCR ===\n")

# 1. Subir factura
print("📤 Subiendo factura...")
with open(FACTURA_PATH, 'rb') as f:
    response = requests.post(API_URL, files={"file": ("f1.jpg", f, "image/jpeg")})

if response.status_code != 200:
    print(f"❌ Error al subir: {response.status_code}")
    print(response.text)
    exit(1)

upload_result = response.json()
factura_id = upload_result.get('id')
print(f"✅ Factura subida con ID: {factura_id}\n")

# 2. Obtener OCR Preview (lo que extrajo el OCR)
ocr_preview = upload_result.get('ocr_preview', {})
print("=" * 80)
print("📊 DATOS EXTRAÍDOS POR OCR (ocr_preview):")
print("=" * 80)
for key, value in sorted(ocr_preview.items()):
    print(f"  {key:30} = {value}")

# 3. Obtener datos guardados en BBDD
print("\n" + "=" * 80)
print("💾 DATOS GUARDADOS EN BASE DE DATOS:")
print("=" * 80)

db_response = requests.get(f"https://rapidenergy.onrender.com/webhook/facturas/{factura_id}")
if db_response.status_code == 200:
    db_data = db_response.json()
    
    campos_importantes = [
        'cups', 'atr', 'consumo_kwh', 'total_factura', 'importe',
        'fecha', 'fecha_inicio', 'fecha_fin', 'periodo_dias',
        'potencia_p1_kw', 'potencia_p2_kw',
        'consumo_p1_kwh', 'consumo_p2_kwh', 'consumo_p3_kwh',
        'titular', 'dni', 'direccion', 'telefono',
        'bono_social', 'alquiler_contador', 'iva', 'impuesto_electrico',
        'numero_factura', 'estado_factura'
    ]
    
    for campo in campos_importantes:
        valor = db_data.get(campo)
        print(f"  {campo:30} = {valor}")
else:
    print(f"❌ Error al obtener BBDD: {db_response.status_code}")

# 4. Comparar diferencias críticas
print("\n" + "=" * 80)
print("🔍 COMPARACIÓN OCR vs BBDD (Campos Críticos):")
print("=" * 80)

campos_criticos = ['cups', 'total_factura', 'consumo_p1_kwh', 'consumo_p2_kwh', 'consumo_p3_kwh']
for campo in campos_criticos:
    ocr_val = ocr_preview.get(campo)
    db_val = db_data.get(campo) if db_response.status_code == 200 else None
    
    match = "✅" if ocr_val == db_val else "❌"
    print(f"{match} {campo:20} | OCR: {ocr_val:20} | BBDD: {db_val}")

print("\n" + "=" * 80)
print("📋 ANÁLISIS:")
print("=" * 80)
print("Si hay diferencias (❌), indica que el flujo está modificando/perdiendo datos.")
print("Si todo coincide (✅), el problema está en el OCR, no en el flujo.")
