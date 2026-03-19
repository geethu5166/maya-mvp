import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

print("[MAYA] Loading training data...")
df = pd.read_csv('data/training_data.csv')

# Features we use to detect attacks
FEATURES = [
    'duration', 'src_bytes', 'dst_bytes',
    'failed_logins', 'login_attempts',
    'num_connections', 'same_srv_rate',
    'diff_srv_rate', 'dst_host_count', 'packet_rate'
]

X = df[FEATURES]
y = df['label']

# Scale the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split into train and test
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

print("[MAYA] Training Random Forest classifier...")
rf_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    max_depth=10
)
rf_model.fit(X_train, y_train)

# Test accuracy
y_pred = rf_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"[MAYA] Model accuracy: {accuracy*100:.2f}%")
print("\n[MAYA] Detailed report:")
print(classification_report(y_test, y_pred,
      target_names=['Normal', 'Attack']))

print("\n[MAYA] Training Isolation Forest for unknown attacks...")
iso_model = IsolationForest(
    contamination=0.3,
    random_state=42,
    n_estimators=100
)
iso_model.fit(X_scaled)

# Save everything
os.makedirs('detection/models', exist_ok=True)
joblib.dump(rf_model, 'detection/models/rf_model.pkl')
joblib.dump(iso_model, 'detection/models/iso_model.pkl')
joblib.dump(scaler, 'detection/models/scaler.pkl')

print("\n[MAYA] Models saved successfully")
print("[MAYA] RF Model  → detection/models/rf_model.pkl")
print("[MAYA] ISO Model → detection/models/iso_model.pkl")
print("[MAYA] Scaler    → detection/models/scaler.pkl")
print("\n[MAYA] AI Brain is ready.")
