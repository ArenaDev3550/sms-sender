import subprocess
import threading
import time
import logging
from datetime import datetime, timedelta
from collections import deque
import uuid

logger = logging.getLogger(__name__)

class SMSSender:
    def __init__(self, rate_limit=500, rate_window=30):
        """
        Inicializa o SMS Sender com rate limiting
        
        Args:
            rate_limit (int): Número máximo de SMS por janela de tempo (padrão: 20)
            rate_window (int): Janela de tempo em segundos (padrão: 60 = 1 minuto)
        """
        self.lock = threading.Lock()
        self.rate_limit = rate_limit
        self.rate_window = rate_window
        
        # Deque para rastrear timestamps dos SMS enviados
        self.sms_timestamps = deque()
        
        # Dicionário para rastrear status dos SMS
        self.sms_status = {}
        
        # Estatísticas
        self.stats = {
            'total_sent': 0,
            'total_errors': 0,
            'rate_limited': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"SMSSender inicializado - Rate limit: {rate_limit} SMS por {rate_window}s")
    
    def _check_rate_limit(self):
        """
        Verifica se o rate limit foi atingido
        
        Returns:
            tuple: (pode_enviar: bool, tempo_espera: float)
        """
        current_time = time.time()
        cutoff_time = current_time - self.rate_window
        
        with self.lock:
            # Remove timestamps antigos (fora da janela)
            while self.sms_timestamps and self.sms_timestamps[0] < cutoff_time:
                self.sms_timestamps.popleft()
            
            # Verifica se pode enviar
            if len(self.sms_timestamps) < self.rate_limit:
                return True, 0
            else:
                # Calcula tempo de espera até que possa enviar
                oldest_timestamp = self.sms_timestamps[0]
                wait_time = oldest_timestamp + self.rate_window - current_time
                return False, max(0, wait_time)
    
    def _add_timestamp(self):
        """Adiciona timestamp do SMS enviado ao controle de rate"""
        with self.lock:
            self.sms_timestamps.append(time.time())
    
    def wait_for_rate_limit(self, max_wait_time=None):
        """
        Aguarda até que seja possível enviar um SMS respeitando o rate limit
        
        Args:
            max_wait_time (float): Tempo máximo de espera em segundos (None = sem limite)
            
        Returns:
            bool: True se pode enviar, False se atingiu o tempo máximo de espera
        """
        start_wait = time.time()
        
        while True:
            can_send, wait_time = self._check_rate_limit()
            
            if can_send:
                return True
            
            # Verifica se atingiu o tempo máximo de espera
            if max_wait_time and (time.time() - start_wait) >= max_wait_time:
                logger.warning(f"Tempo máximo de espera atingido: {max_wait_time}s")
                return False
            
            # Aguarda um pouco antes de verificar novamente
            sleep_time = min(wait_time, 1.0)  # Máximo 1 segundo por verificação
            logger.info(f"Rate limit atingido. Aguardando {sleep_time:.1f}s...")
            time.sleep(sleep_time)
    
    def send_single_sms(self, number, message, sms_id=None, respect_rate_limit=True, max_wait_time=None):
        """
        Envia um SMS individual com controle de rate limiting
        
        Args:
            number (str): Número do destinatário
            message (str): Mensagem a ser enviada
            sms_id (str): ID único do SMS (opcional)
            respect_rate_limit (bool): Se deve respeitar o rate limit (padrão: True)
            max_wait_time (float): Tempo máximo de espera pelo rate limit (None = sem limite)
            
        Returns:
            dict: Resultado do envio
        """
        # Verificar rate limit se habilitado
        if respect_rate_limit:
            can_send, wait_time = self._check_rate_limit()
            
            if not can_send:
                if max_wait_time == 0:
                    # Não aguarda, retorna erro imediatamente
                    with self.lock:
                        self.stats['rate_limited'] += 1
                    
                    error_result = {
                        "status": "rate_limited",
                        "detail": f"Rate limit atingido. Aguarde {wait_time:.1f}s",
                        "to": number,
                        "wait_time": wait_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if sms_id:
                        with self.lock:
                            self.sms_status[sms_id] = error_result
                    
                    return error_result
                
                # Aguarda respeitando o rate limit
                if not self.wait_for_rate_limit(max_wait_time):
                    with self.lock:
                        self.stats['rate_limited'] += 1
                    
                    error_result = {
                        "status": "rate_limited",
                        "detail": "Tempo máximo de espera pelo rate limit atingido",
                        "to": number,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if sms_id:
                        with self.lock:
                            self.sms_status[sms_id] = error_result
                    
                    return error_result
        
        # Enviar SMS
        try:
            start_time = time.time()
            cmd = ["termux-sms-send", "-n", str(number), message]
            
            # Executa o comando com timeout
            process = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            end_time = time.time()
            
            # Adiciona timestamp ao controle de rate
            if respect_rate_limit:
                self._add_timestamp()
            
            # Atualiza estatísticas
            with self.lock:
                self.stats['total_sent'] += 1
            
            result = {
                "status": "sent",
                "to": number,
                "message": message,
                "duration": round(end_time - start_time, 2),
                "timestamp": datetime.now().isoformat(),
                "rate_limit_info": {
                    "current_count": len(self.sms_timestamps),
                    "limit": self.rate_limit,
                    "window": self.rate_window
                }
            }
            
            if sms_id:
                with self.lock:
                    self.sms_status[sms_id] = result
                    
            logger.info(f"SMS enviado para {number} em {result['duration']}s "
                       f"({len(self.sms_timestamps)}/{self.rate_limit} SMS na janela)")
            return result
            
        except subprocess.TimeoutExpired:
            with self.lock:
                self.stats['total_errors'] += 1
            
            error_result = {
                "status": "error",
                "detail": "Timeout ao enviar SMS",
                "to": number,
                "timestamp": datetime.now().isoformat()
            }
            if sms_id:
                with self.lock:
                    self.sms_status[sms_id] = error_result
            return error_result
            
        except Exception as e:
            with self.lock:
                self.stats['total_errors'] += 1
            
            error_result = {
                "status": "error",
                "detail": str(e),
                "to": number,
                "timestamp": datetime.now().isoformat()
            }
            if sms_id:
                with self.lock:
                    self.sms_status[sms_id] = error_result
            return error_result
    
    def get_rate_limit_status(self):
        """
        Retorna informações sobre o status atual do rate limiting
        
        Returns:
            dict: Informações do rate limit
        """
        can_send, wait_time = self._check_rate_limit()
        
        # Não usar lock aqui pois pode ser chamado de dentro de get_stats() que já tem lock
        current_count = len(self.sms_timestamps)
        
        return {
            "can_send": can_send,
            "wait_time": wait_time,
            "current_count": current_count,
            "rate_limit": self.rate_limit,
            "rate_window": self.rate_window,
            "remaining": max(0, self.rate_limit - current_count),
            "reset_time": datetime.fromtimestamp(
                self.sms_timestamps[0] + self.rate_window
            ).isoformat() if self.sms_timestamps else None
        }
    
    def get_sms_status(self, sms_id):
        """
        Retorna o status de um SMS específico
        
        Args:
            sms_id (str): ID do SMS
            
        Returns:
            dict: Status do SMS ou None se não encontrado
        """
        with self.lock:
            return self.sms_status.get(sms_id)
    
    def get_stats(self):
        """
        Retorna estatísticas do SMS Sender
        
        Returns:
            dict: Estatísticas detalhadas
        """
        with self.lock:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
            total_requests = self.stats['total_sent'] + self.stats['total_errors'] + self.stats['rate_limited']
            
            return {
                "total_sent": self.stats['total_sent'],
                "total_errors": self.stats['total_errors'],
                "rate_limited": self.stats['rate_limited'],
                "total_requests": total_requests,
                "success_rate": round(
                    (self.stats['total_sent'] / total_requests * 100) if total_requests > 0 else 0, 2
                ),
                "uptime_seconds": round(uptime, 2),
                "avg_sms_per_minute": round(
                    (self.stats['total_sent'] / (uptime / 60)) if uptime > 0 else 0, 2
                ),
                "rate_limit_config": {
                    "limit": self.rate_limit,
                    "window": self.rate_window
                },
                "current_rate_status": self.get_rate_limit_status()
            }
    
    def clear_old_status(self, max_age_hours=24):
        """
        Remove status antigos para evitar consumo excessivo de memória
        
        Args:
            max_age_hours (int): Idade máxima em horas para manter os status
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with self.lock:
            old_ids = []
            for sms_id, status in self.sms_status.items():
                try:
                    status_time = datetime.fromisoformat(status['timestamp'])
                    if status_time < cutoff_time:
                        old_ids.append(sms_id)
                except:
                    # Se não conseguir parsear o timestamp, remove também
                    old_ids.append(sms_id)
            
            for sms_id in old_ids:
                del self.sms_status[sms_id]
            
            if old_ids:
                logger.info(f"Removidos {len(old_ids)} status antigos de SMS")