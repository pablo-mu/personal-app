import uuid
from typing import List
from src.application.dtos import AccountCreateDTO, AccountOutputDTO, MoneySchema
from src.application.ports import AbstractUnitOfWork
from src.domain.models import Account
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
