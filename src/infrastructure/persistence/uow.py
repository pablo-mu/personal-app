from sqlalchemy.orm import sessionmaker, Session
from src.application.ports import AbstractUnitOfWork
from .db import SessionLocal # La factoría que creamos antes
from .repositories import (
    SQLAlchemyAccountRepository, 
    SQLAlchemyTransactionRepository, 
    SQLAlchemyTagRepository,
    SQLAlchemyRecurringRuleRepository
)

class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    Implementación concreta de la Unit of Work usando SQLAlchemy.
    """

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self.session: Session = None

    def __enter__(self):
        # 1. Abrimos una sesión nueva de base de datos
        self.session = self.session_factory()
        
        # 2. Instanciamos los repositorios pasándoles esa sesión
        # Así todos comparten la misma transacción de DB
        self.accounts = SQLAlchemyAccountRepository(self.session)
        self.transactions = SQLAlchemyTransactionRepository(self.session)
        self.tags = SQLAlchemyTagRepository(self.session)
        self.recurring_rules = SQLAlchemyRecurringRuleRepository(self.session)
        
        # Devolvemos self para que el 'with' funcione
        return super().__enter__()

    def __exit__(self, *args):
        # Cerramos la sesión al terminar el bloque 'with'
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        # Confirmamos los cambios en la base de datos real
        self.session.commit()

    def rollback(self):
        # Deshacemos cambios en caso de error
        self.session.rollback()