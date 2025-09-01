import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import os

# --- 1. CONFIGURAÇÕES E CARREGAMENTO ---
user_home = os.path.expanduser("~")
project_folder = os.path.join(user_home, "digital_twin_mvp")
# --- MUDANÇA: Carregar os novos arquivos da frota ---
data_path = os.path.join(project_folder, "fleet_simulated_data.csv")
life_path = os.path.join(project_folder, "fleet_life_estimate.csv")

try:
    df_data = pd.read_csv(data_path)
    df_data['timestamp'] = pd.to_datetime(df_data['timestamp'])
    df_life = pd.read_csv(life_path)
    df_life['timestamp'] = pd.to_datetime(df_life['timestamp'])
except Exception as e:
    print(f"Erro ao carregar arquivos de dados da frota: {e}. Execute generate_data.py e life_model.py")
    exit()

# Juntando os dataframes para ter tudo em um só lugar
df_final = pd.merge(df_data, df_life.drop(columns=['timestamp', 'evento']), on=['chassis_number', 'temperatura_C', 'vibracao_g', 'velocidade_kmh', 'deformacao_micros', 'radiacao_Wm2'], how='left')

CHASSIS_OPTIONS = df_final['chassis_number'].unique()
SENSOR_OPTIONS = ['temperatura_C', 'vibracao_g', 'radiacao_Wm2', 'velocidade_kmh', 'deformacao_micros']

# --- 2. LAYOUT DO APP DASH (com seletor de chassi) ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
app.title = "Digital Twin - Gestão de Frota"

app.layout = dbc.Container([
    dbc.Row([dbc.Col(html.H1("Digital Twin: Painel de Gestão de Frota", className="text-center text-primary mb-4"), width=12)]),
    dbc.Row([
        # --- Coluna de Controles ---
        dbc.Col([
            dbc.Card([dbc.CardBody([
                html.H4("Filtros de Visualização", className="card-title"),
                html.Label("Selecione o(s) Chassi(s):"),
                dcc.Dropdown(
                    id='chassis-selector',
                    options=[{'label': ch, 'value': ch} for ch in CHASSIS_OPTIONS],
                    value=[CHASSIS_OPTIONS[0]], # Valor inicial é o primeiro chassi
                    multi=True # --- PERMITE MÚLTIPLA SELEÇÃO ---
                ),
                html.Hr(),
                html.Label("Selecione o Sensor:"),
                dcc.Dropdown(id='sensor-selector', options=[{'label': s, 'value': s} for s in SENSOR_OPTIONS], value='vibracao_g'),
            ])]),
            html.Br(),
            dbc.Card([
                dbc.CardHeader("Saúde do Chassi (Primeiro Selecionado)"),
                dbc.CardBody(id='health-cards') # Esta seção será atualizada por um callback
            ]),
        ], width=3),
        # --- Coluna do Gráfico ---
        dbc.Col([
            dcc.Graph(id='main-graph', style={'height': '85vh'})
        ], width=9)
    ])
], fluid=True, className="dbc")

# --- 3. CALLBACKS ---

# Callback 1: Atualiza o gráfico principal
@app.callback(
    Output('main-graph', 'figure'),
    [Input('chassis-selector', 'value'),
     Input('sensor-selector', 'value')]
)
def update_main_graph(selected_chassis, selected_sensor):
    if not selected_chassis:
        return go.Figure().update_layout(template='plotly_dark', title_text='Selecione um chassi para começar')

    dff = df_final[df_final['chassis_number'].isin(selected_chassis)]
    
    # --- MÁGICA: `color='chassis_number'` cria uma linha para cada chassi ---
    fig = px.line(
        dff, x='timestamp', y=selected_sensor, color='chassis_number',
        title=f'Histórico do Sensor: {selected_sensor}',
        labels={'chassis_number': 'Chassi'}
    )
    fig.update_layout(template='plotly_dark', legend_title_text='Legenda')
    return fig

# Callback 2: Atualiza os cards de saúde
@app.callback(
    Output('health-cards', 'children'),
    [Input('chassis-selector', 'value')]
)
def update_health_cards(selected_chassis):
    if not selected_chassis:
        return dbc.Alert("Nenhum chassi selecionado", color="info")
    
    # Vamos exibir os dados do PRIMEIRO chassi da lista selecionada
    chassis_to_display = selected_chassis[0]
    dff = df_final[df_final['chassis_number'] == chassis_to_display].iloc[-1]
    
    life_used = dff['life_used_percent']
    
    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number", value=life_used,
        title={'text': f"Vida Consumida ({chassis_to_display})"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "orange"}, 'steps': [{'range': [0, 80], 'color': "green"}, {'range': [80, 100], 'color': "red"}]}
    ))
    gauge_fig.update_layout(template='plotly_dark', height=250, margin=dict(l=10, r=10, t=50, b=10))

    return dcc.Graph(figure=gauge_fig)

# --- 4. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)