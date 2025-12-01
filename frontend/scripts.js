// Configuração da API
const API_BASE_URL = 'http://localhost:8000/api';

// Variáveis globais para gráficos
let membershipCharts = {};
let simulationChart = null;
let aggregationChart = null;
let currentOperationPoints = {}; // Armazena pontos de operação atuais

// Inicialização quando a página carrega
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadMembershipFunctions();
});

// Event Listeners
function initializeEventListeners() {
    document.getElementById('btnControl').addEventListener('click', executeControl);
    document.getElementById('btnSimulation').addEventListener('click', runSimulation);
    document.getElementById('btnReset').addEventListener('click', resetValues);
}

// Carrega e exibe funções de pertinência
async function loadMembershipFunctions() {
    try {
        const response = await fetch(`${API_BASE_URL}/membership`);
        const data = await response.json();
        
        // Cria gráficos para cada variável
        createMembershipChart('errorChart', 'Erro (e)', data.error, ['NG', 'NM', 'NP', 'Z', 'PP', 'PM', 'PG']);
        createMembershipChart('deltaErrorChart', 'Variação do Erro (Δe)', data.delta_error, ['NG', 'NM', 'NP', 'Z', 'PP', 'PM', 'PG']);
        createMembershipChart('tempChart', 'Temperatura Externa (Text)', data.external_temp, ['MB', 'B', 'M', 'A', 'MA']);
        createMembershipChart('loadChart', 'Carga Térmica (Qest)', data.thermal_load, ['MB', 'B', 'M', 'A', 'MA']);
        createMembershipChart('powerChart', 'Potência CRAC (PCRAC)', data.power_crac, ['MB', 'B', 'M', 'A', 'MA']);
    } catch (error) {
        console.error('Erro ao carregar funções de pertinência:', error);
        showAlert('Erro ao carregar funções de pertinência', 'critical');
    }
}

// Cria gráfico de função de pertinência
function createMembershipChart(canvasId, title, data, labels, currentValue = null, fuzzyValues = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    // Cores para os conjuntos fuzzy
    const colors = {
        'NG': '#ef4444', 'NM': '#f59e0b', 'NP': '#eab308', 'Z': '#10b981',
        'PP': '#3b82f6', 'PM': '#6366f1', 'PG': '#8b5cf6',
        'MB': '#ef4444', 'B': '#f59e0b', 'M': '#10b981', 'A': '#3b82f6', 'MA': '#8b5cf6'
    };
    
    const datasets = labels.map(label => ({
        label: label,
        data: data[label],
        borderColor: colors[label] || '#6b7280',
        backgroundColor: (colors[label] || '#6b7280') + '40',
        borderWidth: 2,
        fill: false,
        tension: 0.1
    }));
    
    // Adiciona linha vertical para ponto de operação atual
    if (currentValue !== null && currentValue !== undefined) {
        // Encontra índices mais próximos do valor atual
        const xValues = data.x;
        const closestIndex = xValues.reduce((prev, curr, idx) => 
            Math.abs(curr - currentValue) < Math.abs(xValues[prev] - currentValue) ? idx : prev, 0
        );
        
        // Linha vertical no ponto de operação (cria array com mesmo tamanho)
        const verticalLineData = xValues.map((x, idx) => 
            idx === closestIndex ? 1 : (Math.abs(x - currentValue) < 0.1 ? 0.95 : null)
        );
        
        datasets.push({
            label: `Ponto de Operação: ${currentValue.toFixed(2)}`,
            data: verticalLineData,
            borderColor: '#ff0000',
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false,
            tension: 0
        });
        
        // Adiciona pontos de pertinência ativados
        if (fuzzyValues) {
            Object.keys(fuzzyValues).forEach(label => {
                if (fuzzyValues[label] > 0) {
                    const pointData = xValues.map((x, idx) => 
                        Math.abs(x - currentValue) < 0.1 ? fuzzyValues[label] : null
                    );
                    datasets.push({
                        label: `${label} (${(fuzzyValues[label] * 100).toFixed(1)}%)`,
                        data: pointData,
                        borderColor: colors[label] || '#6b7280',
                        backgroundColor: colors[label] || '#6b7280',
                        pointRadius: 8,
                        pointHoverRadius: 10,
                        showLine: false,
                        tension: 0
                    });
                }
            });
        }
    }
    
    if (membershipCharts[canvasId]) {
        membershipCharts[canvasId].destroy();
    }
    
    membershipCharts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.x,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Valor'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Pertinência'
                    },
                    min: 0,
                    max: 1
                }
            }
        }
    });
}

