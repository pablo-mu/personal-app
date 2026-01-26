from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from src.ui import views
from src.application.container import Services

# --- STYLES ---
TOPBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "right": 0,
    "height": "60px",
    "backgroundColor": "#ffffff",
    "borderBottom": "1px solid #dee2e6",
    "padding": "0 1rem",
    "display": "flex",
    "alignItems": "center",
    "zIndex": 1000,
}

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "60px",
    "left": 0,
    "bottom": 0,
    "width": "18rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
    "transition": "all 0.3s",
    "overflowY": "auto",
}

SIDEBAR_COLLAPSED = {
    "position": "fixed",
    "top": "60px",
    "left": "-18rem",
    "bottom": 0,
    "width": "18rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
    "transition": "all 0.3s",
    "overflowY": "auto",
}

CONTENT_STYLE = {
    "marginLeft": "18rem",
    "marginTop": "60px",
    "padding": "2rem",
    "backgroundColor": "#f4f6f9",
    "minHeight": "calc(100vh - 60px)",
    "transition": "all 0.3s",
}

CONTENT_STYLE_EXPANDED = {
    "marginLeft": "0",
    "marginTop": "60px",
    "padding": "2rem",
    "backgroundColor": "#f4f6f9",
    "minHeight": "calc(100vh - 60px)",
    "transition": "all 0.3s",
}

def init_dashboard(server, services: Services):
    """
    Inicializa la aplicación Dash con Sidebar Layout.
    """
    app = Dash(
        __name__, 
        server=server, 
        url_base_pathname='/', 
        title="Mi Finanza", 
        suppress_callback_exceptions=True,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"
        ]
    )

    # --- COMPONENTS ---
    # Barra superior con botón de toggle
    topbar = html.Div(
        [
            dbc.Button(
                html.I(className="bi bi-list", style={'fontSize': '1.5rem'}),
                id="sidebar-toggle",
                color="light",
                size="sm",
                style={'border': 'none'}
            ),
            html.Span("💰 Mi Finanza", style={
                'marginLeft': '1rem',
                'fontSize': '1.5rem',
                'fontWeight': '600',
                'color': '#2c3e50'
            })
        ],
        style=TOPBAR_STYLE
    )
    
    sidebar = html.Div(
        [
            dbc.Nav(
                [
                    dbc.NavLink("📝 Seguimiento Diario", href="/", active="exact"),
                    html.Hr(),
                    html.Div("Dashboard", className="text-muted small fw-bold mb-2"),
                    dbc.NavLink("📊 Resumen", href="/summary", active="exact"),
                    html.Hr(),
                    html.Div("PLANIFICACIÓN", className="text-muted small fw-bold mb-2"),
                    dbc.NavLink("🎯 Objetivos", href="/budgets", active="exact"),
                    dbc.NavLink("📅 Recurrencia", href="/recurring", active="exact"),
                    html.Hr(),
                    html.Div("CONFIGURACIÓN", className="text-muted small fw-bold mb-2"),
                    dbc.NavLink("📋 Movimientos", href="/config/transactions", active="exact"),
                    dbc.NavLink("💳 Cuentas", href="/accounts", active="exact"),
                    dbc.NavLink("🛒 Categorías", href="/categories", active="exact"),
                    html.Hr(),
                    html.Div("INFORMACIÓN", className="text-muted small fw-bold mb-2"),
                    dbc.NavLink("ℹ️ Acerca de", href="/about", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        id="sidebar",
        style=SIDEBAR_STYLE,
    )

    content = html.Div(id="page-content", style=CONTENT_STYLE)

    app.layout = html.Div([
        dcc.Location(id="url"),
        dcc.Store(id='sidebar-collapsed', data=False),
        topbar,
        sidebar,
        content
    ])

    # --- REGISTER CALLBACKS ---
    views.register_tracking_callbacks(app, services.account, services.transaction, services.tag)
    views.register_transactions_callbacks(app, services.transaction, services.account, services.tag)
    views.register_accounts_callbacks(app, services.account)
    views.register_categories_callbacks(app, services.account)
    views.register_recurring_callbacks(app, services)

    # --- SIDEBAR TOGGLE CALLBACK ---
    @app.callback(
        [Output("sidebar", "style"),
         Output("page-content", "style"),
         Output("sidebar-collapsed", "data")],
        Input("sidebar-toggle", "n_clicks"),
        State("sidebar-collapsed", "data"),
        prevent_initial_call=True
    )
    def toggle_sidebar(n_clicks, is_collapsed):
        if n_clicks:
            if is_collapsed:
                return SIDEBAR_STYLE, CONTENT_STYLE, False
            else:
                return SIDEBAR_COLLAPSED, CONTENT_STYLE_EXPANDED, True
        return SIDEBAR_STYLE, CONTENT_STYLE, False

    # --- ROUTING CALLBACK ---
    @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def render_page_content(pathname):
        if pathname == "/" or pathname == "/daily":
            return views.layout_daily()
        elif pathname == "/config/transactions":
            return views.layout_transactions_config()
        elif pathname == "/summary":
            return views.layout_summary()
        elif pathname == "/budgets":
            return views.layout_budgets()
        elif pathname == "/recurring":
            return views.layout_recurring()
        elif pathname == "/accounts":
            return views.layout_accounts()
        elif pathname == "/categories":
            return views.layout_categories()
        elif pathname == "/about":
            return views.layout_about()
        
        return html.Div(
            dbc.Container(
                [
                    html.H1("404: Not found", className="text-danger"),
                    html.P(f"The pathname {pathname} was hot found..."),
                ],
                className="py-3",
            )
        )

    return app
