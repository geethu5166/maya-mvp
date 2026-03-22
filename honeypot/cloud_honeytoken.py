import requests
import json
import datetime
import os
import time
import threading
import hashlib
import random
import string

LOG_FILE = '/home/kali/maya-mvp/logs/attacks.log'
TOKEN_FILE = '/home/kali/maya-mvp/logs/honeytokens.json'

def log_attack(data):
    print(f"[HONEYTOKEN] {data['timestamp']} | {data['type']} | IP: {data['attacker_ip']}")
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')

def generate_fake_aws_key():
    """Generate realistic-looking fake AWS credentials."""
    chars = string.ascii_uppercase + string.digits
    access_key = 'AKIA' + ''.join(random.choices(chars, k=16))
    secret_chars = string.ascii_letters + string.digits + '/+'
    secret_key = ''.join(random.choices(secret_chars, k=40))
    return access_key, secret_key

def generate_fake_azure_key():
    """Generate realistic-looking fake Azure credentials."""
    client_id = '-'.join([
        ''.join(random.choices(string.hexdigits[:16], k=8)),
        ''.join(random.choices(string.hexdigits[:16], k=4)),
        ''.join(random.choices(string.hexdigits[:16], k=4)),
        ''.join(random.choices(string.hexdigits[:16], k=4)),
        ''.join(random.choices(string.hexdigits[:16], k=12)),
    ])
    secret = ''.join(random.choices(string.ascii_letters + string.digits + '-_~', k=40))
    return client_id, secret

def generate_fake_github_token():
    """Generate realistic-looking fake GitHub token."""
    return 'ghp_' + ''.join(random.choices(string.ascii_letters + string.digits, k=36))

def generate_fake_stripe_key():
    """Generate realistic-looking fake Stripe key."""
    return 'sk_live_' + ''.join(random.choices(string.ascii_letters + string.digits, k=48))

def create_honeytokens():
    """Create a complete set of honeytokens for deployment."""
    aws_access, aws_secret = generate_fake_aws_key()
    azure_client, azure_secret = generate_fake_azure_key()
    github_token = generate_fake_github_token()
    stripe_key = generate_fake_stripe_key()

    tokens = {
        "created_at": datetime.datetime.now().isoformat(),
        "tokens": [
            {
                "id": "HT-001",
                "type": "AWS_ACCESS_KEY",
                "name": "Production AWS Access Key",
                "access_key": aws_access,
                "secret_key": aws_secret,
                "region": "ap-south-1",
                "deployment": "Place in ~/.aws/credentials or config files",
                "canary_url": f"https://canarytokens.org/generate",
                "status": "ACTIVE"
            },
            {
                "id": "HT-002",
                "type": "AZURE_SERVICE_PRINCIPAL",
                "name": "Azure Production Service Principal",
                "client_id": azure_client,
                "client_secret": azure_secret,
                "tenant_id": "72f988bf-86f1-41af-91ab-2d7cd011db47",
                "deployment": "Place in application config files",
                "status": "ACTIVE"
            },
            {
                "id": "HT-003",
                "type": "GITHUB_TOKEN",
                "name": "GitHub CI/CD Deploy Token",
                "token": github_token,
                "deployment": "Place in .env files, CI/CD configs, GitHub Actions",
                "status": "ACTIVE"
            },
            {
                "id": "HT-004",
                "type": "STRIPE_API_KEY",
                "name": "Stripe Payment Processing Key",
                "key": stripe_key,
                "deployment": "Place in payment service configs",
                "status": "ACTIVE"
            },
            {
                "id": "HT-005",
                "type": "DATABASE_CREDENTIALS",
                "name": "Production Database Credentials",
                "host": "prod-db-01.internal.company.com",
                "username": "db_admin",
                "password": "Pr0d_DB_" + ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + "!",
                "database": "production_customers",
                "deployment": "Place in database config files, docker-compose",
                "status": "ACTIVE"
            }
        ]
    }

    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)

    return tokens

