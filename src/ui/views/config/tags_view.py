from dash import html, dash_table, Input, Output
import dash_bootstrap_components as dbc

def layout_tags():
    """
    Genera y devuelve el diseño (layout) de la interfaz de usuario para la sección de 'Etiquetas'.
    
    Esta vista permite gestionar las etiquetas (tags) utilizadas para clasificar transversalesmente las transacciones.
    
    Componentes principales:
    - Encabezado y descripción.
    - Barra de herramientas:
        - Botón "Nueva Etiqueta".
        - Buscador.
        - Botón "Actualizar".
    - Tabla de datos (dash_table.DataTable):
        - Columnas editables: Nombre, Color, Icono.
    
    Returns:
        html.Div: Contenedor principal con todos los componentes de la vista.
    """
    return html.Div([
        # Título y subtítulo
        html.H2("🏷️ Gestión de Etiquetas", style={'color': '#16a085'}),
        html.P("Etiqueta tus movimientos para un control granular.", style={'color': '#7f8c8d'}),
        html.Hr(),

        # Botonera
        dbc.Row([
            dbc.Col(dbc.Button("➕ Nueva Etiqueta", color="info", id='btn-add-tag'), width="auto"),
            dbc.Col(dbc.Input(type="text", placeholder="Buscar etiqueta..."), width=3),
            dbc.Col(dbc.Button("🔄 Actualizar", id='btn-refresh-tags', color="secondary"), width="auto"),
        ], className="mb-3"),

        # Tabla de etiquetas
        dash_table.DataTable(
            id='table-tags',
            columns=[
                {"name": "Nombre", "id": "name", "editable": True},
                {"name": "Color", "id": "color", "editable": True},  # TODO: Podría implementarse con un color picker
                {"name": "Icono", "id": "icon", "editable": True},
            ],
            data=[],  # Cargado dinámicamente
            page_current=0,
            page_size=10,
            style_header={'backgroundColor': 'white', 'fontWeight': 'bold'},
        )
    ])

def register_callbacks(app, tag_service):
    """
    Registra los callbacks necesarios para la vista de Etiquetas.
    
    Args:
        app (Dash): Instancia de la app Dash.
        tag_service (TagService): Servicio para gestionar Tags.
    """

    @app.callback(
        Output('table-tags', 'data'),
        Input('btn-refresh-tags', 'n_clicks'),
        Input('url', 'pathname')
    )
    def update_tags_table(n_clicks, pathname):
        """
        Callback para actualizar la tabla de etiquetas.
        
        Se dispara al navegar a '/tags' o pulsar actualizar.
        Obtiene la lista completa de tags y la formatea para el DataTable.
        
        Args:
            n_clicks (int): Número de clics en refrescar.
            pathname (str): Ruta actual.
            
        Returns:
            list[dict]: Lista de etiquetas formateada.
        """
        if pathname != '/tags':
            from dash import no_update
            return no_update
            
        tags = tag_service.list_tags()
        
        data = []
        for t in tags:
            data.append({
                "name": t.name,
                "color": t.color,
                "icon": t.icon or ""
            })
            
        return data
