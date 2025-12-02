# Sistema de Controle Fuzzy para Centro de Dados

Sistema completo de controle fuzzy MISO (Multiple Input Single Output) para controle de temperatura em data center, implementado em Python (backend) e HTML5/CSS3/JavaScript (frontend).

## 📋 Descrição

Este projeto implementa um controlador fuzzy tipo Mamdani para gerenciar a temperatura de um data center através do controle da potência do sistema CRAC (Computer Room Air Conditioning). O sistema utiliza lógica fuzzy para tomar decisões inteligentes baseadas em múltiplas variáveis de entrada.

## 🎯 Objetivos

- Implementar controlador fuzzy tipo Mamdani com 4 entradas e 1 saída
- Desenvolver funções de pertinência para todas as variáveis
- Criar base de regras fuzzy completa e consistente
- Implementar simulação de 24 horas com modelo físico
- Integrar comunicação MQTT para alertas e monitoramento
- Fornecer interface web moderna e responsiva

## 🏗️ Arquitetura do Sistema

### Backend (Python)

```
backend/
├── fuzzy/
│   ├── membership_functions.py  # Funções de pertinência
│   ├── rules.py                 # Base de regras fuzzy
│   └── mamdani.py               # Motor de inferência Mamdani
├── simulation/
│   ├── physical_model.py        # Modelo físico do data center
│   └── simulator.py             # Simulador 24 horas
├── mqtt/
│   └── client_mqtt.py           # Cliente MQTT
└── server.py                    # Servidor FastAPI
```

### Frontend (HTML/CSS/JS)

```
frontend/
├── index.html      # Interface principal
├── styles.css      # Estilos modernos e responsivos
└── scripts.js      # Lógica JavaScript e integração com API
```

## 🔧 Variáveis do Sistema

### Entradas (4 variáveis)

1. **Erro (e)** [°C]
   - Range: -10 a 10 °C
   - Conjuntos fuzzy: NG, NM, NP, Z, PP, PM, PG
   - Funções: Triangulares e trapezoidais

2. **Variação do Erro (Δe)** [°C]
   - Range: -10 a 10 °C (similar ao erro)
   - Conjuntos fuzzy: NG, NM, NP, Z, PP, PM, PG
   - Funções: Triangulares e trapezoidais

3. **Temperatura Externa (Text)** [°C]
   - Range: 18 a 32 °C (centrado em 25°C - RF2 obrigatório)
   - Conjuntos fuzzy: MB, B, M, A, MA
   - Funções: Triangulares e trapezoidais

4. **Carga Térmica (Qest)** [%]
   - Range: 0 a 80 % (centrado em 40% - RF2 obrigatório)
   - Conjuntos fuzzy: MB, B, M, A, MA
   - Funções: Triangulares e trapezoidais

### Saída (1 variável)

1. **Potência CRAC (PCRAC)** [%]
   - Range: 0 a 100%
   - Conjuntos fuzzy: MB, B, M, A, MA
   - Funções: Triangulares e trapezoidais
   - Defuzzificação: Método do Centroide

## 📐 Funções de Pertinência

### Erro (e)

- **NG (Negativo Grande)**: Trapezoidal [-10, -10, -7, -4]
- **NM (Negativo Médio)**: Triangular [-7, -4, -1]
- **NP (Negativo Pequeno)**: Triangular [-4, -1, 0]
- **Z (Zero)**: Triangular [-1, 0, 1]
- **PP (Positivo Pequeno)**: Triangular [0, 1, 4]
- **PM (Positivo Médio)**: Triangular [1, 4, 7]
- **PG (Positivo Grande)**: Trapezoidal [4, 7, 10, 10]

### Variação do Erro (Δe)

- **NG (Negativo Grande)**: Trapezoidal [-10, -10, -7, -4]
- **NM (Negativo Médio)**: Triangular [-7, -4, -1]
- **NP (Negativo Pequeno)**: Triangular [-4, -1, 0]
- **Z (Zero)**: Triangular [-1, 0, 1]
- **PP (Positivo Pequeno)**: Triangular [0, 1, 4]
- **PM (Positivo Médio)**: Triangular [1, 4, 7]
- **PG (Positivo Grande)**: Trapezoidal [4, 7, 10, 10]

### Temperatura Externa (Text)

- **MB (Muito Baixa)**: Trapezoidal [18, 18, 20, 22]
- **B (Baixa)**: Triangular [20, 22, 24]
- **M (Média)**: Triangular [23, 25, 27] (centrada em 25°C)
- **A (Alta)**: Triangular [25, 27, 29]
- **MA (Muito Alta)**: Trapezoidal [27, 29, 32, 32]

### Carga Térmica (Qest)

- **MB**: Trapezoidal [0, 0, 10, 20]
- **B**: Triangular [15, 25, 35]
- **M**: Triangular [30, 40, 50] (centrada em 40%)
- **A**: Triangular [45, 55, 65]
- **MA**: Trapezoidal [60, 70, 80, 80]

### Potência CRAC (PCRAC)

- **MB**: Trapezoidal [0, 0, 15, 25] → Centroide: 12.5%
- **B**: Triangular [15, 25, 40] → Centroide: 30%
- **M**: Triangular [25, 40, 60] → Centroide: 50%
- **A**: Triangular [40, 60, 80] → Centroide: 70%
- **MA**: Trapezoidal [60, 80, 100, 100] → Centroide: 90%

## 📜 Base de Regras Fuzzy

O sistema possui uma base de regras completa com **1.225 regras** (7 × 7 × 5 × 5), cobrindo todas as combinações possíveis de entradas.

