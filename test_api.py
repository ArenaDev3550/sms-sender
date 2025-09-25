#!/usr/bin/env python3
"""
Script de teste para a API SMS com multithreading
"""
import requests
import json
import time
import threading

# URL base da API
BASE_URL = "http://localhost:5000"

def test_single_sms():
    """Teste de SMS único síncrono"""
    print("=== Teste SMS Único (Síncrono) ===")
    url = f"{BASE_URL}/send-sms"
    data = {
        "to": "5511999999999",
        "message": "Teste de SMS único"
    }
    
    start_time = time.time()
    response = requests.post(url, json=data)
    end_time = time.time()
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    print(f"Tempo: {end_time - start_time:.2f}s\n")

def test_async_sms():
    """Teste de SMS único assíncrono"""
    print("=== Teste SMS Único (Assíncrono) ===")
    url = f"{BASE_URL}/send-sms"
    data = {
        "to": "5511999999999",
        "message": "Teste de SMS assíncrono",
        "async": True
    }
    
    # Envia SMS assíncrono
    response = requests.post(url, json=data)
    print(f"Status inicial: {response.status_code}")
    print(f"Resposta: {response.json()}")
    
    if response.status_code == 202:
        sms_id = response.json().get("sms_id")
        
        # Verifica status
        for i in range(5):
            time.sleep(1)
            status_response = requests.get(f"{BASE_URL}/sms-status/{sms_id}")
            print(f"Status check {i+1}: {status_response.json()}")
            
            if status_response.status_code == 200:
                break
    print()

def test_bulk_sms():
    """Teste de SMS em lote"""
    print("=== Teste SMS em Lote ===")
    url = f"{BASE_URL}/send-bulk-sms"
    data = {
        "recipients": [
            "5511999999999",
            "5511888888888",
            "5511777777777",
            "5511666666666",
            "5511555555555"
        ],
        "message": "Teste de SMS em lote com multithreading",
        "max_workers": 3
    }
    
    start_time = time.time()
    response = requests.post(url, json=data)
    end_time = time.time()
    
    print(f"Status: {response.status_code}")
    print(f"Tempo total: {end_time - start_time:.2f}s")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total: {result['total']}")
        print(f"Enviados: {result['sent']}")
        print(f"Erros: {result['errors']}")
        print(f"Resultados individuais:")
        for r in result['results']:
            print(f"  - {r['to']}: {r['status']} ({r.get('duration', 'N/A')}s)")
    print()

def test_health_and_stats():
    """Teste dos endpoints de monitoramento"""
    print("=== Health Check ===")
    health_response = requests.get(f"{BASE_URL}/health")
    print(f"Health: {health_response.json()}")
    
    print("\n=== Estatísticas ===")
    stats_response = requests.get(f"{BASE_URL}/stats")
    print(f"Stats: {stats_response.json()}")
    print()

def stress_test():
    """Teste de stress com múltiplas requests simultâneas"""
    print("=== Teste de Stress ===")
    
    def send_sms_thread(thread_id):
        url = f"{BASE_URL}/send-sms"
        data = {
            "to": f"551199999999{thread_id}",
            "message": f"Teste stress thread {thread_id}",
            "async": True
        }
        
        start_time = time.time()
        response = requests.post(url, json=data)
        end_time = time.time()
        
        print(f"Thread {thread_id}: {response.status_code} - {end_time - start_time:.2f}s")
    
    # Criar 10 threads simultâneas
    threads = []
    start_time = time.time()
    
    for i in range(10):
        thread = threading.Thread(target=send_sms_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Aguardar todas as threads
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    print(f"Teste de stress concluído em {end_time - start_time:.2f}s\n")

if __name__ == "__main__":
    print("Iniciando testes da API SMS...")
    print("Certifique-se de que a API está rodando em localhost:5000\n")
    
    try:
        # Testes básicos
        test_single_sms()
        test_async_sms()
        test_bulk_sms()
        test_health_and_stats()
        
        # Teste de stress
        stress_test()
        
        # Stats finais
        test_health_and_stats()
        
    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar à API. Verifique se ela está rodando.")
    except Exception as e:
        print(f"Erro durante os testes: {e}")