"""
Servidor FastAPI - API REST para o Sistema de Controle Fuzzy
Integra todos os componentes: fuzzy, simulação e MQTT.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging

try:
    from backend.fuzzy.mamdani import MamdaniFuzzyController
    from backend.simulation.simulator import Simulator24H
    from backend.mqtt.client_mqtt import MQTTClient
except ImportError:
    # Fallback para imports relativos quando executado da pasta backend
    from fuzzy.mamdani import MamdaniFuzzyController
    from simulation.simulator import Simulator24H
    from mqtt.client_mqtt import MQTTClient

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa FastAPI
app = FastAPI(
    title="Sistema de Controle Fuzzy para Data Center",
    description="API REST para controle fuzzy de temperatura em data center",
    version="1.0.0"
)

# Configura CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instâncias globais
fuzzy_controller = MamdaniFuzzyController(setpoint_temp=22.0)
# Configura cliente MQTT com WebSockets e path /mqtt
mqtt_client = MQTTClient(
    broker_host='broker.com',
    broker_port=8000,
    broker_path='/mqtt',
    use_websockets=True  # Usa WebSockets para suportar path /mqtt
)
simulator = None


# Modelos Pydantic para validação
class ControlRequest(BaseModel):
    """Modelo para requisição de controle."""
    current_temp: float
    external_temp: float
    thermal_load: float
    setpoint_temp: Optional[float] = 22.0


class SimulationRequest(BaseModel):
    """Modelo para requisição de simulação."""
    setpoint_temp: Optional[float] = 22.0
    initial_temp: Optional[float] = 22.0


class ManualControlRequest(BaseModel):
    """Modelo para controle manual."""
    error: float
    delta_error: float
    external_temp: float
    thermal_load: float


# Rotas da API

@app.on_event("startup")
async def startup_event():
    """Inicializa componentes na startup."""
    logger.info("Iniciando servidor...")
    # Tenta conectar ao MQTT (não bloqueia se falhar)
    try:
        connected = mqtt_client.connect(timeout=5)
        if connected:
            logger.info("✅ Conectado ao broker MQTT com sucesso")
        else:
            if mqtt_client.simulation_mode:
                logger.info("ℹ️ Modo simulação MQTT ativado - Sistema funcionando normalmente sem broker")
                logger.info("   Todos os alertas serão salvos localmente e exibidos no dashboard")
            else:
                logger.warning("⚠️ Não foi possível conectar ao MQTT na primeira tentativa")
                logger.info("   O sistema continuará funcionando e tentará reconectar automaticamente")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao tentar conectar ao MQTT: {e}")
        mqtt_client.simulation_mode = True
        logger.info("ℹ️ Modo simulação MQTT ativado - Sistema funcionando normalmente")


@app.on_event("shutdown")
async def shutdown_event():
    """Limpa recursos no shutdown."""
    logger.info("Encerrando servidor...")
    mqtt_client.disconnect()


@app.get("/")
async def root():
    """Rota raiz."""
    return {
        "message": "Sistema de Controle Fuzzy para Data Center",
        "version": "1.0.0",
        "endpoints": {
            "control": "/api/control",
            "manual_control": "/api/manual-control",
            "simulation": "/api/simulation",
            "membership": "/api/membership",
            "rules": "/api/rules",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """Verifica saúde do sistema."""
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_client.is_connected(),
        "mqtt_status": mqtt_client.get_status()
    }


@app.get("/api/mqtt/status")
async def get_mqtt_status():
    """Retorna status completo do MQTT."""
    return mqtt_client.get_status()


@app.get("/api/mqtt/alerts")
async def get_mqtt_alerts(limit: Optional[int] = 50):
    """Retorna histórico de alertas MQTT."""
    return {
        "alerts": mqtt_client.get_alert_history(limit=limit),
        "total": len(mqtt_client.get_alert_history())
    }


@app.post("/api/control")
async def control(request: ControlRequest):
    """
    Executa controle fuzzy com base nas condições atuais.
    
    Args:
        request: Dados de entrada (temperatura atual, externa, carga térmica)
    
    Returns:
        Resultado do controle fuzzy com potência CRAC calculada
    """
    global fuzzy_controller
    try:
        # Atualiza setpoint se fornecido
        if request.setpoint_temp != fuzzy_controller.setpoint_temp:
            fuzzy_controller = MamdaniFuzzyController(setpoint_temp=request.setpoint_temp)
        
        # Executa controle fuzzy
        result = fuzzy_controller.compute(
            current_temp=request.current_temp,
            external_temp=request.external_temp,
            thermal_load=request.thermal_load
        )
        
        # Publica no MQTT
        mqtt_client.publish_temperature(
            temperature=request.current_temp,
            setpoint=request.setpoint_temp,
            error=result['error']
        )
        
        mqtt_client.publish_control({
            'p_crac': result['p_crac'],
            'error': result['error'],
            'delta_error': result['delta_error'],
            'external_temp': request.external_temp,
            'thermal_load': request.thermal_load
        })
        
        # Verifica alertas
        mqtt_client.check_temperature_alerts(
            current_temp=request.current_temp,
            setpoint_temp=request.setpoint_temp
        )
        
        # Verifica alertas de potência CRAC
        mqtt_client.check_power_alerts(result['p_crac'])
        
        # Prepara resposta
        response = {
            'p_crac': result['p_crac'],
            'error': result['error'],
            'delta_error': result['delta_error'],
            'activated_rules_count': len(result['activated_rules']),
            'activated_rules': [
                {
                    'rule': rule['rule'],
                    'activation_degree': rule['activation_degree']
                }
                for rule in result['activated_rules'][:10]  # Limita a 10 regras
            ],
            'fuzzy_values': result['fuzzy_values'],
            'aggregated_output': result['aggregated_output']
        }
        
        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Erro no controle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/manual-control")
async def manual_control(request: ManualControlRequest):
    """
    Executa controle fuzzy com valores manuais de erro e delta erro.
    
    Args:
        request: Valores manuais de erro, delta erro, temp externa e carga térmica
    
    Returns:
        Resultado do controle fuzzy
    """
    try:
        # Fuzzifica manualmente
        try:
            from backend.fuzzy.membership_functions import (
                ErrorMembership,
                DeltaErrorMembership,
                ExternalTempMembership,
                ThermalLoadMembership
            )
            from backend.fuzzy.rules import FuzzyRules
        except ImportError:
            from fuzzy.membership_functions import (
                ErrorMembership,
                DeltaErrorMembership,
                ExternalTempMembership,
                ThermalLoadMembership
            )
            from fuzzy.rules import FuzzyRules
        
        error_fuzzy = ErrorMembership.fuzzify(request.error)
        delta_error_fuzzy = DeltaErrorMembership.fuzzify(request.delta_error)
        temp_fuzzy = ExternalTempMembership.fuzzify(request.external_temp)
        load_fuzzy = ThermalLoadMembership.fuzzify(request.thermal_load)
        
        # Avalia regras
        activated_rules = FuzzyRules.get_activated_rules(
            error_fuzzy, delta_error_fuzzy, temp_fuzzy, load_fuzzy
        )
        
        # Agrega
        aggregated = {}
        for rule_data in activated_rules:
            output_label = rule_data['output']
            activation_degree = rule_data['activation_degree']
            aggregated[output_label] = max(
                aggregated.get(output_label, 0.0),
                activation_degree
            )
        
        # Defuzzifica
        try:
            from backend.fuzzy.membership_functions import PowerCRACMembership
        except ImportError:
            from fuzzy.membership_functions import PowerCRACMembership
        numerator = 0.0
        denominator = 0.0
        for label, degree in aggregated.items():
            if degree > 0.0:
                centroid = PowerCRACMembership.get_centroid(label)
                numerator += centroid * degree
                denominator += degree
        
        p_crac = (numerator / denominator) if denominator > 0 else 50.0
        p_crac = max(0.0, min(100.0, p_crac))
        
        response = {
            'p_crac': p_crac,
            'error': request.error,
            'delta_error': request.delta_error,
            'activated_rules_count': len(activated_rules),
            'activated_rules': [
                {
                    'rule': rule['rule'],
                    'activation_degree': rule['activation_degree']
                }
                for rule in activated_rules[:10]
            ],
            'fuzzy_values': {
                'error': error_fuzzy,
                'delta_error': delta_error_fuzzy,
                'external_temp': temp_fuzzy,
                'thermal_load': load_fuzzy
            },
            'aggregated_output': aggregated
        }
        
        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Erro no controle manual: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulation")
async def run_simulation(request: SimulationRequest):
    """
    Executa simulação de 24 horas.
    
    Args:
        request: Parâmetros da simulação (setpoint, temperatura inicial)
    
    Returns:
        Resultados completos da simulação
    """
    try:
        global simulator
        simulator = Simulator24H(
            setpoint_temp=request.setpoint_temp,
            initial_temp=request.initial_temp
        )
        
        logger.info("Iniciando simulação de 24 horas...")
        results = simulator.run()
        stats = simulator.get_statistics()
        
        logger.info("Simulação concluída!")
        
        response = {
            'results': results,
            'statistics': stats,
            'total_iterations': len(results)
        }
        
        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Erro na simulação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/membership")
async def get_membership_functions():
    """
    Retorna dados das funções de pertinência para visualização.
    
    Returns:
        Dados de todas as funções de pertinência
    """
    try:
        data = fuzzy_controller.get_membership_data()
        return JSONResponse(content=data)
    
    except Exception as e:
        logger.error(f"Erro ao obter funções de pertinência: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rules")
async def get_rules():
    """
    Retorna a base de regras fuzzy.
    
    Returns:
        Base de regras e tabela simplificada
    """
    try:
        try:
            from backend.fuzzy.rules import FuzzyRules
        except ImportError:
            from fuzzy.rules import FuzzyRules
        
        rules = FuzzyRules.get_rules()
        table = FuzzyRules.get_rules_table()
        
        return JSONResponse(content={
            'total_rules': len(rules),
            'rules_table': table,
            'sample_rules': rules[:20]  # Primeiras 20 regras como exemplo
        })
    
    except Exception as e:
        logger.error(f"Erro ao obter regras: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

