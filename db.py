import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# =====================================
# CONFIGURACIÓN DE CONEXIÓN
# =====================================
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "parametros_alberca"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# =====================================
# MOTOR Y SESIÓN
# =====================================
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
