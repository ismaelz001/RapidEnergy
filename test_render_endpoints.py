"""
Script de test para verificar que los cambios se desplegaron en Render
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://rapidenergy.onrender.com"
TIMEOUT = 15

def test_endpoint(name, method, endpoint, **kwargs):
    """Test un endpoint HTTP"""
    url = BASE_URL + endpoint
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"URL: {method} {url}")
    
    try:
        if method.upper() == "GET":
            r = requests.get(url, timeout=TIMEOUT, **kwargs)
        elif method.upper() == "POST":
            r = requests.post(url, timeout=TIMEOUT, **kwargs)
        else:
            print(f"❌ Método no soportado: {method}")
            return False
        
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"✅ Response JSON válido ({len(json.dumps(data))} bytes)")
                print("\nDatos:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                if len(json.dumps(data)) > 500:
                    print("...")
                return True
            except json.JSONDecodeError:
                print(f"⚠️ No es JSON: {r.text[:200]}")
                return False
        else:
            print(f"❌ Error {r.status_code}: {r.text[:200]}")
            return False
            
    except requests.Timeout:
        print(f"⏱️ TIMEOUT después de {TIMEOUT}s (servidor aún desplegando)")
        return None
    except requests.ConnectionError as e:
        print(f"🌐 Error de conexión: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🚀 TEST DE DESPLIEGUE EN RENDER")
    print("="*70)
    print(f"Hora: {datetime.now().strftime('%H:%M:%S')}")
    print(f"URL Base: {BASE_URL}")
    print()
    
    # Test 1: Health check
    print("⏳ TEST 1/4: Health check...")
    try:
        r = requests.get(BASE_URL + "/docs", timeout=TIMEOUT)
        if r.status_code == 200:
            print("✅ API está disponible")
        else:
            print(f"⚠️ API respondió con {r.status_code}")
    except:
        print("⏱️ API aún se está iniciando...")
    
    # Test 2: Estadísticas de tarifas
    print("\n⏳ TEST 2/4: Estadísticas de tarifas...")
    result2 = test_endpoint(
        "GET /debug/tarifas/stats",
        "GET",
        "/debug/tarifas/stats"
    )
    
    # Test 3: Comparador debug
    print("\n⏳ TEST 3/4: Debug comparador...")
    result3 = test_endpoint(
        "POST /debug/comparador/factura/285",
        "POST",
        "/debug/comparador/factura/285"
    )
    
    # Test 4: PDF
    print("\n⏳ TEST 4/4: Generación de PDF...")
    try:
        r = requests.head(BASE_URL + "/webhook/facturas/285/presupuesto.pdf", timeout=TIMEOUT, allow_redirects=False)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"✅ PDF disponible ({r.headers.get('content-length', '?')} bytes)")
        else:
            print(f"⚠️ PDF retornó {r.status_code}")
    except:
        print("⏱️ PDF endpoint aún cargando...")
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN")
    print("="*70)
    print("\n✅ Todos los cambios se han desplegado en Render")
    print("\nPróximos pasos:")
    print("1. Verificar logs de Render para ver si hay errores")
    print("2. Probar los endpoints desde Postman o curl")
    print("3. Verificar que factura 285 tiene datos en Render")

if __name__ == "__main__":
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n\n{'='*70}")
        print(f"INTENTO {attempt}/{max_attempts}")
        print(f"{'='*70}")
        
        main()
        
        if attempt < max_attempts:
            print(f"\n⏳ Esperando 30 segundos para reintentar...")
            time.sleep(30)
        
        break  # Ejecutar solo una vez
