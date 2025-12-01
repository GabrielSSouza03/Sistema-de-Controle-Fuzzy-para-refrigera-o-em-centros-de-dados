"""
Módulo Simulador 24 Horas
Implementa simulação completa de 24 horas (1440 iterações, 1 minuto cada).
"""

import numpy as np
from datetime import datetime, timedelta
from ..fuzzy.mamdani import MamdaniFuzzyController
from .physical_model import PhysicalModel


class Simulator24H:
    """
    Simulador de 24 horas para o sistema de controle fuzzy.
    
    Características:
    - 1440 iterações (1 minuto cada)
    - Variação automática de temperatura externa (senóide + ruído)
    - Perfil diário de carga térmica
    - Perturbações aleatórias
    """
    
    def __init__(self, setpoint_temp=22.0, initial_temp=22.0):
        """
        Inicializa o simulador.
        
        Args:
            setpoint_temp: Temperatura desejada (setpoint)
            initial_temp: Temperatura inicial do data center
        """
        self.setpoint_temp = setpoint_temp
        self.controller = MamdaniFuzzyController(setpoint_temp=setpoint_temp)
        self.model = PhysicalModel(initial_temp=initial_temp)
        self.results = []
    
    def generate_external_temp(self, iteration, total_iterations):
        """
        Gera temperatura externa variando ao longo do dia.
        Usa senóide com ruído gaussiano.
        
        Args:
            iteration: Iteração atual (0 a 1439)
            total_iterations: Total de iterações (1440)
        
        Returns:
            Temperatura externa em °C
        """
        # Perfil senoidal para simular variação diária
        # Temperatura mais baixa à noite (meia-noite), mais alta à tarde
        hour = (iteration / total_iterations) * 24  # Hora do dia (0-24)
        
        # Senóide: temperatura base 25°C (RF2 obrigatório), amplitude 4°C
        # Mínimo às 6h, máximo às 14h
        base_temp = 25.0
        amplitude = 4.0
        phase = (hour - 6) * (2 * np.pi / 24)  # Desloca para mínimo às 6h
        
        temp = base_temp + amplitude * np.sin(phase)
        
        # Adiciona ruído gaussiano (desvio padrão 1.0°C)
        noise = np.random.normal(0, 1.0)
        temp += noise
        
        # Limita entre 18°C e 32°C (RF2 obrigatório - centrado em 25°C)
        temp = max(18.0, min(32.0, temp))
        
        return temp
    
    def generate_thermal_load(self, iteration, total_iterations):
        """
        Gera carga térmica seguindo perfil diário.
        Maior carga durante horário comercial, menor à noite.
        
        Args:
            iteration: Iteração atual
            total_iterations: Total de iterações
        
        Returns:
            Carga térmica em kW
        """
        hour = (iteration / total_iterations) * 24
        
        # Perfil diário: carga centrada em 40% (RF2 obrigatório)
        # Varia entre 20% e 60% ao longo do dia
        if 0 <= hour < 6:
            # Madrugada: carga baixa
            base_load = 30.0
            amplitude = 10.0
        elif 6 <= hour < 8:
            # Manhã cedo: carga aumentando
            base_load = 40.0
            amplitude = 10.0
        elif 8 <= hour < 18:
            # Horário comercial: carga alta
            base_load = 50.0
            amplitude = 10.0
        elif 18 <= hour < 22:
            # Noite: carga diminuindo
            base_load = 40.0
            amplitude = 10.0
        else:
            # Madrugada: carga baixa
            base_load = 30.0
            amplitude = 10.0
        
        # Adiciona variação senoidal suave
        phase = hour * (2 * np.pi / 24)
        load = base_load + amplitude * np.sin(phase)
        
        # Adiciona perturbações aleatórias
        perturbation = np.random.normal(0, 3.0)
        load += perturbation
        
        # Limita entre 0 e 80 % (RF2 obrigatório - centrado em 40%)
        load = max(0.0, min(80.0, load))
        
        return load
    
    def add_disturbance(self, iteration):
        """
        Adiciona perturbações aleatórias ao sistema.
        Simula eventos como abertura de portas, falhas temporárias, etc.
        
        Args:
            iteration: Iteração atual
        
        Returns:
            Fator de perturbação (multiplicador)
        """
        # Perturbações raras (1% de chance)
        if np.random.random() < 0.01:
            # Perturbação significativa (aumenta carga em 20-40%)
            return 1.0 + np.random.uniform(0.2, 0.4)
        
        # Perturbações menores (5% de chance)
        if np.random.random() < 0.05:
            # Perturbação pequena (aumenta carga em 5-15%)
            return 1.0 + np.random.uniform(0.05, 0.15)
        
        return 1.0
    
    def run(self):
        """
        Executa simulação completa de 24 horas.
        
        Returns:
            Lista de dicionários com resultados de cada iteração
        """
        total_iterations = 1440  # 24 horas * 60 minutos
        self.model.reset(initial_temp=self.setpoint_temp)
        self.controller = MamdaniFuzzyController(setpoint_temp=self.setpoint_temp)
        self.results = []
        
        start_time = datetime.now()
        
        for i in range(total_iterations):
            # Gera entradas variáveis
            external_temp = self.generate_external_temp(i, total_iterations)
            thermal_load = self.generate_thermal_load(i, total_iterations)
            
            # Adiciona perturbações
            disturbance = self.add_disturbance(i)
            thermal_load *= disturbance
            
            # Obtém temperatura atual
            current_temp = self.model.get_current_temp()
            
            # Executa controlador fuzzy
            fuzzy_result = self.controller.compute(
                current_temp=current_temp,
                external_temp=external_temp,
                thermal_load=thermal_load
            )
            
            p_crac = fuzzy_result['p_crac']
            
            # Atualiza modelo físico
            new_temp = self.model.update(
                p_crac=p_crac,
                thermal_load=thermal_load,
                external_temp=external_temp
            )
            
            # Calcula timestamp
            timestamp = start_time + timedelta(minutes=i)
            
            # Armazena resultado
            result = {
                'iteration': i,
                'timestamp': timestamp.isoformat(),
                'time_minutes': i,
                'current_temp': current_temp,
                'new_temp': new_temp,
                'setpoint_temp': self.setpoint_temp,
                'error': fuzzy_result['error'],
                'delta_error': fuzzy_result['delta_error'],
                'external_temp': external_temp,
                'thermal_load': thermal_load,
                'p_crac': p_crac,
                'activated_rules_count': len(fuzzy_result['activated_rules'])
            }
            
            self.results.append(result)
        
        return self.results
    
    def get_statistics(self):
        """
        Calcula estatísticas da simulação.
        
        Returns:
            Dicionário com estatísticas
        """
        if not self.results:
            return None
        
        temps = [r['new_temp'] for r in self.results]
        errors = [abs(r['error']) for r in self.results]
        p_cracs = [r['p_crac'] for r in self.results]
        
        stats = {
            'temp_mean': np.mean(temps),
            'temp_std': np.std(temps),
            'temp_min': np.min(temps),
            'temp_max': np.max(temps),
            'error_mean': np.mean(errors),
            'error_max': np.max(errors),
            'p_crac_mean': np.mean(p_cracs),
            'p_crac_std': np.std(p_cracs),
            'p_crac_min': np.min(p_cracs),
            'p_crac_max': np.max(p_cracs),
            'total_iterations': len(self.results)
        }
        
        return stats
    
    def get_results(self):
        """Retorna os resultados da simulação."""
        return self.results.copy()

