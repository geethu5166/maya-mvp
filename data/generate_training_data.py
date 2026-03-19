import pandas as pd
import numpy as np
import json
import random

random.seed(42)
np.random.seed(42)

print("[MAYA] Generating training dataset...")

# Generate normal traffic samples
def normal_traffic(n=5000):
    data = []
    for _ in range(n):
        data.append({
            "duration": round(random.uniform(0.1, 300), 2),
            "src_bytes": random.randint(100, 50000),
            "dst_bytes": random.randint(100, 100000),
            "failed_logins": 0,
            "login_attempts": random.randint(1, 3),
            "num_connections": random.randint(1, 50),
            "same_srv_rate": round(random.uniform(0.7, 1.0), 2),
            "diff_srv_rate": round(random.uniform(0.0, 0.3), 2),
            "dst_host_count": random.randint(1, 10),
            "packet_rate": round(random.uniform(10, 500), 2),
            "label": 0  # 0 = normal
        })
    return data

# Generate SSH brute force samples
def ssh_bruteforce(n=1000):
    data = []
    for _ in range(n):
        data.append({
            "duration": round(random.uniform(0.01, 5), 2),
            "src_bytes": random.randint(50, 500),
            "dst_bytes": random.randint(50, 300),
            "failed_logins": random.randint(5, 50),
            "login_attempts": random.randint(10, 100),
            "num_connections": random.randint(50, 500),
            "same_srv_rate": round(random.uniform(0.8, 1.0), 2),
            "diff_srv_rate": round(random.uniform(0.0, 0.1), 2),
            "dst_host_count": random.randint(1, 3),
            "packet_rate": round(random.uniform(100, 2000), 2),
            "label": 1  # 1 = attack
        })
    return data

# Generate port scan samples
def port_scan(n=1000):
    data = []
    for _ in range(n):
        data.append({
            "duration": round(random.uniform(0.001, 1), 3),
            "src_bytes": random.randint(20, 100),
            "dst_bytes": random.randint(0, 50),
            "failed_logins": 0,
            "login_attempts": 0,
            "num_connections": random.randint(100, 1000),
            "same_srv_rate": round(random.uniform(0.0, 0.3), 2),
            "diff_srv_rate": round(random.uniform(0.7, 1.0), 2),
            "dst_host_count": random.randint(50, 255),
            "packet_rate": round(random.uniform(500, 5000), 2),
            "label": 1
        })
    return data

# Generate credential stuffing samples
def credential_stuffing(n=1000):
    data = []
    for _ in range(n):
        data.append({
            "duration": round(random.uniform(0.5, 10), 2),
            "src_bytes": random.randint(200, 2000),
            "dst_bytes": random.randint(100, 1000),
            "failed_logins": random.randint(3, 30),
            "login_attempts": random.randint(5, 50),
            "num_connections": random.randint(20, 200),
            "same_srv_rate": round(random.uniform(0.9, 1.0), 2),
            "diff_srv_rate": round(random.uniform(0.0, 0.1), 2),
            "dst_host_count": random.randint(1, 5),
            "packet_rate": round(random.uniform(50, 500), 2),
            "label": 1
        })
    return data

# Generate web scanning samples
def web_scan(n=1000):
    data = []
    for _ in range(n):
        data.append({
            "duration": round(random.uniform(0.01, 2), 3),
            "src_bytes": random.randint(100, 500),
            "dst_bytes": random.randint(0, 200),
            "failed_logins": 0,
            "login_attempts": 0,
            "num_connections": random.randint(50, 500),
            "same_srv_rate": round(random.uniform(0.1, 0.5), 2),
            "diff_srv_rate": round(random.uniform(0.5, 1.0), 2),
            "dst_host_count": random.randint(10, 100),
            "packet_rate": round(random.uniform(200, 3000), 2),
            "label": 1
        })
    return data

# Combine all data
all_data = (
    normal_traffic(5000) +
    ssh_bruteforce(1000) +
    port_scan(1000) +
    credential_stuffing(1000) +
    web_scan(1000)
)

# Shuffle
random.shuffle(all_data)

# Save as CSV
df = pd.DataFrame(all_data)
df.to_csv('data/training_data.csv', index=False)

print(f"[MAYA] Generated {len(df)} samples")
print(f"[MAYA] Normal traffic: {len(df[df.label==0])}")
print(f"[MAYA] Attack traffic: {len(df[df.label==1])}")
print(f"[MAYA] Saved to data/training_data.csv")
