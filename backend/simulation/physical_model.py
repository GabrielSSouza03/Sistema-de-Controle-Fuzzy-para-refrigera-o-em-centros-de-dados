"""
Módulo do Modelo Físico do Data Center
Implementa a equação de dinâmica térmica do sistema.
"""

import numpy as np


class PhysicalModel:
    """
    Modelo físico simplificado de um data center.
    
    Equação de dinâmica térmica:
    T[n+1] = 0.9*T[n] - 0.08*PCRAC + 0.05*Qest + 0.02*Text + 3.5
    
    Onde:
    - T[n+1]: Temperatura no próximo instante
    - T[n]: Temperatura atual
    - PCRAC: Potência do CRAC (0-100%)
    - Qest: Carga térmica estimada (kW)
    - Text: Temperatura externa (°C)
    """
    
    def __init__(self, initial_temp=22.0):
        """
        Inicializa o modelo físico.
        
        Args:
            initial_temp: Temperatura inicial do data center (°C)
        """
        self.current_temp = initial_temp
        self.temp_history = [initial_temp]
    
    def update(self, p_crac, thermal_load, external_temp):
        """
        Atualiza a temperatura do data center baseado nas entradas.
        
        Args:
            p_crac: Potência do CRAC em porcentagem (0-100)
            thermal_load: Carga térmica em kW
            external_temp: Temperatura externa em °C
        
        Returns:
            Nova temperatura do data center
        """
        # Equação de dinâmica térmica
        new_temp = (
            0.9 * self.current_temp
            - 0.08 * p_crac
            + 0.05 * thermal_load
            + 0.02 * external_temp
            + 3.5
        )
        
        # Limita a temperatura em um intervalo razoável
        new_temp = max(15.0, min(35.0, new_temp))
        
        self.current_temp = new_temp
        self.temp_history.append(new_temp)
        
        return new_temp
    
    def get_current_temp(self):
        """Retorna a temperatura atual."""
        return self.current_temp
    
    def reset(self, initial_temp=22.0):
        """Reseta o modelo para temperatura inicial."""
        self.current_temp = initial_temp
        self.temp_history = [initial_temp]
    
    def get_history(self):
        """Retorna o histórico de temperaturas."""
        return self.temp_history.copy()

