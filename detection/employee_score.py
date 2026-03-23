import json
import os
import datetime
import time
import threading

LOG_FILE = '/home/kali/maya-mvp/logs/attacks.log'
SCORE_FILE = '/home/kali/maya-mvp/logs/employee_scores.json'

def load_scores():
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, 'r') as f:
            return json.load(f)
    return {"employees": {}}

def save_scores(data):
    with open(SCORE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def log_event(data):
    print(f"[EMPLOYEE SCORE] {data['employee']} | {data['event']} | Score: {data['score']}")
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "EMPLOYEE_SECURITY_EVENT",
            "severity": "MEDIUM" if data['score'] < 50 else "LOW",
            "honeypot": "EMPLOYEE_MONITOR",
            "attacker_ip": "INTERNAL",
            "employee": data['employee'],
            "event": data['event'],
            "score": data['score'],
            "details": f"Employee {data['employee']} security score: {data['score']}/100"
        }) + '\n')

def calculate_score(employee):
    """
    Calculate security score 0-100.
    100 = perfect security behavior
    0   = serious security risk
    """
    score = 100
    events = employee.get('events', [])

    for event in events:
        etype = event.get('type', '')

        # Deductions for bad behavior
        if etype == 'CLICKED_PHISHING_LINK':
            score -= 30
        elif etype == 'USED_HONEYTOKEN':
            score -= 40
        elif etype == 'ACCESSED_HONEYPOT':
            score -= 35
        elif etype == 'WEAK_PASSWORD':
            score -= 20
        elif etype == 'SHARED_CREDENTIALS':
            score -= 25
        elif etype == 'ACCESSED_RESTRICTED':
            score -= 15
        elif etype == 'FAILED_LOGINS':
            score -= 10
        elif etype == 'ODD_HOURS_ACCESS':
            score -= 5

        # Bonuses for good behavior
        elif etype == 'COMPLETED_TRAINING':
            score += 10
        elif etype == 'REPORTED_SUSPICIOUS':
            score += 15
        elif etype == 'STRONG_PASSWORD':
            score += 5
        elif etype == 'MFA_ENABLED':
            score += 10

    return max(0, min(100, score))

def get_risk_level(score):
    if score >= 80:
        return "LOW", "Employee demonstrates good security awareness"
    elif score >= 60:
        return "MEDIUM", "Some security concerns — training recommended"
    elif score >= 40:
        return "HIGH", "Significant security risk — immediate training required"
    else:
        return "CRITICAL", "Serious security risk — account review needed"

