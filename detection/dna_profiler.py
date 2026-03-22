import json
import os
import datetime
import hashlib
import math
from collections import defaultdict

LOG_FILE = '/home/kali/maya-mvp/logs/attacks.log'
DNA_FILE = '/home/kali/maya-mvp/logs/attacker_dna.json'

def load_dna_database():
    """Load existing attacker DNA profiles."""
    if os.path.exists(DNA_FILE):
        with open(DNA_FILE, 'r') as f:
            return json.load(f)
    return {"profiles": {}, "fingerprints": {}}

def save_dna_database(db):
    """Save attacker DNA database."""
    with open(DNA_FILE, 'w') as f:
        json.dump(db, f, indent=2)

def extract_behavioral_features(attacks_by_ip):
    """
    Extract behavioral DNA features from attack patterns.
    These features identify an attacker regardless of IP.
    """
    features = {}

    # Feature 1 — Attack type sequence
    attack_sequence = [a.get('type', '') for a in attacks_by_ip]
    features['attack_sequence'] = attack_sequence

    # Feature 2 — Time patterns (hour of day preference)
    hours = []
    for a in attacks_by_ip:
        try:
            ts = a.get('timestamp', '')
            if ts:
                hour = int(ts[11:13])
                hours.append(hour)
        except:
            pass
    features['preferred_hours'] = hours
    features['avg_hour'] = sum(hours) / len(hours) if hours else 0

    # Feature 3 — Attack speed (time between attempts)
    timestamps = []
    for a in attacks_by_ip:
        try:
            ts = datetime.datetime.fromisoformat(a.get('timestamp', ''))
            timestamps.append(ts)
        except:
            pass
    if len(timestamps) > 1:
        timestamps.sort()
        gaps = [(timestamps[i+1] - timestamps[i]).total_seconds()
                for i in range(len(timestamps)-1)]
        features['avg_gap_seconds'] = sum(gaps) / len(gaps)
        features['min_gap_seconds'] = min(gaps)
    else:
        features['avg_gap_seconds'] = 0
        features['min_gap_seconds'] = 0

    # Feature 4 — Tool signature from user agent
    user_agents = []
    for a in attacks_by_ip:
        ua = a.get('user_agent', '')
        if ua and ua != 'Unknown':
            user_agents.append(ua)
    features['user_agents'] = list(set(user_agents))

    # Feature 5 — Credential patterns
    usernames = []
    passwords = []
    for a in attacks_by_ip:
        if a.get('username_tried'):
            usernames.append(a['username_tried'])
        if a.get('password_tried'):
            passwords.append(a['password_tried'])
    features['usernames_tried'] = list(set(usernames))
    features['passwords_tried'] = list(set(passwords))
    features['unique_usernames'] = len(set(usernames))
    features['unique_passwords'] = len(set(passwords))

    # Feature 6 — Target preference
    honeypots_targeted = list(set(a.get('honeypot', '') for a in attacks_by_ip))
    features['honeypots_targeted'] = honeypots_targeted
    features['target_count'] = len(honeypots_targeted)

    # Feature 7 — Severity pattern
    severities = [a.get('severity', '') for a in attacks_by_ip]
    features['severity_distribution'] = {
        'CRITICAL': severities.count('CRITICAL'),
        'HIGH': severities.count('HIGH'),
        'MEDIUM': severities.count('MEDIUM'),
        'LOW': severities.count('LOW'),
    }

    return features

def generate_dna_hash(features):
    """
    Generate a unique DNA fingerprint from behavioral features.
    This hash identifies the attacker regardless of IP.
    """
    # Create a normalized feature string
    dna_components = []

    # Attack sequence pattern
    seq = '_'.join(features.get('attack_sequence', []))
    dna_components.append(f"seq:{seq}")

    # Time preference bucket (morning/afternoon/evening/night)
    avg_hour = features.get('avg_hour', 12)
    if avg_hour < 6:
        time_bucket = 'NIGHT'
    elif avg_hour < 12:
        time_bucket = 'MORNING'
    elif avg_hour < 18:
        time_bucket = 'AFTERNOON'
    else:
        time_bucket = 'EVENING'
    dna_components.append(f"time:{time_bucket}")

    # Speed bucket (slow/medium/fast/automated)
    avg_gap = features.get('avg_gap_seconds', 60)
    if avg_gap < 1:
        speed = 'AUTOMATED'
    elif avg_gap < 10:
        speed = 'FAST'
    elif avg_gap < 60:
        speed = 'MEDIUM'
    else:
        speed = 'SLOW'
    dna_components.append(f"speed:{speed}")

    # Username patterns
    usernames = sorted(features.get('usernames_tried', []))
    if usernames:
        dna_components.append(f"users:{','.join(usernames[:5])}")

    # Tool signature
    agents = features.get('user_agents', [])
    if agents:
        dna_components.append(f"tool:{agents[0][:30]}")

    dna_string = '|'.join(dna_components)
    dna_hash = hashlib.sha256(dna_string.encode()).hexdigest()[:16]
    return dna_hash, dna_string

