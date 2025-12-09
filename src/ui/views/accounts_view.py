from dash import html, dcc, Input, Output, State, dash_table
import pandas as pd
from decimal import Decimal
from src.application.services.account_service import AccountService
from src.application.dtos import AccountCreateDTO, MoneySchema, AccountUpdateDTO
from src.domain.models import AccountType
from src.domain import AccountAlreadyExistsError

def get_layout():
    return html.Div([
        html.H2("Gestión de Cuentas"),
        
        # --- Formulario de Creación ---
        html.Div([
            html.H3("Nueva Cuenta"),
            dcc.Input(id='acc-name', type='text', placeholder='Nombre de la cuenta', style={'marginRight': '10px'}),
            dcc.Dropdown(
                id='acc-type',
                options=[{'label': t.value, 'value': t.name} for t in AccountType],
                placeholder="Selecciona Tipo",
                style={'width': '200px', 'display': 'inline-block', 'marginRight': '10px'}
            ),
            dcc.Input(id='acc-balance', type='number', placeholder='Saldo Inicial', value=0, step=0.01),
            html.Button('Crear Cuenta', id='btn-create-acc', n_clicks=0, style={'marginLeft': '10px'}),
            html.Div(id='msg-create-acc', style={'marginTop': '10px'})
        ], style={'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'marginBottom': '20px'}),

        # --- Listado de Cuentas ---
        html.Div([
            html.H3("Listado de Cuentas"),
            html.Button('🔄 Actualizar', id='btn-refresh-acc', n_clicks=0, style={'marginBottom': '10px'}),
            html.Div(id='table-accounts'),
            
            # --- Sección de Gestión (Unificada) ---
            html.Hr(style={'marginTop': '30px', 'marginBottom': '30px'}),
            
            html.Div([
                html.H3("⚙️ Gestionar Cuenta Existente", style={'marginTop': '0'}),
                
                # Selector Global
                html.Div([
                    html.Label("1. Selecciona la cuenta a gestionar:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='action-acc-selector',
                        placeholder="Busca por nombre...",
                        style={'width': '100%'}
                    ),
                ], style={'marginBottom': '20px'}),

                # Contenedor de Acciones (Flex)
                html.Div([
                    # Columna Izquierda: Modificar
                    html.Div([
                        html.H4("📝 Modificar Datos", style={'marginTop': '0', 'color': '#2c3e50'}),
                        html.Div([
                            html.Label("Nuevo Nombre:"),
                            dcc.Input(id='edit-acc-name', type='text', placeholder='Dejar vacío para mantener', style={'width': '100%', 'marginBottom': '10px'}),
                            
                            html.Label("Nuevo Tipo:"),
                            dcc.Dropdown(
                                id='edit-acc-type',
                                options=[{'label': t.value, 'value': t.name} for t in AccountType],
                                placeholder="Dejar vacío para mantener",
                                style={'marginBottom': '10px'}
                            ),
                            
                            html.Label("Estado:"),
                            dcc.Dropdown(
                                id='edit-acc-active',
                                options=[{'label': 'Activa', 'value': True}, {'label': 'Inactiva', 'value': False}],
                                placeholder="Dejar vacío para mantener",
                                style={'marginBottom': '15px'}
                            ),
                            
                            html.Button('💾 Guardar Cambios', id='btn-update-acc', n_clicks=0, style={'width': '100%', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'padding': '10px', 'cursor': 'pointer'}),
                        ])
                    ], style={'flex': '1', 'padding': '15px', 'backgroundColor': 'white', 'borderRadius': '5px', 'border': '1px solid #eee'}),

                    # Columna Derecha: Eliminar
                    html.Div([
                        html.H4("⚠️ Zona de Peligro", style={'marginTop': '0', 'color': '#c0392b'}),
                        html.P("Si eliminas la cuenta, esta acción no se puede deshacer. Solo se permite si no tiene transacciones.", style={'fontSize': '0.9em', 'color': '#7f8c8d'}),
                        html.Button('🗑️ Eliminar Cuenta', id='btn-delete-acc', n_clicks=0, style={'width': '100%', 'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 'padding': '10px', 'cursor': 'pointer', 'marginTop': '20px'}),
                    ], style={'flex': '1', 'padding': '15px', 'backgroundColor': '#fff5f5', 'borderRadius': '5px', 'border': '1px solid #ffcccc', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between'}),

                ], style={'display': 'flex', 'gap': '20px'}),

                html.Div(id='msg-action-acc', style={'marginTop': '20px', 'textAlign': 'center', 'fontWeight': 'bold'})

            ], style={'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'backgroundColor': '#f8f9fa'})
        ])
    ])

def register_callbacks(app, account_service: AccountService):
    @app.callback(
        Output('msg-create-acc', 'children'),
        Output('msg-create-acc', 'style'),
        Input('btn-create-acc', 'n_clicks'),
        State('acc-name', 'value'),
        State('acc-type', 'value'),
        State('acc-balance', 'value'),
        prevent_initial_call=True
    )

    def create_account(n_clicks, name, type_str, balance):
        if not name:
            return "❌ El nombre es obligatorio.", {'color': 'red'}
        
        try:
            acc_type = AccountType[type_str]
            dto = AccountCreateDTO(
                name = name,
                type = acc_type,
                initial_balance = MoneySchema(amount=Decimal(str(balance)), currency="EUR")
            )
            account_service.create_account(dto)
            return f"✅ Cuenta '{name}' creada con éxito.", {'color': 'green'}
        except AccountAlreadyExistsError as e:
            return f"⚠️ {str(e)}", {'color': 'orange'}
        except Exception as e:
            return f"❌ Error: {str(e)}", {'color': 'red'}
        
    #Listar Cuentas
    @app.callback(
        Output('table-accounts', 'children'),
        Output('action-acc-selector', 'options'),
        Input('btn-refresh-acc', 'n_clicks'),
        Input('btn-create-acc', 'n_clicks'),
    )
    def list_accounts(n_refresh, n_create):
        accounts = account_service.list_accounts()
        if not accounts:
            return "No hay cuentas registradas.", []

        # Obtenemos el saldo real para cada cuenta
        data = []
        options = []
        for acc in accounts:
            real_balance = account_service.get_account_balance(acc.id)
            data.append({
                "ID": str(acc.id),
                "Nombre": acc.name,
                "Tipo": acc.type.name,
                "Saldo Actual": f"{real_balance.amount} {real_balance.currency}",
                "Estado": "Activa" if acc.is_active else "Inactiva"
            })
            # Llenamos las opciones del dropdown
            options.append({
                'label': f"{acc.name} ({acc.type.name})",
                'value': str(acc.id)
            })
        
        df = pd.DataFrame(data)
        
        # Usamos dash_table.DataTable para una tabla interactiva y copiable
        table = dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'sans-serif'
            },
            style_header={
                'backgroundColor': '#2c3e50',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            page_size=10,  # Paginación
            filter_action="native", # Permite filtrar columnas
            sort_action="native",   # Permite ordenar columnas
            # row_selectable="single", # Desactivamos selección de fila completa para permitir selección de texto
            cell_selectable=True,    # Permite seleccionar celdas individuales (para copiar)
            editable=False           # No editable directamente en tabla (usaremos formulario)
        )

        return table, options
    
    # Delete & Update Account Callback (Unified Output)
    @app.callback(
        Output('msg-action-acc', 'children'),
        Input('btn-delete-acc', 'n_clicks'),
        Input('btn-update-acc', 'n_clicks'),
        State('action-acc-selector', 'value'),
        State('edit-acc-name', 'value'),
        State('edit-acc-type', 'value'),
        State('edit-acc-active', 'value'),
        prevent_initial_call=True
    )
    def handle_account_actions(n_delete, n_update, account_id_str, new_name, new_type_str, new_active):
        from dash import ctx
        
        if not account_id_str:
            return html.Span("❌ Debes seleccionar una cuenta.", style={'color': 'red'})
        
        try:
            from uuid import UUID
            acc_uuid = UUID(account_id_str)
            button_id = ctx.triggered_id

            if button_id == 'btn-delete-acc':
                account_service.delete_account(acc_uuid)
                return html.Span(f"✅ Cuenta eliminada correctamente.", style={'color': 'green'})
            
            elif button_id == 'btn-update-acc':
                # Construir DTO solo con campos que tengan valor
                acc_type = AccountType[new_type_str] if new_type_str else None
                
                dto = AccountUpdateDTO(
                    name=new_name if new_name else None,
                    type=acc_type,
                    is_active=new_active
                )
                
                # Si todos son None, no hacemos nada
                if dto.name is None and dto.type is None and dto.is_active is None:
                     return html.Span("⚠️ No has introducido ningún cambio.", style={'color': 'orange'})

                account_service.update_account(acc_uuid, dto)
                return html.Span(f"✅ Cuenta actualizada correctamente.", style={'color': 'green'})

        except ValueError as e:
            return html.Span(f"⚠️ {str(e)}", style={'color': 'orange'})
        except Exception as e:
            return html.Span(f"❌ Error inesperado: {str(e)}", style={'color': 'red'})

