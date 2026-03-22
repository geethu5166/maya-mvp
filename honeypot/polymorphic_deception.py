import random
import time
import json
import datetime
import os
import threading
import socket
import struct

LOG_FILE = '/home/kali/maya-mvp/logs/attacks.log'
STATE_FILE = '/home/kali/maya-mvp/logs/deception_state.json'

def log_event(data):
    print(f"[POLYMORPHIC] {data['timestamp']} | {data['event']}")
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

# ─── FINGERPRINT LIBRARIES ────────────────────────────────────────────────

OS_FINGERPRINTS = [
    {"os": "Ubuntu 22.04 LTS", "kernel": "5.15.0-91-generic", "ssh_banner": "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6"},
    {"os": "CentOS Linux 7", "kernel": "3.10.0-1160.el7.x86_64", "ssh_banner": "SSH-2.0-OpenSSH_7.4"},
    {"os": "Debian GNU/Linux 11", "kernel": "5.10.0-28-amd64", "ssh_banner": "SSH-2.0-OpenSSH_8.4p1 Debian-5+deb11u3"},
    {"os": "Red Hat Enterprise Linux 8", "kernel": "4.18.0-477.27.1.el8_8.x86_64", "ssh_banner": "SSH-2.0-OpenSSH_8.0"},
    {"os": "Amazon Linux 2", "kernel": "5.10.186-179.751.amzn2.x86_64", "ssh_banner": "SSH-2.0-OpenSSH_7.4"},
    {"os": "Windows Server 2019", "kernel": "10.0.17763", "ssh_banner": "SSH-2.0-OpenSSH_for_Windows_8.1"},
    {"os": "FreeBSD 13.2", "kernel": "FreeBSD 13.2-RELEASE", "ssh_banner": "SSH-2.0-OpenSSH_9.3"},
    {"os": "Alpine Linux 3.18", "kernel": "6.1.34-0-lts", "ssh_banner": "SSH-2.0-OpenSSH_9.3"},
]

WEB_SERVER_SIGNATURES = [
    {"server": "Apache/2.4.57 (Ubuntu)", "x-powered-by": "PHP/8.1.2", "framework": "Laravel"},
    {"server": "nginx/1.24.0", "x-powered-by": None, "framework": "Express"},
    {"server": "Microsoft-IIS/10.0", "x-powered-by": "ASP.NET", "framework": ".NET"},
    {"server": "Apache/2.2.34 (Amazon)", "x-powered-by": "PHP/7.4.33", "framework": "WordPress"},
    {"server": "nginx/1.18.0 (Ubuntu)", "x-powered-by": "PHP/8.0.30", "framework": "Symfony"},
    {"server": "Apache Tomcat/9.0.82", "x-powered-by": "Servlet/4.0 JSP/2.3", "framework": "Java"},
    {"server": "cloudflare", "x-powered-by": None, "framework": "Next.js"},
    {"server": "LiteSpeed", "x-powered-by": "PHP/8.2.9", "framework": "Django"},
]

DB_VERSIONS = [
    {"db": "MySQL", "version": "8.0.34", "banner": "8.0.34-MySQL Community Server - GPL"},
    {"db": "MySQL", "version": "5.7.43", "banner": "5.7.43-log"},
    {"db": "MySQL", "version": "8.0.32", "banner": "8.0.32"},
    {"db": "MariaDB", "version": "10.6.15", "banner": "10.6.15-MariaDB-0ubuntu0.22.04.1"},
    {"db": "MariaDB", "version": "10.11.5", "banner": "10.11.5-MariaDB"},
    {"db": "Percona", "version": "8.0.34-26", "banner": "8.0.34-26-Percona Server"},
]

HOSTNAME_PATTERNS = [
    "prod-web-{n:02d}", "app-server-{n:02d}", "db-primary-{n:02d}",
    "api-gateway-{n:02d}", "backend-{n:02d}", "frontend-{n:02d}",
    "srv-{n:02d}-prod", "ec2-{ip}", "ip-{ip_dash}",
    "compute-{n:03d}", "node-{n:02d}", "worker-{n:02d}",
]

