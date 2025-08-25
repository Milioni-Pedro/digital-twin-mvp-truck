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

# --- 1. CONFIGURAÇÕES E CAMINHOS ---
user_home = os.path.expanduser("~")
project_folder = os.path.join(user_home, "digital_twin_mvp")
raw_data_path = os.path.join(project_folder, "sunvisor_simulated_data.csv")
life_input_path = os.path.join(project_folder, "life_estimate.csv")
fea_input_path = os.path.join(project_folder, "fea", "input_fea.json")
fea_output_path = os.path.join(project_folder, "fea", "output_fea.json")
mock_solver_path = os.path.join(project_folder, "fea", "mock_fea_solver.py")

sensor_options = ['temperatura_C', 'vibracao_g', 'radiacao_Wm2', 'velocidade_kmh', 'deformacao_micros']

# --- 2. FUNÇÃO DE PROCESSAMENTO DE DADOS ---
def detect_anomalies(data):
    df_anom = data.copy()
    model = IsolationForest(contamination=0.001, random_state=42)
    predictions = model.fit_predict(df_anom[sensor_options])
    df_anom['is_anomaly'] = [True if x == -1 else False for x in predictions]
    df_anom.loc[df_anom['evento'] == 'Anomalia: Impacto Severo', 'is_anomaly'] = True
    return df_anom

# --- 3. CARREGAMENTO E PROCESSAMENTO INICIAL ---
try:
    df_raw = pd.read_csv(raw_data_path)
    df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
except Exception as e:
    print(f"Erro ao carregar dados brutos: {e}. Execute generate_data.py")
    exit()

df_final = detect_anomalies(df_raw)

try:
    df_life = pd.read_csv(life_input_path)
    final_life_used = df_life['life_used_percent'].iloc[-1]
    final_life_remaining = df_life['life_remaining_percent'].iloc[-1]
except Exception:
    final_life_used, final_life_remaining = 0, 100

# --- 4. LAYOUT DO APP DASH (CORRIGIDO) ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
app.title = "Digital Twin - Análise de Durabilidade"

gauge_fig = go.Figure(go.Indicator(
    mode="gauge+number", value=final_life_used, title={'text': "Consumo de Vida por Fadiga (%)"},
    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "orange"}, 'steps': [{'range': [0, 80], 'color': "green"}, {'range': [80, 100], 'color': "red"}]}
))
gauge_fig.update_layout(template='plotly_dark', height=250, margin=dict(l=10, r=10, t=50, b=10))

app.layout = dbc.Container([
    dbc.Row([dbc.Col(html.H1("Digital Twin: Monitor de Durabilidade", className="text-center text-primary mb-4"), width=12)]),
    dbc.Row([
        dbc.Col([
            dbc.Card([dbc.CardBody([
                html.H4("Controles", className="card-title"),
                html.Label("Selecione o Sensor:"),
                dcc.Dropdown(id='sensor-dropdown', options=[{'label': s, 'value': s} for s in sensor_options], value='vibracao_g'),
            ])]),
            html.Br(),
            dbc.Card([
                dbc.CardHeader("Estimativa de Vida por Fadiga"),
                dbc.CardBody([
                    dcc.Graph(id='life-gauge', figure=gauge_fig),
                    dbc.Alert(f"Atenção: Vida útil restante é de {final_life_remaining:.1f}%.", color="danger", is_open=(final_life_remaining < 20)),
                ])
            ]),
            html.Br(),
            # --- CARD DO FEA REINSERIDO AQUI ---
            dbc.Card([
                dbc.CardHeader("Retroalimentação por Simulação"),
                dbc.CardBody([
                    html.P("Rode uma simulação 'what-if' com base nas condições operacionais recentes.", className="card-text"),
                    dbc.Button("Rodar Simulação FEA (Mock)", id="run-fea-button", color="warning", className="mt-2"),
                    html.Hr(),
                    dcc.Loading(id="loading-fea", children=[html.Div(id='fea-results-output')], type="default")
                ])
            ])
        ], width=3),
        dbc.Col([dcc.Graph(id='sensor-graph', style={'height': '85vh'})], width=9)
    ])
], fluid=True)


# --- 5. CALLBACKS ---
@app.callback(
    Output('sensor-graph', 'figure'),
    [Input('sensor-dropdown', 'value')]
)
def update_graph(selected_sensor):
    fig = px.line(
        df_final, x='timestamp', y=selected_sensor, color='evento',
        title=f'Histórico do Sensor: {selected_sensor} por Tipo de Trecho',
        hover_data={'evento': True, 'vibracao_g': ':.2f'}
    )
    
    anomalies_df = df_final[df_final['is_anomaly']]
    fig.add_trace(go.Scatter(
        x=anomalies_df['timestamp'], y=anomalies_df[selected_sensor], mode='markers',
        marker=dict(symbol='x', size=12, color='#FF4136', line=dict(width=2)),
        name='Anomalia Pontual',
        hovertemplate="<b>%{customdata[0]}</b><br>Timestamp: %{x}<br>Valor: %{y:.2f}<extra></extra>",
        customdata=anomalies_df[['evento']]
    ))
    
    fig.update_layout(
        template='plotly_dark', xaxis_title='Tempo', yaxis_title=selected_sensor,
        legend_title_text='Eventos/Trechos'
    )
    return fig

@app.callback(
    Output('fea-results-output', 'children'),
    [Input('run-fea-button', 'n_clicks')],
    prevent_initial_call=True
)
def run_fea_simulation(n_clicks):
    last_24h_data = df_final.tail(int(24 * 3600 / 10))
    avg_temp, max_vib = last_24h_data['temperatura_C'].mean(), last_24h_data['vibracao_g'].max()
    input_data = {"avg_temp_C": round(avg_temp, 2), "max_vibracao_g": round(max_vib, 2)}
    with open(fea_input_path, 'w') as f: json.dump(input_data, f, indent=4)
    
    subprocess.run(['python', mock_solver_path], check=True, capture_output=True, text=True)
    
    with open(fea_output_path, 'r') as f: results = json.load(f)
        
    stress = results.get("max_stress_von_mises_MPa")
    sf = results.get("safety_factor")
    
    color = "success"
    if sf < 3: color = "warning"
    if sf < 1.5: color = "danger"
    
    return html.Div([
        html.H6(f"Resultado da Simulação:", className="mt-3"),
        dbc.Alert(f"Tensão Máxima: {stress} MPa", color="info"),
        dbc.Alert(f"Fator de Segurança: {sf}", color=color)
    ])

# --- 6. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)