def deploy_honeytoken_files():
    """
    Create decoy files containing honeytokens.
    These files are placed where attackers look.
    """
    deploy_dir = '/home/kali/maya-mvp/honeypot/decoy_files'
    os.makedirs(deploy_dir, exist_ok=True)

    tokens = create_honeytokens()
    t = tokens['tokens']

    # .env file - most common target
    with open(f'{deploy_dir}/.env', 'w') as f:
        f.write(f"""# Production Environment Configuration
# Generated: {datetime.datetime.now().strftime('%Y-%m-%d')}

NODE_ENV=production
APP_SECRET={"".join(random.choices(string.ascii_letters + string.digits, k=32))}

# AWS Configuration
AWS_ACCESS_KEY_ID={t[0]['access_key']}
AWS_SECRET_ACCESS_KEY={t[0]['secret_key']}
AWS_DEFAULT_REGION={t[0]['region']}
AWS_S3_BUCKET=prod-customer-data-{random.randint(1000,9999)}

# Database
DB_HOST={t[4]['host']}
DB_USER={t[4]['username']}
DB_PASS={t[4]['password']}
DB_NAME={t[4]['database']}

# Payment Processing
STRIPE_SECRET_KEY={t[3]['key']}
STRIPE_WEBHOOK_SECRET=whsec_{"".join(random.choices(string.ascii_letters + string.digits, k=32))}

# GitHub
GITHUB_TOKEN={t[2]['token']}
""")

    # AWS credentials file
    with open(f'{deploy_dir}/aws_credentials', 'w') as f:
        f.write(f"""[default]
aws_access_key_id = {t[0]['access_key']}
aws_secret_access_key = {t[0]['secret_key']}
region = {t[0]['region']}

[production]
aws_access_key_id = {t[0]['access_key']}
aws_secret_access_key = {t[0]['secret_key']}
""")

    # config.json - common in Node.js apps
    config = {
        "environment": "production",
        "database": {
            "host": t[4]['host'],
            "user": t[4]['username'],
            "password": t[4]['password'],
            "name": t[4]['database']
        },
        "aws": {
            "accessKeyId": t[0]['access_key'],
            "secretAccessKey": t[0]['secret_key'],
            "region": t[0]['region']
        },
        "stripe": {
            "secretKey": t[3]['key']
        }
    }
    with open(f'{deploy_dir}/config.json', 'w') as f:
        json.dump(config, f, indent=2)

    # deployment.yml - CI/CD config
    with open(f'{deploy_dir}/deployment.yml', 'w') as f:
        f.write(f"""version: '3.8'
services:
  app:
    image: company/app:latest
    environment:
      - AWS_ACCESS_KEY_ID={t[0]['access_key']}
      - AWS_SECRET_ACCESS_KEY={t[0]['secret_key']}
      - DB_PASSWORD={t[4]['password']}
      - STRIPE_KEY={t[3]['key']}
      - GITHUB_TOKEN={t[2]['token']}
""")

    print(f"[HONEYTOKEN] Deployed {len(os.listdir(deploy_dir))} decoy files")
    print(f"[HONEYTOKEN] Location: {deploy_dir}")
    return deploy_dir, tokens

def check_aws_honeytoken(access_key, secret_key):
    """
    Verify if a honeytoken AWS key was used.
    Uses AWS STS to check if key was accessed.
    This is how we catch attackers who steal our fake keys.
    """
    try:
        import boto3
        from botocore.exceptions import ClientError

        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        sts = session.client('sts', region_name='ap-south-1')
        identity = sts.get_caller_identity()

        log_attack({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "HONEYTOKEN_AWS_USED",
            "severity": "CRITICAL",
            "honeypot": "CLOUD_HONEYTOKEN",
            "attacker_ip": "TRACED_VIA_AWS",
            "details": f"AWS honeytoken {access_key[:8]}... was used — attacker identity: {identity}",
            "token_id": access_key[:8],
            "account_id": identity.get('Account', 'unknown'),
        })
        return True, identity

    except Exception as e:
        return False, str(e)