FAKE_SERVICES = [
    {"port": 8080, "service": "HTTP Alt", "banner": "HTTP/1.1 200 OK\r\nServer: Apache\r\n"},
    {"port": 8443, "service": "HTTPS Alt", "banner": "HTTP/1.1 200 OK\r\nServer: nginx\r\n"},
    {"port": 9200, "service": "Elasticsearch", "banner": '{"name":"node-01","cluster_name":"production"}'},
    {"port": 27017, "service": "MongoDB", "banner": "MongoDB server information"},
    {"port": 5432, "service": "PostgreSQL", "banner": "PostgreSQL 15.4"},
    {"port": 6379, "service": "Redis", "banner": "+PONG\r\n"},
    {"port": 11211, "service": "Memcached", "banner": "VERSION 1.6.21\r\n"},
    {"port": 2181, "service": "Zookeeper", "banner": "Zookeeper version: 3.7.1"},
]

# ─── STATE MANAGEMENT ─────────────────────────────────────────────────────

class DeceptionState:
    def __init__(self):
        self.current_os = None
        self.current_web = None
        self.current_db = None
        self.current_hostname = None
        self.current_services = []
        self.rotation_count = 0
        self.last_rotation = None
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                self.rotation_count = state.get('rotation_count', 0)
        self.rotate()

    def save_state(self):
        state = {
            "current_os": self.current_os,
            "current_web": self.current_web,
            "current_db": self.current_db,
            "current_hostname": self.current_hostname,
            "rotation_count": self.rotation_count,
            "last_rotation": self.last_rotation,
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)

    def generate_hostname(self):
        n = random.randint(1, 99)
        ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        ip_dash = ip.replace('.', '-')
        pattern = random.choice(HOSTNAME_PATTERNS)
        return pattern.format(n=n, ip=ip.split('.')[-1], ip_dash=ip_dash)

    def rotate(self):
        """Rotate all deception fingerprints."""
        old_os = self.current_os
        self.current_os = random.choice(OS_FINGERPRINTS)
        self.current_web = random.choice(WEB_SERVER_SIGNATURES)
        self.current_db = random.choice(DB_VERSIONS)
        self.current_hostname = self.generate_hostname()
        self.current_services = random.sample(FAKE_SERVICES, k=random.randint(3, 6))
        self.rotation_count += 1
        self.last_rotation = datetime.datetime.now().isoformat()
        self.save_state()

        if old_os:
            log_event({
                "timestamp": datetime.datetime.now().isoformat(),
                "event": "DECEPTION_ROTATION",
                "type": "POLYMORPHIC_ROTATION",
                "severity": "LOW",
                "honeypot": "POLYMORPHIC",
                "attacker_ip": "SYSTEM",
                "details": f"Rotation #{self.rotation_count} — OS:{self.current_os['os']} Web:{self.current_web['server']} DB:{self.current_db['banner']}",
                "rotation_count": self.rotation_count,
            })

        print(f"\n[POLYMORPHIC] ═══ ROTATION #{self.rotation_count} ═══")
        print(f"[POLYMORPHIC] OS Fingerprint  : {self.current_os['os']}")
        print(f"[POLYMORPHIC] SSH Banner       : {self.current_os['ssh_banner']}")
        print(f"[POLYMORPHIC] Web Server       : {self.current_web['server']}")
        print(f"[POLYMORPHIC] Database         : {self.current_db['banner']}")
        print(f"[POLYMORPHIC] Hostname         : {self.current_hostname}")
        print(f"[POLYMORPHIC] Active Services  : {len(self.current_services)}")
        print(f"[POLYMORPHIC] Next rotation in : 30 minutes")

    def get_ssh_banner(self):
        return self.current_os['ssh_banner']

    def get_http_headers(self):
        headers = {
            "Server": self.current_web['server'],
            "X-Powered-By": self.current_web.get('x-powered-by', ''),
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
        }
        return {k: v for k, v in headers.items() if v}

    def get_db_banner(self):
        return self.current_db['banner']

    def get_hostname(self):
        return self.current_hostname

# ─── POLYMORPHIC SSH HONEYPOT ─────────────────────────────────────────────

