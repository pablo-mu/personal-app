import sys
import os
from flask import Flask

# Añadimos el directorio raíz al path para que Python encuentre los módulos 'src'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.persistence.db import engine, Base
# Importamos los modelos para asegurarnos de que SQLAlchemy los registre antes de crear las tablas
from src.infrastructure.persistence.models import AccountModel, TransactionModel, TagModel, TransactionEntryModel
from src.infrastructure.persistence.uow import SQLAlchemyUnitOfWork
from src.application.services import AccountService, TransactionService, TagService
from src.application.container import Services
from src.ui.app import init_dashboard

def create_tables():
    """Crea las tablas en la base de datos si no existen."""
    print("🛠️  Verificando tablas de base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas listas.")

def main():
    # 1. Inicialización de Infraestructura
    create_tables()
    
    # 2. Inyección de Dependencias
    uow = SQLAlchemyUnitOfWork()
    
    # Creamos el contenedor de servicios
    services = Services(
        account=AccountService(uow),
        transaction=TransactionService(uow),
        tag=TagService(uow)
    )
    
    # 3. Configuración del Servidor Web (Flask)
    server = Flask(__name__)
    
    # Inicializamos Dash con la instancia de Flask
    app = init_dashboard(server, services)
    
    print("🚀 Servidor arrancando en http://127.0.0.1:8050/")
    # Dash corre por defecto en el puerto 8050
    app.run(debug=True, host="127.0.0.1", port=8050)

if __name__ == "__main__":
    main()
