from dash import html, dcc, Input, Output, State
import pandas as pd
from src.application.dtos import TagDTO

def get_layout():
    return html.Div([
        html.H3("Gestión de Etiquetas"),
        html.P("Las etiquetas te permiten agrupar transacciones transversalmente (ej: 'Vacaciones', 'Boda') independientemente de la categoría."),
        
        html.Div([
            html.Div([
                html.Label("Nombre de la Etiqueta:"),
                dcc.Input(id='tag-name', type='text', placeholder='Ej: Vacaciones 2024', style={'width': '100%'}),
            ], style={'flex': '1'}),
            
            html.Div([
                html.Label("Color (Hex):"),
                dcc.Input(id='tag-color', type='text', placeholder='#FF5733', value='#3498db', style={'width': '100%'}),
            ], style={'flex': '1'}),

            html.Button('Crear Etiqueta', id='btn-create-tag', n_clicks=0, style={'height': '38px', 'alignSelf': 'flex-end'}),
        ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '20px', 'maxWidth': '600px'}),

        html.Div(id='msg-create-tag', style={'fontWeight': 'bold'}),
        
        html.Hr(),
        html.H3("Etiquetas Existentes"),
        html.Button('🔄 Actualizar Etiquetas', id='btn-refresh-tags', n_clicks=0),
        html.Div(id='table-tags', style={'marginTop': '10px'})
    ], style={'padding': '20px'})

def register_callbacks(app, tag_service):
    # 3. Crear Tag
    @app.callback(
        Output('msg-create-tag', 'children'),
        Output('msg-create-tag', 'style'),
        Input('btn-create-tag', 'n_clicks'),
        State('tag-name', 'value'),
        State('tag-color', 'value'),
        prevent_initial_call=True
    )
    def create_tag(n_clicks, name, color):
        if not name:
            return "❌ El nombre es obligatorio.", {'color': 'red'}
        try:
            dto = TagDTO(name=name, color=color)
            tag_service.create_tag(dto)
            return f"✅ Etiqueta '{name}' creada.", {'color': 'green'}
        except Exception as e:
            return f"❌ Error: {str(e)}", {'color': 'red'}

    # 4. Listar Tags
    @app.callback(
        Output('table-tags', 'children'),
        Input('btn-refresh-tags', 'n_clicks'),
        Input('btn-create-tag', 'n_clicks'),
    )
    def list_tags(n_refresh, n_create):
        tags = tag_service.list_tags()
        if not tags:
            return "No hay etiquetas."
        
        data = [{"Nombre": t.name, "Color": t.color} for t in tags]
        df = pd.DataFrame(data)
        return html.Table([
            html.Thead(html.Tr([html.Th(col) for col in df.columns])),
            html.Tbody([
                html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
                for i in range(len(df))
            ])
        ], style={'width': '100%', 'borderCollapse': 'collapse', 'border': '1px solid #ddd'})
