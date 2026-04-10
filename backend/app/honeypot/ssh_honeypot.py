"""
SSH Honeypot - Paramiko-based fake SSH server
Logs all credential attempts to the central event pipeline
"""

import socket
import threading
import paramiko
import datetime
import logging
from typing import Tuple

from app.core.event_pipeline import EventPipeline

logger = logging.getLogger(__name__)

# Generate a simple RSA host key for our fake SSH server
host_key = paramiko.RSAKey.generate(2048)

# Initialize event pipeline
event_pipeline = None


def log_attack(attacker_ip: str, attacker_port: int, username: str, password: str):
    """
    Every time an attacker tries to login,
    we record exactly who they are and what they tried.
    This is our core data collection for the event pipeline.
    """
    global event_pipeline
    
    if event_pipeline is None:
        from app.core.event_pipeline import EventPipeline
        event_pipeline = EventPipeline()
    
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
    logger.warning(
        f"[SSH HONEYPOT] Attack from {attacker_ip}:{attacker_port} | "
        f"Tried: {username}:{password}"
    )
    
    # Publish to event pipeline for enrichment and correlation
    try:
        event = event_pipeline.publish(attack_data)
        logger.info(f"[SSH HONEYPOT] Event {event.get('event_id')} published")
    except Exception as e:
        logger.error(f"Failed to publish SSH attack event: {e}")


class FakeSSHServer(paramiko.ServerInterface):
    """
    This is our fake SSH server.
    It pretends to be a real server.
    It NEVER lets anyone actually login.
    But it records every single attempt.
    """
    
    def __init__(self, client_ip: str, client_port: int):
        self.client_ip = client_ip
        self.client_port = client_port
        self.event = threading.Event()
    
    def check_channel_request(self, kind: str, chanid: int):
        """Handle channel requests"""
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_password(self, username: str, password: str):
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
    
    def check_auth_publickey(self, username: str, key):
        """Always reject public key auth"""
        return paramiko.AUTH_FAILED
    
    def get_allowed_auths(self, username: str):
        """Only claim password auth is available"""
        return 'password'


def handle_connection(client_socket, client_address: Tuple[str, int]):
    """
    Handle each incoming connection in its own thread.
    This means we can handle multiple attackers simultaneously.
    """
    client_ip = client_address[0]
    client_port = client_address[1]
    
    logger.info(f"[SSH HONEYPOT] New connection from {client_ip}:{client_port}")
    
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
        logger.debug(f"SSH connection error: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass


def start_ssh_honeypot(port: int = 2222):
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
    
    logger.info(f"[SSH HONEYPOT] Listening on port {port}")
    logger.info("[SSH HONEYPOT] All attempts flow through the event pipeline")
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            # Handle each connection in a separate thread
            # So multiple attackers can hit us simultaneously
            thread = threading.Thread(
                target=handle_connection,
                args=(client_socket, client_address),
                daemon=True
            )
            thread.start()
        except KeyboardInterrupt:
            logger.info("[SSH HONEYPOT] Stopped.")
            break
        except Exception as e:
            logger.debug(f"SSH server error: {e}")


if __name__ == "__main__":
    # For local testing
    logging.basicConfig(level=logging.INFO)
    start_ssh_honeypot(port=2222)
