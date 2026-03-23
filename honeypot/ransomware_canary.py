import os
import time
import json
import datetime
import threading
import hashlib
import stat

LOG_FILE = '/home/kali/maya-mvp/logs/attacks.log'
CANARY_DIR = '/home/kali/maya-mvp/honeypot/canary_files'
CANARY_DB = '/home/kali/maya-mvp/logs/canary_state.json'

def log_attack(data):
    print(f"[CANARY] {data['timestamp']} | {data['type']} | {data['details']}")
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

def get_file_hash(filepath):
    """Get MD5 hash of file to detect modification."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def get_file_state(filepath):
    """Get complete state of a file."""
    try:
        s = os.stat(filepath)
        return {
            'hash': get_file_hash(filepath),
            'size': s.st_size,
            'mtime': s.st_mtime,
            'exists': True
        }
    except:
        return {'exists': False}

def create_canary_files():
    """
    Create canary files in multiple locations.
    Ransomware always encrypts alphabetically —
    canary files named AAA_ are always hit first.
    """
    os.makedirs(CANARY_DIR, exist_ok=True)
    canary_files = []

    # Named AAA_ so ransomware hits them first
    file_templates = [
        {
            'name': 'AAA_DO_NOT_DELETE_SECURITY.txt',
            'content': 'This file is part of the security monitoring system.\nDo not delete or modify.\nVaultrap MAYA Security Platform\n',
            'description': 'Text canary — first target for ransomware'
        },
        {
            'name': 'AAA_Financial_Report_Q4.docx.txt',
            'content': 'Q4 Financial Report - CONFIDENTIAL\nRevenue: $4,250,000\nExpenses: $3,100,000\nNet Profit: $1,150,000\n',
            'description': 'Fake financial document canary'
        },
        {
            'name': 'AAA_Employee_Database.csv.txt',
            'content': 'id,name,email,salary\n1,John Smith,j.smith@company.com,85000\n2,Sarah Jones,s.jones@company.com,92000\n',
            'description': 'Fake employee data canary'
        },
        {
            'name': 'AAA_backup_credentials.txt',
            'content': 'Backup System Credentials\nHost: backup-01.internal\nUser: backup_admin\nPass: Backup@2024!\n',
            'description': 'Fake credentials canary'
        },
        {
            'name': 'AAA_customer_data_export.txt',
            'content': 'Customer Export - 2024\nID,Name,Email,Phone\n1001,Alice Brown,alice@email.com,+1-555-0101\n',
            'description': 'Fake customer data canary'
        },
    ]

    state = {}
    for template in file_templates:
        filepath = os.path.join(CANARY_DIR, template['name'])
        with open(filepath, 'w') as f:
            f.write(template['content'])

        file_state = get_file_state(filepath)
        state[filepath] = {
            'original_state': file_state,
            'description': template['description'],
            'created_at': datetime.datetime.now().isoformat(),
            'alert_count': 0
        }
        canary_files.append(filepath)
        print(f"[CANARY] Created: {template['name']}")

    # Save baseline state
    with open(CANARY_DB, 'w') as f:
        json.dump(state, f, indent=2)

    print(f"\n[CANARY] {len(canary_files)} canary files deployed")
    print(f"[CANARY] Location: {CANARY_DIR}")
    print(f"[CANARY] Baseline state saved")
    return canary_files, state

def check_canary_files(state):
    """
    Check all canary files for modification.
    Called every 5 seconds — catches ransomware fast.
    """
    alerts = []

    for filepath, info in state.items():
        current_state = get_file_state(filepath)
        original_state = info['original_state']

        # File deleted
        if not current_state['exists'] and original_state['exists']:
            alert = {
                'type': 'CANARY_FILE_DELETED',
                'severity': 'CRITICAL',
                'filepath': filepath,
                'description': 'Canary file DELETED — possible ransomware wiping files'
            }
            alerts.append(alert)

        # File modified
        elif current_state['exists'] and original_state['exists']:
            if current_state['hash'] != original_state['hash']:
                size_change = current_state['size'] - original_state['size']
                alert = {
                    'type': 'CANARY_FILE_MODIFIED',
                    'severity': 'CRITICAL',
                    'filepath': filepath,
                    'size_change': size_change,
                    'description': f'Canary file MODIFIED — size change: {size_change} bytes — RANSOMWARE DETECTED'
                }
                alerts.append(alert)

            # File encrypted signature
            elif current_state['size'] != original_state['size']:
                alert = {
                    'type': 'CANARY_FILE_ENCRYPTED',
                    'severity': 'CRITICAL',
                    'filepath': filepath,
                    'description': 'Canary file size changed — possible encryption in progress'
                }
                alerts.append(alert)

    return alerts

def simulate_ransomware_detection():
    """
    Simulate ransomware modifying a canary file.
    For testing purposes only.
    """
    print("\n[CANARY] Simulating ransomware attack...")
    time.sleep(2)

    # Modify a canary file to simulate encryption
    test_file = os.path.join(CANARY_DIR, 'AAA_DO_NOT_DELETE_SECURITY.txt')
    if os.path.exists(test_file):
        with open(test_file, 'w') as f:
            # Simulate encrypted content
            f.write('ENCRYPTED_CONTENT_' + 'X' * 100)
        print(f"[CANARY] Simulated ransomware modified: {test_file}")

def monitor_canary_files():
    """
    Main monitoring loop.
    Checks every 5 seconds — catches ransomware early.
    """
    print("[CANARY] Starting ransomware detection monitor...")
    print("[CANARY] Checking every 5 seconds")
    print("[CANARY] Will alert if any canary file is modified or deleted")

    # Create canary files and get baseline
    canary_files, state = create_canary_files()

    files_encrypted_count = 0
    ransomware_detected = False

    while True:
        try:
            # Reload state from disk
            if os.path.exists(CANARY_DB):
                with open(CANARY_DB, 'r') as f:
                    state = json.load(f)

            alerts = check_canary_files(state)

            for alert in alerts:
                files_encrypted_count += 1

                log_attack({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "type": alert['type'],
                    "severity": alert['severity'],
                    "honeypot": "RANSOMWARE_CANARY",
                    "attacker_ip": "LOCAL_PROCESS",
                    "details": alert['description'],
                    "filepath": alert['filepath'],
                    "files_encrypted": files_encrypted_count,
                    "message": f"RANSOMWARE DETECTED — {files_encrypted_count} canary files affected — ISOLATE IMMEDIATELY"
                })

                if not ransomware_detected:
                    ransomware_detected = True
                    print(f"\n[CANARY] ⚠ RANSOMWARE DETECTED!")
                    print(f"[CANARY] File affected: {alert['filepath']}")
                    print(f"[CANARY] Type: {alert['type']}")
                    print(f"[CANARY] MAYA has logged alert and notified dashboard")
                    print(f"[CANARY] Action: Isolate affected systems immediately")

                    # Restore canary file
                    try:
                        filepath = alert['filepath']
                        filename = os.path.basename(filepath)
                        original_content = f"This file is part of the security monitoring system.\nDo not delete or modify.\nVaultrap MAYA Security Platform\n"
                        with open(filepath, 'w') as f:
                            f.write(original_content)

                        # Update baseline
                        new_state = get_file_state(filepath)
                        state[filepath]['original_state'] = new_state
                        state[filepath]['alert_count'] += 1
                        with open(CANARY_DB, 'w') as f:
                            json.dump(state, f, indent=2)

                        ransomware_detected = False
                        print(f"[CANARY] Canary file restored for continued monitoring")
                    except Exception as e:
                        pass

        except Exception as e:
            pass

        time.sleep(5)

def run_canary_system():
    """Start complete ransomware canary system."""
    print("""
╔═══════════════════════════════════════════════════════╗
║         MAYA RANSOMWARE CANARY SYSTEM                 ║
║         Detects ransomware after file 1               ║
║         Not file 10,000                               ║
╚═══════════════════════════════════════════════════════╝
    """)

    # Start monitor in background thread
    monitor_thread = threading.Thread(target=monitor_canary_files)
    monitor_thread.daemon = True
    monitor_thread.start()

    print("[CANARY] Monitor running in background")
    print("[CANARY] Type 'test' to simulate ransomware detection")
    print("[CANARY] Type 'quit' to exit")
    print("")

    while True:
        try:
            cmd = input("canary> ").strip().lower()
            if cmd == 'test':
                simulate_ransomware_detection()
            elif cmd == 'quit':
                break
            elif cmd == 'status':
                if os.path.exists(CANARY_DB):
                    with open(CANARY_DB, 'r') as f:
                        state = json.load(f)
                    print(f"[CANARY] {len(state)} canary files active")
                    for fp in state:
                        print(f"  → {os.path.basename(fp)}")
        except KeyboardInterrupt:
            break

    print("\n[CANARY] Stopped")

if __name__ == "__main__":
    run_canary_system()
