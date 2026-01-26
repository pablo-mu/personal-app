from dash import ctx, html, dash_table, Input, Output, State, dcc, no_update
import dash_bootstrap_components as dbc
from decimal import Decimal
from src.domain.models import AccountType
from src.application.services.account_service import AccountService
from src.application.dtos import AccountCreateDTO, AccountUpdateDTO, MoneySchema
from datetime import datetime

def layout_categories():
    """
    Genera y devuelve el diseño (layout) de la interfaz de usuario para la sección de 'Categorías'.
    
    Esta vista permite al usuario gestionar las cuentas de tipo Gasto e Ingreso, que funcionalmente actúan como categorías.
    Se muestran en dos tablas lado a lado: Ingresos (verde) y Gastos (rojo).
    
    Returns:
        html.Div: Contenedor principal con todos los componentes de la vista.
    """
    return html.Div([
        # Stores para gestionar estado
        dcc.Store(id='store-refresh-categories', data=0),
        dcc.Store(id='store-search-categories', data=''),
        
        # Título y subtítulo
        html.H2("🛒 Gestión de Categorías", style={'color': '#27ae60'}),
        html.P("Agrupa tus transacciones para un mejor análisis.", style={'color': '#7f8c8d'}),
        html.Hr(),

        # Botonera
        dbc.Row([
            dbc.Col([
                dbc.Button(html.I(className="bi bi-plus-circle"), color="secondary", outline=True, id='btn-add-category', n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Nueva Categoría", target="btn-add-category", placement="top"),
            ], width="auto"),
            dbc.Col([
                html.Span([
                    dbc.Button(html.I(className="bi bi-pencil"), id='btn-edit-category', color="secondary", outline=True, disabled=True, n_clicks=0, className="btn-sm"),
                ], id="wrapper-edit-category"),
                dbc.Tooltip("Editar (selecciona 1 categoría)", target="wrapper-edit-category", placement="top"),
            ], width="auto"),
            dbc.Col([
                dbc.Button(html.I(className="bi bi-arrow-clockwise"), id='btn-refresh-categories', color="secondary", outline=True, n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Actualizar", target="btn-refresh-categories", placement="top"),
            ], width="auto"),
            dbc.Col(
                dcc.Dropdown(
                    id='filter-category-type',
                    options=[
                        {'label': '📋 Todas', 'value': 'ALL'},
                        {'label': '💰 Ingresos', 'value': 'INCOME'},
                        {'label': '💸 Gastos', 'value': 'EXPENSE'},
                    ],
                    value='ALL',
                    clearable=False,
                    style={'width': '150px'},
                ),
                width="auto"
            ),
            dbc.Col(
                dbc.Input(id='search-category', type="text", placeholder="Buscar categoría...", size="sm"),
                width=3
            ),
        ], className="mb-3 g-3 align-items-center"),

        # Tabla única con badges de colores para diferenciar tipos
        html.H5("Categorías", className="mb-3"),
        dash_table.DataTable(
            id='table-categories',
            columns=[
                {"name": "Nombre", "id": "name", "editable": False},
                {"name": "Tipo", "id": "type_display", "editable": False},
            ],
            data=[],
            row_selectable='multi',
            selected_rows=[],
            page_current=0,
            page_size=25,
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
                {'if': {'state': 'selected'}, 'backgroundColor': 'rgba(0, 123, 255, 0.1)', 'border': '1px solid #007bff'},
                # Ingresos en verde claro
                {
                    'if': {
                        'filter_query': '{type} = INCOME',
                        'column_id': 'type_display'
                    },
                    'backgroundColor': 'rgba(46, 204, 113, 0.15)',
                    'color': '#155724',
                    'fontWeight': '600'
                },
                # Gastos en rojo claro
                {
                    'if': {
                        'filter_query': '{type} = EXPENSE',
                        'column_id': 'type_display'
                    },
                    'backgroundColor': 'rgba(231, 76, 60, 0.15)',
                    'color': '#721c24',
                    'fontWeight': '600'
                },
            ]
        ),
        
        # Modal de Creación/Edición de Categoría
        dbc.Modal([
            dbc.ModalHeader(html.H4(id='modal-category-title', children="Nueva Categoría")),
            dbc.ModalBody([
                dcc.Store(id='category-editing-id', data=None),
                
                # Fila 1: Nombre y Tipo
                html.Div([
                    html.Div([
                        html.Label("Nombre:", style={'fontWeight': 'bold'}),
                        dbc.Input(id='category-input-name', type='text', placeholder='Mi Categoría', style={'width': '100%'}),
                    ], style={'flex': '2'}),
                    
                    html.Div([
                        html.Label("Tipo:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='category-input-type',
                            options=[
                                {'label': f"💰 {AccountType.INCOME.value}", 'value': AccountType.INCOME.name},
                                {'label': f"💸 {AccountType.EXPENSE.value}", 'value': AccountType.EXPENSE.name}
                            ],
                            placeholder="Selecciona...",
                            style={'width': '100%'}
                        ),
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '12px'}),
                
                # Mensaje de error/estado dentro del modal
                html.Div(id='msg-category-modal-result', style={'marginTop': '10px', 'textAlign': 'center', 'fontWeight': 'bold'})
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancel-modal-category", className="ms-auto", n_clicks=0),
                dbc.Button("💾 Guardar", id="btn-save-modal-category", color="success", n_clicks=0),
            ])
        ], id="modal-category-form", is_open=False, size="md"),
        
        # Div auxiliar para outputs
        html.Div(id='msg-category-result', style={'display': 'none'})
    ])

def register_callbacks(app, account_service: AccountService):
    """
    Registra los callbacks necesarios para la vista de Categorías.
    
    Args:
        app (Dash): Instancia de la app Dash.
        account_service (AccountService): Servicio para acceder a las Cuentas (Categorías).
    """

    # 1. Actualizar tabla de categorías
    @app.callback(
        Output('table-categories', 'data'),
        Input('store-refresh-categories', 'data'),
        Input('url', 'pathname'),
        Input('btn-refresh-categories', 'n_clicks'),
        Input('btn-save-modal-category', 'n_clicks'),
        Input('filter-category-type', 'value'),
        State('search-category', 'value'),
    )
    def update_table(refresh_store, pathname, n_refresh, n_save, filter_type, search_value):
        """
        Actualiza la tabla de categorías (Ingresos y Gastos en una sola tabla)
        """
        if pathname != '/categories':
            return no_update
        
        try:
            # Obtener todas las categorías activas (cuentas de tipo INCOME y EXPENSE)
            all_accounts = account_service.list_accounts()
            
            # Filtrar solo INCOME y EXPENSE activas
            categories = [acc for acc in all_accounts if acc.type in [AccountType.INCOME, AccountType.EXPENSE] and acc.is_active]
            
            # Aplicar filtro de tipo
            if filter_type and filter_type != 'ALL':
                categories = [acc for acc in categories if acc.type.name == filter_type]
            
            # Aplicar búsqueda si hay texto
            if search_value:
                search_lower = search_value.lower()
                categories = [acc for acc in categories if search_lower in acc.name.lower()]
            
            # Ordenar: primero Ingresos, luego Gastos, alfabéticamente dentro de cada tipo
            categories.sort(key=lambda x: (x.type.name, x.name.lower()))
            
            # Formatear datos para la tabla
            data = []
            for acc in categories:
                type_display = "💰 Ingreso" if acc.type == AccountType.INCOME else "💸 Gasto"
                data.append({
                    "id": str(acc.id),
                    "name": acc.name,
                    "type": acc.type.name,  # Para filtros condicionales
                    "type_display": type_display,  # Para mostrar
                    "raw_id": str(acc.id),
                    "raw_type": acc.type.name
                })
            
            return data
        
        except Exception as e:
            print(f"Error al actualizar tabla de categorías: {str(e)}")
            return no_update

    # 2. Actualizar búsqueda en tiempo real
    @app.callback(
        Output('store-search-categories', 'data'),
        Input('search-category', 'value'),
    )
    def update_search(search_value):
        return search_value or ''

    # 3. Habilitar/Deshabilitar botón de editar según selección
    @app.callback(
        Output('btn-edit-category', 'disabled'),
        Input('table-categories', 'selected_rows'),
    )
    def toggle_edit_button(selected_rows):
        """
        Habilita el botón de editar solo si hay exactamente 1 categoría seleccionada.
        """
        return len(selected_rows or []) != 1

    # 4. Abrir/cerrar modal de creación/edición
    @app.callback(
        Output('modal-category-form', 'is_open'),
        Output('modal-category-title', 'children'),
        Output('category-editing-id', 'data'),
        Output('category-input-name', 'value'),
        Output('category-input-type', 'value'),
        Output('category-input-type', 'disabled'),
        Input('btn-add-category', 'n_clicks'),
        Input('btn-edit-category', 'n_clicks'),
        Input('btn-cancel-modal-category', 'n_clicks'),
        Input('store-refresh-categories', 'data'),
        State('table-categories', 'data'),
        State('table-categories', 'selected_rows'),
        State('modal-category-form', 'is_open'),
    )
    def toggle_edit_modal(_, __, ___, ____, table_data, selected_rows, is_open):
        """
        Gestiona apertura/cierre del modal y carga de datos para edición.
        Al editar, el tipo no se puede cambiar (solo el nombre).
        """
        trigger_id = ctx.triggered_id
        
        if not trigger_id:
            return is_open, no_update, no_update, no_update, no_update, no_update
        
        # Cerrar modal
        if trigger_id in ['btn-cancel-modal-category', 'store-refresh-categories']:
            return False, no_update, None, '', None, False
        
        # Abrir modal para crear
        if trigger_id == 'btn-add-category':
            return True, "Nueva Categoría", None, '', None, False
        
        # Abrir modal para editar
        if trigger_id == 'btn-edit-category':
            if not selected_rows or len(selected_rows) != 1:
                return no_update, no_update, no_update, no_update, no_update, no_update
            
            selected_cat = table_data[selected_rows[0]]
            return True, "Editar Categoría", selected_cat['raw_id'], selected_cat['name'], selected_cat['raw_type'], True
        
        return is_open, no_update, no_update, no_update, no_update, no_update

    # 5. Guardar categoría (crear o actualizar)
    @app.callback(
        Output('msg-category-modal-result', 'children'),
        Output('store-refresh-categories', 'data'),
        Input('btn-save-modal-category', 'n_clicks'),
        State('category-editing-id', 'data'),
        State('category-input-name', 'value'),
        State('category-input-type', 'value'),
        State('store-refresh-categories', 'data'),
        prevent_initial_call=True
    )
    def save_category(n_clicks, editing_id, name, acc_type, current_refresh):
        """
        Guarda (crea o actualiza) una categoría.
        Las categorías siempre están activas y al editar no se puede cambiar el tipo.
        """
        if not name or not acc_type:
            return html.Span("⚠️ El nombre y tipo son obligatorios", style={'color': 'orange'}), no_update
        
        try:
            if editing_id:
                # Actualizar existente (solo nombre, el tipo no cambia)
                dto = AccountUpdateDTO(
                    name=name,
                    type=AccountType[acc_type],
                    is_active=True
                )
                account_service.update_account(editing_id, dto)
                return html.Span("✅ Categoría actualizada", style={'color': 'green'}), current_refresh + 1
            else:
                # Crear nueva
                dto = AccountCreateDTO(
                    name=name,
                    type=AccountType[acc_type],
                    initial_balance=MoneySchema(amount=Decimal('0.00'), currency='EUR'),
                    account_number=None,
                    is_active=True
                )
                account_service.create_account(dto)
                return html.Span("✅ Categoría creada", style={'color': 'green'}), current_refresh + 1
        
        except Exception as e:
            return html.Span(f"❌ Error: {str(e)}", style={'color': 'red'}), no_update

