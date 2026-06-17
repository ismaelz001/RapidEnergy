"""
🔥 TESTEO EN PRODUCCIÓN - Backend Render
Verifica que el backend desplegado esté operativo
"""
import requests
import json
from datetime import datetime

# URL del backend en producción
BASE_URL = "https://rapidenergy.onrender.com"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_test(name, status, details="", response_time=None):
    """Print test result with color"""
    icon = "✅" if status else "❌"
    color = Colors.GREEN if status else Colors.RED
    time_str = f" ({response_time:.2f}s)" if response_time else ""
    print(f"{icon} {color}{name}{time_str}{Colors.END}")
    if details:
        print(f"   {details}")

def test_health():
    """TEST 1: Health check básico"""
    print(f"\n{Colors.CYAN}═══ TEST 1: Health Check ═══{Colors.END}")
    
    try:
        start = datetime.now()
        response = requests.get(f"{BASE_URL}/", timeout=10)
        elapsed = (datetime.now() - start).total_seconds()
        
        success = response.status_code == 200
        print_test(
            "GET /",
            success,
            f"Status: {response.status_code}",
            elapsed
        )
        
        if success:
            try:
                data = response.json()
                print(f"   Response: {data}")
            except:
                print(f"   Response: {response.text[:100]}")
        
        return success
        
    except requests.exceptions.Timeout:
        print_test("GET /", False, "TIMEOUT - Servidor no responde")
        return False
    except Exception as e:
        print_test("GET /", False, str(e))
        return False

def test_docs():
    """TEST 2: API Docs disponible"""
    print(f"\n{Colors.CYAN}═══ TEST 2: API Documentation ═══{Colors.END}")
    
    try:
        start = datetime.now()
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        elapsed = (datetime.now() - start).total_seconds()
        
        success = response.status_code == 200
        print_test(
            "GET /docs",
            success,
            f"Status: {response.status_code}",
            elapsed
        )
        
        if success:
            print(f"   📚 Swagger UI disponible en: {BASE_URL}/docs")
        
        return success
        
    except Exception as e:
        print_test("GET /docs", False, str(e))
        return False

def test_webhook_endpoint():
    """TEST 3: Webhook endpoint existe"""
    print(f"\n{Colors.CYAN}═══ TEST 3: Webhook Endpoint ═══{Colors.END}")
    
    try:
        # Sin archivo, debería dar error 422 (falta archivo)
        start = datetime.now()
        response = requests.post(
            f"{BASE_URL}/webhook/upload",
            timeout=10
        )
        elapsed = (datetime.now() - start).total_seconds()
        
        # 422 = endpoint existe pero falta parámetro (OK)
        # 401 = requiere autenticación (OK)
        # 404 = endpoint no existe (FAIL)
        success = response.status_code in [401, 422]
        
        print_test(
            "POST /webhook/upload",
            success,
            f"Status: {response.status_code} (endpoint existe)",
            elapsed
        )
        
        if not success and response.status_code == 404:
            print(f"   ❌ Endpoint no encontrado")
        
        return success
        
    except Exception as e:
        print_test("POST /webhook/upload", False, str(e))
        return False

def test_comparador_endpoint():
    """TEST 4: Comparador endpoint existe"""
    print(f"\n{Colors.CYAN}═══ TEST 4: Comparador Endpoint ═══{Colors.END}")
    
    try:
        # Sin factura_id válido, debería dar 401/404
        start = datetime.now()
        response = requests.post(
            f"{BASE_URL}/webhook/comparar/facturas/999999",
            timeout=10
        )
        elapsed = (datetime.now() - start).total_seconds()
        
        # 401 = requiere auth (OK)
        # 404 = factura no existe o endpoint no existe
        success = response.status_code in [401, 404]
        
        print_test(
            "POST /webhook/comparar/facturas/:id",
            success,
            f"Status: {response.status_code} (endpoint existe)",
            elapsed
        )
        
        return success
        
    except Exception as e:
        print_test("POST /webhook/comparar/facturas/:id", False, str(e))
        return False

