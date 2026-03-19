import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import joblib
import os

print("[MAYA] Loading datasets...")

# Load CICIDS sample from middle of file (more variety)
df1 = pd.read_csv('data/cicids2018.csv',
                  low_memory=False,
                  skiprows=range(1, 200000),
                  nrows=30000)
df1.columns = df1.columns.str.strip()

# Load our generated India-specific data
df2 = pd.read_csv('data/training_data.csv')

# Load NSL-KDD
col_names = ['duration','protocol','service','flag',
             'src_bytes','dst_bytes','land','wrong_fragment',
             'urgent','hot','failed_logins','logged_in',
             'num_compromised','root_shell','su_attempted',
             'num_root','num_file_creations','num_shells',
             'num_access_files','num_outbound_cmds',
             'is_host_login','is_guest_login','count',
             'srv_count','serror_rate','srv_serror_rate',
             'rerror_rate','srv_rerror_rate','same_srv_rate',
             'diff_srv_rate','srv_diff_host_rate',
             'dst_host_count','dst_host_srv_count',
             'dst_host_same_srv_rate','dst_host_diff_srv_rate',
             'dst_host_same_src_port_rate',
             'dst_host_srv_diff_host_rate','dst_host_serror_rate',
             'dst_host_srv_serror_rate','dst_host_rerror_rate',
             'dst_host_srv_rerror_rate','label','difficulty']

df3 = pd.read_csv('data/nslkdd_train.txt',
                  names=col_names,
                  low_memory=False)

print(f"[MAYA] CICIDS records: {len(df1)}")
print(f"[MAYA] India-specific records: {len(df2)}")
print(f"[MAYA] NSL-KDD records: {len(df3)}")

# Process CICIDS
label_col = [c for c in df1.columns if 'label' in c.lower()][0]
df1['attack'] = (df1[label_col].str.strip() != 'BENIGN').astype(int)
cicids_features = ['Dst Port','Protocol','Flow Duration',
                   'Tot Fwd Pkts','Tot Bwd Pkts',
                   'TotLen Fwd Pkts','TotLen Bwd Pkts']
df1_clean = df1[cicids_features].replace([np.inf,-np.inf], np.nan).fillna(0)
df1_clean.columns = ['f1','f2','f3','f4','f5','f6','f7']
df1_clean['label'] = df1['attack'].values

# Process NSL-KDD
df3['attack'] = (df3['label'] != 'normal').astype(int)
nsl_features = ['duration','src_bytes','dst_bytes',
                'failed_logins','count','same_srv_rate',
                'diff_srv_rate']
df3_num = df3[nsl_features].apply(pd.to_numeric, errors='coerce').fillna(0)
df3_num.columns = ['f1','f2','f3','f4','f5','f6','f7']
df3_num['label'] = df3['attack'].values

# Process India-specific data
india_features = ['src_bytes','dst_bytes','failed_logins',
                  'login_attempts','num_connections',
                  'same_srv_rate','diff_srv_rate']
df2_clean = df2[india_features].fillna(0)
df2_clean.columns = ['f1','f2','f3','f4','f5','f6','f7']
df2_clean['label'] = df2['label'].values

# Combine all three datasets
combined = pd.concat([df1_clean, df3_num, df2_clean], 
                     ignore_index=True)
combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\n[MAYA] Combined dataset: {len(combined)} records")
print(f"[MAYA] Normal traffic: {(combined.label==0).sum()}")
print(f"[MAYA] Attack traffic: {(combined.label==1).sum()}")

FEATURES = ['f1','f2','f3','f4','f5','f6','f7']
X = combined[FEATURES].replace([np.inf,-np.inf], np.nan).fillna(0)
y = combined['label']

# Scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

print(f"\n[MAYA] Training on {len(X_train)} samples...")
print("[MAYA] Using: CICIDS2018 + NSL-KDD + India-specific data")

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1,
    max_depth=15
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\n[MAYA] Final Accuracy: {acc*100:.2f}%")
print(f"[MAYA] Trained on 3 datasets:")
print(f"       - CICIDS2018 (Western enterprise attacks)")
print(f"       - NSL-KDD (Classic attack patterns)")
print(f"       - India-specific honeypot data")

# Save
os.makedirs('detection/models', exist_ok=True)
joblib.dump(model, 'detection/models/rf_model_real.pkl')
joblib.dump(scaler, 'detection/models/scaler_real.pkl')
joblib.dump(FEATURES, 'detection/models/features_real.pkl')

print("\n[MAYA] AI Brain fully trained and saved.")
print("[MAYA] Ready to detect attacks in real time.")
