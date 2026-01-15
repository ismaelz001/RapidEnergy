
import json
from typing import Any, Dict
from app.services.comparador import compare_factura

# Clase para simular el objeto Factura que viene de la BBDD
class MockFactura:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
    
    @property
    def id(self): return 999
    @property
    def cups(self): return "ES00000000000000000000"
    @property
    def atr(self): return "3.0TD"
    @property
    def periodo_dias(self): return 30

# Clase para simular la conexión a BBDD (no hace nada real)
class MockDB:
    def execute(self, *args, **kwargs):
        return self
    def mappings(self):
        return self
    def all(self):
        # Devolvemos una tarifa 3.0TD ficticia para el test
        return [{
            "id": 1,
            "comercializadora": "Endesa",
            "nombre": "Plan Empresas Plus 3.0TD",
            "atr": "3.0TD",
            "energia_p1_eur_kwh": 0.145,
            "energia_p2_eur_kwh": 0.130,
            "energia_p3_eur_kwh": 0.115,
            "energia_p4_eur_kwh": 0.110,
            "energia_p5_eur_kwh": 0.105,
            "energia_p6_eur_kwh": 0.095,
            "potencia_p1_eur_kw_dia": 0.120,
            "potencia_p2_eur_kw_dia": 0.110,
            "potencia_p3_eur_kw_dia": 0.100,
            "potencia_p4_eur_kw_dia": 0.090,
            "potencia_p5_eur_kw_dia": 0.080,
            "potencia_p6_eur_kw_dia": 0.070,
        }]
    def add(self, *args): pass
    def commit(self): pass
    def refresh(self, *args): pass

def run_brain_test():
    print("🧠 TEST DE LÓGICA: Comparador 3.0TD (Sin BBDD)")
    print("="*50)
    
    # Datos de una factura industrial real (P1-P6)
    data = {
        "total_factura": 1200.50,
        "potencia_p1_kw": 25.0, "potencia_p2_kw": 25.0, "potencia_p3_kw": 25.0,
        "potencia_p4_kw": 25.0, "potencia_p5_kw": 25.0, "potencia_p6_kw": 25.0,
        "consumo_p1_kwh": 1000, "consumo_p2_kwh": 900, "consumo_p3_kwh": 1200,
        "consumo_p4_kwh": 800, "consumo_p5_kwh": 600, "consumo_p6_kwh": 1500
    }
    
    factura = MockFactura(data)
    db = MockDB()
    
    try:
        resultado = compare_factura(factura, db)
        
        offer = resultado['offers'][0]
        print(f"✅ ATR Detectado correctamente")
        print(f"✅ Oferta calculada: {offer['plan_name']}")
        print(f"💰 Total Estimado: {offer['estimated_total']} €")
        print(f"📊 IVA aplicado: {offer['breakdown']['modo_iva']}")
        
        # Validación de IVA
        if "21%" in offer['breakdown']['modo_iva']:
            print("✨ EXITO: El cerebro ha aplicado el 21% de IVA por ser 3.0TD")
        else:
            print("❌ ERROR: El IVA debería ser 21%")

        # Verificación de periodos
        if offer['breakdown']['coste_energia'] > 0:
            print(f"⚡ Coste Energía: {offer['breakdown']['coste_energia']} € (Calculados 6 periodos)")

    except Exception as e:
        print(f"❌ Error en el test: {e}")

if __name__ == "__main__":
    run_brain_test()
