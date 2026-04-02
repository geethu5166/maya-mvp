from flask import Flask, render_template
from auth import auth, login_required
from flask_socketio import SocketIO
import json
import os
import threading
import time

app = Flask(__name__, template_folder='/root/maya-mvp/dashboard/templates')
app.secret_key = 'maya-vaultrap-secret-2026'
app.register_blueprint(auth)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'attacks.log')

def read_attacks():
    attacks = []
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    attacks.append(json.loads(line))
    except:
        pass
    return attacks

def get_stats(attacks):
    total = len(attacks)
    critical = len([a for a in attacks if a.get('severity') == 'CRITICAL'])
    high = len([a for a in attacks if a.get('severity') == 'HIGH'])
    ssh = len([a for a in attacks if a.get('honeypot') == 'SSH'])
    web = len([a for a in attacks if a.get('honeypot') == 'WEB'])
    unique_ips = len(set(a.get('attacker_ip', '') for a in attacks))
    return {
        'total': total,
        'critical': critical,
        'high': high,
        'ssh': ssh,
        'web': web,
        'unique_ips': unique_ips,
        'medium': len([a for a in attacks if a.get('severity') == 'MEDIUM']),
        'low': len([a for a in attacks if a.get('severity') == 'LOW'])
    }

def watch_log():
    last_size = 0
    while True:
        try:
            size = os.path.getsize(LOG_FILE)
            if size != last_size:
                attacks = read_attacks()
                stats = get_stats(attacks)
                socketio.emit('update', {
                    'attacks': attacks[-20:],
                    'stats': stats
                })
                last_size = size
        except:
            pass
        time.sleep(1)

@app.route('/')
@login_required
def index():
    attacks = read_attacks()
    stats = get_stats(attacks)
    return render_template('index.html',
                         attacks=list(reversed(attacks[-20:])),
                         stats=stats)

@socketio.on('connect')
def handle_connect():
    attacks = read_attacks()
    stats = get_stats(attacks)
    socketio.emit('update', {
        'attacks': attacks[-20:],
        'stats': stats
    })

if __name__ == '__main__':
    watcher = threading.Thread(target=watch_log)
    watcher.daemon = True
    watcher.start()
    print("[MAYA] Dashboard running on http://127.0.0.1:5000")
    print("-" * 50)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
