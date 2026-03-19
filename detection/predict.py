import joblib
import json
import numpy as np
import os

# Load the trained models
BASE = os.path.dirname(__file__)
rf_model = joblib.load(os.path.join(BASE, 'models/rf_model.pkl'))
iso_model = joblib.load(os.path.join(BASE, 'models/iso_model.pkl'))
scaler = joblib.load(os.path.join(BASE, 'models/scaler.pkl'))

def extract_features(attack_log):
    """
    Convert a raw honeypot log entry into
    features the AI model understands.
    """
    attack_type = attack_log.get('type', '')
    severity = attack_log.get('severity', 'LOW')

    # Map severity to failed logins
    severity_map = {'LOW': 0, 'MEDIUM': 2, 'HIGH': 10, 'CRITICAL': 30}
    failed = severity_map.get(severity, 0)

    # Map attack types to feature patterns
    if attack_type == 'SSH_BRUTE_FORCE':
        return [
            2.0,      # duration
            200,      # src_bytes
            150,      # dst_bytes
            failed,   # failed_logins
            50,       # login_attempts
            200,      # num_connections
            0.95,     # same_srv_rate
            0.05,     # diff_srv_rate
            2,        # dst_host_count
            800.0     # packet_rate
        ]
    elif attack_type == 'WEB_CREDENTIAL_HARVEST':
        return [
            3.0, 800, 400, failed,
            20, 80, 0.95, 0.05, 3, 300.0
        ]
    elif attack_type == 'WEB_SCAN':
        return [
            0.5, 150, 50, 0,
            0, 300, 0.2, 0.8, 80, 2000.0
        ]
    elif attack_type == 'WEB_RECON':
        return [
            1.0, 300, 100, 0,
            0, 100, 0.3, 0.7, 30, 500.0
        ]
    else:
        return [
            1.0, 500, 200, failed,
            5, 50, 0.5, 0.5, 10, 200.0
        ]

def analyze_attack(attack_log):
    """
    Run AI analysis on a single attack log.
    Returns enriched log with AI verdict.
    """
    features = extract_features(attack_log)
    features_scaled = scaler.transform([features])

    # Random Forest prediction
    rf_prediction = rf_model.predict(features_scaled)[0]
    rf_probability = rf_model.predict_proba(features_scaled)[0]
    attack_confidence = round(rf_probability[1] * 100, 1)

    # Isolation Forest prediction
    iso_prediction = iso_model.predict(features_scaled)[0]
    is_anomaly = iso_prediction == -1

    # Final verdict
    is_attack = rf_prediction == 1 or is_anomaly

    # Threat classification
    if attack_confidence >= 90:
        threat_level = "CONFIRMED ATTACK"
        action = "ISOLATE AND BLOCK"
    elif attack_confidence >= 70:
        threat_level = "LIKELY ATTACK"
        action = "MONITOR CLOSELY"
    elif attack_confidence >= 50:
        threat_level = "SUSPICIOUS"
        action = "INVESTIGATE"
    else:
        threat_level = "NORMAL"
        action = "NO ACTION"

    return {
        **attack_log,
        "ai_analysis": {
            "is_attack": bool(is_attack),
            "confidence": attack_confidence,
            "threat_level": threat_level,
            "recommended_action": action,
            "anomaly_detected": bool(is_anomaly),
            "model": "RandomForest + IsolationForest"
        }
    }

def analyze_log_file(log_file):
    """
    Analyze all attacks in the log file.
    """
    results = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    attack = json.loads(line)
                    result = analyze_attack(attack)
                    results.append(result)
    except Exception as e:
        print(f"Error: {e}")
    return results

if __name__ == '__main__':
    LOG_FILE = os.path.join(BASE, '..', 'logs', 'attacks.log')
    print("[MAYA] Running AI analysis on captured attacks...")
    print("-" * 60)
    results = analyze_log_file(LOG_FILE)
    for r in results:
        ai = r['ai_analysis']
        print(f"Type: {r['type']}")
        print(f"IP: {r['attacker_ip']}")
        print(f"AI Verdict: {ai['threat_level']}")
        print(f"Confidence: {ai['confidence']}%")
        print(f"Action: {ai['recommended_action']}")
        print("-" * 60)
