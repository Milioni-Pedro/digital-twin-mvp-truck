import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
NUM_SAMPLES_PER_CHASSIS = 10000
SAMPLING_INTERVAL_S = 10
START_DATE = datetime(2025, 1, 1, 8, 0, 0)
CHASSIS_LIST = [
    'CH-A01', # Operador Padrão
    'CH-B02', # Operador de Rota Severa
    'CH-C03', # Veículo mais Antigo
    'CH-D04', # Operador Cuidadoso
    'CH-E05'  # Apresenta falha intermitente
]

user_home = os.path.expanduser("~")
output_folder = os.path.join(user_home, "digital_twin_mvp")
CSV_FILE_PATH = os.path.join(output_folder, "fleet_simulated_data.csv") # Novo nome de arquivo
os.makedirs(output_folder, exist_ok=True)

def generate_chassis_data(chassis_id):
    """Gera um DataFrame de dados para um único chassi com uma personalidade."""
    print(f"Gerando dados para o chassi: {chassis_id}...")
    timestamps = pd.to_datetime([START_DATE + timedelta(seconds=i * SAMPLING_INTERVAL_S) for i in range(NUM_SAMPLES_PER_CHASSIS)])
    df = pd.DataFrame({'timestamp': timestamps, 'chassis_number': chassis_id})

    # Definindo a "personalidade" de cada chassi
    if chassis_id == 'CH-B02': # Rota Severa
        vib_mean, vib_std = 3.5, 1.2
    elif chassis_id == 'CH-D04': # Cuidadoso
        vib_mean, vib_std = 0.9, 0.2
    else: # Padrão
        vib_mean, vib_std = 1.8, 0.6

    df['vibracao_g'] = np.random.normal(vib_mean, vib_std, NUM_SAMPLES_PER_CHASSIS).clip(min=0)
    df['velocidade_kmh'] = 80 + np.random.normal(0, 5, NUM_SAMPLES_PER_CHASSIS)
    df['deformacao_micros'] = 12 * df['vibracao_g'] + np.random.normal(5, 2, NUM_SAMPLES_PER_CHASSIS)
    df['temperatura_C'] = 35 + np.random.normal(0, 2, NUM_SAMPLES_PER_CHASSIS)
    df['radiacao_Wm2'] = 600 + np.random.normal(0, 50, NUM_SAMPLES_PER_CHASSIS)
    df['evento'] = f"Operação {chassis_id}"

    # Adicionando anomalias específicas
    if chassis_id == 'CH-E05': # Falha intermitente
        for i in range(5):
            idx = np.random.randint(0, NUM_SAMPLES_PER_CHASSIS)
            df.loc[idx-5:idx+5, 'vibracao_g'] *= np.random.uniform(1.5, 3)
            df.loc[idx-5:idx+5, 'evento'] = "Anomalia: Falha Intermitente"
            
    return df

if __name__ == "__main__":
    all_chassis_df = []
    for chassis in CHASSIS_LIST:
        df = generate_chassis_data(chassis)
        all_chassis_df.append(df)
    
    fleet_df = pd.concat(all_chassis_df, ignore_index=True)
    
    fleet_df.to_csv(CSV_FILE_PATH, index=False)
    print(f"\nDados da frota completa ({len(fleet_df)} linhas) salvos em: {CSV_FILE_PATH}")
    print("\nAmostra dos dados gerados:")
    print(fleet_df.head())
    print(fleet_df.tail())