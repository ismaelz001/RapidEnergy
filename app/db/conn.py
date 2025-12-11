import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carga variables del archivo .env
load_dotenv()

# Lee DATABASE_URL desde variables de entorno (usa Neon en tu caso)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pass@localhost:5432/energy"  # valor por defecto por si falta
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
