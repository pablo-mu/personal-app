from dash import Dash, html, dcc
from src.presentation.views import accounts_view, tags_view, transactions_view, configuration_view
from src.application.container import Services

def init_dashboard(server, services: Services):
    """
    Inicializa la aplicación Dash.
    Recibe el contenedor de servicios para conectar la UI con la lógica de negocio.
    """
    app = Dash(__name__, server=server, url_base_pathname='/', title="Firefly Simple PFM")

    # --- LAYOUT ESTILO FIREFLY ---
    app.layout = html.Div([
        # Header simple simulando barra superior
        html.Div([
            html.H2("Finanzas Personales", style={'color': 'white', 'margin': '0'}),
            html.Div("v1.0", style={'color': '#ecf0f1', 'fontSize': '0.8em'})
        ], style={'backgroundColor': '#2c3e50', 'padding': '15px 30px', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),

        dcc.Tabs([
            # --- TAB 1: DASHBOARD & OPERACIONES DIARIAS ---
            dcc.Tab(label='📊 Dashboard', children=[
                transactions_view.get_layout()
            ], style={'padding': '10px'}, selected_style={'backgroundColor': '#ecf0f1', 'padding': '10px', 'fontWeight': 'bold'}),
            
            # --- TAB 2: ANÁLISIS (GRÁFICOS) ---
            # Por ahora lo dejaremos como placeholder para futura expansión
            dcc.Tab(label='📈 Reportes y Análisis', children=[
                html.Div("Próximamente: Gráficos de tartas y evolución de gastos.", style={'padding': '50px', 'textAlign': 'center', 'color': '#7f8c8d'})
            ]),

            # --- TAB 3: CONFIGURACIÓN (CUENTAS Y ESTRUCTURA) ---
            dcc.Tab(label='⚙️ Cuentas (Activos/Gastos)', children=[
                configuration_view.get_layout()
            ], style={'padding': '10px'}, selected_style={'backgroundColor': '#ecf0f1', 'padding': '10px', 'fontWeight': 'bold'}),

            # --- TAB 4: CONFIG AVANZADA ---
            dcc.Tab(label='🏷️ Etiquetas', children=[
                tags_view.get_layout()
            ])

        ], style={'fontFamily': 'Segoe UI, Arial, sans-serif'})
    ], style={'backgroundColor': '#f4f6f9', 'minHeight': '100vh'})

    # --- REGISTER CALLBACKS ---
    # Nota: accounts_view ya no se usa, reemplazado por configuration_view
    configuration_view.register_callbacks(app, services.account)
    tags_view.register_callbacks(app, services.tag)
    transactions_view.register_callbacks(app, services.transaction, services.account, services.tag)

    return app
