"""
Definimos los modelos de dominio para la aplicación de finanzas personales.
Estos modelos representan las entidades principales y básicas de la aplicación.
Cada modelo está diseñado utilizando dataclasses para facilitar la gestión de datos y asegurar la inmutabilidad donde sea necesario.
Se definen los campos para seguir las mejores prácticas de tipado, 
de responsabilidad única. Y así, construir la base de la contabilidad de partida doble.

Principios:
- Las entidades son objetos puros (dataclasses) sin dependencias externas.
- La lógica de negocio vive en el dominio, no en los servicios.
- Inmutabilidad donde sea posible (frozen=True).
"""
 
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID
 
from .value_objects import Money
 
 
# ─────────────────────────────────────────
# Enumeraciones
# ─────────────────────────────────────────
 
class AccountType(Enum):
    """
    Tipos de cuenta para la contabilidad de partida doble.
    El valor es una tupla (etiqueta, descripción).
    """
    ASSET     = ("Activo",     "Dinero que tengo o poseo (efectivo, cuentas bancarias, inversiones).")
    LIABILITY = ("Pasivo",     "Dinero que debo (préstamos, tarjetas de crédito).")
    INCOME    = ("Ingreso",    "Dinero que recibo (salario, ventas).")
    EXPENSE   = ("Gasto",      "Dinero que gasto (alquiler, comida, ocio).")
    EQUITY    = ("Patrimonio", "Valor neto (activos menos pasivos).")
 
    def __new__(cls, label: str, description: str):
        obj = object.__new__(cls)
        obj._value_ = label
        obj.description = description
        return obj
 
 
class TransactionType(Enum):
    """Tipo semántico de una regla recurrente."""
    INCOME  = "Ingreso"
    EXPENSE = "Gasto"
 
 
class RecurrenceType(Enum):
    """Patrón de recurrencia de una regla."""
    CALENDAR_BASED = "calendar"
    INTERVAL_BASED = "interval"
 
 
class RecurrenceFrequency(Enum):
    """Frecuencia para recurrencias basadas en calendario."""
    DAILY   = "Diaria"
    WEEKLY  = "Semanal"
    MONTHLY = "Mensual"
    YEARLY  = "Anual"
 
 
class IntervalUnit(Enum):
    """Unidad de tiempo para recurrencias basadas en intervalo."""
    DAYS   = "Días"
    WEEKS  = "Semanas"
    MONTHS = "Meses"
    YEARS  = "Años"
 
 
# ─────────────────────────────────────────
# Entidades
# ─────────────────────────────────────────
 
@dataclass(frozen=True)
class Account:
    """
    Cuenta contable. Puede ser un Activo, Pasivo, Ingreso, Gasto o Patrimonio.
 
    - initial_balance: Saldo al momento de crear la cuenta (referencia histórica).
    - current_balance: Saldo actual = initial_balance + suma de transacciones.
      Se almacena desnormalizado para evitar N+1 queries en listados.
    """
    id: UUID
    name: str
    type: AccountType
    initial_balance: Money = field(default_factory=Money.zero)
    current_balance: Money = field(default_factory=Money.zero)
    is_active: bool = True
    account_number: Optional[str] = None
    parent_account_id: Optional[UUID] = None
 
    def __post_init__(self):
        self._validate_balance()
 
    def _validate_balance(self):
        if self.type in (AccountType.ASSET, AccountType.LIABILITY):
            if self.current_balance.amount < 0:
                raise ValueError(
                    f"La cuenta '{self.name}' de tipo {self.type.value} "
                    f"no puede tener saldo negativo ({self.current_balance.amount})."
                )
            if self.initial_balance.amount < 0:
                raise ValueError(
                    f"El saldo inicial de la cuenta '{self.name}' "
                    f"de tipo {self.type.value} no puede ser negativo."
                )
 
 
@dataclass(frozen=True)
class Tag:
    """Etiqueta para categorizar transacciones. El nombre es único."""
    id: UUID
    name: str
    color: str = "#a8a8a8"
 
 
@dataclass(frozen=True)
class TransactionEntry:
    """
    Apunte contable dentro de una transacción (partida doble).
 
    - amount > 0 → Debe (Debit)
    - amount < 0 → Haber (Credit)
    """
    account_id: UUID
    amount: Money
 
 
