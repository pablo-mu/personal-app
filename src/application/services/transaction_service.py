import uuid
from typing import List
from src.application.dtos import TransactionEntryDTO, TransactionOutputDTO, MoneySchema
from src.application.ports import AbstractUnitOfWork
from src.domain.factories import TransactionFactory

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
            
            # 4. Persistencia
            self.uow.transactions.add(transaction)
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
                tags=tag_names
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

                if source_entry:
                    source_acc = self.uow.accounts.get(source_entry.account_id)
                    if source_acc: source_name = source_acc.name
                    amount = abs(source_entry.amount.amount)
                    currency = source_entry.amount.currency
                
                if dest_entry:
                    dest_acc = self.uow.accounts.get(dest_entry.account_id)
                    if dest_acc: dest_name = dest_acc.name
                
                tag_names = []
                if tx.tags_ids:
                    tags = [self.uow.tags.get(tid) for tid in tx.tags_ids]
                    tag_names = [t.name for t in tags if t]

                output_list.append(TransactionOutputDTO(
                    id=tx.id,
                    date=tx.date,
                    description=tx.description,
                    amount=MoneySchema(amount=amount, currency=currency),
                    source_account_name=source_name,
                    destination_account_name=dest_name,
                    tags=tag_names
                ))
            return output_list
