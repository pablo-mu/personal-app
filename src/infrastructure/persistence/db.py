"""
Configuración de la conexión a base de datos (SQLAlchemy).
La URL se lee desde Settings para facilitar el cambio de SQLite → PostgreSQL.
"""
 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
 
from src.config import settings
 
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
 
class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""
    pass
 
 
def get_db():
    """Generador de sesión para FastAPI (si se necesita en el futuro)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 