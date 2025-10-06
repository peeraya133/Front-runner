# logger.py
from datetime import datetime

LOG_FILE = "log.txt"

def log_event(actor, action, status="OK", detail=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {actor} - {action}: {detail} -> {status}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
