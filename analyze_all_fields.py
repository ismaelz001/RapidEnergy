"""
ANÁLISIS EXHAUSTIVO: Todos los campos de extracción OCR
Comparar con datos reales de cada factura
"""
import pypdf
import io
import os
import re
from datetime import datetime

FACTURAS = {
    "Iberdrola": "temp_facturas/Factura Iberdrola.pdf",
    "Naturgy": "temp_facturas/factura Naturgy.pdf",
    "Endesa": "temp_facturas/Factura.pdf",
    "HC Energía": "temp_facturas/Fra Agosto.pdf"
}

def extract_manual_data(pdf_path, comercializadora):
    """Extraer datos MANUALMENTE de cada PDF para comparar con OCR"""
    
    with open(pdf_path, 'rb') as f:
        reader = pypdf.PdfReader(io.BytesIO(f.read()))
        text = ''.join(p.extract_text() for p in reader.pages)
    
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
    
    print(f"\n{'='*100}")
    print(f"FACTURA: {comercializadora.upper()}")
    print(f"{'='*100}")
    
    # Mostrar primeras 50 líneas para referencia
    print(f"\nPRIMERAS 50 LINEAS DEL PDF:")
    print("-" * 100)
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3}. {line}")
    
    print(f"\n\nANALISIS DE CAMPOS CRITICOS:")
    print("-" * 100)
    
    # 1. CUPS
    print(f"\n1 CUPS:")
    cups_matches = re.findall(r"(ES[\s\-]*\d{4}[\s\-]*\d{4}[\s\-]*\d{4}[\s\-]*\d{4}[\s\-]*[A-Z]{2})", text, re.IGNORECASE)
    for match in cups_matches:
        print(f"   ✓ {match}")
    
    # 2. ATR / Peaje
    print(f"\n2️⃣ ATR (Peaje de acceso):")
    atr_patterns = [
        r"2[\.,]0\s*TD",
        r"3[\.,]0\s*TD",
        r"6[\.,]1\s*TD",
        r"peaje.*?(2\.0|3\.0|6\.1)",
    ]
    for pattern in atr_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"   ✓ {matches[0]}")
            break
    else:
        print(f"   ❌ No encontrado")
    
    # 3. Fechas periodo
    print(f"\n3️⃣ PERIODO DE CONSUMO (fechas):")
    fecha_patterns = [
        r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*[-a]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        r"del\s+(\d{1,2})\s+de\s+(\w+)\s+.*?al?\s+(\d{1,2})\s+de\s+(\w+)",
        r"(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})\s*[-a]\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})"
    ]
    for pattern in fecha_patterns:
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            print(f"   ✓ {matches.group(0)}")
            break
    else:
        print(f"   ❌ No encontrado")
    
    # 4. Días facturados
    print(f"\n4️⃣ DÍAS FACTURADOS:")
    dias_patterns = [
        r"(\d+)\s+d[ií]as?\s*(?:facturados?)?",
        r"d[ií]as?\s*(?:facturados?)?\s*[:\-]?\s*(\d+)",
        r"\((\d+)\s+d[ií]as?\)"
    ]
    for pattern in dias_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"   ✓ {matches} → Revisar cuál es el correcto")
            break
    else:
        print(f"   ❌ No encontrado")
    
    # 5. Consumo total
    print(f"\n5️⃣ CONSUMO TOTAL (kWh):")
    consumo_patterns = [
        r"consumo\s+total[:\s]*(\d+[.,]?\d*)\s*kw?h",
        r"su\s+consumo.*?(\d+[.,]?\d*)\s*kw?h",
        r"(\d+[.,]?\d*)\s*kw?h\s+x\s+[\d.,]+\s*€",
    ]
    for pattern in consumo_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"   ✓ {matches}")
            break
    else:
        print(f"   ❌ No encontrado")
    
    # 6. Potencia contratada P1/P2
    print(f"\n6️⃣ POTENCIA CONTRATADA (kW):")
    potencia_patterns = [
        r"potencia\s+(?:contratada\s+)?(?:en\s+)?punta[:\s]*(\d+[.,]?\d*)\s*kw",
        r"potencia\s+(?:contratada\s+)?(?:en\s+)?valle[:\s]*(\d+[.,]?\d*)\s*kw",
        r"potencia\s+(?:contratada\s+)?p1[:\s]*(\d+[.,]?\d*)\s*kw",
        r"potencia\s+(?:contratada\s+)?p2[:\s]*(\d+[.,]?\d*)\s*kw",
    ]
    for pattern in potencia_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"   ✓ {pattern[:40]}... → {matches}")
    
    # 7. Total factura
    print(f"\n7️⃣ TOTAL FACTURA (€):")
    total_patterns = [
        r"total\s+(?:a\s+)?(?:pagar|factura)[:\s]*(\d+[.,]?\d*)\s*€?",
        r"total[:\s]*(\d+[.,]?\d*)\s*€",
    ]
    for pattern in total_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"   ✓ {matches}")
            break
    
    # 8. Impuesto eléctrico
    print(f"\n8️⃣ IMPUESTO ELÉCTRICO (€):")
    ie_patterns = [
        r"impuesto\s+(?:sobre\s+la\s+)?electricidad[:\s]*(\d+[.,]?\d*)\s*€?",
        r"impuesto\s+el[ée]ctrico[:\s]*(\d+[.,]?\d*)\s*€?",
    ]
    for pattern in ie_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"   ✓ {matches}")
            break
    else:
        print(f"   ⚠️  No encontrado (puede estar en línea diferente)")
    
    # 9. Alquiler contador
    print(f"\n9️⃣ ALQUILER CONTADOR (€):")
    alq_patterns = [
        r"alquiler\s+(?:de\s+)?(?:equipo|contador)[:\s]*(\d+[.,]?\d*)\s*€?",
        r"equipo[s]?\s+de\s+medida[:\s]*(\d+[.,]?\d*)\s*€?",
    ]
    for pattern in alq_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"   ✓ {matches}")
            break
    else:
        print(f"   ⚠️  No encontrado")
    
    # 10. Consumos por periodo (P1, P2, P3)
    print(f"\n🔟 CONSUMOS POR PERIODO (P1/P2/P3 kWh):")
    print("   Buscando en texto...")
    consumo_periodo_lines = []
    for i, line in enumerate(lines):
        if re.search(r"\b(p[1-6]|punta|llano|valle)\b.*?\d+.*?kwh", line, re.IGNORECASE):
            consumo_periodo_lines.append((i+1, line))
    
    if consumo_periodo_lines:
        for num, line in consumo_periodo_lines[:10]:
            print(f"   Línea {num:3}: {line}")
    else:
        print(f"   ❌ No encontrado patrón claro")

# Analizar todas
for nombre, path in FACTURAS.items():
    extract_manual_data(path, nombre)

print(f"\n\n{'='*100}")
print(f"CONCLUSION: Revisar cada campo y crear estrategias especificas")
print(f"{'='*100}")
