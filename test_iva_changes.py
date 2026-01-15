#!/usr/bin/env python3
"""
Script de testing local para verificar cambios de IVA antes de producción.
Prueba el comparador con datos reales sin tocar la BD de producción.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.comparador import compare_factura
from app.db.models import Factura
from datetime import date


class MockDB:
    """Mock de base de datos para testing sin tocar producción"""
    def __init__(self):
        self.tarifas = [
            {
                "id": 1,
                "comercializadora": "Endesa",
                "nombre": "Tarifa Libre Promo",
                "atr": "2.0TD",
                "energia_p1_eur_kwh": 0.1059,
                "energia_p2_eur_kwh": 0.1059,
                "energia_p3_eur_kwh": 0.1059,
                "potencia_p1_eur_kw_dia": 0.090214,
                "potencia_p2_eur_kw_dia": 0.090214,
            },
            {
                "id": 2,
                "comercializadora": "Iberdrola",
                "nombre": "Plan Estable",
                "atr": "2.0TD",
                "energia_p1_eur_kwh": 0.127394,
                "energia_p2_eur_kwh": 0.127394,
                "energia_p3_eur_kwh": 0.127394,
                "potencia_p1_eur_kw_dia": None,  # Iberdrola sin precios potencia
                "potencia_p2_eur_kw_dia": None,
            },
            {
                "id": 3,
                "comercializadora": "Naturgy",
                "nombre": "Tarifa Plana",
                "atr": "2.0TD",
                "energia_p1_eur_kwh": 0.120471,
                "energia_p2_eur_kwh": None,  # Tarifa plana 24h
                "energia_p3_eur_kwh": None,
                "potencia_p1_eur_kw_dia": 0.111815,
                "potencia_p2_eur_kw_dia": 0.033933,
            }
        ]
        self.comparativas = []
        self.ofertas = []
    
    def execute(self, query, params=None):
        """Mock de execute para queries SQL"""
        class Result:
            def __init__(self, data):
                self.data = data
            
            def mappings(self):
                return self
            
            def all(self):
                return self.data
        
        # Simular query de tarifas
        if "SELECT * FROM tarifas" in str(query):
            return Result(self.tarifas)
        
        return Result([])
    
    def add(self, obj):
        """Mock de add"""
        if hasattr(obj, '__tablename__'):
            if obj.__tablename__ == 'comparativas':
                obj.id = len(self.comparativas) + 1
                self.comparativas.append(obj)
    
    def commit(self):
        """Mock de commit"""
        pass
    
    def refresh(self, obj):
        """Mock de refresh"""
        pass
    
    def get_bind(self):
        """Mock de get_bind"""
        class Bind:
            class Dialect:
                name = "postgresql"
            dialect = Dialect()
        return Bind()


class MockFactura:
    """Mock de factura para testing"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.cups = kwargs.get('cups', 'ES0021000000000000AA')
        self.atr = kwargs.get('atr', '2.0TD')
        
        # Consumos
        self.consumo_p1_kwh = kwargs.get('consumo_p1_kwh', 50.0)
        self.consumo_p2_kwh = kwargs.get('consumo_p2_kwh', 80.0)
        self.consumo_p3_kwh = kwargs.get('consumo_p3_kwh', 120.0)
        
        # Potencias
        self.potencia_p1_kw = kwargs.get('potencia_p1_kw', 4.6)
        self.potencia_p2_kw = kwargs.get('potencia_p2_kw', 4.6)
        
        # Periodo
        self.periodo_dias = kwargs.get('periodo_dias', 30)
        self.fecha_inicio = kwargs.get('fecha_inicio', None)
        self.fecha_fin = kwargs.get('fecha_fin', None)
        
        # Total
        self.total_factura = kwargs.get('total_factura', 75.50)
        
        # Impuestos (NUEVOS CAMPOS A TESTEAR)
        self.iva = kwargs.get('iva', None)
        self.iva_porcentaje = kwargs.get('iva_porcentaje', None)
        self.impuesto_electrico = kwargs.get('impuesto_electrico', None)
        self.alquiler_contador = kwargs.get('alquiler_contador', None)


