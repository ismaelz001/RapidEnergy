"""
Test automatizado de fixes OCR via API
- Fix nombre cliente (Factura Iberdrola - Maria Constantino)
- Fix fusión pypdf+Vision (protección CUPS)
"""
import requests
import os
import json
import time
from datetime import datetime

BASE_URL = "https://rapidenergy.onrender.com"
UPLOAD_ENDPOINT = f"{BASE_URL}/webhook/upload"
GET_FACTURA_ENDPOINT = f"{BASE_URL}/webhook/facturas"
HEADERS = {"Content-Type": "application/json"}

# Facturas a testear
FACTURAS_TEST = [
    {
        "path": "temp_facturas/Factura Iberdrola.pdf",
        "nombre": "Factura Iberdrola (Maria Constantino)",
        "expected": {
            "titular_contiene": "CONSTANTINO",  # Debe contener parte del nombre
            "cups_format": "ES",  # Debe empezar con ES
            "atr_valido": True,
        }
    },
    {
        "path": "temp_facturas/factura Naturgy.pdf",
        "nombre": "Factura Naturgy",
        "expected": {
            "cups_format": "ES",
            "atr_valido": True,
        }
    }
]

def test_upload_factura(factura_info):
    """Sube factura y valida respuesta OCR"""
    print(f"\n{'='*80}")
    print(f"📄 Testing: {factura_info['nombre']}")
    print(f"{'='*80}")
    
    if not os.path.exists(factura_info['path']):
        print(f"❌ Archivo no encontrado: {factura_info['path']}")
        return None
    
    # Subir factura
    try:
        with open(factura_info['path'], 'rb') as f:
            files = {'file': (os.path.basename(factura_info['path']), f, 'application/pdf')}
            
            print(f"⬆️  Subiendo a {UPLOAD_ENDPOINT}...")
            response = requests.post(
                UPLOAD_ENDPOINT,
                files=files,
                timeout=60  # OCR puede tomar tiempo
            )
            
            # Manejar duplicados (409)
            if response.status_code == 409:
                print(f"ℹ️  Factura duplicada - Consultando existente...")
                try:
                    duplicate_data = response.json()
                    factura_id = duplicate_data.get('detail', {}).get('id')
                    if factura_id:
                        print(f"✅ ID factura existente: {factura_id}")
                    else:
                        print(f"❌ No se pudo extraer ID de duplicado")
                        return None
                except:
                    print(f"❌ Error parseando respuesta de duplicado")
                    return None
            elif response.status_code != 200:
                print(f"❌ Error HTTP {response.status_code}: {response.text[:200]}")
                return None
            else:
                data = response.json()
                factura_id = data.get('id')
                
                if not factura_id:
                    print(f"❌ No se recibió ID de factura")
                    return None
                
                print(f"✅ Factura subida - ID: {factura_id}")
            
            # Esperar a que OCR procese
            time.sleep(2)
            
            # Obtener datos extraídos
            print(f"📥 Obteniendo datos de factura...")
            get_response = requests.get(f"{GET_FACTURA_ENDPOINT}/{factura_id}")
            
            if get_response.status_code != 200:
                print(f"⚠️  No se pudo obtener datos de factura (puede estar procesando)")
                return None
            
            factura_data = get_response.json()
            
            # Validaciones
            print(f"\n📊 RESULTADOS EXTRACCIÓN:")
            print(f"{'─'*80}")
            
            # Campo: Titular/Cliente
            titular = factura_data.get('titular')
            if not titular and factura_data.get('cliente'):
                # Si viene el objeto cliente completo
                cliente_obj = factura_data.get('cliente')
                if isinstance(cliente_obj, dict):
                    titular = cliente_obj.get('nombre')
                else:
                    titular = None
            
            print(f"👤 Cliente/Titular: {titular or '❌ NO EXTRAÍDO'}")
            
            if factura_info['expected'].get('titular_contiene'):
                if titular and factura_info['expected']['titular_contiene'].lower() in titular.lower():
                    print(f"   ✅ Contiene '{factura_info['expected']['titular_contiene']}'")
                else:
                    print(f"   ⚠️  NO contiene '{factura_info['expected']['titular_contiene']}'")
            
            # Campo: CUPS
            cups = factura_data.get('cups')
            print(f"🔌 CUPS: {cups or '❌ NO EXTRAÍDO'}")
            
            if factura_info['expected'].get('cups_format'):
                if cups and cups.startswith(factura_info['expected']['cups_format']):
                    print(f"   ✅ Formato correcto (inicia con {factura_info['expected']['cups_format']})")
                else:
                    print(f"   ⚠️  Formato incorrecto o faltante")
            
            # Campo: ATR
            atr = factura_data.get('atr')
            print(f"📋 ATR: {atr or '❌ NO EXTRAÍDO'}")
            
            if factura_info['expected'].get('atr_valido'):
                if atr and ('TD' in str(atr).upper() or '.' in str(atr)):
                    print(f"   ✅ Formato válido")
                else:
                    print(f"   ⚠️  Formato incorrecto o faltante")
            
            # Otros campos críticos
            print(f"\n📈 CAMPOS ADICIONALES:")
            print(f"   • Consumo: {factura_data.get('consumo_kwh')} kWh")
            print(f"   • Días facturados: {factura_data.get('dias_facturados')}")
            print(f"   • Total factura: {factura_data.get('total_factura')} €")
            print(f"   • Potencia P1: {factura_data.get('potencia_p1_kw')} kW")
            print(f"   • Potencia P2: {factura_data.get('potencia_p2_kw')} kW")
            
            # Motor OCR usado
            raw_data = factura_data.get('raw_data')
            if raw_data:
                try:
                    raw_dict = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    extraction_summary = raw_dict.get('extraction_summary', {})
                    if extraction_summary:
                        print(f"\n🔧 MOTOR OCR:")
                        print(f"   • ATR source: {extraction_summary.get('atr_source', 'N/A')}")
                        print(f"   • Potencia P1 source: {extraction_summary.get('potencia_p1_source', 'N/A')}")
                        print(f"   • Consumo pattern: {extraction_summary.get('consumo_safe_pattern', 'N/A')}")
                except:
                    pass
            
            # Resumen final
            print(f"\n{'─'*80}")
            campos_criticos = [
                titular is not None,
                cups is not None,
                atr is not None,
                factura_data.get('total_factura') is not None,
                factura_data.get('consumo_kwh') is not None
            ]
            score = sum(campos_criticos)
            print(f"📊 SCORE: {score}/5 campos críticos extraídos")
            
            if score >= 4:
                print(f"✅ APROBADO - Extracción exitosa")
            elif score >= 3:
                print(f"⚠️  PARCIAL - Revisar campos faltantes")
            else:
                print(f"❌ FALLIDO - Muchos campos faltantes")
            
            return factura_data
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout - El servidor tardó más de 60s (OCR puede estar procesando)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    TEST AUTOMATIZADO - OCR FIXES                             ║
║                                                                              ║
║  Fix 1: Extracción nombre cliente (DATOS DEL CONTRATO strategy)            ║
║  Fix 2: Fusión pypdf+Vision (priorizar pypdf para CUPS)                    ║
║                                                                              ║
║  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar conectividad
    print(f"🔍 Verificando servidor...")
    try:
        health_check = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"✅ Servidor respondiendo (HTTP {health_check.status_code})")
    except:
        print(f"⚠️  Advertencia: No se pudo conectar al servidor")
        print(f"   Verifica que {BASE_URL} esté activo")
        return
    
    # Ejecutar tests
    resultados = []
    for factura_info in FACTURAS_TEST:
        resultado = test_upload_factura(factura_info)
        resultados.append({
            'nombre': factura_info['nombre'],
            'exito': resultado is not None,
            'data': resultado
        })
        time.sleep(1)  # Pausa entre requests
    
    # Resumen final
    print(f"\n\n{'='*80}")
    print(f"📊 RESUMEN FINAL")
    print(f"{'='*80}")
    
    exitosos = sum(1 for r in resultados if r['exito'])
    print(f"\n✅ {exitosos}/{len(resultados)} facturas procesadas exitosamente")
    
    for r in resultados:
        status = "✅" if r['exito'] else "❌"
        print(f"{status} {r['nombre']}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