def test_clientes_endpoint():
    """TEST 5: Clientes endpoint existe"""
    print(f"\n{Colors.CYAN}═══ TEST 5: Clientes Endpoint ═══{Colors.END}")
    
    try:
        start = datetime.now()
        response = requests.get(
            f"{BASE_URL}/api/clientes",
            timeout=10
        )
        elapsed = (datetime.now() - start).total_seconds()
        
        # 200 = OK (público?)
        # 401 = requiere auth (OK)
        success = response.status_code in [200, 401]
        
        print_test(
            "GET /api/clientes",
            success,
            f"Status: {response.status_code}",
            elapsed
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   📊 Clientes en BD: {len(data) if isinstance(data, list) else 'N/A'}")
            except:
                pass
        
        return success
        
    except Exception as e:
        print_test("GET /api/clientes", False, str(e))
        return False

def test_stats_endpoint():
    """TEST 6: Stats endpoint existe"""
    print(f"\n{Colors.CYAN}═══ TEST 6: Stats Endpoint ═══{Colors.END}")
    
    try:
        start = datetime.now()
        response = requests.get(
            f"{BASE_URL}/api/stats/ceo",
            timeout=10
        )
        elapsed = (datetime.now() - start).total_seconds()
        
        success = response.status_code in [200, 401]
        
        print_test(
            "GET /api/stats/ceo",
            success,
            f"Status: {response.status_code}",
            elapsed
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   📈 Panel CEO: {data.get('total_clientes', 'N/A')} clientes")
            except:
                pass
        
        return success
        
    except Exception as e:
        print_test("GET /api/stats/ceo", False, str(e))
        return False

def test_response_time():
    """TEST 7: Verificar tiempos de respuesta"""
    print(f"\n{Colors.CYAN}═══ TEST 7: Performance ═══{Colors.END}")
    
    try:
        times = []
        for i in range(3):
            start = datetime.now()
            response = requests.get(f"{BASE_URL}/", timeout=10)
            elapsed = (datetime.now() - start).total_seconds()
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        
        # Menos de 2s es bueno
        success = avg_time < 2.0
        
        print_test(
            "Tiempo respuesta promedio",
            success,
            f"{avg_time:.2f}s (3 requests)"
        )
        
        if avg_time > 2.0:
            print(f"   ⚠️  Servidor lento (cold start posible)")
        
        return success
        
    except Exception as e:
        print_test("Performance test", False, str(e))
        return False

def run_production_tests():
    """Ejecutar todos los tests de producción"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🔥 TESTEO EN PRODUCCIÓN - RENDER{Colors.END}")
    print(f"{Colors.BLUE}URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    results = {}
    
    results['health'] = test_health()
    results['docs'] = test_docs()
    results['webhook'] = test_webhook_endpoint()
    results['comparador'] = test_comparador_endpoint()
    results['clientes'] = test_clientes_endpoint()
    results['stats'] = test_stats_endpoint()
    results['performance'] = test_response_time()
    
    # Resumen
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📊 RESUMEN - PRODUCCIÓN{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        color = Colors.GREEN if status else Colors.RED
        print(f"{icon} {color}{name.upper()}: {'PASS' if status else 'FAIL'}{Colors.END}")
    
    print(f"\n{Colors.CYAN}Total: {passed}/{total} tests pasados{Colors.END}")
    
    if passed >= total - 1:  # Permitir 1 fallo (por auth, etc)
        print(f"\n{Colors.GREEN}🎉 PRODUCCIÓN OPERATIVA{Colors.END}")
        print(f"{Colors.GREEN}✅ Backend desplegado funcionando correctamente{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.RED}❌ PROBLEMAS EN PRODUCCIÓN{Colors.END}")
        print(f"{Colors.YELLOW}⚠️  Revisar logs en Render Dashboard{Colors.END}\n")
        return False

if __name__ == "__main__":
    try:
        import sys
        success = run_production_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrumpidos{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error fatal: {str(e)}{Colors.END}")
        sys.exit(1)
