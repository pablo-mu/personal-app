"""
Capa de Aplicación (Application Layer).

Esta capa contiene la lógica de los casos de uso del sistema.
Actúa como orquestador entre el mundo exterior (API/UI) y el Dominio.
"""

# 1. Exponemos los DTOs (Contratos de datos)
from .dtos import (
    AccountCreateDTO,
    AccountOutputDTO,
    TransactionEntryDTO,
    TransactionOutputDTO,
    TagDTO,
    # TransactionRefundDTO,
    # TransactionWithNetBalanceDTO
)

# 2. Exponemos los Puertos (Interfaces para infraestructura)
from .ports import (
    AbstractUnitOfWork,
    AbstractRepository,
    AbstractAccountRepository,
    AbstractTransactionRepository,
    AbstractTagRepository
)

# 3. Exponemos los Servicios (Casos de uso)
from .services import (
    AccountService,
    TransactionService,
    TagService
)