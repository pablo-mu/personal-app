from dash import html, dcc, dash_table, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
from datetime import datetime
from decimal import Decimal
import uuid

from src.application.services.recurring_rule_service import RecurringRuleService
from src.application.services.account_service import AccountService
from src.application.services.tag_service import TagService
from src.application.dtos import RecurringRuleCreateDTO, RecurringRuleUpdateDTO, MoneySchema
from src.domain.models import RecurrenceType, RecurrenceFrequency, IntervalUnit, TransactionType, AccountType

def layout_recurring():
    """
    Genera y devuelve el diseño (layout) de la interfaz de usuario para la sección de 'Reglas Recurrentes'.
    
    Esta vista permite al usuario gestionar transacciones automáticas que se repiten con cierta periodicidad.
    Soporta dos tipos de recurrencia:
    - Basada en calendario: Día específico cada mes/semana/año (ej: día 15 de cada mes)
    - Basada en intervalos: Cada N días/semanas/meses desde última ejecución (ej: cada 30 días)
    
    Componentes principales:
    - Barra de herramientas: Añadir, Editar, Activar/Desactivar, Eliminar, Actualizar
    - Tabla de reglas recurrentes con información completa
    - Modal de creación/edición con formulario dinámico
    - Modal de preview de próximas ejecuciones
    - Modal de confirmación de eliminación
    
    Returns:
        html.Div: Contenedor principal con todos los componentes de la vista.
    """
    return html.Div([
        # Stores para gestión de estado
        dcc.Store(id='store-refresh-recurring', data=0),
        dcc.Store(id='store-editing-recurring-id', data=None),
        
        # Título y descripción
        html.H2("🔁 Reglas Recurrentes", style={'color': '#8e44ad'}),
        html.P("Gestiona transacciones automáticas que se repiten periódicamente.", style={'color': '#7f8c8d'}),
        html.Hr(),
        
        # Barra de herramientas
        dbc.Row([
            dbc.Col([
                dbc.Button(html.I(className="bi bi-plus-circle"), color="secondary", outline=True, 
                          id='btn-add-recurring', n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Nueva Regla Recurrente", target="btn-add-recurring", placement="top"),
            ], width="auto"),
            dbc.Col([
                html.Span([
                    dbc.Button(html.I(className="bi bi-pencil"), id='btn-edit-recurring', 
                              color="secondary", outline=True, disabled=True, n_clicks=0, className="btn-sm"),
                ], id="wrapper-edit-recurring"),
                dbc.Tooltip("Editar (selecciona 1 regla)", target="wrapper-edit-recurring", placement="top"),
            ], width="auto"),
            dbc.Col([
                html.Span([
                    dbc.Button(html.I(className="bi bi-pause-circle"), id='btn-deactivate-recurring', 
                              color="secondary", outline=True, disabled=True, n_clicks=0, className="btn-sm"),
                ], id="wrapper-deactivate-recurring"),
                dbc.Tooltip("Desactivar (selecciona reglas activas)", target="wrapper-deactivate-recurring", placement="top"),
            ], width="auto"),
            dbc.Col([
                html.Span([
                    dbc.Button(html.I(className="bi bi-play-circle"), id='btn-activate-recurring', 
                              color="secondary", outline=True, disabled=True, n_clicks=0, className="btn-sm"),
                ], id="wrapper-activate-recurring"),
                dbc.Tooltip("Activar (selecciona reglas inactivas)", target="wrapper-activate-recurring", placement="top"),
            ], width="auto"),
            dbc.Col([
                html.Span([
                    dbc.Button(html.I(className="bi bi-eye"), id='btn-preview-recurring', 
                              color="secondary", outline=True, disabled=True, n_clicks=0, className="btn-sm"),
                ], id="wrapper-preview-recurring"),
                dbc.Tooltip("Ver próximas ejecuciones (selecciona 1 regla)", target="wrapper-preview-recurring", placement="top"),
            ], width="auto"),
            dbc.Col([
                html.Span([
                    dbc.Button(html.I(className="bi bi-trash"), id='btn-delete-recurring', 
                              color="secondary", outline=True, disabled=True, n_clicks=0, className="btn-sm"),
                ], id="wrapper-delete-recurring"),
                dbc.Tooltip("Eliminar (selecciona reglas)", target="wrapper-delete-recurring", placement="top"),
            ], width="auto"),
            dbc.Col([
                dbc.Button(html.I(className="bi bi-play-fill"), id='btn-execute-pending', 
                          color="success", outline=True, n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Ejecutar reglas pendientes hasta hoy", target="btn-execute-pending", placement="top"),
            ], width="auto"),
            dbc.Col([
                dbc.Button(html.I(className="bi bi-arrow-clockwise"), id='btn-refresh-recurring', 
                          color="secondary", outline=True, n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Actualizar", target="btn-refresh-recurring", placement="top"),
            ], width="auto"),
        ], className="mb-3 g-3"),
        
        # Alert para resultados de ejecución
        html.Div(id='alert-execution-result', className="mt-3"),
        
        # Tabla de reglas recurrentes
        dash_table.DataTable(
            id='table-recurring',
            columns=[
                {"name": "Tipo", "id": "transaction_type"},  # Columna oculta para colorear
                {"name": "Categoría", "id": "destination"},
                {"name": "Cuenta", "id": "source"},
                {"name": "Monto", "id": "amount"},
                {"name": "Frecuencia", "id": "frequency"},
                {"name": "Próxima", "id": "next_execution"},
                {"name": "Descripción", "id": "description"},
                {"name": "Estado", "id": "status"},
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
            style_cell_conditional=[
                {'if': {'column_id': 'transaction_type'}, 'display': 'none'}
            ],
            style_header={
                'backgroundColor': 'rgb(250, 250, 250)',
                'fontWeight': '600',
                'fontSize': '0.85rem',
                'color': '#2c3e50',
                'borderBottom': '2px solid #dee2e6',
                'padding': '10px 12px'
            },
            style_header_conditional=[
                {'if': {'column_id': 'transaction_type'}, 'display': 'none'}
            ],
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(252, 252, 252)'},
                {'if': {'state': 'selected'}, 'backgroundColor': 'rgba(0, 123, 255, 0.1)', 'border': '1px solid #007bff'},
                {'if': {'filter_query': '{status} = "✗ Inactiva"', 'column_id': 'status'}, 
                 'color': '#999', 'fontStyle': 'italic'},
                {'if': {'filter_query': '{transaction_type} = "Gasto"'}, 
                 'backgroundColor': 'rgba(231, 76, 60, 0.04)'},
                {'if': {'filter_query': '{transaction_type} = "Ingreso"'}, 
                 'backgroundColor': 'rgba(46, 204, 113, 0.04)'},
            ]
        ),
        
        # Modal de Creación/Edición
        dbc.Modal([
            dbc.ModalHeader(html.H4(id='modal-recurring-title', children="Nueva Regla Recurrente")),
            dbc.ModalBody([
                # Fila 1: Tipo de Transacción (INGRESO/GASTO)
                dbc.Row([
                    dbc.Col([
                        html.Label("Tipo de Transacción*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        dbc.RadioItems(
                            id='recurring-transaction-type',
                            options=[
                                {'label': '📉 Gasto', 'value': 'Gasto'},
                                {'label': '📈 Ingreso', 'value': 'Ingreso'},
                            ],
                            value='Gasto',
                            inline=True
                        ),
                    ], width=12),
                ], className="mb-2"),
                
                # Fila 2: Categoría y Cuenta
                dbc.Row([
                    dbc.Col([
                        html.Label(id='label-recurring-dest', children="Categoría*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        dcc.Dropdown(id='recurring-dest-account', placeholder="Categoría..."),
                    ], width=6),
                    dbc.Col([
                        html.Label(id='label-recurring-source', children="Cuenta*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        dcc.Dropdown(id='recurring-source-account', placeholder="Cuenta..."),
                    ], width=6),
                ], className="mb-2"),
                
                # Fila 3: Monto y Tags
                dbc.Row([
                    dbc.Col([
                        html.Label("Monto (€)*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        dbc.Input(id='recurring-amount', type='number', value=0, step=0.01, size="sm"),
                    ], width=4),
                    dbc.Col([
                        html.Label("Etiquetas", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        dcc.Dropdown(id='recurring-tags', multi=True, placeholder="Añadir tags..."),
                    ], width=8),
                ], className="mb-2"),
                
                html.Hr(style={'margin': '0.5rem 0'}),
                
                # Tipo de Recurrencia
                dbc.Row([
                    dbc.Col([
                        html.Label("Tipo de Recurrencia*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        dbc.RadioItems(
                            id='recurring-type',
                            options=[
                                {'label': '📅 Calendario (día fijo)', 'value': 'calendar'},
                                {'label': '⏱️ Intervalo (cada N días)', 'value': 'interval'},
                            ],
                            value='calendar',
                            inline=True
                        ),
                    ], width=12),
                ], className="mb-2"),
                
                # Configuración CALENDAR (visible condicionalmente)
                html.Div(id='calendar-config', children=[
                    dbc.Row([
                        dbc.Col([
                            html.Label("Frecuencia*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                            dcc.Dropdown(
                                id='recurring-frequency',
                                options=[
                                    {'label': 'Diaria', 'value': 'Diaria'},
                                    {'label': 'Semanal', 'value': 'Semanal'},
                                    {'label': 'Mensual', 'value': 'Mensual'},
                                    {'label': 'Anual', 'value': 'Anual'},
                                ],
                                value='Mensual'
                            ),
                        ], width=6),
                        dbc.Col([
                            html.Label("Día*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                            dbc.Input(id='recurring-day', type='number', min=1, max=31, value=1, size="sm"),
                            html.Small("Mes: 1-31 | Sem: 1=Lun", className="text-muted", style={'fontSize': '0.75rem'}),
                        ], width=6),
                    ], className="mb-2"),
                ]),
                
                
                # Configuración INTERVAL (visible condicionalmente)
                html.Div(id='interval-config', children=[
                    dbc.Row([
                        dbc.Col([
                            html.Label("Cada*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                            dbc.Input(id='recurring-interval-value', type='number', min=1, value=30, size="sm"),
                        ], width=4),
                        dbc.Col([
                            html.Label("Unidad*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                            dcc.Dropdown(
                                id='recurring-interval-unit',
                                options=[
                                    {'label': 'Días', 'value': 'Días'},
                                    {'label': 'Semanas', 'value': 'Semanas'},
                                    {'label': 'Meses', 'value': 'Meses'},
                                    {'label': 'Años', 'value': 'Años'},
                                ],
                                value='Días'
                            ),
                        ], width=8),
                    ], className="mb-2"),
                ], style={'display': 'none'}),
                
                html.Hr(style={'margin': '0.5rem 0'}),
                
                # Fechas y estado
                dbc.Row([
                    dbc.Col([
                        html.Label("Inicio*", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        dcc.DatePickerSingle(
                            id='recurring-start-date',
                            date=datetime.now().date(),
                            display_format='DD/MM/YYYY'
                        ),
                    ], width=5),
                    dbc.Col([
                        html.Label("Fin", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        dcc.DatePickerSingle(
                            id='recurring-end-date',
                            display_format='DD/MM/YYYY',
                            placeholder='Sin límite'
                        ),
                    ], width=5),
                    dbc.Col([
                        html.Label(" ", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        html.Div([
                            dbc.Checkbox(id='recurring-is-active', label='Activa', value=True),
                        ], style={'paddingTop': '8px'}),
                    ], width=2),
                ], className="mb-2"),
                
                # Descripción (opcional)
                dbc.Row([
                    dbc.Col([
                        html.Label("Descripción", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                        dbc.Input(id='recurring-description', placeholder="Ej: Netflix (opcional)", size="sm"),
                    ], width=12),
                ], className="mb-2"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancel-recurring-modal", className="ms-auto", n_clicks=0),
                dbc.Button("Guardar", id="btn-save-recurring", color="primary", n_clicks=0),
            ])
        ], id="modal-recurring", is_open=False, size="lg"),
        
        # Modal de Preview de Ejecuciones
        dbc.Modal([
            dbc.ModalHeader("🔮 Próximas Ejecuciones"),
            dbc.ModalBody([
                html.Div(id='preview-recurring-content', children=[
                    html.P("Selecciona una regla para ver sus próximas ejecuciones.", className="text-muted")
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cerrar", id="btn-close-preview-recurring", n_clicks=0),
            ])
        ], id="modal-preview-recurring", is_open=False),
        
        # Modal de Confirmación de Eliminación
        dbc.Modal([
            dbc.ModalHeader("Confirmar Eliminación"),
            dbc.ModalBody("¿Estás seguro de que quieres eliminar las reglas seleccionadas? Esta acción no se puede deshacer."),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancel-delete-recurring", className="ms-auto", n_clicks=0),
                dbc.Button("Eliminar", id="btn-confirm-delete-recurring", color="danger", n_clicks=0),
            ])
        ], id="modal-delete-recurring", is_open=False),
    ])


def register_recurring_callbacks(app, services):
    """
    Registra todos los callbacks necesarios para la funcionalidad de reglas recurrentes.
    
    Args:
        app: Instancia de la aplicación Dash
        services: Contenedor de servicios con recurring_rule, account y tag
    """
    
    # ==========================================
    # CALLBACK: Cargar datos en la tabla
    # ==========================================
    @app.callback(
        Output('table-recurring', 'data'),
        [Input('store-refresh-recurring', 'data'),
         Input('btn-refresh-recurring', 'n_clicks')]
    )
    def load_recurring_rules(refresh_trigger, refresh_clicks):
        """Carga todas las reglas recurrentes en la tabla."""
        try:
            rules = services.recurring_rule.list_recurring_rules(active_only=False)
            
            table_data = []
            for rule in rules:
                # Formatear tipo de recurrencia
                if rule.recurrence_type.value == 'calendar':
                    freq_text = f"{rule.frequency.value}"
                    if rule.frequency.value == 'Mensual':
                        freq_text += f" (día {rule.day_of_execution})"
                    elif rule.frequency.value == 'Semanal':
                        days = ['', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
                        freq_text += f" ({days[rule.day_of_execution]})"
                else:
                    freq_text = f"Cada {rule.interval_value} {rule.interval_unit.value}"
                
                # Determinar categoría y cuenta según tipo de transacción
                if rule.transaction_type.value == 'Gasto':
                    # GASTO: Categoría = destino (categoría de gasto), Cuenta = origen (de donde sale)
                    categoria = rule.destination_account_name
                    cuenta = rule.source_account_name
                else:
                    # INGRESO: Categoría = origen (categoría de ingreso), Cuenta = destino (donde entra)
                    categoria = rule.source_account_name
                    cuenta = rule.destination_account_name
                
                table_data.append({
                    'id': str(rule.id),
                    'transaction_type': rule.transaction_type.value,  # Nuevo campo para colorear
                    'destination': categoria,  # Muestra la categoría
                    'source': cuenta,  # Muestra la cuenta
                    'amount': f"{rule.amount.amount:.2f} {rule.amount.currency}",
                    'frequency': freq_text,
                    'next_execution': rule.next_execution_date.strftime('%d/%m/%Y') if rule.next_execution_date else '-',
                    'description': rule.description or '-',
                    'status': '✓ Activa' if rule.is_active else '✗ Inactiva',
                })
            
            return table_data
        except Exception as e:
            print(f"Error cargando reglas: {str(e)}")
            return []
    
    # ==========================================
    # CALLBACK: Ejecutar reglas pendientes
    # ==========================================
    @app.callback(
        [Output('alert-execution-result', 'children'),
         Output('store-refresh-recurring', 'data', allow_duplicate=True)],
        Input('btn-execute-pending', 'n_clicks'),
        State('store-refresh-recurring', 'data'),
        prevent_initial_call=True
    )
    def execute_pending_rules(n_clicks, current_refresh):
        """Ejecuta todas las ocurrencias pendientes de las reglas recurrentes hasta hoy."""
        if not n_clicks:
            return no_update, no_update
        
        try:
            from datetime import datetime
            
            # Ejecutar TODAS las ocurrencias pendientes hasta hoy
            execution_date = datetime.now()
            created_transactions = services.recurring_rule.execute_all_pending_until(
                execution_date, 
                services.transaction
            )
            
            if created_transactions:
                # Agrupar por regla para mejor visualización
                by_rule = {}
                for tx in created_transactions:
                    rule_desc = tx['rule_description']
                    if rule_desc not in by_rule:
                        by_rule[rule_desc] = {'count': 0, 'total': 0}
                    by_rule[rule_desc]['count'] += 1
                    by_rule[rule_desc]['total'] += tx['amount']
                
                message = dbc.Alert([
                    html.H5(f"✅ {len(created_transactions)} transacciones creadas", className="alert-heading"),
                    html.Hr(),
                    html.Ul([
                        html.Li(f"{rule}: {info['count']} ocurrencias ({info['total']:.2f} EUR total)")
                        for rule, info in by_rule.items()
                    ])
                ], color="success", dismissable=True, duration=10000)
            else:
                message = dbc.Alert(
                    "ℹ️ No hay reglas pendientes de ejecutar hasta hoy.",
                    color="info",
                    dismissable=True,
                    duration=4000
                )
            
            # Refrescar la tabla
            return message, (current_refresh or 0) + 1
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = dbc.Alert(
                f"❌ Error ejecutando reglas: {str(e)}",
                color="danger",
                dismissable=True,
                duration=6000
            )
            return error_msg, no_update
    
    # ==========================================
    # CALLBACK: Habilitar/deshabilitar botones según selección
    # ==========================================
    @app.callback(
        [Output('btn-edit-recurring', 'disabled'),
         Output('btn-delete-recurring', 'disabled'),
         Output('btn-activate-recurring', 'disabled'),
         Output('btn-deactivate-recurring', 'disabled'),
         Output('btn-preview-recurring', 'disabled')],
        [Input('table-recurring', 'selected_rows'),
         Input('table-recurring', 'data')]
    )
    def update_button_states(selected_rows, table_data):
        """Habilita/deshabilita botones según la selección."""
        if not selected_rows or not table_data:
            return True, True, True, True, True
        
        num_selected = len(selected_rows)
        
        # Verificar si hay activas/inactivas seleccionadas
        has_active = any(table_data[i]['status'] == '✓ Activa' for i in selected_rows)
        has_inactive = any(table_data[i]['status'] == '✗ Inactiva' for i in selected_rows)
        
        edit_disabled = num_selected != 1
        delete_disabled = num_selected == 0
        activate_disabled = not has_inactive
        deactivate_disabled = not has_active
        preview_disabled = num_selected != 1
        
        return edit_disabled, delete_disabled, activate_disabled, deactivate_disabled, preview_disabled
    
    # ==========================================
    # CALLBACK: Abrir modal de creación
    # ==========================================
    @app.callback(
        [Output('modal-recurring', 'is_open', allow_duplicate=True),
         Output('modal-recurring-title', 'children', allow_duplicate=True),
         Output('store-editing-recurring-id', 'data', allow_duplicate=True),
         # Limpiar formulario
         Output('recurring-transaction-type', 'value', allow_duplicate=True),
         Output('recurring-description', 'value', allow_duplicate=True),
         Output('recurring-amount', 'value', allow_duplicate=True),
         Output('recurring-source-account', 'value', allow_duplicate=True),
         Output('recurring-dest-account', 'value', allow_duplicate=True),
         Output('recurring-tags', 'value', allow_duplicate=True),
         Output('recurring-type', 'value', allow_duplicate=True),
         Output('recurring-is-active', 'value', allow_duplicate=True)],
        Input('btn-add-recurring', 'n_clicks'),
        prevent_initial_call=True
    )
    def open_create_modal(n_clicks):
        """Abre el modal para crear una nueva regla."""
        if n_clicks:
            return True, "Nueva Regla Recurrente", None, 'Gasto', "", 0, None, None, [], 'calendar', True
        return no_update
    
    # ==========================================
    # CALLBACK: Abrir modal de edición
    # ==========================================
    @app.callback(
        [Output('modal-recurring', 'is_open', allow_duplicate=True),
         Output('modal-recurring-title', 'children', allow_duplicate=True),
         Output('store-editing-recurring-id', 'data', allow_duplicate=True),
         Output('recurring-transaction-type', 'value', allow_duplicate=True),
         Output('recurring-description', 'value', allow_duplicate=True),
         Output('recurring-amount', 'value', allow_duplicate=True),
         Output('recurring-source-account', 'value', allow_duplicate=True),
         Output('recurring-dest-account', 'value', allow_duplicate=True),
         Output('recurring-tags', 'value', allow_duplicate=True),
         Output('recurring-type', 'value', allow_duplicate=True),
         Output('recurring-frequency', 'value', allow_duplicate=True),
         Output('recurring-day', 'value', allow_duplicate=True),
         Output('recurring-interval-value', 'value', allow_duplicate=True),
         Output('recurring-interval-unit', 'value', allow_duplicate=True),
         Output('recurring-start-date', 'date', allow_duplicate=True),
         Output('recurring-end-date', 'date', allow_duplicate=True),
         Output('recurring-is-active', 'value', allow_duplicate=True)],
        Input('btn-edit-recurring', 'n_clicks'),
        [State('table-recurring', 'selected_rows'),
         State('table-recurring', 'data')],
        prevent_initial_call=True
    )
    def open_edit_modal(n_clicks, selected_rows, table_data):
        """Abre el modal para editar la regla seleccionada."""
        if not n_clicks or not selected_rows or not table_data:
            return no_update
        
        try:
            rule_id = uuid.UUID(table_data[selected_rows[0]]['id'])
            rule = services.recurring_rule.get_recurring_rule(rule_id)
            
            rec_type = rule.recurrence_type.value
            
            return (
                True,  # is_open
                "Editar Regla Recurrente",
                str(rule.id),
                rule.transaction_type.value,
                rule.description,
                float(rule.amount.amount),
                str(rule.source_account_id),
                str(rule.destination_account_id),
                [str(tag_id) for tag_id in rule.tags_ids],
                rec_type,
                rule.frequency.value if rule.frequency else 'Mensual',
                rule.day_of_execution if rule.day_of_execution else 1,
                rule.interval_value if rule.interval_value else 30,
                rule.interval_unit.value if rule.interval_unit else 'Días',
                rule.start_date.date() if rule.start_date else datetime.now().date(),
                rule.end_date.date() if rule.end_date else None,
                rule.is_active
            )
        except Exception as e:
            print(f"Error abriendo modal de edición: {str(e)}")
            return no_update
    
    # ==========================================
    # CALLBACK: Filtrar cuentas y cambiar etiquetas según tipo de transacción
    # ==========================================
    @app.callback(
        [Output('recurring-source-account', 'options'),
         Output('recurring-dest-account', 'options'),
         Output('recurring-tags', 'options'),
         Output('label-recurring-source', 'children'),
         Output('label-recurring-dest', 'children'),
         Output('recurring-transaction-type', 'disabled')],
        [Input('modal-recurring', 'is_open'),
         Input('recurring-transaction-type', 'value')],
        State('store-editing-recurring-id', 'data')
    )
    def load_dropdown_options(is_open, transaction_type, editing_id):
        """Carga las opciones de cuentas y tags cuando se abre el modal.
        Filtra cuentas según el tipo de transacción seleccionado."""
        if not is_open:
            return no_update
        
        try:
            # Cargar todas las cuentas activas
            accounts = services.account.list_accounts()
            
            # Filtrar según tipo de transacción
            if transaction_type == 'Gasto':
                # GASTO: origen = activos, destino = gastos
                source_options = [
                    {'label': f"{acc.name}", 'value': str(acc.id)}
                    for acc in accounts 
                    if acc.is_active and acc.type in [AccountType.ASSET, AccountType.LIABILITY]
                ]
                dest_options = [
                    {'label': f"{acc.name}", 'value': str(acc.id)}
                    for acc in accounts 
                    if acc.is_active and acc.type == AccountType.EXPENSE
                ]
                label_source = "Cuenta (Pagas con...)*"
                label_dest = "Categoría de Gasto*"
            else:  # Ingreso
                # INGRESO: origen = ingresos, destino = activos
                source_options = [
                    {'label': f"{acc.name}", 'value': str(acc.id)}
                    for acc in accounts 
                    if acc.is_active and acc.type == AccountType.INCOME
                ]
                dest_options = [
                    {'label': f"{acc.name}", 'value': str(acc.id)}
                    for acc in accounts 
                    if acc.is_active and acc.type in [AccountType.ASSET, AccountType.LIABILITY]
                ]
                label_source = "Categoría de Ingreso*"
                label_dest = "Cuenta (Depositar en...)*"
            
            # Cargar tags
            tags = services.tag.list_tags()
            tag_options = [
                {'label': tag.name, 'value': str(tag.id)}
                for tag in tags
            ]
            
            # Deshabilitar cambio de tipo si estamos editando
            disable_type = editing_id is not None
            
            return source_options, dest_options, tag_options, label_source, label_dest, disable_type
        except Exception as e:
            print(f"Error cargando opciones: {str(e)}")
            return [], [], [], "Cuenta*", "Categoría*", False
    
    # ==========================================
    # CALLBACK: Cargar dropdowns de cuentas y tags (ELIMINADO - reemplazado por el anterior)
    # ==========================================
    # @app.callback(
    #     [Output('recurring-source-account', 'options'),
    #      Output('recurring-dest-account', 'options'),
    #      Output('recurring-tags', 'options')],
    #     Input('modal-recurring', 'is_open')
    # )
    # def load_dropdown_options(is_open):
    #     ... código eliminado ...
    
    # ==========================================
    # CALLBACK: Mostrar/ocultar configuración según tipo
    # ==========================================
    @app.callback(
        [Output('calendar-config', 'style'),
         Output('interval-config', 'style')],
        Input('recurring-type', 'value')
    )
    def toggle_recurrence_config(rec_type):
        """Muestra/oculta los campos según el tipo de recurrencia."""
        if rec_type == 'calendar':
            return {'display': 'block'}, {'display': 'none'}
        else:
            return {'display': 'none'}, {'display': 'block'}
    
    # ==========================================
    # CALLBACK: Guardar regla (crear o editar)
    # ==========================================
    @app.callback(
        [Output('modal-recurring', 'is_open', allow_duplicate=True),
         Output('store-refresh-recurring', 'data', allow_duplicate=True),
         Output('table-recurring', 'selected_rows', allow_duplicate=True)],
        Input('btn-save-recurring', 'n_clicks'),
        [State('store-editing-recurring-id', 'data'),
         State('recurring-transaction-type', 'value'),
         State('recurring-description', 'value'),
         State('recurring-amount', 'value'),
         State('recurring-source-account', 'value'),
         State('recurring-dest-account', 'value'),
         State('recurring-tags', 'value'),
         State('recurring-type', 'value'),
         State('recurring-frequency', 'value'),
         State('recurring-day', 'value'),
         State('recurring-interval-value', 'value'),
         State('recurring-interval-unit', 'value'),
         State('recurring-start-date', 'date'),
         State('recurring-end-date', 'date'),
         State('recurring-is-active', 'value'),
         State('store-refresh-recurring', 'data')],
        prevent_initial_call=True
    )
    def save_recurring_rule(n_clicks, editing_id, transaction_type, description, amount, source_id, dest_id, 
                           tags, rec_type, frequency, day, interval_val, interval_unit,
                           start_date, end_date, is_active, current_refresh):
        """Guarda (crea o actualiza) una regla recurrente."""
        if not n_clicks:
            return no_update
        
        try:
            # Validaciones básicas
            if not source_id or not dest_id or not amount or not transaction_type:
                print("Error: Campos obligatorios vacíos")
                return no_update
            
            # Convertir fechas
            start = datetime.fromisoformat(start_date) if start_date else datetime.now()
            end = datetime.fromisoformat(end_date) if end_date else None
            
            # Preparar DTOs según tipo
            if editing_id:
                # Editar
                dto = RecurringRuleUpdateDTO(
                    description=description,
                    amount=MoneySchema(amount=Decimal(str(amount)), currency="EUR"),
                    tags_ids=[uuid.UUID(t) for t in tags] if tags else [],
                    end_date=end,
                    is_active=is_active
                )
                services.recurring_rule.update_recurring_rule(uuid.UUID(editing_id), dto)
            else:
                # Crear
                dto = RecurringRuleCreateDTO(
                    description=description,
                    amount=MoneySchema(amount=Decimal(str(amount)), currency="EUR"),
                    source_account_id=uuid.UUID(source_id),
                    destination_account_id=uuid.UUID(dest_id),
                    transaction_type=TransactionType(transaction_type),
                    tags_ids=[uuid.UUID(t) for t in tags] if tags else [],
                    recurrence_type=RecurrenceType.CALENDAR_BASED if rec_type == 'calendar' else RecurrenceType.INTERVAL_BASED,
                    frequency=RecurrenceFrequency(frequency) if rec_type == 'calendar' else None,
                    day_of_execution=int(day) if rec_type == 'calendar' else None,
                    interval_value=int(interval_val) if rec_type == 'interval' else None,
                    interval_unit=IntervalUnit(interval_unit) if rec_type == 'interval' else None,
                    start_date=start,
                    end_date=end,
                    is_active=is_active
                )
                services.recurring_rule.create_recurring_rule(dto)
            
            # Cerrar modal y refrescar tabla
            return False, current_refresh + 1, []
        
        except Exception as e:
            print(f"Error guardando regla: {str(e)}")
            import traceback
            traceback.print_exc()
            return no_update
    
    # ==========================================
    # CALLBACK: Cancelar modal
    # ==========================================
    @app.callback(
        Output('modal-recurring', 'is_open', allow_duplicate=True),
        Input('btn-cancel-recurring-modal', 'n_clicks'),
        prevent_initial_call=True
    )
    def close_modal(n_clicks):
        """Cierra el modal de creación/edición."""
        if n_clicks:
            return False
        return no_update
    
    # ==========================================
    # CALLBACK: Activar/Desactivar reglas
    # ==========================================
    @app.callback(
        [Output('store-refresh-recurring', 'data', allow_duplicate=True),
         Output('table-recurring', 'selected_rows', allow_duplicate=True)],
        [Input('btn-activate-recurring', 'n_clicks'),
         Input('btn-deactivate-recurring', 'n_clicks')],
        [State('table-recurring', 'selected_rows'),
         State('table-recurring', 'data'),
         State('store-refresh-recurring', 'data')],
        prevent_initial_call=True
    )
    def toggle_rule_status(activate_clicks, deactivate_clicks, selected_rows, table_data, current_refresh):
        """Activa o desactiva las reglas seleccionadas."""
        if not selected_rows or not table_data:
            return no_update
        
        try:
            triggered_id = ctx.triggered_id
            new_status = True if triggered_id == 'btn-activate-recurring' else False
            
            for idx in selected_rows:
                rule_id = uuid.UUID(table_data[idx]['id'])
                dto = RecurringRuleUpdateDTO(is_active=new_status)
                services.recurring_rule.update_recurring_rule(rule_id, dto)
            
            return current_refresh + 1, []
        except Exception as e:
            print(f"Error cambiando estado: {str(e)}")
            return no_update
    
    # ==========================================
    # CALLBACK: Abrir modal de confirmación de eliminación
    # ==========================================
    @app.callback(
        Output('modal-delete-recurring', 'is_open'),
        [Input('btn-delete-recurring', 'n_clicks'),
         Input('btn-cancel-delete-recurring', 'n_clicks'),
         Input('btn-confirm-delete-recurring', 'n_clicks')],
        State('modal-delete-recurring', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_delete_modal(delete_clicks, cancel_clicks, confirm_clicks, is_open):
        """Abre/cierra el modal de confirmación de eliminación."""
        return not is_open
    
    # ==========================================
    # CALLBACK: Confirmar eliminación
    # ==========================================
    @app.callback(
        [Output('store-refresh-recurring', 'data', allow_duplicate=True),
         Output('table-recurring', 'selected_rows', allow_duplicate=True)],
        Input('btn-confirm-delete-recurring', 'n_clicks'),
        [State('table-recurring', 'selected_rows'),
         State('table-recurring', 'data'),
         State('store-refresh-recurring', 'data')],
        prevent_initial_call=True
    )
    def confirm_delete(n_clicks, selected_rows, table_data, current_refresh):
        """Elimina las reglas seleccionadas."""
        if not n_clicks or not selected_rows or not table_data:
            return no_update
        
        try:
            for idx in selected_rows:
                rule_id = uuid.UUID(table_data[idx]['id'])
                services.recurring_rule.delete_recurring_rule(rule_id)
            
            return current_refresh + 1, []
        except Exception as e:
            print(f"Error eliminando reglas: {str(e)}")
            return no_update
    
    # ==========================================
    # CALLBACK: Preview de ejecuciones
    # ==========================================
    @app.callback(
        [Output('modal-preview-recurring', 'is_open', allow_duplicate=True),
         Output('preview-recurring-content', 'children')],
        Input('btn-preview-recurring', 'n_clicks'),
        [State('table-recurring', 'selected_rows'),
         State('table-recurring', 'data')],
        prevent_initial_call=True
    )
    def show_preview(n_clicks, selected_rows, table_data):
        """Muestra las próximas ejecuciones de la regla seleccionada."""
        if not n_clicks or not selected_rows or not table_data:
            return no_update
        
        try:
            rule_id = uuid.UUID(table_data[selected_rows[0]]['id'])
            rule_dto = services.recurring_rule.get_recurring_rule(rule_id)
            
            # Obtener la regla del dominio para usar preview_executions
            with services.recurring_rule.uow:
                rule = services.recurring_rule.uow.recurring_rules.get(rule_id)
                preview_dates = services.recurring_rule.preview_executions(rule, num_executions=10)
            
            # Crear lista con las fechas
            content = [
                html.H5(f"📅 {rule_dto.description}", className="mb-3"),
                html.P(f"Monto: {rule_dto.amount.amount} {rule_dto.amount.currency}", className="text-muted"),
                html.Hr(),
                html.H6("Próximas 10 ejecuciones:", className="mb-2"),
                html.Ol([
                    html.Li(fecha.strftime('%d/%m/%Y (%A)'), className="mb-1")
                    for fecha in preview_dates
                ])
            ]
            
            if not preview_dates:
                content = [
                    html.P("No hay ejecuciones programadas (la regla puede estar expirada o inactiva).", 
                          className="text-muted")
                ]
            
            return True, content
        except Exception as e:
            print(f"Error mostrando preview: {str(e)}")
            return True, [html.P(f"Error: {str(e)}", className="text-danger")]
    
    # ==========================================
    # CALLBACK: Cerrar modal de preview
    # ==========================================
    @app.callback(
        Output('modal-preview-recurring', 'is_open', allow_duplicate=True),
        Input('btn-close-preview-recurring', 'n_clicks'),
        prevent_initial_call=True
    )
    def close_preview_modal(n_clicks):
        """Cierra el modal de preview."""
        if n_clicks:
            return False
        return no_update
