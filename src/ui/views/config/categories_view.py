from dash import html, dash_table, Input, Output
import dash_bootstrap_components as dbc
from src.domain.models import AccountType

def layout_categories():
    """
    Genera y devuelve el diseño (layout) de la interfaz de usuario para la sección de 'Categorías'.
    
    Esta vista permite al usuario gestionar las cuentas de tipo Gasto e Ingreso, que funcionalmente actúan como categorías.
    
    Componentes principales:
    - Encabezado y descripción de la sección.
    - Barra de herramientas:
        - Botón "Nueva Categoría" (Pendiente de lógica).
        - Campo de búsqueda.
        - Botón "Actualizar".
    - Tabla de datos (dash_table.DataTable):
        - Muestra nombre, tipo (Ingreso/Gasto) y estado.
    
    Returns:
        html.Div: Contenedor principal con todos los componentes de la vista.
    """
    return html.Div([
        # Título y subtítulo
        html.H2("🛒 Gestión de Categorías", style={'color': '#27ae60'}),
        html.P("Agrupa tus transacciones para un mejor análisis.", style={'color': '#7f8c8d'}),
        html.Hr(),

        # Botonera
        dbc.Row([
            dbc.Col([
                dbc.Button(html.I(className="bi bi-plus-circle"), color="secondary", outline=True, id='btn-add-category', className="btn-sm"),
                dbc.Tooltip("Nueva Categoría", target="btn-add-category", placement="top"),
            ], width="auto"),
            dbc.Col(dbc.Input(type="text", placeholder="Buscar categoría...", size="sm"), width=3),
            dbc.Col([
                dbc.Button(html.I(className="bi bi-arrow-clockwise"), id='btn-refresh-categories', color="secondary", outline=True, className="btn-sm"),
                dbc.Tooltip("Actualizar", target="btn-refresh-categories", placement="top"),
            ], width="auto"),
        ], className="mb-3 g-2"),

        # Tabla de categorías
        dash_table.DataTable(
            id='table-categories',
            columns=[
                {"name": "Nombre", "id": "name", "editable": True},  # Editable para cambiar nombre rápidamente
                {"name": "Tipo", "id": "type", "editable": False},  # Ingreso/Gasto
                {"name": "Estado", "id": "status", "editable": False},
            ],
            data=[], # Cargado dinámicamente
            page_current=0,
            page_size=10,
            style_header={'backgroundColor': 'white', 'fontWeight': 'bold'},
        )
    ])

def register_callbacks(app, account_service):
    """
    Registra los callbacks necesarios para la vista de Categorías.
    
    Args:
        app (Dash): Instancia de la app Dash.
        account_service (AccountService): Servicio para acceder a las Cuentas (Categorías).
    """

    @app.callback(
        Output('table-categories', 'data'),
        Input('btn-refresh-categories', 'n_clicks'),
        Input('url', 'pathname')
    )
    def update_categories_table(n_clicks, pathname):
        """
        Callback para actualizar la tabla de categorías.
        
        Se dispara al navegar a '/categories' o al pulsar actualizar.
        Filtra las cuentas para mostrar solo aquellas de tipo INCOME o EXPENSE.
        
        Args:
            n_clicks (int): Clics en el botón de refresco.
            pathname (str): Ruta actual.
            
        Returns:
            list[dict]: Datos formateados para la tabla.
        """
        if pathname != '/categories':
            from dash import no_update
            return no_update

        # Obtener todas las cuentas y filtrar
        accounts = account_service.list_accounts()
        # En este dominio, las "Categorías" son Cuentas de tipo INCOME o EXPENSE
        relevant_accounts = [
            a for a in accounts 
            if a.type in [AccountType.INCOME, AccountType.EXPENSE]
        ]
        
        data = []
        for a in relevant_accounts:
            # Obtener string del tipo
            type_str = a.type.value[0] if isinstance(a.type.value, tuple) else a.type.name
            
            data.append({
                "name": a.name,
                "type": type_str,
                "status": "Activa" if a.is_active else "Inactiva"
            })
            
        return data
