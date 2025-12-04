from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session

from src.application.ports import AbstractAccountRepository
from src.domain.models import Account, AccountType
from src.domain.value_objects import Money
from src.infrastructure.persistence.models import AccountModel

class SQLAlchemyAccountRepository(AbstractAccountRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account) -> None:
        account_model = AccountModel(
            id=str(account.id),
            name=account.name,
            type=account.type.name,
            initial_balance=account.initial_balance.amount,
            initial_balance_currency=account.initial_balance.currency
        )
        self.session.add(account_model)

    def get(self, account_id: UUID) -> Optional[Account]:
        model = self.session.query(AccountModel).filter_by(id=str(account_id)).first()
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
            initial_balance=Money(Decimal(model.initial_balance), model.initial_balance_currency)
        )
