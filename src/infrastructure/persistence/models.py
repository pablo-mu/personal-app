import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Numeric, Table
from sqlalchemy.orm import relationship
from .db import Base

# --- TABLA INTERMEDIA (Many-to-Many) para Transacciones <-> Etiquetas ---
transaction_tags = Table(
    "transaction_tags",
    Base.metadata,
    Column("transaction_id", String(36), ForeignKey("transactions.id"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id"), primary_key=True),
)

class AccountModel(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(String, nullable = False)
    is_active = Column(Integer, default=1) # SQLite no tiene Boolean nativo, usamos 0/1
    parent_account_id = Column(String(36), nullable=True)
    account_number = Column(String, nullable=True)

    initial_balance = Column(Numeric(10, 2), default = 0.00)
    initial_balance_currency = Column(String(3), default = "EUR")

    entries = relationship("TransactionEntryModel", back_populates="account")

class TagModel(Base):
    __tablename__ = "tags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)  # UNIQUE constraint
    color = Column(String(7), nullable=False, default="#a8a8a8")  # Color hexadecimal obligatorio

    # Relación
    transactions = relationship(
        "TransactionModel",
        secondary = transaction_tags,
        back_populates="tags")

class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)

    # Campo para Bizums/Devoluciones
    related_transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=True)

    # Relación recursiva para acceder a la transacción padre/hijos
    related_transaction = relationship("TransactionModel", remote_side=[id], backref="refunds")

    # Relaciones
    entries = relationship("TransactionEntryModel", back_populates="transaction", cascade="all, delete-orphan")
    tags = relationship(
        "TagModel",
        secondary=transaction_tags,
        back_populates="transactions"
    )

class TransactionEntryModel(Base):
    """
    Representa cada línea de la transacción en la base de datos.
    """
    __tablename__ = "transaction_entries"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=False)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)

    # Relaciones
    transaction = relationship("TransactionModel", back_populates="entries")
    account = relationship("AccountModel", back_populates="entries") # <--- Conectamos con la relación nueva
    