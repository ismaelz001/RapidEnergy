from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos rutas
from app.routes.webhook import router as webhook_router

app = FastAPI(
    title="RapidEnergy API",
    version="1.0.0"
)

# CORS (permitimos requests desde Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "RapidEnergy API", "version": "1.0.0"}

# Incluimos las rutas
app.include_router(webhook_router)
