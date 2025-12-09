import uuid
from typing import List, Optional
from src.application.dtos import AccountCreateDTO, AccountOutputDTO, MoneySchema, AccountFilterDTO, AccountUpdateDTO
from src.application.ports import AbstractUnitOfWork
from src.domain.models import Account, AccountSearchCriteria
from src.domain.value_objects import Money
from src.domain.exceptions import AccountAlreadyExistsError

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
            # Validación: Verificar si ya existe una cuenta con el mismo nombre y tipo
            # Usamos el método search para reutilizar lógica de filtrado
            criteria = AccountSearchCriteria(name_contains=dto.name, type=dto.type)
            existing_accounts = self.uow.accounts.search(criteria)
            
            # Filtramos exactamente por nombre (search usa ilike/contains)
            if any(acc.name == dto.name for acc in existing_accounts):
                 raise AccountAlreadyExistsError(f"La cuenta '{dto.name}' de tipo '{dto.type.value}' ya existe.")

            # 2. Convertimos el DTO a una Entidad de Dominio
            # Generamos el ID aquí o dejamos que la DB lo haga (mejor aquí para UUIDs)
            new_account = Account(
                id=uuid.uuid4(),
                name=dto.name,
                type=dto.type,
                initial_balance=Money(amount=dto.initial_balance.amount, currency=dto.initial_balance.currency),
                is_active=dto.is_active,
                account_number=dto.account_number,
                parent_account_id=dto.parent_account_id
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
                initial_balance=MoneySchema(amount=new_account.initial_balance.amount, currency=new_account.initial_balance.currency),
                is_active=new_account.is_active,
                account_number=new_account.account_number,
                parent_account_id=new_account.parent_account_id
            )
    
    def update_account(self, account_id: uuid.UUID, dto: AccountUpdateDTO) -> None:
        """
        Actualiza los datos de una cuenta.
        """
        with self.uow:
            account = self.uow.accounts.get(account_id)
            if not account:
                raise ValueError("Cuenta no encontrada.")

            # Actualizamos campos si vienen en el DTO (usamos replace para dataclasses inmutables)
            # Nota: dataclasses.replace crea una copia nueva
            from dataclasses import replace
            
            changes = {}
            if dto.name is not None: changes['name'] = dto.name
            
            if dto.type is not None and dto.type != account.type:
                 # Validación contable: No cambiar tipo si hay historial
                 if self.uow.transactions.count_by_account(account_id) > 0:
                     raise ValueError("No se puede cambiar el tipo de una cuenta que ya tiene movimientos.")
                 changes['type'] = dto.type

            if dto.is_active is not None: changes['is_active'] = dto.is_active
            if dto.account_number is not None: changes['account_number'] = dto.account_number
            if dto.parent_account_id is not None: changes['parent_account_id'] = dto.parent_account_id

            updated_account = replace(account, **changes)
            
            self.uow.accounts.update(updated_account)
            self.uow.commit()

    def delete_account(self, account_id: uuid.UUID) -> None:
        """
        Elimina una cuenta si no tiene transacciones asociadas.
        """
        with self.uow:
            account = self.uow.accounts.get(account_id)
            if not account:
                raise ValueError("Cuenta no encontrada.")
            
            # Validar si tiene transacciones antes de borrar
            if self.uow.transactions.count_by_account(account_id) > 0:
                 raise ValueError("No se puede eliminar una cuenta con transacciones. Archívala en su lugar.")
            
            # Validar si tiene saldo inicial distinto de cero (aunque no tenga transacciones)
            if not account.initial_balance.is_zero():
                 raise ValueError("No se puede eliminar una cuenta con saldo inicial. Ajústalo a cero primero.")

            self.uow.accounts.delete(account_id)
            self.uow.commit()

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
    
    def get_account_balance(self, account_id: uuid.UUID) -> MoneySchema:
        """
        Obtiene el saldo actual calculado de una cuenta.
        """
        with self.uow:
            balance = self.uow.accounts.get_balance(account_id)
            return MoneySchema(amount=balance.amount, currency=balance.currency)

    def list_accounts(self, filters: Optional[AccountFilterDTO] = None) -> List[AccountOutputDTO]:
        """
        Devuelve todas las cuentas en formato DTO, aplicando filtros opcionales.
        """
        if filters is None:
            filters = AccountFilterDTO()

        # Mapeamos el DTO de aplicación al objeto de criterios del dominio
        criteria = AccountSearchCriteria(
            type=filters.type,
            parent_id=filters.parent_id,
            is_active=filters.is_active,
            name_contains=filters.name_contains
        )

        with self.uow:
            accounts = self.uow.accounts.search(criteria)
            return [
                AccountOutputDTO(
                    id=acct.id,
                    name=acct.name,
                    type=acct.type,
                    initial_balance=MoneySchema(amount=acct.initial_balance.amount, currency=acct.initial_balance.currency),
                    is_active=acct.is_active,
                    account_number=acct.account_number,
                    parent_account_id=acct.parent_account_id
                ) for acct in accounts
            ]
