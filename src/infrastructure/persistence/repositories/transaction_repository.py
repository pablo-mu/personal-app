"""
Repositorio SQLAlchemy para Transacciones.

Implementa filtrado y paginación en la capa de base de datos para evitar
traer miles de registros a memoria en listados grandes.
"""

from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.application.ports import AbstractTransactionRepository
from src.domain.models import Transaction, TransactionEntry, TransactionSearchCriteria
from src.domain.value_objects import Money
from src.infrastructure.persistence.models import (
    TagModel,
    TransactionEntryModel,
    TransactionModel,
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
            related_transaction_id=UUID(model.related_transaction_id) if model.related_transaction_id else None,
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
            related_transaction_id=str(transaction.related_transaction_id) if transaction.related_transaction_id else None,
        )
        if transaction.tags_ids:
            model.tags = self.session.query(TagModel).filter(
                TagModel.id.in_([str(t) for t in transaction.tags_ids])
            ).all()

        for entry in transaction.entries:
            model.entries.append(TransactionEntryModel(
                transaction_id=str(transaction.id),
                account_id=str(entry.account_id),
                amount=entry.amount.amount,
                currency=entry.amount.currency,
            ))

        self.session.add(model)

    def get(self, entity_id: UUID) -> Optional[Transaction]:
        model = self.session.query(TransactionModel).filter_by(id=str(entity_id)).first()
        return self._to_domain(model) if model else None

    def list(self) -> List[Transaction]:
        return [self._to_domain(m) for m in self.session.query(TransactionModel).all()]

    def update(self, transaction: Transaction) -> None:
        model = self.session.query(TransactionModel).filter_by(id=str(transaction.id)).first()
        if not model:
            return

        model.description            = transaction.description or ""
        model.date                   = transaction.date
        model.related_transaction_id = str(transaction.related_transaction_id) if transaction.related_transaction_id else None

        # Tags: reemplazar
        if transaction.tags_ids is not None:
            model.tags = self.session.query(TagModel).filter(
                TagModel.id.in_([str(t) for t in transaction.tags_ids])
            ).all()

        # Entries: eliminar las viejas y añadir las nuevas
        self.session.query(TransactionEntryModel).filter_by(transaction_id=str(transaction.id)).delete()
        for entry in transaction.entries:
            model.entries.append(TransactionEntryModel(
                transaction_id=str(transaction.id),
                account_id=str(entry.account_id),
                amount=entry.amount.amount,
                currency=entry.amount.currency,
            ))

    def delete(self, entity_id: UUID) -> None:
        model = self.session.query(TransactionModel).filter_by(id=str(entity_id)).first()
        if model:
            self.session.delete(model)

    # ─────────────────────────────────────
    # Búsqueda con filtros y paginación en BD
    # ─────────────────────────────────────

    def search(
        self,
        criteria: TransactionSearchCriteria,
    ) -> Tuple[List[Transaction], int]:
        """
        Aplica todos los filtros en SQL (no en Python) y devuelve
        (lista_paginada, total_sin_paginar).
        """
        query = (
            self.session
            .query(TransactionModel)
            .join(TransactionModel.entries)
        )

        # Filtro por cuenta específica (cualquier lado)
        if criteria.account_id:
            query = query.filter(
                TransactionEntryModel.account_id == str(criteria.account_id)
            )

        # Filtro por cuenta origen (apunte negativo)
        if criteria.source_account_id:
            query = query.filter(
                TransactionEntryModel.account_id == str(criteria.source_account_id),
                TransactionEntryModel.amount < 0,
            )

        # Filtro por cuenta destino (apunte positivo)
        if criteria.destination_account_id:
            query = query.filter(
                TransactionEntryModel.account_id == str(criteria.destination_account_id),
                TransactionEntryModel.amount > 0,
            )

        # Filtro por rango de fechas
        if criteria.date_from:
            query = query.filter(TransactionModel.date >= criteria.date_from)
        if criteria.date_to:
            query = query.filter(TransactionModel.date <= criteria.date_to)

        # Filtro por monto (sobre el apunte positivo = "el importe real")
        if criteria.min_amount is not None:
            query = query.filter(TransactionEntryModel.amount >= criteria.min_amount)
        if criteria.max_amount is not None:
            query = query.filter(TransactionEntryModel.amount <= criteria.max_amount)

        # Filtro por descripción
        if criteria.description_contains:
            query = query.filter(
                TransactionModel.description.ilike(f"%{criteria.description_contains}%")
            )

        # Filtro por tags (al menos uno de los tags en la lista)
        if criteria.tag_ids:
            query = (
                query
                .join(TransactionModel.tags)
                .filter(TagModel.id.in_([str(tid) for tid in criteria.tag_ids]))
            )

        # Evitar duplicados por el JOIN con entries
        query = query.distinct()

        # Contar total antes de paginar
        total = query.with_entities(func.count(func.distinct(TransactionModel.id))).scalar() or 0

        # Paginación y orden
        transactions = (
            query
            .order_by(TransactionModel.date.desc())
            .offset(criteria.offset)
            .limit(criteria.page_size)
            .all()
        )

        return [self._to_domain(m) for m in transactions], total

    def count_by_account(self, account_id: UUID) -> int:
        return (
            self.session
            .query(TransactionEntryModel)
            .filter(TransactionEntryModel.account_id == str(account_id))
            .count()
        )