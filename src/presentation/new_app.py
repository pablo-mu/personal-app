from dash import Dash, html, dcc, Input, Output, State, callback, ALL
import pandas as pd
from decimal import Decimal
from datetime import datetime

from src.application.dtos import (
    AccountCreateDTO, 
    TransactionEntryDTO, 
    MoneySchema,
    TagDTO
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
        html.H1("💰 Sistema de Finanzas Personales", style={'textAlign': 'center', 'color': '#2c3e50'}),
        
        dcc.Tabs([
            # --- TAB 1: CUENTAS Y CATEGORÍAS ---
            dcc.Tab(label='Cuentas y Categorías', children=[
                html.Div([
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
                                    {'label': 'Activo (Banco/Efectivo)', 'value': 'ASSET'},
                                    {'label': 'Gasto (Categoría de Gasto)', 'value': 'EXPENSE'},
                                    {'label': 'Ingreso (Fuente de Ingreso)', 'value': 'INCOME'},
                                    {'label': 'Pasivo (Deudas/Tarjetas)', 'value': 'LIABILITY'},
                                ],
                                value='ASSET'
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
            ]),
            
            # --- TAB 2: ETIQUETAS (TAGS) ---
            dcc.Tab(label='Etiquetas (Tags)', children=[
                html.Div([
                    html.H3("Gestión de Etiquetas"),
                    html.P("Las etiquetas te permiten agrupar transacciones transversalmente (ej: 'Vacaciones', 'Boda') independientemente de la categoría."),
                    
                    html.Div([
                        html.Div([
                            html.Label("Nombre de la Etiqueta:"),
                            dcc.Input(id='tag-name', type='text', placeholder='Ej: Vacaciones 2024', style={'width': '100%'}),
                        ], style={'flex': '1'}),
                        
                        html.Div([
                            html.Label("Color (Hex):"),
                            dcc.Input(id='tag-color', type='text', placeholder='#FF5733', value='#3498db', style={'width': '100%'}),
                        ], style={'flex': '1'}),

                        html.Button('Crear Etiqueta', id='btn-create-tag', n_clicks=0, style={'height': '38px', 'alignSelf': 'flex-end'}),
                    ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '20px', 'maxWidth': '600px'}),

                    html.Div(id='msg-create-tag', style={'fontWeight': 'bold'}),
                    
                    html.Hr(),
                    html.H3("Etiquetas Existentes"),
                    html.Button('🔄 Actualizar Etiquetas', id='btn-refresh-tags', n_clicks=0),
                    html.Div(id='table-tags', style={'marginTop': '10px'})
                ], style={'padding': '20px'})
            ]),

            # --- TAB 3: TRANSACCIONES ---
            dcc.Tab(label='Transacciones', children=[
                html.Div([
                    html.H3("Registrar Transacción"),
                    html.Div([
                        html.Div([
                            html.Label("Descripción:"),
                            dcc.Input(id='tx-desc', type='text', placeholder='Ej: Compra Semanal', style={'width': '100%'}),
                        ]),
                        html.Div([
                            html.Label("Monto (€):"),
                            dcc.Input(id='tx-amount', type='number', value=0, step=0.01, style={'width': '100%'}),
                        ]),
                        html.Div([
                            html.Label("Origen (De dónde sale el dinero):"),
                            dcc.Dropdown(id='tx-source', placeholder="Selecciona cuenta origen..."),
                        ]),
                        html.Div([
                            html.Label("Destino (A dónde va / Gasto):"),
                            dcc.Dropdown(id='tx-dest', placeholder="Selecciona cuenta destino..."),
                        ]),
                        html.Div([
                            html.Label("Etiquetas (Opcional):"),
                            dcc.Dropdown(id='tx-tags', multi=True, placeholder="Selecciona etiquetas..."),
                        ], style={'gridColumn': 'span 2'}),
                        
                        html.Button('Registrar Transacción', id='btn-create-tx', n_clicks=0, style={'gridColumn': 'span 2', 'marginTop': '10px'}),
                    ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '15px', 'marginBottom': '20px', 'maxWidth': '800px'}),
                    
                    html.Div(id='msg-create-tx', style={'fontWeight': 'bold'}),
                    
                    html.Hr(),
                    html.H3("Historial de Transacciones"),
                    html.Button('🔄 Actualizar Historial', id='btn-refresh-tx', n_clicks=0),
                    html.Div(id='table-transactions', style={'marginTop': '10px'})
                ], style={'padding': '20px'})
            ]),
        ])
    ], style={'fontFamily': 'Segoe UI, Arial, sans-serif', 'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'})

    # --- CALLBACKS ---

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

    # 3. Crear Tag
    @app.callback(
        Output('msg-create-tag', 'children'),
        Output('msg-create-tag', 'style'),
        Input('btn-create-tag', 'n_clicks'),
        State('tag-name', 'value'),
        State('tag-color', 'value'),
        prevent_initial_call=True
    )
    def create_tag(n_clicks, name, color):
        if not name:
            return "❌ El nombre es obligatorio.", {'color': 'red'}
        try:
            dto = TagDTO(name=name, color=color)
            tag_service.create_tag(dto)
            return f"✅ Etiqueta '{name}' creada.", {'color': 'green'}
        except Exception as e:
            return f"❌ Error: {str(e)}", {'color': 'red'}

    # 4. Listar Tags
    @app.callback(
        Output('table-tags', 'children'),
        Input('btn-refresh-tags', 'n_clicks'),
        Input('btn-create-tag', 'n_clicks'),
    )
    def list_tags(n_refresh, n_create):
        tags = tag_service.list_tags()
        if not tags:
            return "No hay etiquetas."
        
        data = [{"Nombre": t.name, "Color": t.color} for t in tags]
        df = pd.DataFrame(data)
        return html.Table([
            html.Thead(html.Tr([html.Th(col) for col in df.columns])),
            html.Tbody([
                html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
                for i in range(len(df))
            ])
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'border': '1px solid #ddd'})

    # 5. Actualizar Dropdowns (Cuentas y Tags)
    @app.callback(
        Output('tx-source', 'options'),
        Output('tx-dest', 'options'),
        Output('tx-tags', 'options'),
        Input('btn-refresh-acc', 'n_clicks'),
        Input('btn-create-acc', 'n_clicks'),
        Input('btn-refresh-tags', 'n_clicks'),
        Input('btn-create-tag', 'n_clicks'),
    )
    def update_dropdowns(n1, n2, n3, n4):
        accounts = account_service.list_accounts()
        tags = tag_service.list_tags()
        
        acc_options = [{'label': f"{acc.name} ({acc.type.name})", 'value': str(acc.id)} for acc in accounts]
        tag_options = [{'label': t.name, 'value': str(t.id)} for t in tags]
        
        return acc_options, acc_options, tag_options

    # 6. Crear Transacción
    @app.callback(
        Output('msg-create-tx', 'children'),
        Output('msg-create-tx', 'style'),
        Input('btn-create-tx', 'n_clicks'),
        State('tx-desc', 'value'),
        State('tx-amount', 'value'),
        State('tx-source', 'value'),
        State('tx-dest', 'value'),
        State('tx-tags', 'value'),
        prevent_initial_call=True
    )
    def create_transaction(n_clicks, desc, amount, source_id, dest_id, tags_ids):
        if not all([desc, amount, source_id, dest_id]):
            return "❌ Todos los campos son obligatorios.", {'color': 'red'}
        
        try:
            dto = TransactionEntryDTO(
                description=desc,
                amount=MoneySchema(amount=Decimal(str(amount)), currency="EUR"),
                source_account_id=source_id,
                destination_account_id=dest_id,
                date=datetime.now(),
                tags_ids=tags_ids if tags_ids else []
            )
            transaction_service.create_transaction(dto)
            return "✅ Transacción registrada correctamente.", {'color': 'green'}
        except Exception as e:
            return f"❌ Error: {str(e)}", {'color': 'red'}

    # 7. Listar Transacciones
    @app.callback(
        Output('table-transactions', 'children'),
        Input('btn-refresh-tx', 'n_clicks'),
        Input('btn-create-tx', 'n_clicks'),
    )
    def list_transactions(n_refresh, n_create):
        txs = transaction_service.list_transactions()
        if not txs:
            return "No hay transacciones."
        
        data = [{
            "Fecha": tx.date.strftime("%Y-%m-%d %H:%M"),
            "Descripción": tx.description,
            "Monto": f"{tx.amount.amount} {tx.amount.currency}",
            "Origen": tx.source_account_name,
            "Destino": tx.destination_account_name,
            "Etiquetas": ", ".join(tx.tags)
        } for tx in txs]
        
        df = pd.DataFrame(data)
        return html.Table([
            html.Thead(html.Tr([html.Th(col) for col in df.columns])),
            html.Tbody([
                html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
                for i in range(len(df))
            ])
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'border': '1px solid #ddd'})

    return app
