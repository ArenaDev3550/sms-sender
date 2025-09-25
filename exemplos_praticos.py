#!/usr/bin/env python3
"""
Exemplo prático de uso da API SMS com mensagens personalizadas
Este script demonstra cenários reais de uso da nova funcionalidade
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def exemplo_loja_online():
    """Exemplo: Loja online enviando status diferentes para diferentes clientes"""
    print("=== Exemplo: Loja Online ===")
    print("Enviando status de pedidos personalizados para cada cliente...\n")
    
    clientes = [
        {
            "to": "5511999999999",
            "message": "Olá João! Seu pedido #1234 foi CONFIRMADO e será entregue em 2 dias úteis. Obrigado pela preferência!"
        },
        {
            "to": "5511888888888",
            "message": "Oi Maria! Seu pedido #1235 foi ENVIADO com código de rastreamento BR123456. Acompanhe pelo site."
        },
        {
            "to": "5511777777777",
            "message": "E aí Pedro! Seu pedido #1236 foi ENTREGUE. Avalie sua experiência em nosso site. Abraços!"
        }
    ]
    
    response = requests.post(f"{BASE_URL}/send-bulk-sms", json={
        "recipients": clientes,
        "max_workers": 3
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['sent']} mensagens enviadas com sucesso!")
        print(f"❌ {result['errors']} erros")
        for r in result['results']:
            status_icon = "✅" if r['status'] == 'sent' else "❌"
            print(f"  {status_icon} {r['to']}: {r['message'][:50]}...")
    else:
        print(f"Erro: {response.json()}")
    print()

def exemplo_escola():
    """Exemplo: Escola enviando notas personalizadas para pais"""
    print("=== Exemplo: Escola ===")
    print("Enviando boletim personalizado para pais dos alunos...\n")
    
    boletins = [
        {
            "to": "5562999999999",
            "message": "Sra. Ana, o boletim de Carlos está pronto: Matemática: 8.5, Português: 9.0, História: 7.5. Parabéns!"
        },
        {
            "to": "5562888888888", 
            "message": "Sr. José, o boletim de Fernanda: Matemática: 6.0, Português: 8.5, História: 9.0. Precisa melhorar em matemática."
        },
        {
            "to": "5562777777777",
            "message": "Sra. Lucia, o boletim de Roberto: Matemática: 9.5, Português: 8.0, História: 8.5. Excelente desempenho!"
        }
    ]
    
    response = requests.post(f"{BASE_URL}/send-bulk-sms", json={
        "recipients": boletins,
        "max_workers": 2
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Boletins enviados: {result['sent']}/{result['total']}")
        for r in result['results']:
            if r['status'] == 'sent':
                print(f"  📚 {r['to']}: Boletim entregue em {r['duration']}s")
    print()

def exemplo_clinica():
    """Exemplo: Clínica enviando lembretes de consulta personalizados"""
    print("=== Exemplo: Clínica ===")
    print("Enviando lembretes personalizados de consultas...\n")
    
    consultas = [
        {
            "to": "5563999999999",
            "message": "Lembrete: Olá Sr. Carlos, sua consulta com Dr. Silva está marcada para AMANHÃ às 14h. Traga seus exames. Clínica SaúdeMax."
        },
        {
            "to": "5563888888888",
            "message": "Lembrete: Oi Sra. Mariana, consulta de pediatria com Dra. Ana na SEXTA às 10h. Traga a carteirinha. Clínica SaúdeMax."
        }
    ]
    
    # Adicionar alguns pacientes com mensagem padrão
    pacientes_padrao = ["5563777777777", "5563666666666"]
    
    response = requests.post(f"{BASE_URL}/send-bulk-sms", json={
        "recipients": consultas + pacientes_padrao,
        "message": "Lembrete: Você tem consulta marcada conosco. Confirme sua presença. Clínica SaúdeMax.",
        "max_workers": 3
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Lembretes enviados: {result['sent']}/{result['total']}")
        personalizados = len([r for r in result['results'] if len(r['message']) > 100])
        padrao = result['total'] - personalizados
        print(f"  📋 {personalizados} mensagens personalizadas")
        print(f"  📄 {padrao} mensagens padrão")
    print()

def exemplo_marketing():
    """Exemplo: Campanha de marketing segmentada"""
    print("=== Exemplo: Marketing Segmentado ===")
    print("Enviando promoções segmentadas por perfil de cliente...\n")
    
    campanhas = [
        # Clientes VIP
        {
            "to": "5564999999999",
            "message": "🌟 VIP: Oferta EXCLUSIVA! 50% OFF em produtos premium só para você. Use: VIP50. Válido até domingo!"
        },
        {
            "to": "5564888888888",
            "message": "🌟 VIP: Pré-venda exclusiva! Novos produtos com 40% OFF. Acesso antecipado: VIP40. Corra!"
        },
        # Clientes regulares
        "5564777777777",
        "5564666666666",
        # Cliente especial
        {
            "to": "5564555555555",
            "message": "🎂 FELIZ ANIVERSÁRIO! Ganhe 30% OFF em sua compra de presente! Use: ANIVER30. Parabéns!"
        }
    ]
    
    response = requests.post(f"{BASE_URL}/send-bulk-sms", json={
        "recipients": campanhas,
        "message": "🛍️ PROMOÇÃO: 20% OFF em toda loja! Use código: PROMO20. Válido por tempo limitado!",
        "max_workers": 4
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Campanhas enviadas: {result['sent']}/{result['total']}")
        vip = len([r for r in result['results'] if 'VIP' in r['message']])
        aniversario = len([r for r in result['results'] if 'ANIVERSÁRIO' in r['message']])
        regular = result['total'] - vip - aniversario
        print(f"  👑 {vip} mensagens VIP")
        print(f"  🎂 {aniversario} mensagem de aniversário")
        print(f"  🛍️ {regular} promoções regulares")
    print()

def teste_validacao_erro():
    """Teste de validação e tratamento de erros"""
    print("=== Teste de Validação de Erros ===")
    
    # Teste 1: Recipients sem mensagem personalizada nem padrão
    print("Testando erro: recipients sem mensagem...")
    response = requests.post(f"{BASE_URL}/send-bulk-sms", json={
        "recipients": [
            {"to": "5565999999999"}  # Sem message e sem message padrão
        ]
    })
    print(f"Status: {response.status_code} - {response.json().get('error', 'OK')}")
    
    # Teste 2: Formato inválido
    print("\nTestando erro: formato inválido...")
    response = requests.post(f"{BASE_URL}/send-bulk-sms", json={
        "recipients": [123456]  # Nem string nem objeto
    })
    print(f"Status: {response.status_code} - {response.json().get('error', 'OK')}")
    
    # Teste 3: Objeto sem campo 'to'
    print("\nTestando erro: objeto sem 'to'...")
    response = requests.post(f"{BASE_URL}/send-bulk-sms", json={
        "recipients": [
            {"message": "Mensagem sem destinatário"}
        ]
    })
    print(f"Status: {response.status_code} - {response.json().get('error', 'OK')}")
    print()

def main():
    print("🚀 Exemplos Práticos da API SMS com Mensagens Personalizadas")
    print("=" * 60)
    
    try:
        # Verificar se a API está online
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Erro: API não está respondendo corretamente")
            return
        print("✅ API conectada com sucesso!\n")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro: Não foi possível conectar à API: {e}")
        return
    
    # Executar exemplos
    exemplo_loja_online()
    exemplo_escola()
    exemplo_clinica()
    exemplo_marketing()
    teste_validacao_erro()
    
    # Estatísticas finais
    stats = requests.get(f"{BASE_URL}/stats").json()
    print("📊 Estatísticas Finais:")
    print(f"  📱 Total de SMS: {stats['total_sms']}")
    print(f"  ✅ Enviados: {stats['sent_sms']}")
    print(f"  ❌ Erros: {stats['error_sms']}")
    print(f"  📈 Taxa de sucesso: {stats['success_rate']}%")

if __name__ == "__main__":
    main()