"""
Este módulo define los servicios de la aplicación:

1. Traduce los DTOs (Data Transfer Objects) a entidades del dominio.
2. Orquesta: Coordina las operaciones y la lógica de negoio. Por ejemplo:
Antes de crear una transacción, verifica que las cuentas existen y que hay saldo suficiente.
3. Gestiona la persistencia: Usa el patrón Unit of Work (UoW) para asegurar que todas las
operaciones de una transacción se completen correctamente (todo o nada).
4. Aísla la lógica de negocio del resto de la aplicación, facilitando pruebas y mantenimiento.
"""

import uuid
from typing import List, Optional
from .dtos import (
    AccountCreateDTO,
    AccountOutputDTO,
    TransactionEntryDTO,
    TransactionOutputDTO,
    TagDTO,
    MoneySchema
)

from .ports import AbstractUnitOfWork

from src.domain.models import Account, Tag, Transaction
from src.domain.factories import TransactionFactory
from src.domain.value_objects import Money

class AccountService:
    """
    Gestiona la lógica de negocio relacionada con las cuentas.
    """
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
    
    def create_account(self, dto: AccountCreateDTO) -> AccountOutputDTO:
        """
        Crea una nueva cuenta en el sistema.
        """
        # 1. Iniciamos la transacción con la base de datos (Unit of Work)
        with self.uow:
            # 2. Convertimos el DTO a una Entidad de Dominio
            # Generamos el ID aquí o dejamos que la DB lo haga (mejor aquí para UUIDs)
            new_account = Account(
                id=uuid.uuid4(),
                name=dto.name,
                type=dto.type,
                initial_balance=Money(amount=dto.initial_balance.amount, currency=dto.initial_balance.currency)
            )

            # 3. Usamos el repositorio para añadirla
            self.uow.accounts.add(new_account)

            # 4. Confirmamos los cambios (Guardar en DB)
            self.uow.commit()

            # 5. Devolvemos un DTO de salida (no la entidad directa)
            return AccountOutputDTO(
                id=new_account.id,
                name=new_account.name,
                type=new_account.type,
                initial_balance=new_account.initial_balance
            )
    
    def suspend_account(self, account_id: uuid.UUID) -> None:
        """
        Suspende una cuenta (lógica de negocio para suspender).
        """
        with self.uow:
            account = self.uow.accounts.get(account_id)
            if not account:
                raise ValueError("Cuenta no encontrada.")
            
            # Aquí iría la lógica para suspender la cuenta
            # Por ejemplo, cambiar un estado o bandera en la entidad
            
            self.uow.commit()
        return None
    
    def list_accounts(self) -> List[AccountOutputDTO]:
        """
        Devuelve todas las cuentas en formato DTO.
        """
        with self.uow:
            accounts = self.uow.accounts.list()
            return [
                AccountOutputDTO(
                    id=acct.id,
                    name=acct.name,
                    type=acct.type,
                    initial_balance=MoneySchema(amount=acct.initial_balance.amount, currency=acct.initial_balance.currency)
                ) for acct in accounts
            ]
        
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


class TagService:
    """
    Gestiona la creación y listado de etiquetas.
    """
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def create_tag(self, dto: TagDTO) -> TagDTO:
        with self.uow:
            new_tag = Tag(
                id=uuid.uuid4(),
                name=dto.name,
                color=dto.color,
                icon=dto.icon
            )
            self.uow.tags.add(new_tag)
            self.uow.commit()
            
            return TagDTO(id=new_tag.id, name=new_tag.name, color=new_tag.color, icon=new_tag.icon)

    def list_tags(self) -> List[TagDTO]:
        with self.uow:
            tags = self.uow.tags.list()
            return [
                TagDTO(id=t.id, name=t.name, color=t.color, icon=t.icon) 
                for t in tags
            ]
