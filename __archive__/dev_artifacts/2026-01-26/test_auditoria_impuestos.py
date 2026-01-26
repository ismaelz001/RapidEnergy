#!/usr/bin/env python3
"""
Test de auditoría: Verificar cálculo IEE/IVA/Base IVA
Caso de prueba proporcionado por el usuario
"""

# CASO DE PRUEBA
dias = 32
E = 8.07  # Energía sin impuestos
P = 21.45  # Potencia sin impuestos
SUBTOTAL_SI = 29.52  # E + P
ALQUILER = 0.85
iva_pct_input = 21  # Porcentaje

# Convertir % a decimal para cálculo
iva_pct = iva_pct_input / 100.0  # 0.21

# Constante regulada
IEE_PCT = 0.0511269632

print("=" * 60)
print("AUDITORÍA DE CÁLCULO - IMPUESTOS EN FACTURA ELÉCTRICA")
print("=" * 60)
print(f"\n📊 DATOS DE ENTRADA:")
print(f"   Días: {dias}")
print(f"   Energía (E): {E:.2f}€")
print(f"   Potencia (P): {P:.2f}€")
print(f"   SUBTOTAL_SI: {SUBTOTAL_SI:.2f}€")
print(f"   Alquiler: {ALQUILER:.2f}€")
print(f"   IVA: {iva_pct_input}%")

print(f"\n🔬 CÁLCULO PASO A PASO:")

# Paso 1: IEE
IEE = SUBTOTAL_SI * IEE_PCT
print(f"   1) IEE = {SUBTOTAL_SI:.2f} × {IEE_PCT}")
print(f"      IEE = {IEE:.4f}€ → {IEE:.2f}€")

# Paso 2: BASE_IVA
BASE_IVA = SUBTOTAL_SI + IEE + ALQUILER
print(f"\n   2) BASE_IVA = SUBTOTAL_SI + IEE + ALQUILER")
print(f"      BASE_IVA = {SUBTOTAL_SI:.2f} + {IEE:.2f} + {ALQUILER:.2f}")
print(f"      BASE_IVA = {BASE_IVA:.2f}€")

# Paso 3: IVA
IVA = BASE_IVA * iva_pct
print(f"\n   3) IVA = BASE_IVA × {iva_pct}")
print(f"      IVA = {BASE_IVA:.2f} × {iva_pct}")
print(f"      IVA = {IVA:.4f}€ → {IVA:.2f}€")

# Paso 4: TOTAL
TOTAL = BASE_IVA + IVA
print(f"\n   4) TOTAL = BASE_IVA + IVA")
print(f"      TOTAL = {BASE_IVA:.2f} + {IVA:.2f}")
print(f"      TOTAL = {TOTAL:.2f}€")

print(f"\n" + "=" * 60)
print("✅ RESULTADOS ESPERADOS (CORRECTOS):")
print("=" * 60)
print(f"   SUBTOTAL_SI:  {SUBTOTAL_SI:.2f}€")
print(f"   IEE:          {IEE:.2f}€")
print(f"   ALQUILER:     {ALQUILER:.2f}€")
print(f"   BASE_IVA:     {BASE_IVA:.2f}€")
print(f"   IVA:          {IVA:.2f}€")
print(f"   TOTAL:        {TOTAL:.2f}€")

# Verificación contra lo que reportó el usuario
print(f"\n" + "=" * 60)
print("📋 COMPARACIÓN CON VALORES REPORTADOS EN PDF:")
print("=" * 60)
impuestos_suma_reportada = 7.77  # IEE + IVA según usuario
total_reportado = 38.58

impuestos_suma_calculada = IEE + IVA
print(f"   'Impuestos (IEE + IVA)' reportado: {impuestos_suma_reportada:.2f}€")
print(f"   'Impuestos (IEE + IVA)' calculado: {impuestos_suma_calculada:.2f}€")
diff_impuestos = abs(impuestos_suma_calculada - impuestos_suma_reportada)
print(f"   Diferencia: {diff_impuestos:.2f}€")

print(f"\n   'Total' reportado: {total_reportado:.2f}€")
print(f"   'Total' calculado: {TOTAL:.2f}€")
diff_total = abs(TOTAL - total_reportado)
print(f"   Diferencia: {diff_total:.2f}€")

if diff_total < 0.01:
    print(f"\n✅ VERIFICACIÓN: Los valores coinciden (diferencia < 0.01€)")
else:
    print(f"\n⚠️  VERIFICACIÓN: Hay discrepancia de {diff_total:.2f}€")
    pct_diff = (diff_total / total_reportado) * 100
    print(f"   Diferencia porcentual: {pct_diff:.2f}%")

print(f"\n" + "=" * 60)
print("🔍 VERIFICACIÓN DEL CÓDIGO FUENTE:")
print("=" * 60)

# Importar y ejecutar la función real del comparador
import sys
sys.path.insert(0, r'e:\MecaEnergy')

try:
    from app.services.comparador import _reconstruir_factura
    
    total_desde_funcion = _reconstruir_factura(
        subtotal_sin_impuestos=SUBTOTAL_SI,
        iva_pct=iva_pct,  # 0.21
        alquiler_total=ALQUILER,
        impuesto_electrico_pct=IEE_PCT
    )
    
    print(f"   Total desde _reconstruir_factura(): {total_desde_funcion:.2f}€")
    print(f"   Total calculado manualmente:        {TOTAL:.2f}€")
    
    if abs(total_desde_funcion - TOTAL) < 0.01:
        print(f"\n✅ La función _reconstruir_factura() está implementada CORRECTAMENTE")
    else:
        print(f"\n❌ DISCREPANCIA en la función _reconstruir_factura()")
        print(f"   Diferencia: {abs(total_desde_funcion - TOTAL):.2f}€")
        
except Exception as e:
    print(f"   ⚠️ No se pudo importar _reconstruir_factura: {e}")

print(f"\n" + "=" * 60)
