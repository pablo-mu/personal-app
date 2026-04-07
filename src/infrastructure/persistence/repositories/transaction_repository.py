"""
Repositorio SQLAlchemy para Transacciones.

Usa EXISTS subqueries para todos los filtros sobre apuntes (entries),
evitando el bug clásico de filtrar source_account_id AND destination_account_id
sobre el mismo JOIN (una fila no puede satisfacer ambas condiciones a la vez).
"""

from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import exists, func
from sqlalchemy.orm import Session

from src.application.ports import AbstractTransactionRepository
from src.domain.models import Transaction, TransactionEntry, TransactionSearchCriteria
from src.domain.value_objects import Money
from src.infrastructure.persistence.models import (
    TagModel,
    TransactionEntryModel,
    TransactionModel,
    transaction_tags,
)


class SQLAlchemyTransactionRepository(AbstractTransactionRepository):
    def __init__(self, session: Session):
        self.session = session

    # ─────────────────────────────────────
    # Mapper: ORM → Entidad de dominio
    # ─────────────────────────────────────

    def _to_domain(self, model: TransactionModel) -> Transaction:
        entries = [
            TransactionEntry(
                account_id=UUID(e.account_id),
                amount=Money(Decimal(str(e.amount)), e.currency),
            )
            for e in model.entries
        ]
        return Transaction(
            id=UUID(model.id),
            date=model.date,
            description=model.description,
            entries=entries,
            related_transaction_id=(
                UUID(model.related_transaction_id) if model.related_transaction_id else None
            ),
            tags_ids=[UUID(t.id) for t in model.tags],
        )

    # ─────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────

    def add(self, transaction: Transaction) -> None:
        model = TransactionModel(
            id=str(transaction.id),
            date=transaction.date,
            description=transaction.description or "",
            related_transaction_id=(
                str(transaction.related_transaction_id)
                if transaction.related_transaction_id else None
            ),
        )
        if transaction.tags_ids:
            model.tags = (
                self.session.query(TagModel)
                .filter(TagModel.id.in_([str(t) for t in transaction.tags_ids]))
                .all()
            )
        for entry in transaction.entries:
            model.entries.append(
                TransactionEntryModel(
                    transaction_id=str(transaction.id),
                    account_id=str(entry.account_id),
                    amount=entry.amount.amount,
                    currency=entry.amount.currency,
                )
            )
        self.session.add(model)

    def get(self, entity_id: UUID) -> Optional[Transaction]:
        model = self.session.query(TransactionModel).filter_by(id=str(entity_id)).first()
        return self._to_domain(model) if model else None

    def list(self) -> List[Transaction]:
        return [
            self._to_domain(m)
            for m in self.session.query(TransactionModel).order_by(TransactionModel.date.desc()).all()
        ]

    def update(self, transaction: Transaction) -> None:
        model = self.session.query(TransactionModel).filter_by(id=str(transaction.id)).first()
        if not model:
            return
        model.description            = transaction.description or ""
        model.date                   = transaction.date
        model.related_transaction_id = (
            str(transaction.related_transaction_id)
            if transaction.related_transaction_id else None
        )
        if transaction.tags_ids is not None:
            model.tags = (
                self.session.query(TagModel)
                .filter(TagModel.id.in_([str(t) for t in transaction.tags_ids]))
                .all()
            )
        # Entries: reemplazar completamente
        self.session.query(TransactionEntryModel).filter_by(
            transaction_id=str(transaction.id)
        ).delete(synchronize_session="fetch")
        for entry in transaction.entries:
            self.session.add(
                TransactionEntryModel(
                    transaction_id=str(transaction.id),
                    account_id=str(entry.account_id),
                    amount=entry.amount.amount,
                    currency=entry.amount.currency,
                )
            )

    def delete(self, entity_id: UUID) -> None:
        model = self.session.query(TransactionModel).filter_by(id=str(entity_id)).first()
        if model:
            self.session.delete(model)

    # ─────────────────────────────────────
    # Búsqueda con EXISTS — correcta para filtros combinados
    # ─────────────────────────────────────

    def search(self, criteria: TransactionSearchCriteria) -> Tuple[List[Transaction], int]:
        """
        Todos los filtros sobre apuntes usan EXISTS subqueries independientes.
        Esto permite combinar source_account_id AND destination_account_id correctamente:
        cada condición se evalúa sobre su propia fila en transaction_entries.
        """
        q = self.session.query(TransactionModel)

        # ── Fecha ─────────────────────────────────────────────────────────────
        if criteria.date_from:
            q = q.filter(TransactionModel.date >= criteria.date_from)
        if criteria.date_to:
            q = q.filter(TransactionModel.date <= criteria.date_to)

        # ── Descripción ───────────────────────────────────────────────────────
        if criteria.description_contains:
            q = q.filter(
                TransactionModel.description.ilike(f"%{criteria.description_contains}%")
            )

        # ── Cuenta (cualquier apunte) ─────────────────────────────────────────
        if criteria.account_id:
            q = q.filter(
                exists().where(
                    TransactionEntryModel.transaction_id == TransactionModel.id,
                    TransactionEntryModel.account_id == str(criteria.account_id),
                )
            )

        # ── Cuenta origen (apunte negativo) ───────────────────────────────────
        if criteria.source_account_id:
            q = q.filter(
                exists().where(
                    TransactionEntryModel.transaction_id == TransactionModel.id,
                    TransactionEntryModel.account_id == str(criteria.source_account_id),
                    TransactionEntryModel.amount < 0,
                )
            )

        # ── Cuenta destino (apunte positivo) ──────────────────────────────────
        if criteria.destination_account_id:
            q = q.filter(
                exists().where(
                    TransactionEntryModel.transaction_id == TransactionModel.id,
                    TransactionEntryModel.account_id == str(criteria.destination_account_id),
                    TransactionEntryModel.amount > 0,
                )
            )

        # ── Importe mínimo/máximo (apunte positivo = "el importe real") ───────
        if criteria.min_amount is not None:
            q = q.filter(
                exists().where(
                    TransactionEntryModel.transaction_id == TransactionModel.id,
                    TransactionEntryModel.amount >= criteria.min_amount,
                )
            )
        if criteria.max_amount is not None:
            q = q.filter(
                exists().where(
                    TransactionEntryModel.transaction_id == TransactionModel.id,
                    TransactionEntryModel.amount > 0,
                    TransactionEntryModel.amount <= criteria.max_amount,
                )
            )

        # ── Tags (OR: al menos uno de los IDs indicados) ─────────────────────
        if criteria.tag_ids:
            q = q.filter(
                exists().where(
                    transaction_tags.c.transaction_id == TransactionModel.id,
                    transaction_tags.c.tag_id.in_([str(tid) for tid in criteria.tag_ids]),
                )
            )

        # ── Total antes de paginar ─────────────────────────────────────────────
        total: int = q.with_entities(func.count(TransactionModel.id)).scalar() or 0

        # ── Resultados paginados ───────────────────────────────────────────────
        models = (
            q
            .order_by(TransactionModel.date.desc())
            .offset(criteria.offset)
            .limit(criteria.page_size)
            .all()
        )

        return [self._to_domain(m) for m in models], total

    def count_by_account(self, account_id: UUID) -> int:
        return (
            self.session.query(TransactionEntryModel)
            .filter(TransactionEntryModel.account_id == str(account_id))
            .count()
        )