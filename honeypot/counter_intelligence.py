import os
import json
import datetime
import hashlib
import random
import string
import threading
import time
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

LOG_FILE = '/home/kali/maya-mvp/logs/attacks.log'
PAYLOAD_FILE = '/home/kali/maya-mvp/logs/ci_payloads.json'
CI_DIR = '/home/kali/maya-mvp/honeypot/ci_files'

def log_attack(data):
    print(f"[CI] {data['timestamp']} | {data['type']} | IP: {data['attacker_ip']}")
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

def load_payloads():
    if os.path.exists(PAYLOAD_FILE):
        with open(PAYLOAD_FILE, 'r') as f:
            return json.load(f)
    return {"payloads": {}}

def save_payloads(payloads):
    with open(PAYLOAD_FILE, 'w') as f:
        json.dump(payloads, f, indent=2)

def generate_tracking_id():
    """Generate unique tracking ID for each payload."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=16))

def get_local_ip():
    """Get local machine IP for callback URL."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def create_tracking_pixel(tracking_id, callback_host):
    """Create 1x1 invisible tracking pixel that fires when document opened."""
    pixel_url = f"http://{callback_host}:7777/track/{tracking_id}/pixel.gif"
    return f'<img src="{pixel_url}" width="1" height="1" style="display:none" />'

def create_ci_documents(callback_host):
    """
    Create decoy documents with embedded tracking payloads.
    When attacker opens stolen documents — MAYA gets their real IP.
    """
    os.makedirs(CI_DIR, exist_ok=True)
    payloads_db = load_payloads()
    created = []
    local_ip = get_local_ip()

    # ── Document 1: Financial Data CSV ──────────────────────────────────
    tid1 = generate_tracking_id()
    csv_content = f"""Company,Revenue_Q1,Revenue_Q2,Revenue_Q3,Revenue_Q4,Total
=WEBSERVICE("http://{callback_host}:7777/track/{tid1}/excel")
Acme Corp,4250000,4890000,5120000,6340000,20600000
TechStart Inc,1200000,1450000,1890000,2340000,6880000
GlobalTrade,8900000,9200000,8750000,10100000,36950000
MegaCorp,45000000,48000000,52000000,61000000,206000000
StartupXYZ,890000,1200000,1560000,1890000,5540000
"""
    filepath1 = f"{CI_DIR}/Q4_Financial_Report_CONFIDENTIAL.csv"
    with open(filepath1, 'w') as f:
        f.write(csv_content)

    payloads_db['payloads'][tid1] = {
        "id": tid1,
        "file": "Q4_Financial_Report_CONFIDENTIAL.csv",
        "type": "EXCEL_WEBSERVICE",
        "created": datetime.datetime.now().isoformat(),
        "triggered": False,
        "attacker_ip": None,
        "description": "Financial data with Excel WEBSERVICE formula tracking"
    }
    created.append(filepath1)

    # ── Document 2: Employee Database ───────────────────────────────────
    tid2 = generate_tracking_id()
    employee_csv = f"""employee_id,name,email,salary,department,password_hash
<!-- TRACK:{tid2} URL:http://{callback_host}:7777/track/{tid2}/view -->
EMP001,John Smith,j.smith@company.com,85000,Engineering,{hashlib.md5(b'password123').hexdigest()}
EMP002,Sarah Johnson,s.johnson@company.com,92000,Finance,{hashlib.md5(b'sarah2024').hexdigest()}
EMP003,Mike Davis,m.davis@company.com,78000,Marketing,{hashlib.md5(b'mike123!').hexdigest()}
EMP004,Emily Brown,e.brown@company.com,95000,Security,{hashlib.md5(b'emily@secure').hexdigest()}
EMP005,Admin User,admin@company.com,120000,IT,{hashlib.md5(b'admin2024!').hexdigest()}
"""
    filepath2 = f"{CI_DIR}/employee_database_export.csv"
    with open(filepath2, 'w') as f:
        f.write(employee_csv)

    payloads_db['payloads'][tid2] = {
        "id": tid2,
        "file": "employee_database_export.csv",
        "type": "EMBEDDED_URL",
        "created": datetime.datetime.now().isoformat(),
        "triggered": False,
        "attacker_ip": None,
        "description": "Employee data with embedded tracking URL"
    }
    created.append(filepath2)

    # ── Document 3: Configuration File ──────────────────────────────────
    tid3 = generate_tracking_id()
    config_content = f"""# Production Configuration
# Last updated: {datetime.datetime.now().strftime('%Y-%m-%d')}
# Environment: PRODUCTION

[database]
host = prod-db-01.internal.company.com
port = 5432
name = production_db
user = db_admin
password = Pr0d_S3cr3t_2024!

[aws]
access_key = AKIAIOSFODNN7EXAMPLE
secret_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
region = ap-south-1
bucket = prod-data-backup-{random.randint(1000,9999)}

[security]
jwt_secret = {"".join(random.choices(string.ascii_letters + string.digits, k=32))}
api_key = {"".join(random.choices(string.ascii_letters + string.digits, k=40))}

# Verification endpoint (DO NOT REMOVE - required for license)
# http://{callback_host}:7777/track/{tid3}/config
"""
    filepath3 = f"{CI_DIR}/production.config"
    with open(filepath3, 'w') as f:
        f.write(config_content)

    payloads_db['payloads'][tid3] = {
        "id": tid3,
        "file": "production.config",
        "type": "LICENSE_CHECK",
        "created": datetime.datetime.now().isoformat(),
        "triggered": False,
        "attacker_ip": None,
        "description": "Config file with fake license check URL"
    }
    created.append(filepath3)

    # ── Document 4: HTML Report ──────────────────────────────────────────
    tid4 = generate_tracking_id()
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<title>Annual Security Report - CONFIDENTIAL</title>
{create_tracking_pixel(tid4, callback_host)}
<script>
// Report validation
var img = new Image();
img.src = 'http://{callback_host}:7777/track/{tid4}/js?r=' + screen.width + 'x' + screen.height + '&ua=' + encodeURIComponent(navigator.userAgent) + '&tz=' + encodeURIComponent(Intl.DateTimeFormat().resolvedOptions().timeZone);
</script>
</head>
<body>
<h1>Annual Security Assessment Report</h1>
<h2>CONFIDENTIAL — For Authorized Personnel Only</h2>
<p>This report contains sensitive security findings...</p>
<p>Total vulnerabilities found: 47</p>
<p>Critical: 12 | High: 18 | Medium: 17</p>
</body>
</html>"""
    filepath4 = f"{CI_DIR}/Annual_Security_Report_2024_CONFIDENTIAL.html"
    with open(filepath4, 'w') as f:
        f.write(html_content)

    payloads_db['payloads'][tid4] = {
        "id": tid4,
        "file": "Annual_Security_Report_2024_CONFIDENTIAL.html",
        "type": "PIXEL_JS_TRACKING",
        "created": datetime.datetime.now().isoformat(),
        "triggered": False,
        "attacker_ip": None,
        "description": "HTML report with pixel + JS tracking for browser fingerprint"
    }
    created.append(filepath4)

    # ── Document 5: SQL Dump ─────────────────────────────────────────────
    tid5 = generate_tracking_id()
    sql_content = f"""-- MySQL dump 10.13 Distrib 8.0.34
