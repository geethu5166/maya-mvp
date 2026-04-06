"""
MAYA Auto-Block Module
Autonomous IP blocking based on attack thresholds
"""
import subprocess
import json
import os
from datetime import datetime
from collections import defaultdict

# Configuration
BLOCK_THRESHOLD = 5  # Block after 5 attacks
BLOCKED_IPS_FILE = "logs/blocked_ips.txt"
AUDIT_LOG_FILE = "logs/audit.log"
ATTACKS_LOG_FILE = "logs/attacks.log"

def load_blocked_ips():
    """Load set of already blocked IPs"""
    if not os.path.exists(BLOCKED_IPS_FILE):
        return set()
    try:
        with open(BLOCKED_IPS_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except:
        return set()

def save_blocked_ip(ip, reason):
    """Save blocked IP to file and audit log"""
    with open(BLOCKED_IPS_FILE, 'a') as f:
        f.write(f"{ip}\n")
    
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "IP_BLOCKED",
        "ip": ip,
        "reason": reason,
        "automated": True
    }
    
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    with open(AUDIT_LOG_FILE, 'a') as f:
        f.write(json.dumps(audit_entry) + "\n")
    
    print(f"[MAYA AUTO-BLOCK] {ip} blocked: {reason}")

def auto_block_ip(ip, reason):
    """Block IP using UFW firewall"""
    blocked_ips = load_blocked_ips()
    
    if ip in blocked_ips:
        return False  # Already blocked
    
    try:
        result = subprocess.run(
            ['sudo', 'ufw', 'deny', 'from', ip],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            save_blocked_ip(ip, reason)
            return True
        else:
            print(f"[MAYA ERROR] Failed to block {ip}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[MAYA ERROR] Exception blocking {ip}: {e}")
        return False

def check_and_block_attacker(attacker_ip):
    """Check if IP should be auto-blocked based on attack count"""
    if not os.path.exists(ATTACKS_LOG_FILE):
        return
    
    # Count recent attacks from this IP
    attack_count = 0
    try:
        with open(ATTACKS_LOG_FILE, 'r') as f:
            for line in f:
                try:
                    attack = json.loads(line.strip())
                    if attack.get("attacker_ip") == attacker_ip:
                        attack_count += 1
                except:
                    continue
    except:
        return
    
    # Block if threshold exceeded
    if attack_count >= BLOCK_THRESHOLD:
        reason = f"Exceeded threshold: {attack_count} attacks detected"
        auto_block_ip(attacker_ip, reason)

if __name__ == "__main__":
    print("MAYA Auto-Block Module")
    print("Testing configuration...")
    print(f"Threshold: {BLOCK_THRESHOLD} attacks")
    print(f"Blocked IPs file: {BLOCKED_IPS_FILE}")
    print(f"Audit log: {AUDIT_LOG_FILE}")
