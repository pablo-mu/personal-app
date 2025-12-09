from dash import html, dcc, Input, Output, State
import pandas as pd
from decimal import Decimal
from src.application.dtos import AccountCreateDTO, MoneySchema
from src.domain.models import AccountType
from src.domain.exceptions import AccountAlreadyExistsError

def get_layout():
    return html.Div([
        html.Div([
            html.H4("ℹ️ Concepto Importante", style={'marginTop': '0'}),
            html.P("En este sistema de contabilidad de doble entrada, todo es una 'Cuenta'."),
            html.Ul([
                html.Li("Tus cuentas bancarias o efectivo son cuentas de tipo ASSET (Activo)."),
                html.Li("Tus categorías de gasto (Comida, Alquiler) son cuentas de tipo EXPENSE (Gasto)."),
                html.Li("Tus fuentes de ingreso (Nómina) son cuentas de tipo INCOME (Ingreso).")
            ])
        ], style={'backgroundColor': '#e8f4f8', 'padding': '15px', 'borderRadius': '5px', 'marginBottom': '20px'}),

        html.H3("Crear Nueva Cuenta / Categoría"),
        html.Div([
            html.Div([
                html.Label("Nombre:"),
                dcc.Input(id='acc-name', type='text', placeholder='Ej: BBVA, Mercadona, Nómina...', style={'width': '100%'}),
            ], style={'flex': '1'}),
            
            html.Div([
                html.Label("Tipo:"),
                dcc.Dropdown(
                    id='acc-type',
                    options=[
                        {'label': 'Activo (Banco/Efectivo)', 'value': AccountType.ASSET.name},
                        {'label': 'Gasto (Categoría de Gasto)', 'value': AccountType.EXPENSE.name},
                        {'label': 'Ingreso (Fuente de Ingreso)', 'value': AccountType.INCOME.name},
                        {'label': 'Pasivo (Deudas/Tarjetas)', 'value': AccountType.LIABILITY.name},
                        {'label': 'Patrimonio', 'value': AccountType.EQUITY.name},
                    ],
                    value=AccountType.ASSET.name
                ),
            ], style={'flex': '1'}),
            
            html.Div([
                html.Label("Saldo Inicial (€):"),
                dcc.Input(id='acc-balance', type='number', value=0, step=0.01, style={'width': '100%'}),
            ], style={'flex': '1'}),
            
            html.Button('Crear', id='btn-create-acc', n_clicks=0, style={'height': '38px', 'alignSelf': 'flex-end'}),
        ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '20px'}),
        
        html.Div(id='msg-create-acc', style={'fontWeight': 'bold'}),
        
        html.Hr(),
        html.H3("Listado de Cuentas"),
        html.Button('🔄 Actualizar Lista', id='btn-refresh-acc', n_clicks=0),
        html.Div(id='table-accounts', style={'marginTop': '10px'})
    ], style={'padding': '20px'})

def register_callbacks(app, account_service):
    # 1. Crear Cuenta
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
                name=name,
                type=acc_type,
                initial_balance=MoneySchema(amount=Decimal(str(balance)), currency="EUR")
            )
            account_service.create_account(dto)
            return f"✅ Cuenta '{name}' creada con éxito.", {'color': 'green'}
        except AccountAlreadyExistsError as e:
            return f"⚠️ {str(e)}", {'color': 'orange'}
        except Exception as e:
            return f"❌ Error: {str(e)}", {'color': 'red'}

    # 2. Listar Cuentas
    @app.callback(
        Output('table-accounts', 'children'),
        Input('btn-refresh-acc', 'n_clicks'),
        Input('btn-create-acc', 'n_clicks'),
    )
    def list_accounts(n_refresh, n_create):
        accounts = account_service.list_accounts()
        if not accounts:
            return "No hay cuentas registradas."

        data = [{
            "Nombre": acc.name,
            "Tipo": acc.type.name,
            "Saldo Inicial": f"{acc.initial_balance.amount} {acc.initial_balance.currency}"
        } for acc in accounts]
        
        df = pd.DataFrame(data)
        return html.Table([
            html.Thead(html.Tr([html.Th(col) for col in df.columns])),
            html.Tbody([
                html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
                for i in range(len(df))
            ])
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'border': '1px solid #ddd', 'textAlign': 'left'})
