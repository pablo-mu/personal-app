from dataclasses import dataclass
from src.application.services.account_service import AccountService
from src.application.services.transaction_service import TransactionService
from src.application.services.tag_service import TagService
from src.application.services.recurring_rule_service import RecurringRuleService
from src.application.services.report_service import ReportService

@dataclass(frozen=True)
class Services:
    """
    Contenedor inmutable para agrupar todos los servicios de la aplicación.
    Facilita la inyección de dependencias en la capa de presentación.
    """
    account: AccountService
    transaction: TransactionService
    tag: TagService
    recurring_rule: RecurringRuleService
    report: ReportService
