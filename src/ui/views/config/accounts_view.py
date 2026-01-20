from dash import html, dash_table, Input, Output, State, dcc, no_update
import dash_bootstrap_components as dbc
from src.domain.models import AccountType
from src.application.services.account_service import AccountService
from src.application.dtos import AccountCreateDTO, AccountUpdateDTO, AccountFilterDTO
from datetime import datetime

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
        # Stores para gestionar estado
        dcc.Store(id='store-account-filters', data={}),
        dcc.Store(id='store-refresh-accounts', data=0),
        
        # Título y subtítulo de la sección
        html.H2("💳 Gestión de Cuentas", style={'color': '#c0392b'}),
        html.P("Gestiona tus cuentas bancarias y tarjetas de crédito.", style={'color': '#7f8c8d'}),
        html.Hr(),
        
        # Barra de herramientas (Botonera)
        dbc.Row([
            dbc.Col(dbc.Button("➕ Nueva Cuenta", color="danger", id='btn-add-account', n_clicks=0), width="auto"),
            dbc.Col(dbc.Button("✏️ Editar", id='btn-edit-account', color="warning", disabled=True, n_clicks=0), width="auto"),
            dbc.Col(dbc.Button("⏸️ Desactivar", id='btn-deactivate-account', color="secondary", disabled=True, n_clicks=0), width="auto"),
            dbc.Col(dbc.Button("🔍 Filtros", id='btn-filters-account', color="info", n_clicks=0), width="auto"),
            dbc.Col(dbc.Button("🔄 Actualizar", id='btn-refresh-accounts', color="secondary", n_clicks=0), width="auto"),
        ], className="mb-3 g-2"),

        # Tabla de visualización de cuentas
        dash_table.DataTable(
            id='table-accounts',
            columns=[
                {"name": "Nombre", "id": "name", "editable": False},  # Nombre editable directamente en celda
                {"name": "Tipo", "id": "type", "editable": False},  # Tipo (Activo/Pasivo), no editable aquí
                {"name": "Saldo Inicial", "id": "balance", "editable": False},
                {"name": "IBAN/Nº", "id": "number", "editable": False}, # Número de cuenta editable
                {"name": "Estado", "id": "status", "editable": False}, # Estado (Activa/Inactiva)
            ],
            data=[], # Se carga vía callback
            editable=False, 
            row_selectable='multi', # Permite seleccionar varias filas para borrar
            selected_rows=[],
            page_current=0,
            page_size=15,
            page_action='native',
            sort_action='native',
            sort_mode='single',
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'} # Rayado tipo cebra
            ]
        ),
        
        # Modal de Creación/Edición de Cuenta
        dbc.Modal([
            dbc.ModalHeader(html.H4(id='modal-account-title', children="Nueva Cuenta")),
            dbc.ModalBody([
                dcc.Store(id='account-editing-id', data=None),  # ID oculto si estamos editando
                
                # Nombre de la Cuenta
                html.Div([
                    html.Label("Nombre de la Cuenta:", style={'fontWeight': 'bold'}),
                    dbc.Input(id='account-input-name', type='text', placeholder='Mi Cuenta Bancaria', style={'width': '100%', 'padding': '8px'}),
                ], style={'marginBottom': '15px'}),
                
                # Tipo de Cuenta
                html.Div([
                    html.Label("Tipo de Cuenta:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='account-input-type',
                        options=[
                            {'label': f"{t.value} - {t.description}", 'value': t.name}
                            for t in [AccountType.ASSET, AccountType.LIABILITY]
                        ],
                        placeholder="Selecciona...",
                        style={'width': '100%'}
                    ),
                ], style={'marginBottom': '15px'}),
                
                # Saldo Inicial y Moneda
                html.Div([
                    html.Div([
                        html.Label("Saldo Inicial (€):", style={'fontWeight': 'bold'}),
                        dbc.Input(id='account-input-balance', type='number', placeholder='0.00', step=0.01, value=0, style={'width': '100%', 'padding': '8px'}),
                    ], style={'flex': '1'}),
                    
                    html.Div([
                        html.Label("Moneda:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='account-input-currency',
                            options=[
                                {'label': 'EUR (€)', 'value': 'EUR'},
                                {'label': 'USD ($)', 'value': 'USD'},
                                {'label': 'GBP (£)', 'value': 'GBP'},
                            ],
                            value='EUR',
                            style={'width': '100%'}
                        ),
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}),
                
                # Número de Cuenta/IBAN
                html.Div([
                    html.Label("Número de Cuenta / IBAN (Opcional):", style={'fontWeight': 'bold'}),
                    dbc.Input(id='account-input-number', type='text', placeholder='ES9121000418450200051332', style={'width': '100%', 'padding': '8px'}),
                ], style={'marginBottom': '15px'}),
                
                # Estado Activo/Inactivo
                html.Div([
                    dbc.Checkbox(id='account-input-active', label="Cuenta Activa", value=True),
                ], style={'marginBottom': '15px'}),
                
                # Mensaje de error/estado dentro del modal
                html.Div(id='msg-account-modal-result', style={'marginTop': '10px', 'textAlign': 'center', 'color': 'red'})
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancel-modal-account", className="ms-auto", n_clicks=0),
                dbc.Button("💾 Guardar", id="btn-save-modal-account", color="success", n_clicks=0),
            ])
        ], id="modal-account-form", is_open=False, size="lg"),
        
        # Modal de Confirmación de Desactivación
        dbc.Modal([
            dbc.ModalHeader("Confirmar Desactivación"),
            dbc.ModalBody(html.Div(id='msg-deactivate-confirm', children="¿Estás seguro de que deseas desactivar esta cuenta? Las transacciones existentes no se eliminarán.")),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancel-deactivate", className="ms-auto", n_clicks=0),
                dbc.Button("Desactivar", id="btn-confirm-deactivate", color="warning", n_clicks=0),
            ])
        ], id="modal-deactivate-account", is_open=False),
        
        # Modal de Filtros
        dbc.Modal([
            dbc.ModalHeader(html.H4("🔍 Filtrar Cuentas")),
            dbc.ModalBody([
                # Tipo de Cuenta
                html.Div([
                    html.Label("Tipo de Cuenta:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='filter-account-type',
                        options=[
                            {'label': 'Todos', 'value': 'ALL'},
                            {'label': f"{AccountType.ASSET.value}", 'value': AccountType.ASSET.name},
                            {'label': f"{AccountType.LIABILITY.value}", 'value': AccountType.LIABILITY.name},
                        ],
                        value='ALL',
                        clearable=False,
                        style={'width': '100%'}
                    ),
                ], style={'marginBottom': '15px'}),
                
                # Estado
                html.Div([
                    html.Label("Estado:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='filter-account-status',
                        options=[
                            {'label': 'Todas', 'value': 'ALL'},
                            {'label': 'Activas', 'value': 'ACTIVE'},
                            {'label': 'Inactivas', 'value': 'INACTIVE'},
                        ],
                        value='ALL',
                        clearable=False,
                        style={'width': '100%'}
                    ),
                ], style={'marginBottom': '15px'}),
                
                # Búsqueda por nombre
                html.Div([
                    html.Label("Buscar por Nombre:", style={'fontWeight': 'bold'}),
                    dbc.Input(id='filter-account-name', type='text', placeholder='Introduce parte del nombre...', style={'width': '100%', 'padding': '8px'}),
                ], style={'marginBottom': '15px'}),
            ]),
            dbc.ModalFooter([
                dbc.Button("Limpiar Filtros", id="btn-clear-filters-account", color="secondary", n_clicks=0),
                dbc.Button("Cancelar", id="btn-cancel-filters-account", className="ms-auto", n_clicks=0),
                dbc.Button("Aplicar", id="btn-apply-filters-account", color="primary", n_clicks=0),
            ])
        ], id="modal-account-filters", is_open=False, size="lg"),
        
        # Div auxiliar (invisible) para outputs de callbacks
        html.Div(id='msg-account-result', style={'display': 'none'})
    ])

