"""
Data Transfer Objects (DTOs) de la capa de aplicación.

Responsabilidad: Definir los contratos de datos entre la UI/API y los servicios.
Los DTOs validan con Pydantic pero NO contienen lógica de negocio.
"""

from datetime import datetime
from decimal import Decimal
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, UUID4, field_validator, model_validator

from src.domain.models import AccountType


# ─────────────────────────────────────────
# Tipos y Auxiliares
# ─────────────────────────────────────────

T = TypeVar("T")


class MoneySchema(BaseModel):
    amount: Decimal
    currency: str = "EUR"

    @field_validator("amount")
    @classmethod
    def round_amount(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class PaginationParams(BaseModel):
    """Parámetros de paginación comunes."""
    page: int = Field(default=1, ge=1, description="Número de página (empieza en 1)")
    page_size: int = Field(default=20, ge=1, le=1000, description="Elementos por página")


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica."""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        pages = max(1, -(-total // page_size))  # ceiling division
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


# ─────────────────────────────────────────
# Cuentas
# ─────────────────────────────────────────

class AccountCreateDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: AccountType
    initial_balance: MoneySchema = Field(default_factory=lambda: MoneySchema(amount=Decimal("0.00")))
    is_active: bool = True
    account_number: Optional[str] = Field(default=None, max_length=50)
    parent_account_id: Optional[UUID4] = None


class AccountUpdateDTO(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    type: Optional[AccountType] = None
    is_active: Optional[bool] = None
    account_number: Optional[str] = Field(default=None, max_length=50)
    parent_account_id: Optional[UUID4] = None


class AccountFilterDTO(BaseModel):
    """
    DTO para filtrar cuentas. Todos los campos son opcionales.
    No es frozen: la capa UI construye el objeto vacío y luego asigna campos.
    """
    type: Optional[AccountType] = None
    parent_id: Optional[UUID4] = None
    is_active: Optional[bool] = None
    name_contains: Optional[str] = None


class AccountOutputDTO(BaseModel):
    id: UUID4
    name: str
    type: AccountType
    initial_balance: MoneySchema
    current_balance: MoneySchema
    is_active: bool
    account_number: Optional[str] = None
    parent_account_id: Optional[UUID4] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Transacciones
# ─────────────────────────────────────────

class TransactionEntryDTO(BaseModel):
    description: Optional[str] = Field(default=None, max_length=200)
    amount: MoneySchema
    source_account_id: UUID4
    destination_account_id: UUID4
    date: datetime = Field(default_factory=datetime.now)
    tags_ids: List[UUID4] = Field(default_factory=list)
    related_transaction_id: Optional[UUID4] = None

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: MoneySchema) -> MoneySchema:
        if v.amount <= 0:
            raise ValueError("El monto debe ser positivo.")
        return v

    @model_validator(mode="after")
    def validate_different_accounts(self) -> "TransactionEntryDTO":
        if self.source_account_id == self.destination_account_id:
            raise ValueError("Las cuentas de origen y destino no pueden ser la misma.")
        return self


class TransactionFilterDTO(BaseModel):
    """Filtros para búsqueda de transacciones (aplicados en BD)."""
    account_id: Optional[UUID4] = None
    source_account_id: Optional[UUID4] = None
    destination_account_id: Optional[UUID4] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    tag_ids: Optional[List[UUID4]] = None
    description_contains: Optional[str] = None

    model_config = {"frozen": True}


class TransactionOutputDTO(BaseModel):
    id: UUID4
    date: datetime
    description: str
    amount: MoneySchema
    source_account_name: str
    destination_account_name: str
    source_account_id: Optional[UUID4] = None
    destination_account_id: Optional[UUID4] = None
    tags: List[str] = Field(default_factory=list)
    tags_ids: List[UUID4] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Etiquetas
# ─────────────────────────────────────────

class TagDTO(BaseModel):
    id: Optional[UUID4] = None
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#a8a8a8", pattern=r"^#[0-9a-fA-F]{6}$")

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Reglas Recurrentes
# ─────────────────────────────────────────

from src.domain.models import RecurrenceType, RecurrenceFrequency, IntervalUnit, TransactionType


class RecurringRuleCreateDTO(BaseModel):
    description: Optional[str] = Field(default=None, max_length=200)
    amount: MoneySchema
    source_account_id: UUID4
    destination_account_id: UUID4
    transaction_type: TransactionType
    tags_ids: List[UUID4] = Field(default_factory=list)

    recurrence_type: RecurrenceType = RecurrenceType.CALENDAR_BASED
    frequency: Optional[RecurrenceFrequency] = None
    day_of_execution: Optional[int] = None
    interval_value: Optional[int] = None
    interval_unit: Optional[IntervalUnit] = None

    start_date: datetime = Field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_recurrence_config(self) -> "RecurringRuleCreateDTO":
        if self.recurrence_type == RecurrenceType.CALENDAR_BASED:
            if not self.frequency:
                raise ValueError("CALENDAR_BASED requiere 'frequency'.")
            if self.day_of_execution is None:
                raise ValueError("CALENDAR_BASED requiere 'day_of_execution'.")
        elif self.recurrence_type == RecurrenceType.INTERVAL_BASED:
            if not self.interval_value:
                raise ValueError("INTERVAL_BASED requiere 'interval_value'.")
            if not self.interval_unit:
                raise ValueError("INTERVAL_BASED requiere 'interval_unit'.")
        return self


class RecurringRuleUpdateDTO(BaseModel):
    description: Optional[str] = Field(default=None, max_length=200)
    amount: Optional[MoneySchema] = None
    tags_ids: Optional[List[UUID4]] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class RecurringRuleOutputDTO(BaseModel):
    id: UUID4
    description: Optional[str]
    amount: MoneySchema
    source_account_id: UUID4
    destination_account_id: UUID4
    source_account_name: str
    destination_account_name: str
    transaction_type: TransactionType
    tags_ids: List[UUID4]

    recurrence_type: RecurrenceType
    frequency: Optional[RecurrenceFrequency]
    day_of_execution: Optional[int]
    interval_value: Optional[int]
    interval_unit: Optional[IntervalUnit]

    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
    last_execution_date: Optional[datetime]
    next_execution_date: Optional[datetime]

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# Reportes
# ─────────────────────────────────────────

class AccountBalanceSummaryDTO(BaseModel):
    """Resumen de saldo de una cuenta."""
    id: UUID4
    name: str
    type: AccountType
    current_balance: MoneySchema


class CategorySummaryDTO(BaseModel):
    """Desglose de una categoría dentro de un período."""
    category_id: UUID4
    category_name: str
    total: MoneySchema
    transaction_count: int
    percentage: float  # del total de la misma naturaleza (ingresos o gastos)


class PeriodSummaryDTO(BaseModel):
    """Resumen financiero de un período."""
    period_start: datetime
    period_end: datetime
    total_income: MoneySchema
    total_expense: MoneySchema
    net: MoneySchema  # income - expense
    expense_by_category: List[CategorySummaryDTO] = Field(default_factory=list)
    income_by_category: List[CategorySummaryDTO] = Field(default_factory=list)


class MonthlyEvolutionDTO(BaseModel):
    """Datos de un mes para la gráfica de evolución."""
    year: int
    month: int
    label: str           # "Ene 2025"
    income: MoneySchema
    expense: MoneySchema
    net: MoneySchema


class NetWorthDTO(BaseModel):
    """Patrimonio neto actual."""
    total_assets: MoneySchema
    total_liabilities: MoneySchema
    net_worth: MoneySchema         # assets - liabilities
    accounts: List[AccountBalanceSummaryDTO] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=datetime.now)