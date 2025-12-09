from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session

from src.application.ports import AbstractAccountRepository
from src.domain.models import Account, AccountType, AccountSearchCriteria
from src.domain.value_objects import Money
from sqlalchemy import func
from src.infrastructure.persistence.models import AccountModel, TransactionEntryModel

class SQLAlchemyAccountRepository(AbstractAccountRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account) -> None:
        account_model = AccountModel(
            id=str(account.id),
            name=account.name,
            type=account.type.name,
            initial_balance=account.initial_balance.amount,
            initial_balance_currency=account.initial_balance.currency,
            is_active=account.is_active,
            parent_account_id=str(account.parent_account_id) if account.parent_account_id else None,
            account_number=account.account_number
        )
        self.session.add(account_model)

    def get(self, account_id: UUID) -> Optional[Account]:
        model = self.session.query(AccountModel).filter_by(id=str(account_id)).first()
        if not model:
            return None
        return self._to_domain(model)

    def get_by_name_and_type(self, name: str, type: AccountType) -> Optional[Account]:
        model = self.session.query(AccountModel).filter_by(name=name, type=type.name).first()
        if not model:
            return None
        return self._to_domain(model)
    
    def list(self) -> List[Account]:
        models = self.session.query(AccountModel).all()
        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: AccountModel) -> Account:
        """
        Método helper (Factory/Mapper) para convertir modelo DB -> Entidad Dominio.
        """
        return Account(
            id=UUID(model.id),
            name=model.name,
            type=AccountType[model.type],
            initial_balance=Money(Decimal(model.initial_balance), model.initial_balance_currency),
            is_active=bool(model.is_active),
            parent_account_id=UUID(model.parent_account_id) if model.parent_account_id else None,
            account_number=model.account_number
        )
    
    def search(self, criteria: AccountSearchCriteria) -> List[Account]:
        query = self.session.query(AccountModel)

        if criteria.type:
            query = query.filter(AccountModel.type == criteria.type.name)
        
        if criteria.parent_id:
            query = query.filter(AccountModel.parent_account_id == str(criteria.parent_id))
            
        if criteria.is_active is not None:
            query = query.filter(AccountModel.is_active == criteria.is_active)

        if criteria.name_contains:
            query = query.filter(AccountModel.name.ilike(f"%{criteria.name_contains}%"))

        return [self._to_domain(model) for model in query.all()]

    def update(self, account: Account) -> None:
        model = self.session.query(AccountModel).filter_by(id=str(account.id)).first()
        if model:
            model.name = account.name
            model.type = account.type.name
            model.is_active = account.is_active
            model.account_number = account.account_number
            model.parent_account_id = str(account.parent_account_id) if account.parent_account_id else None
            # Nota: No actualizamos el balance inicial normalmente, pero si se requiere, se añade aquí.

    def delete(self, account_id: UUID) -> None:
        self.session.query(AccountModel).filter_by(id=str(account_id)).delete()

    def get_balance(self, account_id: UUID) -> Money:
        """
        Calcula el saldo actual sumando el balance inicial + todas las transacciones.
        """
        # 1. Obtener balance inicial
        account_model = self.session.query(AccountModel).filter_by(id=str(account_id)).first()
        if not account_model:
            return Money(Decimal('0.00'))
            
        initial_balance = Decimal(account_model.initial_balance)
        currency = account_model.initial_balance_currency

        # 2. Sumar transacciones
        # SELECT SUM(amount) FROM transaction_entries WHERE account_id = :id
        total_transactions = self.session.query(func.sum(TransactionEntryModel.amount))\
            .filter(TransactionEntryModel.account_id == str(account_id))\
            .scalar() or Decimal('0.00')

        return Money(initial_balance + total_transactions, currency)
