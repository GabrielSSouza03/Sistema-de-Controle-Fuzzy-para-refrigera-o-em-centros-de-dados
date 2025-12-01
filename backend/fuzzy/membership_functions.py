"""
Módulo de Funções de Pertinência Fuzzy
Implementa funções triangulares e trapezoidais para todas as variáveis do sistema.
"""

import numpy as np


class MembershipFunction:
    """Classe base para funções de pertinência."""
    
    @staticmethod
    def triangular(x, a, b, c):
        """
        Função de pertinência triangular.
        
        Args:
            x: Valor de entrada
            a: Ponto inicial (pertinência = 0)
            b: Ponto central (pertinência = 1)
            c: Ponto final (pertinência = 0)
        
        Returns:
            Valor de pertinência entre 0 e 1
        """
        if x <= a or x >= c:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a) if b != a else 0.0
        elif b < x < c:
            return (c - x) / (c - b) if c != b else 0.0
        return 0.0
    
    @staticmethod
    def trapezoidal(x, a, b, c, d):
        """
        Função de pertinência trapezoidal.
        
        Args:
            x: Valor de entrada
            a: Ponto inicial (pertinência = 0)
            b: Início do platô (pertinência = 1)
            c: Fim do platô (pertinência = 1)
            d: Ponto final (pertinência = 0)
        
        Returns:
            Valor de pertinência entre 0 e 1
        """
        if x <= a or x >= d:
            return 0.0
        elif a < x < b:
            return (x - a) / (b - a) if b != a else 0.0
        elif b <= x <= c:
            return 1.0
        elif c < x < d:
            return (d - x) / (d - c) if d != c else 0.0
        return 0.0


class ErrorMembership:
    """Funções de pertinência para a variável Erro (e)."""
    
    # Universo de discurso: -10 a 10 °C
    MIN = -10.0
    MAX = 10.0
    
    @staticmethod
    def negativo_grande(x):
        """Erro negativo grande (NG) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, -10, -10, -7, -4)
    
    @staticmethod
    def negativo_medio(x):
        """Erro negativo médio (NM) - triangular."""
        return MembershipFunction.triangular(x, -7, -4, -1)
    
    @staticmethod
    def negativo_pequeno(x):
        """Erro negativo pequeno (NP) - triangular."""
        return MembershipFunction.triangular(x, -4, -1, 0)
    
    @staticmethod
    def zero(x):
        """Erro zero (Z) - triangular."""
        return MembershipFunction.triangular(x, -1, 0, 1)
    
    @staticmethod
    def positivo_pequeno(x):
        """Erro positivo pequeno (PP) - triangular."""
        return MembershipFunction.triangular(x, 0, 1, 4)
    
    @staticmethod
    def positivo_medio(x):
        """Erro positivo médio (PM) - triangular."""
        return MembershipFunction.triangular(x, 1, 4, 7)
    
    @staticmethod
    def positivo_grande(x):
        """Erro positivo grande (PG) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, 4, 7, 10, 10)
    
    @staticmethod
    def fuzzify(x):
        """Fuzzifica o valor de erro."""
        return {
            'NG': ErrorMembership.negativo_grande(x),
            'NM': ErrorMembership.negativo_medio(x),
            'NP': ErrorMembership.negativo_pequeno(x),
            'Z': ErrorMembership.zero(x),
            'PP': ErrorMembership.positivo_pequeno(x),
            'PM': ErrorMembership.positivo_medio(x),
            'PG': ErrorMembership.positivo_grande(x)
        }


class DeltaErrorMembership:
    """Funções de pertinência para a variável Variação do Erro (Δe)."""
    
    # Universo de discurso: -10 a 10 °C (similar ao erro)
    MIN = -10.0
    MAX = 10.0
    
    @staticmethod
    def negativo_grande(x):
        """Variação negativa grande (NG) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, -10, -10, -7, -4)
    
    @staticmethod
    def negativo_medio(x):
        """Variação negativa média (NM) - triangular."""
        return MembershipFunction.triangular(x, -7, -4, -1)
    
    @staticmethod
    def negativo_pequeno(x):
        """Variação negativa pequena (NP) - triangular."""
        return MembershipFunction.triangular(x, -4, -1, 0)
    
    @staticmethod
    def zero(x):
        """Variação zero (Z) - triangular."""
        return MembershipFunction.triangular(x, -1, 0, 1)
    
    @staticmethod
    def positivo_pequeno(x):
        """Variação positiva pequena (PP) - triangular."""
        return MembershipFunction.triangular(x, 0, 1, 4)
    
    @staticmethod
    def positivo_medio(x):
        """Variação positiva média (PM) - triangular."""
        return MembershipFunction.triangular(x, 1, 4, 7)
    
    @staticmethod
    def positivo_grande(x):
        """Variação positiva grande (PG) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, 4, 7, 10, 10)
    
    @staticmethod
    def fuzzify(x):
        """Fuzzifica o valor de variação do erro."""
        return {
            'NG': DeltaErrorMembership.negativo_grande(x),
            'NM': DeltaErrorMembership.negativo_medio(x),
            'NP': DeltaErrorMembership.negativo_pequeno(x),
            'Z': DeltaErrorMembership.zero(x),
            'PP': DeltaErrorMembership.positivo_pequeno(x),
            'PM': DeltaErrorMembership.positivo_medio(x),
            'PG': DeltaErrorMembership.positivo_grande(x)
        }


