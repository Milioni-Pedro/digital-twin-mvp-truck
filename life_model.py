import pandas as pd
import numpy as np
import os

# --- 1. CONFIGURAÇÕES E PARÂMETROS DO MODELO ---

# Este é o "limite de falha". É um valor abstrato que representa
# a quantidade total de dano que o componente pode suportar.
# Em um projeto real, este valor seria calibrado com testes de bancada ou dados de campo.
TOTAL_LIFE_UNITS = 1_000_000 

# Pesos para cada sensor na fórmula de dano.
# A ideia é que vibração e deformação são os principais causadores de dano por fadiga,
# enquanto a temperatura acelera o processo.
# Estes também são valores empíricos que precisariam de calibração.
W_VIBRATION = 1.5
W_DEFORMATION = 1.0
W_TEMP = 0.8
TEMP_BASELINE_C = 20.0 # Dano por temperatura só é considerado acima desta linha de base

# Caminhos dos arquivos
user_home = os.path.expanduser("~")
project_folder = os.path.join(user_home, "digital_twin_mvp")
input_csv_path = os.path.join(project_folder, "sunvisor_simulated_data.csv")
output_csv_path = os.path.join(project_folder, "life_estimate.csv")

# --- 2. FUNÇÃO DE CÁLCULO DE DANO ---

def calculate_life_estimate(df_input):
    """
    Calcula o dano incremental e cumulativo com base nos dados dos sensores.
    """
    print("Iniciando cálculo de estimativa de vida útil...")
    df = df_input.copy()

    # Normaliza a temperatura para que apenas valores acima da linha de base contribuam para o dano
    temp_damage_factor = (df['temperatura_C'] - TEMP_BASELINE_C).clip(lower=0)

    # Fórmula de Dano Incremental (Miner Simplificado)
    # Esta é a "lógica de negócio" do nosso modelo de vida.
    damage_increment = (
        W_VIBRATION * df['vibracao_g']**2 +          # Dano por vibração (exponencial)
        W_DEFORMATION * df['deformacao_micros'] +   # Dano linear por deformação
        W_TEMP * temp_damage_factor                 # Dano acelerado pela temperatura
    )
    df['damage_increment'] = damage_increment

    # Calcula o dano cumulativo
    df['damage_cumulative'] = df['damage_increment'].cumsum()

    # Calcula as porcentagens de vida
    df['life_used_percent'] = (df['damage_cumulative'] / TOTAL_LIFE_UNITS) * 100
    df['life_used_percent'] = df['life_used_percent'].clip(upper=100) # Não pode passar de 100%
    df['life_remaining_percent'] = 100 - df['life_used_percent']

    print("Cálculo finalizado com sucesso.")
    return df[['timestamp', 'damage_increment', 'damage_cumulative', 'life_used_percent', 'life_remaining_percent']]

# --- 3. EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    try:
        df_sensors = pd.read_csv(input_csv_path)
        df_life = calculate_life_estimate(df_sensors)
        
        df_life.to_csv(output_csv_path, index=False)
        print(f"Arquivo de estimativa de vida salvo em: {output_csv_path}")
        
        print("\nÚltimas 5 entradas do cálculo de vida:")
        print(df_life.tail())

    except FileNotFoundError:
        print(f"ERRO: Arquivo de entrada '{input_csv_path}' não encontrado. Execute 'generate_data.py' primeiro.")