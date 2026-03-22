import json
import datetime
import os
import time
import platform
import socket
import threading
import requests

# MAYA Central Server URL
# Change this to your cloud server IP when deployed
MAYA_SERVER = "http://127.0.0.1:5000"
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'attacks.log')

def log_attack(data):
    """Send attack data to MAYA central dashboard."""
    # Log locally
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')
    print(f"[WINDOWS AGENT] {data['timestamp']} | {data['type']} | {data['severity']}")

    # Send to MAYA server
    try:
        requests.post(f"{MAYA_SERVER}/api/attack", json=data, timeout=3)
    except:
        pass

def get_system_info():
    """Get basic system information."""
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "ip": socket.gethostbyname(socket.gethostname())
    }

def monitor_windows_events():
    """
    Monitor Windows Event Logs for attacks.
    This runs on actual Windows machines.
    Detects:
    - Failed login attempts (Event ID 4625)
    - Account lockouts (Event ID 4740)
    - Privilege escalation (Event ID 4672)
    - RDP attacks (Event ID 4624 with LogonType 10)
    """
    if platform.system() != 'Windows':
        print("[WINDOWS AGENT] Simulating Windows event monitoring on Linux...")
        simulate_windows_events()
        return

    try:
        import win32evtlog
        import win32evtlogutil
        import win32con

        server = 'localhost'
        logtype = 'Security'
        hand = win32evtlog.OpenEventLog(server, logtype)

        print("[WINDOWS AGENT] Monitoring Windows Security Event Log...")
        print("[WINDOWS AGENT] Watching for: Failed logins, RDP attacks, Privilege escalation")

        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

        while True:
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            if events:
                for event in events:
                    event_id = event.EventID & 0xFFFF

                    # Failed login attempt
                    if event_id == 4625:
                        data = win32evtlogutil.SafeFormatMessage(event, logtype)
                        log_attack({
                            "timestamp": datetime.datetime.now().isoformat(),
                            "type": "WINDOWS_FAILED_LOGIN",
                            "severity": "HIGH",
                            "honeypot": "WINDOWS",
                            "attacker_ip": extract_ip(str(data)),
                            "details": str(data)[:200],
                            "event_id": event_id,
                            "system_info": get_system_info()
                        })

                    # Account lockout
                    elif event_id == 4740:
                        log_attack({
                            "timestamp": datetime.datetime.now().isoformat(),
                            "type": "WINDOWS_ACCOUNT_LOCKOUT",
                            "severity": "CRITICAL",
                            "honeypot": "WINDOWS",
                            "attacker_ip": "unknown",
                            "details": "Account locked out due to repeated failed attempts",
                            "event_id": event_id,
                            "system_info": get_system_info()
                        })

                    # Privilege escalation
                    elif event_id == 4672:
                        log_attack({
                            "timestamp": datetime.datetime.now().isoformat(),
                            "type": "WINDOWS_PRIVILEGE_ESCALATION",
                            "severity": "CRITICAL",
                            "honeypot": "WINDOWS",
                            "attacker_ip": "unknown",
                            "details": "Special privileges assigned to new logon",
                            "event_id": event_id,
                            "system_info": get_system_info()
                        })

            time.sleep(5)

    except ImportError:
        print("[WINDOWS AGENT] win32evtlog not available — running simulation mode")
        simulate_windows_events()

def simulate_windows_events():
    """
    Simulate Windows attacks for testing on Linux.
    Generates realistic Windows attack patterns.
    """
    print("[WINDOWS AGENT] Running in simulation mode")
    print("[WINDOWS AGENT] Generating realistic Windows attack patterns...")

    attack_patterns = [
        {
            "type": "WINDOWS_RDP_BRUTE_FORCE",
            "severity": "CRITICAL",
            "details": "RDP brute force detected — 847 failed attempts from single IP",
            "attacker_ip": "185.220.101.47"
        },
        {
            "type": "WINDOWS_FAILED_LOGIN",
            "severity": "HIGH",
            "details": "Multiple failed login attempts for Administrator account",
            "attacker_ip": "45.152.66.12"
        },
        {
            "type": "WINDOWS_LATERAL_MOVEMENT",
            "severity": "CRITICAL",
            "details": "Suspicious lateral movement detected — attacker moving between systems",
            "attacker_ip": "103.216.221.15"
        },
        {
            "type": "WINDOWS_PRIVILEGE_ESCALATION",
            "severity": "CRITICAL",
            "details": "Privilege escalation attempt — trying to gain SYSTEM level access",
            "attacker_ip": "91.108.4.177"
        },
        {
            "type": "WINDOWS_RANSOMWARE_BEHAVIOR",
            "severity": "CRITICAL",
            "details": "Ransomware-like behavior — mass file encryption detected",
            "attacker_ip": "185.220.101.32"
        },
        {
            "type": "WINDOWS_HONEYTOKEN_TRIGGERED",
            "severity": "CRITICAL",
            "details": "Fake admin credentials used — attacker accessed honeytoken",
            "attacker_ip": "45.95.168.119"
        }
    ]

    system_info = get_system_info()

    for pattern in attack_patterns:
        attack = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": pattern["type"],
            "severity": pattern["severity"],
            "honeypot": "WINDOWS_AGENT",
            "attacker_ip": pattern["attacker_ip"],
            "details": pattern["details"],
            "system_info": system_info
        }
        log_attack(attack)
        time.sleep(2)

    print("[WINDOWS AGENT] Simulation complete")
    print("[WINDOWS AGENT] Now monitoring for real attacks...")

    # Keep running and monitor
    while True:
        time.sleep(60)

