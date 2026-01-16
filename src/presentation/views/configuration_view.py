from dash import html, dcc, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
from src.application.dtos import AccountCreateDTO, MoneySchema
from src.domain.models import AccountType
from src.domain.exceptions import AccountAlreadyExistsError
from decimal import Decimal

def get_layout():
    return html.Div([
        html.H2("⚙️ Configuración de Finanzas (Cuentas y Conceptos)", style={'marginBottom': '20px', 'color': '#2c3e50'}),
        html.P("Administra aquí tus bancos, tarjetas, categorías de gasto y fuentes de ingreso. Al estilo Firefly III.", style={'color': '#7f8c8d'}),
        
        dcc.Tabs(id="config-tabs", value='tab-assets', children=[
            dcc.Tab(label='🏦 Cuentas de Activo (Bancos)', value='tab-assets', style={'fontWeight': 'bold'}),
            dcc.Tab(label='💳 Pasivos (Deudas/Tarjetas)', value='tab-liabilities', style={'fontWeight': 'bold', 'color': '#c0392b'}),
            dcc.Tab(label='🛒 Cuentas de Gasto (Categorías)', value='tab-expenses', style={'fontWeight': 'bold'}),
            dcc.Tab(label='💰 Cuentas de Ingreso (Fuentes)', value='tab-revenue', style={'fontWeight': 'bold', 'color': '#27ae60'}),
        ]),
        
        html.Div(id='config-content', style={'padding': '20px', 'border': '1px solid #d6d6d6', 'borderTop': 'none', 'backgroundColor': 'white'})
    ])

def _get_account_section_layout(account_type: AccountType, title: str, description: str, icon: str):
    """Genera el layout genérico para una sección de configuración de cuentas"""
    type_name = account_type.name  # ASSET, EXPENSE, etc.
    
    return html.Div([
        html.H4(f"{icon} {title}"),
        html.P(description, style={'fontSize': '0.9em', 'color': '#7f8c8d'}),
        
        # Formulario de Creación
        html.Div([
            html.H5("Crear Nuevo"),
            html.Div([
                html.Label("Nombre:"),
                dcc.Input(id={'type': 'new-acc-name', 'index': type_name}, type='text', placeholder=f'Ej: {title} 1...', style={'width': '100%', 'marginBottom': '10px'}),
                
                html.Label("Saldo Inicial (€):") if account_type in [AccountType.ASSET, AccountType.LIABILITY] else html.Div(),
                dcc.Input(id={'type': 'new-acc-balance', 'index': type_name}, type='number', value=0, step=0.01, style={'width': '100%', 'marginBottom': '10px'}) if account_type in [AccountType.ASSET, AccountType.LIABILITY] else html.Div(),
                
                html.Button([f'➕ Crear {title}'], id={'type': 'btn-create-acc', 'index': type_name}, n_clicks=0, style={'width': '100%', 'marginTop': '10px', 'backgroundColor': '#ecf0f1', 'border': '1px solid #bdc3c7'}),
            ], style={'backgroundColor': '#f9f9f9', 'padding': '15px', 'borderRadius': '5px', 'marginBottom': '20px'}),
            html.Div(id={'type': 'msg-create-acc', 'index': type_name})
        ], style={'maxWidth': '400px'}),

        html.Hr(),
        
        # Tabla de Listado
        html.Div([
            html.H5(f"Listado de {title}"),
            html.Button('🔄 Refrescar Lista', id={'type': 'btn-refresh-list', 'index': type_name}, n_clicks=0, style={'marginBottom': '10px'}),
            html.Div(id={'type': 'list-acc-container', 'index': type_name})
        ])
    ])

