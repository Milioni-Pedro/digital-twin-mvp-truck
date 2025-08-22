import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import os

# --- 1. CARREGAMENTO DOS DADOS ---
# Constrói o caminho para o arquivo CSV de forma robusta
user_home = os.path.expanduser("~")
csv_path = os.path.join(user_home, "digital_twin_mvp", "sunvisor_simulated_data.csv")

# Tenta carregar o DataFrame
try:
    df = pd.read_csv(csv_path)
    # Converte a coluna 'timestamp' para o tipo datetime, essencial para gráficos de séries temporais
    df['timestamp'] = pd.to_datetime(df['timestamp'])
except FileNotFoundError:
    print(f"ERRO: O arquivo {csv_path} não foi encontrado. Execute o script 'generate_data.py' primeiro.")
    exit()

# Lista de sensores disponíveis para o dropdown (excluindo o timestamp)
sensor_options = [col for col in df.columns if col != 'timestamp']

# --- 2. INICIALIZAÇÃO DO APP DASH ---
# Usamos um tema do Bootstrap para um visual mais profissional
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
app.title = "Digital Twin MVP - Cabine"

# --- 3. LAYOUT DO PAINEL ---
app.layout = dbc.Container([
    # Linha do Título
    dbc.Row([
        dbc.Col(html.H1("Digital Twin MVP: Monitor de Componente da Cabine", className="text-center text-primary mb-4"), width=12)
    ]),

    # Linha com os Controles e o Gráfico
    dbc.Row([
        # Coluna dos Controles (à esquerda)
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Controles", className="card-title"),
                    html.Label("Selecione o Sensor:"),
                    dcc.Dropdown(
                        id='sensor-dropdown',
                        options=[{'label': sensor, 'value': sensor} for sensor in sensor_options],
                        value=sensor_options[0] # Valor inicial
                    ),
                    html.Hr(),
                    html.P("Este painel monitora dados simulados de um componente da cabine de um caminhão em tempo real.", className="card-text")
                ])
            ])
        ], width=3),

        # Coluna do Gráfico (à direita)
        dbc.Col([
            # O dcc.Graph será atualizado pelo callback
            dcc.Graph(id='sensor-graph')
        ], width=9)
    ])
], fluid=True) # fluid=True usa a largura total da tela

# --- 4. CALLBACKS (INTERATIVIDADE) ---
# O callback conecta um ou mais Inputs a um ou mais Outputs.
# Quando o valor do Input muda, a função do callback é executada
# e o valor que ela retorna atualiza o Output.
@app.callback(
    Output('sensor-graph', 'figure'), # Onde o resultado vai (o gráfico)
    [Input('sensor-dropdown', 'value')]  # O que dispara a atualização (o dropdown)
)
def update_graph(selected_sensor):
    """
    Esta função é chamada toda vez que o valor do dropdown muda.
    Ela gera um novo gráfico com base no sensor selecionado.
    """
    print(f"Atualizando gráfico para o sensor: {selected_sensor}")
    
    # Cria a figura (gráfico) usando Plotly Express
    fig = px.line(
        df,
        x='timestamp',
        y=selected_sensor,
        title=f'Histórico do Sensor: {selected_sensor}'
    )
    
    # Melhora a aparência do gráfico
    fig.update_layout(
        template='plotly_dark', # Tema escuro para combinar com o tema SOLAR
        xaxis_title='Tempo',
        yaxis_title=selected_sensor,
        transition_duration=500 # Animação suave na transição
    )
    
    return fig

# --- 5. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    # Usamos app.run com debug=True para desenvolvimento.
    # Ele irá recarregar o servidor automaticamente quando você salvar o arquivo.
    app.run(debug=True)