"""
Views Module - Interfaz de usuario organizada por sección

Estructura:
- tracking_view: Vista principal de seguimiento diario
- dashboard: Vistas de visualización y resumen
- planning: Vistas de planificación financiera
- config: Vistas de configuración del sistema
- info: Vistas informativas
"""

# Vista principal (raíz)
from .tracking_view import layout_daily, register_callbacks as register_tracking_callbacks

# Dashboard
from .dashboard import layout_summary

# Planning
from .planning import layout_budgets, layout_recurring, register_recurring_callbacks

# Config
from .config import (
    layout_transactions_config, register_transactions_callbacks,
    layout_accounts, register_accounts_callbacks,
    layout_categories, register_categories_callbacks
)

# Info
from .info import layout_about

__all__ = [
    # Main
    'layout_daily', 'register_tracking_callbacks',
    
    # Dashboard
    'layout_summary',
    
    # Planning
    'layout_budgets', 'layout_recurring', 'register_recurring_callbacks',
    
    # Config
    'layout_transactions_config', 'register_transactions_callbacks',
    'layout_accounts', 'register_accounts_callbacks',
    'layout_categories', 'register_categories_callbacks',
    
    # Info
    'layout_about'
]