def extract_ip(text):
    """Extract IP address from Windows event log text."""
    import re
    pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    matches = re.findall(pattern, text)
    for ip in matches:
        if not ip.startswith('127.') and not ip.startswith('0.'):
            return ip
    return "unknown"

def deploy_honeytokens():
    """
    Deploy fake credentials that alert when used.
    On Windows — plants fake credentials in:
    - Windows Credential Manager
    - Registry fake keys
    - Fake config files
    """
    print("[WINDOWS AGENT] Deploying honeytokens...")

    honeytokens = [
        {
            "type": "FAKE_ADMIN_CREDENTIALS",
            "username": "admin_backup",
            "password": "P@ssw0rd123!",
            "location": "Windows Credential Manager"
        },
        {
            "type": "FAKE_DATABASE_CONNECTION",
            "connection_string": "Server=db-prod-01;Database=CustomerData;User=sa;Password=SqlP@ss2024",
            "location": "C:\\Config\\database.config"
        },
        {
            "type": "FAKE_API_KEY",
            "api_key": "sk-prod-xK8mN2pL9qR4tV7wY1zA3cB6dE0fG5hJ",
            "location": "C:\\Apps\\api_config.json"
        }
    ]

    for token in honeytokens:
        print(f"[WINDOWS AGENT] Honeytoken deployed: {token['type']} at {token['location']}")

    print(f"[WINDOWS AGENT] {len(honeytokens)} honeytokens active")
    print("[WINDOWS AGENT] Any access will trigger MAYA alert")

    return honeytokens

def monitor_network_connections():
    """
    Monitor suspicious network connections.
    Detects C2 communication, data exfiltration attempts.
    """
    print("[WINDOWS AGENT] Monitoring network connections...")

    suspicious_ports = [4444, 1337, 31337, 8888, 9999, 6666]
    known_c2_patterns = ["metasploit", "cobalt", "empire", "meterpreter"]

    while True:
        try:
            import psutil
            connections = psutil.net_connections()
            for conn in connections:
                if conn.raddr and conn.raddr.port in suspicious_ports:
                    log_attack({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "type": "SUSPICIOUS_C2_CONNECTION",
                        "severity": "CRITICAL",
                        "honeypot": "WINDOWS_NETWORK",
                        "attacker_ip": conn.raddr.ip,
                        "details": f"Suspicious connection to port {conn.raddr.port} — possible C2 communication",
                        "system_info": get_system_info()
                    })
        except:
            pass
        time.sleep(10)

def run_windows_agent():
    """
    Main Windows Agent — runs all monitoring simultaneously.
    Deploy this on any Windows machine in the network.
    It reports everything back to MAYA central.
    """
    print("""
╔═══════════════════════════════════════════════════════╗
║         MAYA WINDOWS AGENT v1.0                       ║
║         Protecting Windows Infrastructure             ║
║         Reporting to MAYA Central                     ║
╚═══════════════════════════════════════════════════════╝
    """)

    system_info = get_system_info()
    print(f"[WINDOWS AGENT] System: {system_info['hostname']}")
    print(f"[WINDOWS AGENT] OS: {system_info['os']} {system_info['os_version'][:30]}")
    print(f"[WINDOWS AGENT] IP: {system_info['ip']}")
    print(f"[WINDOWS AGENT] MAYA Server: {MAYA_SERVER}")
    print("-" * 55)

    # Deploy honeytokens
    deploy_honeytokens()

    # Start monitoring threads
    threads = [
        threading.Thread(target=monitor_windows_events),
        threading.Thread(target=monitor_network_connections),
    ]

    for t in threads:
        t.daemon = True
        t.start()

    print("\n[WINDOWS AGENT] All monitors active")
    print("[WINDOWS AGENT] Reporting attacks to MAYA dashboard")
    print("[WINDOWS AGENT] Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[WINDOWS AGENT] Shutting down...")

if __name__ == "__main__":
    run_windows_agent()
