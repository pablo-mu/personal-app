from dash import Dash, html, dcc, Input, Output, State, callback, ALL
import pandas as pd
from decimal import Decimal
from datetime import datetime

from src.application.dtos import (
    AccountCreateDTO, 
    TransactionEntryDTO, 
    MoneySchema
)
from src.domain.models import AccountType

def init_dashboard(server, account_service, transaction_service, tag_service):
    """
    Inicializa la aplicación Dash.
    Recibe los servicios inyectados para conectar la UI con la lógica de negocio.
    """
    app = Dash(__name__, server=server, url_base_pathname='/')

    # --- LAYOUT ---
    app.layout = html.Div([
        html.H1("💰 Sistema de Finanzas Personales (Fase 1)", style={'textAlign': 'center'}),
        
        # TABS
        dcc.Tabs([
            dcc.Tab(label='Cuentas', children=[
                html.Div([
                    html.H3("Crear Nueva Cuenta"),
                    html.Div([
                        html.Label("Nombre:"),
                        dcc.Input(id='acc-name', type='text', placeholder='Ej: BBVA, Mercadona...'),
                        
                        html.Label("Tipo:"),
                        dcc.Dropdown(
                            id='acc-type',
                            options=[{'label': t.name, 'value': t.name} for t in AccountType],
                            value='ASSET'
                        ),
                        
                        html.Label("Saldo Inicial:"),
                        dcc.Input(id='acc-balance', type='number', value=0, step=0.01),
                        
                        html.Button('Crear Cuenta', id='btn-create-acc', n_clicks=0),
                    ], style={'display': 'flex', 'gap': '10px', 'alignItems': 'center', 'marginBottom': '20px'}),
                    
                    html.Div(id='msg-create-acc', style={'color': 'green'}),
                    
                    html.Hr(),
                    html.H3("Listado de Cuentas"),
                    html.Button('Actualizar Lista', id='btn-refresh-acc', n_clicks=0),
                    html.Div(id='table-accounts')
                ], style={'padding': '20px'})
            ]),
            
            dcc.Tab(label='Transacciones', children=[
                html.Div([
                    html.H3("Registrar Transacción"),
                    html.Div([
                        html.Div([
                            html.Label("Descripción:"),
                            dcc.Input(id='tx-desc', type='text', placeholder='Ej: Compra Semanal'),
                        ]),
                        html.Div([
                            html.Label("Monto (€):"),
                            dcc.Input(id='tx-amount', type='number', value=0, step=0.01),
                        ]),
                        html.Div([
                            html.Label("Origen (Sale dinero):"),
                            dcc.Dropdown(id='tx-source'),
                        ]),
                        html.Div([
                            html.Label("Destino (Entra dinero):"),
                            dcc.Dropdown(id='tx-dest'),
                        ]),
                        html.Button('Registrar', id='btn-create-tx', n_clicks=0),
                    ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '10px', 'marginBottom': '20px'}),
                    
                    html.Div(id='msg-create-tx', style={'color': 'blue'}),
                    
                    html.Hr(),
                    html.H3("Historial de Transacciones"),
                    html.Button('Actualizar Historial', id='btn-refresh-tx', n_clicks=0),
                    html.Div(id='table-transactions')
                ], style={'padding': '20px'})
            ]),
        ])
    ], style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1000px', 'margin': '0 auto'})

    # --- CALLBACKS ---

    # 1. Crear Cuenta
    @app.callback(
        Output('msg-create-acc', 'children'),
        Input('btn-create-acc', 'n_clicks'),
        State('acc-name', 'value'),
        State('acc-type', 'value'),
        State('acc-balance', 'value'),
        prevent_initial_call=True
    )
    def create_account(n_clicks, name, type_str, balance):
        if not name:
            return "❌ El nombre es obligatorio."
        
        try:
            # Convertimos string del dropdown al Enum
            acc_type = AccountType[type_str]
            
            dto = AccountCreateDTO(
                name=name,
                type=acc_type,
                initial_balance=MoneySchema(amount=Decimal(str(balance)), currency="EUR")
            )
            account_service.create_account(dto)
            return f"✅ Cuenta '{name}' creada con éxito."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    # 2. Listar Cuentas
    @app.callback(
        Output('table-accounts', 'children'),
        Input('btn-refresh-acc', 'n_clicks'),
        Input('btn-create-acc', 'n_clicks'), # Actualizar al crear
    )
    def list_accounts(n_refresh, n_create):
        accounts = account_service.list_accounts()
        
        if not accounts:
            return "No hay cuentas registradas."

        # Convertimos a DataFrame para facilitar la tabla HTML
        data = [
            {
                "ID": str(acc.id),
                "Nombre": acc.name,
                "Tipo": acc.type.name,
                "Saldo Inicial": f"{acc.initial_balance.amount} {acc.initial_balance.currency}"
            }
            for acc in accounts
        ]
        df = pd.DataFrame(data)
        
        return html.Table([
            html.Thead(html.Tr([html.Th(col) for col in df.columns])),
            html.Tbody([
                html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
                for i in range(len(df))
            ])
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'border': '1px solid #ddd'})

    # 3. Cargar Dropdowns de Transacciones (Cuentas)
    @app.callback(
        Output('tx-source', 'options'),
        Output('tx-dest', 'options'),
        Input('btn-refresh-acc', 'n_clicks'), # Recargar si actualizamos cuentas
        Input('btn-create-acc', 'n_clicks'),
    )
    def update_account_dropdowns(n1, n2):
        accounts = account_service.list_accounts()
        options = [{'label': f"{acc.name} ({acc.type.name})", 'value': str(acc.id)} for acc in accounts]
        return options, options

    # 4. Crear Transacción
    @app.callback(
        Output('msg-create-tx', 'children'),
        Input('btn-create-tx', 'n_clicks'),
        State('tx-desc', 'value'),
        State('tx-amount', 'value'),
        State('tx-source', 'value'),
        State('tx-dest', 'value'),
        prevent_initial_call=True
    )
    def create_transaction(n_clicks, desc, amount, source_id, dest_id):
        if not all([desc, amount, source_id, dest_id]):
            return "❌ Todos los campos son obligatorios."
        
        try:
            dto = TransactionEntryDTO(
                description=desc,
                amount=MoneySchema(amount=Decimal(str(amount)), currency="EUR"),
                source_account_id=source_id,
                destination_account_id=dest_id,
                date=datetime.now(),
                tags_ids=[] # Opcional por ahora
            )
            transaction_service.create_transaction(dto)
            return "✅ Transacción registrada correctamente."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    # 5. Listar Transacciones (Simplificado, falta implementar list_transactions en servicio)
    # Como no implementamos list_transactions en el servicio anterior, lo dejamos pendiente o
    # usamos el repositorio directamente (no recomendado) o añadimos el método.
    # Por ahora, mostraremos un mensaje.
    
    return app
