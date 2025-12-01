"""
Módulo Cliente MQTT
Implementa comunicação MQTT para envio de alertas, controle e temperatura.
"""

import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime


class MQTTClient:
    """
    Cliente MQTT para comunicação do sistema de controle fuzzy.
    
    Tópicos:
    - datacenter/fuzzy/alert: Alertas do sistema
    
    Estrutura de Mensagens de Alerta:
    As mensagens de alerta contêm:
    - timestamp: Marca temporal da ocorrência (ISO format)
    - tipo: Categoria do alerta ('crítico', 'eficiência', 'estabilidade')
    - mensagem: Descrição human-readable
    - dados: Valores relevantes do sistema (dicionário)
    - severidade: Nível de importância ('baixa', 'média', 'alta', 'crítica')
    
    - datacenter/fuzzy/control: Informações de controle
    - datacenter/fuzzy/temp: Temperatura atual
    """
    
    def __init__(self, broker_host='broker.com', broker_port=8000, broker_path='/mqtt', use_websockets=False):
        """
        Inicializa o cliente MQTT.
        
        Args:
            broker_host: Endereço do broker MQTT (padrão: broker.com)
            broker_port: Porta do broker MQTT (padrão: 8000)
            broker_path: Path do broker para WebSockets (padrão: /mqtt)
            use_websockets: Se True, usa WebSockets em vez de TCP (padrão: False)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.broker_path = broker_path
        self.use_websockets = use_websockets
        self.client = None
        self.connected = False
        self.simulation_mode = False  # Modo simulação quando não consegue conectar
        self.connection_failures = 0  # Contador de falhas de conexão
        self.last_connection_attempt = None
        
        # Histórico para monitoramento de alertas
        self.power_history = []  # Histórico de potência CRAC
        self.temp_history = []  # Histórico de temperatura
        self.max_power_threshold = 95.0  # Limiar de potência máxima (%)
        self.max_power_duration = 10  # Duração mínima em minutos para alerta
        self.oscillation_threshold = 2.0  # Limiar de oscilação (°C)
        
        # Histórico de alertas para dashboard
        self.alert_history = []  # Histórico de alertas enviados
        self.max_alert_history = 100  # Limite de alertas no histórico
        
        # Controle de alertas duplicados (evita spam)
        self.last_alert_times = {}  # Última vez que cada tipo de alerta foi enviado
        self.alert_cooldown = 60  # Cooldown em segundos entre alertas do mesmo tipo
        
        # Reconexão automática
        self.auto_reconnect_enabled = True
        self.reconnect_interval = 30  # Tentar reconectar a cada 30 segundos
        self.last_reconnect_attempt = None
        
        # Configura logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self._setup_client()
    
    def _setup_client(self):
        """Configura o cliente MQTT."""
        # Usa WebSockets se especificado, senão usa TCP padrão
        if self.use_websockets:
            self.client = mqtt.Client(transport='websockets')
            # Configura path para WebSockets
            self.client.ws_set_options(path=self.broker_path)
        else:
            self.client = mqtt.Client()
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_log = self._on_log
        
        # Configurações de conexão
        self.client.reconnect_delay_set(min_delay=1, max_delay=120)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback quando conecta ao broker."""
        if rc == 0:
            previous_failures = self.connection_failures
            self.connected = True
            self.simulation_mode = False
            self.connection_failures = 0  # Reset apenas após conexão bem-sucedida
            if self.use_websockets:
                self.logger.info(f"Conectado ao broker MQTT via WebSocket em {self.broker_host}:{self.broker_port}{self.broker_path}")
            else:
                self.logger.info(f"Conectado ao broker MQTT em {self.broker_host}:{self.broker_port}")
            
            # Publica alerta de reconexão se havia falhas anteriores
            if previous_failures > 0:
                self._add_alert_to_history({
                    'timestamp': datetime.now().isoformat(),
                    'tipo': 'comunicação',
                    'mensagem': f'Conexão MQTT restabelecida após {previous_failures} tentativas',
                    'severidade': 'média',
                    'dados': {
                        'broker': f'{self.broker_host}:{self.broker_port}{self.broker_path if self.use_websockets else ""}',
                        'tentativas_anteriores': previous_failures,
                        'websocket': self.use_websockets
                    }
                })
        else:
            self.connected = False
            self.connection_failures += 1
            
            # Mensagens de erro mais descritivas
            error_messages = {
                1: "Código de retorno incorreto",
                2: "Identificador de cliente inválido",
                3: "Servidor indisponível",
                4: "Credenciais inválidas",
                5: "Não autorizado"
            }
            error_msg = error_messages.get(rc, f"Código desconhecido: {rc}")
            self.logger.error(f"Falha ao conectar ao broker. {error_msg} (código: {rc})")
            
            # Ativa modo simulação após múltiplas falhas
            if self.connection_failures >= 3:
                self.simulation_mode = True
                self.logger.warning("Modo simulação ativado devido a falhas de conexão")
                self._add_alert_to_history({
                    'timestamp': datetime.now().isoformat(),
                    'tipo': 'comunicação',
                    'mensagem': f'Falha ao conectar ao broker MQTT: {error_msg} (código: {rc})',
                    'severidade': 'alta',
                    'dados': {
                        'broker': f'{self.broker_host}:{self.broker_port}',
                        'codigo_erro': rc,
                        'mensagem_erro': error_msg,
                        'tentativas': self.connection_failures,
                        'modo_simulacao': True
                    }
                })
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback quando desconecta do broker."""
        was_connected = self.connected
        self.connected = False
        self.logger.info("Desconectado do broker MQTT")
        
        # Se estava conectado e desconectou inesperadamente, gera alerta
        if was_connected and rc != 0:
            self.connection_failures += 1
            self._add_alert_to_history({
                'timestamp': datetime.now().isoformat(),
                'tipo': 'comunicação',
                'mensagem': f'Conexão MQTT perdida inesperadamente (código: {rc})',
                'severidade': 'alta',
                'dados': {
                    'broker': f'{self.broker_host}:{self.broker_port}',
                    'codigo_erro': rc,
                    'tentativas_falhas': self.connection_failures
                }
            })
            
            # Ativa modo simulação após múltiplas falhas
            if self.connection_failures >= 3:
                self.simulation_mode = True
                self.logger.warning("Modo simulação ativado devido a falhas de conexão")
    
    def _on_publish(self, client, userdata, mid):
        """Callback quando publica mensagem."""
        self.logger.debug(f"Mensagem publicada. MID: {mid}")
    
    def _on_log(self, client, userdata, level, buf):
        """Callback para logs do cliente MQTT."""
        if level == mqtt.MQTT_LOG_ERR:
            self.logger.error(f"MQTT Error: {buf}")
        elif level == mqtt.MQTT_LOG_WARNING:
            self.logger.warning(f"MQTT Warning: {buf}")
        else:
            self.logger.debug(f"MQTT: {buf}")
    
    def connect(self, timeout=5):
        """
        Conecta ao broker MQTT.
        
        Args:
            timeout: Tempo máximo de espera para conexão (segundos)
        
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        import time
        import socket
        
        # Se já está conectado, retorna True
        if self.connected:
            return True
        
        # Se está em modo simulação e já tentou várias vezes, não tenta mais
        if self.simulation_mode and self.connection_failures >= 5:
            self.logger.debug("Em modo simulação, pulando tentativa de conexão")
            return False
        
        try:
            self.last_connection_attempt = datetime.now()
            
            # Verifica se o host é acessível antes de tentar conectar
            try:
                # Testa conectividade básica
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(2)
                result = test_socket.connect_ex((self.broker_host, self.broker_port))
                test_socket.close()
                
                if result != 0:
                    # Host inacessível - ativa modo simulação imediatamente
                    self.connection_failures += 1
                    self.simulation_mode = True
                    self.logger.warning(f"⚠️ Host {self.broker_host}:{self.broker_port} não acessível. Modo simulação ativado.")
                    self._add_alert_to_history({
                        'timestamp': datetime.now().isoformat(),
                        'tipo': 'comunicação',
                        'mensagem': f'Host {self.broker_host}:{self.broker_port} não acessível. Modo simulação ativado.',
                        'severidade': 'alta',
                        'dados': {
                            'broker': f'{self.broker_host}:{self.broker_port}',
                            'erro': 'Host não acessível',
                            'tentativas': self.connection_failures,
                            'modo_simulacao': True
                        }
                    })
                    return False
            except socket.gaierror as e:
                # Erro de DNS - ativa modo simulação imediatamente
                self.connection_failures += 1
                self.simulation_mode = True
                self.logger.warning(f"⚠️ Erro de DNS ao resolver {self.broker_host}. Modo simulação ativado.")
                self._add_alert_to_history({
                    'timestamp': datetime.now().isoformat(),
                    'tipo': 'comunicação',
                    'mensagem': f'Erro de DNS ao resolver {self.broker_host}. Modo simulação ativado.',
                    'severidade': 'alta',
                    'dados': {
                        'broker': f'{self.broker_host}:{self.broker_port}',
                        'erro': f'DNS Error: {str(e)}',
                        'tentativas': self.connection_failures,
                        'modo_simulacao': True
                    }
                })
                return False
            except Exception as e:
                self.logger.warning(f"Erro ao testar conectividade: {e}")
                # Continua tentando mesmo assim (pode ser temporário)
            
            # Tenta conectar ao broker MQTT
            if self.use_websockets:
                self.logger.info(f"Tentando conectar ao broker MQTT via WebSocket {self.broker_host}:{self.broker_port}{self.broker_path}...")
            else:
                self.logger.info(f"Tentando conectar ao broker MQTT {self.broker_host}:{self.broker_port}...")
            
            # Reinicia o cliente se necessário
            if self.client is None:
                self._setup_client()
            
            # Conecta (não bloqueia)
            self.client.connect_async(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
            
            # Aguarda conexão com timeout
            wait_time = 0
            check_interval = 0.1
            while wait_time < timeout:
                if self.connected:
                    if self.use_websockets:
                        self.logger.info(f"Conectado ao broker MQTT via WebSocket em {self.broker_host}:{self.broker_port}{self.broker_path}")
                    else:
                        self.logger.info(f"Conectado ao broker MQTT em {self.broker_host}:{self.broker_port}")
                    self.connection_failures = 0  # Reset contador em caso de sucesso
                    return True
                time.sleep(check_interval)
                wait_time += check_interval
            
            # Timeout atingido
            if not self.connected:
                self.connection_failures += 1
                self.logger.warning(f"Timeout ao conectar ao broker MQTT após {timeout}s")
                
                # Para o loop para evitar tentativas infinitas
                self.client.loop_stop()
                
                # Ativa modo simulação após 2 falhas (mais rápido para erros de timeout)
                if self.connection_failures >= 2:
                    self.simulation_mode = True
                    self.logger.warning("⚠️ Modo simulação ativado - Sistema continuará funcionando normalmente sem MQTT")
                    self._add_alert_to_history({
                        'timestamp': datetime.now().isoformat(),
                        'tipo': 'comunicação',
                        'mensagem': f'Falha ao conectar ao broker MQTT após {self.connection_failures} tentativas. Modo simulação ativado.',
                        'severidade': 'alta',
                        'dados': {
                            'broker': f'{self.broker_host}:{self.broker_port}',
                            'tentativas': self.connection_failures,
                            'timeout': timeout,
                            'modo_simulacao': True
                        }
                    })
                
                return False
            
            return True
            
        except socket.timeout:
            self.connection_failures += 1
            self.logger.error(f"Timeout ao conectar ao broker MQTT {self.broker_host}:{self.broker_port}")
            if self.client:
                self.client.loop_stop()
            return False
            
        except socket.gaierror as e:
            self.connection_failures += 1
            self.logger.error(f"Erro de DNS ao resolver {self.broker_host}: {e}")
            if self.client:
                self.client.loop_stop()
            
            # Erro de DNS ativa modo simulação imediatamente (host não existe)
            self.simulation_mode = True
            self.logger.warning(f"⚠️ Modo simulação ativado - Host {self.broker_host} não encontrado. Sistema continuará funcionando normalmente.")
            self._add_alert_to_history({
                'timestamp': datetime.now().isoformat(),
                'tipo': 'comunicação',
                'mensagem': f'Erro de DNS ao resolver {self.broker_host}. Modo simulação ativado.',
                'severidade': 'alta',
                'dados': {
                    'broker': f'{self.broker_host}:{self.broker_port}',
                    'erro': f'DNS Error: {str(e)}',
                    'tentativas': self.connection_failures,
                    'modo_simulacao': True
                }
            })
            return False
            
        except Exception as e:
            self.connection_failures += 1
            self.logger.error(f"Erro ao conectar ao broker: {e}", exc_info=True)
            
            if self.client:
                try:
                    self.client.loop_stop()
                except:
                    pass
            
            if self.connection_failures >= 3:
                self.simulation_mode = True
                self.logger.warning("Modo simulação ativado devido a falhas de conexão")
                self._add_alert_to_history({
                    'timestamp': datetime.now().isoformat(),
                    'tipo': 'comunicação',
                    'mensagem': f'Erro ao conectar ao broker MQTT: {str(e)}. Modo simulação ativado.',
                    'severidade': 'alta',
                    'dados': {
                        'broker': f'{self.broker_host}:{self.broker_port}',
                        'erro': str(e),
                        'tipo_erro': type(e).__name__,
                        'tentativas': self.connection_failures,
                        'modo_simulacao': True
                    }
                })
            
            return False
    
    def disconnect(self):
        """Desconecta do broker MQTT."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
    
    def _add_alert_to_history(self, alert_payload):
        """Adiciona alerta ao histórico interno."""
        self.alert_history.append(alert_payload)
        # Mantém apenas os últimos N alertas
        if len(self.alert_history) > self.max_alert_history:
            self.alert_history = self.alert_history[-self.max_alert_history:]
    
    def _try_auto_reconnect(self):
        """Tenta reconectar automaticamente se estiver em modo simulação."""
        if not self.auto_reconnect_enabled:
            return
        
        if not self.simulation_mode:
            return  # Já está conectado ou não precisa reconectar
        
        if self.connection_failures >= 10:
            # Após muitas falhas, tenta menos frequentemente
            if self.last_reconnect_attempt:
                time_since_last = (datetime.now() - self.last_reconnect_attempt).total_seconds()
                if time_since_last < 300:  # 5 minutos
                    return
        
        now = datetime.now()
        if self.last_reconnect_attempt:
            time_since_last = (now - self.last_reconnect_attempt).total_seconds()
            if time_since_last < self.reconnect_interval:
                return
        
        self.last_reconnect_attempt = now
        self.logger.info("Tentando reconexão automática ao broker MQTT...")
        self.connect(timeout=3)
    
    def publish_alert(self, alert_category, message, severity='média', data=None):
        """
        Publica alerta seguindo a estrutura especificada.
        
        Args:
            alert_category: Categoria do alerta ('crítico', 'eficiência', 'estabilidade', 'comunicação')
            message: Descrição human-readable do alerta
            severity: Nível de importância ('baixa', 'média', 'alta', 'crítica')
            data: Dicionário com valores relevantes do sistema (opcional)
        """
        # Tenta reconectar automaticamente se necessário
        if self.simulation_mode:
            self._try_auto_reconnect()
        
        payload = {
            'timestamp': datetime.now().isoformat(),
            'tipo': alert_category,
            'mensagem': message,
            'severidade': severity,
            'dados': data if data is not None else {}
        }
        
        # Sempre adiciona ao histórico interno
        self._add_alert_to_history(payload)
        
        # Se em modo simulação, apenas loga
        if self.simulation_mode:
            self.logger.info(f"[MODO SIMULAÇÃO] Alerta (não publicado): {message}")
            return True
        
        # Tenta conectar se não estiver conectado
        if not self.connected:
            self.logger.warning("Cliente MQTT não conectado. Tentando conectar...")
            if not self.connect():
                self.logger.warning(f"[MODO SIMULAÇÃO] Alerta não publicado (sem conexão): {message}")
                return False
        
        try:
            result = self.client.publish(
                'datacenter/fuzzy/alert',
                json.dumps(payload),
                qos=1
            )
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"Alerta publicado: {message}")
                return True
            else:
                self.logger.error(f"Erro ao publicar alerta. Código: {result.rc}")
                # Incrementa falhas de conexão
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    self.connection_failures += 1
                return False
        except Exception as e:
            self.logger.error(f"Exceção ao publicar alerta: {e}")
            self.connection_failures += 1
            return False
    
    def publish_control(self, control_data):
        """
        Publica informações de controle.
        
        Args:
            control_data: Dicionário com dados de controle
        """
        payload = {
            'timestamp': datetime.now().isoformat(),
            **control_data
        }
        
        # Se em modo simulação, apenas loga
        if self.simulation_mode:
            self.logger.debug("[MODO SIMULAÇÃO] Dados de controle (não publicados)")
            return True
        
        # Tenta conectar se não estiver conectado
        if not self.connected:
            if not self.connect():
                self.logger.debug("[MODO SIMULAÇÃO] Dados de controle não publicados (sem conexão)")
                return False
        
        try:
            result = self.client.publish(
                'datacenter/fuzzy/control',
                json.dumps(payload),
                qos=1
            )
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug("Dados de controle publicados")
                return True
            else:
                self.logger.error(f"Erro ao publicar controle. Código: {result.rc}")
                return False
        except Exception as e:
            self.logger.error(f"Exceção ao publicar controle: {e}")
            return False
    
    def publish_temperature(self, temperature, setpoint=None, error=None):
        """
        Publica temperatura atual.
        
        Args:
            temperature: Temperatura atual em °C
            setpoint: Temperatura desejada (setpoint) em °C
            error: Erro (setpoint - temperatura)
        """
        payload = {
            'timestamp': datetime.now().isoformat(),
            'temperature': temperature,
            'setpoint': setpoint,
            'error': error
        }
        
        # Se em modo simulação, apenas loga
        if self.simulation_mode:
            self.logger.debug(f"[MODO SIMULAÇÃO] Temperatura (não publicada): {temperature}°C")
            return True
        
        # Tenta conectar se não estiver conectado
        if not self.connected:
            if not self.connect():
                self.logger.debug(f"[MODO SIMULAÇÃO] Temperatura não publicada (sem conexão): {temperature}°C")
                return False
        
        try:
            result = self.client.publish(
                'datacenter/fuzzy/temp',
                json.dumps(payload),
                qos=1
            )
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Temperatura publicada: {temperature}°C")
                return True
            else:
                self.logger.error(f"Erro ao publicar temperatura. Código: {result.rc}")
                return False
        except Exception as e:
            self.logger.error(f"Exceção ao publicar temperatura: {e}")
            return False
    
    def check_temperature_alerts(self, current_temp, setpoint_temp, threshold_warning=2.0, threshold_critical=5.0):
        """
        Verifica se há alertas de temperatura e publica se necessário.
        
        Args:
            current_temp: Temperatura atual
            setpoint_temp: Temperatura desejada
            threshold_warning: Limiar para alerta de aviso
            threshold_critical: Limiar para alerta crítico
        """
        # Adiciona ao histórico
        self.temp_history.append({
            'temp': current_temp,
            'timestamp': datetime.now()
        })
        
        # Mantém apenas últimos 60 minutos (para análise de oscilações)
        cutoff_time = datetime.now().timestamp() - 3600
        self.temp_history = [h for h in self.temp_history 
                            if h['timestamp'].timestamp() > cutoff_time]
        
        # 1. Verifica temperatura crítica absoluta (< 18°C ou > 26°C) - RF4 obrigatório
        # Verifica cooldown para evitar spam
        now = datetime.now().timestamp()
        
        if current_temp < 18.0:
            alert_key = 'temp_critical_low'
            last_alert_time = self.last_alert_times.get(alert_key, 0)
            
            if now - last_alert_time >= self.alert_cooldown:
                self.last_alert_times[alert_key] = now
                self.publish_alert(
                    alert_category='crítico',
                    message=f"Temperatura crítica muito baixa! Atual: {current_temp:.2f}°C (limite: 18°C)",
                    severity='crítica',
                    data={
                        'temperatura_atual': current_temp,
                        'temperatura_setpoint': setpoint_temp,
                        'limite_minimo': 18.0,
                        'limite_maximo': 26.0,
                        'erro': abs(setpoint_temp - current_temp)
                    }
                )
        elif current_temp > 26.0:
            alert_key = 'temp_critical_high'
            last_alert_time = self.last_alert_times.get(alert_key, 0)
            
            if now - last_alert_time >= self.alert_cooldown:
                self.last_alert_times[alert_key] = now
                self.publish_alert(
                    alert_category='crítico',
                    message=f"Temperatura crítica muito alta! Atual: {current_temp:.2f}°C (limite: 26°C)",
                    severity='crítica',
                    data={
                        'temperatura_atual': current_temp,
                        'temperatura_setpoint': setpoint_temp,
                        'limite_minimo': 18.0,
                        'limite_maximo': 26.0,
                        'erro': abs(setpoint_temp - current_temp)
                    }
                )
        
        # 2. Verifica erro em relação ao setpoint
        error = abs(setpoint_temp - current_temp)
        
        if error >= threshold_critical:
            self.publish_alert(
                alert_category='crítico',
                message=f"Temperatura crítica! Atual: {current_temp:.2f}°C, Setpoint: {setpoint_temp:.2f}°C, Erro: {error:.2f}°C",
                severity='crítica',
                data={
                    'temperatura_atual': current_temp,
                    'temperatura_setpoint': setpoint_temp,
                    'erro': error,
                    'threshold_critico': threshold_critical,
                    'threshold_aviso': threshold_warning
                }
            )
        elif error >= threshold_warning:
            self.publish_alert(
                alert_category='estabilidade',
                message=f"Temperatura fora do ideal. Atual: {current_temp:.2f}°C, Setpoint: {setpoint_temp:.2f}°C, Erro: {error:.2f}°C",
                severity='média',
                data={
                    'temperatura_atual': current_temp,
                    'temperatura_setpoint': setpoint_temp,
                    'erro': error,
                    'threshold_critico': threshold_critical,
                    'threshold_aviso': threshold_warning
                }
            )
        
        # 3. Verifica oscilações excessivas
        self._check_oscillations()
    
    def check_power_alerts(self, p_crac):
        """
        Verifica se há alertas de potência CRAC máxima por tempo prolongado.
        RF4 obrigatório: Potência CRAC máxima por tempo prolongado.
        
        Args:
            p_crac: Potência CRAC atual (%)
        """
        # Adiciona ao histórico
        self.power_history.append({
            'power': p_crac,
            'timestamp': datetime.now()
        })
        
        # Mantém apenas últimos 60 minutos
        cutoff_time = datetime.now().timestamp() - 3600
        self.power_history = [h for h in self.power_history 
                             if h['timestamp'].timestamp() > cutoff_time]
        
        # Verifica se potência está acima do limiar
        if p_crac >= self.max_power_threshold:
            # Conta quantos minutos consecutivos acima do limiar
            consecutive_minutes = 0
            for entry in reversed(self.power_history):
                if entry['power'] >= self.max_power_threshold:
                    consecutive_minutes += 1
                else:
                    break
            
            # Alerta se exceder duração mínima
            if consecutive_minutes >= self.max_power_duration:
                # Verifica cooldown para evitar spam
                alert_key = 'power_max'
                now = datetime.now().timestamp()
                last_alert_time = self.last_alert_times.get(alert_key, 0)
                
                # Cooldown maior para alertas de potência (5 minutos)
                if now - last_alert_time >= (self.alert_cooldown * 5):
                    self.last_alert_times[alert_key] = now
                    
                    self.publish_alert(
                        alert_category='eficiência',
                        message=f"Potência CRAC máxima por tempo prolongado! {p_crac:.2f}% há {consecutive_minutes} minutos (limite: {self.max_power_threshold}%)",
                        severity='crítica',
                        data={
                            'potencia_crac': p_crac,
                            'duracao_minutos': consecutive_minutes,
                            'limiar_potencia': self.max_power_threshold,
                            'duracao_minima_alert': self.max_power_duration
                        }
                    )
    
    def _check_oscillations(self):
        """
        Verifica se há oscilações excessivas no sistema.
        RF4 obrigatório: Oscilações excessivas no sistema.
        """
        if len(self.temp_history) < 10:
            return  # Precisa de histórico suficiente
        
        # Calcula variação (desvio padrão) das últimas 10 leituras
        recent_temps = [h['temp'] for h in self.temp_history[-10:]]
        
        if len(recent_temps) < 2:
            return
        
        # Calcula desvio padrão
        mean_temp = sum(recent_temps) / len(recent_temps)
        variance = sum((t - mean_temp) ** 2 for t in recent_temps) / len(recent_temps)
        std_dev = variance ** 0.5
        
        # Verifica se desvio padrão excede limiar
        if std_dev >= self.oscillation_threshold:
            # Calcula amplitude (diferença entre máximo e mínimo)
            amplitude = max(recent_temps) - min(recent_temps)
            
            # Verifica se amplitude é significativa
            if amplitude >= self.oscillation_threshold * 2:
                # Verifica cooldown para evitar spam
                alert_key = 'oscillations'
                now = datetime.now().timestamp()
                last_alert_time = self.last_alert_times.get(alert_key, 0)
                
                if now - last_alert_time >= self.alert_cooldown:
                    self.last_alert_times[alert_key] = now
                    
                    # Calcula número de mudanças de direção (indicador de oscilação)
                    direction_changes = 0
                    for i in range(1, len(recent_temps) - 1):
                        if (recent_temps[i] > recent_temps[i-1] and recent_temps[i+1] < recent_temps[i]) or \
                           (recent_temps[i] < recent_temps[i-1] and recent_temps[i+1] > recent_temps[i]):
                            direction_changes += 1
                    
                    self.publish_alert(
                        alert_category='estabilidade',
                        message=f"Oscilações excessivas detectadas! Amplitude: {amplitude:.2f}°C, Desvio padrão: {std_dev:.2f}°C (limite: {self.oscillation_threshold}°C)",
                        severity='alta',
                        data={
                            'amplitude': amplitude,
                            'desvio_padrao': std_dev,
                            'temperatura_media': mean_temp,
                            'temperatura_minima': min(recent_temps),
                            'temperatura_maxima': max(recent_temps),
                            'mudancas_direcao': direction_changes,
                            'limiar_oscillacao': self.oscillation_threshold,
                            'numero_leituras': len(recent_temps)
                        }
                    )
    
    def is_connected(self):
        """Verifica se está conectado ao broker."""
        return self.connected
    
    def get_status(self):
        """Retorna status completo do cliente MQTT."""
        return {
            'connected': self.connected,
            'simulation_mode': self.simulation_mode,
            'broker_host': self.broker_host,
            'broker_port': self.broker_port,
            'broker_path': self.broker_path if self.use_websockets else None,
            'use_websockets': self.use_websockets,
            'connection_failures': self.connection_failures,
            'last_connection_attempt': self.last_connection_attempt.isoformat() if self.last_connection_attempt else None
        }
    
    def get_alert_history(self, limit=50):
        """Retorna histórico de alertas."""
        return self.alert_history[-limit:] if limit else self.alert_history

