"""Gunicorn configuration for the Employee Management API.

Gunicorn manages a small pool of Uvicorn workers, so the async FastAPI app is
served correctly while Gunicorn handles process supervision. Bound to localhost
only -- nginx sits in front and is the sole public entry point.
"""

# Listen on loopback; nginx proxies public :80 traffic here.
bind = "127.0.0.1:8000"

# Uvicorn workers so ASGI/async endpoints work.
worker_class = "uvicorn.workers.UvicornWorker"

# A t2/t3.micro has 1 vCPU and 1 GB RAM. Two workers is a safe, responsive
# choice that stays well within memory; raise this on a larger instance.
workers = 2

timeout = 60
graceful_timeout = 30
keepalive = 5

# Logs to stdout/stderr so journald/CloudWatch can capture them.
accesslog = "-"
errorlog = "-"
loglevel = "info"
