import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
NUM_SAMPLES = 10000
SAMPLING_INTERVAL_S = 10
START_DATE = datetime(2025, 8, 20, 8, 0, 0)

# Define o caminho de saída de forma robusta, usando a pasta home do usuário
# Isso evita problemas com a troca de <MEU_USUARIO>
user_home = os.path.expanduser("~")
output_folder = os.path.join(user_home, "digital_twin_mvp")
CSV_FILE_PATH = os.path.join(output_folder, "sunvisor_simulated_data.csv")

# Garante que a pasta de saída existe
os.makedirs(output_folder, exist_ok=True)


# --- FUNÇÃO PRINCIPAL ---
def generate_data():
    """
    Gera dados simulados de sensores para um componente de caminhão.
    Inclui condições normais de operação e eventos anômalos.
    """
    print("Iniciando a geração de dados simulados...")

    # 1. Gerar Timestamps
    timestamps = pd.to_datetime([START_DATE + timedelta(seconds=i * SAMPLING_INTERVAL_S) for i in range(NUM_SAMPLES)])

    # 2. Gerar Dados Base (Operação Normal)
    # Simula um ciclo diário de temperatura e radiação
    time_of_day_effect = np.sin(np.linspace(0, 4 * np.pi, NUM_SAMPLES)) 

    temperatura_c = 25 + 15 * time_of_day_effect + np.random.normal(0, 1.5, NUM_SAMPLES)
    radiacao_wm2 = 500 + 450 * time_of_day_effect.clip(min=0) + np.random.normal(0, 25, NUM_SAMPLES)
    radiacao_wm2 = radiacao_wm2.clip(min=0) # Radiação não pode ser negativa
    
    # Simula períodos de movimento (velocidade > 0) e paradas
    velocidade_kmh = np.zeros(NUM_SAMPLES)
    for i in range(5): # 5 ciclos de viagem
        start, end = int(NUM_SAMPLES * i/5), int(NUM_SAMPLES * (i+0.7)/5)
        velocidade_kmh[start:end] = 80 + np.random.normal(0, 10, end-start)
    velocidade_kmh = np.convolve(velocidade_kmh, np.ones(50)/50, mode='same').clip(min=0, max=100)
    
    # Vibração e deformação dependem da velocidade
    vibracao_g = (velocidade_kmh / 80) * 1.5 + np.random.normal(0, 0.2, NUM_SAMPLES)
    deformacao_micros = (velocidade_kmh / 80) * 50 + (temperatura_c / 40) * 10 + np.random.normal(0, 5, NUM_SAMPLES)
    vibracao_g = vibracao_g.clip(min=0)
    deformacao_micros = deformacao_micros.clip(min=0)

    # 3. Injetar Anomalias Realistas
    print("Injetando anomalias...")
    # Anomalia 1: Impacto severo (buraco na pista)
    impact_index = int(NUM_SAMPLES * 0.2)
    vibracao_g[impact_index : impact_index + 3] = np.random.uniform(8, 12, 3)
    deformacao_micros[impact_index : impact_index + 3] = np.random.uniform(200, 300, 3)

    # Anomalia 2: Superaquecimento com caminhão parado sob o sol
    heat_start, heat_end = int(NUM_SAMPLES * 0.5), int(NUM_SAMPLES * 0.52)
    velocidade_kmh[heat_start:heat_end] = 0
    temperatura_c[heat_start:heat_end] += np.linspace(0, 25, heat_end-heat_start) # Aumenta 25°C
    deformacao_micros[heat_start:heat_end] += np.linspace(0, 80, heat_end-heat_start) # Dilatação térmica

    # Anomalia 3: Falha temporária do sensor de vibração (valor travado em zero)
    sensor_fail_start, sensor_fail_end = int(NUM_SAMPLES * 0.8), int(NUM_SAMPLES * 0.81)
    vibracao_g[sensor_fail_start:sensor_fail_end] = 0

    # 4. Montar o DataFrame e Salvar
    df = pd.DataFrame({
        'timestamp': timestamps,
        'temperatura_C': temperatura_c.round(2),
        'vibracao_g': vibracao_g.round(3),
        'radiacao_Wm2': radiacao_wm2.round(1),
        'velocidade_kmh': velocidade_kmh.round(1),
        'deformacao_micros': deformacao_micros.round(2)
    })

    print(f"Salvando dados em: {CSV_FILE_PATH}")
    df.to_csv(CSV_FILE_PATH, index=False)

    print("\nDados gerados com sucesso! 5 primeiras linhas:")
    print(df.head())
    
    return df

if __name__ == "__main__":
    generate_data()