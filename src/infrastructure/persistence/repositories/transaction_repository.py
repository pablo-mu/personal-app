from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.application.ports import AbstractTransactionRepository
from src.domain.models import Transaction, TransactionEntry
from src.domain.value_objects import Money
from src.infrastructure.persistence.models import TransactionModel, TagModel, TransactionEntryModel

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
        if transaction.tags_ids:
            # Buscamos los modelos de tags existentes para relacionarlos
            tags = self.session.query(TagModel).filter(TagModel.id.in_([str(t) for t in transaction.tags_ids])).all()
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
        return self._to_domain(model)
    
    def delete(self, transaction_id: str) -> None:
        # En SQLAlchemy con cascade="all, delete-orphan", eliminar el padre debería eliminar los hijos (entries).
        # Tags es many-to-many, solo se elimina la relación en la tabla association.
        tx_model = self.session.query(TransactionModel).filter_by(id=str(transaction_id)).first()
        if tx_model:
            self.session.delete(tx_model)

    def list(self) -> List[Transaction]:
        models = self.session.query(TransactionModel).all()
        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: TransactionModel) -> Transaction:
        """
        Método helper (Factory/Mapper) para convertir modelo DB -> Entidad Dominio.
        Centraliza la lógica de reconstrucción.
        """
        entries = [
            TransactionEntry(
                account_id=UUID(e.account_id),
                amount=Money(e.amount, e.currency)
            ) for e in model.entries
        ]
        tag_ids = [UUID(t.id) for t in model.tags]

        return Transaction(
            id=UUID(model.id),
            date=model.date,
            description=model.description,
            entries=entries,
            related_transaction_id=UUID(model.related_transaction_id) if model.related_transaction_id else None,
            tags_ids=tag_ids
        )

    def count_by_account(self, account_id: UUID) -> int:
        return self.session.query(TransactionEntryModel).filter(TransactionEntryModel.account_id == str(account_id)).count()

    def update(self, transaction: Transaction) -> None:
        model = self.session.query(TransactionModel).filter_by(id=str(transaction.id)).first()
        if model:
            # 1. Actualizar campos simples
            model.description = transaction.description
            model.date = transaction.date
            model.related_transaction_id = str(transaction.related_transaction_id) if transaction.related_transaction_id else None

            # 2. Gestionar Etiquetas (Reemplazo total)
            if transaction.tags_ids is not None:
                model.tags = [] # Limpiar
                tags = self.session.query(TagModel).filter(TagModel.id.in_([str(t) for t in transaction.tags_ids])).all()
                model.tags = tags

            # 3. Gestionar Entradas (Reemplazo total: Borrar viejas, crear nuevas)
            # SQLAlchemy debería borrar las entries viejas si la cascada está configurada.
            # Si no, las borramos manualmente.
            self.session.query(TransactionEntryModel).filter_by(transaction_id=str(transaction.id)).delete()
            
            new_entries = []
            for entry in transaction.entries:
                entry_model = TransactionEntryModel(
                    transaction_id=str(transaction.id),
                    account_id=str(entry.account_id),
                    amount=entry.amount.amount,
                    currency=entry.amount.currency
                )
                new_entries.append(entry_model)
            
            model.entries = new_entries
            model.date = transaction.date
            model.description = transaction.description
            model.related_transaction_id = str(transaction.related_transaction_id) if transaction.related_transaction_id else None
            # TODO: Actualizar tags y entries si es necesario

    def delete(self, transaction_id: UUID) -> None:
        self.session.query(TransactionModel).filter_by(id=str(transaction_id)).delete()
