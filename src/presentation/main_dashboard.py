from dash import Dash, html, dcc
from src.presentation.views import accounts_view, tags_view, transactions_view

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
                accounts_view.get_layout()
            ]),
            
            # --- TAB 2: ETIQUETAS (TAGS) ---
            dcc.Tab(label='Etiquetas (Tags)', children=[
                tags_view.get_layout()
            ]),

            # --- TAB 3: TRANSACCIONES ---
            dcc.Tab(label='Transacciones', children=[
                transactions_view.get_layout()
            ]),
        ])
    ], style={'fontFamily': 'Segoe UI, Arial, sans-serif', 'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'})

    # --- REGISTER CALLBACKS ---
    accounts_view.register_callbacks(app, account_service)
    tags_view.register_callbacks(app, tag_service)
    transactions_view.register_callbacks(app, transaction_service, account_service, tag_service)

    return app
