# SMS API com Multithreading para Termux

API Flask otimizada para envio rápido e eficiente de SMS via Termux no Android, com suporte a multithreading e processamento em lote.

## Características

- ✅ **Multithreading**: Envio simultâneo de múltiplos SMS
- ✅ **Processamento Assíncrono**: Não bloqueia a API durante envios
- ✅ **Envio em Lote**: Suporte para múltiplos destinatários
- ✅ **Monitoramento**: Endpoints de health check e estatísticas
- ✅ **Controle de Status**: Rastreamento de SMS enviados
- ✅ **Otimizado para Termux**: Timeouts e configurações específicas

## Instalação no Termux

```bash
# Atualizar pacotes
pkg update && pkg upgrade -y

# Instalar dependências
pkg install python git termux-api -y

# Instalar Flask
pip install flask requests

# Clonar o repositório (ou copiar os arquivos)
git clone <seu-repositorio>
cd sms-sender

# Dar permissões necessárias
termux-setup-storage
```

## Uso da API

### 1. Iniciar a API

```bash
python smsApi.py
```

A API estará disponível em `http://localhost:5000`

### 2. Enviar SMS Único (Síncrono)

```bash
curl -X POST http://localhost:5000/send-sms \
  -H "Content-Type: application/json" \
  -d '{
    "to": "5511999999999",
    "message": "Olá! Este é um teste de SMS."
  }'
```

**Resposta:**
```json
{
  "status": "sent",
  "to": "5511999999999",
  "message": "Olá! Este é um teste de SMS.",
  "duration": 1.23,
  "timestamp": "2025-09-25T10:30:00"
}
```

### 3. Enviar SMS Único (Assíncrono)

```bash
curl -X POST http://localhost:5000/send-sms \
  -H "Content-Type: application/json" \
  -d '{
    "to": "5511999999999",
    "message": "SMS assíncrono",
    "async": true
  }'
```

**Resposta:**
```json
{
  "status": "queued",
  "sms_id": "abc123-def456",
  "message": "SMS adicionado à fila de processamento",
  "check_status_url": "/sms-status/abc123-def456"
}
```

### 4. Verificar Status do SMS

```bash
curl http://localhost:5000/sms-status/abc123-def456
```

### 5. Enviar SMS em Lote

**Formato 1: Mensagem única para todos (formato antigo)**
```bash
curl -X POST http://localhost:5000/send-bulk-sms \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      "5511999999999",
      "5511888888888",
      "5511777777777"
    ],
    "message": "Mensagem única para todos",
    "max_workers": 3
  }'
```

**Formato 2: Mensagem personalizada para cada destinatário (NOVO)**
```bash
curl -X POST http://localhost:5000/send-bulk-sms \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      {
        "to": "5511999999999",
        "message": "Olá João! Esta é sua mensagem personalizada."
      },
      {
        "to": "5511888888888", 
        "message": "Oi Maria! Sua mensagem especial está aqui."
      },
      {
        "to": "5511777777777",
        "message": "E aí Pedro! Mensagem exclusiva para você."
      }
    ],
    "max_workers": 3
  }'
```

**Formato 3: Formato misto (alguns personalizados, outros padrão)**
```bash
curl -X POST http://localhost:5000/send-bulk-sms \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      {
        "to": "5511999999999",
        "message": "Mensagem personalizada para João"
      },
      {
        "to": "5511888888888"
      },
      "5511777777777"
    ],
    "message": "Mensagem padrão para quem não tem personalizada",
    "max_workers": 3
  }'
```

**Resposta:**
```json
{
  "batch_id": "batch-abc123",
  "total": 3,
  "sent": 2,
  "errors": 1,
  "results": [
    {
      "status": "sent",
      "to": "5511999999999",
      "duration": 1.1,
      "timestamp": "2025-09-25T10:30:00"
    }
  ]
}
```

## Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/send-sms` | Envia SMS único |
| POST | `/send-bulk-sms` | Envia SMS em lote |
| GET | `/sms-status/<id>` | Consulta status do SMS |
| GET | `/health` | Health check da API |
| GET | `/stats` | Estatísticas de uso |

## Teste da API

Execute o script de teste:

```bash
python test_api.py
```

## Parâmetros de Configuração

### SMS Único
- `to` (string): Número do destinatário
- `message` (string): Mensagem a ser enviada
- `async` (boolean, opcional): Envio assíncrono (padrão: false)

### SMS em Lote
- `recipients` (array): Lista de destinatários. Pode ser:
  - **Formato simples**: Array de strings com números de telefone
  - **Formato personalizado**: Array de objetos com `to` e `message`
  - **Formato misto**: Combinação dos dois formatos
- `message` (string, opcional): Mensagem padrão (obrigatória no formato simples)
- `max_workers` (int, opcional): Máximo de threads simultâneas (padrão: 5, máximo: 10)

**Exemplos de recipients:**
```json
// Formato simples (requer message padrão)
"recipients": ["5511999999999", "5511888888888"]

// Formato personalizado
"recipients": [
  {"to": "5511999999999", "message": "Oi João!"},
  {"to": "5511888888888", "message": "Olá Maria!"}
]

// Formato misto
"recipients": [
  {"to": "5511999999999", "message": "Mensagem personalizada"},
  {"to": "5511888888888"},  // usará message padrão
  "5511777777777"           // usará message padrão
]
```

## Otimizações Implementadas

1. **ThreadPoolExecutor**: Pool de threads reutilizáveis
2. **Timeouts**: Evita travamentos em envios lentos
3. **Controle de Concorrência**: Limite de threads simultâneas
4. **Logging**: Monitoramento de performance
5. **Status Tracking**: Acompanhamento de envios assíncronos
6. **Error Handling**: Tratamento robusto de erros

## Monitoramento

### Health Check
```bash
curl http://localhost:5000/health
```

### Estatísticas
```bash
curl http://localhost:5000/stats
```

## Dicas de Performance

1. **Para poucos SMS**: Use o modo síncrono
2. **Para muitos SMS**: Use envio em lote
3. **Para alta concorrência**: Use modo assíncrono
4. **Ajuste max_workers**: Baseado na capacidade do dispositivo
5. **Monitore threads ativas**: Use o endpoint `/health`

## Troubleshooting

- Verifique se o Termux API está instalado: `pkg list-installed | grep termux-api`
- Permissões SMS: Certifique-se de que o Termux tem permissão para enviar SMS
- Recursos do sistema: Monitor threads ativas para evitar sobrecarga

## Limitações

- Máximo de 10 threads simultâneas (configurável)
- Timeout de 30 segundos por SMS
- Depende das permissões do Android para SMS