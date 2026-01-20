import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Carga variables del archivo .env
load_dotenv()

# Lee DATABASE_URL desde variables de entorno (usa Neon en tu caso)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pass@localhost:5432/energy"  # valor por defecto por si falta
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Verifica la conexión antes de usarla
    pool_recycle=300,        # Recicla conexiones cada 5 minutos
    pool_size=5,             # Tamaño base del pool
    max_overflow=10,         # Conexiones extra permitidas en picos
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
