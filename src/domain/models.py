"""
Definimos los modelos de dominio para la aplicación de finanzas personales.
Estos modelos representan las entidades principales y básicas de la aplicación.
Cada modelo está diseñado utilizando dataclasses para facilitar la gestión de datos y asegurar la inmutabilidad donde sea necesario.
Se definen los campos para seguir las mejores prácticas de tipado, 
de responsabilidad única. Y así, construir la base de la contabilidad de partida doble.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID
from enum import Enum, auto
from .value_objects import Money

class AccountType(Enum): 
    """
    Tipos de cuentas para la contabilidad de partida doble.
    Se define el nombre en español como valor y una descripción como metadato.
    """
    ASSET = ("Activo", "Dinero que tengo o poseo. (Efectivo, cuentas bancarias, inversiones).")
    LIABILITY = ("Pasivo", "Dinero que debo. (Préstamos, tarjetas de crédito).")
    INCOME = ("Ingreso", "Dinero que recibo. (Salario, ventas).")
    EXPENSE = ("Gasto", "Dinero que gasto. (Alquiler, comida, ocio).")
    EQUITY = ("Patrimonio", "Valor neto (activos menos pasivos).")

    def __new__(cls, label, description):
        obj = object.__new__(cls)
        obj._value_ = label
        obj.description = description
        return obj
    
@dataclass(frozen = True)
class Account:
    """
    Representa una cuenta en la aplicación de finanzas personales.
    Cada cuenta tiene un identificador único, un nombre, un tipo y un saldo.
    
    - initial_balance: Saldo registrado al crear la cuenta (referencia histórica).
    - current_balance: Saldo actual calculado (initial_balance + todas las transacciones).
      Se actualiza automáticamente con cada transacción para mejor rendimiento.
    
    Validaciones:
    - ASSET (Activo): No puede tener saldo negativo (no puedes tener -500€ en efectivo).
    - LIABILITY (Pasivo): No puede tener saldo negativo (si te deben dinero, es un activo).
    """
    id: UUID
    name: str
    type: AccountType
    initial_balance: Money = field(default_factory=Money.zero)
    current_balance: Money = field(default_factory=Money.zero)  # Sincronizado con transacciones
    is_active: bool = True
    account_number: Optional[str] = None
    parent_account_id: Optional[UUID] = None  # Para cuentas jerárquicas
    
    def __post_init__(self):
        """Valida el saldo según el tipo de cuenta."""
        self._validate_balance()
    
    def _validate_balance(self):
        """
        Valida que el balance sea coherente con el tipo de cuenta.
        
        Raises:
            ValueError: Si el balance no es válido para el tipo de cuenta.
        """
        # Validar saldo actual (current_balance)
        if self.current_balance.amount < 0:
            if self.type == AccountType.ASSET:
                raise ValueError(
                    f"Una cuenta de tipo ACTIVO '{self.name}' no puede tener saldo negativo. "
                    f"Saldo actual: {self.current_balance.amount} {self.current_balance.currency}"
                )
            elif self.type == AccountType.LIABILITY:
                raise ValueError(
                    f"Una cuenta de tipo PASIVO '{self.name}' no puede tener saldo negativo. "
                    f"Si te deben dinero, debería ser un ACTIVO, no un PASIVO. "
                    f"Saldo actual: {self.current_balance.amount} {self.current_balance.currency}"
                )
        
        # Validar saldo inicial también
        if self.initial_balance.amount < 0:
            if self.type in [AccountType.ASSET, AccountType.LIABILITY]:
                raise ValueError(
                    f"El saldo inicial de una cuenta '{self.name}' de tipo {self.type.value} "
                    f"no puede ser negativo. Valor: {self.initial_balance.amount} {self.initial_balance.currency}"
                )

@dataclass(frozen=True)
class AccountSearchCriteria:
    """
    Criterios de búsqueda para filtrar cuentas en el dominio.
    Desacopla la capa de persistencia de los DTOs de aplicación.
    """
    type: Optional[AccountType] = None
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    name_contains: Optional[str] = None

@dataclass(frozen = True)
class Tag:
    """
    Representa una etiqueta para categorizar transacciones.
    El nombre debe ser único en el sistema.
    """
    id: UUID
    name: str  # UNIQUE constraint en BD
    color: str = "#a8a8a8"  # Color en formato hexadecimal, por defecto azul

@dataclass(frozen = True)
class TransactionEntry:
    """
    Representa un apunte individual (línea) dentro de una transacción.
    En partida doble, cada línea afecta a una cuenta específica.

    - amount > 0: Debe (Debit) -> Aumenta activos/gastos, disminuye pasivos/ingresos.
    - amount < 0: Haber (Credit) -> Disminuye activos/gastos, aumenta pasivos/ingresos.
    """
    account_id: UUID
    amount: Money

@dataclass
class Transaction:
    """
    Representa un movimiento financiero completo.
    Una transacción consta de múltiples apuntes (líneas) cuya suma total
    debe ser siempre CERO para mantener el equilibrio contable.

    related_transacion_id: Permite vincular devoluciones o ajustes a transacciones originales 
    sin modificar el historial.
    """
    id: UUID
    date: datetime
    entries: list[TransactionEntry]
    description: Optional[str] = None
    related_transaction_id: Optional[UUID] = None
    tags_ids: list[UUID] = field(default_factory=list)

    def validate(self):
        """
        Valida la integridad de la transacción bajo el principio de partida doble.
        """
        if not self.entries:
            raise ValueError("La transacción debe tener al menos un apunte.")
        if len(self.entries) < 2:
            raise ValueError("Mínimo 2 apuntes requeridos.")
        
        base_currency = self.entries[0].amount.currency
        if any(e.amount.currency != base_currency for e in self.entries):
             raise ValueError("Transacciones multi-moneda no soportadas.")

        total = sum((entry.amount for entry in self.entries), Money.zero(base_currency))

        if not total.is_zero():
            raise ValueError(f"La transacción está desbalanceada. Suma total: {total.amount}")



class TransactionType(Enum):
    """Tipo de transacción recurrente."""
    INCOME = "Ingreso"
    EXPENSE = "Gasto"


class RecurrenceType(Enum):
    """ Tipo de patrón de recurrencia."""
    CALENDAR_BASED = "calendar"
    INTERVAL_BASED = "interval"


class RecurrenceFrequency(Enum):
    """ Frecuencia de recurrencia."""
    DAILY = "Diaria"
    WEEKLY = "Semanal"
    MONTHLY = "Mensual"
    YEARLY = "Anual"


class IntervalUnit(Enum):
    """Unidad de tiempo para recurrencias basadas en intervalos."""
    DAYS = "Días"
    WEEKS = "Semanas"
    MONTHS = "Meses"
    YEARS = "Años"

@dataclass(frozen = True)
class RecurringRule:
    """
    Regla para automatizar transacciones recurrentes.
    Soporta dos tipos de recurrencia:
    - Basada en calendario: Se repite en fechas específicas (ej. 1ro de cada mes).
    - Basada en intervalos: Se repite cada N días, semanas, meses o años desde la última ocurrencia.
    
    transaction_type indica si es un INGRESO o GASTO, lo cual determina cómo interpretar
    source_account_id y destination_account_id:
    - EXPENSE: source es cuenta activo (de donde sale), destination es categoría de gasto
    - INCOME: source es categoría de ingreso, destination es cuenta activo (donde entra)
    """
    # Campos obligatorios (sin valores por defecto)
    id: UUID
    amount: Money
    source_account_id: UUID
    destination_account_id: UUID
    transaction_type: TransactionType
    
    # Campos opcionales o con valores por defecto
    description: Optional[str] = None
    tags_ids: Optional[list[UUID]] = field(default_factory=list)

    # Configuración de recurrencia
    recurrence_type: RecurrenceType = RecurrenceType.CALENDAR_BASED

    # Calendar based 
    frequency: Optional[RecurrenceFrequency] = None
    day_of_execution: Optional[int] = None

    # Interval based
    interval_value: Optional[int] = None
    interval_unit: Optional[IntervalUnit] = None

    # Control de ejecución
    start_date: datetime = field(default_factory=lambda: datetime.now())
    end_date: Optional[datetime] = None
    is_active: bool = True
    last_execution_date: Optional[datetime] = None
    next_execution_date: Optional[datetime] = None

    def __post_init__(self):
        """Validaciones de integridad de la configuración de recurrencia."""
        # Validar coherencia según tipo de recurrencia
        if self.recurrence_type == RecurrenceType.CALENDAR_BASED:
            if self.frequency is None:
                raise ValueError("CALENDAR_BASED requiere especificar 'frequency'")
            if self.day_of_execution is None:
                raise ValueError("CALENDAR_BASED requiere especificar 'day_of_execution'")
            
            # Validar rango de day_of_execution según frecuencia
            if self.frequency == RecurrenceFrequency.MONTHLY:
                if not 1 <= self.day_of_execution <= 31:
                    raise ValueError(f"Para frecuencia MENSUAL, day_of_execution debe estar entre 1 y 31. Valor: {self.day_of_execution}")
            elif self.frequency == RecurrenceFrequency.WEEKLY:
                if not 1 <= self.day_of_execution <= 7:
                    raise ValueError(f"Para frecuencia SEMANAL, day_of_execution debe estar entre 1 (lunes) y 7 (domingo). Valor: {self.day_of_execution}")
        
        elif self.recurrence_type == RecurrenceType.INTERVAL_BASED:
            if self.interval_value is None:
                raise ValueError("INTERVAL_BASED requiere especificar 'interval_value'")
            if self.interval_unit is None:
                raise ValueError("INTERVAL_BASED requiere especificar 'interval_unit'")
            if self.interval_value <= 0:
                raise ValueError(f"interval_value debe ser mayor a 0. Valor: {self.interval_value}")
        
        # Validar fechas
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError(f"end_date ({self.end_date}) no puede ser anterior a start_date ({self.start_date})")
        
        # Validar que amount sea válido
        if self.amount.amount <= 0:
            raise ValueError(f"El monto de la regla debe ser mayor a 0. Valor: {self.amount.amount}")