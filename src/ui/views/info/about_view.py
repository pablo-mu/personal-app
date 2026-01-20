from dash import html
import dash_bootstrap_components as dbc

def layout_about():
    """
    Genera el diseño (layout) de la vista 'Acerca de'.
    
    Muestra información sobre la aplicación, versión, tecnologías utilizadas
    y créditos del desarrollo.
    
    Returns:
        html.Div: Contenedor principal con la información de la aplicación.
    """
    return html.Div([
        # Encabezado
        html.H2("ℹ️ Acerca de Mi Finanza", style={'color': '#2c3e50'}),
        html.P("Información sobre la aplicación", style={'color': '#7f8c8d'}),
        html.Hr(),
        
        # Card de Información General
        dbc.Card([
            dbc.CardHeader(html.H4("📱 Información General", className="mb-0")),
            dbc.CardBody([
                html.P([
                    html.Strong("Nombre: "),
                    "Mi Finanza - Sistema de Gestión Financiera Personal"
                ]),
                html.P([
                    html.Strong("Versión: "),
                    "1.0.0"
                ]),
                html.P([
                    html.Strong("Descripción: "),
                    "Aplicación web para el control y seguimiento de finanzas personales, "
                    "basada en el principio de contabilidad de partida doble."
                ]),
            ])
        ], className="mb-3"),
        
        # Card de Tecnologías
        dbc.Card([
            dbc.CardHeader(html.H4("🛠️ Tecnologías Utilizadas", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5("Frontend", className="text-primary"),
                        html.Ul([
                            html.Li("Dash (Plotly)"),
                            html.Li("Dash Bootstrap Components"),
                            html.Li("Python 3.11+"),
                        ])
                    ], width=6),
                    dbc.Col([
                        html.H5("Backend", className="text-success"),
                        html.Ul([
                            html.Li("SQLAlchemy (ORM)"),
                            html.Li("SQLite (Base de datos)"),
                            html.Li("Pydantic (Validación)"),
                        ])
                    ], width=6),
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H5("Arquitectura", className="text-warning"),
                        html.Ul([
                            html.Li("Clean Architecture"),
                            html.Li("Domain-Driven Design (DDD)"),
                            html.Li("Repository Pattern"),
                            html.Li("Unit of Work Pattern"),
                        ])
                    ], width=12),
                ])
            ])
        ], className="mb-3"),
        
        # Card de Características
        dbc.Card([
            dbc.CardHeader(html.H4("✨ Características Principales", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H6("📊 Dashboard", className="fw-bold"),
                            html.P("Visualización de resumen financiero y gráficos interactivos", className="text-muted small"),
                        ]),
                        html.Div([
                            html.H6("💳 Gestión de Cuentas", className="fw-bold"),
                            html.P("Administra cuentas bancarias, efectivo y tarjetas", className="text-muted small"),
                        ]),
                        html.Div([
                            html.H6("📋 Transacciones", className="fw-bold"),
                            html.P("Registro completo de movimientos con partida doble", className="text-muted small"),
                        ]),
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.H6("🏷️ Etiquetas", className="fw-bold"),
                            html.P("Clasifica y organiza tus transacciones", className="text-muted small"),
                        ]),
                        html.Div([
                            html.H6("🎯 Presupuestos", className="fw-bold"),
                            html.P("Define y monitorea objetivos financieros", className="text-muted small"),
                        ]),
                        html.Div([
                            html.H6("🔍 Filtros Avanzados", className="fw-bold"),
                            html.P("Búsqueda y filtrado de información detallada", className="text-muted small"),
                        ]),
                    ], width=6),
                ])
            ])
        ], className="mb-3"),
        
        # Card de Principios Contables
        dbc.Card([
            dbc.CardHeader(html.H4("📖 Principios Contables", className="mb-0")),
            dbc.CardBody([
                html.P([
                    html.Strong("Partida Doble: "),
                    "Cada transacción afecta al menos dos cuentas, manteniendo el balance contable. "
                    "La suma de todos los débitos debe ser igual a la suma de todos los créditos."
                ]),
                html.P([
                    html.Strong("Tipos de Cuenta: "),
                ]),
                html.Ul([
                    html.Li([html.Strong("Activos: "), "Lo que posees (efectivo, cuentas bancarias, inversiones)"]),
                    html.Li([html.Strong("Pasivos: "), "Lo que debes (préstamos, tarjetas de crédito)"]),
                    html.Li([html.Strong("Ingresos: "), "Dinero que recibes (salario, ventas)"]),
                    html.Li([html.Strong("Gastos: "), "Dinero que gastas (alquiler, comida, ocio)"]),
                    html.Li([html.Strong("Patrimonio: "), "Valor neto (activos - pasivos)"]),
                ]),
                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    "Las cuentas de tipo ACTIVO y PASIVO no pueden tener saldo negativo. "
                    "El sistema valida automáticamente la integridad de cada transacción."
                ], color="info", className="mt-3"),
            ])
        ], className="mb-3"),
        
        # Footer con información de desarrollo
        html.Hr(),
        html.Div([
            html.P([
                html.Small([
                    "Desarrollado con ❤️ usando Python y Dash | ",
                    html.A("Documentación", href="#", className="text-decoration-none"),
                    " | ",
                    html.A("Reportar Error", href="#", className="text-decoration-none"),
                ], className="text-muted")
            ], className="text-center")
        ])
    ])
