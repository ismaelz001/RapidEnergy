from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos rutas
from app.routes.webhook import router as webhook_router
from app.routes.clientes import router as clientes_router

from app.db.conn import Base, engine
from app.db import models

app = FastAPI(
    title="RapidEnergy API",
    version="1.0.0"
)

# Inicializar Base de Datos (crear tablas)
Base.metadata.create_all(bind=engine)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "https://energy.rodorte.com",
    "https://www.energy.rodorte.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "RapidEnergy API", "version": "1.0.0"}

# Incluimos las rutas
app.include_router(webhook_router)
app.include_router(clientes_router)
