"""
Módulo de Base de Regras Fuzzy
Implementa a base de regras completa e consistente para o controlador fuzzy.
"""


class FuzzyRules:
    """
    Base de regras fuzzy para o controlador MISO.
    
    Formato das regras: IF (Erro, DeltaErro, TempExterna, CargaTermica) THEN PotenciaCRAC
    
    Variáveis de entrada:
    - Erro (e): NG, NM, NP, Z, PP, PM, PG
    - DeltaErro (Δe): NG, NM, NP, Z, PP, PM, PG
    - TempExterna (Text): MB, B, M, A, MA
    - CargaTermica (Qest): MB, B, M, A, MA
    
    Variável de saída:
    - PotenciaCRAC (PCRAC): MB, B, M, A, MA
    """
    
    # Mapeamento de labels para valores numéricos (para facilitar comparações)
    ERROR_LABELS = ['NG', 'NM', 'NP', 'Z', 'PP', 'PM', 'PG']
    DELTA_ERROR_LABELS = ['NG', 'NM', 'NP', 'Z', 'PP', 'PM', 'PG']
    TEMP_LABELS = ['MB', 'B', 'M', 'A', 'MA']
    LOAD_LABELS = ['MB', 'B', 'M', 'A', 'MA']
    OUTPUT_LABELS = ['MB', 'B', 'M', 'A', 'MA']
    
    # Mapeamento de saída para índices (para ajustes)
    OUTPUT_INDEX = {'MB': 0, 'B': 1, 'M': 2, 'A': 3, 'MA': 4}
    INDEX_OUTPUT = {0: 'MB', 1: 'B', 2: 'M', 3: 'A', 4: 'MA'}
    
    @staticmethod
    def _adjust_power_by_conditions(base_output, temp, load):
        """
        Ajusta a potência base baseada em temperatura externa e carga térmica.
        
        Lógica de controle térmico:
        - Alta temperatura externa ou alta carga → aumenta potência
        - Baixa temperatura externa e baixa carga → reduz potência
        - Condições médias → mantém potência base
        
        Args:
            base_output: Saída base (MB, B, M, A, MA)
            temp: Temperatura externa (MB, B, M, A, MA)
            load: Carga térmica (MB, B, M, A, MA)
        
        Returns:
            Saída ajustada (MB, B, M, A, MA)
        """
        base_idx = FuzzyRules.OUTPUT_INDEX[base_output]
        
        # Determina ajuste baseado em temp e load
        # Alta temp ou alta carga → +1 nível
        # Baixa temp e baixa carga → -1 nível
        # Caso contrário → 0 (sem ajuste)
        
        if temp in ['MA', 'A'] or load in ['MA', 'A']:
            # Alta demanda térmica → aumenta potência
            adjustment = 1
        elif temp in ['MB', 'B'] and load in ['MB', 'B']:
            # Baixa demanda térmica → reduz potência
            adjustment = -1
        else:
            # Condições médias → sem ajuste
            adjustment = 0
        
        # Aplica ajuste, limitando entre MB (0) e MA (4)
        adjusted_idx = max(0, min(4, base_idx + adjustment))
        
        return FuzzyRules.INDEX_OUTPUT[adjusted_idx]
    
    @staticmethod
    def get_rules():
        """
        Retorna a base de regras completa.
        
        Returns:
            Lista de dicionários, cada um representando uma regra fuzzy.
        """
        rules = []
        
        # Estratégia de regras: Priorizar controle baseado em Erro e DeltaErro,
        # com ajustes baseados em TempExterna e CargaTermica
        
        # Regras quando Erro é Negativo Grande (NG) - temperatura muito abaixo do setpoint
        for delta_e in FuzzyRules.DELTA_ERROR_LABELS:
            for temp in FuzzyRules.TEMP_LABELS:
                for load in FuzzyRules.LOAD_LABELS:
                    # Se erro muito negativo, precisa reduzir potência drasticamente
                    if delta_e in ['NG', 'NM']:
                        base_output = 'MB'  # Muito baixa potência base
                    elif delta_e == 'NP':
                        base_output = 'B'   # Baixa potência base
                    else:
                        base_output = 'B'   # Baixa potência base
                    
                    # Ajusta baseado em temperatura externa e carga térmica
                    output = FuzzyRules._adjust_power_by_conditions(base_output, temp, load)
                    
                    rules.append({
                        'error': 'NG',
                        'delta_error': delta_e,
                        'external_temp': temp,
                        'thermal_load': load,
                        'output': output
                    })
        
        # Regras quando Erro é Negativo Médio (NM)
        for delta_e in FuzzyRules.DELTA_ERROR_LABELS:
            for temp in FuzzyRules.TEMP_LABELS:
                for load in FuzzyRules.LOAD_LABELS:
                    if delta_e in ['NG', 'NM']:
                        base_output = 'MB'
                    elif delta_e == 'NP':
                        base_output = 'B'
                    elif delta_e == 'Z':
                        base_output = 'B'
                    else:
                        base_output = 'M'
                    
                    # Ajusta baseado em temperatura externa e carga térmica
                    output = FuzzyRules._adjust_power_by_conditions(base_output, temp, load)
                    
                    rules.append({
                        'error': 'NM',
                        'delta_error': delta_e,
                        'external_temp': temp,
                        'thermal_load': load,
                        'output': output
                    })
        
        # Regras quando Erro é Negativo Pequeno (NP)
        for delta_e in FuzzyRules.DELTA_ERROR_LABELS:
            for temp in FuzzyRules.TEMP_LABELS:
                for load in FuzzyRules.LOAD_LABELS:
                    if delta_e in ['NG', 'NM']:
                        base_output = 'B'
                    elif delta_e in ['NP', 'Z']:
                        base_output = 'M'
                    elif delta_e == 'PP':
                        base_output = 'M'
                    else:
                        base_output = 'A'
                    
                    # Ajusta baseado em temperatura externa e carga térmica
                    output = FuzzyRules._adjust_power_by_conditions(base_output, temp, load)
                    
                    rules.append({
                        'error': 'NP',
                        'delta_error': delta_e,
                        'external_temp': temp,
                        'thermal_load': load,
                        'output': output
                    })
        
        # Regras quando Erro é Zero (Z) - temperatura no setpoint
        for delta_e in FuzzyRules.DELTA_ERROR_LABELS:
            for temp in FuzzyRules.TEMP_LABELS:
                for load in FuzzyRules.LOAD_LABELS:
                    # Ajuste baseado em carga térmica e temperatura externa
                    if load in ['MA', 'A'] or temp in ['MA', 'A']:
                        # Alta carga ou alta temp externa requer mais potência
                        if delta_e in ['NG', 'NM']:
                            output = 'M'
                        elif delta_e in ['NP', 'Z', 'PP']:
                            output = 'A'
                        else:
                            output = 'A'
                    elif load in ['MB', 'B'] and temp in ['MB', 'B']:
                        # Baixa carga e baixa temp externa requer menos potência
                        if delta_e in ['NG', 'NM']:
                            output = 'B'
                        elif delta_e in ['NP', 'Z', 'PP']:
                            output = 'M'
                        else:
                            output = 'M'
                    else:
                        # Condições médias
                        if delta_e in ['NG', 'NM']:
                            output = 'B'
                        elif delta_e in ['NP', 'Z', 'PP']:
                            output = 'M'
                        else:
                            output = 'A'
                    rules.append({
                        'error': 'Z',
                        'delta_error': delta_e,
                        'external_temp': temp,
                        'thermal_load': load,
                        'output': output
                    })
        
        # Regras quando Erro é Positivo Pequeno (PP)
        for delta_e in FuzzyRules.DELTA_ERROR_LABELS:
            for temp in FuzzyRules.TEMP_LABELS:
                for load in FuzzyRules.LOAD_LABELS:
                    if delta_e in ['NG', 'NM']:
                        base_output = 'M'
                    elif delta_e in ['NP', 'Z', 'PP']:
                        base_output = 'A'
                    else:
                        base_output = 'A'
                    
                    # Ajusta baseado em temperatura externa e carga térmica
                    output = FuzzyRules._adjust_power_by_conditions(base_output, temp, load)
                    
                    rules.append({
                        'error': 'PP',
                        'delta_error': delta_e,
                        'external_temp': temp,
                        'thermal_load': load,
                        'output': output
                    })
        
        # Regras quando Erro é Positivo Médio (PM)
        for delta_e in FuzzyRules.DELTA_ERROR_LABELS:
            for temp in FuzzyRules.TEMP_LABELS:
                for load in FuzzyRules.LOAD_LABELS:
                    if delta_e in ['NG', 'NM']:
                        base_output = 'A'
                    elif delta_e in ['NP', 'Z']:
                        base_output = 'A'
                    else:
                        base_output = 'MA'
                    
                    # Ajusta baseado em temperatura externa e carga térmica
                    output = FuzzyRules._adjust_power_by_conditions(base_output, temp, load)
                    
                    rules.append({
                        'error': 'PM',
                        'delta_error': delta_e,
                        'external_temp': temp,
                        'thermal_load': load,
                        'output': output
                    })
        
        # Regras quando Erro é Positivo Grande (PG) - temperatura muito acima do setpoint
        for delta_e in FuzzyRules.DELTA_ERROR_LABELS:
            for temp in FuzzyRules.TEMP_LABELS:
                for load in FuzzyRules.LOAD_LABELS:
                    # Se erro muito positivo, precisa aumentar potência drasticamente
                    if delta_e in ['PP', 'PM', 'PG']:
                        base_output = 'MA'  # Muito alta potência base
                    elif delta_e in ['NP', 'Z']:
                        base_output = 'A'   # Alta potência base
                    else:
                        base_output = 'A'   # Alta potência base
                    
                    # Ajusta baseado em temperatura externa e carga térmica
                    # Nota: Se já está em MA, não pode aumentar mais, mas pode reduzir se condições forem favoráveis
                    output = FuzzyRules._adjust_power_by_conditions(base_output, temp, load)
                    
                    rules.append({
                        'error': 'PG',
                        'delta_error': delta_e,
                        'external_temp': temp,
                        'thermal_load': load,
                        'output': output
                    })
        
        return rules
    
    @staticmethod
    def get_activated_rules(error_fuzzy, delta_error_fuzzy, temp_fuzzy, load_fuzzy):
        """
        Retorna as regras ativadas baseadas nos valores fuzzificados.
        
        Args:
            error_fuzzy: Dicionário com valores de pertinência do erro
            delta_error_fuzzy: Dicionário com valores de pertinência da variação do erro
            temp_fuzzy: Dicionário com valores de pertinência da temperatura externa
            load_fuzzy: Dicionário com valores de pertinência da carga térmica
        
        Returns:
            Lista de regras ativadas com seus graus de ativação
        """
        rules = FuzzyRules.get_rules()
        activated = []
        
        for rule in rules:
            # Calcula o grau de ativação usando operador MIN (interseção)
            error_degree = error_fuzzy.get(rule['error'], 0.0)
            delta_error_degree = delta_error_fuzzy.get(rule['delta_error'], 0.0)
            temp_degree = temp_fuzzy.get(rule['external_temp'], 0.0)
            load_degree = load_fuzzy.get(rule['thermal_load'], 0.0)
            
            # Grau de ativação = mínimo entre todos os antecedentes
            activation_degree = min(
                error_degree,
                delta_error_degree,
                temp_degree,
                load_degree
            )
            
            # Só adiciona se a regra estiver ativada (grau > 0)
            if activation_degree > 0.0:
                activated.append({
                    'rule': rule,
                    'activation_degree': activation_degree,
                    'output': rule['output']
                })
        
        return activated
    
    @staticmethod
    def get_rules_table():
        """
        Retorna uma representação tabular simplificada das regras principais.
        Útil para documentação e visualização.
        """
        # Tabela simplificada mostrando regras principais
        # (considerando apenas Erro e DeltaErro para simplificar)
        table = []
        
        error_labels = ['NG', 'NM', 'NP', 'Z', 'PP', 'PM', 'PG']
        delta_error_labels = ['NG', 'NM', 'NP', 'Z', 'PP', 'PM', 'PG']
        
        # Para simplificar, vamos considerar apenas quando Temp e Load são médios
        for error in error_labels:
            row = {'error': error, 'outputs': {}}
            for delta_error in delta_error_labels:
                # Busca uma regra representativa (com temp='M' e load='M')
                rules = FuzzyRules.get_rules()
                for rule in rules:
                    if (rule['error'] == error and 
                        rule['delta_error'] == delta_error and
                        rule['external_temp'] == 'M' and
                        rule['thermal_load'] == 'M'):
                        row['outputs'][delta_error] = rule['output']
                        break
            table.append(row)
        
        return table

