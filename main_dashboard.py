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
anomalies_output_path = os.path.join(project_folder, "anomalies_events.csv") # Nome do arquivo de saída atualizado
life_input_path = os.path.join(project_folder, "life_estimate.csv")
fea_input_path = os.path.join(project_folder, "fea", "input_fea.json")
fea_output_path = os.path.join(project_folder, "fea", "output_fea.json")
mock_solver_path = os.path.join(project_folder, "fea", "mock_fea_solver.py")

USE_ISOLATION_FOREST = True
sensor_options = ['temperatura_C', 'vibracao_g', 'radiacao_Wm2', 'velocidade_kmh', 'deformacao_micros']


# --- 2. FUNÇÕES DE PROCESSAMENTO DE DADOS (INTELIGÊNCIA) ---

def detect_anomalies(data, method_flag):
    df_anom = data.copy()
    features = sensor_options
    if method_flag:
        model = IsolationForest(contamination=0.01, random_state=42)
        predictions = model.fit_predict(df_anom[features])
        df_anom['is_anomaly'] = [True if x == -1 else False for x in predictions]
    else:
        df_anom['is_anomaly'] = False
        for col in features:
            mean, std = df_anom[col].mean(), df_anom[col].std()
            upper_bound, lower_bound = mean + 3 * std, mean - 3 * std
            anomalies = (df_anom[col] > upper_bound) | (df_anom[col] < lower_bound)
            df_anom['is_anomaly'] = df_anom['is_anomaly'] | anomalies
    return df_anom

# --- NOVA FUNÇÃO DE CORRELAÇÃO DE EVENTOS ---
def correlate_events(data):
    print("Correlacionando anomalias com eventos...")
    df_events = data.copy()
    df_events['evento'] = "Operação Normal"
    anomalies_idx = df_events[df_events['is_anomaly']].index
    
    for idx in anomalies_idx:
        row = df_events.loc[idx]
        if row['vibracao_g'] > 7.0 and row['deformacao_micros'] > 150:
            df_events.loc[idx, 'evento'] = "Impacto Severo (Buraco/Obstáculo)"
        elif row['temperatura_C'] > 55 and row['velocidade_kmh'] < 10:
            df_events.loc[idx, 'evento'] = "Superaquecimento (Veículo Parado)"
        elif row['vibracao_g'] == 0 and row['velocidade_kmh'] > 30:
            df_events.loc[idx, 'evento'] = "Suspeita de Falha (Sensor de Vibração)"
        else:
            df_events.loc[idx, 'evento'] = "Anomalia Não Especificada"
    return df_events

# --- 3. CARREGAMENTO E PROCESSAMENTO INICIAL ---
try:
    df_raw = pd.read_csv(raw_data_path)
    df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
except Exception as e:
    print(f"Erro ao carregar dados brutos: {e}. Execute generate_data.py")
    exit()

# FLUXO DE INTELIGÊNCIA MODIFICADO
df_anomalies = detect_anomalies(df_raw, USE_ISOLATION_FOREST)
df_final = correlate_events(df_anomalies) # Usa o resultado final com a coluna 'evento'
df_final.to_csv(anomalies_output_path, index=False)
print(f"Dados com anomalias e eventos salvos em: {anomalies_output_path}")

try:
    df_life = pd.read_csv(life_input_path)
    final_life_used = df_life['life_used_percent'].iloc[-1]
    final_life_remaining = df_life['life_remaining_percent'].iloc[-1]
except Exception:
    final_life_used, final_life_remaining = 0, 100


# --- 4. INICIALIZAÇÃO E LAYOUT DO APP DASH ---
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


# --- 5. CALLBACKS ---

# Callback 1: Atualiza o gráfico principal (MODIFICADO)
@app.callback(
    Output('sensor-graph', 'figure'),
    [Input('sensor-dropdown', 'value')]
)
def update_graph(selected_sensor):
    fig = px.line(
        df_final,
        x='timestamp',
        y=selected_sensor,
        title=f'Histórico do Sensor: {selected_sensor}',
        hover_data={'evento': True, 'velocidade_kmh': ':.1f', 'temperatura_C': ':.1f'}
    )
    
    anomalies_df = df_final[df_final['is_anomaly']]
    
    fig.add_trace(go.Scatter(
        x=anomalies_df['timestamp'],
        y=anomalies_df[selected_sensor],
        mode='markers',
        marker=dict(color='red', size=12, symbol='x-thin', line={'width': 2}),
        name='Anomalia',
        customdata=anomalies_df[['evento', 'vibracao_g', 'temperatura_C']],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>" +
            "Timestamp: %{x|%d-%b-%Y %H:%M}<br>" +
            f"{selected_sensor}: %{{y:.2f}}<br>" +
            "Vibração (g): %{customdata[1]:.2f}<br>" +
            "Temperatura (°C): %{customdata[2]:.1f}<extra></extra>"
        )
    ))
    
    fig.update_layout(
        template='plotly_dark',
        xaxis_title='Tempo',
        yaxis_title=selected_sensor,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    return fig

# Callback 2: Roda a simulação FEA Mock (MODIFICADO para usar df_final)
@app.callback(
    Output('fea-results-output', 'children'),
    [Input('run-fea-button', 'n_clicks')],
    prevent_initial_call=True
)
def run_fea_simulation(n_clicks):
    last_24h_data = df_final.tail(int(24 * 3600 / 10))
    avg_temp = last_24h_data['temperatura_C'].mean()
    max_vib = last_24h_data['vibracao_g'].max()

    input_data = {"avg_temp_C": round(avg_temp, 2), "max_vibracao_g": round(max_vib, 2)}
    with open(fea_input_path, 'w') as f:
        json.dump(input_data, f, indent=4)

    subprocess.run(['python', mock_solver_path], check=True, capture_output=True, text=True)

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

# --- 6. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)