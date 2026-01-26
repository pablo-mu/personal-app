from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, UUID4, field_validator, model_validator

from src.domain import AccountType

# --- SCHEMAS AUXILIARES ---

class MoneySchema(BaseModel):
    """
    Esquema para validar entrada/salida de dinero en JSON.
    Ejemplo: {"amount": 10.50, "currency": "EUR"}
    """
    amount: Decimal
    currency: str = "EUR"

# --- ACCOUNTS ---

class AccountCreateDTO(BaseModel):
    """ DTO de Entrada: Lo que el usuario envía para crear cuenta """
    name: str
    type: AccountType
    # Pydantic validará que sea un objeto con amount y currency
    initial_balance: MoneySchema = Field(default_factory=lambda: MoneySchema(amount=Decimal('0.00')))
    is_active: bool = True
    account_number: Optional[str] = None
    parent_account_id: Optional[UUID4] = None

class AccountOutputDTO(BaseModel):
    """ DTO de Salida: Lo que respondemos al usuario """
    id: UUID4
    name: str
    type: AccountType
    initial_balance: MoneySchema
    current_balance: MoneySchema  # Saldo actualizado con transacciones
    is_active: bool
    account_number: Optional[str] = None
    parent_account_id: Optional[UUID4] = None

    # Esto permite crear el DTO directamente desde la Entidad de Dominio
    model_config = {"from_attributes": True}

class AccountUpdateDTO(BaseModel):
    """ DTO para actualizar una cuenta existente """
    name: Optional[str] = None
    type: Optional[AccountType] = None
    is_active: Optional[bool] = None
    account_number: Optional[str] = None
    parent_account_id: Optional[UUID4] = None

class AccountFilterDTO(BaseModel):
    """
    DTO para filtrar búsquedas de cuentas.
    Todos los campos son opcionales.
    """
    type: Optional[AccountType] = None
    parent_id: Optional[UUID4] = None
    is_active: Optional[bool] = None  # None = Traer todas, True = Solo activas
    name_contains: Optional[str] = None
    
    # Configuración extra si quieres que sea inmutable (opcional)
    model_config = {"frozen": True}
    
# --- TRANSACTIONS ---

class TransactionEntryDTO(BaseModel):
    """ DTO de Entrada: Crear transacción """
    description: Optional[str] = None
    amount: MoneySchema
    source_account_id: UUID4
    destination_account_id: UUID4
    date: datetime = Field(default_factory=datetime.now)
    tags_ids: List[UUID4] = Field(default_factory=list)
    related_transaction_id: Optional[UUID4] = None

    @field_validator('amount')
    def validate_positive_amount(cls, v):
        if v.amount <= 0:
            raise ValueError('El monto debe ser positivo')
        return v

class TransactionOutputDTO(BaseModel):
    """ DTO de Salida: Leer transacción """
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

# --- TAGS ---

class TagDTO(BaseModel):
    """ DTO para Etiquetas (Sirve para entrada y salida) """
    id: Optional[UUID4] = None # Opcional al crear, obligatorio al leer
    name: str  # Debe ser único
    color: str = "#a8a8a8"  # Color hexadecimal, por defecto gris

    model_config = {"from_attributes": True}

# --- RECURRING RULES ---

from src.domain.models import RecurrenceType, RecurrenceFrequency, IntervalUnit, TransactionType

class RecurringRuleCreateDTO(BaseModel):
    """DTO de Entrada: Crear regla recurrente"""
    description: Optional[str] = None
    amount: MoneySchema
    source_account_id: UUID4
    destination_account_id: UUID4
    transaction_type: TransactionType
    tags_ids: List[UUID4] = Field(default_factory=list)
    
    # Configuración de recurrencia
    recurrence_type: RecurrenceType = RecurrenceType.CALENDAR_BASED
    
    # Calendar based
    frequency: Optional[RecurrenceFrequency] = None
    day_of_execution: Optional[int] = None
    
    # Interval based
    interval_value: Optional[int] = None
    interval_unit: Optional[IntervalUnit] = None
    
    # Control de ejecución
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    is_active: bool = True
    
    @model_validator(mode='after')
    def validate_recurrence_config(self):
        """Valida que la configuración sea coherente según el tipo"""
        if self.recurrence_type == RecurrenceType.CALENDAR_BASED:
            if not self.frequency:
                raise ValueError("CALENDAR_BASED requiere especificar 'frequency'")
            if self.day_of_execution is None:
                raise ValueError("CALENDAR_BASED requiere especificar 'day_of_execution'")
        
        elif self.recurrence_type == RecurrenceType.INTERVAL_BASED:
            if not self.interval_value:
                raise ValueError("INTERVAL_BASED requiere especificar 'interval_value'")
            if not self.interval_unit:
                raise ValueError("INTERVAL_BASED requiere especificar 'interval_unit'")
        
        return self

class RecurringRuleUpdateDTO(BaseModel):
    """DTO para actualizar regla recurrente"""
    description: Optional[str] = None
    amount: Optional[MoneySchema] = None
    tags_ids: Optional[List[UUID4]] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class RecurringRuleOutputDTO(BaseModel):
    """DTO de Salida: Leer regla recurrente"""
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