@dataclass
class Transaction:
    """
    Movimiento financiero completo.
    La suma de todos los apuntes debe ser siempre CERO.
    """
    id: UUID
    date: datetime
    entries: list[TransactionEntry]
    description: Optional[str] = None
    related_transaction_id: Optional[UUID] = None
    tags_ids: list[UUID] = field(default_factory=list)
 
    def validate(self):
        if not self.entries:
            raise ValueError("La transacción debe tener al menos un apunte.")
        if len(self.entries) < 2:
            raise ValueError("Mínimo 2 apuntes requeridos (partida doble).")
 
        base_currency = self.entries[0].amount.currency
        if any(e.amount.currency != base_currency for e in self.entries):
            raise ValueError("Transacciones multi-moneda no soportadas.")
 
        total = sum(
            (entry.amount for entry in self.entries),
            Money.zero(base_currency),
        )
        if not total.is_zero():
            from .exceptions import TransactionImbalancedError
            raise TransactionImbalancedError(total.amount)
 
 
@dataclass(frozen=True)
class RecurringRule:
    """
    Regla para automatizar transacciones recurrentes.
 
    Soporta dos patrones:
    - CALENDAR_BASED: día fijo en el calendario (ej. día 15 de cada mes).
    - INTERVAL_BASED: cada N unidades desde la última ejecución.
    """
    id: UUID
    amount: Money
    source_account_id: UUID
    destination_account_id: UUID
    transaction_type: TransactionType
 
    description: Optional[str] = None
    tags_ids: list[UUID] = field(default_factory=list)
 
    # Configuración de recurrencia
    recurrence_type: RecurrenceType = RecurrenceType.CALENDAR_BASED
    frequency: Optional[RecurrenceFrequency] = None
    day_of_execution: Optional[int] = None
    interval_value: Optional[int] = None
    interval_unit: Optional[IntervalUnit] = None
 
    # Control temporal
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    is_active: bool = True
    last_execution_date: Optional[datetime] = None
    next_execution_date: Optional[datetime] = None
 
    def __post_init__(self):
        self._validate()
 
    def _validate(self):
        if self.recurrence_type == RecurrenceType.CALENDAR_BASED:
            if self.frequency is None:
                raise ValueError("CALENDAR_BASED requiere 'frequency'.")
            if self.day_of_execution is None:
                raise ValueError("CALENDAR_BASED requiere 'day_of_execution'.")
            if self.frequency == RecurrenceFrequency.MONTHLY and not 1 <= self.day_of_execution <= 31:
                raise ValueError("Para frecuencia MENSUAL, 'day_of_execution' debe estar entre 1 y 31.")
            if self.frequency == RecurrenceFrequency.WEEKLY and not 1 <= self.day_of_execution <= 7:
                raise ValueError("Para frecuencia SEMANAL, 'day_of_execution' debe estar entre 1 (lunes) y 7 (domingo).")
 
        elif self.recurrence_type == RecurrenceType.INTERVAL_BASED:
            if not self.interval_value:
                raise ValueError("INTERVAL_BASED requiere 'interval_value'.")
            if not self.interval_unit:
                raise ValueError("INTERVAL_BASED requiere 'interval_unit'.")
            if self.interval_value <= 0:
                raise ValueError("'interval_value' debe ser mayor que 0.")
 
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("'end_date' no puede ser anterior a 'start_date'.")
 
        if self.amount.amount <= 0:
            raise ValueError("El monto debe ser mayor que 0.")
 
 
# ─────────────────────────────────────────
# Criterios de búsqueda (Value Objects)
# ─────────────────────────────────────────
 
@dataclass(frozen=True)
class AccountSearchCriteria:
    """Criterios de búsqueda para filtrar cuentas."""
    type: Optional[AccountType] = None
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    name_contains: Optional[str] = None
 
 
@dataclass(frozen=True)
class TransactionSearchCriteria:
    """
    Criterios de búsqueda para filtrar transacciones.
    El filtrado ocurre en la capa de infraestructura (SQL), no en Python.
    """
    # Filtros de cuenta
    account_id: Optional[UUID] = None           # Cualquier lado (origen o destino)
    source_account_id: Optional[UUID] = None
    destination_account_id: Optional[UUID] = None
 
    # Filtros de monto
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
 
    # Filtros de fecha
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
 
    # Filtros de contenido
    tag_ids: Optional[list[UUID]] = None
    description_contains: Optional[str] = None
 
    # Paginación
    page: int = 1
    page_size: int = 50
 
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size