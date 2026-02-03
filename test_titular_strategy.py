"""
Test local: Validar nueva estrategia de extracción titular
"""
import sys
sys.path.insert(0, 'f:/MecaEnergy')

from app.services.ocr import parse_invoice_text
import pypdf
import io

FACTURAS_TEST = {
    "Iberdrola": "temp_facturas/Factura Iberdrola.pdf",
    "Naturgy": "temp_facturas/factura Naturgy.pdf", 
    "Endesa": "temp_facturas/Factura.pdf",
    "HC Energía": "temp_facturas/Fra Agosto.pdf"
}

EXPECTED = {
    "Iberdrola": "JOSE ANTONIO RODRIGUEZ UROZ",
    "Naturgy": "ENCARNACIÓN LINARES LÓPEZ",
    "Endesa": "ANTONIO RUIZ MORENO",
    "HC Energía": "Vygantas Kaminskas"
}

print("🧪 TESTING ESTRATEGIA ROBUSTA EXTRACCIÓN TITULAR")
print("=" * 100)

results = []
for nombre, pdf_path in FACTURAS_TEST.items():
    print(f"\n📄 {nombre}")
    print("-" * 100)
    
    with open(pdf_path, 'rb') as f:
        reader = pypdf.PdfReader(io.BytesIO(f.read()))
        text = ''.join(p.extract_text() for p in reader.pages)
    
    result = parse_invoice_text(text)
    titular_extraido = result.get('titular')
    titular_esperado = EXPECTED[nombre]
    
    if titular_extraido == titular_esperado:
        print(f"✅ CORRECTO: '{titular_extraido}'")
        results.append(True)
    else:
        print(f"❌ FALLIDO")
        print(f"   Extraído: '{titular_extraido}'")
        print(f"   Esperado: '{titular_esperado}'")
        results.append(False)

print(f"\n{'=' * 100}")
print(f"📊 RESULTADO FINAL: {sum(results)}/{len(results)} facturas correctas")
print(f"{'=' * 100}")

if all(results):
    print("✅ TODOS LOS TESTS PASARON - OK para commitear")
else:
    print("⚠️ HAY FALLOS - Revisar estrategia antes de commitear")