def polymorphic_ssh_handler(client_socket, addr, state):
    """SSH honeypot with rotating fingerprint."""
    ip = addr[0]
    try:
        # Use current OS fingerprint for SSH banner
        banner = state.get_ssh_banner() + "\r\n"
        client_socket.send(banner.encode())
        client_socket.settimeout(10)

        try:
            data = client_socket.recv(1024)
            if data:
                log_event({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "event": "POLYMORPHIC_SSH_PROBE",
                    "type": "POLYMORPHIC_SSH_PROBE",
                    "severity": "HIGH",
                    "honeypot": "POLYMORPHIC_SSH",
                    "attacker_ip": ip,
                    "fingerprint_shown": state.get_ssh_banner(),
                    "os_fingerprint": state.current_os['os'],
                    "details": f"SSH probe against {state.current_os['os']} fingerprint — rotation #{state.rotation_count}"
                })
        except socket.timeout:
            pass
    except:
        pass
    finally:
        client_socket.close()

def run_polymorphic_ssh(state, port=2223):
    """Run polymorphic SSH honeypot on alternate port."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('0.0.0.0', port))
        server.listen(50)
        print(f"[POLYMORPHIC] SSH honeypot on port {port}")

        while True:
            try:
                client, addr = server.accept()
                t = threading.Thread(target=polymorphic_ssh_handler, args=(client, addr, state))
                t.daemon = True
                t.start()
            except:
                break
    except OSError as e:
        print(f"[POLYMORPHIC] SSH port {port} error: {e}")

# ─── POLYMORPHIC WEB HONEYPOT ─────────────────────────────────────────────

def run_polymorphic_web(state, port=5002):
    """Web honeypot with rotating server fingerprints."""
    from flask import Flask, request, Response
    import json

    app = Flask(__name__)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        ip = request.remote_addr
        headers = state.get_http_headers()

        log_event({
            "timestamp": datetime.datetime.now().isoformat(),
            "event": "POLYMORPHIC_WEB_PROBE",
            "type": "POLYMORPHIC_WEB_PROBE",
            "severity": "MEDIUM",
            "honeypot": "POLYMORPHIC_WEB",
            "attacker_ip": ip,
            "path_probed": f"/{path}",
            "fingerprint_shown": headers.get('Server', ''),
            "os_fingerprint": state.current_os['os'],
            "details": f"Web probe /{path} — showing {headers.get('Server','')} fingerprint"
        })

        # Respond based on path
        if 'api' in path or 'v1' in path or 'v2' in path:
            body = json.dumps({"status": "ok", "version": "1.0.0", "env": "production"})
            content_type = 'application/json'
        elif 'admin' in path or 'login' in path:
            body = '<html><body><h1>Admin Login</h1><form><input name="user"><input name="pass" type="password"><button>Login</button></form></body></html>'
            content_type = 'text/html'
        elif '.env' in path or 'config' in path:
            body = '# Config file\nDB_HOST=localhost\nDB_PASS=secret123\n'
            content_type = 'text/plain'
        else:
            body = f'<html><head><title>{state.current_hostname}</title></head><body><h1>Welcome</h1></body></html>'
            content_type = 'text/html'

        response = Response(body, content_type=content_type)
        for key, value in headers.items():
            response.headers[key] = value

        return response

    print(f"[POLYMORPHIC] Web honeypot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ─── ROTATION SCHEDULER ───────────────────────────────────────────────────

def rotation_scheduler(state, interval_minutes=30):
    """Rotate fingerprints every 30 minutes."""
    print(f"[POLYMORPHIC] Auto-rotation every {interval_minutes} minutes")
    while True:
        time.sleep(interval_minutes * 60)
        print(f"\n[POLYMORPHIC] Time-based rotation triggered...")
        state.rotate()

def run_polymorphic_system():
    """Start complete polymorphic deception system."""
    print("""
╔═══════════════════════════════════════════════════════╗
║         MAYA POLYMORPHIC DECEPTION SYSTEM             ║
║         Rotating fingerprints every 30 minutes        ║
║         Attackers cannot identify our decoys          ║
╚═══════════════════════════════════════════════════════╝
    """)

    state = DeceptionState()

    threads = [
        threading.Thread(target=run_polymorphic_ssh, args=(state,)),
        threading.Thread(target=run_polymorphic_web, args=(state,)),
        threading.Thread(target=rotation_scheduler, args=(state,)),
    ]

    for t in threads:
        t.daemon = True
        t.start()

    print("[POLYMORPHIC] All systems active")
    print("[POLYMORPHIC] Fingerprints rotating every 30 minutes")
    print("[POLYMORPHIC] Attackers cannot fingerprint our decoys")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[POLYMORPHIC] Stopped")

if __name__ == "__main__":
    run_polymorphic_system()
