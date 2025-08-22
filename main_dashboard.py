import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Usaremos para adicionar os marcadores de anomalia
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import os

# --- NOVAS IMPORTAÇÕES PARA DETECÇÃO DE ANOMALIAS ---
from sklearn.ensemble import IsolationForest

# --- 1. CONFIGURAÇÕES E CARREGAMENTO DOS DADOS ---

# Flag para escolher o método de detecção. Mude para False para usar o método 3-Sigma.
USE_ISOLATION_FOREST = True

user_home = os.path.expanduser("~")
project_folder = os.path.join(user_home, "digital_twin_mvp")
csv_path = os.path.join(project_folder, "sunvisor_simulated_data.csv")
anomalies_output_path = os.path.join(project_folder, "anomalies.csv")

try:
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
except FileNotFoundError:
    print(f"ERRO: O arquivo {csv_path} não foi encontrado. Execute 'generate_data.py' primeiro.")
    exit()

sensor_options = [col for col in df.columns if col != 'timestamp']

# --- 2. FUNÇÃO DE DETECÇÃO DE ANOMALIAS (NOVA SEÇÃO) ---

def detect_anomalies(data, method_flag):
    """
    Detecta anomalias no DataFrame usando um dos dois métodos.
    """
    df_anom = data.copy()
    features = sensor_options # Usamos todos os sensores como características para o modelo

    if method_flag:
        print("Detectando anomalias com Isolation Forest...")
        # Isolation Forest é bom para detectar anomalias em dados multivariados.
        # 'contamination' é a proporção esperada de anomalias no dataset.
        model = IsolationForest(contamination=0.01, random_state=42)
        predictions = model.fit_predict(df_anom[features])
        # O modelo retorna -1 para anomalias e 1 para pontos normais.
        df_anom['is_anomaly'] = [True if x == -1 else False for x in predictions]
    else:
        print("Detectando anomalias com o método 3-Sigma...")
        # O método 3-Sigma avalia cada sensor individualmente.
        # Uma anomalia é qualquer ponto que esteja a mais de 3 desvios padrão da média.
        df_anom['is_anomaly'] = False # Começamos assumindo que nenhum ponto é anômalo
        for col in features:
            mean = df_anom[col].mean()
            std = df_anom[col].std()
            upper_bound = mean + 3 * std
            lower_bound = mean - 3 * std
            # Marca como anomalia se estiver fora dos limites
            anomalies = (df_anom[col] > upper_bound) | (df_anom[col] < lower_bound)
            df_anom['is_anomaly'] = df_anom['is_anomaly'] | anomalies

    num_anomalies = df_anom['is_anomaly'].sum()
    print(f"Total de {num_anomalies} anomalias detectadas.")
    return df_anom

# Executa a detecção e salva o resultado
df = detect_anomalies(df, USE_ISOLATION_FOREST)
df.to_csv(anomalies_output_path, index=False)
print(f"Dados com anomalias salvos em: {anomalies_output_path}")


# --- 3. INICIALIZAÇÃO E LAYOUT DO APP DASH (SEM MUDANÇAS AQUI) ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
app.title = "Digital Twin MVP - Cabine"

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Digital Twin MVP: Monitor de Componente da Cabine", className="text-center text-primary mb-4"), width=12)
    ]),
    dbc.Row([
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
            ])
        ], width=3),
        dbc.Col([
            dcc.Graph(id='sensor-graph')
        ], width=9)
    ])
], fluid=True)


# --- 4. CALLBACKS (ATUALIZADO PARA MOSTRAR ANOMALIAS) ---
@app.callback(
    Output('sensor-graph', 'figure'),
    [Input('sensor-dropdown', 'value')]
)
def update_graph(selected_sensor):
    """
    Atualiza o gráfico para mostrar a série temporal e destacar as anomalias.
    """
    print(f"Atualizando gráfico para o sensor: {selected_sensor}")
    
    # Cria a figura base com a linha do sensor
    fig = px.line(
        df,
        x='timestamp',
        y=selected_sensor,
        title=f'Histórico do Sensor: {selected_sensor}'
    )
    
    # Adiciona os marcadores de anomalia
    anomalies_df = df[df['is_anomaly']]
    fig.add_trace(go.Scatter(
        x=anomalies_df['timestamp'],
        y=anomalies_df[selected_sensor],
        mode='markers',
        marker=dict(
            color='red',
            size=10,
            symbol='x'
        ),
        name='Anomalia Detectada'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        xaxis_title='Tempo',
        yaxis_title=selected_sensor,
        transition_duration=200
    )
    
    return fig

# --- 5. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)