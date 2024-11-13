
### Part 2:Train a Probabilistic Model Using the Results ###
# INPUT:
# 1. simulation results (csv) - after running the filtered sample set through the simulation

### OUTPUT:



import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C

# Step 1: Load and Prepare Initial Dataset
# Load the results data from csv file
df_results = pd.read_csv('training_data.csv')

# Convert collision_occurred to binary (1 = collision, 0 = no collision)
df_results['collision_occurred'] = df_results['collision_occurred'].astype(int)

# Define features (X) and target variable (y)
# X contains the relevant parameters from the AEB simulation (e.g., starting positions, speeds, etc.)
X = df_results[['ego_start_x', 'ego_speed', 'target_start_x', 'target_speed', 'target_decel', 'target_decel_trigger']]
# y is the target variable indicating collision occurrence (1 for collision, 0 for no collision)
y = df_results['collision_occurred']


# Step 2: Train the Initial Gaussian Process Model
# Define the kernel for the Gaussian Process (combining Constant and RBF kernels)
# Constant kernel scales the output, while RBF controls smoothness
kernel = C(1.0) * RBF(length_scale=5.0)

# Initialize the Gaussian Process Classifier with the defined kernel
# Setting random_state ensures reproducibility
gp_model = GaussianProcessClassifier(kernel=kernel, random_state=42)

# Train the model on the initial dataset (the 99 filtered scenarios)
gp_model.fit(X, y)

# Step 3: Generate new configuration dataset using Latin Hypercube Sampling (LHS)
from scipy.stats import qmc
from LHS_filter import generate_lhs_samples

# Generate new configurations using the generate_lhs_samples function from LHS_filter.py
new_configs = generate_lhs_samples(1000)
new_configs = new_configs.rename(columns={
    'ego_start_speed': 'ego_speed',
    'target_start_speed': 'target_speed'
})

print("\nStep 1: Predicting collision probabilities using GP model...")
collision_probs = gp_model.predict_proba(new_configs)[:, 1]  # Probability of collision

print("\nStep 2: Calculating uncertainty scores...")
uncertainty = np.abs(collision_probs - 0.5)

print("\nStep 3: Filtering scenarios with probability between 0.4-0.5...")
# Create a mask for scenarios with probability between 0.4 and 0.5
prob_mask = (collision_probs >= 0.35) & (collision_probs <= 0.5)
filtered_indices = np.where(prob_mask)[0]

# Filter configurations, probabilities and uncertainty scores
filtered_configs = new_configs.iloc[filtered_indices]
filtered_probs = collision_probs[filtered_indices]
filtered_uncertainty = uncertainty[filtered_indices]

print("\nStep 4: Selecting top 10 scenarios with highest uncertainty...")
# Get indices of top 10 highest uncertainty scenarios from the filtered set
top_10_indices = np.argsort(filtered_uncertainty)[-10:][::-1]  # Sort in descending order
high_uncertainty_configs = filtered_configs.iloc[top_10_indices]
selected_probs = filtered_probs[top_10_indices]
selected_uncertainty = filtered_uncertainty[top_10_indices]

print("\nStep 5: Saving high uncertainty scenarios to CSV...")
high_uncertainty_configs.to_csv('CSV/high_uncertainty_scenarios.csv', index=False)
print("High uncertainty scenarios saved to 'high_uncertainty_scenarios.csv'")

print("\nTop 10 scenarios with highest uncertainty (from probability range 0.4-0.6):")
print("==========================================")
for i, (idx, row) in enumerate(high_uncertainty_configs.iterrows()):
    print(f"Collision Probability: {selected_probs[i]:.3f}")
    print(f"Uncertainty Score: {selected_uncertainty[i]:.3f}")
    print(f"Parameters: {row['ego_start_x']:.1f},{row['ego_speed']:.1f},{row['target_start_x']:.1f},{row['target_speed']:.1f},{row['target_decel']:.1f},{row['target_decel_trigger']:.1f}")
    print()

