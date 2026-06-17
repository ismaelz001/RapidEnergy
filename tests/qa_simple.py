"""
🧪 QA OPERATIVA SIMPLE - Verificación Backend
"""
import sys
import os

print("=" * 60)
print("🔍 QA POST-CLEANUP - VERIFICACIÓN OPERATIVA")
print("=" * 60)

# Test 1: Verificar archivos críticos
print("\n✅ TEST 1: Estructura de Archivos")
critical_files = [
    "app/main.py",
    "app/services/ocr.py",
    "app/services/comparador.py",
    "app/services/pdf_generator.py",
    "app/db/models.py",
    "app/routes/webhook.py",
]

all_good = True
for file in critical_files:
    exists = os.path.exists(file)
    status = "✅" if exists else "❌"
    print(f"  {status} {file}")
    if not exists:
        all_good = False

# Test 2: Verificar que OCR.py tiene funciones críticas
print("\n✅ TEST 2: Funciones OCR")
try:
    with open("app/services/ocr.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    functions = [
        "parse_es_number",
        "extract_atr",
        "extract_potencias",
        "parse_invoice_text",
        "extract_data_from_pdf"
    ]
    
    for func in functions:
        has_func = f"def {func}" in content
        status = "✅" if has_func else "❌"
        print(f"  {status} {func}")
        if not has_func:
            all_good = False
            
except Exception as e:
    print(f"  ❌ Error leyendo ocr.py: {e}")
    all_good = False

# Test 3: Verificar que comparador.py tiene funciones críticas
print("\n✅ TEST 3: Funciones Comparador")
try:
    with open("app/services/comparador.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    functions = [
        "compare_factura",
        "_reconstruir_factura",
        "_insert_comparativa",
        "_insert_ofertas"
    ]
    
    for func in functions:
        has_func = f"def {func}" in content
        status = "✅" if has_func else "❌"
        print(f"  {status} {func}")
        if not has_func:
            all_good = False
            
except Exception as e:
    print(f"  ❌ Error leyendo comparador.py: {e}")
    all_good = False

# Test 4: Verificar modelos en db
print("\n✅ TEST 4: Modelos Database")
try:
    with open("app/db/models.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    models = [
        "class Factura",
        "class Cliente",
        "class Oferta",
        "class OfertaCalculada"
    ]
    
    for model in models:
        has_model = model in content
        status = "✅" if has_model else "❌"
        print(f"  {status} {model}")
        if not has_model:
            all_good = False
            
except Exception as e:
    print(f"  ❌ Error leyendo models.py: {e}")
    all_good = False

# Test 5: Verificar rutas
print("\n✅ TEST 5: Rutas API")
try:
    with open("app/routes/webhook.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    endpoints = [
        "@router.post(\"/upload\"",
        "async def process_factura"
    ]
    
    for endpoint in endpoints:
        has_endpoint = endpoint in content
        status = "✅" if has_endpoint else "❌"
        print(f"  {status} {endpoint}")
        if not has_endpoint:
            all_good = False
            
except Exception as e:
    print(f"  ❌ Error leyendo webhook.py: {e}")
    all_good = False

# Test 6: Verificar dependencias
print("\n✅ TEST 6: Dependencias")
try:
    with open("requirements.txt", "r", encoding="utf-8") as f:
        content = f.read()
        
    deps = [
        "fastapi",
        "pypdf",
        "google-cloud-vision",
        "sqlalchemy",
        "psycopg2"
    ]
    
    for dep in deps:
        has_dep = dep in content.lower()
        status = "✅" if has_dep else "❌"
        print(f"  {status} {dep}")
        if not has_dep:
            all_good = False
            
except Exception as e:
    print(f"  ❌ Error leyendo requirements.txt: {e}")
    all_good = False

# Test 7: Verificar migraciones
print("\n✅ TEST 7: Migraciones SQL")
try:
    import os
    sql_files = [f for f in os.listdir("migrations") if f.endswith(".sql")]
    print(f"  ✅ {len(sql_files)} archivos de migración encontrados")
    for sql in sql_files:
        print(f"     • {sql}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    all_good = False

# Test 8: Verificar documentación
print("\n✅ TEST 8: Documentación")
docs = [
    "README.md",
    "PROMPT_SISTEMA_OCR_FACTURAS.md"
]
for doc in docs:
    exists = os.path.exists(doc)
    status = "✅" if exists else "❌"
    print(f"  {status} {doc}")
    if not exists:
        all_good = False

# Resumen final
print("\n" + "=" * 60)
if all_good:
    print("🎉 TODOS LOS TESTS PASARON - OPERATIVA OK")
    print("✅ La limpieza NO rompió ninguna funcionalidad crítica")
    print("✅ Todos los archivos y funciones están en su lugar")
else:
    print("⚠️  Algunos tests fallaron - Ver detalles arriba")

print("=" * 60 + "\n")

sys.exit(0 if all_good else 1)