def register_callbacks(app, account_service: AccountService):
    """
    Registra los callbacks (lógica interactiva) necesarios para la vista de Cuentas.
    
    Args:
        app (Dash): La instancia principal de la aplicación Dash.
        account_service (AccountService): Servicio de dominio para acceder a las operaciones de Cuentas.
    """
    
    # 1. Actualizar tabla de cuentas
    @app.callback(
        Output('table-accounts', 'data'), # Datos de la tabla
        Input('store-refresh-accounts', 'data'), # Trigger para refrescar
        Input('store-account-filters', 'data'), # Filtros aplicados
        Input('url', 'pathname'), # Para detectar navegación
        Input('btn-refresh-accounts', 'n_clicks'), # Botón de refresco manual
        Input('btn-save-modal-account', 'n_clicks'), # Guardar cuenta (nuevo o editado)
        Input('btn-confirm-deactivate', 'n_clicks'), # Confirmar desactivación
    )
    def update_table(_, account_filters, current_pathname, *args):
        """
        Actualiza los datos de la tabla de cuentas según los filtros y acciones realizadas.
        """
        if current_pathname != '/accounts':
            return no_update
        
        try:
            # Construir DTO de filtros a partir del store
            filter_dto = AccountFilterDTO()
            
            if account_filters:
                # Filtrar por tipo
                if account_filters.get('type') and account_filters['type'] != 'ALL':
                    filter_dto.type = AccountType[account_filters['type']]
                
                # Filtrar por estado (is_active)
                if account_filters.get('status') and account_filters['status'] != 'ALL':
                    filter_dto.is_active = (account_filters['status'] == 'ACTIVE')
                
                # Filtrar por nombre (búsqueda)
                if account_filters.get('name'):
                    filter_dto.name_contains = account_filters['name']
            
            # Obtener cuentas desde el servicio aplicando filtros
            accounts_dto = account_service.list_accounts(filter_dto)
            
            # Transformar DTOs a formato de tabla
            data = []
            for acc in accounts_dto:
                type_str = acc.type.value  # El valor es una tupla (nombre, descripción), tomamos solo el nombre
                
                data.append({
                    "id": str(acc.id),
                    "name": acc.name,
                    "type": type_str,
                    "balance": f"{acc.initial_balance.amount} {acc.initial_balance.currency}",
                    "number": acc.account_number or "-",
                    "status": "Activa" if acc.is_active else "Inactiva",
                    # Datos ocultos (raw) para facilitar edición
                    "raw_id": str(acc.id),
                    "raw_type": acc.type.name,
                    "raw_amount": float(acc.initial_balance.amount),
                    "raw_currency": acc.initial_balance.currency,
                    "raw_active": acc.is_active
                })
            
            return data
        
        except Exception as e:
            print(f"Error al actualizar tabla de cuentas: {str(e)}")
            return no_update

