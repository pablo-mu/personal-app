import uuid
from datetime import datetime
from decimal import Decimal

from .exceptions import NegativeAmountError, TransactionImbalancedError
from .models import Transaction, TransactionEntry
from .value_objects import Money


class TransactionFactory:
    """Fábrica para crear transacciones válidas con los apuntes de partida doble."""

    @staticmethod
    def create_transaction(
        description: str,
        source_account_id: uuid.UUID,
        destination_account_id: uuid.UUID,
        amount: Decimal,
        currency: str = "EUR",
        date: datetime = None,
        related_transaction_id: uuid.UUID = None,
        tags_ids: list[uuid.UUID] = None,
    ) -> Transaction:
        if date is None:
            date = datetime.now()

        if amount <= 0:
            raise NegativeAmountError("monto de la transacción")

        amount_money = Money(amount, currency)

        entries = [
            TransactionEntry(account_id=source_account_id,      amount=-amount_money),
            TransactionEntry(account_id=destination_account_id, amount=amount_money),
        ]

        transaction = Transaction(
            id=uuid.uuid4(),
            date=date,
            description=description or "",
            entries=entries,
            related_transaction_id=related_transaction_id,
            tags_ids=tags_ids or [],
        )

        transaction.validate()
        return transaction