bind            = "127.0.0.1:5000"
workers         = 1        # 1 seul worker pour la webcam
worker_class    = "sync"
timeout         = 120
keepalive       = 5
accesslog       = "instance/logs/access.log"
errorlog        = "instance/logs/error.log"
loglevel        = "info"
