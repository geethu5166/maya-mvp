import subprocess
import requests
import json
import datetime
import os
import time
import threading

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'attacks.log')
AGENT_LOG = os.path.join(os.path.dirname(__file__), '..', 'logs', 'agent_actions.log')
BLOCKED_IPS = os.path.join(os.path.dirname(__file__), '..', 'logs', 'blocked_ips.txt')

def think(attack_context):
    """
    Send attack to Mistral brain.
    Get back a decision in structured format.
    """
    prompt = f"""You are MAYA, an autonomous cybersecurity AI agent protecting an Indian enterprise network.

ATTACK DETECTED:
- Type: {attack_context.get('type')}
- Attacker IP: {attack_context.get('attacker_ip')}
- Severity: {attack_context.get('severity')}
- Honeypot: {attack_context.get('honeypot')}
- Timestamp: {attack_context.get('timestamp')}
- Details: {attack_context.get('credentials', attack_context.get('path', 'N/A'))}

Analyze this attack and respond ONLY with this JSON format:
{{
  "threat_level": "CRITICAL/HIGH/MEDIUM/LOW",
  "attack_classification": "what type of attack this is",
  "attacker_intent": "what the attacker is trying to do",
  "immediate_actions": ["action1", "action2"],
  "block_ip": true or false,
  "alert_team": true or false,
  "risk_score": 0-100,
  "explanation": "brief explanation in plain English",
  "predicted_next_move": "what attacker will try next"
}}"""

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'mistral',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,
                    'num_predict': 500
                }
            },
            timeout=30
        )
        
        result = response.json().get('response', '')
        
        # Extract JSON from response
        start = result.find('{')
        end = result.rfind('}') + 1
        if start != -1 and end != 0:
            decision = json.loads(result[start:end])
            return decision
    except Exception as e:
        pass
    
    # Fallback decision if Mistral fails
    return {
        "threat_level": attack_context.get('severity', 'HIGH'),
        "attack_classification": attack_context.get('type'),
        "attacker_intent": "Unknown — manual review needed",
        "immediate_actions": ["Block IP", "Alert team"],
        "block_ip": True,
        "alert_team": True,
        "risk_score": 75,
        "explanation": "Automated fallback decision — Mistral unavailable",
        "predicted_next_move": "Further reconnaissance expected"
    }

def block_ip(ip):
    """Block attacker IP using iptables."""
    if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.'):
        return False, "Local IP skipped"
    
    blocked = set()
    if os.path.exists(BLOCKED_IPS):
        with open(BLOCKED_IPS, 'r') as f:
            blocked = set(f.read().splitlines())
    
    if ip in blocked:
        return False, "Already blocked"
    
    try:
        subprocess.run(
            ['sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'],
            capture_output=True, timeout=5
        )
        with open(BLOCKED_IPS, 'a') as f:
            f.write(ip + '\n')
        return True, f"IP {ip} blocked"
    except Exception as e:
        return False, str(e)

def isolate_threat(ip):
    """
    Full threat isolation.
    Block all traffic from attacker IP.
    """
    # Block incoming
    subprocess.run(['sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'],
                  capture_output=True)
    # Block outgoing to attacker
    subprocess.run(['sudo', 'iptables', '-A', 'OUTPUT', '-d', ip, '-j', 'DROP'],
                  capture_output=True)
    # Block forwarding
    subprocess.run(['sudo', 'iptables', '-A', 'FORWARD', '-s', ip, '-j', 'DROP'],
                  capture_output=True)

def log_action(action):
    """Log every action MAYA takes."""
    with open(AGENT_LOG, 'a') as f:
        f.write(json.dumps(action) + '\n')
    print(f"[MAYA AGENT] {action['timestamp']} | {action['action']} | {action['details']}")

