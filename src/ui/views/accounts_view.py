from dash import html, dash_table, Input, Output
import dash_bootstrap_components as dbc
from src.domain.models import AccountType

def layout_accounts():
    """
    Genera y devuelve el diseño (layout) de la interfaz de usuario para la sección de 'Cuentas'.
    
    Esta vista permite al usuario visualizar el listado de cuentas (Activos y Pasivos) existentes en el sistema.
    
    Componentes principales:
    - Encabezado y descripción de la sección.
    - Barra de herramientas:
        - Botón "Nueva Cuenta" (Pendiente de implementación lógica).
        - Campo de búsqueda (Filtro visual).
        - Botón "Actualizar" para recargar los datos manualmente.
    - Tabla de datos (dash_table.DataTable):
        - Muestra columnas como Nombre, Tipo, Saldo Inicial, IBAN/Nº y Estado.
        - Configurada con paginación y estilos básicos.
    
    Returns:
        html.Div: Contenedor principal con todos los componentes de la vista.
    """
    return html.Div([
        # Título y subtítulo de la sección
        html.H2("💳 Gestión de Cuentas", style={'color': '#c0392b'}),
        html.P("Gestiona tus cuentas bancarias y tarjetas de crédito.", style={'color': '#7f8c8d'}),
        html.Hr(),
        
        # Barra de herramientas (Botonera)
        dbc.Row([
            dbc.Col(dbc.Button("➕ Nueva Cuenta", color="danger", id='btn-add-account'), width="auto"),
            dbc.Col(dbc.Input(type="text", placeholder="Buscar cuenta..."), width=3),
            dbc.Col(dbc.Button("🔄 Actualizar", id='btn-refresh-accounts', color="secondary"), width="auto"),
        ], className="mb-3"),

        # Tabla de visualización de cuentas
        dash_table.DataTable(
            id='table-accounts',
            columns=[
                {"name": "Nombre", "id": "name", "editable": True},  # Nombre editable directamente en celda
                {"name": "Tipo", "id": "type", "editable": False},  # Tipo (Activo/Pasivo), no editable aquí
                {"name": "Saldo Inicial", "id": "balance", "editable": False},
                {"name": "IBAN/Nº", "id": "number", "editable": True}, # Número de cuenta editable
                {"name": "Estado", "id": "status", "editable": False}, # Estado (Activa/Inactiva)
            ],
            data=[], # Los datos se rellenan vía callback
            page_current=0,
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': 'white', 'fontWeight': 'bold'},
        )
    ])

def register_callbacks(app, account_service):
    """
    Registra los callbacks (lógica interactiva) necesarios para la vista de Cuentas.
    
    Args:
        app (Dash): La instancia principal de la aplicación Dash.
        account_service (AccountService): Servicio de dominio para acceder a las operaciones de Cuentas.
    """
    
    @app.callback(
        Output('table-accounts', 'data'),
        Input('btn-refresh-accounts', 'n_clicks'),
        Input('url', 'pathname')
    )
    def update_accounts_table(n_clicks, pathname):
        """
        Callback para actualizar la tabla de cuentas.
        
        Se dispara cuando:
        1. Se carga la URL '/accounts' (navegación).
        2. El usuario pulsa el botón 'Actualizar'.
        
        Proceso:
        - Verifica si la ruta actual es correcta.
        - Llama al servicio para obtener todas las cuentas.
        - Filtra solo las cuentas relevantes para esta vista (Activos 'ASSET' y Pasivos 'LIABILITY').
          Se excluyen categorías de ingresos/gastos.
        - Formatea los datos para que sean compatibles con el DataTable.
        
        Args:
            n_clicks (int): Número de veces que se ha pulsado el botón refrescar.
            pathname (str): Ruta actual de la aplicación.
            
        Returns:
            list[dict]: Lista de diccionarios con la información a mostrar en la tabla.
        """
        if pathname != '/accounts':
            from dash import no_update
            return no_update
            
        # Obtener todas las cuentas del servicio
        accounts = account_service.list_accounts()
        
        # Filtrar solo cuentas reales (Bancos, Efectivo, Tarjetas) y Deudas.
        # Se omiten las cuentas de sistema usadas para Ingresos y Gastos (Categorías).
        relevant_accounts = [
            a for a in accounts 
            if a.type in [AccountType.ASSET, AccountType.LIABILITY]
        ]
        
        # Transformar DTOs a formato para la tabla
        data = []
        for a in relevant_accounts:
            # Obtener representación legible del tipo de cuenta
            # Si el enum tiene valores complejos tupla, tomamos el primero, o usamos el nombre.
            # Ajustar según implementación de AccountType.
            type_str = a.type.value[0] if isinstance(a.type.value, tuple) else a.type.name
            
            data.append({
                "name": a.name,
                "type": type_str,
                "balance": f"{a.initial_balance.amount} {a.initial_balance.currency}",
                "number": a.account_number or "-",
                "status": "Activa" if a.is_active else "Inactiva"
            })
            
        return data
