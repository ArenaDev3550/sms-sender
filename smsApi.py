from flask import Flask, request, jsonify
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import uuid
from datetime import datetime

# Importar a classe SMSSender do arquivo separado
from sms_sender import SMSSender

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Pool de threads para processar SMS
thread_pool = ThreadPoolExecutor(max_workers=10)

# Queue para batch processing
sms_queue = Queue()

# Instância do sender com rate limiting (20 SMS por minuto)
sms_sender = SMSSender(rate_limit=20, rate_window=60)

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
    status = sms_sender.get_sms_status(sms_id)
    
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

@app.route("/rate-limit", methods=["GET"])
def get_rate_limit_status():
    """Retorna informações detalhadas sobre o rate limiting"""
    return jsonify(sms_sender.get_rate_limit_status())

@app.route("/stats", methods=["GET"])
def get_stats():
    """Retorna estatísticas da API"""
    # Usar as estatísticas da classe SMSSender
    sms_stats = sms_sender.get_stats()
    
    return jsonify({
        "sms_sender_stats": sms_stats,
        "active_threads": threading.active_count(),
        "rate_limit_status": sms_sender.get_rate_limit_status()
    })

if __name__ == "__main__":
    logger.info("Iniciando SMS API com suporte a multithreading...")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
