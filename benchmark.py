#!/usr/bin/env python3
"""
Benchmark para testar performance da SMS API
"""
import requests
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:5000"

class SMSBenchmark:
    def __init__(self):
        self.results = []
        self.lock = threading.Lock()
    
    def single_sms_test(self, count=10):
        """Teste de SMS únicos sequenciais"""
        print(f"\n=== Teste SMS Únicos Sequenciais ({count} SMS) ===")
        
        times = []
        successes = 0
        
        for i in range(count):
            start_time = time.time()
            
            response = requests.post(f"{BASE_URL}/send-sms", json={
                "to": f"5511{str(i).zfill(9)}",
                "message": f"Teste sequencial {i+1}"
            })
            
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            if response.status_code == 200:
                successes += 1
            
            print(f"SMS {i+1}: {response.status_code} - {duration:.2f}s")
        
        self._print_stats("SMS Únicos Sequenciais", times, successes, count)
    
    def async_sms_test(self, count=10):
        """Teste de SMS assíncronos"""
        print(f"\n=== Teste SMS Assíncronos ({count} SMS) ===")
        
        times = []
        successes = 0
        
        for i in range(count):
            start_time = time.time()
            
            response = requests.post(f"{BASE_URL}/send-sms", json={
                "to": f"5522{str(i).zfill(9)}",
                "message": f"Teste assíncrono {i+1}",
                "async": True
            })
            
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            if response.status_code == 202:
                successes += 1
            
            print(f"SMS {i+1}: {response.status_code} - {duration:.2f}s")
        
        self._print_stats("SMS Assíncronos", times, successes, count)
    
    def bulk_sms_test(self, batch_sizes=[5, 10, 20]):
        """Teste de SMS em lote com diferentes tamanhos"""
        print(f"\n=== Teste SMS em Lote ===")
        
        for batch_size in batch_sizes:
            print(f"\nTestando lote de {batch_size} SMS...")
            
            recipients = [f"5533{str(i).zfill(9)}" for i in range(batch_size)]
            
            start_time = time.time()
            
            response = requests.post(f"{BASE_URL}/send-bulk-sms", json={
                "recipients": recipients,
                "message": f"Teste lote {batch_size} SMS",
                "max_workers": min(batch_size, 5)
            })
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"Lote {batch_size}: {duration:.2f}s")
                print(f"  - Total: {result['total']}")
                print(f"  - Enviados: {result['sent']}")
                print(f"  - Erros: {result['errors']}")
                print(f"  - Taxa sucesso: {(result['sent']/result['total']*100):.1f}%")
                print(f"  - SMS/segundo: {(result['total']/duration):.2f}")
            else:
                print(f"Erro no lote {batch_size}: {response.status_code}")
    
    def concurrent_requests_test(self, threads=5, requests_per_thread=5):
        """Teste de requests simultâneas"""
        print(f"\n=== Teste Requests Simultâneas ({threads} threads, {requests_per_thread} req/thread) ===")
        
        def worker_thread(thread_id):
            thread_times = []
            thread_successes = 0
            
            for i in range(requests_per_thread):
                start_time = time.time()
                
                response = requests.post(f"{BASE_URL}/send-sms", json={
                    "to": f"5544{str(thread_id).zfill(3)}{str(i).zfill(6)}",
                    "message": f"Thread {thread_id} - Request {i+1}",
                    "async": True
                })
                
                end_time = time.time()
                duration = end_time - start_time
                thread_times.append(duration)
                
                if response.status_code == 202:
                    thread_successes += 1
            
            with self.lock:
                self.results.extend(thread_times)
            
            return thread_successes, thread_times
        
        # Executar threads
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(threads)]
            thread_results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calcular estatísticas
        total_requests = threads * requests_per_thread
        total_successes = sum(result[0] for result in thread_results)
        all_times = []
        for result in thread_results:
            all_times.extend(result[1])
        
        print(f"Duração total: {total_duration:.2f}s")
        print(f"Requests totais: {total_requests}")
        print(f"Sucessos: {total_successes}")
        print(f"Taxa sucesso: {(total_successes/total_requests*100):.1f}%")
        print(f"Requests/segundo: {(total_requests/total_duration):.2f}")
        print(f"Tempo médio por request: {statistics.mean(all_times):.3f}s")
        print(f"Tempo mín/máx: {min(all_times):.3f}s / {max(all_times):.3f}s")
    
    def memory_usage_test(self):
        """Teste de uso de recursos"""
        print(f"\n=== Teste de Recursos ===")
        
        # Health check antes
        health_before = requests.get(f"{BASE_URL}/health").json()
        
        # Fazer várias requests
        for i in range(20):
            requests.post(f"{BASE_URL}/send-sms", json={
                "to": f"5555{str(i).zfill(9)}",
                "message": f"Teste recursos {i+1}",
                "async": True
            })
        
        time.sleep(2)  # Aguardar processamento
        
        # Health check depois
        health_after = requests.get(f"{BASE_URL}/health").json()
        stats = requests.get(f"{BASE_URL}/stats").json()
        
        print("Antes:")
        print(f"  - Threads ativas: {health_before.get('active_threads', 'N/A')}")
        
        print("Depois:")
        print(f"  - Threads ativas: {health_after.get('active_threads', 'N/A')}")
        print(f"  - SMS processados: {stats.get('total_sms', 'N/A')}")
        print(f"  - Taxa sucesso: {stats.get('success_rate', 'N/A')}%")
    
    def _print_stats(self, test_name, times, successes, total):
        """Imprime estatísticas de um teste"""
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            success_rate = (successes / total) * 100
            throughput = total / sum(times)
            
            print(f"\nResultados {test_name}:")
            print(f"  - Sucessos: {successes}/{total} ({success_rate:.1f}%)")
            print(f"  - Tempo médio: {avg_time:.3f}s")
            print(f"  - Tempo mín/máx: {min_time:.3f}s / {max_time:.3f}s")
            print(f"  - Throughput: {throughput:.2f} SMS/s")

def main():
    print("=== SMS API Benchmark ===")
    print("Certifique-se de que a API está rodando em localhost:5000")
    
    try:
        # Verificar se a API está online
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("Erro: API não está respondendo corretamente")
            return
    except requests.exceptions.RequestException as e:
        print(f"Erro: Não foi possível conectar à API: {e}")
        return
    
    benchmark = SMSBenchmark()
    
    # Executar testes
    benchmark.single_sms_test(count=5)  # Reduzido para teste
    benchmark.async_sms_test(count=5)
    benchmark.bulk_sms_test(batch_sizes=[3, 5, 8])
    benchmark.concurrent_requests_test(threads=3, requests_per_thread=3)
    benchmark.memory_usage_test()
    
    print("\n=== Benchmark Concluído ===")

if __name__ == "__main__":
    main()