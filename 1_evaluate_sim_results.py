import numpy as np
import pandas as pd

from tqdm import tqdm # for progress bar
from AEB_SIM_LOOP import run_aeb_simulation  # Import the AEB simulation function


# check sim result to see if the simulator is working as expected


### STEP 4: Sanity Check. ###
# check the filters by simulating the configs that were filtered out and see if there are any collisions.
# Load the initial and filtered sample sets
df_filtered_samples = pd.read_csv('lhs_filtered_samples.csv')
df_initial_samples = pd.read_csv('lhs_initial_samples.csv')


filtered_set = set(map(tuple, df_filtered_samples.values))
initial_set = set(map(tuple, df_initial_samples.values))

# Get scenarios that were filtered out using set difference
filtered_out_set = initial_set - filtered_set

# Convert back to DataFrame with original column names
filtered_out_scenarios = pd.DataFrame(list(filtered_out_set), columns=df_initial_samples.columns)

# Save filtered-out scenarios
filtered_out_scenarios.to_csv('lhs_filtered_out_samples.csv', index=False)

print(f"\nSanity Check:")
print(f"Initial scenarios: {len(initial_set)}")
print(f"Filtered scenarios: {len(filtered_set)}")
print(f"Filtered-out scenarios: {len(filtered_out_set)}")

# Simulate filtered-out scenarios
filtered_out_results = []
for index, row in tqdm(filtered_out_scenarios.iterrows(), total=len(filtered_out_scenarios), desc="Simulating filtered-out scenarios"):
    config = {
        'ego_start_x': row['ego_start_x'],
        'ego_speed': row['ego_start_speed'] / 3.6,  # Convert from kph to m/s
        'target_start_x': row['target_start_x'],
        'target_speed': row['target_start_speed'] / 3.6,  # Convert from kph to m/s
        'target_decel': row['target_decel'],
        'target_decel_trigger': row['target_decel_trigger']
    }

    result = run_aeb_simulation(config)
    
    simulation_result = {
        'ego_start_x': round(config['ego_start_x'], 2),
        'ego_speed': round(config['ego_speed'] * 3.6, 2),
        'target_start_x': round(config['target_start_x'], 2),
        'target_speed': round(config['target_speed'] * 3.6, 2),
        'target_decel': round(config['target_decel'], 2),
        'target_decel_trigger': round(config['target_decel_trigger'], 2),
        'collision_occurred': result['collision_occurred'],
        'impact_speed': round(result['impact_speed'], 2),
        'aeb_triggered': result['aeb_triggered']
    }
    filtered_out_results.append(simulation_result)

# Convert results to DataFrame and save
df_filtered_out_results = pd.DataFrame(filtered_out_results)
df_filtered_out_results.to_csv('filtered_out_simulation_results.csv', index=False)

# Count collisions in filtered-out scenarios
num_collisions_filtered_out = df_filtered_out_results['collision_occurred'].sum()
total_filtered_out = len(df_filtered_out_results)

print("\nSanity Check Results:")
print(f"Number of collisions in filtered-out scenarios: {num_collisions_filtered_out} out of {total_filtered_out}")
if num_collisions_filtered_out > 0:
    print("WARNING: Some filtered-out scenarios resulted in collisions! Filters may need adjustment.")
else:
    print("Sanity check passed: No collisions in filtered-out scenarios.")

# After running simulations
aeb_triggers = df_filtered_out_results['aeb_triggered'].sum()
total_scenarios = len(df_filtered_out_results)

print(f"\nAEB Statistics:")
print(f"AEB triggered in {aeb_triggers} out of {total_scenarios} scenarios ({(aeb_triggers/total_scenarios)*100:.1f}%)")