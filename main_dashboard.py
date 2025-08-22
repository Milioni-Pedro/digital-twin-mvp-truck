import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import os
import json
import subprocess # Para chamar nosso script mock

# --- 1. CONFIGURAÇÕES E CARREGAMENTO ---
user_home = os.path.expanduser("~")
project_folder = os.path.join(user_home, "digital_twin_mvp")
anomalies_input_path = os.path.join(project_folder, "anomalies.csv")
life_input_path = os.path.join(project_folder, "life_estimate.csv")
fea_input_path = os.path.join(project_folder, "fea", "input_fea.json")
fea_output_path = os.path.join(project_folder, "fea", "output_fea.json")
mock_solver_path = os.path.join(project_folder, "fea", "mock_fea_solver.py")

try:
    df_anomalies = pd.read_csv(anomalies_input_path)
    df_anomalies['timestamp'] = pd.to_datetime(df_anomalies['timestamp'])
except Exception as e:
    print(f"Erro ao carregar dados de anomalias: {e}")
    exit()

try:
    df_life = pd.read_csv(life_input_path)
    final_life_used = df_life['life_used_percent'].iloc[-1]
    final_life_remaining = df_life['life_remaining_percent'].iloc[-1]
except Exception:
    final_life_used, final_life_remaining = 0, 100

sensor_options = [col for col in df_anomalies.columns if col not in ['timestamp', 'is_anomaly']]

# --- 2. INICIALIZAÇÃO E LAYOUT DO APP DASH (FINAL) ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
app.title = "Digital Twin MVP - Cabine"

gauge_fig = go.Figure(go.Indicator(
    mode="gauge+number", value=final_life_used, title={'text': "Vida Útil Consumida (%)"},
    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "orange"}, 'steps': [{'range': [0, 80], 'color': "green"}, {'range': [80, 100], 'color': "red"}]}
))
gauge_fig.update_layout(template='plotly_dark', height=250, margin=dict(l=10, r=10, t=40, b=10))

app.layout = dbc.Container([
    dbc.Row([dbc.Col(html.H1("Digital Twin MVP: Monitor de Componente da Cabine", className="text-center text-primary mb-4"), width=12)]),
    dbc.Row([
        dbc.Col([
            dbc.Card([dbc.CardBody([
                html.H4("Controles", className="card-title"),
                html.Label("Selecione o Sensor:"),
                dcc.Dropdown(id='sensor-dropdown', options=[{'label': s, 'value': s} for s in sensor_options], value=sensor_options[0]),
            ])]),
            html.Br(),
            dbc.Card([
                dbc.CardHeader("Estimativa de Vida Útil"),
                dbc.CardBody([
                    dcc.Graph(id='life-gauge', figure=gauge_fig),
                    dbc.Alert(f"Atenção: Vida útil restante é de {final_life_remaining:.1f}%.", color="danger", is_open=(final_life_remaining < 20)),
                ])
            ]),
            html.Br(),
            # --- NOVO: Card de Simulação FEA ---
            dbc.Card([
                dbc.CardHeader("Retroalimentação por Simulação"),
                dbc.CardBody([
                    html.P("Use as condições atuais para rodar uma simulação de engenharia (FEA).", className="card-text"),
                    dbc.Button("Rodar Simulação FEA (Mock)", id="run-fea-button", color="warning", className="mt-2"),
                    html.Hr(),
                    dcc.Loading(id="loading-fea", children=[html.Div(id='fea-results-output')], type="default")
                ])
            ])
        ], width=3),
        dbc.Col([dcc.Graph(id='sensor-graph', style={'height': '85vh'})], width=9)
    ])
], fluid=True)


# --- 3. CALLBACKS ---
# Callback 1: Atualiza o gráfico principal
@app.callback(
    Output('sensor-graph', 'figure'),
    [Input('sensor-dropdown', 'value')]
)
def update_graph(selected_sensor):
    fig = px.line(df_anomalies, x='timestamp', y=selected_sensor, title=f'Histórico do Sensor: {selected_sensor}')
    anomalies_df = df_anomalies[df_anomalies['is_anomaly']]
    fig.add_trace(go.Scatter(
        x=anomalies_df['timestamp'], y=anomalies_df[selected_sensor], mode='markers',
        marker=dict(color='red', size=10, symbol='x'), name='Anomalia'
    ))
    fig.update_layout(template='plotly_dark', xaxis_title='Tempo', yaxis_title=selected_sensor)
    return fig

# --- NOVO: Callback 2: Roda a simulação FEA Mock ---
@app.callback(
    Output('fea-results-output', 'children'),
    [Input('run-fea-button', 'n_clicks')],
    prevent_initial_call=True # Não roda quando o app inicia
)
def run_fea_simulation(n_clicks):
    # 1. Extrai as condições de carga do histórico de dados (últimas 24h simuladas)
    last_24h_data = df_anomalies.tail(int(24 * 3600 / 10)) # 10s por amostra
    avg_temp = last_24h_data['temperatura_C'].mean()
    max_vib = last_24h_data['vibracao_g'].max()

    # 2. Escreve o arquivo de input para o solver
    input_data = {"avg_temp_C": round(avg_temp, 2), "max_vibracao_g": round(max_vib, 2)}
    with open(fea_input_path, 'w') as f:
        json.dump(input_data, f, indent=4)

    # 3. Executa o script do solver em um processo separado
    # Usamos 'python' para garantir que ele use o interpretador padrão
    subprocess.run(['python', mock_solver_path], check=True)

    # 4. Lê o resultado e exibe no painel
    with open(fea_output_path, 'r') as f:
        results = json.load(f)
        
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

# --- 4. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)