def calculate_similarity(features1, features2):
    """
    Calculate behavioral similarity between two attack profiles.
    Returns 0-100% similarity score.
    """
    score = 0
    max_score = 0

    # Attack sequence similarity (weight: 30)
    max_score += 30
    seq1 = set(features1.get('attack_sequence', []))
    seq2 = set(features2.get('attack_sequence', []))
    if seq1 and seq2:
        intersection = len(seq1 & seq2)
        union = len(seq1 | seq2)
        score += 30 * (intersection / union) if union > 0 else 0

    # Time preference similarity (weight: 20)
    max_score += 20
    h1 = features1.get('avg_hour', 12)
    h2 = features2.get('avg_hour', 12)
    hour_diff = abs(h1 - h2)
    if hour_diff <= 2:
        score += 20
    elif hour_diff <= 4:
        score += 10

    # Speed similarity (weight: 20)
    max_score += 20
    g1 = features1.get('avg_gap_seconds', 60)
    g2 = features2.get('avg_gap_seconds', 60)
    if g1 > 0 and g2 > 0:
        ratio = min(g1, g2) / max(g1, g2)
        score += 20 * ratio

    # Username overlap (weight: 20)
    max_score += 20
    u1 = set(features1.get('usernames_tried', []))
    u2 = set(features2.get('usernames_tried', []))
    if u1 and u2:
        overlap = len(u1 & u2) / len(u1 | u2)
        score += 20 * overlap

    # Tool similarity (weight: 10)
    max_score += 10
    t1 = set(features1.get('user_agents', []))
    t2 = set(features2.get('user_agents', []))
    if t1 and t2 and t1 & t2:
        score += 10

    return (score / max_score * 100) if max_score > 0 else 0

def build_attacker_profile(ip, attacks):
    """Build complete attacker profile with DNA."""
    features = extract_behavioral_features(attacks)
    dna_hash, dna_string = generate_dna_hash(features)

    profile = {
        "ip": ip,
        "dna_hash": dna_hash,
        "dna_string": dna_string,
        "first_seen": attacks[0].get('timestamp', '') if attacks else '',
        "last_seen": attacks[-1].get('timestamp', '') if attacks else '',
        "total_attacks": len(attacks),
        "features": features,
        "severity": "CRITICAL" if any(a.get('severity') == 'CRITICAL' for a in attacks) else "HIGH",
        "classification": classify_attacker(features),
        "updated_at": datetime.datetime.now().isoformat(),
    }
    return profile

def classify_attacker(features):
    """
    Classify attacker type based on behavioral DNA.
    """
    avg_gap = features.get('avg_gap_seconds', 60)
    unique_users = features.get('unique_usernames', 0)
    targets = features.get('target_count', 1)
    severities = features.get('severity_distribution', {})

    # Nation state / APT — slow, methodical, multi-target
    if avg_gap > 30 and targets > 2 and severities.get('CRITICAL', 0) > 0:
        return "APT / NATION STATE"

    # Ransomware group — targets Windows, fast, credential focused
    attack_seq = features.get('attack_sequence', [])
    if any('WINDOWS' in a for a in attack_seq):
        if avg_gap < 5:
            return "RANSOMWARE GROUP"

    # Automated scanner — very fast, many usernames
    if avg_gap < 2 and unique_users > 10:
        return "AUTOMATED SCANNER"

    # Credential stuffing — many passwords, specific usernames
    if unique_users < 5 and features.get('unique_passwords', 0) > 20:
        return "CREDENTIAL STUFFING"

    # Script kiddie — random, fast, unsophisticated
    if avg_gap < 10 and targets < 2:
        return "SCRIPT KIDDIE"

    # Targeted attacker — slow, specific targets
    if avg_gap > 10 and targets > 1:
        return "TARGETED ATTACKER"

    return "UNKNOWN THREAT ACTOR"

