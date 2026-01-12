import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos rutas
from app.routes.webhook import router as webhook_router
from app.routes.clientes import router as clientes_router
from app.routes.debug import router as debug_router

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
# CORS Configuration
# Usamos regex para permitir Vercel previews y cualquier subdominio
# allow_origin_regex permite:
# - http://localhost:3000 (local)
# - https://*.vercel.app (previews)
# - https://*.rodorte.com (producción)
# - De hecho, permitimos CUALQUIER https:// para máxima compatibilidad si es una API pública.

# CORS Configuration (FIX: permitir dominios Vercel explícitamente)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://rapid-energy-iwdtwxqzr-ismaelz001s-projects.vercel.app",
        "https://*.vercel.app",  # Previews
    ],
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+",
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
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say 'OK'")
        return {"status": "SUCCESS", "response": response.text}
    except Exception as e:
        return {"status": "ERROR", "detail": str(e)}

# Incluimos las rutas
app.include_router(webhook_router)
app.include_router(clientes_router)
app.include_router(debug_router)

