import pandas as pd
import numpy as np
import os

# --- 1. CONFIGURAÇÕES E PARÂMETROS DO MODELO DE FADIGA ---

# --- MUDANÇA PRINCIPAL: Contextualização para Durabilidade ---
# AVISO: Estes parâmetros são o PONTO DE CALIBRAÇÃO com o FEA de durabilidade.
# O processo é:
# 1. Rodar um perfil de carga (ex: 8h de dados) no software de FEA e obter o dano total (a "Verdade").
# 2. Rodar o mesmo perfil de 8h neste script.
# 3. Ajustar os coeficientes W_... e TOTAL_LIFE_UNITS até que o resultado deste script
#    seja o mais próximo possível do resultado do FEA.
# --------------------------------------------------------------------

# TOTAL_LIFE_UNITS: Representa o dano total que o componente suporta até a falha.
# Este valor é diretamente derivado das análises de fadiga (curva S-N do material).
TOTAL_LIFE_UNITS = 5_000_000 

# Pesos para cada sensor na fórmula de dano por fadiga.
W_VIBRATION = 2.0  # Vibração é o principal fator de dano em fadiga.
W_DEFORMATION = 0.5 # Deformação contribui, mas é correlacionada com a vibração.
W_TEMP = 0.2       # Temperatura acelera a degradação do material.
TEMP_BASELINE_C = 25.0

user_home = os.path.expanduser("~")
project_folder = os.path.join(user_home, "digital_twin_mvp")
input_csv_path = os.path.join(project_folder, "sunvisor_simulated_data.csv")
output_csv_path = os.path.join(project_folder, "life_estimate.csv")

def calculate_fatigue_life(df_input):
    print("Iniciando cálculo de consumo de vida por fadiga...")
    df = df_input.copy()

    temp_damage_factor = (df['temperatura_C'] - TEMP_BASELINE_C).clip(lower=0)

    # Fórmula de Dano por Fadiga (Proxy da Regra de Miner)
    fatigue_damage_increment = (
        W_VIBRATION * df['vibracao_g']**2 +
        W_DEFORMATION * df['deformacao_micros'] +
        W_TEMP * temp_damage_factor
    )
    df['fatigue_damage_increment'] = fatigue_damage_increment
    df['fatigue_damage_cumulative'] = df['fatigue_damage_increment'].cumsum()

    df['life_used_percent'] = (df['fatigue_damage_cumulative'] / TOTAL_LIFE_UNITS) * 100
    df['life_used_percent'] = df['life_used_percent'].clip(upper=100)
    df['life_remaining_percent'] = 100 - df['life_used_percent']

    print("Cálculo de fadiga finalizado.")
    return df[['timestamp', 'evento', 'fatigue_damage_increment', 'fatigue_damage_cumulative', 'life_used_percent', 'life_remaining_percent']]

if __name__ == "__main__":
    try:
        df_sensors = pd.read_csv(input_csv_path)
        df_life = calculate_fatigue_life(df_sensors)
        df_life.to_csv(output_csv_path, index=False)
        print(f"Arquivo de estimativa de vida salvo em: {output_csv_path}")
        print("\nÚltimas 5 entradas do cálculo de vida:")
        print(df_life.tail())
    except FileNotFoundError:
        print(f"ERRO: Arquivo de entrada '{input_csv_path}' não encontrado. Execute 'generate_data.py' primeiro.")