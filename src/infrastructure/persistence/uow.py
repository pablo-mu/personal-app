"""
Implementación SQLAlchemy del patrón Unit of Work.
 
Abre una sesión de BD al entrar al bloque `with` y la cierra al salir.
Si ocurre cualquier excepción, hace rollback automáticamente.
"""
 
from sqlalchemy.orm import Session
 
from src.application.ports import AbstractUnitOfWork
from src.infrastructure.persistence.db import SessionLocal
from src.infrastructure.persistence.repositories.account_repository import SQLAlchemyAccountRepository
from src.infrastructure.persistence.repositories.transaction_repository import SQLAlchemyTransactionRepository
from src.infrastructure.persistence.repositories.tag_repository import SQLAlchemyTagRepository
from src.infrastructure.persistence.repositories.recurring_rule_repository import SQLAlchemyRecurringRuleRepository
 
 
class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self.session: Session | None = None
 
    def __enter__(self):
        self.session   = self.session_factory()
        self.accounts  = SQLAlchemyAccountRepository(self.session)
        self.transactions = SQLAlchemyTransactionRepository(self.session)
        self.tags      = SQLAlchemyTagRepository(self.session)
        self.recurring_rules = SQLAlchemyRecurringRuleRepository(self.session)
        return super().__enter__()
 
    def __exit__(self, *args):
        super().__exit__(*args)
        self.session_factory.remove()
 
    def commit(self):
        self.session.commit()
 
    def rollback(self):
        self.session.rollback()
 