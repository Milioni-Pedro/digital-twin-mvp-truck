import json
import os
import time
import numpy as np

script_dir = os.path.dirname(__file__)
input_path = os.path.join(script_dir, "input_fea.json")
output_path = os.path.join(script_dir, "output_fea.json")

def run_mock_simulation():
    with open(input_path, 'r') as f:
        inputs = json.load(f)

    analysis_type = inputs.get("analysis_type", "fadiga")
    print(f"[MOCK FEA] Recebido pedido de análise do tipo: {analysis_type}")
    time.sleep(1.5)
    
    output_data = {}

    # --- MUDANÇA PRINCIPAL: Lógica para cada tipo de análise ---
    if analysis_type == "estatico":
        peak_strain = inputs.get("peak_deformacao_micros", 0)
        # Simula um cálculo de Fator de Segurança para um pico de carga
        max_allowed_strain = 1500 # Limite de escoamento em microstrain
        safety_factor = max_allowed_strain / peak_strain if peak_strain > 0 else 999
        output_data = {
            "tipo_analise": "Análise Estática",
            "fator_seguranca_estatico": round(safety_factor, 2),
            "pico_deformacao_medido": f"{peak_strain:.1f} µs"
        }

    elif analysis_type == "fadiga":
        avg_vib = inputs.get("avg_vibracao_g", 0)
        # Simula um cálculo de dano relativo (proxy para vida)
        base_damage_rate = 1.0
        damage_rate = base_damage_rate * (avg_vib / 2.0)**2 # Dano cresce com o quadrado da vibração
        output_data = {
            "tipo_analise": "Análise de Fadiga",
            "taxa_dano_relativa": f"{damage_rate:.2f}x (vs. Normal)",
            "vibracao_g_media_periodo": f"{avg_vib:.2f} g"
        }

    elif analysis_type == "modal":
        # Simula uma análise de frequência (FFT)
        natural_frequency_hz = 18.0 # Frequência natural crítica do componente (do FEA Modal de projeto)
        dominant_frequency_hz = inputs.get("dominant_freq_hz", 0)
        freq_diff = abs(natural_frequency_hz - dominant_frequency_hz)
        risk = "Baixo"
        if freq_diff < 5.0: risk = "Médio"
        if freq_diff < 2.0: risk = "ALTO (Risco de Ressonância!)"
        output_data = {
            "tipo_analise": "Análise Modal",
            "freq_natural_projeto": f"{natural_frequency_hz} Hz",
            "freq_dominante_operacao": f"{dominant_frequency_hz:.1f} Hz",
            "risco_ressonancia": risk
        }
        
    output_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)
    
    print(f"[MOCK FEA] Análise '{analysis_type}' concluída.")

if __name__ == "__main__":
    run_mock_simulation()