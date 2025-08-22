import json
import os
import time

# Caminhos relativos ao script
script_dir = os.path.dirname(__file__)
input_path = os.path.join(script_dir, "input_fea.json")
output_path = os.path.join(script_dir, "output_fea.json")

def run_mock_simulation():
    """
    Lê as condições de carga, calcula um resultado 'tipo FEA' e salva.
    """
    print("[MOCK FEA] Lendo condições de carga...")
    with open(input_path, 'r') as f:
        inputs = json.load(f)

    avg_temp = inputs.get("avg_temp_C", 20.0)
    max_vib = inputs.get("max_vibracao_g", 0.0)

    print(f"[MOCK FEA] Condições: Temp={avg_temp}°C, Vib={max_vib}g")
    print("[MOCK FEA] Simulando...")
    time.sleep(2) # Finge que está fazendo um cálculo pesado

    # Lógica determinística simples para simular o resultado do FEA
    # Tensão base + efeito da vibração + efeito da dilatação térmica
    base_stress_mpa = 50
    stress_from_vibration = max_vib * 15 
    stress_from_temp = (avg_temp - 20) * 0.5 if avg_temp > 20 else 0
    
    max_stress_mpa = base_stress_mpa + stress_from_vibration + stress_from_temp
    
    # Fator de segurança (Safety Factor)
    yield_strength_mpa = 250 # Limite de escoamento do material (ex: Alumínio)
    safety_factor = yield_strength_mpa / max_stress_mpa if max_stress_mpa > 0 else 999

    output_data = {
        "max_stress_von_mises_MPa": round(max_stress_mpa, 2),
        "safety_factor": round(safety_factor, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    print(f"[MOCK FEA] Resultado: Tensão Máxima = {output_data['max_stress_von_mises_MPa']} MPa")
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)
    
    print("[MOCK FEA] Simulação concluída.")

if __name__ == "__main__":
    run_mock_simulation()