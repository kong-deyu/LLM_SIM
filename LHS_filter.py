# This script aims to allocate simulation resources intelligently by iteratively refining the pass/fail boundary, thus maximizing test coverage where it matters most.
# 1. Optimizes the allocation of simulation resources through the use of probablistic models
# 2. Maximize test coverage by exploring the entire parameter space with adaptive sampling techniques
# 3. Identifies the most critical scenarios by targeting the 'unknown regions' - boundaries of pass/fail within the parameter space


### Part 1: Initial Sampling of the Parameter Space ###
# this script is the first part of the process, it focuses on initial sampling of the parameter space using Latin Hypercube Sampling (LHS) and then filtering out unrealistic/unimportant scenarios before running them in simulation and outputting the results.

### INPUT:
# 1. scenario parameters
# 2. the realistic ranges and step sizes for each parameter

### OUTPUT:
# 1. initial sample set of 1000 scenarios (csv) - from LHS
# 2. filtered sample set of ~250 scenarios (csv) - after applying filters
# 3. simulation results (csv) - after running the filtered sample set through the simulation, then applying post-simulation filtering


# Parameters:
'''
ego_start_x = [1, 400, 5] m
ego_start_speed = [1, 150, 5] kph

target_start_x = [1, 400, 5] m 
target_start_speed = [0, 150, 5] kph
target_decel = [-8, 0, 0.5] m/s^2
target_decel_trigger = [0, 40, 1] m # based on distance to ego
'''
# These are all the parameters that could logically exist in the parameter space. However, not all combinations would result in salient, critical, realistic scenarios.

# step 1: use Latin Hypercube Sampling (LHS) to build a probabilistic model of the parameter space. LHS divides each parameter range into evenly spaced intervals and picks one from each interval, ensuring that every part of each parameter range is represented at least once. giving us a well distributed sample. LHS is selected because it is a good balance between coverage and computational efficiency. output: initial sample set

 
import numpy as np
import pandas as pd
from scipy.stats import qmc # Import qmc (Quasi-Monte Carlo) module from scipy.stats to use Latin Hypercube Sampling

from tqdm import tqdm # for progress bar
# from AEB_SIM_LOOP import run_aeb_simulation  # Import the AEB simulation function (AEB ONLY)
from Combined_SIM_LOOP import run_aeb_simulation  # Import the AEB simulation function (AEB + ACC)


# Parameter ranges based on your input
param_ranges = {
    'ego_start_x': (1, 200, 2),              # Range for ego starting position (meters)
    'ego_start_speed': (0, 150, 5),          # Range for ego starting speed (kph)
    'target_start_x': (30, 300, 5),          # Range for target starting position (meters)
    'target_start_speed': (0, 100, 5),       # Range for target starting speed (kph)
    'target_decel': (-6, 0, 0.5),           # Range for target deceleration (m/s²)
    'target_decel_trigger': (12, 40, 1),     # Range for target deceleration trigger distance (meters)
}

# Extract min and max values from parameter ranges for LHS
lower_bounds = []
upper_bounds = []

for range_tuple in param_ranges.values():
    lower_bounds.append(range_tuple[0])
    upper_bounds.append(range_tuple[1])

# set sample size based on computational resources
num_samples = 2000

# Function to create the Latin Hypercube Sampler and Generate Samples
def generate_lhs_samples(num_samples):
    # Number of parameters
    num_params = len(param_ranges)

    # Create Latin Hypercube Sampler
    sampler = qmc.LatinHypercube(d=num_params)

    # Generate samples in the unit cube
    unit_samples = sampler.random(n=num_samples)

    # Scale samples to actual parameter ranges
    scaled_samples = qmc.scale(unit_samples, lower_bounds, upper_bounds)

    # Round each column to the nearest valid step size
    for i, (param, (low, high, step)) in enumerate(param_ranges.items()):
        # Scale each sample to the nearest valid step size
        scaled_samples[:, i] = np.round((scaled_samples[:, i] - low) / step) * step + low

    # Convert to DataFrame 
    df_samples = pd.DataFrame(scaled_samples, columns=param_ranges.keys())

    # Save to CSV for inspection or future use
    df_samples.to_csv('lhs_initial_samples.csv', index=False)

    print(f"Initial sample set ({num_samples} samples) saved to 'lhs_initial_samples.csv'")
    print(f"Parameter ranges:")
    for param, (low, high, step) in param_ranges.items():
        print(f"  {param}: {low} to {high} (step size: {step})")
    
    return df_samples



### STEP 2: Filtering our LHS sample set to remove undesirable scenarios ###
# after obtaining the inital sample set, we apply filters to remove unrealistic scenarios or non-critical scenarios. output: filtered sample set

