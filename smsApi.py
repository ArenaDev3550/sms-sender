from flask import Flask, request, jsonify
import subprocess
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import uuid
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Pool de threads para processar SMS
thread_pool = ThreadPoolExecutor(max_workers=10)

# Dicionário para rastrear status dos SMS
sms_status = {}

# Queue para batch processing
sms_queue = Queue()

class SMSSender:
    def __init__(self):
        self.lock = threading.Lock()
        
    def send_single_sms(self, number, message, sms_id=None):
        """Envia um SMS individual"""
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
            
            result = {
                "status": "sent",
                "to": number,
                "message": message,
                "duration": round(end_time - start_time, 2),
                "timestamp": datetime.now().isoformat()
            }
            
            if sms_id:
                with self.lock:
                    sms_status[sms_id] = result
                    
            logger.info(f"SMS enviado para {number} em {result['duration']}s")
            return result
            
        except subprocess.TimeoutExpired:
            error_result = {
                "status": "error",
                "detail": "Timeout ao enviar SMS",
                "to": number,
                "timestamp": datetime.now().isoformat()
            }
            if sms_id:
                with self.lock:
                    sms_status[sms_id] = error_result
            return error_result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "detail": str(e),
                "to": number,
                "timestamp": datetime.now().isoformat()
            }
            if sms_id:
                with self.lock:
                    sms_status[sms_id] = error_result
            return error_result

# Instância do sender
sms_sender = SMSSender()

@app.route("/send-sms", methods=["POST"])
def send_sms():
    """Envia SMS único de forma assíncrona"""
    data = request.get_json(force=True)
    number = data.get("to")
    message = data.get("message")
    async_mode = data.get("async", False)

    if not number or not message:
        return jsonify({"error": "Campos 'to' e 'message' são obrigatórios"}), 400

    if async_mode:
        # Modo assíncrono - retorna imediatamente
        sms_id = str(uuid.uuid4())
        future = thread_pool.submit(sms_sender.send_single_sms, number, message, sms_id)
        
        return jsonify({
            "status": "queued",
            "sms_id": sms_id,
            "message": "SMS adicionado à fila de processamento",
            "check_status_url": f"/sms-status/{sms_id}"
        }), 202
    else:
        # Modo síncrono - aguarda o envio
        result = sms_sender.send_single_sms(number, message)
        if result["status"] == "sent":
            return jsonify(result), 200
        else:
            return jsonify(result), 500

@app.route("/send-bulk-sms", methods=["POST"])
def send_bulk_sms():
    """Envia SMS em lote usando multithreading com mensagens personalizadas"""
    data = request.get_json(force=True)
    recipients = data.get("recipients", [])
    message = data.get("message")  # Mensagem padrão (opcional)
    max_workers = data.get("max_workers", 5)  # Limite de threads simultâneas
    
    if not recipients:
        return jsonify({"error": "Campo 'recipients' é obrigatório"}), 400
    
    if not isinstance(recipients, list):
        return jsonify({"error": "Campo 'recipients' deve ser uma lista"}), 400
    
    # Validar formato dos recipients
    processed_recipients = []
    
    for i, recipient in enumerate(recipients):
        if isinstance(recipient, str):
            # Formato antigo: lista de números com mensagem padrão
            if not message:
                return jsonify({
                    "error": f"Mensagem é obrigatória quando recipients[{i}] é uma string"
                }), 400
            processed_recipients.append({
                "to": recipient,
                "message": message
            })
        elif isinstance(recipient, dict):
            # Formato novo: objetos com "to" e "message"
            to_number = recipient.get("to")
            msg = recipient.get("message")
            
            if not to_number:
                return jsonify({
                    "error": f"Campo 'to' é obrigatório em recipients[{i}]"
                }), 400
            
            if not msg:
                # Se não tem mensagem específica, usa a mensagem padrão
                if not message:
                    return jsonify({
                        "error": f"Mensagem é obrigatória em recipients[{i}] ou como mensagem padrão"
                    }), 400
                msg = message
            
            processed_recipients.append({
                "to": to_number,
                "message": msg
            })
        else:
            return jsonify({
                "error": f"recipients[{i}] deve ser uma string ou objeto com 'to' e 'message'"
            }), 400
    
    if not processed_recipients:
        return jsonify({"error": "Nenhum destinatário válido encontrado"}), 400
    
    # Limite de workers para não sobrecarregar o sistema
    max_workers = min(max_workers, 10)
    
    batch_id = str(uuid.uuid4())
    results = []
    
    # Usar ThreadPoolExecutor para envio em paralelo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submeter todas as tarefas com mensagens personalizadas
        future_to_recipient = {
            executor.submit(sms_sender.send_single_sms, recipient["to"], recipient["message"]): recipient 
            for recipient in processed_recipients
        }
        
        # Coletar resultados conforme completam
        for future in as_completed(future_to_recipient):
            recipient = future_to_recipient[future]
            try:
                result = future.result(timeout=30)
                results.append(result)
            except Exception as e:
                results.append({
                    "status": "error",
                    "to": recipient["to"],
                    "message": recipient["message"],
                    "detail": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    # Estatísticas
    sent_count = len([r for r in results if r["status"] == "sent"])
    error_count = len(results) - sent_count
    
    return jsonify({
        "batch_id": batch_id,
        "total": len(processed_recipients),
        "sent": sent_count,
        "errors": error_count,
        "results": results
    })

@app.route("/sms-status/<sms_id>", methods=["GET"])
def get_sms_status(sms_id):
    """Consulta o status de um SMS enviado assincronamente"""
    with sms_sender.lock:
        status = sms_status.get(sms_id)
    
    if status:
        return jsonify(status)
    else:
        return jsonify({
            "status": "not_found",
            "message": "SMS ID não encontrado ou ainda processando"
        }), 404

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_threads": threading.active_count(),
        "pending_sms": sms_queue.qsize() if hasattr(sms_queue, 'qsize') else 0
    })

@app.route("/stats", methods=["GET"])
def get_stats():
    """Retorna estatísticas da API"""
    with sms_sender.lock:
        total_sms = len(sms_status)
        sent_sms = len([s for s in sms_status.values() if s.get("status") == "sent"])
        error_sms = total_sms - sent_sms
    
    return jsonify({
        "total_sms": total_sms,
        "sent_sms": sent_sms,
        "error_sms": error_sms,
        "active_threads": threading.active_count(),
        "success_rate": round((sent_sms / total_sms * 100), 2) if total_sms > 0 else 0
    })

if __name__ == "__main__":
    logger.info("Iniciando SMS API com suporte a multithreading...")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
