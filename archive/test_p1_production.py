"""
P1 PRODUCCIÓN - Script de Testing
"""
import requests
import json
import sqlite3

BASE_URL = "http://127.0.0.1:8000"

def crear_factura_test(con_periodo=True):
    """Crea una factura de prueba en SQLite"""
    conn = sqlite3.connect('local.db')
    c = conn.cursor()
    
    # Insertar factura de prueba
    periodo = 60 if con_periodo else None
    c.execute("""
        INSERT INTO facturas (
            filename, cups, atr, 
            consumo_p1_kwh, consumo_p2_kwh, consumo_p3_kwh,
            potencia_p1_kw, potencia_p2_kw,
            total_factura, estado_factura, periodo_dias
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'test_p1.pdf', 
        'ES0031408491710001TN0F', 
        '2.0TD',
        100.5, 50.2, 30.1,  # consumos
        4.6, 4.6,            # potencias
        156.80,              # total
        'validado',
        periodo
    ))
    conn.commit()
    factura_id = c.lastrowid
    conn.close()
    
    print(f"✅ Factura {factura_id} creada (periodo_dias={periodo})")
    return factura_id

def test_comparar_sin_periodo():
    """TEST 1: Factura SIN periodo → debe devolver HTTP 422"""
    print("\n" + "="*60)
    print("TEST 1: Comparar factura SIN periodo_dias")
    print("="*60)
    
    factura_id = crear_factura_test(con_periodo=False)
    
    url = f"{BASE_URL}/webhook/comparar/facturas/{factura_id}"
    print(f"POST {url}")
    
    try:
        r = requests.post(url)
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 422:
            data = r.json()
            print(f"✅ ÉXITO: HTTP 422 devuelto")
            print(f"Code: {data.get('detail', {}).get('code')}")
            print(f"Message: {data.get('detail', {}).get('message')}")
            return True
        else:
            print(f"❌ FALLO: Esperaba 422, recibió {r.status_code}")
            print(f"Response: {r.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_comparar_con_periodo():
    """TEST 2: Factura CON periodo → debe devolver HTTP 200 con comparativa_id"""
    print("\n" + "="*60)
    print("TEST 2: Comparar factura CON periodo_dias=60")
    print("="*60)
    
    factura_id = crear_factura_test(con_periodo=True)
    
    url = f"{BASE_URL}/webhook/comparar/facturas/{factura_id}"
    print(f"POST {url}")
    
    try:
        r = requests.post(url)
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"✅ ÉXITO: HTTP 200 devuelto")
            print(f"\nRespuesta:")
            print(f"  factura_id: {data.get('factura_id')}")
            print(f"  comparativa_id: {data.get('comparativa_id')}")
            print(f"  periodo_dias: {data.get('periodo_dias')}")
            print(f"  current_total: {data.get('current_total')}")
            print(f"  offers count: {len(data.get('offers', []))}")
            
            if data.get('offers'):
                offer = data['offers'][0]
                print(f"\nPrimera oferta:")
                print(f"  provider: {offer.get('provider')}")
                print(f"  estimated_total_periodo: {offer.get('estimated_total_periodo')}")
                print(f"  ahorro_periodo: {offer.get('ahorro_periodo')}")
                print(f"  ahorro_mensual_equiv: {offer.get('ahorro_mensual_equiv')}")
                print(f"  ahorro_anual_equiv: {offer.get('ahorro_anual_equiv')}")
            
            return True
        else:
            print(f"❌ FALLO: Esperaba 200, recibió {r.status_code}")
            print(f"Response: {r.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_comparativa_en_bd():
    """TEST 3: Verificar que comparativa se guardó en BD"""
    print("\n" + "="*60)
    print("TEST 3: Verificar comparativa en BD")
    print("="*60)
    
    conn = sqlite3.connect('local.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT id, factura_id, periodo_dias, current_total, status, created_at
        FROM comparativas 
        ORDER BY id DESC 
        LIMIT 1
    """)
    
    row = c.fetchone()
    conn.close()
    
    if row:
        print(f"✅ Comparativa encontrada:")
        print(f"  id: {row[0]}")
        print(f"  factura_id: {row[1]}")
        print(f"  periodo_dias: {row[2]}")
        print(f"  current_total: {row[3]}")
        print(f"  status: {row[4]}")
        print(f"  created_at: {row[5]}")
        return True
    else:
        print(f"❌ No se encontró ninguna comparativa en la BD")
        return False

if __name__ == "__main__":
    print("\n🚀 P1 PRODUCCIÓN - TESTS AUTOMÁTICOS")
    print("="*60)
    
    resultados = []
    
    # Test 1: Sin periodo
    resultados.append(("Sin periodo → HTTP 422", test_comparar_sin_periodo()))
    
    # Test 2: Con periodo
    resultados.append(("Con periodo → HTTP 200", test_comparar_con_periodo()))
    
    # Test 3: BD
    resultados.append(("Comparativa en BD", test_comparativa_en_bd()))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE TESTS")
    print("="*60)
    
    for nombre, ok in resultados:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status}  {nombre}")
    
    total = len(resultados)
    passed = sum(1 for _, ok in resultados if ok)
    
    print(f"\nTotal: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON! P1 PRODUCCIÓN OK")
    else:
        print(f"\n⚠️ {total - passed} tests fallaron")
