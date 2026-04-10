"""
Database Honeypot - Fake MySQL and Redis servers
Logs all connection attempts and commands to the event pipeline
"""

import socket
import threading
import struct
import datetime
import logging
from typing import Tuple

from app.core.event_pipeline import EventPipeline

logger = logging.getLogger(__name__)

# Initialize event pipeline
event_pipeline = None


def get_event_pipeline():
    """Lazy initialize event pipeline"""
    global event_pipeline
    if event_pipeline is None:
        event_pipeline = EventPipeline()
    return event_pipeline


def log_attack(data: dict):
    """Log attack data to event pipeline"""
    try:
        pipeline = get_event_pipeline()
        data['timestamp'] = datetime.datetime.now().isoformat()
        logger.warning(
            f"[DB HONEYPOT] {data['type']} from {data['attacker_ip']} | "
            f"Details: {data.get('details', 'N/A')}"
        )
        event = pipeline.publish(data)
        logger.info(f"[DB HONEYPOT] Event {event.get('event_id')} published")
    except Exception as e:
        logger.error(f"Failed to publish DB attack event: {e}")


# ==================== MySQL Honeypot ====================

def mysql_greeting():
    """Generate a MySQL 8.0 greeting packet"""
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
    """Generate a MySQL auth error response"""
    msg = b"Access denied for user 'root'@'localhost' (using password: YES)"
    code = struct.pack('<H', 1045)
    state = b"#28000"
    payload = b"\xff" + code + state + msg
    length = struct.pack('<I', len(payload))[:3]
    return length + b"\x02" + payload


def handle_mysql(client_socket, addr: Tuple[str, int]):
    """Handle MySQL connection - log and reject"""
    ip = addr[0]
    port = addr[1]

    # Log connection attempt
    log_attack({
        "type": "DB_CONNECTION",
        "severity": "HIGH",
        "honeypot": "MYSQL",
        "attacker_ip": ip,
        "attacker_port": port,
        "details": f"MySQL connection attempt from {ip}:{port}"
    })

    try:
        # Send MySQL greeting
        client_socket.send(mysql_greeting())
        client_socket.settimeout(10)

        try:
            # Receive auth attempt
            data = client_socket.recv(4096)
            if data and len(data) > 4:
                # Try to extract username from auth packet
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

                # Log login attempt
                log_attack({
                    "type": "DB_LOGIN_ATTEMPT",
                    "severity": "CRITICAL",
                    "honeypot": "MYSQL",
                    "attacker_ip": ip,
                    "attacker_port": port,
                    "username_tried": username,
                    "details": f"MySQL login attempt: user={username}"
                })

                # Send error response
                client_socket.send(mysql_error())

        except socket.timeout:
            pass

    except Exception as e:
        logger.debug(f"MySQL handler error: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass


# ==================== Redis Honeypot ====================

def handle_redis(client_socket, addr: Tuple[str, int]):
    """Handle Redis connection - log and reject"""
    ip = addr[0]

    # Log connection attempt
    log_attack({
        "type": "REDIS_PROBE",
        "severity": "HIGH",
        "honeypot": "REDIS",
        "attacker_ip": ip,
        "details": f"Redis connection from {ip}"
    })

    try:
        client_socket.settimeout(5)
        try:
            # Receive command
            data = client_socket.recv(1024)
            if data:
                cmd = data.decode('utf-8', errors='ignore').strip()[:100]
                
                # Log command attempt
                log_attack({
                    "type": "REDIS_COMMAND",
                    "severity": "CRITICAL",
                    "honeypot": "REDIS",
                    "attacker_ip": ip,
                    "command": cmd,
                    "details": f"Redis command: {cmd}"
                })
                
                # Send auth error
                if 'AUTH' in cmd.upper():
                    client_socket.send(b"-WRONGPASS invalid username-password pair\r\n")
                else:
                    client_socket.send(b"-NOAUTH Authentication required\r\n")
        except socket.timeout:
            pass
    except Exception as e:
        logger.debug(f"Redis handler error: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass


# ==================== Server Startup ====================

def start_server(handler, port: int, name: str):
    """Generic honeypot server startup"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('0.0.0.0', port))
        server.listen(100)
        logger.info(f"[DB HONEYPOT] {name} listening on port {port}")
        
        while True:
            try:
                client_socket, addr = server.accept()
                thread = threading.Thread(
                    target=handler,
                    args=(client_socket, addr),
                    daemon=True
                )
                thread.start()
            except KeyboardInterrupt:
                logger.info(f"[DB HONEYPOT] {name} stopped.")
                break
            except Exception as e:
                logger.debug(f"{name} error: {e}")
    except Exception as e:
        logger.error(f"Failed to start {name}: {e}")
    finally:
        server.close()


def start_mysql_honeypot(port: int = 3306):
    """Start MySQL honeypot server"""
    start_server(handle_mysql, port, "MySQL Honeypot")


def start_redis_honeypot(port: int = 6379):
    """Start Redis honeypot server"""
    start_server(handle_redis, port, "Redis Honeypot")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Start both in threads
    import threading
    
    mysql_thread = threading.Thread(
        target=start_mysql_honeypot,
        daemon=True
    )
    redis_thread = threading.Thread(
        target=start_redis_honeypot,
        daemon=True
    )
    
    mysql_thread.start()
    redis_thread.start()
    
    logger.info("[DB HONEYPOT] Both services running")
    
    try:
        mysql_thread.join()
    except KeyboardInterrupt:
        logger.info("[DB HONEYPOT] Stopped.")
