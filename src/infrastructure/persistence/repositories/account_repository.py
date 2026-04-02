"""
Repositorio SQLAlchemy para Cuentas.

"""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.application.ports import AbstractAccountRepository
from src.domain.models import Account, AccountSearchCriteria, AccountType
from src.domain.value_objects import Money
from src.infrastructure.persistence.models import AccountModel, TransactionEntryModel


class SQLAlchemyAccountRepository(AbstractAccountRepository):
    def __init__(self, session: Session):
        self.session = session

    # ─────────────────────────────────────
    # Mapper: ORM → Entidad de dominio
    # ─────────────────────────────────────

    def _to_domain(self, model: AccountModel) -> Account:
        """
        Convierte un registro de BD a una entidad de dominio.
        El current_balance se lee desde la columna desnormalizada.
        """
        return Account(
            id=UUID(model.id),
            name=model.name,
            type=AccountType[model.type],
            initial_balance=Money(
                Decimal(str(model.initial_balance)),
                model.initial_balance_currency,
            ),
            current_balance=Money(
                Decimal(str(model.current_balance)),
                model.current_balance_currency,
            ),
            is_active=bool(model.is_active),
            account_number=model.account_number,
            parent_account_id=UUID(model.parent_account_id) if model.parent_account_id else None,
        )

    # ─────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────

    def add(self, account: Account) -> None:
        model = AccountModel(
            id=str(account.id),
            name=account.name,
            type=account.type.name,
            initial_balance=account.initial_balance.amount,
            initial_balance_currency=account.initial_balance.currency,
            current_balance=account.current_balance.amount,
            current_balance_currency=account.current_balance.currency,
            is_active=int(account.is_active),
            account_number=account.account_number,
            parent_account_id=str(account.parent_account_id) if account.parent_account_id else None,
        )
        self.session.add(model)

    def get(self, account_id: UUID) -> Optional[Account]:
        model = self.session.query(AccountModel).filter_by(id=str(account_id)).first()
        return self._to_domain(model) if model else None

    def get_by_name_and_type(self, name: str, account_type: AccountType) -> Optional[Account]:
        model = self.session.query(AccountModel).filter_by(name=name, type=account_type.name).first()
        return self._to_domain(model) if model else None

    def list(self) -> List[Account]:
        return [self._to_domain(m) for m in self.session.query(AccountModel).all()]

    def update(self, account: Account) -> None:
        model = self.session.query(AccountModel).filter_by(id=str(account.id)).first()
        if not model:
            return
        model.name                   = account.name
        model.type                   = account.type.name
        model.is_active              = int(account.is_active)
        model.account_number         = account.account_number
        model.parent_account_id      = str(account.parent_account_id) if account.parent_account_id else None
        # Persistir saldo actual (corrección del bug)
        model.current_balance          = account.current_balance.amount
        model.current_balance_currency = account.current_balance.currency

    def delete(self, account_id: UUID) -> None:
        self.session.query(AccountModel).filter_by(id=str(account_id)).delete()

    # ─────────────────────────────────────
    # Búsqueda con filtros
    # ─────────────────────────────────────

    def search(self, criteria: AccountSearchCriteria) -> List[Account]:
        query = self.session.query(AccountModel)

        if criteria.type:
            query = query.filter(AccountModel.type == criteria.type.name)
        if criteria.parent_id:
            query = query.filter(AccountModel.parent_account_id == str(criteria.parent_id))
        if criteria.is_active is not None:
            query = query.filter(AccountModel.is_active == int(criteria.is_active))
        if criteria.name_contains:
            query = query.filter(AccountModel.name.ilike(f"%{criteria.name_contains}%"))

        return [self._to_domain(m) for m in query.order_by(AccountModel.name).all()]

    # ─────────────────────────────────────
    # Saldo calculado desde BD (fuente de verdad)
    # ─────────────────────────────────────

    def get_balance(self, account_id: UUID) -> Money:
        """
        Calcula el saldo real sumando initial_balance + todos los apuntes.
        Útil para verificar consistencia o recalcular tras importaciones.
        """
        model = self.session.query(AccountModel).filter_by(id=str(account_id)).first()
        if not model:
            return Money(Decimal("0.00"))

        initial  = Decimal(str(model.initial_balance))
        currency = model.initial_balance_currency

        total_entries = (
            self.session
            .query(func.sum(TransactionEntryModel.amount))
            .filter(TransactionEntryModel.account_id == str(account_id))
            .scalar()
        ) or Decimal("0.00")

        return Money(initial + Decimal(str(total_entries)), currency)