def find_matching_profiles(new_profile, existing_profiles, threshold=70):
    """
    Find existing profiles that match the new attacker.
    This is how we recognize returning attackers with different IPs.
    """
    matches = []
    for ip, profile in existing_profiles.items():
        if ip == new_profile['ip']:
            continue
        similarity = calculate_similarity(
            new_profile['features'],
            profile['features']
        )
        if similarity >= threshold:
            matches.append({
                'ip': ip,
                'similarity': round(similarity, 1),
                'dna_hash': profile['dna_hash'],
                'classification': profile['classification'],
                'first_seen': profile['first_seen'],
                'total_attacks': profile['total_attacks'],
            })

    matches.sort(key=lambda x: x['similarity'], reverse=True)
    return matches

def analyze_all_attackers():
    """
    Main analysis function.
    Builds DNA profiles for all attackers in log.
    Identifies returning attackers across different IPs.
    """
    print("\n[DNA PROFILER] Analyzing all captured attacks...")

    # Load attacks
    attacks = []
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        attacks.append(json.loads(line))
                    except:
                        pass
    except:
        print("[DNA PROFILER] No attacks found in log")
        return

    if not attacks:
        print("[DNA PROFILER] No attacks to analyze")
        return

    # Group by IP
    by_ip = defaultdict(list)
    for attack in attacks:
        ip = attack.get('attacker_ip', 'unknown')
        by_ip[ip].append(attack)

    print(f"[DNA PROFILER] Found {len(attacks)} attacks from {len(by_ip)} unique IPs")

    # Load existing database
    db = load_dna_database()

    # Build profiles for each IP
    new_profiles = {}
    for ip, ip_attacks in by_ip.items():
        profile = build_attacker_profile(ip, ip_attacks)
        new_profiles[ip] = profile
        db['profiles'][ip] = profile
        db['fingerprints'][profile['dna_hash']] = ip

    print(f"\n{'='*60}")
    print(f"[DNA PROFILER] ATTACKER DNA PROFILES")
    print(f"{'='*60}")

    for ip, profile in new_profiles.items():
        print(f"\n[+] Attacker IP: {ip}")
        print(f"    DNA Hash: {profile['dna_hash']}")
        print(f"    Classification: {profile['classification']}")
        print(f"    Total Attacks: {profile['total_attacks']}")
        print(f"    Attack Types: {set(profile['features'].get('attack_sequence', []))}")
        print(f"    Attack Speed: {profile['features'].get('avg_gap_seconds', 0):.1f}s avg gap")
        print(f"    Time Preference: Hour {profile['features'].get('avg_hour', 0):.0f}:00")

        # Find matching profiles
        matches = find_matching_profiles(profile, new_profiles)
        if matches:
            print(f"    ⚠ SAME ATTACKER DETECTED across {len(matches)} other IPs:")
            for match in matches[:3]:
                print(f"      → IP {match['ip']} — {match['similarity']}% behavioral match")
                print(f"        Classification: {match['classification']}")

    save_dna_database(db)
    print(f"\n[DNA PROFILER] Database saved: {len(db['profiles'])} profiles")
    print(f"[DNA PROFILER] {len(db['fingerprints'])} unique DNA fingerprints")
    return db

def watch_and_profile():
    """
    Continuously profile new attackers as they appear.
    Runs as part of MAYA main system.
    """
    import time
    print("[DNA PROFILER] Attacker DNA Profiling System active")
    print("[DNA PROFILER] Building behavioral fingerprints for all attackers")

    last_count = 0
    while True:
        try:
            attacks = []
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            attacks.append(json.loads(line.strip()))
                        except:
                            pass

            if len(attacks) != last_count:
                last_count = len(attacks)
                analyze_all_attackers()

        except Exception as e:
            pass

        time.sleep(30)

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════╗
║         MAYA ATTACKER DNA PROFILING SYSTEM            ║
║         Recognizes attackers across different IPs     ║
║         Behavioral fingerprinting + Classification    ║
╚═══════════════════════════════════════════════════════╝
    """)
    analyze_all_attackers()