// Executa controle fuzzy
async function executeControl() {
    const btn = document.getElementById('btnControl');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Processando...';
    
    try {
        // Obtém valores do formulário
        const error = parseFloat(document.getElementById('error').value);
        const deltaError = parseFloat(document.getElementById('deltaError').value);
        const externalTemp = parseFloat(document.getElementById('externalTemp').value);
        const thermalLoad = parseFloat(document.getElementById('thermalLoad').value);
        
        // Obtém setpoint configurado
        const setpoint = parseFloat(document.getElementById('setpoint').value);
        const currentTemp = setpoint - error;
        
        // Chama API de controle manual
        const response = await fetch(`${API_BASE_URL}/manual-control`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                error: error,
                delta_error: deltaError,
                external_temp: externalTemp,
                thermal_load: thermalLoad
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Armazena pontos de operação
        currentOperationPoints = {
            error: error,
            deltaError: deltaError,
            externalTemp: externalTemp,
            thermalLoad: thermalLoad,
            pCrac: result.p_crac
        };
        
        // Atualiza interface
        updateControlResults(result);
        displayActivatedRules(result.activated_rules);
        updateMembershipChartsWithOperationPoints(result.fuzzy_values);
        displayAggregationAndDefuzzification(result);
        
        showAlert('Controle executado com sucesso!', 'info');
        
    } catch (error) {
        console.error('Erro no controle:', error);
        showAlert('Erro ao executar controle: ' + error.message, 'critical');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 Executar Controle';
    }
}

// Atualiza resultados do controle
function updateControlResults(result) {
    document.getElementById('pCrac').textContent = result.p_crac.toFixed(2);
    document.getElementById('errorResult').textContent = result.error.toFixed(2);
    document.getElementById('deltaErrorResult').textContent = result.delta_error.toFixed(2);
    document.getElementById('activatedRules').textContent = result.activated_rules_count;
}

// Exibe regras ativadas
function displayActivatedRules(rules) {
    const rulesList = document.getElementById('rulesList');
    
    if (rules.length === 0) {
        rulesList.innerHTML = '<p class="empty-message">Nenhuma regra ativada</p>';
        return;
    }
    
    // Ordena por grau de ativação (maior primeiro)
    const sortedRules = [...rules].sort((a, b) => b.activation_degree - a.activation_degree);
    
    rulesList.innerHTML = sortedRules.map((ruleData, index) => {
        const rule = ruleData.rule;
        const degree = ruleData.activation_degree;
        
        return `
            <div class="rule-item">
                <strong>Regra ${index + 1}:</strong> 
                IF Erro=${rule.error} AND ΔErro=${rule.delta_error} 
                AND Text=${rule.external_temp} AND Qest=${rule.thermal_load} 
                THEN PCRAC=${rule.output}
                <span class="activation">Ativação: ${(degree * 100).toFixed(1)}%</span>
            </div>
        `;
    }).join('');
}

// Executa simulação de 24 horas
async function runSimulation() {
    const btn = document.getElementById('btnSimulation');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Simulando 24h... (pode levar alguns minutos)';
    
    try {
        const response = await fetch(`${API_BASE_URL}/simulation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                setpoint_temp: parseFloat(document.getElementById('setpoint').value),
                initial_temp: parseFloat(document.getElementById('setpoint').value)
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Exibe gráfico de simulação
        displaySimulationChart(data.results);
        
        // Exibe estatísticas
        displaySimulationStats(data.statistics);
        
        showAlert('Simulação de 24h concluída!', 'info');
        
    } catch (error) {
        console.error('Erro na simulação:', error);
        showAlert('Erro ao executar simulação: ' + error.message, 'critical');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '📊 Rodar Simulação 24h';
    }
}

// Exibe gráfico de simulação
function displaySimulationChart(results) {
    const ctx = document.getElementById('simulationChart');
    if (!ctx) return;
    
    // Prepara dados
    const times = results.map(r => r.time_minutes);
    const temps = results.map(r => r.new_temp);
    const setpoints = results.map(r => r.setpoint_temp);
    const pCracs = results.map(r => r.p_crac);
    const externalTemps = results.map(r => r.external_temp);
    
    if (simulationChart) {
        simulationChart.destroy();
    }
    
    simulationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: times,
            datasets: [
                {
                    label: 'Temperatura do Data Center',
                    data: temps,
                    borderColor: '#ef4444',
                    backgroundColor: '#ef444440',
                    borderWidth: 2,
                    yAxisID: 'y',
                    tension: 0.1
                },
                {
                    label: 'Setpoint',
                    data: setpoints,
                    borderColor: '#10b981',
                    backgroundColor: '#10b98140',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    yAxisID: 'y',
                    tension: 0.1
                },
                {
                    label: 'Temperatura Externa',
                    data: externalTemps,
                    borderColor: '#f59e0b',
                    backgroundColor: '#f59e0b40',
                    borderWidth: 1,
                    yAxisID: 'y',
                    tension: 0.1
                },
                {
                    label: 'Potência CRAC (%)',
                    data: pCracs,
                    borderColor: '#3b82f6',
                    backgroundColor: '#3b82f640',
                    borderWidth: 2,
                    yAxisID: 'y1',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Simulação 24 Horas - Evolução do Sistema',
                    font: {
                        size: 18,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y.toFixed(2);
                            if (context.dataset.label.includes('Potência')) {
                                label += '%';
                            } else {
                                label += '°C';
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Tempo (minutos)'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Temperatura (°C)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Potência CRAC (%)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Exibe estatísticas da simulação
function displaySimulationStats(stats) {
    const statsPanel = document.getElementById('simulationStats');
    
    if (!stats) {
        statsPanel.innerHTML = '';
        return;
    }
    
    statsPanel.innerHTML = `
        <div class="stat-item">
            <div class="stat-label">Temperatura Média</div>
            <div class="stat-value">${stats.temp_mean.toFixed(2)}°C</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Temperatura Mín/Máx</div>
            <div class="stat-value">${stats.temp_min.toFixed(2)}°C / ${stats.temp_max.toFixed(2)}°C</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Erro Médio Absoluto</div>
            <div class="stat-value">${stats.error_mean.toFixed(2)}°C</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Erro Máximo</div>
            <div class="stat-value">${stats.error_max.toFixed(2)}°C</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Potência CRAC Média</div>
            <div class="stat-value">${stats.p_crac_mean.toFixed(2)}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Potência CRAC Mín/Máx</div>
            <div class="stat-value">${stats.p_crac_min.toFixed(2)}% / ${stats.p_crac_max.toFixed(2)}%</div>
        </div>
    `;
}

// Atualiza gráficos de pertinência com pontos de operação
function updateMembershipChartsWithOperationPoints(fuzzyValues) {
    // Recarrega dados de pertinência e atualiza com pontos de operação
    fetch(`${API_BASE_URL}/membership`)
        .then(response => response.json())
        .then(data => {
            createMembershipChart('errorChart', 'Erro (e)', data.error, 
                ['NG', 'NM', 'NP', 'Z', 'PP', 'PM', 'PG'], 
                currentOperationPoints.error, 
                fuzzyValues?.error);
            
            createMembershipChart('deltaErrorChart', 'Variação do Erro (Δe)', data.delta_error, 
                ['NG', 'NM', 'NP', 'Z', 'PP', 'PM', 'PG'], 
                currentOperationPoints.deltaError, 
                fuzzyValues?.delta_error);
            
            createMembershipChart('tempChart', 'Temperatura Externa (Text)', data.external_temp, 
                ['MB', 'B', 'M', 'A', 'MA'], 
                currentOperationPoints.externalTemp, 
                fuzzyValues?.external_temp);
            
            createMembershipChart('loadChart', 'Carga Térmica (Qest)', data.thermal_load, 
                ['MB', 'B', 'M', 'A', 'MA'], 
                currentOperationPoints.thermalLoad, 
                fuzzyValues?.thermal_load);
        })
        .catch(error => console.error('Erro ao atualizar gráficos:', error));
}

// Exibe agregação e defuzzificação
function displayAggregationAndDefuzzification(result) {
    // Gráfico de agregação
    displayAggregationChart(result.aggregated_output, result.p_crac);
    
    // Detalhes da defuzzificação
    displayDefuzzificationDetails(result.aggregated_output, result.p_crac);
}

// Cria gráfico de agregação
function displayAggregationChart(aggregatedOutput, crispOutput) {
    const ctx = document.getElementById('aggregationChart');
    if (!ctx) return;
    
    // Carrega dados da função de saída
    fetch(`${API_BASE_URL}/membership`)
        .then(response => response.json())
        .then(data => {
            const powerData = data.power_crac;
            const labels = ['MB', 'B', 'M', 'A', 'MA'];
            const colors = {
                'MB': '#ef4444', 'B': '#f59e0b', 'M': '#10b981', 
                'A': '#3b82f6', 'MA': '#8b5cf6'
            };
            
            // Cria datasets para cada conjunto fuzzy com grau de agregação
            const datasets = labels.map(label => {
                const degree = aggregatedOutput[label] || 0;
                const originalData = powerData[label].map((y, i) => ({
                    x: powerData.x[i],
                    y: Math.min(y, degree) // Limita pela agregação
                }));
                
                return {
                    label: `${label} (grau: ${(degree * 100).toFixed(1)}%)`,
                    data: originalData,
                    borderColor: colors[label],
                    backgroundColor: colors[label] + '60',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                };
            });
            
            // Adiciona linha vertical para valor crisp (defuzzificado)
            const crispLineData = powerData.x.map(x => 
                Math.abs(x - crispOutput) < 0.5 ? 1 : null
            );
            
            datasets.push({
                label: `Valor Defuzzificado: ${crispOutput.toFixed(2)}%`,
                data: crispLineData,
                borderColor: '#ff0000',
                backgroundColor: 'transparent',
                borderWidth: 3,
                borderDash: [10, 5],
                pointRadius: 0,
                fill: false,
                tension: 0
            });
            
            if (aggregationChart) {
                aggregationChart.destroy();
            }
            
            aggregationChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: powerData.x,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Agregação de Saídas e Defuzzificação',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Potência CRAC (%)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Pertinência'
                            },
                            min: 0,
                            max: 1
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Erro ao criar gráfico de agregação:', error));
}

// Exibe detalhes da defuzzificação
function displayDefuzzificationDetails(aggregatedOutput, crispOutput) {
    const detailsDiv = document.getElementById('defuzzificationDetails');
    
    // Centroides dos conjuntos fuzzy de saída
    const centroids = {
        'MB': 12.5,
        'B': 30.0,
        'M': 50.0,
        'A': 70.0,
        'MA': 90.0
    };
    
    let numerator = 0;
    let denominator = 0;
    const contributions = [];
    
    Object.keys(aggregatedOutput).forEach(label => {
        const degree = aggregatedOutput[label];
        if (degree > 0) {
            const centroid = centroids[label];
            const contribution = centroid * degree;
            numerator += contribution;
            denominator += degree;
            contributions.push({
                label: label,
                centroid: centroid,
                degree: degree,
                contribution: contribution
            });
        }
    });
    
    const calculatedOutput = denominator > 0 ? numerator / denominator : 0;
    
    let html = `
        <div class="defuzz-item">
            <strong>Método:</strong> Centroide (Centroid)
        </div>
        <div class="defuzz-item">
            <strong>Fórmula:</strong> PCRAC = Σ(centroide × grau) / Σ(grau)
        </div>
        <div class="defuzz-calculation">
            <h4>Cálculo:</h4>
            <table class="defuzz-table">
                <thead>
                    <tr>
                        <th>Conjunto</th>
                        <th>Centroide</th>
                        <th>Grau</th>
                        <th>Contribuição</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    contributions.forEach(contrib => {
        html += `
            <tr>
                <td>${contrib.label}</td>
                <td>${contrib.centroid}%</td>
                <td>${(contrib.degree * 100).toFixed(1)}%</td>
                <td>${contrib.contribution.toFixed(2)}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
            <div class="defuzz-result">
                <div class="defuzz-item">
                    <strong>Numerador (Σ):</strong> ${numerator.toFixed(2)}
                </div>
                <div class="defuzz-item">
                    <strong>Denominador (Σ):</strong> ${denominator.toFixed(2)}
                </div>
                <div class="defuzz-item highlight">
                    <strong>PCRAC Calculado:</strong> ${calculatedOutput.toFixed(2)}%
                </div>
                <div class="defuzz-item highlight">
                    <strong>PCRAC Final:</strong> ${crispOutput.toFixed(2)}%
                </div>
            </div>
        </div>
    `;
    
    detailsDiv.innerHTML = html;
}

// Limpa/reseta valores
function resetValues() {
    // Reseta campos de entrada
    document.getElementById('error').value = 0;
    document.getElementById('deltaError').value = 0;
    document.getElementById('externalTemp').value = 25;
    document.getElementById('thermalLoad').value = 50;
    document.getElementById('setpoint').value = 22.0;
    
    // Limpa resultados
    document.getElementById('pCrac').textContent = '--';
    document.getElementById('errorResult').textContent = '--';
    document.getElementById('deltaErrorResult').textContent = '--';
    document.getElementById('activatedRules').textContent = '--';
    
    // Limpa regras ativadas
    document.getElementById('rulesList').innerHTML = 
        '<p class="empty-message">Execute um controle para ver as regras ativadas</p>';
    
    // Limpa agregação e defuzzificação
    if (aggregationChart) {
        aggregationChart.destroy();
        aggregationChart = null;
    }
    document.getElementById('defuzzificationDetails').innerHTML = 
        '<p class="empty-message">Execute um controle para ver os detalhes da defuzzificação</p>';
    
    // Recarrega gráficos de pertinência sem pontos de operação
    currentOperationPoints = {};
    loadMembershipFunctions();
    
    showAlert('Valores resetados com sucesso!', 'info');
}

// Exibe alerta (agora apenas no console, já que o painel foi removido)
function showAlert(message, severity = 'info') {
    // Log no console para debug
    const timestamp = new Date().toLocaleTimeString('pt-BR');
    const logMessage = `[${timestamp}] [${severity.toUpperCase()}] ${message}`;
    
    switch(severity) {
        case 'critical':
        case 'error':
            console.error(logMessage);
            break;
        case 'warning':
            console.warn(logMessage);
            break;
        default:
            console.log(logMessage);
    }
}

