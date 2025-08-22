import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import os
from sklearn.ensemble import IsolationForest

# --- 1. CONFIGURAÇÕES E CARREGAMENTO DOS DADOS ---
USE_ISOLATION_FOREST = True

user_home = os.path.expanduser("~")
project_folder = os.path.join(user_home, "digital_twin_mvp")
anomalies_input_path = os.path.join(project_folder, "anomalies.csv")
life_input_path = os.path.join(project_folder, "life_estimate.csv") # NOVO CAMINHO

# Carrega dados de anomalias (gerados na Etapa C)
try:
    df_anomalies = pd.read_csv(anomalies_input_path)
    df_anomalies['timestamp'] = pd.to_datetime(df_anomalies['timestamp'])
except FileNotFoundError:
    print(f"ERRO: O arquivo {anomalies_input_path} não foi encontrado. Rode o dashboard da Etapa C primeiro para gerá-lo.")
    exit()

# --- NOVO: Carrega dados de vida útil ---
try:
    df_life = pd.read_csv(life_input_path)
    df_life['timestamp'] = pd.to_datetime(df_life['timestamp'])
    # Pega os valores finais para o gauge e o alerta
    final_life_used = df_life['life_used_percent'].iloc[-1]
    final_life_remaining = df_life['life_remaining_percent'].iloc[-1]
except FileNotFoundError:
    print(f"ERRO: O arquivo {life_input_path} não foi encontrado. Execute o script 'life_model.py' primeiro.")
    # Define valores padrão para o dashboard não quebrar
    final_life_used, final_life_remaining = 0, 100

sensor_options = [col for col in df_anomalies.columns if col not in ['timestamp', 'is_anomaly']]

# --- 2. INICIALIZAÇÃO E LAYOUT DO APP DASH (ATUALIZADO) ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
app.title = "Digital Twin MVP - Cabine"

# --- NOVO: Criação do Gauge de Vida Útil ---
gauge_fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=final_life_used,
    title={'text': "Vida Útil Consumida (%)"},
    gauge={'axis': {'range': [0, 100]},
           'bar': {'color': "orange"},
           'steps': [
               {'range': [0, 50], 'color': "green"},
               {'range': [50, 80], 'color': "yellow"}],
           'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 80}
          }
))
gauge_fig.update_layout(template='plotly_dark', height=300, margin=dict(l=10, r=10, t=40, b=10))

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Digital Twin MVP: Monitor de Componente da Cabine", className="text-center text-primary mb-4"), width=12)
    ]),
    dbc.Row([
        # Coluna da esquerda (controles e vida útil)
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Controles", className="card-title"),
                    html.Label("Selecione o Sensor:"),
                    dcc.Dropdown(
                        id='sensor-dropdown',
                        options=[{'label': sensor, 'value': sensor} for sensor in sensor_options],
                        value=sensor_options[0]
                    ),
                ])
            ]),
            html.Br(), # Espaçamento
            # --- NOVO: Card de Vida Útil ---
            dbc.Card([
                dbc.CardHeader("Estimativa de Vida Útil"),
                dbc.CardBody([
                    dcc.Graph(id='life-gauge', figure=gauge_fig),
                    # Alerta que aparece se a vida restante for baixa
                    dbc.Alert(
                        f"Atenção: Vida útil restante é de {final_life_remaining:.1f}%. Manutenção recomendada.",
                        color="danger",
                        is_open=(final_life_remaining < 20), # O alerta só aparece se a condição for verdadeira
                    )
                ])
            ]),
        ], width=3),
        # Coluna da direita (gráfico principal)
        dbc.Col([
            dcc.Graph(id='sensor-graph', style={'height': '80vh'})
        ], width=9)
    ])
], fluid=True)


# --- 3. CALLBACKS (SEM MUDANÇAS AQUI) ---
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
    fig.update_layout(template='plotly_dark', xaxis_title='Tempo', yaxis_title=selected_sensor, transition_duration=200)
    return fig

# --- 4. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)