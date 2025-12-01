"""
Módulo do Motor de Inferência Fuzzy Mamdani
Implementa fuzzificação, avaliação de regras, agregação e defuzzificação.
"""

from .membership_functions import (
    ErrorMembership,
    DeltaErrorMembership,
    ExternalTempMembership,
    ThermalLoadMembership,
    PowerCRACMembership
)
from .rules import FuzzyRules
import numpy as np


class MamdaniFuzzyController:
    """
    Controlador Fuzzy tipo Mamdani para controle de temperatura em data center.
    
    Entradas:
    - Erro (e): diferença entre temperatura desejada e atual
    - Variação do Erro (Δe): diferença entre erros consecutivos
    - Temperatura Externa (Text): temperatura ambiente externa
    - Carga Térmica (Qest): carga térmica estimada
    
    Saída:
    - Potência CRAC (PCRAC): porcentagem de potência do sistema de refrigeração
    """
    
    def __init__(self, setpoint_temp=22.0):
        """
        Inicializa o controlador fuzzy.
        
        Args:
            setpoint_temp: Temperatura desejada (setpoint) em °C
        """
        self.setpoint_temp = setpoint_temp
        self.last_error = 0.0
    
    def fuzzify(self, error, delta_error, external_temp, thermal_load):
        """
        Fase 1: Fuzzificação
        Converte valores crisp (numéricos) em valores fuzzy.
        
        Args:
            error: Erro atual (temperatura desejada - temperatura atual)
            delta_error: Variação do erro
            external_temp: Temperatura externa
            thermal_load: Carga térmica
        
        Returns:
            Tupla com os dicionários de pertinência de cada variável
        """
        error_fuzzy = ErrorMembership.fuzzify(error)
        delta_error_fuzzy = DeltaErrorMembership.fuzzify(delta_error)
        temp_fuzzy = ExternalTempMembership.fuzzify(external_temp)
        load_fuzzy = ThermalLoadMembership.fuzzify(thermal_load)
        
        return error_fuzzy, delta_error_fuzzy, temp_fuzzy, load_fuzzy
    
    def evaluate_rules(self, error_fuzzy, delta_error_fuzzy, temp_fuzzy, load_fuzzy):
        """
        Fase 2: Avaliação de Regras
        Identifica quais regras estão ativadas e calcula seus graus de ativação.
        
        Args:
            error_fuzzy: Valores de pertinência do erro
            delta_error_fuzzy: Valores de pertinência da variação do erro
            temp_fuzzy: Valores de pertinência da temperatura externa
            load_fuzzy: Valores de pertinência da carga térmica
        
        Returns:
            Lista de regras ativadas com seus graus de ativação
        """
        activated_rules = FuzzyRules.get_activated_rules(
            error_fuzzy,
            delta_error_fuzzy,
            temp_fuzzy,
            load_fuzzy
        )
        
        return activated_rules
    
    def aggregate(self, activated_rules):
        """
        Fase 3: Agregação
        Combina as saídas de todas as regras ativadas.
        Usa operador MAX (união) para agregar os conjuntos fuzzy de saída.
        
        Args:
            activated_rules: Lista de regras ativadas
        
        Returns:
            Dicionário com o grau máximo de pertinência para cada label de saída
        """
        aggregated = {
            'MB': 0.0,
            'B': 0.0,
            'M': 0.0,
            'A': 0.0,
            'MA': 0.0
        }
        
        for rule_data in activated_rules:
            output_label = rule_data['output']
            activation_degree = rule_data['activation_degree']
            
            # Operador MAX: pega o maior grau de pertinência
            aggregated[output_label] = max(
                aggregated[output_label],
                activation_degree
            )
        
        return aggregated
    
    def defuzzify(self, aggregated_output):
        """
        Fase 4: Defuzzificação
        Converte o conjunto fuzzy agregado em um valor crisp (numérico).
        Usa método do Centroide (Centroid Method).
        
        Args:
            aggregated_output: Dicionário com graus de pertinência agregados
        
        Returns:
            Valor numérico da potência CRAC em porcentagem (0-100)
        """
        # Método do Centroide
        numerator = 0.0
        denominator = 0.0
        
        for label, degree in aggregated_output.items():
            if degree > 0.0:
                centroid = PowerCRACMembership.get_centroid(label)
                numerator += centroid * degree
                denominator += degree
        
        if denominator == 0.0:
            # Se nenhuma regra foi ativada, retorna valor médio
            return 50.0
        
        crisp_output = numerator / denominator
        
        # Garante que o valor está no intervalo [0, 100]
        crisp_output = max(0.0, min(100.0, crisp_output))
        
        return crisp_output
    
    def compute(self, current_temp, external_temp, thermal_load):
        """
        Método principal: executa todo o processo de inferência fuzzy.
        
        Args:
            current_temp: Temperatura atual do data center (°C)
            external_temp: Temperatura externa (°C)
            thermal_load: Carga térmica (kW)
        
        Returns:
            Dicionário com:
            - p_crac: Potência CRAC calculada (%)
            - error: Erro atual
            - delta_error: Variação do erro
            - activated_rules: Regras ativadas
            - fuzzy_values: Valores fuzzificados
        """
        # Calcula erro e variação do erro
        error = self.setpoint_temp - current_temp
        delta_error = error - self.last_error
        self.last_error = error
        
        # Fase 1: Fuzzificação
        error_fuzzy, delta_error_fuzzy, temp_fuzzy, load_fuzzy = self.fuzzify(
            error, delta_error, external_temp, thermal_load
        )
        
        # Fase 2: Avaliação de Regras
        activated_rules = self.evaluate_rules(
            error_fuzzy, delta_error_fuzzy, temp_fuzzy, load_fuzzy
        )
        
        # Fase 3: Agregação
        aggregated_output = self.aggregate(activated_rules)
        
        # Fase 4: Defuzzificação
        p_crac = self.defuzzify(aggregated_output)
        
        return {
            'p_crac': p_crac,
            'error': error,
            'delta_error': delta_error,
            'activated_rules': activated_rules,
            'fuzzy_values': {
                'error': error_fuzzy,
                'delta_error': delta_error_fuzzy,
                'external_temp': temp_fuzzy,
                'thermal_load': load_fuzzy
            },
            'aggregated_output': aggregated_output
        }
    
    def get_membership_data(self):
        """
        Retorna dados das funções de pertinência para visualização.
        
        Returns:
            Dicionário com arrays de pontos para plotagem
        """
        # Gera pontos para plotagem
        n_points = 200
        
        # Erro
        error_range = np.linspace(ErrorMembership.MIN, ErrorMembership.MAX, n_points)
        error_data = {
            'x': error_range.tolist(),
            'NG': [ErrorMembership.negativo_grande(x) for x in error_range],
            'NM': [ErrorMembership.negativo_medio(x) for x in error_range],
            'NP': [ErrorMembership.negativo_pequeno(x) for x in error_range],
            'Z': [ErrorMembership.zero(x) for x in error_range],
            'PP': [ErrorMembership.positivo_pequeno(x) for x in error_range],
            'PM': [ErrorMembership.positivo_medio(x) for x in error_range],
            'PG': [ErrorMembership.positivo_grande(x) for x in error_range]
        }
        
        # Delta Erro
        delta_error_range = np.linspace(DeltaErrorMembership.MIN, DeltaErrorMembership.MAX, n_points)
        delta_error_data = {
            'x': delta_error_range.tolist(),
            'NG': [DeltaErrorMembership.negativo_grande(x) for x in delta_error_range],
            'NM': [DeltaErrorMembership.negativo_medio(x) for x in delta_error_range],
            'NP': [DeltaErrorMembership.negativo_pequeno(x) for x in delta_error_range],
            'Z': [DeltaErrorMembership.zero(x) for x in delta_error_range],
            'PP': [DeltaErrorMembership.positivo_pequeno(x) for x in delta_error_range],
            'PM': [DeltaErrorMembership.positivo_medio(x) for x in delta_error_range],
            'PG': [DeltaErrorMembership.positivo_grande(x) for x in delta_error_range]
        }
        
        # Temperatura Externa
        temp_range = np.linspace(ExternalTempMembership.MIN, ExternalTempMembership.MAX, n_points)
        temp_data = {
            'x': temp_range.tolist(),
            'MB': [ExternalTempMembership.muito_baixa(x) for x in temp_range],
            'B': [ExternalTempMembership.baixa(x) for x in temp_range],
            'M': [ExternalTempMembership.media(x) for x in temp_range],
            'A': [ExternalTempMembership.alta(x) for x in temp_range],
            'MA': [ExternalTempMembership.muito_alta(x) for x in temp_range]
        }
        
        # Carga Térmica
        load_range = np.linspace(ThermalLoadMembership.MIN, ThermalLoadMembership.MAX, n_points)
        load_data = {
            'x': load_range.tolist(),
            'MB': [ThermalLoadMembership.muito_baixa(x) for x in load_range],
            'B': [ThermalLoadMembership.baixa(x) for x in load_range],
            'M': [ThermalLoadMembership.media(x) for x in load_range],
            'A': [ThermalLoadMembership.alta(x) for x in load_range],
            'MA': [ThermalLoadMembership.muito_alta(x) for x in load_range]
        }
        
        # Potência CRAC
        power_range = np.linspace(PowerCRACMembership.MIN, PowerCRACMembership.MAX, n_points)
        power_data = {
            'x': power_range.tolist(),
            'MB': [PowerCRACMembership.muito_baixa(x) for x in power_range],
            'B': [PowerCRACMembership.baixa(x) for x in power_range],
            'M': [PowerCRACMembership.media(x) for x in power_range],
            'A': [PowerCRACMembership.alta(x) for x in power_range],
            'MA': [PowerCRACMembership.muito_alta(x) for x in power_range]
        }
        
        return {
            'error': error_data,
            'delta_error': delta_error_data,
            'external_temp': temp_data,
            'thermal_load': load_data,
            'power_crac': power_data
        }

