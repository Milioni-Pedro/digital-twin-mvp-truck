# MVP de Gêmeo Digital para Gestão de Frotas e Análise de Durabilidade

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Dash](https://img.shields.io/badge/Dash-2.17-blue?logo=plotly)
![Scikit-learn](https://img.shields.io/badge/SciKit--Learn-1.3+-orange?logo=scikit-learn)
![License](https://img.shields.io/badge/License-MIT-green)

Este projeto é um MVP (Minimum Viable Product) funcional de um Gêmeo Digital, agora evoluído para uma plataforma de **gestão de frotas**. O sistema monitora, compara e analisa a saúde de múltiplos veículos (chassis), com foco em **durabilidade e prognóstico de falhas por fadiga**.

Inspirado em plataformas de telemetria e análise de ativos, o objetivo é demonstrar um fluxo completo: desde a geração de dados para uma frota com diferentes perfis operacionais, até um dashboard interativo que permite a **análise comparativa** entre os veículos, identificando os ativos de maior risco e fornecendo insights para manutenção preditiva e desenvolvimento de produtos.

## 📸 Screenshot do Painel de Frota

*(Dica: Rode o painel, selecione 2 ou 3 chassis diferentes para exibir múltiplas linhas no gráfico, tire um print screen e salve como `dashboard_fleet.png` dentro da pasta `img`)*

![Screenshot do Painel de Frota](img/dashboard_fleet.png)

## ✨ Principais Funcionalidades

-   **Geração de Dados Sintéticos para uma Frota**: Criação de um dataset para 5 chassis, cada um com uma "personalidade" única (operação severa, operador cuidadoso, veículo antigo, etc.), simulando perfis de uso realistas.
-   **Dashboard Interativo com Visualização Comparativa**: A interface web agora permite selecionar múltiplos chassis, exibindo seus dados em linhas coloridas separadas no mesmo gráfico para comparação direta de desempenho e desgaste.
-   **Análise de Saúde por Ativo**: O modelo de vida por fadiga é aplicado individualmente a cada chassi, permitindo que o painel exiba a saúde específica do veículo selecionado.
-   **Detecção de Anomalias Pontuais**: O sistema continua identificando eventos extremos (como impactos) que se destacam do desgaste normal por fadiga.
-   **Ciclo de Retroalimentação com Simulação FEA**: A plataforma mantém a capacidade de realizar análises "what-if" (Estática, Fadiga, Modal) com base nos dados do chassi selecionado.

## 📁 Estrutura do Projeto

```
C:\Users\<SEU_USUARIO>\digital_twin_mvp\
│  README.md
│  .gitignore
│  requirements.txt
│  fleet_simulated_data.csv  <- NOVO
│  fleet_life_estimate.csv   <- NOVO
│  main_dashboard.py
│  life_model.py
│  generate_data.py
│
├─fea\
│  │  input_fea.json
│  │  output_fea.json
│  └  mock_fea_solver.py
│
└─img\
   └  dashboard_fleet.png
```

## 🛠️ Tecnologias Utilizadas

-   **Linguagem**: Python 3.10+
-   **Bibliotecas Principais**:
    -   `pandas` e `numpy` para manipulação de dados.
    -   `scikit-learn` para detecção de anomalias.
    -   `dash`, `plotly` e `dash-bootstrap-components` para o painel web.

## 🚀 Instalação e Execução

Siga os passos abaixo para rodar a nova versão do projeto.

**1. Clone o Repositório (se ainda não o fez):**
```bash
git clone https://github.com/Milioni-Pedro/digital-twin-mvp-truck.git
cd C:\Users\a350748\digital_twin_mvp
```

**2. Crie e Ative o Ambiente Virtual:**
```powershell
# Crie o ambiente
python -m venv .venv

# Ative o ambiente no PowerShell
.\.venv\Scripts\Activate
```

**3. Instale as Dependências:**
```bash
pip install -r requirements.txt
```

**4. Execute o Projeto (em ordem):**
A sequência é crucial para gerar os arquivos de dados da frota.

   **a. Gere os dados da frota:**
   ```bash
   python generate_data.py
   ```
   *Isso cria o `fleet_simulated_data.csv`.*

   **b. Calcule a estimativa de vida para a frota:**
   ```bash
   python life_model.py
   ```
   *Isso cria o `fleet_life_estimate.csv`.*

   **c. Inicie o Painel de Gestão de Frota:**
   ```bash
   python main_dashboard.py
   ```
   
**5. Acesse o Painel:**
   Abra seu navegador e acesse a URL: [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

## 📈 Plano de Evolução

Com a base de gestão de frotas estabelecida, os próximos passos são:
-   [ ] **Dados Reais**: Integrar com a telemetria real dos chassis via IoT.
-   [ ] **Dashboard de Gestão Agregada**: Criar novas telas, como um mapa de saúde da frota e rankings de veículos por criticidade.
-   [ ] **Hospedagem em Nuvem**: Migrar a aplicação para um serviço como AWS ou Azure para acesso multi-usuário.
-   [ ] **Machine Learning Avançado**: Usar os dados da frota para treinar modelos que possam prever falhas com base no comportamento comparativo entre os veículos.

## 📄 Licença

Distribuído sob a licença MIT.