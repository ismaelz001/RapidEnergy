"""
Quick check: ¿Qué titular tiene REALMENTE el PDF de Iberdrola?
"""
import pypdf
import io

PDF_PATH = "temp_facturas/Factura Iberdrola.pdf"

with open(PDF_PATH, 'rb') as f:
    reader = pypdf.PdfReader(io.BytesIO(f.read()))
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

print("🔍 Buscando titular en PDF...")
print("=" * 80)

# Buscar líneas con nombres (mayúsculas, 2+ palabras)
import re
lines = full_text.split('\n')

print("\n📄 PRIMERAS 50 LÍNEAS DEL PDF:")
print("-" * 80)
for i, line in enumerate(lines[:50], 1):
    print(f"{i:3}. {line.strip()}")

print("\n\n👤 CANDIDATOS A TITULAR (nombres en mayúsculas):")
print("-" * 80)
for line in lines[:100]:
    # Buscar patrones de nombre: NOMBRE APELLIDO(S)
    if re.match(r'^[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ ,.\'-]{10,60}$', line.strip()):
        # Filtrar keywords técnicos
        if not any(k in line.lower() for k in ['iberdrola', 'factura', 'cups', 'importe', 'consumo', 'potencia', 'peaje']):
            print(f"   ✓ {line.strip()}")

# Buscar sección "DATOS DEL CONTRATO"
print("\n\n📋 SECCIÓN 'DATOS DEL CONTRATO':")
print("-" * 80)
match = re.search(r"DATOS\s+DEL\s+CONTRATO[\s\S]{0,800}", full_text, re.IGNORECASE)
if match:
    print(match.group(0))
else:
    print("❌ No encontrado")

# Buscar patrón "Titular:"
print("\n\n🎯 PATRÓN 'Titular:':")
print("-" * 80)
match = re.search(r"(?:titular|nombre\s+del\s+titular)\s*[:\-]?\s*([A-ZÁÉÍÓÚÜÑ][A-Za-záéíóúüñ ,.\'-]{10,80})", full_text, re.IGNORECASE)
if match:
    print(f"   ✓ {match.group(1).strip()}")
else:
    print("❌ No encontrado")