def main():
    # Read the initial LHS samples from CSV
    df_samples = generate_lhs_samples(num_samples)
    
    # Filter 1: remove scenarios where the ego vehicle is ahead of the target vehicle, these scenarios do not make sense.

    df_samples = df_samples[df_samples['ego_start_x'] <= df_samples['target_start_x']]


    # Filter 2: if the target speed is greater than the ego speed, then the ego will never catch up to trigger AEB UNLESS the target is also decelerating. So then we want to keep scenarios where either the ego speed is greater than or equal to the target speed, or the target vehicle is decelerating
    df_samples = df_samples[
        (df_samples['ego_start_speed'] >= df_samples['target_start_speed']) |
        (df_samples['target_decel'] < 0)
    ]

    # Filter 3: TTC based filter: remove scenarios where the initial TTC is greater than 20 seconds.
    # Calculate initial distance and relative speed
    df_samples['initial_gap'] = df_samples['target_start_x'] - df_samples['ego_start_x']
    # Convert speeds from kph to m/s for TTC calculation
    df_samples['relative_speed'] = (df_samples['ego_start_speed'] - df_samples['target_start_speed']) / 3.6

    # Avoid division by zero for relative speed
    df_samples['TTC'] = np.where(df_samples['relative_speed'] > 0,
                                 df_samples['initial_gap'] / df_samples['relative_speed'],
                                 np.inf)  # Set TTC to infinity if relative speed is <= 0

    # Apply the TTC filter (keep scenarios with TTC between 3 and 15 seconds)
    df_samples = df_samples[(df_samples['TTC'] >= 3) & (df_samples['TTC'] <= 20)]

    # Filter 4: remove scenarios where the relative speed is > 65 kph, we are trying to find scnearios where AEB barely avoids a collision
    df_samples = df_samples[df_samples['relative_speed'] <= 65]

    # Remove temporary columns
    df_samples = df_samples.drop(columns=['initial_gap', 'relative_speed', 'TTC'])





    # Print number of remaining samples after filtering
    # The result was ~200 out of 1k scenarios remaining, so the filters eliminate ~75-80% of the scenarios.
    # Save filtered samples to CSV for inspection or future use
    df_samples.to_csv('lhs_filtered_samples.csv', index=False)

    print(f"Filtered sample set ({len(df_samples)} samples) saved to 'lhs_filtered_samples.csv'")


    ### STEP 3:Simulate the filtered LHS sample set and obtain results ###
    # List to store results
    simulation_results = []

    # Loop through each configuration row with progress bar
    for index, row in tqdm(df_samples.iterrows(), total=len(df_samples), desc="Running simulations"):
        # Convert row to configuration dictionary
        config = {
            'ego_start_x': row['ego_start_x'],
            'ego_speed': row['ego_start_speed'] / 3.6,  # Convert from kph to m/s
            'target_start_x': row['target_start_x'],
            'target_speed': row['target_start_speed'] / 3.6,  # Convert from kph to m/s
            'target_decel': row['target_decel'],
            'target_decel_trigger': row['target_decel_trigger']
        }

        # Run simulation and capture result
        result = run_aeb_simulation(config)
        
        # Format the results before saving
        simulation_result = {
            'ego_start_x': round(config['ego_start_x'], 2),      # meters, 2 decimal
            'ego_speed': round(config['ego_speed'] * 3.6, 2),    # convert back to km/h, 2 decimal
            'target_start_x': round(config['target_start_x'], 2), # meters, 2 decimal
            'target_speed': round(config['target_speed'] * 3.6, 2), # convert back to km/h, 2 decimal
            'target_decel': round(config['target_decel'], 2),     # m/s², 2 decimal
            'target_decel_trigger': round(config['target_decel_trigger'], 2), # meters, 2 decimal
            'collision_occurred': result['collision_occurred'],    # boolean, no change needed
            'impact_speed': round(result['impact_speed'], 2),     # km/h, 2 decimal
            'aeb_triggered': result['aeb_triggered'],             # boolean, indicating if AEB was activated
            'speed_reduction': result['speed_reduction']          # km/h, 2 decimal
        }
        simulation_results.append(simulation_result)

    # Convert the results list to a DataFrame
    df_results = pd.DataFrame(simulation_results)


    # post simulation filtering for AEB scenarios that was on the borderline of passing and failing

    # Filter 1: filter out scenarios where the collision speed is > 20 kph
    df_results = df_results[
        (df_results['collision_occurred'] == False) |  # Keep non-collision scenarios
        ((df_results['collision_occurred'] == True) & (df_results['impact_speed'] < 20))  # Keep low-speed collisions
    ]

    # Filter 2: filter out scenarios where the maximum speed reduction is < 40 kph
    df_results = df_results[
        (df_results['speed_reduction'] >= 40) |  # Keep scenarios with significant speed reduction
        (df_results['collision_occurred'] == False)  # Keep all non-collision scenarios
    ]

    # Save results to a CSV file
    df_results.to_csv('simulation_results.csv', index=False)

    # Count collisions and print summary
    num_collisions = df_results['collision_occurred'].sum()
    total_scenarios = len(df_results)

    print(f"Filtered results to include only scenarios with collision speeds < 20 kph. {len(df_results)} scenarios remaining.")
    print(f"Batch simulation completed. Results saved to 'simulation_results.csv'")
    print(f"Number of collisions: {num_collisions} out of {total_scenarios} scenarios")
    print(f"Number of AEB activations: {df_results['aeb_triggered'].sum()} out of {total_scenarios} scenarios")

if __name__ == '__main__':
    main()







