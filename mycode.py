import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

#set the df as the pd . read file
df = pd.read_csv("vspaero_results.csv")
print(df.head())

# Features are X targets are Y


# === Define features (Reynolds removed) ===
features = [
    'Camber', 'Camber_Loc', 'Thickness',
    'Span', 'Root Chord', 'Tip Chord',
    'Angle of attack'
]
X = df[features]

y_cl = df["CL"]
y_cd = df["CD"]
y_ld = df["L/D"]

rf_ld = RandomForestRegressor(n_estimators=200, random_state=42).fit(X, y_ld)
rf_cd = RandomForestRegressor(n_estimators=200, random_state=42).fit(X, y_cd)
rf_cl = RandomForestRegressor(n_estimators=200,random_state = 42).fit(X,y_cl)

missions = {
    "STOL": {
           "min_ld": 10, "max_cd":0.045, "min_cl": 0.7, "max_alpha": 6,
        "span_min": 10, "span_max":18, "rootc_min": 2.5, "rootc_max" : 3.5,
        "tipc_min": 1.5, "tipc_max":2.5,
        "generate_synthetic": True
    },
    "Glider": {
        "min_ld": 25, "max_cd": 0.035, "min_cl": 0.7, "max_alpha": 6,
        "span_min": 15, "span_max":30, "rootc_min": 1.0, "rootc_max" : 2.5,
        "tipc_min": 0.3, "tipc_max":1.5,
        "generate_synthetic": True
    },
    "UAV_Loiter": {
        "min_ld": 15, "max_cd": 0.035, "min_cl": 0.6, "max_alpha": 6,
        "span_min": 2, "span_max":5, "rootc_min": 0.4, "rootc_max" : 0.8,
        "tipc_min": 0.2, "tipc_max":0.5,
        "generate_synthetic": True
    },
    "Trainer": {
        "min_ld": 12, "max_cd": 0.035, "min_cl": 0.6, "max_alpha": 6,
        "span_min": 8, "span_max":12, "rootc_min": 1.5, "rootc_max" : 2,
        "tipc_min": 0.8, "tipc_max":1.2,
        "generate_synthetic": False
    },
    "Utility": {
        "min_ld": 10, "max_cd": 0.045, "min_cl": 0.7, "max_alpha": 7,
        "span_min": 9, "span_max":12, "rootc_min": 2.5, "rootc_max" : 3.5,
        "tipc_min": 1.5, "tipc_max":2.5,
        "generate_synthetic": True
    }
}

def filter_and_rank_airfoil(mission_name,top =5, num_samples = 1000):
    mission = missions.get(mission_name)
    
    if mission is None:
        print("BADDDD")
        return
    
    if mission.get("generate_synthetic"):
        np.random.seed(42)
        new_data_frame = pd.DataFrame({
            "Camber"  : np.random.uniform(df["Camber"].min(),df["Camber"].max(),num_samples),
            "Camber_Loc": np.random.uniform(df['Camber_Loc'].min(), df['Camber_Loc'].max(), num_samples),
            'Thickness': np.random.uniform(df['Thickness'].min(), df['Thickness'].max(), num_samples),
            "Span" : np.random.uniform(mission.get("span_min"),mission.get("span_max"),num_samples),
            "Root Chord" : np.random.uniform(mission.get("rootc_min"),mission.get("rootc_max"),num_samples),
            "Tip Chord" : np.random.uniform(mission.get("tipc_min"),mission.get("tipc_max"),num_samples),
            "Angle of attack"  : np.random.uniform(0,mission.get("max_alpha"),num_samples)
        })
    
    else:
        # Use filtered real data
        new_data_frame = df.copy()

    # Predict performance
    new_data_frame['CL'] = rf_cl.predict(new_data_frame[features])
    new_data_frame['CD'] = rf_cd.predict(new_data_frame[features])
    new_data_frame['L/D'] = rf_ld.predict(new_data_frame[features])

    # Apply mission constraints
    filtered = new_data_frame[
        (new_data_frame['L/D'] >= mission['min_ld']) &
        (new_data_frame['CD'] <= mission['max_cd']) &
        (new_data_frame['CL'] >= mission['min_cl']) &
        (new_data_frame['Angle of attack'] <= mission['max_alpha']) &
        (new_data_frame['Span'] >= mission['span_min']) &
        (new_data_frame['Span'] <= mission['span_max']) &
        (new_data_frame['Root Chord'] >= mission['rootc_min']) &
        (new_data_frame['Root Chord'] <= mission['rootc_max']) &
        (new_data_frame['Tip Chord'] >= mission['tipc_min']) &
        (new_data_frame['Tip Chord'] <= mission['tipc_max'])
    ]

    if filtered.empty:
        print(f"No airfoils meet the {mission_name} constraints.")
        return

    ranked = filtered.sort_values(by='L/D', ascending=False)
    print(f"\n=== Top Airfoils for {mission_name} ===")
    print(ranked[features + ['CL', 'CD', 'L/D']].head())

    print("======================================")



while True:
    print("\n=== Mission-Based Selector ===")
    mission = input("Enter mission (STOL, Glider, UAV_Loiter, Trainer, Utility): ").strip()
    filter_and_rank_airfoil(mission)

    if input("Check another mission? (y/n): ").strip().lower() != 'y':
        break

 