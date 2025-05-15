# Gunicorn configuration file per gestire file di grandi dimensioni

# Timeout aumentato per gestire le richieste di caricamento file grandi
timeout = 3600  # 1 ora
keepalive = 65
worker_class = 'sync'
workers = 2
threads = 4

# Configurazione buffer e limiti
limit_request_line = 0
limit_request_fields = 200
limit_request_field_size = 0

# Opzioni di logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Configurazione del server
bind = '0.0.0.0:5000'