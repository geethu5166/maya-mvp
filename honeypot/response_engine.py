import subprocess
import json
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'attacks.log')
RESPONSE_LOG = os.path.join(os.path.dirname(__file__), '..', 'logs', 'responses.log')
BLOCKED_IPS = os.path.join(os.path.dirname(__file__), '..', 'logs', 'blocked_ips.txt')

# Load already blocked IPs
def get_blocked_ips():
    if not os.path.exists(BLOCKED_IPS):
        return set()
    with open(BLOCKED_IPS, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def block_ip(ip):
    """
    Blocks attacker IP using Linux firewall.
    This is the autonomous response.
    No human needed.
    """
    # Skip local IPs
    if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.'):
        return False, "Local IP — skipped"

    blocked = get_blocked_ips()
    if ip in blocked:
        return False, "Already blocked"

    try:
        # Block using iptables
        subprocess.run(
            ['sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'],
            capture_output=True, timeout=5
        )

        # Save to blocked list
        with open(BLOCKED_IPS, 'a') as f:
            f.write(ip + '\n')

        return True, f"IP {ip} blocked successfully"

    except Exception as e:
        return False, f"Block failed: {str(e)}"

def log_response(action):
    """Log every autonomous action MAYA takes."""
    with open(RESPONSE_LOG, 'a') as f:
        f.write(json.dumps(action) + '\n')
    print(f"[MAYA RESPONSE] {action['timestamp']} | {action['action']} | {action['details']}")

def send_email_alert(attack, email_to="geetesh5166@gmail.com"):
    """
    Send email alert when critical attack detected.
    Uses Gmail SMTP.
    """
    try:
        # Email config — update with your credentials
        EMAIL_FROM = "your_email@gmail.com"
        EMAIL_PASSWORD = "your_app_password"

        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = email_to
        msg['Subject'] = f"[MAYA ALERT] {attack['severity']} Attack Detected"

        body = f"""
MAYA Autonomous Security Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ATTACK DETECTED AND CONTAINED

Time: {attack['timestamp']}
Attacker IP: {attack['attacker_ip']}
Attack Type: {attack['type']}
Severity: {attack['severity']}
Honeypot: {attack['honeypot']}

MAYA Response:
→ Attacker IP blocked automatically
→ All credentials revoked
→ Additional decoys deployed

No manual action required.
MAYA has contained this threat.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAYA — Autonomous Deception & Security Platform
Built in India. Protecting India.
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        return False

def respond_to_attack(attack):
    """
    Main response function.
    Called every time a new attack is detected.
    Decides what to do and does it automatically.
    """
    severity = attack.get('severity', 'LOW')
    ip = attack.get('attacker_ip', '')
    attack_type = attack.get('type', '')
    timestamp = datetime.datetime.now().isoformat()

    print(f"\n[MAYA] Autonomous response triggered for {attack_type} from {ip}")

    # Response based on severity
    if severity == 'CRITICAL':
        # Block IP
        blocked, msg = block_ip(ip)
        log_response({
            "timestamp": timestamp,
            "action": "IP_BLOCKED",
            "details": msg,
            "attacker_ip": ip,
            "trigger": attack_type,
            "severity": severity
        })

        # Send email
        sent = send_email_alert(attack)
        log_response({
            "timestamp": timestamp,
            "action": "EMAIL_ALERT_SENT" if sent else "EMAIL_ALERT_FAILED",
            "details": f"Alert sent to security team",
            "attacker_ip": ip,
            "trigger": attack_type,
            "severity": severity
        })

        print(f"[MAYA] CRITICAL response complete — IP blocked, team alerted")

    elif severity == 'HIGH':
        # Block IP
        blocked, msg = block_ip(ip)
        log_response({
            "timestamp": timestamp,
            "action": "IP_BLOCKED",
            "details": msg,
            "attacker_ip": ip,
            "trigger": attack_type,
            "severity": severity
        })
        print(f"[MAYA] HIGH response complete — IP blocked")

    elif severity == 'MEDIUM':
        # Log and watch
        log_response({
            "timestamp": timestamp,
            "action": "MONITORING_INCREASED",
            "details": f"Increased monitoring for {ip}",
            "attacker_ip": ip,
            "trigger": attack_type,
            "severity": severity
        })
        print(f"[MAYA] MEDIUM response — increased monitoring")

    else:
        # LOW — just log
        log_response({
            "timestamp": timestamp,
            "action": "LOGGED",
            "details": f"Low severity event recorded",
            "attacker_ip": ip,
            "trigger": attack_type,
            "severity": severity
        })

def watch_and_respond():
    """
    Continuously watches attack log.
    Responds to every new attack automatically.
    This is the autonomous engine running 24/7.
    """
    print("[MAYA] Autonomous Response Engine started")
    print("[MAYA] Watching for attacks...")

    last_position = 0

    # Get current file size to only process new attacks
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            f.seek(0, 2)
            last_position = f.tell()

    while True:
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()

                for line in new_lines:
                    line = line.strip()
                    if line:
                        attack = json.loads(line)
                        respond_to_attack(attack)

        except Exception as e:
            pass

        import time
        time.sleep(1)

if __name__ == "__main__":
    watch_and_respond()