class ExternalTempMembership:
    """Funções de pertinência para a variável Temperatura Externa (Text)."""
    
    # Universo de discurso: centrado em 25 °C 
    # Intervalo: 18 a 32 °C (centrado em 25)
    MIN = 18.0
    MAX = 32.0
    
    @staticmethod
    def muito_baixa(x):
        """Temperatura muito baixa (MB) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, 18, 18, 20, 22)
    
    @staticmethod
    def baixa(x):
        """Temperatura baixa (B) - triangular."""
        return MembershipFunction.triangular(x, 20, 22, 24)
    
    @staticmethod
    def media(x):
        """Temperatura média (M) - triangular (centrada em 25°C)."""
        return MembershipFunction.triangular(x, 23, 25, 27)
    
    @staticmethod
    def alta(x):
        """Temperatura alta (A) - triangular."""
        return MembershipFunction.triangular(x, 25, 27, 29)
    
    @staticmethod
    def muito_alta(x):
        """Temperatura muito alta (MA) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, 27, 29, 32, 32)
    
    @staticmethod
    def fuzzify(x):
        """Fuzzifica o valor de temperatura externa."""
        return {
            'MB': ExternalTempMembership.muito_baixa(x),
            'B': ExternalTempMembership.baixa(x),
            'M': ExternalTempMembership.media(x),
            'A': ExternalTempMembership.alta(x),
            'MA': ExternalTempMembership.muito_alta(x)
        }


class ThermalLoadMembership:
    """Funções de pertinência para a variável Carga Térmica (Qest)."""
    
    # Universo de discurso: centrado em 40 % 
    # Intervalo: 0 a 80 % (centrado em 40)
    MIN = 0.0
    MAX = 80.0
    
    @staticmethod
    def muito_baixa(x):
        """Carga muito baixa (MB) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, 0, 0, 10, 20)
    
    @staticmethod
    def baixa(x):
        """Carga baixa (B) - triangular."""
        return MembershipFunction.triangular(x, 15, 25, 35)
    
    @staticmethod
    def media(x):
        """Carga média (M) - triangular (centrada em 40%)."""
        return MembershipFunction.triangular(x, 30, 40, 50)
    
    @staticmethod
    def alta(x):
        """Carga alta (A) - triangular."""
        return MembershipFunction.triangular(x, 45, 55, 65)
    
    @staticmethod
    def muito_alta(x):
        """Carga muito alta (MA) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, 60, 70, 80, 80)
    
    @staticmethod
    def fuzzify(x):
        """Fuzzifica o valor de carga térmica."""
        return {
            'MB': ThermalLoadMembership.muito_baixa(x),
            'B': ThermalLoadMembership.baixa(x),
            'M': ThermalLoadMembership.media(x),
            'A': ThermalLoadMembership.alta(x),
            'MA': ThermalLoadMembership.muito_alta(x)
        }


class PowerCRACMembership:
    """Funções de pertinência para a variável Potência CRAC (PCRAC)."""
    
    # Universo de discurso: 0 a 100 %
    MIN = 0.0
    MAX = 100.0
    
    @staticmethod
    def muito_baixa(x):
        """Potência muito baixa (MB) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, 0, 0, 15, 25)
    
    @staticmethod
    def baixa(x):
        """Potência baixa (B) - triangular."""
        return MembershipFunction.triangular(x, 15, 25, 40)
    
    @staticmethod
    def media(x):
        """Potência média (M) - triangular."""
        return MembershipFunction.triangular(x, 25, 40, 60)
    
    @staticmethod
    def alta(x):
        """Potência alta (A) - triangular."""
        return MembershipFunction.triangular(x, 40, 60, 80)
    
    @staticmethod
    def muito_alta(x):
        """Potência muito alta (MA) - trapezoidal."""
        return MembershipFunction.trapezoidal(x, 60, 80, 100, 100)
    
    @staticmethod
    def get_centroid(label):
        """
        Retorna o centroide (valor central) de cada conjunto fuzzy de saída.
        Usado para defuzzificação.
        """
        centroids = {
            'MB': 12.5,   # Centro do trapezoidal [0, 0, 15, 25]
            'B': 30.0,    # Centro do triangular [15, 25, 40]
            'M': 50.0,    # Centro do triangular [25, 40, 60]
            'A': 70.0,    # Centro do triangular [40, 60, 80]
            'MA': 90.0    # Centro do trapezoidal [60, 80, 100, 100]
        }
        return centroids.get(label, 50.0)

