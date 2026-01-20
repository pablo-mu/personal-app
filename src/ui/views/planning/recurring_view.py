from dash import html, dcc
import dash_bootstrap_components as dbc

def layout_recurring():
    """
    Genera y devuelve el diseño (layout) de la interfaz de usuario para la sección de 'Pagos Recurrentes'.
    
    Esta vista permite al usuario configurar transacciones automáticas que se repiten con cierta periodicidad 
    (ej. suscripciones, alquileres).
    
    Componentes principales:
    - Encabezado y descripción.
    - Tarjeta (Card) de creación de nueva regla:
        - Campos para Concepto, Monto y Día de pago.
        - Botón "Añadir".
    - Lista simple (estática/placeholder) mostrando ejemplos de automatizaciones activas.
    
    NOTA: Esta es una implementación visual/prototipo. La lógica de programación de tareas backend no está visible aquí.
    
    Returns:
        html.Div: Contenedor principal con todos los componentes de la vista.
    """
    return html.Div([
        # Título y subtítulo
        html.H2("📅 Pagos Recurrentes", style={'color': '#8e44ad'}),
        html.P("Configura pagos que se repiten automáticamente.", style={'color': '#7f8c8d'}),
        html.Hr(),
        
        # Formulario en tarjeta para nueva regla
        dbc.Card([
            dbc.CardHeader("Nueva Regla Recurrente"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([dbc.Label("Concepto"), dbc.Input(placeholder="Ej: Netflix")], width=4),
                    dbc.Col([dbc.Label("Monto"), dbc.Input(type="number")], width=2),
                    dbc.Col([dbc.Label("Día Pago"), dbc.Input(type="number", min=1, max=31)], width=2),
                    dbc.Col([dbc.Button("Añadir", color="primary", className="mt-4")], width=2)
                ])
            ])
        ]),
        
        # Listado de reglas existentes (Placeholder)
        html.H5("Listado de Automatizaciones", className="mt-4"),
        html.Ul([
            html.Li("Alquiler - 800€ (Día 1)"), 
            html.Li("Spotify - 10€ (Día 5)")
        ])
    ])
