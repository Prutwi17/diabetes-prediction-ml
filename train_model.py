import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import pickle

# Load dataset
df = pd.read_csv('diabetes_prediction_3class.csv')

# Show available columns
print("Available columns:", df.columns.tolist())

# Encode categorical features
df['gender'] = df['gender'].map({'Male': 1, 'Female': 0})
smoking_map = {
    'never': 0,
    'former': 1,
    'current': 2,
    'not current': 3,
    'ever': 4,
    'No Info': 5
}
df['smoking_history'] = df['smoking_history'].map(smoking_map)

# Drop rows with missing or invalid values
df = df.dropna()

# Feature selection
features = ['gender', 'age', 'hypertension', 'heart_disease', 'smoking_history',
            'bmi', 'HbA1c_level', 'blood_glucose_level']
X = df[features]
y = df['diabetes_status']

print("✅ Features shape:", X.shape)
print("✅ Target shape:", y.shape)
print("🎯 Classes in target:", y.unique())

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
print("\n🔍 Model Evaluation")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))

# Save the trained model
with open('model.pkl', 'wb') as model_file:
    pickle.dump(model, model_file)

print("\n✅ Model trained and saved to 'model.pkl'")
