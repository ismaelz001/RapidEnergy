"""
Test FRESCO: Subir factura nueva para validar fix en producción
"""
import requests
import time
import json

BASE_URL = "https://rapidenergy.onrender.com"
PDF_PATH = "temp_facturas/Factura_Modified.pdf"

print("🚀 Subiendo NUEVA factura para validar fix...")
print("=" * 80)

with open(PDF_PATH, 'rb') as f:
    files = {'file': ('test_fix_fresh.pdf', f, 'application/pdf')}
    
    print(f"⬆️  POST {BASE_URL}/webhook/upload...")
    response = requests.post(
        f"{BASE_URL}/webhook/upload",
        files=files,
        timeout=90
    )
    
    if response.status_code == 409:
        print(f"❌ Duplicado detectado (hash match) - Render aún no tiene el fix o PDF ya existe")
        print(f"   Detalles: {response.json()}")
        exit(1)
    
    if response.status_code != 200:
        print(f"❌ Error HTTP {response.status_code}")
        print(response.text)
        exit(1)
    
    data = response.json()
    factura_id = data.get('id')
    print(f"✅ Factura subida - ID: {factura_id}")
    
    # Esperar procesamiento OCR
    print(f"\n⏳ Esperando 5 segundos para procesamiento OCR...")
    time.sleep(5)
    
    # Consultar datos
    print(f"\n📥 GET /webhook/facturas/{factura_id}...")
    get_response = requests.get(f"{BASE_URL}/webhook/facturas/{factura_id}")
    
    if get_response.status_code != 200:
        print(f"❌ Error obteniendo factura: {get_response.status_code}")
        exit(1)
    
    factura_data = get_response.json()
    
    # Extraer titular
    titular = factura_data.get('titular')
    if not titular and factura_data.get('cliente'):
        cliente_obj = factura_data.get('cliente')
        if isinstance(cliente_obj, dict):
            titular = cliente_obj.get('nombre')
    
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO FIX EXTRACCIÓN NOMBRE")
    print(f"{'='*80}")
    print(f"\n👤 Titular extraído: {titular}")
    print(f"🔌 CUPS extraído: {factura_data.get('cups')}")
    print(f"📋 ATR extraído: {factura_data.get('atr')}")
    
    # Validación esperada
    print(f"\n{'─'*80}")
    print(f"✅ VALIDACIÓN:")
    print(f"{'─'*80}")
    
    expected_titular = "JOSE ANTONIO RODRIGUEZ UROZ"  # Este es el titular REAL del PDF
    if titular == expected_titular:
        print(f"✅ Titular correcto: '{titular}'")
        print(f"✅ FIX FUNCIONANDO - Extrae correctamente el nombre del PDF")
    else:
        print(f"⚠️  Titular extraído: '{titular}'")
        print(f"⚠️  Esperado: '{expected_titular}'")
        print(f"❌ Algo falló en la extracción")
    
    # Ver raw_data para debug
    if factura_data.get('raw_data'):
        try:
            raw = json.loads(factura_data['raw_data']) if isinstance(factura_data['raw_data'], str) else factura_data['raw_data']
            extraction = raw.get('extraction_summary', {})
            print(f"\n🔍 DEBUG INFO:")
            print(f"   • Motor: {extraction}")
        except:
            pass

print(f"\n{'='*80}\n")
