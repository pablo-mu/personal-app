from dash import html, dcc
import dash_bootstrap_components as dbc

def layout_budgets():
    """
    Genera y devuelve el diseño (layout) de la interfaz de usuario para la sección de 'Objetivos Mensuales'.
    
    Esta vista permite al usuario definir presupuestos límite para diferentes categorías de gasto.
    
    Componentes principales:
    - Encabezado y descripción de la sección.
    - Formulario de creación de presupuesto (dbc.Row):
        - Dropdown para seleccionar la categoría de gasto.
        - Input numérico para establecer el límite en euros.
        - Botón "Guardar Objetivo" (Pendiente de implementación lógica).
    - Marcador de posición (Placeholder) para una futura gráfica de visualización del estado del presupuesto.
    
    Returns:
        html.Div: Contenedor principal con todos los componentes de la vista.
    """
    return html.Div([
        # Título y subtítulo de la sección
        html.H2("🎯 Objetivos Mensuales", style={'color': '#d35400'}),
        html.P("Define cuánto quieres gastar como máximo en cada categoría este mes.", style={'color': '#7f8c8d'}),
        html.Hr(),
        
        # Formulario para establecer nuevo presupuesto
        dbc.Row([
            dbc.Col([
                dbc.Label("Categoría"),
                dcc.Dropdown(id='budget-category', placeholder="Selecciona categoría...")
            ], width=4),
            dbc.Col([
                dbc.Label("Límite (€)"),
                dbc.Input(id='budget-amount', type='number', placeholder="300")
            ], width=3),
            dbc.Col([
                dbc.Button(html.I(className="bi bi-save"), color="secondary", outline=True, className="mt-4 btn-sm", id="btn-save-budget"),
                dbc.Tooltip("Guardar Objetivo", target="btn-save-budget", placement="top"),
            ], width="auto")
        ], className="mb-4"),
        
        # Placeholder para futura funcionalidad de gráficas
        html.Div("Gráfica de estado del presupuesto (Placeholder)", style={'padding': '40px', 'border': '1px dashed #ccc', 'textAlign': 'center'})
    ])
