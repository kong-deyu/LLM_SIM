import numpy as np

# AEB constants
FCW_TTC = 2.3        # Forward Collision Warning Time-to-Collision threshold (seconds)
SOFT_BRAKE_TTC = 1.5 # Threshold for initiating soft braking (seconds)
FULL_BRAKE_TTC = 1.1 # Threshold for initiating emergency braking (seconds)
MAX_SOFT_BRAKE = -3.0  # Maximum soft braking deceleration (m/s²)
MAX_FULL_BRAKE = -8.5  # Maximum emergency braking deceleration (m/s²)
SYSTEM_LATENCY = 0.3     # System response delay (seconds)
TARGET_FINAL_DISTANCE = 3.0  # Desired final distance between vehicles (meters)

class AEBController:
    def __init__(self):
        self.command_time = float('-inf')
        self.commanded_deceleration = 0
        self.current_deceleration = 0
        self.fcw_activation = None
        self.soft_brake_activation = None
        self.hard_brake_activation = None
        
    def calculate_control(self, ego_car, target_car, current_time):
        # Calculate distances and speeds
        distance = ego_car.distanceTo(target_car)
        relative_speed = ego_car.velocity.x - target_car.velocity.x
        ttc = distance / relative_speed if relative_speed > 0 else float('inf')
        
        # Calculate required deceleration
        required_decel = 0
        if distance > TARGET_FINAL_DISTANCE and relative_speed > 0:
            stopping_distance = distance - TARGET_FINAL_DISTANCE
            required_decel = -(relative_speed ** 2) / (2 * stopping_distance)
        
        # Determine AEB command based on TTC thresholds
        if ttc <= FULL_BRAKE_TTC:
            max_allowed_decel = MAX_FULL_BRAKE
        elif ttc <= SOFT_BRAKE_TTC:
            max_allowed_decel = MAX_SOFT_BRAKE
        else:
            max_allowed_decel = 0
            
        # Apply the less aggressive deceleration
        if required_decel < 0:
            applied_decel = max(required_decel, max_allowed_decel)
        else:
            applied_decel = max_allowed_decel

        # Update brake command if changed
        if applied_decel != self.commanded_deceleration:
            self.commanded_deceleration = applied_decel
            self.command_time = current_time
            
        # Check activation events
        if ttc <= FCW_TTC and self.fcw_activation is None:
            self.fcw_activation = (current_time, distance)
        if ttc <= SOFT_BRAKE_TTC and self.soft_brake_activation is None:
            self.soft_brake_activation = (current_time, distance)
        if ttc <= FULL_BRAKE_TTC and self.hard_brake_activation is None:
            self.hard_brake_activation = (current_time, distance)
            
        return {
            'distance': distance,
            'ttc': ttc,
            'required_decel': required_decel,
            'applied_decel': applied_decel,
            'speed_mph': ego_car.velocity.x * 2.237
        }
