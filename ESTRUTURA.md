# Estrutura do Projeto

## 📁 Organização de Arquivos

```
projetoFuzzy/
│
├── backend/                    # Backend Python
│   ├── __init__.py
│   ├── server.py              # Servidor FastAPI principal
│   │
│   ├── fuzzy/                 # Módulo de Lógica Fuzzy
│   │   ├── __init__.py
│   │   ├── membership_functions.py  # Funções de pertinência
│   │   ├── rules.py                 # Base de regras fuzzy
│   │   └── mamdani.py               # Motor de inferência Mamdani
│   │
│   ├── simulation/            # Módulo de Simulação
│   │   ├── __init__.py
│   │   ├── physical_model.py   # Modelo físico do data center
│   │   └── simulator.py        # Simulador 24 horas
│   │
│   └── mqtt/                  # Módulo MQTT
│       ├── __init__.py
│       └── client_mqtt.py     # Cliente MQTT
│
├── frontend/                   # Frontend Web
│   ├── index.html             # Interface principal
│   ├── styles.css             # Estilos CSS
│   └── scripts.js             # Lógica JavaScript
│
├── run_server.py              # Script de inicialização
├── requirements.txt           # Dependências Python
├── README.md                  # Documentação principal
├── ESTRUTURA.md              # Este arquivo
└── .gitignore                # Arquivos ignorados pelo Git

```

## 🔄 Fluxo de Funcionamento

### 1. Controle Fuzzy

```
Entradas → Fuzzificação → Avaliação de Regras → Agregação → Defuzzificação → Saída
```

1. **Fuzzificação**: Converte valores numéricos (crisp) em valores fuzzy
2. **Avaliação de Regras**: Identifica regras ativadas e calcula graus de ativação
3. **Agregação**: Combina saídas das regras usando operador MAX
4. **Defuzzificação**: Converte conjunto fuzzy agregado em valor numérico (Centroide)

### 2. Simulação 24 Horas

```
Inicialização → Loop (1440 iterações) → Para cada iteração:
  - Gera temperatura externa (senóide + ruído)
  - Gera carga térmica (perfil diário)
  - Aplica perturbações aleatórias
  - Executa controle fuzzy
  - Atualiza modelo físico
  - Armazena resultados
→ Retorna estatísticas
```

### 3. Comunicação MQTT

```
Eventos do Sistema → Cliente MQTT → Broker MQTT → Tópicos:
  - datacenter/fuzzy/alert
  - datacenter/fuzzy/control
  - datacenter/fuzzy/temp
```

## 🔌 API REST Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Informações da API |
| GET | `/api/health` | Status do sistema |
| POST | `/api/control` | Controle fuzzy com modelo físico |
| POST | `/api/manual-control` | Controle fuzzy com valores manuais |
| POST | `/api/simulation` | Executa simulação 24h |
| GET | `/api/membership` | Dados das funções de pertinência |
| GET | `/api/rules` | Base de regras fuzzy |

## 📊 Componentes Principais

### Backend

- **MamdaniFuzzyController**: Controlador fuzzy principal
- **PhysicalModel**: Modelo físico do data center
- **Simulator24H**: Simulador completo
- **MQTTClient**: Cliente MQTT para comunicação
- **FastAPI Server**: Servidor REST API

### Frontend

- **Interface HTML**: Estrutura da página
- **CSS Moderno**: Design responsivo e moderno
- **JavaScript ES6**: Lógica e integração com API
- **Chart.js**: Visualizações gráficas

## 🎯 Requisitos Atendidos

✅ **RF1**: Sistema Fuzzy Mamdani completo  
✅ **RF2**: Funções de pertinência para todas as variáveis  
✅ **RF3**: Base de regras completa (1.225 regras)  
✅ **RF4**: Sistema MQTT implementado  
✅ **RF5**: Simulação 24h funcional  
✅ **RF6**: Integração com modelo físico  
✅ **RF7**: Interface web completa  

## 🚀 Como Executar

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Iniciar servidor:
```bash
python3 run_server.py
```

3. Abrir frontend:
- Abrir `frontend/index.html` no navegador
- Ou usar servidor HTTP local

4. Acessar API:
- Documentação: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

