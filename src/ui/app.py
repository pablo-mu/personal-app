from dash import Dash, html, dcc
from src.ui.views import accounts_view
from src.application.container import Services


def init_dashboard(server, services: Services):
    """
    Inicializa la aplicación Dash.
    Recibe el contenedor de servicios para conectar la UI con la lógica de negocio.
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
                # Aquí se agregaría la vista de etiquetas
            ]),

            # --- TAB 3: TRANSACCIONES ---
            dcc.Tab(label='Transacciones', children=[
                # Aquí se agregaría la vista de transacciones
            ]),
        ])
    ], style={'fontFamily': 'Segoe UI, Arial, sans-serif', 'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'})

    # --- REGISTER CALLBACKS ---
    accounts_view.register_callbacks(app, services.account)
    # Aquí se registrarían los callbacks para tags_view y transactions_view
    # tags_view.register_callbacks(app, tag_service)
    # transactions_view.register_callbacks(app, transaction_service, account_service, tag_service)
    return app