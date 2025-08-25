import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
NUM_SAMPLES = 10000
SAMPLING_INTERVAL_S = 10
START_DATE = datetime(2025, 8, 20, 8, 0, 0)
user_home = os.path.expanduser("~")
output_folder = os.path.join(user_home, "digital_twin_mvp")
CSV_FILE_PATH = os.path.join(output_folder, "sunvisor_simulated_data.csv")
os.makedirs(output_folder, exist_ok=True)

def generate_road_segment(num_points, road_type):
    """Gera um segmento de dados de vibração para um tipo de pista."""
    if road_type == "Asfalto Liso":
        return np.random.normal(0.8, 0.3, num_points)
    elif road_type == "Paralelepípedo":
        return np.random.normal(2.5, 0.8, num_points)
    elif road_type == "Estrada de Terra":
        return np.random.normal(4.0, 1.5, num_points)
    return np.zeros(num_points)

def generate_data():
    print("Iniciando a geração de dados com foco em perfis de durabilidade...")
    timestamps = pd.to_datetime([START_DATE + timedelta(seconds=i * SAMPLING_INTERVAL_S) for i in range(NUM_SAMPLES)])
    
    df = pd.DataFrame({'timestamp': timestamps})
    df['evento'] = "Operação Normal" # Coluna de eventos criada na fonte
    df['velocidade_kmh'] = 80 + np.random.normal(0, 5, NUM_SAMPLES)
    
    # --- MUDANÇA PRINCIPAL: Simular trechos de diferentes pistas ---
    segment_length = NUM_SAMPLES // 4
    df.loc[0:segment_length, 'evento'] = "Trecho: Asfalto Liso"
    df.loc[segment_length:2*segment_length, 'evento'] = "Trecho: Paralelepípedo"
    df.loc[2*segment_length:3*segment_length, 'evento'] = "Trecho: Estrada de Terra"
    df.loc[3*segment_length:, 'evento'] = "Trecho: Asfalto Liso"
    
    vib_segments = [
        generate_road_segment(segment_length, "Asfalto Liso"),
        generate_road_segment(segment_length, "Paralelepípedo"),
        generate_road_segment(segment_length, "Estrada de Terra"),
        generate_road_segment(NUM_SAMPLES - 3*segment_length, "Asfalto Liso")
    ]
    df['vibracao_g'] = np.concatenate(vib_segments).clip(min=0)
    
    # Outros sensores com base na vibração e velocidade
    df['deformacao_micros'] = 10 * df['vibracao_g'] + np.random.normal(5, 2, NUM_SAMPLES)
    df['temperatura_C'] = 35 + np.random.normal(0, 2, NUM_SAMPLES)
    df['radiacao_Wm2'] = 600 + np.random.normal(0, 50, NUM_SAMPLES)

    # Injetar anomalias pontuais sobre o perfil de fadiga
    impact_index = np.random.randint(segment_length, 2*segment_length)
    df.loc[impact_index, 'vibracao_g'] *= 3 # Impacto severo
    df.loc[impact_index, 'deformacao_micros'] *= 3
    df.loc[impact_index, 'evento'] = "Anomalia: Impacto Severo"
    
    print(f"Salvando dados em: {CSV_FILE_PATH}")
    df.to_csv(CSV_FILE_PATH, index=False)
    print("\nDados de durabilidade gerados! 5 primeiras linhas:")
    print(df.head())

if __name__ == "__main__":
    generate_data()