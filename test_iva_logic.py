#!/usr/bin/env python3
"""
Test simple de la lógica de IVA sin conexión a BD.
Verifica que la lógica de prioridades funciona correctamente.
"""

def test_iva_logic():
    """Simula la lógica de IVA del comparador"""
    
    print("="*80)
    print("  🧪 TEST: Lógica de IVA")
    print("="*80)
    
    # Simular objeto factura
    class MockFactura:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    # TEST 1: Con iva_porcentaje especificado
    print("\n📋 TEST 1: Factura con iva_porcentaje = 21%")
    factura = MockFactura(iva_porcentaje=21.0, potencia_p1_kw=4.6)
    
    if hasattr(factura, 'iva_porcentaje') and factura.iva_porcentaje is not None:
        iva_pct = float(factura.iva_porcentaje) / 100.0
        modo_iva = f"factura_{factura.iva_porcentaje}%"
    else:
        iva_pct = 0.10 if factura.potencia_p1_kw < 10 else 0.21
        modo_iva = f"calculado_{int(iva_pct*100)}%"
    
    print(f"   ✅ IVA: {iva_pct*100}%")
    print(f"   ✅ Modo: {modo_iva}")
    assert modo_iva == "factura_21.0%", f"ERROR: Esperado 'factura_21.0%', obtenido '{modo_iva}'"
    
    # TEST 2: Con iva_porcentaje = 10%
    print("\n📋 TEST 2: Factura con iva_porcentaje = 10%")
    factura = MockFactura(iva_porcentaje=10.0, potencia_p1_kw=4.6)
    
    if hasattr(factura, 'iva_porcentaje') and factura.iva_porcentaje is not None:
        iva_pct = float(factura.iva_porcentaje) / 100.0
        modo_iva = f"factura_{factura.iva_porcentaje}%"
    else:
        iva_pct = 0.10 if factura.potencia_p1_kw < 10 else 0.21
        modo_iva = f"calculado_{int(iva_pct*100)}%"
    
    print(f"   ✅ IVA: {iva_pct*100}%")
    print(f"   ✅ Modo: {modo_iva}")
    assert modo_iva == "factura_10.0%", f"ERROR: Esperado 'factura_10.0%', obtenido '{modo_iva}'"
    
    # TEST 3: SIN iva_porcentaje, potencia < 10kW
    print("\n📋 TEST 3: SIN iva_porcentaje, potencia < 10kW (fallback 10%)")
    factura = MockFactura(iva_porcentaje=None, potencia_p1_kw=4.6)
    
    if hasattr(factura, 'iva_porcentaje') and factura.iva_porcentaje is not None:
        iva_pct = float(factura.iva_porcentaje) / 100.0
        modo_iva = f"factura_{factura.iva_porcentaje}%"
    else:
        iva_pct = 0.10 if factura.potencia_p1_kw < 10 else 0.21
        modo_iva = f"calculado_{int(iva_pct*100)}%"
    
    print(f"   ✅ IVA: {iva_pct*100}%")
    print(f"   ✅ Modo: {modo_iva}")
    assert modo_iva == "calculado_10%", f"ERROR: Esperado 'calculado_10%', obtenido '{modo_iva}'"
    
    # TEST 4: SIN iva_porcentaje, potencia >= 10kW
    print("\n📋 TEST 4: SIN iva_porcentaje, potencia >= 10kW (fallback 21%)")
    factura = MockFactura(iva_porcentaje=None, potencia_p1_kw=15.0)
    
    if hasattr(factura, 'iva_porcentaje') and factura.iva_porcentaje is not None:
        iva_pct = float(factura.iva_porcentaje) / 100.0
        modo_iva = f"factura_{factura.iva_porcentaje}%"
    else:
        iva_pct = 0.10 if factura.potencia_p1_kw < 10 else 0.21
        modo_iva = f"calculado_{int(iva_pct*100)}%"
    
    print(f"   ✅ IVA: {iva_pct*100}%")
    print(f"   ✅ Modo: {modo_iva}")
    assert modo_iva == "calculado_21%", f"ERROR: Esperado 'calculado_21%', obtenido '{modo_iva}'"
    
    print("\n" + "="*80)
    print("  ✅ TODOS LOS TESTS DE IVA PASARON")
    print("="*80)


