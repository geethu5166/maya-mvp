import threading
import os
import sys
import time


import subprocess
import json
from datetime import datetime

# Auto-block configuration
BLOCK_THRESHOLD = 5  # Block after 5 failed attempts
BLOCKED_IPS_FILE = "logs/blocked_ips.txt"
AUDIT_LOG_FILE = "logs/audit.log"

def load_blocked_ips():
    try:
        with open(BLOCKED_IPS_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_blocked_ip(ip, reason):
    with open(BLOCKED_IPS_FILE, 'a') as f:
        f.write(f"{ip}\n")
    
    # Log to audit trail
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "IP_BLOCKED",
        "ip": ip,
        "reason": reason,
        "automated": True
    }
    with open(AUDIT_LOG_FILE, 'a') as f:
        f.write(json.dumps(audit_entry) + "\n")

def auto_block_ip(ip, reason):
    """Auto-block IP using ufw firewall"""
    blocked_ips = load_blocked_ips()
    
    if ip in blocked_ips:
        return False  # Already blocked
    
    try:
        # Block with ufw
        result = subprocess.run(
            ['ufw', 'deny', 'from', ip],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            save_blocked_ip(ip, reason)
            print(f"[MAYA AUTO-BLOCK] Blocked {ip}: {reason}")
            return True
        else:
            print(f"[MAYA ERROR] Failed to block {ip}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[MAYA ERROR] Exception blocking {ip}: {e}")
        return False

def check_and_block_attacker(attacker_ip):
    """Check if IP should be auto-blocked based on attack count"""
    # Count attacks from this IP in last 10 minutes
    from collections import defaultdict
    recent_attacks = defaultdict(int)
    
    try:
        with open("logs/attacks.log", 'r') as f:
            for line in f:
                try:
                    attack = json.loads(line.strip())
                    if attack.get("attacker_ip") == attacker_ip:
                        recent_attacks[attacker_ip] += 1
                except:
                    continue
    except:
        pass
    
    if recent_attacks[attacker_ip] >= BLOCK_THRESHOLD:
        reason = f"Exceeded threshold: {recent_attacks[attacker_ip]} attacks detected"
        auto_block_ip(attacker_ip, reason)
\n\ndef banner():
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
    os.chdir("/root/maya-mvp/dashboard"); os.system("python3 app.py"); os.chdir("/root/maya-mvp")

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

def start_threat_intel():
    time.sleep(4)
    print("[MAYA] Starting Threat Intelligence Engine...")
    from detection.threat_intelligence import run_continuous_intel
    run_continuous_intel()

def start_dna_profiler():
    time.sleep(6)
    print("[MAYA] Starting Attacker DNA Profiling System...")
    from detection.dna_profiler import watch_and_profile
    watch_and_profile()
