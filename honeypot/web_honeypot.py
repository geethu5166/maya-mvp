from flask import Flask, request, render_template_string
import json
import datetime
import os

app = Flask(__name__)
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'attacks.log')

def log_attack(data):
    print(f"[MAYA ALERT] {data['timestamp']} | IP: {data['attacker_ip']} | Type: {data['type']}")
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

BANK_PAGE = """<!DOCTYPE html>
<html>
<head><title>SecureBank India - Net Banking</title>
<style>
body{font-family:Arial;background:#f0f4f8;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{background:white;padding:40px;border-radius:8px;width:380px;box-shadow:0 2px 20px rgba(0,0,0,0.1)}
.title{text-align:center;color:#1a237e;font-size:24px;font-weight:bold;margin-bottom:5px}
.sub{text-align:center;color:#666;font-size:12px;margin-bottom:20px}
label{display:block;font-size:13px;color:#333;margin-bottom:5px;font-weight:500}
input{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px;margin-bottom:15px}
.btn{width:100%;padding:12px;background:#1a237e;color:white;border:none;border-radius:4px;font-size:15px;cursor:pointer}
.warn{background:#fff3e0;border-left:3px solid #ff9800;padding:10px;font-size:12px;color:#e65100;margin-bottom:20px}
.foot{text-align:center;margin-top:15px;font-size:11px;color:#999}
</style></head>
<body>
<div class="box">
<div class="title">SecureBank India</div>
<div class="sub">Internet Banking Portal</div>
<div class="warn">Never share your password or OTP with anyone including bank staff.</div>
<form method="POST" action="/login">
<label>Customer ID</label>
<input type="text" name="username" placeholder="Enter Customer ID" required>
<label>Password</label>
<input type="password" name="password" placeholder="Enter Password" required>
<button type="submit" class="btn">Login Securely</button>
</form>
<div class="foot">&copy; 2026 SecureBank India Ltd | Regulated by RBI</div>
</div>
</body></html>"""

ERROR_PAGE = """<!DOCTYPE html>
<html>
<head><title>SecureBank India - Error</title>
<style>
body{font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;background:#f0f4f8}
.box{background:white;padding:40px;border-radius:8px;width:380px;text-align:center}
.err{color:#c62828;margin:20px 0}
a{color:#1a237e;font-size:13px}
</style></head>
<body>
<div class="box">
<div style="color:#1a237e;font-size:22px;font-weight:bold">SecureBank India</div>
<div class="err">Invalid Customer ID or Password.<br>Please try again.</div>
<a href="/">Back to Login</a>
</div>
</body></html>"""

@app.route('/')
def home():
    log_attack({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "WEB_RECON",
        "attacker_ip": request.remote_addr,
        "honeypot": "WEB",
        "severity": "LOW",
        "path": request.path,
        "user_agent": request.headers.get('User-Agent', 'Unknown')
    })
    return render_template_string(BANK_PAGE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    log_attack({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "WEB_CREDENTIAL_HARVEST",
        "attacker_ip": request.remote_addr,
        "honeypot": "WEB",
        "severity": "CRITICAL",
        "credentials": f"{username}:{password}",
        "user_agent": request.headers.get('User-Agent', 'Unknown')
    })
    return render_template_string(ERROR_PAGE)

@app.route('/admin')
@app.route('/wp-admin')
@app.route('/.env')
@app.route('/config.php')
def traps():
    log_attack({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "WEB_SCAN",
        "attacker_ip": request.remote_addr,
        "honeypot": "WEB",
        "severity": "MEDIUM",
        "path": request.path
    })
    return "404 Not Found", 404

if __name__ == '__main__':
    print("[MAYA] Web Honeypot running on http://localhost:5001")
    print("-" * 50)
    app.run(host='0.0.0.0', port=5001, debug=False)