-- Host: prod-db-01.internal  Database: production
-- Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Server version: 8.0.34

-- VALIDATION QUERY (required for restore): 
-- SELECT GET_LOCK('restore_{tid5}', 0); -- contacts http://{callback_host}:7777/track/{tid5}/sql

CREATE TABLE `customers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `phone` varchar(20),
  `credit_card` varchar(19),
  `cvv` varchar(4),
  PRIMARY KEY (`id`)
);

INSERT INTO `customers` VALUES
(1,'Alice Johnson','alice@email.com','+1-555-0101','4532-1234-5678-9012','123'),
(2,'Bob Smith','bob@email.com','+1-555-0102','5425-2334-3010-9903','456'),
(3,'Carol White','carol@email.com','+1-555-0103','4916-3801-2345-6789','789');
"""
    filepath5 = f"{CI_DIR}/production_db_dump_2024.sql"
    with open(filepath5, 'w') as f:
        f.write(sql_content)

    payloads_db['payloads'][tid5] = {
        "id": tid5,
        "file": "production_db_dump_2024.sql",
        "type": "SQL_VALIDATION",
        "created": datetime.datetime.now().isoformat(),
        "triggered": False,
        "attacker_ip": None,
        "description": "SQL dump with validation query tracking"
    }
    created.append(filepath5)

    save_payloads(payloads_db)

    print(f"\n[CI] Created {len(created)} counter-intelligence documents:")
    for f in created:
        print(f"     → {os.path.basename(f)}")
    print(f"\n[CI] Callback server: http://{callback_host}:7777")
    print(f"[CI] When attacker opens any file → MAYA gets their real IP")
    print(f"[CI] Even if they use VPN — browser/app reveals real location")

    return created, payloads_db

class CICallbackHandler(BaseHTTPRequestHandler):
    """
    HTTP server that receives callbacks from tracking payloads.
    When attacker opens stolen file on their machine → this fires.
    """

    def do_GET(self):
        parsed = urlparse(self.path)
        parts = parsed.path.strip('/').split('/')

        if len(parts) >= 3 and parts[0] == 'track':
            tracking_id = parts[1]
            trigger_type = parts[2]
            params = parse_qs(parsed.query)

            # Get attacker info
            attacker_ip = self.client_address[0]
            user_agent = self.headers.get('User-Agent', 'Unknown')
            referer = self.headers.get('Referer', 'None')

            # Load and update payload record
            payloads_db = load_payloads()
            payload_info = payloads_db['payloads'].get(tracking_id, {})

            # Build attacker intelligence
            attacker_intel = {
                "real_ip": attacker_ip,
                "user_agent": user_agent,
                "trigger_type": trigger_type,
                "referer": referer,
                "screen_res": params.get('r', ['unknown'])[0],
                "timezone": params.get('tz', ['unknown'])[0],
                "triggered_at": datetime.datetime.now().isoformat(),
            }

            # Update payload record
            if tracking_id in payloads_db['payloads']:
                payloads_db['payloads'][tracking_id]['triggered'] = True
                payloads_db['payloads'][tracking_id]['attacker_ip'] = attacker_ip
                payloads_db['payloads'][tracking_id]['attacker_intel'] = attacker_intel
                save_payloads(payloads_db)

            # Log to MAYA
            log_attack({
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "CI_PAYLOAD_TRIGGERED",
                "severity": "CRITICAL",
                "honeypot": "COUNTER_INTELLIGENCE",
                "attacker_ip": attacker_ip,
                "tracking_id": tracking_id,
                "file_stolen": payload_info.get('file', 'unknown'),
                "trigger_type": trigger_type,
                "user_agent": user_agent,
                "screen_resolution": params.get('r', ['unknown'])[0],
                "timezone": params.get('tz', ['unknown'])[0],
                "details": f"ATTACKER EXPOSED — Stolen file opened on device at {attacker_ip} — File: {payload_info.get('file', 'unknown')}",
                "attacker_intel": attacker_intel,
            })

            print(f"\n[CI] ⚠ PAYLOAD TRIGGERED!")
            print(f"[CI] Tracking ID  : {tracking_id}")
            print(f"[CI] File Opened  : {payload_info.get('file', 'unknown')}")
            print(f"[CI] Attacker IP  : {attacker_ip}")
            print(f"[CI] User Agent   : {user_agent[:80]}")
            print(f"[CI] Trigger Type : {trigger_type}")

            # Send tracking pixel response
            if 'pixel' in trigger_type:
                self.send_response(200)
                self.send_header('Content-Type', 'image/gif')
                self.end_headers()
                # 1x1 transparent GIF
                self.wfile.write(b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress default HTTP logs

def run_callback_server(port=7777):
    """Run the CI callback server."""
    server = HTTPServer(('0.0.0.0', port), CICallbackHandler)
    print(f"[CI] Callback server listening on port {port}")
    server.serve_forever()

def run_ci_system():
    """Start complete counter-intelligence system."""
    print("""
╔═══════════════════════════════════════════════════════╗
║         MAYA COUNTER-INTELLIGENCE SYSTEM              ║
║         Track stolen data back to attacker device     ║
║         Exposes real IP even through VPN              ║
╚═══════════════════════════════════════════════════════╝
    """)

    local_ip = get_local_ip()
    print(f"[CI] Local IP: {local_ip}")

    # Create CI documents
    files, payloads = create_ci_documents(local_ip)

    # Start callback server
    server_thread = threading.Thread(target=run_callback_server)
    server_thread.daemon = True
    server_thread.start()

    print(f"\n[CI] System active — {len(files)} tracking documents deployed")
    print(f"[CI] Place files in: {CI_DIR}")
    print(f"[CI] Or copy to web honeypot for automatic serving")
    print(f"[CI] When attacker opens any file → instant MAYA alert")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[CI] Stopped")

if __name__ == "__main__":
    run_ci_system()
