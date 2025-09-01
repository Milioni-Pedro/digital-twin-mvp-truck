import pandas as pd
import numpy as np
import os

# --- CONFIGURAÇÕES E PARÂMETROS DO MODELO DE FADIGA ---
TOTAL_LIFE_UNITS = 5_000_000 
W_VIBRATION = 2.0
W_DEFORMATION = 0.5
W_TEMP = 0.2
TEMP_BASELINE_C = 25.0

user_home = os.path.expanduser("~")
project_folder = os.path.join(user_home, "digital_twin_mvp")
input_csv_path = os.path.join(project_folder, "fleet_simulated_data.csv") # Ler o novo arquivo
output_csv_path = os.path.join(project_folder, "fleet_life_estimate.csv") # Novo arquivo de saída

def calculate_fatigue_life(df_group):
    """Aplica o cálculo de vida a um grupo de dados (um único chassi)."""
    df = df_group.copy()
    
    # Adiciona um desgaste inicial para o "veículo antigo"
    initial_damage = 0
    if df['chassis_number'].iloc[0] == 'CH-C03':
        initial_damage = TOTAL_LIFE_UNITS * 0.4 # Começa com 40% da vida consumida
        
    temp_damage_factor = (df['temperatura_C'] - TEMP_BASELINE_C).clip(lower=0)
    
    fatigue_damage_increment = (
        W_VIBRATION * df['vibracao_g']**2 +
        W_DEFORMATION * df['deformacao_micros'] +
        W_TEMP * temp_damage_factor
    )
    df['fatigue_damage_cumulative'] = fatigue_damage_increment.cumsum() + initial_damage

    df['life_used_percent'] = (df['fatigue_damage_cumulative'] / TOTAL_LIFE_UNITS) * 100
    df['life_used_percent'] = df['life_used_percent'].clip(upper=100)
    df['life_remaining_percent'] = 100 - df['life_used_percent']

    return df

if __name__ == "__main__":
    try:
        fleet_df = pd.read_csv(input_csv_path)
        print("Calculando estimativa de vida para toda a frota...")
        
        # --- MUDANÇA PRINCIPAL: Usar groupby para calcular por chassi ---
        fleet_life_df = fleet_df.groupby('chassis_number', group_keys=False).apply(calculate_fatigue_life)
        
        fleet_life_df.to_csv(output_csv_path, index=False)
        print(f"Arquivo de estimativa de vida da frota salvo em: {output_csv_path}")
        
        print("\nÚltimos dados de vida para cada chassi:")
        print(fleet_life_df.groupby('chassis_number').tail(1))

    except FileNotFoundError:
        print(f"ERRO: Arquivo de entrada '{input_csv_path}' não encontrado. Execute 'generate_data.py' primeiro.")