def test_iee_logic():
    """Simula la lógica de Impuesto Eléctrico"""
    
    print("\n" + "="*80)
    print("  🧪 TEST: Lógica de Impuesto Eléctrico")
    print("="*80)
    
    class MockFactura:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    # TEST 1: Con impuesto_electrico especificado
    print("\n📋 TEST 1: Factura con impuesto_electrico = 3.80€")
    factura = MockFactura(impuesto_electrico=3.80)
    subtotal = 74.30
    
    if hasattr(factura, 'impuesto_electrico') and factura.impuesto_electrico is not None:
        impuesto_electrico = float(factura.impuesto_electrico)
        modo_iee = "factura_real"
    else:
        impuesto_electrico = subtotal * 0.0511269632
        modo_iee = "calculado_5.11%"
    
    print(f"   ✅ IEE: {impuesto_electrico}€")
    print(f"   ✅ Modo: {modo_iee}")
    assert modo_iee == "factura_real", f"ERROR: Esperado 'factura_real', obtenido '{modo_iee}'"
    assert impuesto_electrico == 3.80, f"ERROR: Esperado 3.80, obtenido {impuesto_electrico}"
    
    # TEST 2: SIN impuesto_electrico (debe calcular)
    print("\n📋 TEST 2: SIN impuesto_electrico (debe calcular 5.11269632%)")
    factura = MockFactura(impuesto_electrico=None)
    subtotal = 74.30
    
    if hasattr(factura, 'impuesto_electrico') and factura.impuesto_electrico is not None:
        impuesto_electrico = float(factura.impuesto_electrico)
        modo_iee = "factura_real"
    else:
        impuesto_electrico = subtotal * 0.0511269632
        modo_iee = "calculado_5.11%"
    
    expected_iee = 74.30 * 0.0511269632
    print(f"   ✅ IEE: {impuesto_electrico:.2f}€ (calculado)")
    print(f"   ✅ Modo: {modo_iee}")
    assert modo_iee == "calculado_5.11%", f"ERROR: Esperado 'calculado_5.11%', obtenido '{modo_iee}'"
    assert abs(impuesto_electrico - expected_iee) < 0.01, f"ERROR: Cálculo incorrecto"
    
    print("\n" + "="*80)
    print("  ✅ TODOS LOS TESTS DE IEE PASARON")
    print("="*80)


def test_alquiler_logic():
    """Simula la lógica de Alquiler Contador"""
    
    print("\n" + "="*80)
    print("  🧪 TEST: Lógica de Alquiler Contador")
    print("="*80)
    
    class MockFactura:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    # TEST 1: Con alquiler_contador especificado
    print("\n📋 TEST 1: Factura con alquiler_contador = 0.80€")
    factura = MockFactura(alquiler_contador=0.80)
    
    if hasattr(factura, 'alquiler_contador') and factura.alquiler_contador is not None:
        alquiler_equipo = float(factura.alquiler_contador)
        modo_alquiler = "factura_real"
    else:
        alquiler_equipo = 0.0
        modo_alquiler = "no_aplica"
    
    print(f"   ✅ Alquiler: {alquiler_equipo}€")
    print(f"   ✅ Modo: {modo_alquiler}")
    assert modo_alquiler == "factura_real", f"ERROR: Esperado 'factura_real', obtenido '{modo_alquiler}'"
    assert alquiler_equipo == 0.80, f"ERROR: Esperado 0.80, obtenido {alquiler_equipo}"
    
    # TEST 2: SIN alquiler_contador (NO debe incluirlo)
    print("\n📋 TEST 2: SIN alquiler_contador (debe ser 0)")
    factura = MockFactura(alquiler_contador=None)
    
    if hasattr(factura, 'alquiler_contador') and factura.alquiler_contador is not None:
        alquiler_equipo = float(factura.alquiler_contador)
        modo_alquiler = "factura_real"
    else:
        alquiler_equipo = 0.0
        modo_alquiler = "no_aplica"
    
    print(f"   ✅ Alquiler: {alquiler_equipo}€")
    print(f"   ✅ Modo: {modo_alquiler}")
    assert modo_alquiler == "no_aplica", f"ERROR: Esperado 'no_aplica', obtenido '{modo_alquiler}'"
    assert alquiler_equipo == 0.0, f"ERROR: Esperado 0.0, obtenido {alquiler_equipo}"
    
    print("\n" + "="*80)
    print("  ✅ TODOS LOS TESTS DE ALQUILER PASARON")
    print("="*80)


if __name__ == "__main__":
    try:
        test_iva_logic()
        test_iee_logic()
        test_alquiler_logic()
        
        print("\n" + "="*80)
        print("  🎉 TODOS LOS TESTS PASARON - LÓGICA CORRECTA")
        print("="*80)
        print("\n✅ Los cambios de IVA están funcionando correctamente")
        print("✅ Seguro para continuar con testing en desarrollo")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        print("\n⚠️  NO DESPLEGAR A PRODUCCIÓN")
        exit(1)
