from dash import html, dcc, Input, Output, State
import pandas as pd
from decimal import Decimal
from datetime import datetime
from src.application.dtos import TransactionEntryDTO, MoneySchema

def get_layout():
    return html.Div([
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

def register_callbacks(app, transaction_service, account_service, tag_service):
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
