import os
import sys
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def banner():
    print(r"""
+-------------------------------------------------------+
|   MAYA - Autonomous Deception & Security Platform     |
|   Version 4.0 - Vaultrap Security Technologies        |
|   Pipeline: Ingest > Enrich > Correlate > Respond     |
+-------------------------------------------------------+
    """)


def run_script(relative_path: str):
    os.system(f'"{sys.executable}" "{BASE_DIR / relative_path}"')


def start_ssh_honeypot():
    print("[MAYA] SSH Honeypot -> port 2222")
    run_script("honeypot/ssh_honeypot.py")


def start_web_honeypot():
    time.sleep(1)
    print("[MAYA] Web Honeypot -> port 5001")
    run_script("honeypot/web_honeypot.py")


def start_db_honeypot():
    time.sleep(2)
    print("[MAYA] Database Honeypots -> MySQL 3306 | Redis 6379")
    run_script("honeypot/db_honeypot.py")


def start_dashboard():
    time.sleep(2)
    print("[MAYA] Dashboard -> port 5000")
    dashboard_dir = BASE_DIR / "dashboard"
    current_dir = Path.cwd()
    os.chdir(dashboard_dir)
    os.system(f'"{sys.executable}" "app.py"')
    os.chdir(current_dir)


def start_response_engine():
    time.sleep(3)
    print("[MAYA] Autonomous Response Engine -> ACTIVE")
    from honeypot.response_engine import watch_and_respond
    watch_and_respond()


def start_threat_intel():
    time.sleep(4)
    print("[MAYA] Threat Intelligence Engine -> ACTIVE")
    from detection.threat_intelligence import run_continuous_intel
    run_continuous_intel()


def start_dna_profiler():
    time.sleep(5)
    print("[MAYA] Attacker DNA Profiler -> ACTIVE")
    from detection.dna_profiler import watch_and_profile
    watch_and_profile()


def main():
    banner()
    print("[MAYA] Initializing unified product pipeline...")
    print("[MAYA] Core modules : event_bus + agentic_ai + graph_analytics + continuous_learning")
    print("[MAYA] Datasets     : CICIDS2018 + NSL-KDD + India")
    print("[MAYA] Login        : vaultrap / maya@2026")
    print("-" * 55)

    threads = [
        threading.Thread(target=start_ssh_honeypot, daemon=True),
        threading.Thread(target=start_web_honeypot, daemon=True),
        threading.Thread(target=start_db_honeypot, daemon=True),
        threading.Thread(target=start_dashboard, daemon=True),
        threading.Thread(target=start_response_engine, daemon=True),
        threading.Thread(target=start_threat_intel, daemon=True),
        threading.Thread(target=start_dna_profiler, daemon=True),
    ]

    for thread in threads:
        thread.start()

    time.sleep(8)
    print("\n" + "=" * 55)
    print("[MAYA] ALL SYSTEMS OPERATIONAL - v4.0")
    print("=" * 55)
    print("[MAYA] SSH Honeypot         -> port 2222")
    print("[MAYA] Web Honeypot         -> http://127.0.0.1:5001")
    print("[MAYA] DB Honeypots         -> MySQL 3306 | Redis 6379")
    print("[MAYA] Dashboard            -> http://127.0.0.1:5000")
    print("[MAYA] Product Pipeline     -> ACTIVE")
    print("[MAYA] Graph Correlation    -> ACTIVE")
    print("[MAYA] Continuous Learning  -> ACTIVE")
    print("=" * 55 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAYA] Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
