"""
Análisis de TODAS las facturas en temp_facturas para identificar patrones
"""
import pypdf
import io
import os
import re

FACTURAS = [
    "temp_facturas/Factura Iberdrola.pdf",
    "temp_facturas/factura Naturgy.pdf",
    "temp_facturas/Factura.pdf",
    "temp_facturas/Fra Agosto.pdf"
]

def analyze_invoice(pdf_path):
    print(f"\n{'='*100}")
    print(f"📄 ARCHIVO: {pdf_path}")
    print(f"{'='*100}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ No encontrado")
        return
    
    with open(pdf_path, 'rb') as f:
        reader = pypdf.PdfReader(io.BytesIO(f.read()))
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    lines = [ln.strip() for ln in full_text.split('\n') if ln.strip()]
    
    # Mostrar primeras 30 líneas
    print(f"\n📋 PRIMERAS 30 LÍNEAS:")
    print("-" * 100)
    for i, line in enumerate(lines[:30], 1):
        print(f"{i:3}. {line}")
    
    # Identificar comercializadora
    print(f"\n🏢 COMERCIALIZADORA DETECTADA:")
    print("-" * 100)
    comercializadoras = {
        'Iberdrola': 'IBERDROLA',
        'Naturgy': 'NATURGY',
        'Endesa': 'ENDESA',
        'Repsol': 'REPSOL',
        'TotalEnergies': 'TOTALENERGIES'
    }
    
    comercializadora_detectada = None
    for nombre, keyword in comercializadoras.items():
        if keyword in full_text.upper()[:500]:
            comercializadora_detectada = nombre
            print(f"✓ {nombre}")
            break
    
    if not comercializadora_detectada:
        print("⚠️ No detectada - Buscar manualmente")
    
    # Buscar candidatos a titular (nombres en mayúsculas)
    print(f"\n👤 CANDIDATOS A TITULAR (nombres en mayúsculas, 2+ palabras):")
    print("-" * 100)
    found_names = []
    for i, line in enumerate(lines[:50], 1):
        # Patrón: Línea con 2-5 palabras, todas en mayúsculas
        if re.match(r'^[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ ,.\'\-]{10,80}$', line):
            # Filtrar keywords obvias
            if not any(k in line.upper() for k in ['IBERDROLA', 'NATURGY', 'ENDESA', 'REPSOL', 
                                                      'FACTURA', 'ELECTRICIDAD', 'CIF', 'MERCANTIL',
                                                      'REGISTRO', 'MADRID', 'BARCELONA', 'INSCRITA']):
                found_names.append((i, line))
                print(f"   Línea {i:3}: {line}")
    
    # Buscar patrón "Titular:"
    print(f"\n🎯 PATRÓN 'Titular:' o similar:")
    print("-" * 100)
    titular_pattern = re.search(r"(?:titular|nombre\s+del\s+titular|cliente|nombre\s+y\s+apellidos)[:\s]+([A-ZÁÉÍÓÚÜÑ][A-Za-záéíóúüñ ,.\'\-]{10,80})", full_text, re.IGNORECASE)
    if titular_pattern:
        print(f"   ✓ Encontrado: {titular_pattern.group(1).strip()}")
    else:
        print(f"   ❌ No encontrado")
    
    # Buscar CUPS para contexto
    print(f"\n🔌 CUPS:")
    print("-" * 100)
    cups_match = re.search(r"(ES[\s\-]*\d{4}[\s\-]*\d{4}[\s\-]*\d{4}[\s\-]*\d{4}[\s\-]*[A-Z]{2})", full_text, re.IGNORECASE)
    if cups_match:
        print(f"   ✓ {cups_match.group(0)}")
    else:
        print(f"   ❌ No encontrado")
    
    # CONCLUSIÓN
    print(f"\n💡 RECOMENDACIÓN PARA ESTA FACTURA:")
    print("-" * 100)
    if found_names:
        print(f"   • MEJOR CANDIDATO: Línea {found_names[0][0]} → '{found_names[0][1]}'")
        print(f"   • ALTERNATIVAS: {len(found_names)-1} más encontradas")
    else:
        print(f"   ⚠️ No se encontraron candidatos obvios - necesita regex más flexible")

# Analizar todas
for pdf in FACTURAS:
    analyze_invoice(pdf)

print(f"\n\n{'='*100}")
print(f"📊 RESUMEN Y ESTRATEGIA RECOMENDADA")
print(f"{'='*100}")
print("""
OBSERVACIONES:
1. Cada comercializadora tiene formato diferente
2. El titular SIEMPRE está en las primeras 5-15 líneas
3. No todas tienen 'Titular:' o 'DATOS DEL CONTRATO'
4. El nombre SIEMPRE está:
   - En MAYÚSCULAS (a veces con acentos minúsculas)
   - 2-5 palabras
   - ANTES de la dirección
   - DESPUÉS del logo/CIF de la empresa

ESTRATEGIA ROBUSTA:
1. Ignorar primeras 1-2 líneas (suelen ser códigos/referencias)
2. Buscar en líneas 2-15 nombres válidos (mayúsculas, 2+ palabras)
3. Aplicar filtro ESTRICTO de keywords (empresas, legal, técnico)
4. Si hay múltiples candidatos, tomar el PRIMERO que pase filtros
5. Validación cruzada: Debe estar ANTES de dirección (números+letras)
""")
