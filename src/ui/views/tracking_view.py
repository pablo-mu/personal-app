from dash import html, dcc, Input, Output, State, ALL, ctx, no_update
import dash_bootstrap_components as dbc
from decimal import Decimal
from datetime import datetime
from src.application.dtos import AccountCreateDTO, MoneySchema, TransactionEntryDTO, TagDTO
from src.domain.models import AccountType

# --- LAYOUT EXPORTS ---

def layout_daily():
    """
    Genera y devuelve el diseño (layout) de la interfaz de usuario para la sección de 'Movimientos Diarios'.
    
    Esta vista es el corazón operativo de la aplicación, permitiendo registrar nuevas transacciones (Gastos, Ingresos, Transferencias)
    y visualizar el historial reciente.
    
    Componentes principales:
    - Barra de comandos superior: Botones rápidos para iniciar un nuevo Gasto, Ingreso o Transferencia.
    - Contenedor de Formulario Dinámico: Se muestra/oculta según la acción seleccionada. Cambia sus etiquetas y opciones
      contextualmente (ej. "Origen" vs "Pagado con"). Permite crear etiquetas nuevas al vuelo.
    - Historial: Lista de los últimos movimientos registrados.
    
    Returns:
        html.Div: Contenedor principal con todos los componentes de la vista.
    """
    return html.Div([
        # Encabezado
        html.H2("📝 Movimientos Diarios", style={'color': '#2c3e50'}),
        html.P("Registra y gestiona tus transacciones diarias aquí.", style={'color': '#7f8c8d'}),
        html.Hr(),
        
        # --- COMMAND BAR (Botonera de Acciones Rápidas) ---
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className="bi bi-dash-circle me-2"),
                    "Nuevo Gasto"
                ], id='btn-mode-expense', color="danger", outline=True, n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Registrar un gasto", target="btn-mode-expense", placement="top"),
            ], width="auto"),
            dbc.Col([
                dbc.Button([
                    html.I(className="bi bi-plus-circle me-2"),
                    "Nuevo Ingreso"
                ], id='btn-mode-income', color="success", outline=True, n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Registrar un ingreso", target="btn-mode-income", placement="top"),
            ], width="auto"),
            dbc.Col([
                dbc.Button([
                    html.I(className="bi bi-arrow-left-right me-2"),
                    "Transferencia"
                ], id='btn-mode-transfer', color="primary", outline=True, n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Transferir entre cuentas", target="btn-mode-transfer", placement="top"),
            ], width="auto"),
        ], className="mb-3 g-2"), 

        # --- FORMULARIO DINÁMICO (Oculto por defecto) ---
        html.Div(id='transaction-form-container', style={'display': 'none'}, children=[
            # Cabecera del formulario con botón de cierre
            html.Div([
                html.H4(id='form-title', children="Registrar Transacción", style={'flex': '1'}),
                html.Button('❌', id='btn-close-form', n_clicks=0, style={'background': 'none', 'border': 'none', 'fontSize': '1.5em', 'cursor': 'pointer'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
            
            # Stores para mantener el estado del formulario
            dcc.Store(id='current-tx-mode', data='EXPENSE'), 
            dcc.Store(id='editing-tx-id', data=None), # ID si estamos editando, None si es nuevo

            # 1. Row: Selección de Cuentas (Origen y Destino)
            html.Div([
                html.Div([
                    html.Label(id='label-source', children="Cuenta Origen", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='tx-source', placeholder="Selecciona...", style={'width': '100%'}),
                ], style={'flex': '1'}),
                
                html.Div([
                    html.Label(id='label-dest', children="Cuenta Destino", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='tx-dest', placeholder="Selecciona...", style={'width': '100%'}),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}),

            # 2. Row: Monto, Fecha y Etiquetas
            html.Div([
                 html.Div([
                    html.Label("Monto (€)", style={'fontWeight': 'bold'}),
                    dcc.Input(id='tx-amount', type='number', value=0, step=0.01, style={'width': '100%', 'padding': '8px'}),
                ], style={'flex': '1'}),

                 html.Div([
                    html.Label("Fecha:", style={'fontWeight': 'bold', 'display': 'block'}),
                    dcc.DatePickerSingle(
                        id='tx-date',
                        min_date_allowed=datetime(2020, 1, 1),
                        max_date_allowed=datetime(2030, 12, 31),
                        initial_visible_month=datetime.now(),
                        date=datetime.now().date(),
                        style={'width':'100%'}
                    ),
                ], style={'flex': '1'}),
                
                html.Div([
                    html.Label("Etiquetas:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='tx-tags', multi=True, placeholder="Añadir tags...", style={'width': '100%'}),
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}),
            
            # 3. Row: Descripción y Botón Guardar
            html.Div([
                html.Label("Descripción (Opcional)", style={'fontWeight': 'bold'}),
                dcc.Input(id='tx-desc', type='text', placeholder='¿Qué es?', style={'width': '100%', 'padding': '8px'}),
            ], style={'marginBottom': '15px'}),
            
            html.Button('💾 Guardar Transacción', id='btn-submit-tx', n_clicks=0, style={
                'backgroundColor': '#2c3e50', 'color': 'white', 'width': '100%', 'padding': '12px', 'fontWeight': 'bold', 'border': 'none', 'borderRadius': '5px'
            }),
            html.Div(id='msg-tx-result', style={'marginTop': '10px', 'textAlign': 'center'})
        ]),

        html.Hr(),
        
        # --- Listado de Últimos Movimientos ---
        dbc.Row([
            dbc.Col(html.H3("Últimos Movimientos"), width="auto"),
            #Espacio en blanco para separar
            dbc.Col([], width="auto", style={'flex': '1'}),
            dbc.Col([
                dbc.Button(html.I(className="bi bi-arrow-clockwise"), id='btn-refresh-tx', color="secondary", outline=True, n_clicks=0, className="btn-sm"),
                dbc.Tooltip("Actualizar lista de movimientos", target="btn-refresh-tx", placement="top"),
            ], width="auto"),
        ], className="mb-3 g-2 align-items-center"),
        html.Div(id='table-transactions', style={'marginTop': '10px'})
    ])

def register_callbacks(app, account_service, transaction_service, tag_service):
    """
    Registra toda la lógica de interacción de la vista de registro diario.
    Incluye gestión del formulario, autodetección de modo edición, creación dinámica de tags y guardado.
    
    Args:
        app (Dash): Instancia de la aplicación.
        account_service: Servicio de cuentas.
        transaction_service: Servicio de transacciones.
        tag_service: Servicio de etiquetas.
    """
    
    # --- 1. GESTIÓN DE ESTADO DEL FORMULARIO (VISIBILIDAD / MODO / CARGA DATOS) ---
    @app.callback(
        Output('transaction-form-container', 'style'),
        Output('current-tx-mode', 'data'),
        Output('editing-tx-id', 'data'),
        Output('form-title', 'children'),
        Output('form-title', 'style'),
        Output('label-source', 'children'),
        Output('label-dest', 'children'),
        Output('tx-source', 'options'), 
        Output('tx-dest', 'options'),
        Output('tx-desc', 'value'),
        Output('tx-amount', 'value'),
        Output('tx-source', 'value'),
        Output('tx-dest', 'value'),
        Output('tx-date', 'date'),
        Output('tx-tags', 'options'),
        Output('tx-tags', 'value'),
        
        Input('btn-mode-expense', 'n_clicks'),
        Input('btn-mode-income', 'n_clicks'),
        Input('btn-mode-transfer', 'n_clicks'),
        Input('btn-close-form', 'n_clicks'),
        Input({'type': 'btn-edit-tx', 'index': ALL}, 'n_clicks'), # Pattern matching para botones de editar en lista
        Input('url', 'search'), # Escucha Query Params en la URL para editar desde otras vistas
        
        State('transaction-form-container', 'style'),
        prevent_initial_call=True
    )
    def manage_form(n_exp, n_inc, n_trans, n_close, n_edits, url_search, current_style):
        """
        Controlador maestro del formulario. Decide si mostrar u ocultar y el contenido de los dropdowns
        basado en si el usuario quiere registrar un Gasto, Ingreso o Transferencia, o si está editando.
        """
        triggered = ctx.triggered_id
        
        # Estilos predefinidos para visibilidad
        hidden = {'display': 'none'}
        visible = {'display': 'block', 'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 'border': '1px solid #ddd'}

        # Helper para reiniciar el formulario a estado "cerrado/limpio"
        def clean_return():
            return hidden, 'EXPENSE', None, "", {}, "", "", [], [], "", 0, None, None, datetime.now().date(), [], []
        
        # --- Lógica de Disparadores ---
        
        # Si no hay trigger explícito pero hay parámetros en la URL (ej. carga inicial con ?edit_id=...)
        if not triggered:
            if url_search and 'edit_id=' in url_search:
                import urllib.parse
                base_query = urllib.parse.parse_qs(url_search.lstrip('?'))
                if 'edit_id' in base_query:
                    edit_id_from_url = base_query['edit_id'][0]
                    # Simulamos trigger de edición
                    triggered = {'type': 'btn-edit-tx', 'index': edit_id_from_url}
            else:
                 return clean_return()

        # Botón de cierre
        if triggered == 'btn-close-form':
            return clean_return()

        # Validación de triggers complejos (Dash a veces dispara callbacks sin valor en componentes dinámicos)
        if triggered != 'url' and not isinstance(triggered, dict) and not isinstance(triggered, str):
             pass
        elif triggered == 'url':
             pass
        elif isinstance(triggered, dict):
            # Verificar si el clic fue real
            trigger_value = ctx.triggered[0]['value'] if ctx.triggered else None
            if not trigger_value and ctx.triggered_id != 'url': 
                return tuple([no_update] * 16)

        # --- Preparación de Datos ---
        all_accounts = account_service.list_accounts()
        # Clasificar cuentas según su naturaleza contable para filtrar los dropdowns adecuadamente
        assets = [{'label': a.name, 'value': str(a.id)} for a in all_accounts if a.type in [AccountType.ASSET, AccountType.LIABILITY]]
        expenses = [{'label': a.name, 'value': str(a.id)} for a in all_accounts if a.type == AccountType.EXPENSE]
        incomes = [{'label': a.name, 'value': str(a.id)} for a in all_accounts if a.type == AccountType.INCOME]
        
        all_tags = tag_service.list_tags()
        tag_options = [{'label': t.name, 'value': str(t.id)} for t in all_tags]

        # --- MODO EDICIÓN (Desde lista o URL) ---
        is_edit_click = isinstance(triggered, dict) and triggered.get('type') == 'btn-edit-tx'
        is_url_edit = (ctx.triggered_id == 'url') and url_search and 'edit_id' in url_search

        if is_edit_click or is_url_edit:
            # Resolver ID de la transacción a editar
            if is_edit_click:
                tx_id = triggered['index']
            else:
                 import urllib.parse
                 base_query = urllib.parse.parse_qs(url_search.lstrip('?'))
                 tx_id = base_query['edit_id'][0]
            
            # Buscar transacción en servicio
            all_txs = transaction_service.list_transactions_flat()
            tx = next((t for t in all_txs if str(t.id) == str(tx_id)), None)
            
            if not tx: return clean_return()
            
            # Inferir el MODO (Gasto/Ingreso/Transf) analizando las cuentas origen/destino
            s_acc = next((a for a in all_accounts if str(a.id) == str(tx.source_account_id)), None)
            d_acc = next((a for a in all_accounts if str(a.id) == str(tx.destination_account_id)), None)
            
            mode = 'EXPENSE' # Default
            if s_acc and s_acc.type == AccountType.INCOME: mode = 'INCOME'
            elif s_acc and s_acc.type in [AccountType.ASSET, AccountType.LIABILITY] and d_acc and d_acc.type in [AccountType.ASSET, AccountType.LIABILITY]: mode = 'TRANSFER'
            
            # Configurar UI según modo detectado
            title = "✏️ Editar Transacción"
            title_style = {'color': '#f39c12'}
            l_src, l_dest = "Cuenta Origen", "Cuenta Destino"
            opt_src, opt_dest = [], []
            
            # Replicar lógica de listas de cuentas (igual que en creación)
            if mode == 'EXPENSE':
                l_src, l_dest = "Pagas con...", "Categoría..."
                opt_src, opt_dest = assets, expenses
            elif mode == 'INCOME':
                l_src, l_dest = "Ingreso de...", "Depositar en..."
                opt_src, opt_dest = incomes, assets
            else: # Transfer
                l_src, l_dest = "Desde...", "Hacia..."
                opt_src, opt_dest = assets, assets
                
            # Resolver IDs de Tags para pre-rellenar
            current_tag_ids = []
            if tx.tags:
                current_tag_ids = [str(tag.id) for tag in all_tags if tag.name in tx.tags]

            return visible, mode, str(tx.id), title, title_style, l_src, l_dest, opt_src, opt_dest, \
                   tx.description, tx.amount.amount, str(tx.source_account_id), str(tx.destination_account_id), tx.date.date(), tag_options, current_tag_ids

        # --- MODO CREACIÓN (Botones Superiores) ---
        mode = 'EXPENSE'
        title = "📉 Nuevo Gasto"
        title_style = {'color': '#e74c3c'}
        l_src, l_dest = "Origen", "Destino"
        opt_src, opt_dest = [], []
        
        # Check URL param for new action shortcut
        if ctx.triggered_id == 'url' and url_search and 'action=new' in url_search:
             triggered = 'btn-mode-expense'

        if triggered == 'btn-mode-expense':
            mode = 'EXPENSE'
            title = "📉 Nuevo Gasto"
            title_style = {'color': '#e74c3c'}
            l_src, l_dest = "Cuenta Origen (Pagas con...)", "Categoría de Gasto (Compraste...)"
            opt_src, opt_dest = assets, expenses
        elif triggered == 'btn-mode-income':
            mode = 'INCOME'
            title = "📈 Nuevo Ingreso"
            title_style = {'color': '#27ae60'}
            l_src, l_dest = "Fuente de Ingreso (Viene de...)", "Cuenta Destino (Depositar en...)"
            opt_src, opt_dest = incomes, assets
        elif triggered == 'btn-mode-transfer':
            mode = 'TRANSFER'
            title = "↔️ Registrar Transferencia"
            title_style = {'color': '#3498db'}
            l_src, l_dest = "Desde Cuenta...", "Hacia Cuenta..."
            opt_src, opt_dest = assets, assets
        
        return visible, mode, None, title, title_style, l_src, l_dest, opt_src, opt_dest, "", 0, None, None, datetime.now().date(), tag_options, []

    # --- 2. LÓGICA DE CREACIÓN INSTANTÁNEA DE TAGS ---
    @app.callback(
        Output('tx-tags', 'options', allow_duplicate=True),
        Input('tx-tags', 'search_value'),
        State('tx-tags', 'options'),
        State('tx-tags', 'value'),
        prevent_initial_call=True
    )
    def update_tag_options(search_value, current_options, current_values):
        """
        Permite añadir una opción 'Crear...' al dropdown de tags cuando el usuario
        escribe un texto que no coincide con ninguna etiqueta existente.
        """
        current_values = current_values or []
        
        # Limpiar opciones temporales previas ("NEW:...")
        clean_options = [
            opt for opt in current_options 
            if not str(opt['value']).startswith("NEW:") or opt['value'] in current_values
        ]

        if not search_value:
            return clean_options
        
        # Validar duplicados (case insensitive)
        if any(opt['label'].lower() == search_value.lower() for opt in clean_options):
            return clean_options
        
        # Ofrecer opción de creación
        new_option = {'label': f"➕ Crear: {search_value}", 'value': f"NEW:{search_value}"}
        
        return clean_options + [new_option]


    # --- 3. GUARDADO DE TRANSACCIÓN (CREATE / UPDATE) ---
    @app.callback(
        Output('msg-tx-result', 'children'),
        Output('tx-tags', 'options', allow_duplicate=True),
        Output('tx-tags', 'value', allow_duplicate=True),
        Input('btn-submit-tx', 'n_clicks'),
        State('current-tx-mode', 'data'),
        State('editing-tx-id', 'data'), # ¿Estamos editando?
        State('tx-desc', 'value'),
        State('tx-amount', 'value'),
        State('tx-source', 'value'),
        State('tx-dest', 'value'),
        State('tx-date', 'date'),
        State('tx-tags', 'value'),
        prevent_initial_call=True
    )
    def submit_transaction(n_clicks, mode, edit_id, desc, amount, source_id, dest_id, date_str, tags_values):
        """
        Procesa el formulario, crea tags si es necesario y envía el DTO al servicio 
        para crear o actualizar la transacción.
        """
        if not all([amount, source_id, dest_id]):
             return html.Span("❌ Faltan datos obligatorios (Monto, Origen o Destino)", style={'color': 'red'}), no_update, no_update
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
            
            # Procesar Tags: Separar UUIDs existentes de solicitudes de creación "NEW:..."
            final_tag_ids = []
            new_tags_created = False
            
            if tags_values:
                for val in tags_values:
                    if str(val).startswith("NEW:"):
                        # Crear Tag on-the-fly
                        tag_name = val.split("NEW:")[1]
                        new_tag_dto = tag_service.create_tag(TagDTO(name=tag_name))
                        final_tag_ids.append(str(new_tag_dto.id))
                        new_tags_created = True
                    else:
                        # Es un ID existente
                        final_tag_ids.append(str(val))

            # Construcción del DTO
            dto = TransactionEntryDTO(
                description=desc if desc else "",
                amount=MoneySchema(amount=Decimal(str(amount)), currency="EUR"),
                source_account_id=source_id,
                destination_account_id=dest_id,
                date=date_obj,
                tags_ids=final_tag_ids
            )
            
            # Si se crearon tags, necesitamos refrescar las opciones para los siguientes usos
            updated_options = no_update
            updated_values = no_update
            
            if new_tags_created:
                all_tags = tag_service.list_tags()
                updated_options = [{'label': t.name, 'value': str(t.id)} for t in all_tags]
                updated_values = final_tag_ids
            
            if edit_id:
                # Actualizar
                transaction_service.update_transaction(edit_id, dto)
                return html.Span("✅ Transacción ACTUALIZADA con éxito", style={'color': 'blue', 'fontWeight': 'bold'}), updated_options, updated_values
            else:
                # Crear
                transaction_service.create_transaction(dto)
                return html.Span("✅ Transacción CREADA con éxito", style={'color': 'green', 'fontWeight': 'bold'}), updated_options, updated_values
                
        except Exception as e:
            return html.Span(f"❌ Error: {str(e)}", style={'color': 'red'}), no_update, no_update

    # --- 4. LISTADO DE HISTORIAL ---
    @app.callback(
        Output('table-transactions', 'children'),
        Input('btn-refresh-tx', 'n_clicks'),
        Input('msg-tx-result', 'children'), # Refrescar también al guardar éxito
    )
    def update_tx_list(n1, n2):
        """
        Actualiza la tabla visual de transacciones recientes.
        Modificado para un diseño más compacto (ListGroup) con botón de edición.
        """
        txs = transaction_service.list_transactions_flat()
        if not txs: return html.Div("No hay movimientos recientes.", className="text-muted text-center mt-3")
        
        list_items = []
        # Mostrar solo las últimas 15 para mantenerlo ágil
        for tx in sorted(txs, key=lambda x: x.date, reverse=True)[:15]:
            
            # Formateo de TAGS como badges
            tags_badges = [dbc.Badge(t, color="info", className="me-1", style={'fontSize': '0.7em'}) for t in tx.tags]
            
            # Contenido de la fila
            item_content = dbc.Row([
                # Columna 1: Fecha (Día/Mes)
                dbc.Col([
                    html.Div(tx.date.strftime('%d'), className="fw-bold", style={'fontSize': '1.1em', 'lineHeight': '1'}),
                    html.Small(tx.date.strftime('%b'), className="text-muted text-uppercase", style={'fontSize': '0.65em', 'letterSpacing': '0.5px'})
                ], width=1, className="d-flex flex-column align-items-center justify-content-center border-end px-1"),
                
                # Columna 2: Detalles (Cuentas + Descripción + Tags)
                dbc.Col([
                    html.Div([
                        html.Span(tx.source_account_name, className="fw-bold text-dark"),
                        html.Span(" → ", className="text-muted mx-1"),
                        html.Span(tx.destination_account_name, className="fw-bold text-dark"),
                    ], style={'fontSize': '0.9em', 'marginBottom': '2px'}),
                    
                    html.Div([
                        html.Small(tx.description if tx.description else "Sin descripción", className="text-secondary fst-italic me-2"),
                        *tags_badges
                    ], style={'fontSize': '0.8em'})
                ], width=7, className="ps-2 d-flex flex-column justify-content-center"),
                
                # Columna 3: Monto y Acción
                dbc.Col([
                    html.Div(f"{tx.amount.amount:,.2f} €", className="fw-bold me-3", style={'fontSize': '1.1em', 'color': '#2c3e50'}),
                    dbc.Button(
                        html.I(className="bi bi-pencil"), 
                        id={'type': 'btn-edit-tx', 'index': str(tx.id)},
                        color="secondary",
                        outline=True,
                        size="sm"
                    ),
                    dbc.Tooltip("Editar transacción", target={'type': 'btn-edit-tx', 'index': str(tx.id)}, placement="top"),
                ], width=4, className="d-flex align-items-center justify-content-end pe-3")
            ], className="g-0 align-items-center")
            
            list_items.append(dbc.ListGroupItem(item_content, className="py-1 action-item", style={'borderLeft': 'none', 'borderRight': 'none'}))

        return dbc.ListGroup(list_items, flush=True, className="shadow-sm rounded")
