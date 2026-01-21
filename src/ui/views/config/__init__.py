"""Configuration views - Configuración del sistema"""
from .transactions_view import layout_transactions_config, register_callbacks as register_transactions_callbacks
from .accounts_view import layout_accounts, register_callbacks as register_accounts_callbacks
from .categories_view import layout_categories, register_callbacks as register_categories_callbacks

__all__ = [
    'layout_transactions_config', 'register_transactions_callbacks',
    'layout_accounts', 'register_accounts_callbacks',
    'layout_categories', 'register_categories_callbacks'
]
