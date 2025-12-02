# backend/gunicorn_config.py
import os
from multiprocessing import cpu_count

# Fix working directory
workers = int(os.environ.get("GUNICORN_WORKERS", "1"))
worker_class = "sync"
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Critical: change directory to where app.py lives
chdir = os.path.dirname(__file__)
