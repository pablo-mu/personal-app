"""
Define los puertos (interfaces) de la aplicación.

CONCEPTOS CLAVE:
----------------
1. REPOSITORIO (The Drawer/Cajón):
   Abstrae el almacenamiento. Para la aplicación, guardar un dato es como meterlo
   en un cajón. No le importa si el cajón es de madera (Memoria), metal (SQLite)
   o está en la nube (PostgreSQL). Es decir, define qué operaciones existen, no 
   cómo se implementan. 

2. UNIT OF WORK (The Save Button/Botón Maestro):
   Maneja la "Atomicidad". Si tienes que hacer 3 cosas (restar dinero, sumar dinero,
   guardar registro), la UoW asegura que se hagan las 3 o ninguna. Evita datos corruptos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Tuple
from uuid import UUID
 
from src.domain.models import (
    Account,
    AccountSearchCriteria,
    AccountType,
    Transaction,
    TransactionSearchCriteria,
)
 

class AbstractRepository(ABC):
    """
    Interfaz genérica para cualquier "colección" de objetos.
    Define las operaciones básicas CRUD (Create, Read, Update, Delete) sin implementación.
    """
    @abstractmethod
    def add(self, entity: Any) -> None:
        """Añade una entidad nueva al repositorio (pero no la guarda en DB hasta el commit)."""
        pass

    @abstractmethod
    def get(self, entity_id: UUID) -> Optional[Any]:
        """Busca una entidad por su ID único."""
        pass

    @abstractmethod
    def list(self) -> List[Any]:
        """Devuelve todas las entidades disponibles."""
        pass

    @abstractmethod
    def update(self, entity: Any) -> None:
        """Actualiza una entidad existente."""
        pass

    @abstractmethod
    def delete(self, entity_id: UUID) -> None:
        """Elimina una entidad por su ID."""
        pass


class AbstractAccountRepository(AbstractRepository):
    """Puerto específico para gestionar Cuentas (Accounts)."""
    @abstractmethod
    def get_by_name_and_type(self, name: str, type: AccountType) -> Optional[Any]:
        """Busca una cuenta por nombre y tipo."""
        pass

    @abstractmethod
    def search(self, criteria: AccountSearchCriteria) -> List[Account]:
        """Busca cuentas según los criterios de búsqueda del dominio."""
        pass

    @abstractmethod
    def get_balance(self, account_id: UUID) -> Any:
        """Calcula el saldo actual de la cuenta."""
        pass
class AbstractTransactionRepository(AbstractRepository):
    """Puerto específico para gestionar Transacciones (Transactions)."""

    @abstractmethod
    def search(
        self,
        criteria: TransactionSearchCriteria,
    ) -> Tuple[List[Transaction], int]:
        """
        Busca transacciones con filtros y paginación.
        Devuelve (lista_de_transacciones, total_sin_paginar).
        """
        pass

    @abstractmethod
    def count_by_account(self, account_id: UUID) -> int:
        """Cuenta cuántas transacciones afectan a una cuenta específica."""
        pass

class AbstractTagRepository(AbstractRepository):
    """Puerto específico para gestionar Etiquetas (Tags)."""
    pass

class AbstractRecurringRuleRepository(AbstractRepository):
    """Puerto específico para gestionar Reglas Recurrentes (RecurringRules)."""
    @abstractmethod
    def get_active_rules(self) -> List[Any]:
        """Obtiene todas las reglas activas."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Any]:
        """Obtiene todas las reglas (activas e inactivas)."""
        pass

class AbstractUnitOfWork(ABC):
    """
    El patrón Unit of Work (Unidad de Trabajo).
    
    Actúa como un gestor de transacciones de base de datos. Mantiene una lista de
    objetos nuevos, modificados o eliminados y los envía a la base de datos todos
    juntos cuando se llama a `commit()`.

    Uso típico con 'context manager' (with):
    ---------------------------------------
    with uow:
        uow.accounts.add(cuenta_nueva)
        uow.transactions.add(transaccion_nueva)
        uow.commit()  # <- Aquí se guarda todo de golpe.
    # Si hay un error dentro del 'with', se ejecuta rollback() automáticamente.
    """
    
    accounts: AbstractAccountRepository
    transactions: AbstractTransactionRepository
    tags: AbstractTagRepository
    recurring_rules: AbstractRecurringRuleRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        """Inicia el bloque 'with'. Prepara la sesión."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Cierra el bloque 'with'.
        Si hubo una excepción (error), hace rollback automáticamente.
        """
        if exc_type is not None:
            self.rollback()

    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def rollback(self) -> None:
        pass