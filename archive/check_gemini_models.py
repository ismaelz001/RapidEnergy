import os
import google.generativeai as genai

# Configurar API key desde variable de entorno
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ GEMINI_API_KEY no encontrada en variables de entorno")
    print("Configúrala con: export GEMINI_API_KEY='tu-api-key'")
    exit(1)

print(f"✅ API Key encontrada: {api_key[:10]}...")
print("\n🔍 Listando modelos disponibles...\n")

try:
    genai.configure(api_key=api_key)
    
    # Listar todos los modelos
    models = genai.list_models()
    
    print("=" * 80)
    print("MODELOS DISPONIBLES:")
    print("=" * 80)
    
    for model in models:
        print(f"\n📦 {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        print(f"   Supported Methods: {', '.join(model.supported_generation_methods)}")
        
    print("\n" + "=" * 80)
    print("MODELOS RECOMENDADOS PARA OCR:")
    print("=" * 80)
    print("✅ gemini-1.5-flash (rápido, barato)")
    print("✅ gemini-1.5-flash-latest (última versión)")
    print("✅ gemini-1.5-pro (más preciso, más caro)")
    print("✅ gemini-2.0-flash-exp (experimental, gratis)")
    
except Exception as e:
    print(f"❌ Error al conectar con Gemini API:")
    print(f"   {e}")
    print("\n💡 Posibles soluciones:")
    print("   1. Verifica que tu API key sea correcta")
    print("   2. Asegúrate de tener acceso a Gemini API en Google Cloud Console")
    print("   3. Revisa que no haya límites de cuota excedidos")
