"""
Test del comparador para Factura #285
Simula los datos del OCR y verifica qué ofertas genera
"""

import os
import sys
import json
from datetime import datetime

# Add app to path
sys.path.insert(0, os.getcwd())

# Configurar variables de entorno
os.environ.setdefault('DATABASE_URL', 'sqlite:///./local.db')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Mock factura class que simula la BD
class MockCliente:
    def __init__(self):
        self.nombre = "JOSE ANTONIO RODRIGUEZ UROZ"

class MockFactura:
    def __init__(self):
        self.id = 285
        self.cups = "ES0031103378680001TE"
        self.atr = "2.0TD"
        self.total_factura = 38.88
        self.periodo_dias = 31
        self.cliente = MockCliente()
        self.consumo_p1_kwh = 59
        self.consumo_p2_kwh = 55.99
        self.consumo_p3_kwh = 166.72
        self.consumo_p4_kwh = 0
        self.consumo_p5_kwh = 0
        self.consumo_p6_kwh = 0
        self.potencia_p1_kw = 5
        self.potencia_p2_kw = 5
        self.iva_porcentaje = 21
        self.alquiler_contador = 2.1
        self.iva = None
        self.impuesto_electrico = None
        self.coste_energia_actual = None
        self.coste_potencia_actual = None
        self.fecha_inicio = None
        self.fecha_fin = None
        self.validado_step2 = False
        self.total_ajustado = None
        self.estado_factura = "lista_para_comparar"

def main():
    print("\n" + "="*70)
    print("TEST COMPARADOR - FACTURA #285")
    print("="*70)
    
    # Intentar conectar a la BD
    try:
        db_url = os.environ.get('DATABASE_URL', 'sqlite:///./local.db')
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        print(f"\n✅ Conexión a BD exitosa: {db_url}")
        
        # Verificar que existen tarifas
        result = db.execute(text("SELECT COUNT(*) as count FROM tarifas"))
        count = result.scalar()
        print(f"📊 Total de tarifas en BD: {count}")
        
        if count == 0:
            print("⚠️  No hay tarifas en la BD. El comparador no podrá generar ofertas.")
            return
        
        # Mostrar algunas tarifas 2.0TD
        result = db.execute(text("""
            SELECT id, comercializadora, nombre, energia_p1_eur_kwh, 
                   potencia_p1_eur_kw_dia, potencia_p2_eur_kw_dia
            FROM tarifas 
            WHERE atr = '2.0TD'
            LIMIT 5
        """))
        tarifas_sample = result.fetchall()
        
        print(f"\n📋 Muestra de tarifas 2.0TD:")
        for tarifa in tarifas_sample:
            print(f"  - {tarifa[1]}: {tarifa[2]} (E_P1={tarifa[3]}, POT_P1={tarifa[4]}, POT_P2={tarifa[5]})")
        
        # Ahora simular el comparador
        print("\n" + "-"*70)
        print("EJECUTANDO COMPARADOR...")
        print("-"*70)
        
        from app.services.comparador import compare_factura
        
        factura = MockFactura()
        
        try:
            result = compare_factura(factura, db)
            
            print("\n✅ COMPARADOR EJECUTADO EXITOSAMENTE")
            print(f"\n📊 Resultados:")
            print(f"  - Factura ID: {result['factura_id']}")
            print(f"  - Total actual: {result['current_total']}€")
            print(f"  - Periodo: {result['periodo_dias']} días")
            print(f"  - Total de ofertas: {len(result['offers'])}")
            
            if result['offers']:
                print(f"\n🎯 Ofertas generadas:")
                for idx, offer in enumerate(result['offers'][:5], 1):
                    ahorro_anual = offer.get('saving_amount_annual', 0)
                    ahorro_periodo = offer.get('saving_amount', 0)
                    total_est = offer.get('estimated_total', 0)
                    
                    print(f"\n  [{idx}] {offer['provider']} - {offer['plan_name']}")
                    print(f"      Total estimado: {total_est}€")
                    print(f"      Ahorro período ({result['periodo_dias']}d): {ahorro_periodo}€")
                    print(f"      Ahorro anual: {ahorro_anual}€")
                    print(f"      Tag: {offer.get('tag', 'N/A')}")
                    print(f"      Comparable: {offer.get('is_structural_comparable', False)}")
                
                # Estadísticas
                ahorros = [o.get('saving_amount_annual', 0) for o in result['offers']]
                max_ahorro = max(ahorros)
                min_ahorro = min(ahorros)
                avg_ahorro = sum(ahorros) / len(ahorros)
                
                print(f"\n📈 Estadísticas de ahorro anual:")
                print(f"  - Máximo: {max_ahorro}€")
                print(f"  - Mínimo: {min_ahorro}€")
                print(f"  - Promedio: {avg_ahorro:.2f}€")
                print(f"  - Ofertas con ahorro > 0: {len([o for o in result['offers'] if o.get('saving_amount_annual', 0) > 0])}")
                print(f"  - Ofertas con ahorro <= 0: {len([o for o in result['offers'] if o.get('saving_amount_annual', 0) <= 0])}")
            else:
                print("\n⚠️  NO HAY OFERTAS GENERADAS")
                if result.get('error_code'):
                    print(f"  Error: {result.get('error_code')}")
                    print(f"  Mensaje: {result.get('message')}")
            
            # Mostrar baseline
            print(f"\n🔍 Detalles del cálculo:")
            print(f"  - Método: {result.get('baseline_method', 'N/A')}")
            print(f"  - Subtotal sin IVA actual: {result.get('subtotal_si_actual', 'N/A')}€")
            print(f"  - Total reconstruido: {result.get('total_actual_reconstruido', 'N/A')}€")
            print(f"  - Diferencia vs original: {result.get('diff_vs_current_total', 'N/A')}€")
            
        except Exception as e:
            print(f"\n❌ ERROR AL EJECUTAR COMPARADOR:")
            print(f"  {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ ERROR DE CONEXIÓN:")
        print(f"  {type(e).__name__}: {str(e)}")
        print("\n💡 Asegúrate de que:")
        print("    1. La BD local.db existe en F:\\MecaEnergy")
        print("    2. Hay tarifas importadas en la tabla 'tarifas'")

if __name__ == "__main__":
    main()
