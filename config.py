"""
Configurações da SMS API
"""

# Configurações de Threading
MAX_WORKERS = 10  # Máximo de threads simultâneas
DEFAULT_BULK_WORKERS = 5  # Workers padrão para envio em lote
SMS_TIMEOUT = 30  # Timeout em segundos para envio de SMS

# Configurações da API
API_HOST = "0.0.0.0"
API_PORT = 5000
DEBUG_MODE = False
THREADED = True

# Configurações de Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configurações de Performance
ENABLE_ASYNC_MODE = True  # Habilita modo assíncrono
MAX_SMS_HISTORY = 1000  # Máximo de SMS no histórico de status
CLEANUP_INTERVAL = 3600  # Intervalo de limpeza em segundos

# Configurações do Termux
TERMUX_SMS_COMMAND = "termux-sms-send"
TERMUX_SMS_ARGS = ["-n"]  # Argumentos padrão

# Limites de Rate Limiting (futuro)
RATE_LIMIT_ENABLED = False
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # segundos