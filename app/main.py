import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos rutas
from app.routes.webhook import router as webhook_router
from app.routes.clientes import router as clientes_router
from app.routes.debug import router as debug_router
from app.routes.comisiones import router as comisiones_router  # ⭐ Carga masiva de comisiones

from app.db.conn import Base, engine
from app.db import models
# P1 FIX: Importar explícitamente para registrar en SQLAlchemy
from app.db.models import Factura, Cliente, Comparativa

app = FastAPI(
    title="RapidEnergy API",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    import os
    db_url = os.getenv("DATABASE_URL", "")
    masked_url = "SQLite/Local"
    if "@" in db_url:
        masked_url = db_url.split("@")[1]
    print(f"🚀 [STARTUP] Conectado a BD: {masked_url}")

# Inicializar Base de Datos (crear tablas)
Base.metadata.create_all(bind=engine)

# CORS Configuration
# Cargamos orígenes desde ENV para no tener que tocar código la próxima vez
origins_env = os.getenv("ALLOWED_ORIGINS", "")
extra_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

allow_origins = [
    "http://localhost:3000",
    "https://energy.rodorte.com",  # Dominio Producción
    "https://rapid-energy-iwdtwxqzr-ismaelz001s-projects.vercel.app", # Preview específica
]

# Unimos todo eliminando duplicados
total_origins = list(set(allow_origins + extra_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=total_origins,
    # El regex permite cualquier subdominio de Vercel para que las Previews nunca fallen
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "Hello": "World",
        "version": "1.1.0 (Strict Regex + Gemini Support)",
        "python": "3.11.9",
        "gemini_configured": "YES" if os.getenv("GEMINI_API_KEY") else "NO"
    }

@app.get("/debug/gemini")
def debug_gemini():
    import google.generativeai as genai
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return {"status": "MISSING_KEY"}
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Intentar listar para ver qué hay si falla
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        response = model.generate_content("Say 'OK'")
        return {
            "status": "SUCCESS", 
            "response": response.text,
            "available_models": available_models
        }
    except Exception as e:
        # Intentar listar incluso si falla la generación
        available = []
        try:
            for m in genai.list_models():
                available.append(m.name)
        except:
             pass
        return {"status": "ERROR", "detail": str(e), "available": available}

# Incluimos las rutas
app.include_router(webhook_router)
app.include_router(clientes_router)
app.include_router(debug_router)
app.include_router(comisiones_router)  # ⭐ Comisiones

