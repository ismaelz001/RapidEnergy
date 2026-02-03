#!/usr/bin/env python3
"""
Extraer texto raw de cada PDF para analizar patrones
"""
import sys
import pypdf
import io

pdfs = {
    "Iberdrola": "temp_facturas/Factura Iberdrola.pdf",
    "Naturgy": "temp_facturas/factura Naturgy.pdf",
    "Endesa": "temp_facturas/Factura.pdf",
    "HC_Energia": "temp_facturas/Fra Agosto.pdf"
}

for name, path in pdfs.items():
    print(f"\n{'='*100}")
    print(f"{name.upper()} - Buscando: DIRECCION, LOCALIDAD, ALQUILER")
    print(f"{'='*100}")
    
    with open(path, "rb") as f:
        reader = pypdf.PdfReader(io.BytesIO(f.read()))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    
    lines = text.split('\n')
    
    # Buscar líneas con palabras clave
    keywords = ['direcci', 'domicilio', 'calle', 'avenida', 'localidad', 'provincia', 
                'alquiler', 'equipo', 'medida', 'contador']
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            # Mostrar contexto: 2 líneas antes y después
            start = max(0, i-2)
            end = min(len(lines), i+3)
            print(f"\n[Línea {i}] Contexto:")
            for j in range(start, end):
                marker = ">>> " if j == i else "    "
                print(f"{marker}{lines[j][:120]}")
