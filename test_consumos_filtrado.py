#!/usr/bin/env python3
"""
Test: Verificar si 'Sus consumos desagregados' se incluye en consumo_source
"""

import re
import sys
sys.path.insert(0, '/f:/MecaEnergy')

from app.services.ocr import extract_data_from_pdf

factura_path = "f:/MecaEnergy/temp_facturas/Factura Iberdrola.pdf"

with open(factura_path, 'rb') as f:
    file_bytes = f.read()

from pypdf import PdfReader
from io import BytesIO

reader = PdfReader(BytesIO(file_bytes))
raw_text = ""
for page in reader.pages:
    raw_text += page.extract_text() or ""

print("="*70)
print("BUSCANDO 'Sus consumos desagregados' EN EL RAW_TEXT")
print("="*70)

if "Sus consumos desagregados" in raw_text:
    print("✅ ENCONTRADO 'Sus consumos desagregados'")
    
    # Encontrar el contexto
    idx = raw_text.find("Sus consumos desagregados")
    start = max(0, idx - 100)
    end = min(len(raw_text), idx + 200)
    
    print(f"\nContexto (200 chars alrededor):")
    print(f"[...]{raw_text[start:end]}[...]")
    
    # Buscar punta, llano, valle cerca
    section = raw_text[idx:idx+300]
    print(f"\nSección 300 chars después:")
    print(f"{section}\n")
    
    # Test patterns en esta sección
    for term, pat in [("punta", r"punta[:\s]+([\d.,]+)"), 
                       ("llano", r"llano[:\s]+([\d.,]+)"),
                       ("valle", r"valle[:\s]+([\d.,]+)")]:
        m = re.search(pat, section, re.IGNORECASE)
        if m:
            print(f"✅ {term}: {m.group(1)}")
        else:
            print(f"❌ {term}: no match")
else:
    print("❌ NO ENCONTRADO 'Sus consumos desagregados'")
    print("\nBuscando 'punta' y 'llano' en el texto...")
    
    if re.search(r"punta", raw_text, re.IGNORECASE):
        print("✅ Encontré 'punta'")
        m = re.search(r"punta[:\s]+([\d.,]+)", raw_text, re.IGNORECASE)
        if m:
            print(f"   Valor: {m.group(1)}")
    
    if re.search(r"llano", raw_text, re.IGNORECASE):
        print("✅ Encontré 'llano'")
        m = re.search(r"llano[:\s]+([\d.,]+)", raw_text, re.IGNORECASE)
        if m:
            print(f"   Valor: {m.group(1)}")
    
    if re.search(r"valle", raw_text, re.IGNORECASE):
        print("✅ Encontré 'valle'")
        m = re.search(r"valle[:\s]+([\d.,]+)", raw_text, re.IGNORECASE)
        if m:
            print(f"   Valor: {m.group(1)}")

print("\n" + "="*70)
print("ANALIZANDO CONSUMO_SOURCE FILTRADO")
print("="*70)

# Reproducir el filtrado del código
def normalize_text(text):
    """Normalize text for regex search"""
    return re.sub(r'\s+', ' ', text.strip())

filtered_keywords = ["factura", "resumen", "total", "cliente", "telefono", "cif", "contrato", 
                     "correos", "madrid", "obligatorio", "obligatoria", "opcional", "información", 
                     "informacion", "referencia", "referencia", "renuncia", "pago"]

consumo_lines = []
for line in raw_text.split('\n'):
    clean = line.strip()
    if not clean:
        continue
    lower = clean.lower()
    # [PATCH] Allow lines with "consumo" OR specific period keywords
    if "consumo" not in lower and not re.search(r"\b(p[1-6]|punta|llano|valle)\b", lower):
        continue
    if any(bad in lower for bad in filtered_keywords):
        print(f"   FILTERED OUT (keyword): {clean[:60]}...")
        continue
    consumo_lines.append(clean)
    print(f"   ✅ INCLUDED: {clean[:70]}...")

consumo_source = "\n".join(consumo_lines) if consumo_lines else raw_text
normalized_consumo_text = normalize_text(consumo_source)

print(f"\nConsumo source total lines: {len(consumo_lines)}")
print(f"\nSearching for punta/llano/valle in consumo_source:")

for term, pat in [("punta", r"punta[:\s]+([\d.,]+)"), 
                   ("llano", r"llano[:\s]+([\d.,]+)"),
                   ("valle", r"valle[:\s]+([\d.,]+)")]:
    m = re.search(pat, normalized_consumo_text, re.IGNORECASE)
    if m:
        print(f"✅ {term}: {m.group(1)}")
    else:
        print(f"❌ {term}: no match")
