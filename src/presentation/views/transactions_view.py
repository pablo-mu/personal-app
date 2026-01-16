from dash import html, dcc, Input, Output, State, ctx
import pandas as pd
from decimal import Decimal
from datetime import datetime
from src.application.dtos import TransactionEntryDTO, MoneySchema
from src.domain.models import AccountType

def get_layout():
    return html.Div([
        # --- ZONA SUPERIOR: ACCIONES RÁPIDAS (FIREFLY III STYLE) ---
        html.Div([
            html.H3("🚀 Operaciones Diarias", style={'marginTop': '0'}),
            html.Div([
                html.Button('📉 Nuevo Gasto', id='btn-mode-expense', n_clicks=0, style={'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'padding': '15px', 'borderRadius': '5px', 'fontWeight': 'bold', 'cursor': 'pointer', 'marginRight': '10px'}),
                html.Button('📈 Nuevo Ingreso', id='btn-mode-income', n_clicks=0, style={'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'padding': '15px', 'borderRadius': '5px', 'fontWeight': 'bold', 'cursor': 'pointer', 'marginRight': '10px'}),
                html.Button('↔️ Transferencia', id='btn-mode-transfer', n_clicks=0, style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'padding': '15px', 'borderRadius': '5px', 'fontWeight': 'bold', 'cursor': 'pointer'}),
            ], style={'marginBottom': '20px'}),
        ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'borderRadius': '8px', 'marginBottom': '20px'}),

        # --- FORMULARIO DINÁMICO ---
        html.Div(id='transaction-form-container', style={'display': 'none'}, children=[
            html.H4(id='form-title', children="Registrar Transacción"),
            
            # Hidden div para guardar el modo actual (expense, income, transfer)
            dcc.Store(id='current-tx-mode', data='EXPENSE'), 
            
            html.Div([
                html.Div([
                    html.Label("Descripción", style={'fontWeight': 'bold'}),
                    dcc.Input(id='tx-desc', type='text', placeholder='¿Qué es?', style={'width': '100%', 'padding': '8px'}),
                ], style={'flex': '2'}),
                
                html.Div([
                    html.Label("Monto (€)", style={'fontWeight': 'bold'}),
                    dcc.Input(id='tx-amount', type='number', value=0, step=0.01, style={'width': '100%', 'padding': '8px'}),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}),
            
            html.Div([
                # Origen y Destino cambian de etiqueta según el modo
                html.Div([
                    html.Label(id='label-source', children="Cuenta Origen (Pagas con...)", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='tx-source', placeholder="Selecciona...", style={'width': '100%'}),
                ], style={'flex': '1'}),
                
                html.Div([
                    html.Label(id='label-dest', children="Cuenta Destino (Categoría...)", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='tx-dest', placeholder="Selecciona...", style={'width': '100%'}),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}),

            html.Div([
                html.Label("Fecha:", style={'fontWeight': 'bold', 'display': 'block'}),
                dcc.DatePickerSingle(
                    id='tx-date',
                    min_date_allowed=datetime(2020, 1, 1),
                    max_date_allowed=datetime(2030, 12, 31),
                    initial_visible_month=datetime.now(),
                    date=datetime.now().date()
                ),
            ], style={'marginBottom': '15px'}),
            
            html.Button('💾 Guardar Transacción', id='btn-submit-tx', n_clicks=0, style={
                'backgroundColor': '#2c3e50', 'color': 'white', 'width': '100%', 'padding': '12px', 'fontWeight': 'bold', 'border': 'none', 'borderRadius': '5px'
            }),
            html.Div(id='msg-tx-result', style={'marginTop': '10px', 'textAlign': 'center'})
        ]),

        html.Hr(),
        html.H3("⏱️ Últimos Movimientos"),
        html.Button('🔄 Actualizar Lista', id='btn-refresh-tx', n_clicks=0),
        html.Div(id='table-transactions', style={'marginTop': '10px'})
    ], style={'padding': '20px', 'maxWidth': '1000px', 'margin': '0 auto'})

def register_callbacks(app, transaction_service, account_service, tag_service):
    
    # 1. Control de Modos (Botones Gasto/Ingreso/Transferencia)
    @app.callback(
        Output('transaction-form-container', 'style'),
        Output('current-tx-mode', 'data'),
        Output('form-title', 'children'),
        Output('form-title', 'style'),
        Output('label-source', 'children'),
        Output('label-dest', 'children'),
        Output('tx-source', 'options'), # Filtrar opciones según modo
        Output('tx-dest', 'options'),   # Filtrar opciones según modo
        Input('btn-mode-expense', 'n_clicks'),
        Input('btn-mode-income', 'n_clicks'),
        Input('btn-mode-transfer', 'n_clicks'),
        State('transaction-form-container', 'style')
    )
    def toggle_mode(n_exp, n_inc, n_trans, current_style):
        ctx_id = ctx.triggered_id
        if not ctx_id:
            # Estado inicial: Formulario oculto
            return {'display': 'none'}, 'EXPENSE', "", {}, "", "", [], []
        
        # Mostrar formulario
        form_style = {'display': 'block', 'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 'border': '1px solid #ddd'}
        
        all_accounts = account_service.list_accounts()
        
        # Filtros Helper
        assets = [{'label': a.name, 'value': str(a.id)} for a in all_accounts if a.type in [AccountType.ASSET, AccountType.LIABILITY]]
        expenses = [{'label': a.name, 'value': str(a.id)} for a in all_accounts if a.type == AccountType.EXPENSE]
        incomes = [{'label': a.name, 'value': str(a.id)} for a in all_accounts if a.type == AccountType.INCOME]
        
        if ctx_id == 'btn-mode-expense':
            return (
                form_style, 'EXPENSE', 
                "📉 Registrar Nuevo Gasto", {'color': '#e74c3c'},
                "Cuenta de Origen (Pagas con...)", "Categoría de Gasto (Compraste...)",
                assets, expenses # Origen: Asset, Destino: Expense
            )
        elif ctx_id == 'btn-mode-income':
            return (
                form_style, 'INCOME',
                "📈 Registrar Nuevo Ingreso", {'color': '#27ae60'},
                "Fuente de Ingreso (Viene de...)", "Cuenta Destino (Depositar en...)",
                incomes, assets # Origen: Income, Destino: Asset
            )
        elif ctx_id == 'btn-mode-transfer':
            return (
                form_style, 'TRANSFER',
                "↔️ Registrar Transferencia", {'color': '#3498db'},
                "Desde Cuenta...", "Hacia Cuenta...",
                assets, assets # Origen: Asset, Destino: Asset
            )
            
        return {'display': 'none'}, 'EXPENSE', "", {}, "", "", [], []

    # 2. Guardar Transacción
    @app.callback(
        Output('msg-tx-result', 'children'),
        Input('btn-submit-tx', 'n_clicks'),
        State('current-tx-mode', 'data'),
        State('tx-desc', 'value'),
        State('tx-amount', 'value'),
        State('tx-source', 'value'),
        State('tx-dest', 'value'),
        State('tx-date', 'date'),
        prevent_initial_call=True
    )
    def submit_transaction(n_clicks, mode, desc, amount, source_id, dest_id, date_str):
        if not all([desc, amount, source_id, dest_id]):
             return html.Span("❌ Faltan datos obligatorios", style={'color': 'red'})
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
            
            dto = TransactionEntryDTO(
                description=desc,
                amount=MoneySchema(amount=Decimal(str(amount)), currency="EUR"),
                source_account_id=source_id,
                destination_account_id=dest_id,
                date=date_obj,
                tags_ids=[]
            )
            transaction_service.create_transaction(dto)
            return html.Span("✅ Transacción guardada con éxito", style={'color': 'green', 'fontWeight': 'bold', 'fontSize': '1.2em'})
        except Exception as e:
            return html.Span(f"❌ Error: {str(e)}", style={'color': 'red'})

    # 3. Listar Actualizaciones (Historial)
    @app.callback(
        Output('table-transactions', 'children'),
        Input('btn-refresh-tx', 'n_clicks'),
        Input('btn-submit-tx', 'n_clicks'), # Actualizar al guardar
    )
    def update_tx_list(n1, n2):
        txs = transaction_service.list_transactions()
        if not txs: return html.Div("No hay movimientos recientes.")
        
        # Ordenar por fecha reciente
        txs.sort(key=lambda x: x.date, reverse=True)
        
        rows = []
        for tx in txs[:10]: # Solo últimos 10
            # Detectar tipo visualmente
            # Esto es una simplificación visual, lo ideal sería ver los tipos de cuentas involucradas
            amount_style = {'fontWeight': 'bold'}
            
            rows.append(html.Tr([
                html.Td(tx.date.strftime("%d/%m/%Y")),
                html.Td(tx.description),
                html.Td(tx.source_account_name),
                html.Td("➡"),
                html.Td(tx.destination_account_name),
                html.Td(f"{tx.amount.amount} €", style=amount_style),
            ]))

        return html.Table([
            html.Thead(html.Tr([html.Th("Fecha"), html.Th("Desc."), html.Th("Origen"), html.Th(""), html.Th("Destino"), html.Th("Monto")])),
            html.Tbody(rows)
        ], style={'width': '100%', 'textAlign': 'left', 'fontSize': '0.9em'})

