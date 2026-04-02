"""
Servicio de Aplicación para Transacciones.
 
Gestiona el ciclo de vida completo de un movimiento financiero:
creación, actualización, eliminación y búsqueda con filtros.
"""
 
import uuid
from dataclasses import replace
from decimal import Decimal
from typing import List, Optional, Tuple
 
from src.application.dtos import (
    MoneySchema,
    PaginatedResponse,
    PaginationParams,
    TransactionEntryDTO,
    TransactionFilterDTO,
    TransactionOutputDTO,
    TagDTO,
)
from src.application.ports import AbstractUnitOfWork
from src.domain.exceptions import (
    AccountNotFoundError,
    CurrencyMismatchError,
    TagNotFoundError,
    TransactionNotFoundError,
)
from src.domain.factories import TransactionFactory
from src.domain.models import TransactionSearchCriteria
from src.domain.value_objects import Money


class TransactionService:
    """
    Gestiona la lógica de negocio relacionada con las transacciones.
    """
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    # Helper DTO
    def _build_output_dto(self, tx, uow) -> TransactionOutputDTO:
        """Construye el DTO de salida inspeccionando los apuntes de la transacción"""
        source_entry = next((e for e in tx.entries if e.amount.amount < 0), None)
        dest_entry   = next((e for e in tx.entries if e.amount.amount > 0), None)
 
        source_name, dest_name = "Desconocido", "Desconocido"
        source_id, dest_id     = None, None
        amount, currency       = Decimal("0"), "EUR"
 
        if source_entry:
            acc = uow.accounts.get(source_entry.account_id)
            if acc:
                source_name, source_id = acc.name, acc.id
            amount   = abs(source_entry.amount.amount)
            currency = source_entry.amount.currency
 
        if dest_entry:
            acc = uow.accounts.get(dest_entry.account_id)
            if acc:
                dest_name, dest_id = acc.name, acc.id
 
        tag_names = []
        tags_ids  = []
        if tx.tags_ids:
            tags = [uow.tags.get(tid) for tid in tx.tags_ids]
            tag_names = [t.name for t in tags if t]
            tags_ids  = [t.id   for t in tags if t]
 
        return TransactionOutputDTO(
            id=tx.id,
            date=tx.date,
            description=tx.description or "",
            amount=MoneySchema(amount=amount, currency=currency),
            source_account_name=source_name,
            destination_account_name=dest_name,
            source_account_id=source_id,
            destination_account_id=dest_id,
            tags=tag_names,
            tags_ids=tags_ids,
        )
    
    def _apply_balance_delta(self, transaction, uow, sign: int = 1) -> None:
        """
        Aplica (sign=+1) o revierte (sign=-1) el impacto de una transacción
        en los saldos de las cuentas.
        """
        for entry in transaction.entries:
            account = uow.accounts.get(entry.account_id)
            if not account:
                raise AccountNotFoundError(entry.account_id)
 
            if account.current_balance.currency != entry.amount.currency:
                raise CurrencyMismatchError(account.current_balance.currency, entry.amount.currency)
 
            new_amount  = account.current_balance.amount + sign * entry.amount.amount
            updated_acc = replace(account, current_balance=Money(new_amount, account.current_balance.currency))
            uow.accounts.update(updated_acc)

    def create_transaction(self, dto: TransactionEntryDTO) -> TransactionOutputDTO:
        """
        Registra una nueva transacción (Gasto, Ingreso o Transferencia).
        """
        with self.uow:
            # 1. Validación de existencia: Verificar que las cuentas existen
            source_account = self.uow.accounts.get(dto.source_account_id)
            dest_account = self.uow.accounts.get(dto.destination_account_id)

            if not source_account:
                raise AccountNotFoundError(dto.source_account_id)
            if not dest_account:
                raise AccountNotFoundError(dto.destination_account_id)
            
            # 2. Validación de etiquetas (si se enviaron)
            for tag_id in dto.tags_ids:
                if not self.uow.tags.get(tag_id):
                    raise TagNotFoundError(tag_id)
                
            # 3. Creación usando la FACTORY del Dominio
            # La factory se encarga de crear los apuntes (entries) y validar reglas de negocio
            transaction = TransactionFactory.create_transaction(
                description=dto.description,
                amount=dto.amount.amount,
                currency=dto.amount.currency,
                source_account_id=dto.source_account_id,
                destination_account_id=dto.destination_account_id,
                date=dto.date,
                related_transaction_id=dto.related_transaction_id,
                tags_ids=dto.tags_ids,
            )
            
            # 4. Persistencia de la transacción PRIMERO
            # Así si falla la persistencia, no se modifican los balances
            self.uow.transactions.add(transaction)

            self.uow.transactions.add(transaction)
            self._apply_balance_delta(transaction, self.uow, sign=1)
            self.uow.commit()
 
            return self._build_output_dto(transaction, self.uow)

    def delete_transaction(self, transaction_id: str) -> None:
        """
        Elimina una transacción del sistema y revierte los cambios en los balances.
        """
        with self.uow:
            # 1. Buscar Existente para validar que existe
            existing_tx = self.uow.transactions.get(transaction_id)
            if not existing_tx:
                raise TransactionNotFoundError(transaction_id)
            
            self._apply_balance_delta(existing_tx, self.uow, sign=-1)
            self.uow.transactions.delete(transaction_id)
            self.uow.commit()

    def update_transaction(self, transaction_id: str, dto: TransactionEntryDTO) -> TransactionOutputDTO:
        """
        Actualiza una transacción existente.
        """
        with self.uow:
            # 1. Buscar Existente
            existing_tx = self.uow.transactions.get(transaction_id)
            if not existing_tx:
                raise TransactionNotFoundError(transaction_id)

            # 2. Validar cuentas nuevas existen
            source_account = self.uow.accounts.get(dto.source_account_id)
            dest_account = self.uow.accounts.get(dto.destination_account_id)
            if not source_account:
                raise AccountNotFoundError(dto.source_account_id)
            if not dest_account:
                raise AccountNotFoundError(dto.destination_account_id)

            # Revertir impacto de la transacción antigua
            self._apply_balance_delta(existing_tx, self.uow, sign=-1)
            
            # 4. Re-crear objeto dominio usando Factory (reciclando ID)
            # Esto valida reglas de negocio de nuevo con los nuevos datos
            updated_tx = TransactionFactory.create_transaction(
                description=dto.description,
                amount=dto.amount.amount,
                currency=dto.amount.currency,
                source_account_id=dto.source_account_id,
                destination_account_id=dto.destination_account_id,
                date=dto.date,
                related_transaction_id=existing_tx.related_transaction_id, # Mantener relación si había
                tags_ids=dto.tags_ids
            )
            # Forzamos el ID original para que sea un UPDATE en vez de INSERT
            updated_tx.id = existing_tx.id
            
            # 5. Persistir transacción actualizada
            self.uow.transactions.update(updated_tx)
            
            # 6. Aplicar nuevos balances
            self._apply_balance_delta(updated_tx, self.uow, sign=1)
            self.uow.commit()
 
            return self._build_output_dto(updated_tx, self.uow)
        
    
    def get_transaction(self, transaction_id: uuid.UUID) -> TransactionOutputDTO:
        with self.uow:
            tx = self.uow.transactions.get(transaction_id)
            if not tx:
                raise TransactionNotFoundError(transaction_id)
            return self._build_output_dto(tx, self.uow)

    def list_transactions(
        self,
        filters: Optional[TransactionFilterDTO] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResponse[TransactionOutputDTO]:
        """
        Lista transacciones con filtros aplicados en BD y paginación.
        Devuelve una respuesta paginada.
        """
        if pagination is None:
            pagination = PaginationParams(page=1, page_size=50)
 
        criteria = TransactionSearchCriteria(
            account_id=filters.account_id if filters else None,
            source_account_id=filters.source_account_id if filters else None,
            destination_account_id=filters.destination_account_id if filters else None,
            min_amount=filters.min_amount if filters else None,
            max_amount=filters.max_amount if filters else None,
            date_from=filters.date_from if filters else None,
            date_to=filters.date_to if filters else None,
            tag_ids=list(filters.tag_ids) if filters and filters.tag_ids else None,
            description_contains=filters.description_contains if filters else None,
            page=pagination.page,
            page_size=pagination.page_size,
        )
 
        with self.uow:
            transactions, total = self.uow.transactions.search(criteria)
            items = [self._build_output_dto(tx, self.uow) for tx in transactions]
            return PaginatedResponse.build(
                items=items,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
            )
 
    # Compat: devuelve lista plana (usada por la UI de Dash)
    def list_transactions_flat(self) -> List[TransactionOutputDTO]:
        paged = self.list_transactions(pagination=PaginationParams(page=1, page_size=1000))
        return paged.items