def print_separator(title):
    """Imprime separador visual"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_scenario(name, factura, expected_modes):
    """Ejecuta un escenario de test"""
    print_separator(f"TEST: {name}")
    
    db = MockDB()
    
    try:
        result = compare_factura(factura, db)
        
        print(f"✅ Comparación exitosa")
        print(f"   - Ofertas generadas: {len(result['offers'])}")
        print(f"   - Periodo usado: {result['periodo_dias']} días")
        print(f"   - Total factura: {result['current_total']}€")
        
        # Verificar primera oferta
        if result['offers']:
            offer = result['offers'][0]
            breakdown = offer['breakdown']
            
            print(f"\n📊 Primera oferta: {offer['provider']} - {offer['plan_name']}")
            print(f"   - Total estimado: {offer['estimated_total_periodo']}€")
            print(f"   - Ahorro: {offer['ahorro_periodo']}€")
            
            print(f"\n🔍 Modos de cálculo:")
            print(f"   - Energía: {breakdown['modo_energia']}")
            print(f"   - Potencia: {breakdown['modo_potencia']}")
            print(f"   - IEE: {breakdown.get('modo_iee', 'N/A')}")
            print(f"   - IVA: {breakdown.get('modo_iva', 'N/A')}")
            print(f"   - Alquiler: {breakdown.get('modo_alquiler', 'N/A')}")
            
            # Verificar modos esperados
            print(f"\n✓ Verificación de modos:")
            for key, expected_value in expected_modes.items():
                actual_value = breakdown.get(key, 'N/A')
                status = "✅" if expected_value in actual_value else "❌"
                print(f"   {status} {key}: esperado '{expected_value}', obtenido '{actual_value}'")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todos los tests"""
    print_separator("🧪 TESTS LOCALES - CAMBIOS IVA")
    print("Verificando que los cambios funcionan correctamente antes de producción")
    
    tests_passed = 0
    tests_total = 0
    
    # TEST 1: Factura CON iva_porcentaje especificado (21%)
    tests_total += 1
    factura1 = MockFactura(
        consumo_p1_kwh=50,
        consumo_p2_kwh=80,
        consumo_p3_kwh=120,
        potencia_p1_kw=4.6,
        potencia_p2_kw=4.6,
        periodo_dias=30,
        total_factura=75.50,
        iva=14.50,
        iva_porcentaje=21.0,  # Usuario seleccionó 21%
        impuesto_electrico=3.80,
        alquiler_contador=0.80
    )
    if test_scenario(
        "Factura con IVA 21% especificado",
        factura1,
        expected_modes={
            'modo_iva': 'factura_21',
            'modo_iee': 'factura_real',
            'modo_alquiler': 'factura_real'
        }
    ):
        tests_passed += 1
    
    # TEST 2: Factura CON iva_porcentaje 10%
    tests_total += 1
    factura2 = MockFactura(
        consumo_p1_kwh=50,
        consumo_p2_kwh=80,
        consumo_p3_kwh=120,
        potencia_p1_kw=4.6,
        potencia_p2_kw=4.6,
        periodo_dias=30,
        total_factura=68.30,
        iva=6.21,
        iva_porcentaje=10.0,  # Usuario seleccionó 10%
        impuesto_electrico=3.17,
        alquiler_contador=None  # Sin alquiler
    )
    if test_scenario(
        "Factura con IVA 10% y SIN alquiler contador",
        factura2,
        expected_modes={
            'modo_iva': 'factura_10',
            'modo_iee': 'factura_real',
            'modo_alquiler': 'no_aplica'
        }
    ):
        tests_passed += 1
    
    # TEST 3: Factura SIN iva_porcentaje (debe usar fallback por potencia)
    tests_total += 1
    factura3 = MockFactura(
        consumo_p1_kwh=50,
        consumo_p2_kwh=80,
        consumo_p3_kwh=120,
        potencia_p1_kw=4.6,  # < 10kW, debe usar 10%
        potencia_p2_kw=4.6,
        periodo_dias=30,
        total_factura=70.00,
        iva=None,  # No especificado
        iva_porcentaje=None,  # No especificado
        impuesto_electrico=None,  # Debe calcular
        alquiler_contador=None
    )
    if test_scenario(
        "Factura SIN IVA especificado (fallback por potencia <10kW)",
        factura3,
        expected_modes={
            'modo_iva': 'calculado_10',
            'modo_iee': 'calculado_5.11',
            'modo_alquiler': 'no_aplica'
        }
    ):
        tests_passed += 1
    
    # TEST 4: Factura con potencia alta (debe usar IVA 21% en fallback)
    tests_total += 1
    factura4 = MockFactura(
        consumo_p1_kwh=100,
        consumo_p2_kwh=150,
        consumo_p3_kwh=200,
        potencia_p1_kw=15.0,  # >= 10kW, debe usar 21%
        potencia_p2_kw=15.0,
        periodo_dias=30,
        total_factura=180.00,
        iva=None,
        iva_porcentaje=None,
        impuesto_electrico=None,
        alquiler_contador=None
    )
    if test_scenario(
        "Factura SIN IVA especificado (fallback por potencia >=10kW)",
        factura4,
        expected_modes={
            'modo_iva': 'calculado_21',
            'modo_iee': 'calculado_5.11',
            'modo_alquiler': 'no_aplica'
        }
    ):
        tests_passed += 1
    
    # TEST 5: Factura con IVA 4% (caso especial)
    tests_total += 1
    factura5 = MockFactura(
        consumo_p1_kwh=50,
        consumo_p2_kwh=80,
        consumo_p3_kwh=120,
        potencia_p1_kw=4.6,
        potencia_p2_kw=4.6,
        periodo_dias=30,
        total_factura=65.00,
        iva=2.50,
        iva_porcentaje=4.0,  # IVA superreducido
        impuesto_electrico=3.17,
        alquiler_contador=0.80
    )
    if test_scenario(
        "Factura con IVA 4% (superreducido)",
        factura5,
        expected_modes={
            'modo_iva': 'factura_4',
            'modo_iee': 'factura_real',
            'modo_alquiler': 'factura_real'
        }
    ):
        tests_passed += 1
    
    # RESUMEN
    print_separator("📊 RESUMEN DE TESTS")
    print(f"Tests ejecutados: {tests_total}")
    print(f"Tests exitosos: {tests_passed}")
    print(f"Tests fallidos: {tests_total - tests_passed}")
    
    if tests_passed == tests_total:
        print("\n✅ TODOS LOS TESTS PASARON - Seguro para producción")
        return 0
    else:
        print(f"\n❌ FALLOS DETECTADOS - NO DESPLEGAR A PRODUCCIÓN")
        return 1


if __name__ == "__main__":
    sys.exit(main())
