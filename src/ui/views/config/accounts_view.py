from dash import ctx, html, dash_table, Input, Output, State, dcc, no_update
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
            dbc.Col([
                dbc.Button(html.I(className="bi bi-plus-circle"), color="secondary", outline=True, id='btn-add-account', n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Nueva Cuenta", target="btn-add-account", placement="top"),
            ], width="auto"),
            dbc.Col([
                html.Span([
                    dbc.Button(html.I(className="bi bi-pencil"), id='btn-edit-account', color="secondary", outline=True, disabled=True, n_clicks=0, className="btn-sm"),
                ], id="wrapper-edit-account"),
                dbc.Tooltip("Editar (selecciona 1 cuenta)", target="wrapper-edit-account", placement="top"),
            ], width="auto"),
            dbc.Col([
                html.Span([
                    dbc.Button(html.I(className="bi bi-pause-circle"), id='btn-deactivate-account', color="secondary", outline=True, disabled=True, n_clicks=0, className="btn-sm"),
                ], id="wrapper-deactivate-account"),
                dbc.Tooltip("Desactivar (selecciona cuentas activas)", target="wrapper-deactivate-account", placement="top"),
            ], width="auto"),
            dbc.Col([
                html.Span([
                    dbc.Button(html.I(className="bi bi-play-circle"), id='btn-activate-account', color="secondary", outline=True, disabled=True, n_clicks=0, className="btn-sm"),
                ], id="wrapper-activate-account"),
                dbc.Tooltip("Activar (selecciona cuentas inactivas)", target="wrapper-activate-account", placement="top"),
            ], width="auto"),
            dbc.Col([
                dbc.Button(html.I(className="bi bi-funnel"), id='btn-filters-account', color="secondary", outline=True, n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Filtros", target="btn-filters-account", placement="top"),
            ], width="auto"),
            dbc.Col([
                dbc.Button(html.I(className="bi bi-arrow-clockwise"), id='btn-refresh-accounts', color="secondary", outline=True, n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Actualizar", target="btn-refresh-accounts", placement="top"),
            ], width="auto"),
        ], className="mb-3 g-3"),

        # Tabla de visualización de cuentas
        dash_table.DataTable(
            id='table-accounts',
            columns=[
                {"name": "Nombre", "id": "name", "editable": False},
                {"name": "Tipo", "id": "type", "editable": False},
                {"name": "Saldo Actual", "id": "balance", "editable": False},
                {"name": "IBAN/Nº", "id": "number", "editable": False},
                {"name": "Estado", "id": "status", "editable": False},
            ],
            data=[],
            editable=False,
            row_selectable='multi',
            selected_rows=[],
            page_current=0,
            page_size=20,
            page_action='native',
            sort_action='native',
            sort_mode='single',
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px 12px',
                'fontSize': '0.9rem',
                'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial'
            },
            style_header={
                'backgroundColor': 'rgb(250, 250, 250)',
                'fontWeight': '600',
                'fontSize': '0.85rem',
                'color': '#2c3e50',
                'borderBottom': '2px solid #dee2e6',
                'padding': '10px 12px'
            },
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(252, 252, 252)'},
                {'if': {'state': 'selected'}, 'backgroundColor': 'rgba(0, 123, 255, 0.1)', 'border': '1px solid #007bff'}
            ]
        ),
        
        # Modal de Creación/Edición de Cuenta
        dbc.Modal([
            dbc.ModalHeader(html.H4(id='modal-account-title', children="Nueva Cuenta")),
            dbc.ModalBody([
                dcc.Store(id='account-editing-id', data=None),  # ID oculto si estamos editando
                
                # Fila 1: Nombre y Tipo
                html.Div([
                    html.Div([
                        html.Label("Nombre:", style={'fontWeight': 'bold'}),
                        dbc.Input(id='account-input-name', type='text', placeholder='Mi Cuenta Bancaria', style={'width': '100%'}),
                    ], style={'flex': '2'}),
                    
                    html.Div([
                        html.Label("Tipo:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='account-input-type',
                            options=[
                                {'label': f"💰 {AccountType.ASSET.value}", 'value': AccountType.ASSET.name},
                                {'label': f"💳 {AccountType.LIABILITY.value}", 'value': AccountType.LIABILITY.name}
                            ],
                            placeholder="Selecciona...",
                            style={'width': '100%'}
                        ),
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '12px'}),
                
                # Fila 2: Saldo Actual (solo lectura - calculado)
                html.Div([
                    html.Label("💰 Saldo Actual:", style={'fontWeight': 'bold', 'color': '#28a745'}),
                    dbc.Input(id='account-input-current-balance', type='text', disabled=True, placeholder='0.00 EUR', style={'backgroundColor': '#e9f7ef', 'fontWeight': 'bold'}),
                    html.Small("Calculado automáticamente con las transacciones", style={'color': '#6c757d', 'fontStyle': 'italic', 'fontSize': '0.8em'}),
                ], style={'marginBottom': '12px'}),
                
                # Fila 3: Saldo Inicial, Moneda y Número de Cuenta
                html.Div([
                    html.Div([
                        html.Label("Saldo Inicial:", style={'fontWeight': 'bold'}),
                        dbc.Input(id='account-input-balance', type='number', placeholder='0.00', step=0.01, value=0, style={'width': '100%'}),
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
                            clearable=False,
                            style={'width': '100%'}
                        ),
                    ], style={'flex': '0.6'}),
                    
                    html.Div([
                        html.Label("IBAN / Nº Cuenta:", style={'fontWeight': 'bold'}),
                        dbc.Input(id='account-input-number', type='text', placeholder='ES91...', style={'width': '100%'}),
                    ], style={'flex': '1.5'}),
                ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '12px'}),
                
                # Fila 4: Estado
                html.Div([
                    dbc.Checkbox(id='account-input-active', label="✓ Cuenta Activa", value=True, className="form-check-input-lg"),
                ], style={'marginBottom': '10px'}),
                
                # Mensaje de error/estado dentro del modal
                html.Div(id='msg-account-modal-result', style={'marginTop': '10px', 'textAlign': 'center', 'fontWeight': 'bold'})
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
        
        # Modal de Confirmación de Activación
        dbc.Modal([
            dbc.ModalHeader("Confirmar Activación"),
            dbc.ModalBody(html.Div(id='msg-activate-confirm', children="¿Estás seguro de que deseas activar esta cuenta?")),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancel-activate", className="ms-auto", n_clicks=0),
                dbc.Button("Activar", id="btn-confirm-activate", color="success", n_clicks=0),
            ])
        ], id="modal-activate-account", is_open=False),
        
        # Modal de Filtros
        dbc.Modal([
            dbc.ModalHeader(html.H4("🔍 Filtrar Cuentas")),
            dbc.ModalBody([
                # Fila 1: Tipo de Cuenta y Estado
                html.Div([
                    html.Div([
                        html.Label("Tipo:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='filter-account-type',
                            options=[
                                {'label': 'Todos', 'value': 'ALL'},
                                {'label': f"💰 {AccountType.ASSET.value}", 'value': AccountType.ASSET.name},
                                {'label': f"💳 {AccountType.LIABILITY.value}", 'value': AccountType.LIABILITY.name},
                            ],
                            value='ALL',
                            clearable=False,
                            style={'width': '100%'}
                        ),
                    ], style={'flex': '1'}),
                    
                    html.Div([
                        html.Label("Estado:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='filter-account-status',
                            options=[
                                {'label': 'Todas', 'value': 'ALL'},
                                {'label': '✓ Activas', 'value': 'ACTIVE'},
                                {'label': '✗ Inactivas', 'value': 'INACTIVE'},
                            ],
                            value='ALL',
                            clearable=False,
                            style={'width': '100%'}
                        ),
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '12px'}),
                
                # Fila 2: Búsqueda por nombre
                html.Div([
                    html.Label("Buscar por Nombre:", style={'fontWeight': 'bold'}),
                    dbc.Input(id='filter-account-name', type='text', placeholder='Escribe parte del nombre...', style={'width': '100%'}),
                ], style={'marginBottom': '10px'}),
            ]),
            dbc.ModalFooter([
                dbc.Button("Limpiar", id="btn-clear-filters-account", color="secondary", n_clicks=0),
                dbc.Button("Cancelar", id="btn-cancel-filters-account", n_clicks=0),
                dbc.Button("✓ Aplicar", id="btn-apply-filters-account", color="primary", n_clicks=0),
            ])
        ], id="modal-account-filters", is_open=False, size="md"),
        
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
        Input('btn-confirm-activate', 'n_clicks'), # Confirmar activación
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
            
            # Filtrar SOLO cuentas de tipo ASSET y LIABILITY (las demás se tratan como categorías)
            accounts_dto = [acc for acc in accounts_dto if acc.type in [AccountType.ASSET, AccountType.LIABILITY]]
            
            # Transformar DTOs a formato de tabla
            data = []
            for acc in accounts_dto:
                type_str = acc.type.value  # El valor es una tupla (nombre, descripción), tomamos solo el nombre
                
                data.append({
                    "id": str(acc.id),
                    "name": acc.name,
                    "type": type_str,
                    "balance": f"{acc.current_balance.amount} {acc.current_balance.currency}",
                    "number": acc.account_number or "-",
                    "status": "Activa" if acc.is_active else "Inactiva",
                    # Datos ocultos (raw) para facilitar edición
                    "raw_id": str(acc.id),
                    "raw_type": acc.type.name,
                    "raw_initial_amount": float(acc.initial_balance.amount),
                    "raw_current_amount": float(acc.current_balance.amount),
                    "raw_currency": acc.initial_balance.currency,
                    "raw_active": acc.is_active
                })
            
            return data
        
        except Exception as e:
            print(f"Error al actualizar tabla de cuentas: {str(e)}")
            return no_update


    # 2. Gestión de botones toolbar

    #Habilitar/Deshabilitar botones según selección de filas
    @app.callback(
        Output('btn-edit-account', 'disabled'),
        Output('btn-deactivate-account', 'disabled'),
        Output('btn-activate-account', 'disabled'),
        Input('table-accounts', 'selected_rows'),
        State('table-accounts', 'data')
    )
    def toggle_buttons(selected_rows, table_data):
        """
        Habilita o deshabilita los botones de Editar, Desactivar y Activar según la selección en la tabla.
        - Editar: Solo si hay exactamente 1 fila seleccionada
        - Desactivar: Solo si hay selección Y todas las cuentas seleccionadas están activas
        - Activar: Solo si hay selección Y todas las cuentas seleccionadas están inactivas
        """
        if not selected_rows or len(selected_rows) == 0:
            return True, True, True  # Todos deshabilitados
        
        # Verificar el estado de las cuentas seleccionadas
        selected_accounts = [table_data[idx] for idx in selected_rows]
        all_active = all(acc['raw_active'] for acc in selected_accounts)
        all_inactive = all(not acc['raw_active'] for acc in selected_accounts)
        
        # Editar: solo habilitado si hay exactamente 1 seleccionada
        edit_disabled = len(selected_rows) != 1
        
        # Desactivar: habilitado si todas están activas
        deactivate_disabled = not all_active
        
        # Activar: habilitado si todas están inactivas
        activate_disabled = not all_inactive
        
        return edit_disabled, deactivate_disabled, activate_disabled
    

    @app.callback(
        Output('modal-account-form', 'is_open'),
        Output('modal-account-title', 'children'),

        Output('account-editing-id', 'data'),
        Output('account-input-name', 'value'),
        Output('account-input-type', 'value'),
        Output('account-input-current-balance', 'value'),
        Output('account-input-balance', 'value'),
        Output('account-input-currency', 'value'),
        Output('account-input-number', 'value'),
        Output('account-input-active', 'value'),

        Input('btn-add-account', 'n_clicks'),
        Input('btn-edit-account', 'n_clicks'),
        Input('btn-cancel-modal-account', 'n_clicks'),
        Input('store-refresh-accounts', 'data'), # Para cerrar modal tras guardar

        State('table-accounts', 'data'),
        State('table-accounts', 'selected_rows'),
        State('modal-account-form', 'is_open')
    )
    def toggle_edit_modal(_, __, ___, _____, table_data, selected_rows, is_open):
        """
        Abre o cierra el modal de creación/edición de cuenta.
        Si se abre para edición, carga los datos de la cuenta seleccionada.
        """
        trigger_id = ctx.triggered_id

        if not trigger_id:
            return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        # Cerrar el modal
        if trigger_id in ['btn-cancel-modal-account', 'store-refresh-accounts']:
            return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        # Abrir modal para "crear nueva cuenta"
        if trigger_id == 'btn-add-account':
            # Nueva cuenta - saldo actual será igual al inicial
            return True, "Nueva Cuenta", None, "", None, "0.00 EUR", 0.00, "EUR", "", True
        
        # Abrir modal para "editar cuenta"
        if trigger_id == 'btn-edit-account':
            if not selected_rows or len(selected_rows) != 1:
                return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
            
            row_idx = selected_rows[0]
            row_data = table_data[row_idx]
            
            # Extraer valores exactos de la cuenta seleccionada
            account_id = row_data['raw_id']
            name = row_data['name']
            account_type = row_data['raw_type']  # Debería ser "ASSET" o "LIABILITY"
            initial_balance = row_data['raw_initial_amount']
            current_balance = row_data['raw_current_amount']
            currency = row_data['raw_currency']
            # Convertir "-" a string vacío para el input
            account_number = "" if row_data['number'] == "-" else row_data['number']
            is_active = row_data['raw_active']
            
            # Formatear saldo actual para mostrar (solo lectura)
            current_balance_display = f"{current_balance} {currency}"
            
            # Cargar datos TAL CUAL están (sin valores por defecto)
            return True, "Editar Cuenta", account_id, name, account_type, current_balance_display, initial_balance, currency, account_number, is_active
        
        return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    @app.callback(
        Output('msg-account-modal-result', 'children'),
        Output('store-refresh-accounts', 'data'),
        Input('btn-save-modal-account', 'n_clicks'),
        State('account-editing-id', 'data'),
        State('account-input-name', 'value'),
        State('account-input-type', 'value'),
        State('account-input-balance', 'value'),
        State('account-input-currency', 'value'),
        State('account-input-number', 'value'),
        State('account-input-active', 'value'),
        prevent_initial_call=True
    )
    def save_account(n_clicks, account_id, name, type_str, balance, currency, account_number, is_active):
        """
        Guarda una cuenta nueva o actualiza una existente.
        """
        if not n_clicks:
            return no_update, no_update
        
        # Validaciones básicas
        if not name or not name.strip():
            return "❌ El nombre de la cuenta es obligatorio.", no_update
        
        if not type_str:
            return "❌ Debes seleccionar un tipo de cuenta.", no_update
        
        if balance is None:
            return "❌ El saldo inicial es obligatorio.", no_update
        
        try:
            # Convertir tipo de string a enum
            account_type = AccountType[type_str]
            
            # Si estamos creando una cuenta nueva
            if not account_id:
                from src.domain.value_objects import Money
                
                # Crear DTO para nueva cuenta
                create_dto = AccountCreateDTO(
                    name=name.strip(),
                    type=account_type,
                    initial_balance=Money(amount=float(balance), currency=currency),
                    account_number=account_number.strip() if account_number else None,
                    is_active=is_active
                )
                
                # Crear cuenta
                account_service.create_account(create_dto)
                
                # Incrementar store para disparar refresh
                return "✅ Cuenta creada exitosamente.", n_clicks
            
            # Si estamos editando una cuenta existente
            else:
                from uuid import UUID
                from src.domain.value_objects import Money
                
                # Crear DTO para actualizar
                update_dto = AccountUpdateDTO(
                    name=name.strip(),
                    type=account_type,
                    initial_balance=Money(amount=float(balance), currency=currency),
                    account_number=account_number.strip() if account_number else None,
                    is_active=is_active
                )
                
                # Actualizar cuenta
                account_service.update_account(UUID(account_id), update_dto)
                
                # Incrementar store para disparar refresh
                return "✅ Cuenta actualizada exitosamente.", n_clicks
        
        except ValueError as e:
            # Error de validación de dominio (ej: balance negativo en ASSET)
            return f"❌ Error de validación: {str(e)}", no_update
        
        except Exception as e:
            # Cualquier otro error
            print(f"Error al guardar cuenta: {str(e)}")
            return f"❌ Error al guardar la cuenta: {str(e)}", no_update
    
    # Callback para abrir/cerrar modal de desactivación
    @app.callback(
        Output('modal-deactivate-account', 'is_open'),
        Input('btn-deactivate-account', 'n_clicks'),
        Input('btn-cancel-deactivate', 'n_clicks'),
        Input('btn-confirm-deactivate', 'n_clicks'),
        State('modal-deactivate-account', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_deactivate_modal(open_click, cancel_click, confirm_click, is_open):
        """Abre o cierra el modal de confirmación de desactivación."""
        return not is_open
    
    # Callback para confirmar desactivación
    @app.callback(
        Output('store-refresh-accounts', 'data', allow_duplicate=True),
        Input('btn-confirm-deactivate', 'n_clicks'),
        State('table-accounts', 'selected_rows'),
        State('table-accounts', 'data'),
        State('store-refresh-accounts', 'data'),
        prevent_initial_call=True
    )
    def confirm_deactivate(n_clicks, selected_rows, table_data, current_refresh):
        """Desactiva las cuentas seleccionadas."""
        if not n_clicks or not selected_rows:
            return no_update
        
        try:
            from uuid import UUID
            from src.domain.value_objects import Money
            
            for idx in selected_rows:
                account_data = table_data[idx]
                account_id = UUID(account_data['raw_id'])
                
                # Crear DTO con is_active=False
                update_dto = AccountUpdateDTO(
                    name=account_data['name'],
                    type=AccountType[account_data['raw_type']],
                    initial_balance=Money(amount=account_data['raw_initial_amount'], currency=account_data['raw_currency']),
                    account_number=None if account_data['number'] == "-" else account_data['number'],
                    is_active=False
                )
                
                account_service.update_account(account_id, update_dto)
            
            return (current_refresh or 0) + 1
        
        except Exception as e:
            print(f"Error al desactivar cuentas: {str(e)}")
            return no_update
    
    # Callback para abrir/cerrar modal de activación
    @app.callback(
        Output('modal-activate-account', 'is_open'),
        Input('btn-activate-account', 'n_clicks'),
        Input('btn-cancel-activate', 'n_clicks'),
        Input('btn-confirm-activate', 'n_clicks'),
        State('modal-activate-account', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_activate_modal(open_click, cancel_click, confirm_click, is_open):
        """Abre o cierra el modal de confirmación de activación."""
        return not is_open
    
    # Callback para confirmar activación
    @app.callback(
        Output('store-refresh-accounts', 'data', allow_duplicate=True),
        Input('btn-confirm-activate', 'n_clicks'),
        State('table-accounts', 'selected_rows'),
        State('table-accounts', 'data'),
        State('store-refresh-accounts', 'data'),
        prevent_initial_call=True
    )
    def confirm_activate(n_clicks, selected_rows, table_data, current_refresh):
        """Activa las cuentas seleccionadas."""
        if not n_clicks or not selected_rows:
            return no_update
        
        try:
            from uuid import UUID
            from src.domain.value_objects import Money
            
            for idx in selected_rows:
                account_data = table_data[idx]
                account_id = UUID(account_data['raw_id'])
                
                # Crear DTO con is_active=True
                update_dto = AccountUpdateDTO(
                    name=account_data['name'],
                    type=AccountType[account_data['raw_type']],
                    initial_balance=Money(amount=account_data['raw_initial_amount'], currency=account_data['raw_currency']),
                    account_number=None if account_data['number'] == "-" else account_data['number'],
                    is_active=True
                )
                
                account_service.update_account(account_id, update_dto)
            
            return (current_refresh or 0) + 1
        
        except Exception as e:
            print(f"Error al activar cuentas: {str(e)}")
            return no_update
    
    # Callback para abrir/cerrar modal de filtros
    @app.callback(
        Output('modal-account-filters', 'is_open'),
        Input('btn-filters-account', 'n_clicks'),
        Input('btn-cancel-filters-account', 'n_clicks'),
        Input('btn-apply-filters-account', 'n_clicks'),
        State('modal-account-filters', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_filters_modal(open_click, cancel_click, apply_click, is_open):
        """Abre o cierra el modal de filtros."""
        return not is_open
    
    # Callback para aplicar filtros
    @app.callback(
        Output('store-account-filters', 'data'),
        Input('btn-apply-filters-account', 'n_clicks'),
        Input('btn-clear-filters-account', 'n_clicks'),
        State('filter-account-type', 'value'),
        State('filter-account-status', 'value'),
        State('filter-account-name', 'value'),
        prevent_initial_call=True
    )
    def apply_filters(apply_clicks, clear_clicks, account_type, status, name):
        """
        Aplica o limpia los filtros de cuentas.
        """
        trigger_id = ctx.triggered_id
        
        # Limpiar filtros
        if trigger_id == 'btn-clear-filters-account':
            return {}
        
        # Aplicar filtros
        if trigger_id == 'btn-apply-filters-account':
            filters = {}
            
            if account_type and account_type != 'ALL':
                filters['type'] = account_type
            
            if status and status != 'ALL':
                filters['status'] = status
            
            if name and name.strip():
                filters['name'] = name.strip()
            
            return filters
        
        return no_update
    
    # Callback para resetear valores del modal de filtros al limpiar
    @app.callback(
        Output('filter-account-type', 'value'),
        Output('filter-account-status', 'value'),
        Output('filter-account-name', 'value'),
        Input('btn-clear-filters-account', 'n_clicks'),
        prevent_initial_call=True
    )
    def clear_filter_inputs(n_clicks):
        """Resetea los valores de los inputs del modal de filtros."""
        return 'ALL', 'ALL', ''