def simulate_employee_events():
    """
    Simulate employee security events for testing.
    In production these come from real honeypot interactions.
    """
    db = load_scores()

    # Simulated employees with different behaviors
    employees = [
        {
            "id": "EMP001",
            "name": "Rajesh Kumar",
            "department": "Finance",
            "email": "rajesh@company.com",
            "events": [
                {"type": "MFA_ENABLED", "date": "2026-03-20"},
                {"type": "COMPLETED_TRAINING", "date": "2026-03-19"},
                {"type": "REPORTED_SUSPICIOUS", "date": "2026-03-18"},
                {"type": "STRONG_PASSWORD", "date": "2026-03-15"},
            ]
        },
        {
            "id": "EMP002",
            "name": "Priya Sharma",
            "department": "IT",
            "email": "priya@company.com",
            "events": [
                {"type": "COMPLETED_TRAINING", "date": "2026-03-20"},
                {"type": "MFA_ENABLED", "date": "2026-03-18"},
                {"type": "ODD_HOURS_ACCESS", "date": "2026-03-17"},
                {"type": "STRONG_PASSWORD", "date": "2026-03-15"},
            ]
        },
        {
            "id": "EMP003",
            "name": "Amit Patel",
            "department": "Sales",
            "email": "amit@company.com",
            "events": [
                {"type": "CLICKED_PHISHING_LINK", "date": "2026-03-21"},
                {"type": "WEAK_PASSWORD", "date": "2026-03-19"},
                {"type": "FAILED_LOGINS", "date": "2026-03-18"},
                {"type": "ODD_HOURS_ACCESS", "date": "2026-03-17"},
            ]
        },
        {
            "id": "EMP004",
            "name": "Sneha Reddy",
            "department": "HR",
            "email": "sneha@company.com",
            "events": [
                {"type": "USED_HONEYTOKEN", "date": "2026-03-22"},
                {"type": "ACCESSED_RESTRICTED", "date": "2026-03-20"},
                {"type": "SHARED_CREDENTIALS", "date": "2026-03-18"},
                {"type": "WEAK_PASSWORD", "date": "2026-03-15"},
            ]
        },
        {
            "id": "EMP005",
            "name": "Vikram Singh",
            "department": "Engineering",
            "email": "vikram@company.com",
            "events": [
                {"type": "MFA_ENABLED", "date": "2026-03-20"},
                {"type": "COMPLETED_TRAINING", "date": "2026-03-18"},
                {"type": "REPORTED_SUSPICIOUS", "date": "2026-03-17"},
                {"type": "STRONG_PASSWORD", "date": "2026-03-15"},
                {"type": "COMPLETED_TRAINING", "date": "2026-03-10"},
            ]
        },
    ]

    print("\n[EMPLOYEE SCORE] Calculating security scores...")
    print("=" * 60)
    print(f"{'Employee':<20} {'Dept':<12} {'Score':<8} {'Risk':<10} Assessment")
    print("=" * 60)

    for emp in employees:
        score = calculate_score(emp)
        risk, assessment = get_risk_level(score)

        db['employees'][emp['id']] = {
            "id": emp['id'],
            "name": emp['name'],
            "department": emp['department'],
            "email": emp['email'],
            "score": score,
            "risk": risk,
            "assessment": assessment,
            "events": emp['events'],
            "last_updated": datetime.datetime.now().isoformat()
        }

        # Color indicator
        indicator = "🟢" if risk == "LOW" else "🟡" if risk == "MEDIUM" else "🔴" if risk == "HIGH" else "⚫"
        print(f"{emp['name']:<20} {emp['department']:<12} {score:<8} {indicator} {risk:<8} {assessment}")

        log_event({
            "employee": emp['name'],
            "event": f"Score calculated: {score}/100",
            "score": score,
            "risk": risk
        })

    save_scores(db)
    print("=" * 60)

    # Summary
    employees_data = list(db['employees'].values())
    avg_score = sum(e['score'] for e in employees_data) / len(employees_data)
    critical = [e for e in employees_data if e['risk'] == 'CRITICAL']
    high = [e for e in employees_data if e['risk'] == 'HIGH']

    print(f"\n[SUMMARY]")
    print(f"  Average security score : {avg_score:.0f}/100")
    print(f"  Critical risk employees: {len(critical)}")
    print(f"  High risk employees    : {len(high)}")

    if critical:
        print(f"\n[ACTION REQUIRED]")
        for emp in critical:
            print(f"  → {emp['name']} ({emp['department']}) — Score: {emp['score']} — {emp['assessment']}")

    print(f"\n[EMPLOYEE SCORE] Scores saved to: {SCORE_FILE}")
    return db

def monitor_and_score():
    """Continuously monitor and update scores."""
    print("[EMPLOYEE SCORE] Employee Security Scoring System active")
    print("[EMPLOYEE SCORE] Monitoring honeytoken access and behavior")

    while True:
        try:
            # Read attacks log for employee-related events
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            # If honeytoken triggered by internal IP
                            # it could be an employee
                            if event.get('type') == 'HONEYTOKEN_TRIGGERED':
                                ip = event.get('attacker_ip', '')
                                if ip.startswith('192.168') or ip.startswith('10.'):
                                    print(f"[EMPLOYEE SCORE] Internal IP {ip} triggered honeytoken — possible insider threat")
                        except:
                            pass
        except:
            pass
        time.sleep(60)

def run_employee_scoring():
    print("""
╔═══════════════════════════════════════════════════════╗
║         MAYA EMPLOYEE SECURITY SCORING                ║
║         Know your insider threat risk                 ║
║         Score every employee 0-100                   ║
╚═══════════════════════════════════════════════════════╝
    """)

    # Run initial scoring
    simulate_employee_events()

    # Start continuous monitor
    monitor_thread = threading.Thread(target=monitor_and_score)
    monitor_thread.daemon = True
    monitor_thread.start()

    print("\n[EMPLOYEE SCORE] Continuous monitoring active")
    print("[EMPLOYEE SCORE] Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[EMPLOYEE SCORE] Stopped")

if __name__ == "__main__":
    run_employee_scoring()
