from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session

from src.application.ports import (
    AbstractAccountRepository,
    AbstractTagRepository,
    AbstractTransactionRepository
)

from src.domain.models import Account, Transaction, Tag, TransactionEntry, AccountType
from src.domain.value_objects import Money

from .models import AccountModel, TransactionModel, TagModel, TransactionEntryModel

class SQLAlchemyAccountRepository(AbstractAccountRepository):
    def __init__(self, session: Session):
        self.session = session

    # Implementación de métodos abstractos...
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

        # Mapeo de modelo a entidad de dominio (ORM -> Dominio)
        return Account(
            id=UUID(model.id),
            name=model.name,
            type=AccountType[model.type],
            initial_balance=Money(Decimal(model.initial_balance), model.initial_balance_currency)
        )
    
    def list(self) -> List[Account]:
        models = self.session.query(AccountModel).all()
        return [
            Account(
                id=UUID(model.id),
                name=model.name,
                type=AccountType[model.type],
                initial_balance=Money(Decimal(model.initial_balance), model.initial_balance_currency)
            )
            for model in models
        ]
    
class SQLAlchemyTagRepository(AbstractTagRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, tag: Tag) -> None:
        model = TagModel(
            id=str(tag.id),
            name=tag.name,
            color=tag.color,
            icon=tag.icon
        )
        self.session.add(model)

    def get(self, tag_id: UUID) -> Optional[Tag]:
        model = self.session.query(TagModel).filter_by(id=str(tag_id)).first()
        if not model: 
            return None
        return Tag(id=UUID(model.id), name=model.name, color=model.color, icon=model.icon)

    def list(self) -> List[Tag]:
        models = self.session.query(TagModel).all()
        return [Tag(id=UUID(m.id), name=m.name, color=m.color, icon=m.icon) for m in models]


class SQLAlchemyTransactionRepository(AbstractTransactionRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, transaction: Transaction) -> None:
        # 1. Crear el modelo de la transacción padre
        tx_model = TransactionModel(
            id=str(transaction.id),
            date=transaction.date,
            description=transaction.description,
            related_transaction_id=str(transaction.related_transaction_id) if transaction.related_transaction_id else None
        )

        # 2. Gestionar las etiquetas (Tags)
        if transaction.tag_ids:
            # Buscamos los modelos de tags existentes para relacionarlos
            tags = self.session.query(TagModel).filter(TagModel.id.in_([str(t) for t in transaction.tag_ids])).all()
            tx_model.tags = tags

        # 3. Crear los modelos de las entradas (Entries)
        for entry in transaction.entries:
            entry_model = TransactionEntryModel(
                transaction_id=str(transaction.id),
                account_id=str(entry.account_id),
                amount=entry.amount.amount,
                currency=entry.amount.currency
            )
            # Añadimos a la relación (SQLAlchemy gestiona la FK)
            tx_model.entries.append(entry_model)

        self.session.add(tx_model)

    def get(self, transaction_id: UUID) -> Optional[Transaction]:
        model = self.session.query(TransactionModel).filter_by(id=str(transaction_id)).first()
        if not model:
            return None
        
        # Reconstruir Entradas
        entries = [
            TransactionEntry(
                account_id=UUID(e.account_id),
                amount=Money(e.amount, e.currency)
            ) for e in model.entries
        ]

        # Reconstruir Tags IDs
        tag_ids = [UUID(t.id) for t in model.tags]

        return Transaction(
            id=UUID(model.id),
            date=model.date,
            description=model.description,
            entries=entries,
            related_transaction_id=UUID(model.related_transaction_id) if model.related_transaction_id else None,
            tags_ids=tag_ids
        )
    
    def list(self) -> List[Transaction]:
        models = self.session.query(TransactionModel).all()
        transactions = []
        for model in models:
            entries = [
                TransactionEntry(
                    account_id=UUID(e.account_id),
                    amount=Money(e.amount, e.currency)
                ) for e in model.entries
            ]
            tag_ids = [UUID(t.id) for t in model.tags]

            transaction = Transaction(
                id=UUID(model.id),
                date=model.date,
                description=model.description,
                entries=entries,
                related_transaction_id=UUID(model.related_transaction_id) if model.related_transaction_id else None,
                tags_ids=tag_ids
            )
            transactions.append(transaction)
        return transactions

