from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from src.ui.views import tracking_view, budgets_view, recurring_view, accounts_view, categories_view, tags_view, transactions_config_view
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
        title="Firefly Simple PFM", 
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
                    html.Div("PLANIFICACIÓN", className="text-muted small fw-bold mb-2"),
                    dbc.NavLink("🎯 Objetivos", href="/budgets", active="exact"),
                    dbc.NavLink("📅 Recurrencia", href="/recurring", active="exact"),
                    html.Hr(),
                    html.Div("CONFIGURACIÓN", className="text-muted small fw-bold mb-2"),
                    dbc.NavLink("📋 Movimientos", href="/config/transactions", active="exact"),
                    dbc.NavLink("💳 Cuentas", href="/accounts", active="exact"),
                    dbc.NavLink("🛒 Categorías", href="/categories", active="exact"),
                    dbc.NavLink("🏷️ Etiquetas", href="/tags", active="exact"),
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
    tracking_view.register_callbacks(app, services.account, services.transaction, services.tag)
    transactions_config_view.register_callbacks(app, services.transaction, services.account, services.tag)
    accounts_view.register_callbacks(app, services.account)
    categories_view.register_callbacks(app, services.account)
    tags_view.register_callbacks(app, services.tag)

    # --- ROUTING CALLBACK ---
    @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def render_page_content(pathname):
        if pathname == "/" or pathname == "/daily":
            return tracking_view.layout_daily()
        elif pathname == "/config/transactions":
            return transactions_config_view.layout_transactions_config()
        elif pathname == "/budgets":
            return budgets_view.layout_budgets()
        elif pathname == "/recurring":
            return recurring_view.layout_recurring()
        elif pathname == "/accounts":
            return accounts_view.layout_accounts()
        elif pathname == "/categories":
            return categories_view.layout_categories()
        elif pathname == "/tags":
            return tags_view.layout_tags()
        
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
