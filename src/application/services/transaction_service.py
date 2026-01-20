import uuid
from typing import List
from dataclasses import replace
from src.application.dtos import TransactionEntryDTO, TransactionOutputDTO, MoneySchema
from src.application.ports import AbstractUnitOfWork
from src.domain.factories import TransactionFactory
from src.domain.value_objects import Money

class TransactionService:
    """
    Gestiona la lógica de negocio relacionada con las transacciones.
    """
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def create_transaction(self, dto: TransactionEntryDTO) -> TransactionOutputDTO:
        """
        Registra una nueva transacción (Gasto, Ingreso o Transferencia).
        """
        with self.uow:
            # 1. Validación de existencia: Verificar que las cuentas existen
            source_account = self.uow.accounts.get(dto.source_account_id)
            dest_account = self.uow.accounts.get(dto.destination_account_id)

            if not source_account:
                raise ValueError("Cuenta de origen no encontrada.")
            if not dest_account:
                raise ValueError("Cuenta de destino no encontrada.")
            
            # 2. Validación de etiquetas (si se enviaron)
            for tag_id in dto.tags_ids:
                tag = self.uow.tags.get(tag_id)
                if not tag:
                    raise ValueError(f"Etiqueta con ID {tag_id} no encontrada.")
                
            # 3. Creación usando la FACTORY del Dominio
            # La factory se encarga de crear los apuntes (entries) y validar reglas de negocio
            transaction = TransactionFactory.create_transaction(
                description=dto.description,
                amount=dto.amount.amount, # Extraemos el Decimal del objeto Money
                currency=dto.amount.currency,
                source_account_id=dto.source_account_id,
                destination_account_id=dto.destination_account_id,
                date=dto.date,
                related_transaction_id=dto.related_transaction_id,
                tags_ids=dto.tags_ids
            )
            
            # 4. Persistencia de la transacción PRIMERO
            # Así si falla la persistencia, no se modifican los balances
            self.uow.transactions.add(transaction)
            
            # 5. Actualizar current_balance de las cuentas afectadas
            # Iterar sobre los apuntes de la transacción y actualizar saldos
            for entry in transaction.entries:
                account = self.uow.accounts.get(entry.account_id)
                if not account:
                    raise ValueError(f"Cuenta {entry.account_id} no encontrada al actualizar balance")
                
                # Validar consistencia de moneda
                if account.current_balance.currency != entry.amount.currency:
                    raise ValueError(f"Inconsistencia de moneda: cuenta usa {account.current_balance.currency}, transacción usa {entry.amount.currency}")
                
                # Sumar el apunte al saldo actual (amount puede ser positivo o negativo)
                new_balance_amount = account.current_balance.amount + entry.amount.amount
                new_current_balance = Money(amount=new_balance_amount, currency=account.current_balance.currency)
                updated_account = replace(account, current_balance=new_current_balance)
                self.uow.accounts.update(updated_account)
            
            # 6. Commit de TODO (transacción + balances actualizados)
            # Si falla, el UoW hace rollback automático
            self.uow.commit()

            # 5. Devolvemos un DTO de salida
            tag_names = []
            tags = [self.uow.tags.get(tag_id) for tag_id in transaction.tags_ids]
            tag_names = [tag.name for tag in tags if tag]

            return TransactionOutputDTO(
                id=transaction.id,
                date=transaction.date,
                description=transaction.description,
                amount=MoneySchema(amount=dto.amount.amount, currency=dto.amount.currency),
                source_account_name=source_account.name,
                destination_account_name=dest_account.name,
                source_account_id=source_account.id,
                destination_account_id=dest_account.id,
                tags=tag_names
            )

    def delete_transaction(self, transaction_id: str) -> None:
        """
        Elimina una transacción del sistema y revierte los cambios en los balances.
        """
        with self.uow:
            # 1. Buscar Existente para validar que existe
            existing_tx = self.uow.transactions.get(transaction_id)
            if not existing_tx:
                # O podríamos lanzar error, o simplemente ignorar si ya no existe (idempotencia)
                 raise ValueError(f"Transacción {transaction_id} no encontrada")
            
            # 2. Revertir cambios en current_balance ANTES de eliminar
            for entry in existing_tx.entries:
                account = self.uow.accounts.get(entry.account_id)
                if not account:
                    raise ValueError(f"Cuenta {entry.account_id} no encontrada al revertir balance")
                
                # Validar consistencia de moneda
                if account.current_balance.currency != entry.amount.currency:
                    raise ValueError(f"Inconsistencia de moneda al eliminar transacción")
                
                # Restar el apunte del saldo actual (inverso de la creación)
                new_balance_amount = account.current_balance.amount - entry.amount.amount
                new_current_balance = Money(amount=new_balance_amount, currency=account.current_balance.currency)
                updated_account = replace(account, current_balance=new_current_balance)
                self.uow.accounts.update(updated_account)
            
            # 3. Eliminar la transacción
            self.uow.transactions.delete(transaction_id)
            
            # 4. Commit de TODO
            self.uow.commit()

    def update_transaction(self, transaction_id: str, dto: TransactionEntryDTO) -> TransactionOutputDTO:
        """
        Actualiza una transacción existente.
        """
        with self.uow:
            # 1. Buscar Existente
            existing_tx = self.uow.transactions.get(transaction_id)
            if not existing_tx:
                raise ValueError(f"Transacción {transaction_id} no encontrada")

            # 2. Validar cuentas nuevas existen
            source_account = self.uow.accounts.get(dto.source_account_id)
            dest_account = self.uow.accounts.get(dto.destination_account_id)
            if not source_account or not dest_account:
                raise ValueError("Cuentas de origen o destino no encontradas")

            # 3. Revertir balances de la transacción antigua
            for entry in existing_tx.entries:
                account = self.uow.accounts.get(entry.account_id)
                if not account:
                    raise ValueError(f"Cuenta {entry.account_id} no encontrada al revertir balance")
                
                if account.current_balance.currency != entry.amount.currency:
                    raise ValueError(f"Inconsistencia de moneda al revertir")
                
                new_balance_amount = account.current_balance.amount - entry.amount.amount
                new_current_balance = Money(amount=new_balance_amount, currency=account.current_balance.currency)
                updated_account = replace(account, current_balance=new_current_balance)
                self.uow.accounts.update(updated_account)
            
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
            for entry in updated_tx.entries:
                account = self.uow.accounts.get(entry.account_id)
                if not account:
                    raise ValueError(f"Cuenta {entry.account_id} no encontrada al aplicar balance")
                
                if account.current_balance.currency != entry.amount.currency:
                    raise ValueError(f"Inconsistencia de moneda: cuenta usa {account.current_balance.currency}, transacción usa {entry.amount.currency}")
                
                new_balance_amount = account.current_balance.amount + entry.amount.amount
                new_current_balance = Money(amount=new_balance_amount, currency=account.current_balance.currency)
                updated_account = replace(account, current_balance=new_current_balance)
                self.uow.accounts.update(updated_account)
            
            # 7. Commit de TODO (transacción actualizada + balances)
            self.uow.commit()

            return TransactionOutputDTO(
                id=updated_tx.id,
                date=updated_tx.date,
                description=updated_tx.description,
                amount=dto.amount,
                source_account_name=source_account.name,
                destination_account_name=dest_account.name,
                source_account_id=source_account.id,
                destination_account_id=dest_account.id,
                tags=[] # Simplificación
            )

    def list_transactions(self) -> List[TransactionOutputDTO]:
        """
        Lista todas las transacciones.
        """
        with self.uow:
            transactions = self.uow.transactions.list()
            output_list = []
            for tx in transactions:
                # Necesitamos obtener los nombres de las cuentas para el DTO
                # Esto podría ser ineficiente (N+1 queries), pero por ahora es funcional.
                # En una implementación real, el repositorio debería hacer un JOIN o traer la info necesaria.
                # O el DTO podría solo tener IDs y el frontend resolver los nombres.
                # Asumiremos que podemos obtener las cuentas.
                
                # Nota: TransactionEntry tiene account_id.
                # Buscamos la cuenta origen (amount < 0) y destino (amount > 0) para simplificar la vista
                # Aunque una transacción puede tener N entradas.
                # Asumimos la estructura simple de 2 entradas creada por la Factory.
                
                source_entry = next((e for e in tx.entries if e.amount.amount < 0), None)
                dest_entry = next((e for e in tx.entries if e.amount.amount > 0), None)
                
                source_name = "Desconocido"
                dest_name = "Desconocido"
                amount = 0
                currency = "EUR"

                source_id = None
                dest_id = None

                if source_entry:
                    source_acc = self.uow.accounts.get(source_entry.account_id)
                    if source_acc: 
                        source_name = source_acc.name
                        source_id = source_acc.id
                    amount = abs(source_entry.amount.amount)
                    currency = source_entry.amount.currency
                
                if dest_entry:
                    dest_acc = self.uow.accounts.get(dest_entry.account_id)
                    if dest_acc: 
                        dest_name = dest_acc.name
                        dest_id = dest_acc.id
                
                tag_names = []
                tags_ids = []
                if tx.tags_ids:
                    tags = [self.uow.tags.get(tid) for tid in tx.tags_ids]
                    tag_names = [t.name for t in tags if t]
                    tags_ids = [t.id for t in tags if t]

                output_list.append(TransactionOutputDTO(
                    id=tx.id,
                    date=tx.date,
                    description=tx.description,
                    amount=MoneySchema(amount=amount, currency=currency),
                    source_account_name=source_name,
                    destination_account_name=dest_name,
                    source_account_id=source_id,
                    destination_account_id=dest_id,
                    tags=tag_names,
                    tags_ids=tags_ids
                ))
            return output_list
