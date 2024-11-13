import numpy as np

# ACC Constants
DESIRED_TIME_GAP = 1.8         # Time gap to maintain (seconds)
MAX_ACCEL = 2.5                # Maximum acceleration allowed (m/s²)
MAX_DECEL = -3.0               # Maximum deceleration allowed (m/s²)
MIN_FOLLOWING_DISTANCE = 2.0   # Minimum safe distance (meters)
DETECTION_RANGE = 100          # Maximum distance to detect and follow a lead vehicle (meters)

class ACCController:
    def __init__(self):
        self.desired_cruise_speed = 30  # Default cruise speed in km/h
        
    def set_desired_cruise_speed(self, speed_kph):
        """Set the desired cruise speed in km/h"""
        self.desired_cruise_speed = speed_kph
        
    def target_follow_control(self, ego_car, target_car):
        """Calculate acceleration command to follow target vehicle"""
        # Calculate current distance and desired following distance
        current_distance = ego_car.distanceTo(target_car)
        desired_distance = ego_car.velocity.x * DESIRED_TIME_GAP + MIN_FOLLOWING_DISTANCE

        # Determine acceleration based on distance error
        distance_error = current_distance - desired_distance
        acceleration = distance_error / DESIRED_TIME_GAP
        
        # Limit acceleration between max deceleration and acceleration
        if acceleration < MAX_DECEL:
            return MAX_DECEL
        elif acceleration > MAX_ACCEL:
            return MAX_ACCEL
        return acceleration
    
    def cruise_control(self, ego_car):
        """Calculate acceleration command to maintain cruise speed"""
        # Convert desired cruise speed from km/h to m/s
        target_speed_ms = self.desired_cruise_speed / 3.6
            
        # Determine acceleration based on speed error
        speed_error = target_speed_ms - ego_car.velocity.x
        acceleration = speed_error / DESIRED_TIME_GAP
        
        # Limit acceleration to vehicle constraints
        if acceleration < MAX_DECEL:
            return MAX_DECEL
        elif acceleration > MAX_ACCEL:
            return MAX_ACCEL
        return acceleration
    
    def acc_control_loop(self, ego_car, target_car=None):
        """Main ACC control loop that switches between following and cruising"""
        if target_car and ego_car.distanceTo(target_car) < DETECTION_RANGE:
            return self.target_follow_control(ego_car, target_car)
        else:
            return self.cruise_control(ego_car)