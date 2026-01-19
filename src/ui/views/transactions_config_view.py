from dash import html, dash_table, Input, Output, State, no_update, dcc, ALL, ctx
import dash_bootstrap_components as dbc
from datetime import datetime
from decimal import Decimal
import uuid
import json

from src.application.services.transaction_service import TransactionService
from src.application.services.account_service import AccountService
from src.application.services.tag_service import TagService
from src.application.dtos import TransactionEntryDTO, MoneySchema, TagDTO

def layout_transactions_config():
    """
    Genera y devuelve el diseño (layout) de la interfaz de usuario para la sección de 'Configuración de Movimientos'.
    
    Esta vista es la herramienta de administración avanzada para las transacciones. A diferencia de la vista diaria,
    aquí se presenta un enfoque tabular completo, ideal para revisiones masivas, eliminaciones múltiples y ediciones
    detalladas de cualquier movimiento histórico.
    
    Componentes principales:
    - Barra de herramientas: Botones para Añadir, Editar, Eliminar y Actualizar.
    - Tabla de Datos (dash_table.DataTable):
        - Listado paginado de transacciones.
        - Selección múltiple habilitada para borrar en lote.
    - Modales:
        - Modal de Confirmación de Borrado: Seguridad antes de acciones destructivas.
        - Modal de Edición/Creación: Formulario completo para gestionar los detalles de la transacción.
          Incluye soporte para creación dinámica de tags.
    
    Returns:
        html.Div: Contenedor principal con todos los componentes de la vista.
    """
    return html.Div([
        # Store auxiliar para señales de refresco entre componentes
        dcc.Store(id='store-refresh-trigger-tx', data=0), 
        
        # Título y encabezado
        html.H2("📋 Gestión de Movimientos", style={'color': '#34495e'}),
        html.P("Consulta, edita y gestiona todo el historial de transacciones.", style={'color': '#7f8c8d'}),
        html.Hr(),
        
        # Barra de Botones (Toolbar)
        dbc.Row([
            dbc.Col(dbc.Button("➕ Añadir Movimiento", color="primary", id='btn-add-tx-config', n_clicks=0), width="auto"),
            dbc.Col(dbc.Button("✏️ Editar", id='btn-edit-tx-config', color="warning", disabled=True, n_clicks=0), width="auto"),
            dbc.Col(dbc.Button("🗑️ Eliminar Seleccionados", id='btn-delete-tx-config', color="danger", disabled=True, n_clicks=0), width="auto"),
            dbc.Col(dbc.Button("🔄 Actualizar", id='btn-refresh-tx-config', color="secondary", n_clicks=0), width="auto"),
        ], className="mb-3 g-2"),

        # Tabla Principal de Datos
        dash_table.DataTable(
            id='table-transactions-config',
            columns=[
                {"name": "Fecha", "id": "date"},
                {"name": "Descripción", "id": "description"},
                {"name": "Monto", "id": "amount"},
                {"name": "Origen", "id": "source"},
                {"name": "Destino", "id": "destination"},
                {"name": "Tags", "id": "tags"},
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
        
        # Modal de Confirmación de Borrado
        dbc.Modal([
            dbc.ModalHeader("Confirmar Eliminación"),
            dbc.ModalBody("¿Estás seguro de que quieres eliminar las transacciones seleccionadas? Esta acción no se puede deshacer."),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancel-delete", className="ms-auto", n_clicks=0),
                dbc.Button("Eliminar", id="btn-confirm-delete", color="danger", n_clicks=0),
            ])
        ], id="modal-delete-tx", is_open=False),
        
        # Modal de Formulario (Crear / Editar)
        dbc.Modal([
            dbc.ModalHeader(html.H4(id='modal-tx-title', children="Transacción")),
            dbc.ModalBody([
                 dcc.Store(id='config-editing-tx-id', data=None), # ID oculto si estamos editando
                 
                 # 1. Fila: Cuentas
                html.Div([
                    html.Div([
                        html.Label("Cuenta Origen", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(id='config-tx-source', placeholder="Selecciona...", style={'width': '100%'}),
                    ], style={'flex': '1'}),
                    
                    html.Div([
                        html.Label("Cuenta Destino", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(id='config-tx-dest', placeholder="Selecciona...", style={'width': '100%'}),
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}),

                # 2. Fila: Datos monetarios y fecha
                html.Div([
                     html.Div([
                        html.Label("Monto (€)", style={'fontWeight': 'bold'}),
                        dbc.Input(id='config-tx-amount', type='number', value=0, step=0.01, style={'width': '100%', 'padding': '8px'}),
                    ], style={'flex': '1'}),

                     html.Div([
                        html.Label("Fecha:", style={'fontWeight': 'bold', 'display': 'block'}),
                        dcc.DatePickerSingle(
                            id='config-tx-date',
                            min_date_allowed=datetime(2020, 1, 1),
                            max_date_allowed=datetime(2030, 12, 31),
                            initial_visible_month=datetime.now(),
                            date=datetime.now().date(),
                            style={'width':'100%', 'border': '1px solid #ced4da', 'borderRadius': '4px'}
                        ),
                    ], style={'flex': '1'}),
                    
                    html.Div([
                        html.Label("Etiquetas:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(id='config-tx-tags', multi=True, placeholder="Añadir tags...", style={'width': '100%'}),
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '15px', 'marginBottom': '15px'}),
                
                # 3. Fila: Descripción
                html.Div([
                    html.Label("Descripción (Opcional)", style={'fontWeight': 'bold'}),
                    dbc.Input(id='config-tx-desc', type='text', placeholder='¿Qué es?', style={'width': '100%', 'padding': '8px'}),
                ], style={'marginBottom': '15px'}),
                
                # Mensaje de error/estado dentro del modal
                html.Div(id='msg-tx-modal-result', style={'marginTop': '10px', 'textAlign': 'center', 'color': 'red'})
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="btn-cancel-modal-tx", className="ms-auto", n_clicks=0),
                dbc.Button("💾 Guardar", id="btn-save-modal-tx", color="success", n_clicks=0),
            ])
        ], id="modal-tx-config", is_open=False, size="lg"),

        # Div auxiliar (invisible) para outputs de callbacks que no requieren feedback visual directo
        html.Div(id='msg-tx-config-result', style={'display': 'none'})
    ])

def register_callbacks(app, transaction_service: TransactionService, account_service: AccountService, tag_service: TagService):
    """
    Registra los callbacks (lógica) para la vista de Configuración de Transacciones.
    
    Args:
        app (Dash): Instancia de la aplicación.
        transaction_service (TransactionService): Lógica de negocio de transacciones.
        account_service (AccountService): Lógica de negocio de cuentas (para dropdowns).
        tag_service (TagService): Lógica de negocio de etiquetas.
    """
    
    # 1. ACTUALIZAR TABLA (Carga de datos)
    @app.callback(
        Output('table-transactions-config', 'data'),
        Input('btn-refresh-tx-config', 'n_clicks'),
        Input('url', 'pathname'),
        Input('btn-confirm-delete', 'n_clicks'), # Refrescar tras borrar
        Input('store-refresh-trigger-tx', 'data'), # Refrescar tras guardar edición/creación
        State('table-transactions-config', 'data')
    )
    def update_table(n_refresh, pathname, n_delete, n_signal, current_data):
        """
        Carga la lista de transacciones en la tabla.
        Incluye datos ocultos (raw_...) para facilitar la edición posterior sin re-consultar al backend.
        """
        if pathname != '/config/transactions':
             return no_update
             
        txs = transaction_service.list_transactions()
        
        data = []
        for t in txs:
            data.append({
                # Datos visibles
                "id": str(t.id),
                "date": t.date.strftime("%Y-%m-%d"),
                "description": t.description,
                "amount": f"{t.amount.amount} {t.amount.currency}",
                "source": t.source_account_name,
                "destination": t.destination_account_name,
                "tags": ", ".join(t.tags) if t.tags else "", 
                
                # Datos ocultos (RAW) para rellenar el formulario de edición
                "raw_amount": float(t.amount.amount),
                "raw_source_id": str(t.source_account_id) if t.source_account_id else None,
                "raw_dest_id": str(t.destination_account_id) if t.destination_account_id else None,
                "raw_tags_ids": json.dumps([str(tid) for tid in t.tags_ids]) # Serializado para evitar errores de Dash
            })
        
        # Ordenar por fecha descendente
        data.sort(key=lambda x: x['date'], reverse=True)
        return data

    # 2. GESTIÓN BOTONES TOOLBAR
    @app.callback(
        Output('btn-delete-tx-config', 'disabled'),
        Output('btn-edit-tx-config', 'disabled'),
        Input('table-transactions-config', 'selected_rows'),
        State('table-transactions-config', 'data')
    )
    def toggle_buttons(selected_rows, data):
        """
        Habilita/Deshabilita botones según la selección de filas.
        - Eliminar: Habilitado si hay al menos 1 selección.
        - Editar: Habilitado SOLO si hay exactamente 1 selección.
        """
        disabled_delete = not bool(selected_rows)
        disabled_edit = True
        
        if selected_rows and len(selected_rows) == 1:
            disabled_edit = False
            
        return disabled_delete, disabled_edit

    # 3. MODAL DE BORRADO (Abrir/Cerrar)
    @app.callback(
        Output("modal-delete-tx", "is_open"),
        Input("btn-delete-tx-config", "n_clicks"),
        Input("btn-cancel-delete", "n_clicks"),
        Input("btn-confirm-delete", "n_clicks"),
        State("modal-delete-tx", "is_open"),
    )
    def toggle_delete_modal(n1, n2, n3, is_open):
        """Controla la visibilidad del modal de confirmación de borrado."""
        if n1 or n2 or n3:
            return not is_open
        return is_open

    # 4. EJECUTAR BORRADO
    @app.callback(
        Output('msg-tx-config-result', 'children'),
        Input('btn-confirm-delete', 'n_clicks'),
        State('table-transactions-config', 'selected_rows'),
        State('table-transactions-config', 'data'),
        prevent_initial_call=True
    )
    def delete_transactions(n_clicks, selected_indices, all_data):
        """
        Elimina las transacciones seleccionadas una a una llamando al servicio.
        """
        if not selected_indices or not all_data:
            return no_update
        
        ids_to_delete = []
        for index in selected_indices:
             if index < len(all_data):
                 ids_to_delete.append(all_data[index]['id'])
        
        count = 0
        for tx_id in ids_to_delete:
            try:
                transaction_service.delete_transaction(tx_id) 
                count += 1
            except Exception:
                pass
        
        return f"Eliminados {count} registros"

    # 5. CARGAR OPCIONES DEL FORMULARIO
    @app.callback(
        Output('config-tx-source', 'options'),
        Output('config-tx-dest', 'options'),
        Output('config-tx-tags', 'options'),
        Input('btn-add-tx-config', 'n_clicks'),
        Input('btn-edit-tx-config', 'n_clicks'),
    )
    def populate_options(n1, n2):
        """
        Recarga las opciones de los desplegables (Cuentas y Tags) cada vez que se abre el modal,
        asegurando que se muestran los datos más recientes.
        """
        accounts = account_service.list_accounts()
        tags = tag_service.list_tags()
        
        acc_options = [{'label': a.name, 'value': str(a.id)} for a in accounts]
        tag_options = [{'label': t.name, 'value': str(t.id)} for t in tags]
        
        return acc_options, acc_options, tag_options

    # 6. MODAL DE EDICIÓN/CREACIÓN (Abrir y Rellenar)
    @app.callback(
        Output("modal-tx-config", "is_open"),
        Output("modal-tx-title", "children"),
        Output("config-editing-tx-id", "data"),
        
        Output("config-tx-source", "value"),
        Output("config-tx-dest", "value"),
        Output("config-tx-amount", "value"),
        Output("config-tx-date", "date"),
        Output("config-tx-tags", "value"),
        Output("config-tx-desc", "value"),
        
        Input("btn-add-tx-config", "n_clicks"),
        Input("btn-edit-tx-config", "n_clicks"),
        Input("btn-cancel-modal-tx", "n_clicks"),
        Input("store-refresh-trigger-tx", "data"), # Señal de cierre por éxito
        
        State("table-transactions-config", "selected_rows"),
        State("table-transactions-config", "data"),
        State("modal-tx-config", "is_open")
    )
    def toggle_edit_modal(n_add, n_edit, n_cancel, n_signal, selected_rows, data, is_open):
        """
        Gestiona la apertura el modal de edición/creación.
        Si es Editar: Rellena los campos con los datos RAW de la fila seleccionada.
        Si es Añadir: Limpia los campos.
        """
        triggered_id = ctx.triggered_id
        
        if not triggered_id:
            return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        # Cerrar el modal
        if triggered_id == 'btn-cancel-modal-tx' or triggered_id == 'store-refresh-trigger-tx':
            return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        # Abrir para "Añadir"
        if triggered_id == 'btn-add-tx-config':
            return True, "Nueva Transacción", None, None, None, 0, datetime.now().date(), [], ""

        # Abrir para "Editar"
        if triggered_id == 'btn-edit-tx-config':
            if not selected_rows or len(selected_rows) != 1:
                return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
            
            idx = selected_rows[0]
            row = data[idx]
            
            # Extraer datos RAW
            tx_id = row['id']
            amount = row.get('raw_amount', 0)
            date_str = row['date']
            desc = row['description']
            source_id = row.get('raw_source_id')
            dest_id = row.get('raw_dest_id')
            tags_json = row.get('raw_tags_ids', '[]')
            try:
                tags_ids = json.loads(tags_json)
            except:
                tags_ids = []
            
            return True, "Editar Transacción", tx_id, source_id, dest_id, amount, date_str, tags_ids, desc

        return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    # 7. GUARDAR TRANSACCIÓN (Submit)
    @app.callback(
        Output('msg-tx-modal-result', 'children'),
        Output('store-refresh-trigger-tx', 'data'),
        Input('btn-save-modal-tx', 'n_clicks'),
        State('config-editing-tx-id', 'data'),
        State('config-tx-source', 'value'),
        State('config-tx-dest', 'value'),
        State('config-tx-amount', 'value'),
        State('config-tx-date', 'date'),
        State('config-tx-tags', 'value'),
        State('config-tx-desc', 'value'),
        prevent_initial_call=True
    )
    def save_transaction(n_clicks, tx_id, source, dest, amount, date_str, tags, desc):
        """
        Procesa el guardado del formulario.
        - Gestiona creación de Tags nuevos ("NEW:...").
        - Crea o Actualiza la transacción según corresponda.
        - Devuelve una señal (timestamp) para refrescar la tabla y cerrar el modal.
        """
        if not ctx.triggered_id:
             return no_update, no_update
             
        try:
            if not source or not dest:
                 pass 

            # Parsear fecha
            if not date_str:
                date_obj = datetime.now()
            else:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

            # Gestionar Tags (Crear nuevos si el prefix es NEW:)
            final_tag_ids = []
            if tags:
                for val in tags:
                    if str(val).startswith("NEW:"):
                        tag_name = val.split("NEW:")[1]
                        new_tag_dto = tag_service.create_tag(TagDTO(name=tag_name))
                        final_tag_ids.append(new_tag_dto.id)
                    else:
                        final_tag_ids.append(uuid.UUID(val))

            dto = TransactionEntryDTO(
                description=desc or "",
                amount=MoneySchema(amount=Decimal(str(amount)), currency="EUR"),
                source_account_id=uuid.UUID(source),
                destination_account_id=uuid.UUID(dest),
                date=date_obj,
                tags_ids=final_tag_ids
            )

            if tx_id:
                # Update
                transaction_service.update_transaction(uuid.UUID(tx_id), dto)
            else:
                # Create
                transaction_service.create_transaction(dto)
            
            # Emitir señal de éxito (timestamp actual para asegurar trigger)
            return "", datetime.now().timestamp()

        except Exception as e:
            return f"Error: {str(e)}", no_update

    # 8. TECLAS DINÁMICAS (Creación de Tags)
    @app.callback(
        Output('config-tx-tags', 'options', allow_duplicate=True),
        Input('config-tx-tags', 'search_value'),
        State('config-tx-tags', 'options'),
        State('config-tx-tags', 'value'),
        prevent_initial_call=True
    )
    def update_tag_options(search_value, current_options, current_values):
        """
        Habilita la opción de crear tags al vuelo cuando el texto buscado no existe.
        """
        current_values = current_values or []
        
        # Limpiar opciones temporales
        clean_options = [
            opt for opt in current_options 
            if not str(opt['value']).startswith("NEW:") or opt['value'] in current_values
        ]

        if not search_value:
            return clean_options

        # Chequear existencia
        exists = any(opt['label'].lower() == search_value.lower() for opt in clean_options)
        
        if not exists:
            clean_options.append({
                'label': f'➕ Crear "{search_value}"',
                'value': f'NEW:{search_value}'
            })
            
        return clean_options
