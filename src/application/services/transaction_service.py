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
                source_account_id=source_account.id,
                destination_account_id=dest_account.id,
                tags=tag_names
            )

    def delete_transaction(self, transaction_id: str) -> None:
        """
        Elimina una transacción del sistema.
        """
        with self.uow:
            # 1. Buscar Existente para validar que existe
            existing_tx = self.uow.transactions.get(transaction_id)
            if not existing_tx:
                # O podríamos lanzar error, o simplemente ignorar si ya no existe (idempotencia)
                 raise ValueError(f"Transacción {transaction_id} no encontrada")
            
            # 2. Eliminar
            # Dependiendo de la implementación del Repo, podría ser un hard delete.
            # En repositories/transaction_repository.py, necesitamos un método delete.
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
                raise ValueError(f"Transacción {transaction_id} no encontrada")

            # 2. Re-crear objeto dominio usando Factory (reciclando ID)
            # Esto valida reglas de negocio de nuevo con los nuevos datos
            source_account = self.uow.accounts.get(dto.source_account_id)
            dest_account = self.uow.accounts.get(dto.destination_account_id)

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
            # Hack simple dado que la dataclass es 'frozen=False' por defecto (si no se especifica frozen=True)
            # Pero en models.py Transaction NO es frozen (solo Entries y Accounts lo son), así que podemos asignar id.
            updated_tx.id = existing_tx.id
            
            # 3. Persistir Cambios
            self.uow.transactions.update(updated_tx)
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
