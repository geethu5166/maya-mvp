import threading
import os
import sys
import time

def banner():
    print("""
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   ███╗   ███╗ █████╗ ██╗   ██╗ █████╗               ║
║   ████╗ ████║██╔══██╗╚██╗ ██╔╝██╔══██╗              ║
║   ██╔████╔██║███████║ ╚████╔╝ ███████║              ║
║   ██║╚██╔╝██║██╔══██║  ╚██╔╝  ██╔══██║              ║
║   ██║ ╚═╝ ██║██║  ██║   ██║   ██║  ██║              ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝              ║
║                                                       ║
║   Autonomous Deception & Security Platform           ║
║   Version 1.0 — Built in India                       ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
    """)

def start_ssh_honeypot():
    print("[MAYA] Starting SSH Honeypot on port 2222...")
    os.system("python3 honeypot/ssh_honeypot.py")

def start_web_honeypot():
    time.sleep(1)
    print("[MAYA] Starting Web Honeypot on port 5001...")
    os.system("python3 honeypot/web_honeypot.py")

def start_dashboard():
    time.sleep(2)
    print("[MAYA] Starting Dashboard on port 5000...")
    os.system("python3 dashboard/app.py")

def start_response_engine():
    time.sleep(3)
    print("[MAYA] Starting Autonomous Response Engine...")
    from honeypot.response_engine import watch_and_respond
    watch_and_respond()

def main():
    banner()

    print("[MAYA] Initializing all systems...")
    print("[MAYA] AI Model    : 98.68% accuracy")
    print("[MAYA] Datasets    : CICIDS2018 + NSL-KDD + India")
    print("[MAYA] Honeypots   : SSH + Web")
    print("[MAYA] Response    : Autonomous")
    print("-" * 55)

    threads = [
        threading.Thread(target=start_ssh_honeypot),
        threading.Thread(target=start_web_honeypot),
        threading.Thread(target=start_dashboard),
        threading.Thread(target=start_response_engine)
    ]

    for t in threads:
        t.daemon = True
        t.start()

    time.sleep(4)
    print("\n" + "=" * 55)
    print("[MAYA] ALL SYSTEMS OPERATIONAL")
    print("=" * 55)
    print("[MAYA] SSH Honeypot         → port 2222")
    print("[MAYA] Web Honeypot         → http://127.0.0.1:5001")
    print("[MAYA] Dashboard            → http://127.0.0.1:5000")
    print("[MAYA] Response Engine      → ACTIVE")
    print("[MAYA] AI Detection         → 98.68% accuracy")
    print("=" * 55)
    print("[MAYA] Open Firefox → http://127.0.0.1:5000")
    print("[MAYA] Press Ctrl+C to stop all systems")
    print("=" * 55 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAYA] Shutting down all systems...")
        print("[MAYA] Goodbye.")
        sys.exit(0)

if __name__ == "__main__":
    main()