def execute_decision(attack, decision):
    """
    Execute whatever Mistral decided.
    This is where thinking becomes action.
    """
    timestamp = datetime.datetime.now().isoformat()
    ip = attack.get('attacker_ip', '')

    print(f"\n{'='*60}")
    print(f"[MAYA BRAIN] Mistral Analysis Complete")
    print(f"{'='*60}")
    print(f"Threat Level    : {decision.get('threat_level')}")
    print(f"Classification  : {decision.get('attack_classification')}")
    print(f"Attacker Intent : {decision.get('attacker_intent')}")
    print(f"Risk Score      : {decision.get('risk_score')}/100")
    print(f"Explanation     : {decision.get('explanation')}")
    print(f"Predicted Next  : {decision.get('predicted_next_move')}")
    print(f"Actions         : {', '.join(decision.get('immediate_actions', []))}")
    print(f"{'='*60}")

    # Execute actions based on Mistral's decision
    actions_taken = []

    # Block IP if decided
    if decision.get('block_ip', False):
        blocked, msg = block_ip(ip)
        log_action({
            "timestamp": timestamp,
            "action": "IP_BLOCKED" if blocked else "IP_BLOCK_SKIPPED",
            "details": msg,
            "attacker_ip": ip,
            "decided_by": "Mistral AI"
        })
        actions_taken.append(f"IP {'blocked' if blocked else 'skip'}: {msg}")

    # Full isolation for critical threats
    if decision.get('threat_level') == 'CRITICAL':
        isolate_threat(ip)
        log_action({
            "timestamp": timestamp,
            "action": "FULL_ISOLATION",
            "details": f"All traffic from {ip} blocked — CRITICAL threat",
            "attacker_ip": ip,
            "decided_by": "Mistral AI"
        })
        actions_taken.append("Full network isolation applied")

    # Log complete agent decision
    log_action({
        "timestamp": timestamp,
        "action": "AGENT_DECISION_EXECUTED",
        "details": f"Risk: {decision.get('risk_score')}/100 | Actions: {len(actions_taken)}",
        "attacker_ip": ip,
        "decided_by": "Mistral AI",
        "full_decision": decision,
        "actions_taken": actions_taken
    })

    print(f"[MAYA AGENT] {len(actions_taken)} actions executed autonomously")
    print(f"[MAYA AGENT] No human intervention required")

def process_attack(attack):
    """
    Full pipeline:
    Detect → Think → Decide → Act
    """
    print(f"\n[MAYA AGENT] New attack detected — sending to Mistral brain...")
    print(f"[MAYA AGENT] Attack: {attack.get('type')} from {attack.get('attacker_ip')}")
    print(f"[MAYA AGENT] Mistral is analyzing...")

    # Think
    decision = think(attack)

    # Act
    execute_decision(attack, decision)

def run_maya_agent():
    """
    MAYA Autonomous Agent — runs 24/7.
    Every attack → Mistral thinks → MAYA acts.
    """
    print("""
╔═══════════════════════════════════════════════════════╗
║         MAYA AUTONOMOUS AI AGENT                      ║
║         Powered by Mistral 7B                         ║
║         Detect → Think → Decide → Act                 ║
╚═══════════════════════════════════════════════════════╝
    """)
    print("[MAYA AGENT] Brain: Mistral 7B (Local — Private — Free)")
    print("[MAYA AGENT] Mode: Fully Autonomous")
    print("[MAYA AGENT] Watching for attacks 24/7...")
    print("-" * 60)

    last_position = 0
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
                        # Process each attack in separate thread
                        # So multiple attacks handled simultaneously
                        t = threading.Thread(
                            target=process_attack,
                            args=(attack,)
                        )
                        t.daemon = True
                        t.start()

        except Exception as e:
            pass

        time.sleep(1)

if __name__ == "__main__":
    # Test on last attack in log
    print("[MAYA AGENT] Testing AI brain on existing attacks...")
    try:
        with open(LOG_FILE, 'r') as f:
            attacks = [json.loads(l.strip()) for l in f if l.strip()]
        if attacks:
            process_attack(attacks[-1])
        else:
            print("[MAYA AGENT] No attacks yet. Start honeypots first.")
    except Exception as e:
        print(f"[MAYA AGENT] Error: {e}")
