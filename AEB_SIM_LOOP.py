import numpy as np
from world import World
from agents import Car, RectangleBuilding, Pedestrian, Painting
from geometry import Point
import time
from AEB_algo import (
    AEBController, TARGET_FINAL_DISTANCE, 
    FCW_TTC, SOFT_BRAKE_TTC, FULL_BRAKE_TTC,
    MAX_SOFT_BRAKE, MAX_FULL_BRAKE, SYSTEM_LATENCY
)
from plots import create_aeb_plots
import os

# Function to run AEB simulation
def run_aeb_simulation(config):
    dt = 0.1  # time steps in seconds
    time_data, speed_data, distance_data = [], [], []
    ttc_data, required_decel_data, applied_decel_data = [], [], []
    target_speed_data = []

    # Initialize collision flags
    collision_occurred = False
    impact_speed = 0

    # Create AEB controller
    aeb = AEBController()

    # Set up simulation environment
    w = World(dt, width=400, height=40, ppm=6)

    # Configure road and visual elements (optional; can be removed if running headless)
    # Road setup code here...

    # Set up ego and target vehicles
    ego_car = Car(Point(config['ego_start_x'], 18.15), 0, 'blue')
    ego_car.velocity = Point(config['ego_speed'], 0)
    w.add(ego_car)

    target_car = Car(Point(config['target_start_x'], 18.15), 0, 'red')
    target_car.velocity = Point(config['target_speed'], 0)
    w.add(target_car)

    # Add this after initializing aeb controller (around line 26)
    aeb_was_triggered = False

    # Simulation loop
    for k in range(250):
        current_time = k * dt
        distance = ego_car.distanceTo(target_car)

        # Trigger deceleration if within specified distance
        if distance <= config['target_decel_trigger']:
            target_car.set_control(0, config['target_decel'])

        # Calculate control info
        control = aeb.calculate_control(ego_car, target_car, current_time)
        
        # Apply AEB control after latency
        if k * dt >= aeb.command_time + SYSTEM_LATENCY:
            aeb.current_deceleration = aeb.commanded_deceleration
            ego_car.set_control(0, aeb.current_deceleration)
        
        # Inside the simulation loop, after applying AEB control (around line 58)
        if aeb.current_deceleration < 0:
            aeb_was_triggered = True

        # Tick the world
        w.tick()

        # Check for collision
        if w.collision_exists():
            collision_occurred = True
            impact_speed = abs(ego_car.velocity.x - target_car.velocity.x) * 3.6  # Convert to kph
            break

    w.close()  # Close the visualizer to prevent memory issues

    # Return result in dictionary format
    initial_speed = config['ego_speed'] * 3.6  # Convert to kph
    final_speed = ego_car.velocity.x * 3.6     # Convert to kph
    speed_reduction = initial_speed - final_speed

    result = {
        'collision_occurred': collision_occurred,
        'impact_speed': impact_speed,
        'aeb_triggered': aeb_was_triggered,
        'speed_reduction': round(speed_reduction, 2)  # Add speed reduction to result
    }

    return result


# Example configuration
config = {
    "initial_gap": 100,
    "ego_start_speed": 55,  # kph
    "target_start_speed": 0,  # kph
    "target_decel": 0,
    "target_decel_trigger": 0  # Trigger distance
}

# Convert speeds from kph to m/s
config['ego_speed'] = config.pop('ego_start_speed') / 3.6
config['target_speed'] = config.pop('target_start_speed') / 3.6

# Run simulation
result = run_aeb_simulation(config)
print(result)