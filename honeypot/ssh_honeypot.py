import sys; sys.path.append("/root/maya-mvp")
from autoblock import check_and_block_attacker
import socket
import threading
import paramiko
import json
import datetime
import os

# Generate a simple RSA host key for our fake SSH server
host_key = paramiko.RSAKey.generate(2048)

# Log file path
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'attacks.log')

def log_attack(attacker_ip, attacker_port, username, password):
    """
    Every time an attacker tries to login,
    we record exactly who they are and what they tried.
    This is our core data collection.
    """
    attack_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "SSH_BRUTE_FORCE",
        "attacker_ip": attacker_ip,
        "attacker_port": attacker_port,
        "username_tried": username,
        "password_tried": password,
        "honeypot": "SSH",
        "severity": "HIGH"
    }
    
    # Print to terminal so you can watch attacks live
    print(f"[MAYA ALERT] {attack_data['timestamp']} | "
          f"IP: {attacker_ip} | "
          f"Tried: {username}:{password}")
    
    # Save to log file for the dashboard to read
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(attack_data) + '\n')
    check_and_block_attacker(attacker_ip)

class FakeSSHServer(paramiko.ServerInterface):
    """
    This is our fake SSH server.
    It pretends to be a real server.
    It NEVER lets anyone actually login.
    But it records every single attempt.
    """
    
    def __init__(self, client_ip, client_port):
        self.client_ip = client_ip
        self.client_port = client_port
        self.event = threading.Event()
    
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_password(self, username, password):
        """
        This is called every time an attacker
        tries a username and password combination.
        We log it — then always say wrong password.
        """
        log_attack(
            self.client_ip,
            self.client_port,
            username,
            password
        )
        # Always return failure — we never let them in
        # But we pretend to think about it (realistic behavior)
        return paramiko.AUTH_FAILED
    
    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED
    
    def get_allowed_auths(self, username):
        return 'password'

def handle_connection(client_socket, client_address):
    """
    Handle each incoming connection in its own thread.
    This means we can handle multiple attackers simultaneously.
    """
    client_ip = client_address[0]
    client_port = client_address[1]
    
    print(f"[MAYA] New connection from {client_ip}:{client_port}")
    
    try:
        # Create SSH transport layer
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(host_key)
        
        # Create our fake server
        fake_server = FakeSSHServer(client_ip, client_port)
        
        # Start the SSH negotiation
        # Attacker thinks they're connecting to a real server
        transport.start_server(server=fake_server)
        
        # Keep connection open for 30 seconds max
        # This wastes the attacker's time
        fake_server.event.wait(30)
        
    except Exception as e:
        pass
    finally:
        try:
            client_socket.close()
        except:
            pass

def start_ssh_honeypot(port=2222):
    """
    Start listening for SSH connections.
    We use port 2222 instead of 22
    because port 22 requires root access.
    In production deployment we'll redirect 22 → 2222.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(100)
    
    print(f"[MAYA] SSH Honeypot listening on port {port}")
    print(f"[MAYA] Waiting for attackers...")
    print(f"[MAYA] All attempts logged to {LOG_FILE}")
    print("-" * 50)
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            # Handle each connection in a separate thread
            # So multiple attackers can hit us simultaneously
            thread = threading.Thread(
                target=handle_connection,
                args=(client_socket, client_address)
            )
            thread.daemon = True
            thread.start()
        except KeyboardInterrupt:
            print("\n[MAYA] Honeypot stopped.")
            break
        except Exception as e:
            pass

if __name__ == "__main__":
    start_ssh_honeypot(port=2222)