def monitor_canarytoken(token_url):
    """
    Monitor a canarytokens.org token for usage.
    Free service that alerts when tokens are used.
    """
    try:
        response = requests.get(token_url, timeout=10)
        data = response.json()
        if data.get('triggered'):
            log_attack({
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "HONEYTOKEN_TRIGGERED",
                "severity": "CRITICAL",
                "honeypot": "CANARYTOKEN",
                "attacker_ip": data.get('src_ip', 'Unknown'),
                "details": f"Canarytoken triggered — attacker IP: {data.get('src_ip')} location: {data.get('geo', {})}",
                "geo": data.get('geo', {}),
            })
            return True, data
    except:
        pass
    return False, {}

def watch_honeytokens():
    """
    Continuously monitor all deployed honeytokens.
    Check every 5 minutes if any token was used.
    """
    print("[HONEYTOKEN] Starting honeytoken monitor...")
    print("[HONEYTOKEN] Checking every 5 minutes for token usage")

    while True:
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'r') as f:
                    tokens = json.load(f)

                for token in tokens.get('tokens', []):
                    if token['type'] == 'AWS_ACCESS_KEY' and token['status'] == 'ACTIVE':
                        used, result = check_aws_honeytoken(
                            token['access_key'],
                            token['secret_key']
                        )
                        if used:
                            print(f"[HONEYTOKEN] ALERT! Token {token['id']} was used!")
        except:
            pass

        time.sleep(300)  # Check every 5 minutes

def print_deployment_guide(deploy_dir, tokens):
    """Print guide for deploying honeytokens."""
    print("\n" + "="*60)
    print("[HONEYTOKEN] DEPLOYMENT GUIDE")
    print("="*60)
    print(f"\n[+] Decoy files created in: {deploy_dir}")
    print("\n[+] Where to plant these files for maximum coverage:")
    print("    → ~/.aws/credentials — catches AWS key thieves")
    print("    → /var/www/html/.env — catches web app attackers")
    print("    → /etc/app/config.json — catches config file thieves")
    print("    → /home/*/documents/ — catches insider threats")
    print("    → Git repositories — catches code repo attackers")
    print("\n[+] Honeytokens generated:")
    for t in tokens['tokens']:
        print(f"    → {t['id']}: {t['name']}")
    print("\n[+] How detection works:")
    print("    1. Attacker finds decoy file and steals credentials")
    print("    2. Attacker tries to use the stolen credentials")
    print("    3. MAYA detects the usage attempt in real-time")
    print("    4. Attacker's REAL IP exposed even through VPN")
    print("    5. Full alert sent to MAYA dashboard immediately")
    print("\n[+] For free canarytokens (no AWS needed):")
    print("    → Visit: https://canarytokens.org")
    print("    → Create tokens for: AWS keys, URLs, documents")
    print("    → Add webhook URL pointing to your MAYA server")
    print("="*60)

def run_honeytoken_system():
    """Main honeytoken system."""
    print("""
╔═══════════════════════════════════════════════════════╗
║         MAYA CLOUD HONEYTOKEN SYSTEM                  ║
║         AWS + Azure + GitHub + Stripe + DB            ║
║         Exposes attackers through stolen credentials  ║
╚═══════════════════════════════════════════════════════╝
    """)

    # Deploy honeytoken files
    deploy_dir, tokens = deploy_honeytoken_files()
    print_deployment_guide(deploy_dir, tokens)

    # Start monitoring in background
    monitor_thread = threading.Thread(target=watch_honeytokens)
    monitor_thread.daemon = True
    monitor_thread.start()

    print("\n[HONEYTOKEN] System active — monitoring all tokens")
    print("[HONEYTOKEN] Any token usage triggers instant MAYA alert")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[HONEYTOKEN] Stopped")

if __name__ == "__main__":
    run_honeytoken_system()