def register_callbacks(app, account_service):
    
    # 1. Renderizar contenido de las Tabs
    @app.callback(
        Output('config-content', 'children'),
        Input('config-tabs', 'value')
    )
    def render_tab_content(tab_value):
        if tab_value == 'tab-assets':
            return _get_account_section_layout(
                AccountType.ASSET, "Cuentas de Activo", 
                "Tus cuentas bancarias, efectivo, huchas. El dinero que posees.", "🏦"
            )
        elif tab_value == 'tab-liabilities':
            return _get_account_section_layout(
                AccountType.LIABILITY, "Pasivos (Deudas)", 
                "Tarjetas de crédito, préstamos, hipotecas. El dinero que debes.", "💳"
            )
        elif tab_value == 'tab-expenses':
            return _get_account_section_layout(
                AccountType.EXPENSE, "Cuentas de Gasto", 
                "Categorías donde se va tu dinero: Comida, Alquiler, Ocio.", "🛒"
            )
        elif tab_value == 'tab-revenue':
            return _get_account_section_layout(
                AccountType.INCOME, "Cuentas de Ingreso", 
                "Fuentes de donde viene tu dinero: Nómina, Ventas, Dividendos.", "💰"
            )
        return html.Div("Selecciona una pestaña")

    # 2. Manejar creación de Cuentas (Generic Pattern Matching)
    @app.callback(
        Output({'type': 'msg-create-acc', 'index': ALL}, 'children'),
        Output({'type': 'msg-create-acc', 'index': ALL}, 'style'),
        Output({'type': 'new-acc-name', 'index': ALL}, 'value'), # Para limpiar input
        Input({'type': 'btn-create-acc', 'index': ALL}, 'n_clicks'),
        State({'type': 'new-acc-name', 'index': ALL}, 'value'),
        State({'type': 'new-acc-balance', 'index': ALL}, 'value'),
        prevent_initial_call=True
    )
    def create_account(n_clicks_list, names, balances):
        # Dash Pattern Matching: Identificar cuál botón se pulsó
        triggered_id = ctx.triggered_id
        if not triggered_id: 
            return [html.Div()]*len(n_clicks_list), [{}]*len(n_clicks_list), [""]*len(n_clicks_list)

        type_str = triggered_id['index'] # "ASSET", "EXPENSE", etc.
        
        # Encontrar el índice correcto en la lista de inputs (puede haber varios en el DOM fantasma, pero solo uno activo visible usualmente, aunque ALL devuelve todos)
        # Nota: Al usar Tabs, los componentes se destruyen/crean. ALL puede ser tricky.
        # Pero como regeneramos layout, solo debería haber uno en el DOM.
        # Simplificación: Asumimos que la lista tiene 1 elemento porque solo 1 tab se renderiza a la vez
        
        # Workaround para listas de ALL: Encontrar el que coincide con el ID
        # En este caso simple con Tabs dinámicas, ALL devuelve lista de lo que está en pantalla.
        
        if not names or not names[0]:
             return ["❌ Nombre obligatorio"]*len(n_clicks_list), [{'color':'red'}]*len(n_clicks_list), names

        name = names[0]
        balance_val = balances[0] if balances else 0
        
        # Si es Income/Expense, el balance inicial suele ser 0 o irrelevante en creación simple, 
        # pero para consistencia lo dejamos.
        
        try:
            acc_type = AccountType[type_str]
            dto = AccountCreateDTO(
                name=name,
                type=acc_type,
                initial_balance=MoneySchema(amount=Decimal(str(balance_val if balance_val else 0)), currency="EUR")
            )
            account_service.create_account(dto)
            return [f"✅ {name} creado/a."]*len(n_clicks_list), [{'color': 'green'}]*len(n_clicks_list), [""]*len(n_clicks_list)
        except Exception as e:
            return [f"❌ Error: {str(e)}"]*len(n_clicks_list), [{'color': 'red'}]*len(n_clicks_list), names

    # 3. Listar Cuentas
    @app.callback(
        Output({'type': 'list-acc-container', 'index': ALL}, 'children'),
        Input({'type': 'btn-refresh-list', 'index': ALL}, 'n_clicks'),
        Input('config-tabs', 'value'), # Recargar al cambiar tab
        Input({'type': 'btn-create-acc', 'index': ALL}, 'n_clicks') # Recargar al crear
    )
    def list_accounts(n1, tab_val, n2):
        # Determinar qué tipo listar basado en el contexto o el tab actual
        # Como ListAccContainer se regenera, usamos el ID del componente que disparó o el tab value
        
        # Truco: Si el callback se dispara por Tab Change, 'ctx.triggered_id' es 'config-tabs'.
        # Necesitamos saber qué Tab es para listar lo correcto.
        
        current_tab_map = {
            'tab-assets': AccountType.ASSET,
            'tab-liabilities': AccountType.LIABILITY,
            'tab-expenses': AccountType.EXPENSE,
            'tab-revenue': AccountType.INCOME
        }
        
        if isinstance(tab_val, str): # Viene del input directo 'config-tabs.value' si está en args, dash pasa lista si es ALL
             # Espera, 'tab_val' aquí es una lista si viene de ALL? No, config-tabs es id único.
             # Pero list_accounts tiene inputs ALL. 'config-tabs' NO es ALL.
             # La firma recibe: [n1_list], tab_value, [n2_list]
             pass
        else:
            # tab_val es el segundo argumento, que es single value
            pass
            
        target_type_enum = current_tab_map.get(tab_val, AccountType.ASSET)
        
        accounts = account_service.list_accounts()
        # Filtrar en memoria (rápido para pocas cuentas)
        filtered = [a for a in accounts if a.type == target_type_enum]
        
        if not filtered:
            return [html.Div("No hay cuentas de este tipo registradas.")]
            
        # Generar tabla simple
        rows = []
        for acc in filtered:
            rows.append(html.Tr([
                html.Td(acc.name, style={'fontWeight': 'bold'}),
                html.Td(f"{acc.balance.amount} €" if hasattr(acc, 'balance') else "-"), # El modelo Account no tiene balance vivo calculado, solo inicial. 
                # TODO: AccountService debería devolver el balance actual calculado. Por ahora mostramos nombre.
                html.Td(acc.account_number if acc.account_number else "-")
            ]))
            
        table = html.Table([
            html.Thead(html.Tr([html.Th("Nombre"), html.Th("Saldo (Simulado)"), html.Th("Info")])),
            html.Tbody(rows)
        ], style={'width': '100%', 'textAlign': 'left'})
        
        return [table]
