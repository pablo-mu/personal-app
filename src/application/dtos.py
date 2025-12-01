from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from src.domain import AccountType, Money
from uuid import UUID

@dataclass
class AccountCreateDTO:
    """ DTO para crear una nueva cuenta """
    name: str
    type: AccountType  
    initial_balance: Money = Money.zero()

@dataclass
class AccountOutputDTO:
    """ DTO para representar una cuenta """
    id: UUID
    name: str
    type: AccountType
    initial_balance: Money

@dataclass
class TransactionEntryDTO:
    """ DTO para registrar un apunte de transacción """
    description: str
    amount: Money
    source_account_id: UUID
    destination_account_id: UUID
    date: datetime = field(default_factory=datetime.now)
    tags_ids: List[UUID] = field(default_factory=list)
    related_transaction_id: Optional[UUID] = None

@dataclass
class TransactionOutputDTO:
    """ DTO para representar una transacción completa """
    id: UUID
    date: datetime
    description: str
    amount: Money
    source_account_name: str
    destination_account_name: str
    tags: List[str]


@dataclass
class TagDTO:
    """ DTO para representar una etiqueta """
    id: UUID
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None

