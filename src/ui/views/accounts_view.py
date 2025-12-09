from dash import html, dcc, Input, Output, State
import pandas as pd
from decimal import Decimal
from application.services.account_service import AccountService
from src.application.dtos import AccountCreateDTO, MoneySchema
from src.domain.models import AccountType
from src.domain import AccountAlreadyExistsError

def registert_callbacks(app, account_service: AccountService):
    @app.callback(
        Output('msg-create-acc', 'children'),
        Output('msg-create-acc', 'style'),
        Input('btn-create-acc', 'n_clicks'),
        State('acc-name', 'value'),
        State('acc-type', 'value'),
        State('acc-balance', 'value'),
        prevent_initial_call=True
    )

    def create_account(n_clicks, name, type_str, balance):
        if not name:
            return "❌ El nombre es obligatorio.", {'color': 'red'}
        
        try:
            acc_type = AccountType[type_str]
            dto = AccountCreateDTO(
                name = name,
                type = acc_type,
                initial_balance = MoneySchema(amount=Decimal(str(balance)), currency="EUR")
            )
            account_service.create_account(dto)
            return f"✅ Cuenta '{name}' creada con éxito.", {'color': 'green'}
        except AccountAlreadyExistsError as e:
            return f"⚠️ {str(e)}", {'color': 'orange'}
        except Exception as e:
            return f"❌ Error: {str(e)}", {'color': 'red'}