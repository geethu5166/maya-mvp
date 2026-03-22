import socket
import threading
import struct
import json
import datetime
import os
import time

LOG_FILE = '/home/kali/maya-mvp/logs/attacks.log'

def log_attack(data):
    print(f"[DB HONEYPOT] {data['timestamp']} | {data['type']} | IP: {data['attacker_ip']}")
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

def mysql_greeting():
    server_version = b"8.0.32\x00"
    connection_id = struct.pack('<I', 1)
    auth_data = b"ABCDEFGH\x00"
    capability_flags = struct.pack('<H', 0xffff)
    charset = b"\x21"
    status_flags = struct.pack('<H', 0x0002)
    capability_flags2 = struct.pack('<H', 0x8181)
    auth_len = b"\x15"
    reserved = b"\x00" * 10
    auth_data2 = b"ABCDEFGHIJKL\x00"
    plugin = b"mysql_native_password\x00"
    payload = (b"\x0a" + server_version + connection_id +
               auth_data + capability_flags + charset +
               status_flags + capability_flags2 + auth_len +
               reserved + auth_data2 + plugin)
    length = struct.pack('<I', len(payload))[:3]
    return length + b"\x00" + payload

def mysql_error():
    msg = b"Access denied for user 'root'@'localhost' (using password: YES)"
    code = struct.pack('<H', 1045)
    state = b"#28000"
    payload = b"\xff" + code + state + msg
    length = struct.pack('<I', len(payload))[:3]
    return length + b"\x02" + payload

def handle_mysql(client_socket, addr):
    ip = addr[0]
    port = addr[1]

    # Log immediately when connection is made
    log_attack({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "DB_CONNECTION",
        "severity": "HIGH",
        "honeypot": "MYSQL",
        "attacker_ip": ip,
        "attacker_port": port,
        "details": f"MySQL connection attempt from {ip}:{port}"
    })

    try:
        client_socket.send(mysql_greeting())
        client_socket.settimeout(10)

        try:
            data = client_socket.recv(4096)
            if data and len(data) > 4:
                # Try extract username
                username = "unknown"
                try:
                    payload = data[4:]
                    parts = payload.split(b'\x00')
                    for part in parts:
                        if part and 2 < len(part) < 32:
                            try:
                                decoded = part.decode('utf-8', errors='ignore')
                                if decoded.isprintable() and decoded.strip():
                                    username = decoded.strip()
                                    break
                            except:
                                pass
                except:
                    pass

                log_attack({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "type": "DB_LOGIN_ATTEMPT",
                    "severity": "CRITICAL",
                    "honeypot": "MYSQL",
                    "attacker_ip": ip,
                    "attacker_port": port,
                    "username_tried": username,
                    "details": f"MySQL login — user:{username}"
                })

                client_socket.send(mysql_error())

        except socket.timeout:
            pass

    except Exception as e:
        pass
    finally:
        client_socket.close()

def handle_redis(client_socket, addr):
    ip = addr[0]
    try:
        log_attack({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "REDIS_PROBE",
            "severity": "HIGH",
            "honeypot": "REDIS",
            "attacker_ip": ip,
            "details": f"Redis probe from {ip}"
        })

        client_socket.settimeout(5)
        try:
            data = client_socket.recv(1024)
            if data:
                cmd = data.decode('utf-8', errors='ignore').strip()[:100]
                log_attack({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "type": "REDIS_COMMAND",
                    "severity": "CRITICAL",
                    "honeypot": "REDIS",
                    "attacker_ip": ip,
                    "command": cmd,
                    "details": f"Redis command: {cmd}"
                })
                if 'AUTH' in cmd.upper():
                    client_socket.send(b"-WRONGPASS invalid username-password pair\r\n")
                else:
                    client_socket.send(b"-NOAUTH Authentication required\r\n")
        except socket.timeout:
            pass
    except:
        pass
    finally:
        client_socket.close()

def start_server(handler, port, name):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('0.0.0.0', port))
        server.listen(100)
        print(f"[DB HONEYPOT] {name} listening on port {port}")
        while True:
            try:
                client, addr = server.accept()
                t = threading.Thread(target=handler, args=(client, addr))
                t.daemon = True
                t.start()
            except:
                break
    except OSError as e:
        print(f"[DB HONEYPOT] {name} port {port} error: {e}")
        print(f"[DB HONEYPOT] Try: sudo python3 honeypot/db_honeypot.py")

def run_db_honeypots():
    print("[DB HONEYPOT] Starting MySQL:3306 and Redis:6379")
    threads = [
        threading.Thread(target=start_server, args=(handle_mysql, 3306, "MySQL")),
        threading.Thread(target=start_server, args=(handle_redis, 6379, "Redis")),
    ]
    for t in threads:
        t.daemon = True
        t.start()
    print("[DB HONEYPOT] All database honeypots active")
    print("[DB HONEYPOT] Every connection logged instantly")
    print("-" * 55)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[DB HONEYPOT] Stopped")

if __name__ == "__main__":
    run_db_honeypots()