### Estrutura das Regras

Formato: `IF (Erro, ΔErro, TempExterna, CargaTermica) THEN PotenciaCRAC`

### Estratégia de Regras

1. **Erro Negativo Grande (NG)**: Reduz potência drasticamente (MB ou B)
2. **Erro Negativo Médio (NM)**: Reduz potência moderadamente (MB ou B)
3. **Erro Negativo Pequeno (NP)**: Ajusta potência levemente (B ou M)
4. **Erro Zero (Z)**: Mantém potência baseada em carga e temperatura externa
5. **Erro Positivo Pequeno (PP)**: Aumenta potência levemente (A)
6. **Erro Positivo Médio (PM)**: Aumenta potência moderadamente (A ou MA)
7. **Erro Positivo Grande (PG)**: Aumenta potência drasticamente (MA)

A variação do erro (Δe) modula a resposta, enquanto temperatura externa e carga térmica ajustam o nível base de potência.

## 🔄 Motor de Inferência Mamdani

O sistema implementa o motor de inferência fuzzy tipo Mamdani com 4 fases:

1. **Fuzzificação**: Converte valores crisp em valores fuzzy
2. **Avaliação de Regras**: Identifica regras ativadas e calcula graus de ativação
3. **Agregação**: Combina saídas usando operador MAX (união)
4. **Defuzzificação**: Converte conjunto fuzzy agregado em valor crisp usando método do Centroide

## 🌡️ Modelo Físico

O modelo físico do data center é baseado na equação:

```
T[n+1] = 0.9*T[n] - 0.08*PCRAC + 0.05*Qest + 0.02*Text + 3.5
```

Onde:
- `T[n+1]`: Temperatura no próximo instante
- `T[n]`: Temperatura atual
- `PCRAC`: Potência do CRAC (0-100%)
- `Qest`: Carga térmica (kW)
- `Text`: Temperatura externa (°C)

## 📡 Comunicação MQTT

O sistema publica em três tópicos MQTT:

1. **datacenter/fuzzy/alert**: Alertas críticos do sistema
2. **datacenter/fuzzy/control**: Informações de controle
3. **datacenter/fuzzy/temp**: Temperatura atual

### Configuração MQTT

- **Broker**: broker.com:8000/mqtt
- **QoS**: 1 (pelo menos uma vez)
- **Formato**: JSON

## 🚀 Instalação e Execução

### Pré-requisitos

- Python 3.8 ou superior
- Navegador web moderno (Chrome, Firefox, Edge)

### Instalação

1. Clone o repositório ou navegue até o diretório do projeto:
```bash
cd projetoFuzzy
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

### Execução

1. Inicie o servidor backend (a partir da raiz do projeto):
```bash
python3 run_server.py
```

Ou, se preferir executar diretamente:
```bash
cd backend
python3 server.py
```

O servidor estará disponível em `http://localhost:8000`

2. Abra o frontend:
   - Abra o arquivo `frontend/index.html` no navegador
   - Ou use um servidor HTTP local (ex: `python3 -m http.server` na pasta frontend)

3. Acesse a interface:
   - Se usar servidor HTTP: `http://localhost:8000` (ou porta configurada)
   - Se abrir diretamente: caminho do arquivo `index.html`

## 📊 Funcionalidades da Interface

### Controle Manual
- Entrada manual de valores para Erro, ΔErro, Temperatura Externa e Carga Térmica
- Execução do controle fuzzy em tempo real
- Visualização da potência CRAC calculada

### Visualização de Funções de Pertinência
- Gráficos interativos de todas as funções de pertinência
- Visualização usando Chart.js

### Regras Ativadas
- Lista de regras ativadas em cada execução
- Grau de ativação de cada regra
- Ordenação por relevância

### Simulação 24 Horas
- Execução completa de simulação (1440 iterações)
- Gráfico de evolução da temperatura
- Gráfico de potência CRAC
- Estatísticas da simulação

### Alertas MQTT
- Painel de alertas em tempo real
- Classificação por severidade (info, warning, critical)

## 🔌 API REST

### Endpoints Disponíveis

- `GET /`: Informações sobre a API
- `GET /api/health`: Verificação de saúde do sistema
- `POST /api/control`: Executa controle fuzzy
- `POST /api/manual-control`: Controle com valores manuais
- `POST /api/simulation`: Executa simulação de 24 horas
- `GET /api/membership`: Retorna dados das funções de pertinência
- `GET /api/rules`: Retorna base de regras

## 📈 Simulação 24 Horas

A simulação executa 1440 iterações (uma por minuto) com:

- **Variação de temperatura externa**: Senóide com ruído gaussiano
- **Perfil de carga térmica**: Variação diária (baixa à noite, alta durante dia)
- **Perturbações aleatórias**: Eventos raros simulando condições reais
- **Modelo físico**: Equação de dinâmica térmica aplicada a cada iteração

## 🧪 Validação

O sistema foi validado através de:

1. **Testes de funções de pertinência**: Verificação de valores de pertinência
2. **Testes de regras**: Validação de ativação de regras
3. **Simulação 24h**: Validação de comportamento ao longo do tempo
4. **Testes de integração**: Verificação de comunicação MQTT e API


## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.8+**
- **FastAPI**: Framework web moderno e rápido
- **NumPy**: Cálculos numéricos
- **paho-mqtt**: Cliente MQTT
- **Pydantic**: Validação de dados

### Frontend
- **HTML5**: Estrutura semântica
- **CSS3**: Estilos modernos e responsivos
- **JavaScript ES6**: Lógica e interatividade
- **Chart.js**: Gráficos 

