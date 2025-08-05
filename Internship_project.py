import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from scipy.optimize import minimize

# Load your data
df = pd.read_csv('processed_airfoil_data.csv')

# Features and targets
X = df[['Camber', 'CamberLoc', 'Thickness']]
y_ld = df['L/D']
y_cd = df['CD']

# Fit Random Forest models
rf_ld = RandomForestRegressor(n_estimators=200, random_state=42).fit(X, y_ld)
rf_cd = RandomForestRegressor(n_estimators=200, random_state=42).fit(X, y_cd)

# Bounds based on your dataset
bounds = [
    (X['Camber'].min(), X['Camber'].max()),
    (X['CamberLoc'].min(), X['CamberLoc'].max()),
    (X['Thickness'].min(), X['Thickness'].max())
]

# Objective function: Maximize L/D
def objective(params):
    camber, camberloc, thickness = params
    input_features = np.array([[camber, camberloc, thickness]])
    predicted_ld = rf_ld.predict(input_features)[0]
    return -predicted_ld  # Maximize L/D

# Constraint function: CD ≤ 0.02
def cd_constraint(params):
    camber, camberloc, thickness = params
    input_features = np.array([[camber, camberloc, thickness]])
    predicted_cd = rf_cd.predict(input_features)[0]
    return 0.02 - predicted_cd

# Initial guess (center of bounds)
x0 = [(b[0] + b[1]) / 2 for b in bounds]

# Perform optimization using SLSQP
result = minimize(
    objective,
    x0,
    method='SLSQP',
    bounds=bounds,
    constraints={'type': 'ineq', 'fun': cd_constraint}
)

# Output optimization results
print("=== Optimization Result ===")
print(f"Optimal Camber: {result.x[0]:.4f}")
print(f"Optimal CamberLoc: {result.x[1]:.4f}")
print(f"Optimal Thickness: {result.x[2]:.4f}")
print(f"Predicted L/D at Optimum: {-result.fun:.4f}")
ld_opt, cd_opt = rf_ld.predict([result.x])[0], rf_cd.predict([result.x])[0]
print(f"Predicted CD at Optimum: {cd_opt:.5f}")
print("============================\n")

# Prediction function
def predict_ld_cd(camber, camberloc, thickness):
    input_features = np.array([[camber, camberloc, thickness]])
    predicted_ld = rf_ld.predict(input_features)[0]
    predicted_cd = rf_cd.predict(input_features)[0]
    return predicted_ld, predicted_cd

# User input loop
while True:
    print("\n=== Custom Prediction ===")
    try:
        camber_input = float(input("Enter Camber: "))
        camberloc_input = float(input("Enter CamberLoc: "))
        thickness_input = float(input("Enter Thickness: "))
    except ValueError:
        print("Invalid input. Please enter numeric values.")
        continue

    ld_pred, cd_pred = predict_ld_cd(camber_input, camberloc_input, thickness_input)
    print(f"Predicted L/D: {ld_pred:.4f}")
    print(f"Predicted CD: {cd_pred:.5f}")
    
    cont = input("Do you want to predict again? (y/n): ").strip().lower()
    if cont != 'y':
        print("Exiting prediction loop.")
        break

