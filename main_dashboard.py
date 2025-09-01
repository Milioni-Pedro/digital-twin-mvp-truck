import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import os
import json
import subprocess
from sklearn.ensemble import IsolationForest
import numpy as np

# --- 1. CONFIGURAÇÕES E CARREGAMENTO ---
user_home = os.path.expanduser("~")
project_folder = os.path.join(user_home, "digital_twin_mvp")
data_path = os.path.join(project_folder, "fleet_simulated_data.csv")
life_path = os.path.join(project_folder, "fleet_life_estimate.csv")
fea_input_path = os.path.join(project_folder, "fea", "input_fea.json")
fea_output_path = os.path.join(project_folder, "fea", "output_fea.json")
mock_solver_path = os.path.join(project_folder, "fea", "mock_fea_solver.py")
SAMPLING_INTERVAL_S = 10

try:
    df_data = pd.read_csv(data_path)
    df_data['timestamp'] = pd.to_datetime(df_data['timestamp'])
    df_life = pd.read_csv(life_path)
    df_life['timestamp'] = pd.to_datetime(df_life['timestamp'])
except Exception as e:
    print(f"Erro ao carregar arquivos de dados da frota: {e}. Execute generate_data.py e life_model.py")
    exit()

# O merge aqui foi removido para simplificar, faremos os joins necessários nos callbacks.
# Isso melhora a performance inicial de carregamento.
CHASSIS_OPTIONS = df_data['chassis_number'].unique()
SENSOR_OPTIONS = ['temperatura_C', 'vibracao_g', 'radiacao_Wm2', 'velocidade_kmh', 'deformacao_micros']

# --- 2. LAYOUT DO APP DASH (CORRIGIDO COM O CARD DE FEA) ---
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
                    value=[CHASSIS_OPTIONS[0]],
                    multi=True
                ),
                html.Hr(),
                html.Label("Selecione o Sensor:"),
                dcc.Dropdown(id='sensor-selector', options=[{'label': s, 'value': s} for s in SENSOR_OPTIONS], value='vibracao_g'),
            ])]),
            html.Br(),
            dbc.Card([
                dbc.CardHeader("Saúde do Chassi (Primeiro Selecionado)"),
                dbc.CardBody(id='health-cards')
            ]),
            html.Br(),
            # --- CARD DE SIMULAÇÃO FEA REINSERIDO AQUI ---
            dbc.Card([
                dbc.CardHeader("Simulação de Engenharia 'What-if'"),
                dbc.CardBody([
                    html.Label("Selecione o Tipo de Análise:"),
                    dcc.RadioItems(
                        options=[
                            {'label': 'Estático', 'value': 'estatico'},
                            {'label': 'Fadiga', 'value': 'fadiga'},
                            {'label': 'Modal', 'value': 'modal'},
                        ],
                        value='fadiga', id='analysis-type-selector', inline=True, inputStyle={"margin-left": "20px", "margin-right": "5px"}
                    ),
                    dbc.Button("Rodar Simulação", id="run-fea-button", color="warning", className="mt-3 w-100"),
                    html.Hr(),
                    dcc.Loading(id="loading-fea", children=[html.Div(id='fea-results-output')], type="default")
                ])
            ])
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
    dff = df_data[df_data['chassis_number'].isin(selected_chassis)]
    fig = px.line(
        dff, x='timestamp', y=selected_sensor, color='chassis_number',
        title=f'Histórico do Sensor: {selected_sensor}', labels={'chassis_number': 'Chassi'}
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
    chassis_to_display = selected_chassis[0]
    life_data = df_life[df_life['chassis_number'] == chassis_to_display].iloc[-1]
    life_used = life_data['life_used_percent']
    
    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number", value=life_used,
        title={'text': f"Vida Consumida ({chassis_to_display})"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "orange"}, 'steps': [{'range': [0, 80], 'color': "green"}, {'range': [80, 100], 'color': "red"}]}
    ))
    gauge_fig.update_layout(template='plotly_dark', height=250, margin=dict(l=10, r=10, t=50, b=10))
    return dcc.Graph(figure=gauge_fig)

# --- CALLBACK DO FEA ATUALIZADO PARA USAR O CHASSI SELECIONADO ---
@app.callback(
    Output('fea-results-output', 'children'),
    Input('run-fea-button', 'n_clicks'),
    [State('chassis-selector', 'value'),
     State('analysis-type-selector', 'value')],
    prevent_initial_call=True
)
def run_fea_simulation(n_clicks, selected_chassis, analysis_type):
    if not selected_chassis:
        return dbc.Alert("Por favor, selecione um chassi primeiro.", color="warning")
    
    chassis_to_analyze = selected_chassis[0]
    recent_data = df_data[df_data['chassis_number'] == chassis_to_analyze].tail(500)
    
    input_data = {"analysis_type": analysis_type}
    
    if analysis_type == 'estatico':
        input_data["peak_deformacao_micros"] = recent_data['deformacao_micros'].max()
    elif analysis_type == 'fadiga':
        input_data["avg_vibracao_g"] = recent_data['vibracao_g'].mean()
    elif analysis_type == 'modal':
        vibration_data = recent_data['vibracao_g'].to_numpy()
        fft_result = np.fft.fft(vibration_data - vibration_data.mean())
        freqs = np.fft.fftfreq(len(vibration_data), d=SAMPLING_INTERVAL_S)
        peak_freq_idx = np.argmax(np.abs(fft_result[1:len(fft_result)//2])) + 1
        dominant_freq = freqs[peak_freq_idx]
        input_data["dominant_freq_hz"] = dominant_freq

    with open(fea_input_path, 'w') as f: json.dump(input_data, f, indent=4)
    subprocess.run(['python', mock_solver_path], check=True, capture_output=True, text=True)
    with open(fea_output_path, 'r') as f: results = json.load(f)

    alerts = [dbc.Alert(f"Análise para Chassi: {chassis_to_analyze}", color="secondary")]
    alerts.append(dbc.Alert(f"Tipo de Análise: {results.pop('tipo_analise')}", color="primary"))
    results.pop("timestamp", None)
    
    for key, value in results.items():
        color = "info"
        risk_key = str(value).upper()
        if "risco" in key.lower() and ("ALTO" in risk_key or "MÉDIO" in risk_key): color = "danger"
        try:
            numeric_value = float(str(value).split(' ')[0])
            if "fator" in key.lower() and numeric_value < 1.5: color = "danger"
        except (ValueError, IndexError): pass
        alerts.append(dbc.Alert(f"{key.replace('_', ' ').title()}: {value}", color=color))
        
    return html.Div(alerts)

# --- 4. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)