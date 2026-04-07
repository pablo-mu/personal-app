"""
Servicio de Reportes.

Genera resúmenes y análisis financieros consultando los repositorios
a través de la Unit of Work. No modifica datos, solo los lee y agrega.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from src.application.dtos import (
    AccountBalanceSummaryDTO,
    CategorySummaryDTO,
    MoneySchema,
    MonthlyEvolutionDTO,
    NetWorthDTO,
    PeriodSummaryDTO,
    TransactionFilterDTO,
    PaginationParams,
)
from src.application.ports import AbstractUnitOfWork
from src.domain.models import AccountType, TransactionSearchCriteria


_ZERO = Decimal("0.00")
_MONTHS_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


class ReportService:
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    # ─────────────────────────────────────
    # Patrimonio Neto
    # ─────────────────────────────────────

    def get_net_worth(self, currency: str = "EUR") -> NetWorthDTO:
        """
        Calcula el patrimonio neto (Activos − Pasivos).
        Solo considera cuentas activas de tipo ASSET y LIABILITY.
        """
        with self.uow:
            all_accounts = self.uow.accounts.list()

            assets      = [a for a in all_accounts if a.type == AccountType.ASSET      and a.is_active]
            liabilities = [a for a in all_accounts if a.type == AccountType.LIABILITY  and a.is_active]

            total_assets = sum((a.current_balance.amount for a in assets), _ZERO)
            total_liab   = sum((a.current_balance.amount for a in liabilities), _ZERO)

            def to_summary(account):
                return AccountBalanceSummaryDTO(
                    id=account.id,
                    name=account.name,
                    type=account.type,
                    current_balance=MoneySchema(amount=account.current_balance.amount, currency=account.current_balance.currency),
                )

            return NetWorthDTO(
                total_assets=MoneySchema(amount=total_assets, currency=currency),
                total_liabilities=MoneySchema(amount=total_liab, currency=currency),
                net_worth=MoneySchema(amount=total_assets - total_liab, currency=currency),
                accounts=[to_summary(a) for a in assets + liabilities],
            )

    # ─────────────────────────────────────
    # Resumen por período
    # ─────────────────────────────────────

    def get_period_summary(
        self,
        date_from: datetime,
        date_to: datetime,
        currency: str = "EUR",
    ) -> PeriodSummaryDTO:
        """
        Suma ingresos y gastos en el período indicado y los desglosa por categoría.
        Un ingreso es una transacción cuya cuenta ORIGEN es de tipo INCOME.
        Un gasto es una transacción cuya cuenta DESTINO es de tipo EXPENSE.
        """
        with self.uow:
            criteria = TransactionSearchCriteria(
                date_from=date_from,
                date_to=date_to,
                page=1,
                page_size=10_000,  # Traer todo para el cálculo
            )
            transactions, _ = self.uow.transactions.search(criteria)
            all_accounts = {str(a.id): a for a in self.uow.accounts.list()}

            total_income  = _ZERO
            total_expense = _ZERO
            income_by_cat: dict  = {}   # category_id → {name, total, count}
            expense_by_cat: dict = {}

            for tx in transactions:
                # Identificar apuntes positivos (destino) y negativos (origen)
                credit_entry = next((e for e in tx.entries if e.amount.amount > 0), None)
                debit_entry  = next((e for e in tx.entries if e.amount.amount < 0), None)

                if not credit_entry or not debit_entry:
                    continue

                src_acc  = all_accounts.get(str(debit_entry.account_id))
                dest_acc = all_accounts.get(str(credit_entry.account_id))

                amount = credit_entry.amount.amount

                # INGRESO: origen es categoría de tipo INCOME
                if src_acc and src_acc.type == AccountType.INCOME:
                    total_income += amount
                    key = str(src_acc.id)
                    if key not in income_by_cat:
                        income_by_cat[key] = {"name": src_acc.name, "total": _ZERO, "count": 0}
                    income_by_cat[key]["total"] += amount
                    income_by_cat[key]["count"] += 1

                # GASTO: destino es categoría de tipo EXPENSE
                elif dest_acc and dest_acc.type == AccountType.EXPENSE:
                    total_expense += amount
                    key = str(dest_acc.id)
                    if key not in expense_by_cat:
                        expense_by_cat[key] = {"name": dest_acc.name, "total": _ZERO, "count": 0}
                    expense_by_cat[key]["total"] += amount
                    expense_by_cat[key]["count"] += 1

            def _to_category_dto(cat_id: str, data: dict, total_ref: Decimal) -> CategorySummaryDTO:
                from uuid import UUID
                pct = float(data["total"] / total_ref * 100) if total_ref else 0.0
                return CategorySummaryDTO(
                    category_id=UUID(cat_id),
                    category_name=data["name"],
                    total=MoneySchema(amount=data["total"], currency=currency),
                    transaction_count=data["count"],
                    percentage=round(pct, 2),
                )

            expense_categories = sorted(
                [_to_category_dto(k, v, total_expense) for k, v in expense_by_cat.items()],
                key=lambda x: x.total.amount,
                reverse=True,
            )
            income_categories = sorted(
                [_to_category_dto(k, v, total_income) for k, v in income_by_cat.items()],
                key=lambda x: x.total.amount,
                reverse=True,
            )

            return PeriodSummaryDTO(
                period_start=date_from,
                period_end=date_to,
                total_income=MoneySchema(amount=total_income, currency=currency),
                total_expense=MoneySchema(amount=total_expense, currency=currency),
                net=MoneySchema(amount=total_income - total_expense, currency=currency),
                expense_by_category=expense_categories,
                income_by_category=income_categories,
            )

    # ─────────────────────────────────────
    # Evolución mensual
    # ─────────────────────────────────────

    def get_monthly_evolution(
        self,
        months: int = 12,
        currency: str = "EUR",
    ) -> List[MonthlyEvolutionDTO]:
        """
        Devuelve el resumen de ingresos/gastos para los últimos N meses.
        """
        from dateutil.relativedelta import relativedelta

        today = datetime.now()
        result: List[MonthlyEvolutionDTO] = []

        for i in range(months - 1, -1, -1):
            first_day = (today - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day  = (first_day + relativedelta(months=1))

            summary = self.get_period_summary(first_day, last_day, currency)
            result.append(MonthlyEvolutionDTO(
                year=first_day.year,
                month=first_day.month,
                label=f"{_MONTHS_ES[first_day.month - 1]} {first_day.year}",
                income=summary.total_income,
                expense=summary.total_expense,
                net=summary.net,
            ))

        return result