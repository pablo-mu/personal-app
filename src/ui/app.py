from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from src.ui import views
from src.application.container import Services

# --- STYLES ---
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "18rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
}

CONTENT_STYLE = {
    "marginLeft": "18rem",
    "padding": "2rem",
    "backgroundColor": "#f4f6f9",
    "minHeight": "100vh"
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
        external_stylesheets=[dbc.themes.BOOTSTRAP] # Use Bootstrap Theme
    )

    # --- COMPONENTS ---
    sidebar = html.Div(
        [
            html.H3("💰 Mi Finanza", className="display-6"),
            html.Hr(),
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
                    dbc.NavLink("🏷️ Etiquetas", href="/tags", active="exact"),
                    html.Hr(),
                    html.Div("INFORMACIÓN", className="text-muted small fw-bold mb-2"),
                    dbc.NavLink("ℹ️ Acerca de", href="/about", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        style=SIDEBAR_STYLE,
    )

    content = html.Div(id="page-content", style=CONTENT_STYLE)

    app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

    # --- REGISTER CALLBACKS ---
    views.register_tracking_callbacks(app, services.account, services.transaction, services.tag)
    views.register_transactions_callbacks(app, services.transaction, services.account, services.tag)
    views.register_accounts_callbacks(app, services.account)
    views.register_categories_callbacks(app, services.account)
    views.register_tags_callbacks(app, services.tag)

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
        elif pathname == "/tags":
            return views.layout_tags()
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