def plot_gp_2D(gp_model, X, feature1_idx, feature2_idx, feature_names=None):
    """
    Create a 2D visualization of the GP model predictions
    
    Args:
        gp_model: Trained GaussianProcessClassifier
        X: Original training data
        feature1_idx: Index of first feature to plot
        feature2_idx: Index of second feature to plot
        feature_names: List of feature names
    """
    # Use feature names if provided, otherwise use indices
    if feature_names is None:
        feature_names = [f'Feature {i}' for i in range(X.shape[1])]
    
    # Create mesh grid
    x1_min, x1_max = X[:, feature1_idx].min() - 1, X[:, feature1_idx].max() + 1
    x2_min, x2_max = X[:, feature2_idx].min() - 1, X[:, feature2_idx].max() + 1
    xx1, xx2 = np.meshgrid(np.linspace(x1_min, x1_max, 100),
                          np.linspace(x2_min, x2_max, 100))
    
    # Prepare query points
    X_query = np.zeros((xx1.ravel().shape[0], X.shape[1]))
    # Use mean values for non-plotted dimensions
    for i in range(X.shape[1]):
        if i not in [feature1_idx, feature2_idx]:
            X_query[:, i] = X[:, i].mean()
    X_query[:, feature1_idx] = xx1.ravel()
    X_query[:, feature2_idx] = xx2.ravel()
    
    # Get predictions
    Z = gp_model.predict_proba(X_query)[:, 1]
    Z = Z.reshape(xx1.shape)
    
    # Create plot
    plt.figure(figsize=(10, 8))
    plt.contourf(xx1, xx2, Z, levels=np.linspace(0, 1, 11), cmap=cm.RdYlBu)
    plt.colorbar(label='Collision Probability')
    
    # Plot training points
    plt.scatter(X[:, feature1_idx], X[:, feature2_idx], c='black', marker='x', label='Training Points')
    
    plt.xlabel(feature_names[feature1_idx])
    plt.ylabel(feature_names[feature2_idx])
    plt.title(f'GP Model Predictions: {feature_names[feature1_idx]} vs {feature_names[feature2_idx]}')
    plt.legend()
    plt.show()

# After training your GP model, create visualizations for different feature pairs
feature_names = ['Ego Start X', 'Ego Speed', 'Target Start X', 'Target Speed', 
                'Target Decel', 'Target Decel Trigger']

# Plot ego speed vs target speed
plot_gp_2D(gp_model, X.values, 1, 3, feature_names)

# Plot initial distance vs target deceleration
plot_gp_2D(gp_model, X.values, 2, 4, feature_names)

# Plot target speed vs deceleration trigger
plot_gp_2D(gp_model, X.values, 3, 5, feature_names)

# Most important feature relationships for collision prediction
feature_names = ['Ego Start X', 'Ego Speed', 'Target Start X', 'Target Speed', 
                'Target Decel', 'Target Decel Trigger']

# 1. Initial Distance vs Ego Speed
# (Initial distance = Target Start X - Ego Start X)
initial_distance = X['target_start_x'] - X['ego_start_x']
X_with_distance = X.copy()
X_with_distance['initial_distance'] = initial_distance
plot_gp_2D(gp_model, X_with_distance.values, -1, 1, feature_names + ['Initial Distance'])

# 2. Relative Speed vs Target Decel
# (Relative Speed = Ego Speed - Target Speed)
relative_speed = X['ego_speed'] - X['target_speed']
X_with_rel_speed = X.copy()
X_with_rel_speed['relative_speed'] = relative_speed
plot_gp_2D(gp_model, X_with_rel_speed.values, -1, 4, feature_names + ['Relative Speed'])

# 3. Target Decel vs Decel Trigger Distance
plot_gp_2D(gp_model, X.values, 4, 5, feature_names)

