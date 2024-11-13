# This script is a simple AEB simulation for Car to Car testing
# Assumptions:
# Perfect sensing and detection - this simulation abstracts away the perception system
# Theoretical braking performance - does not take into account tire slip, fade, or other imperfections
# Fixed TTC thresholds - in a real scenario, these would be dynamically tuned based on relative velocity

# other variables to add
# - duration of target deceleration

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
import json  # Add to imports at top
from ACC_algo import (
    DESIRED_TIME_GAP, MAX_ACCEL, MAX_DECEL,
    MIN_FOLLOWING_DISTANCE, DETECTION_RANGE,
    ACCController
)

### Initialize data collection lists for plotting
dt = 0.1  # time steps in terms of seconds
time_data = []
speed_data = []
distance_data = []
ttc_data = []
required_decel_data = []
applied_decel_data = []
target_speed_data = []

# FCW warning display initialization
warning_square = None
warning_text = None
warning_visible = False
warning_start_time = None

# Create AEB controller
aeb = AEBController()

### Sim environment setup ###
# Get current file name
current_file = os.path.basename(__file__)

# Create world with custom window title
w = World(dt, width=400, height=40, ppm=6)
w.visualizer.window_title = current_file  # Set the window title to current file name

# Road configuration plot
w.add(Painting(Point(60, 33.7), Point(800, 20), 'dark green'))  # Upper grass
w.add(Painting(Point(60, 6.3), Point(800, 20), 'dark green'))   # Lower grass
w.add(Painting(Point(60, 20), Point(800, 7.4), 'gray80'))  # Main road surface - total width 7.4m
w.add(Painting(Point(60, 23.7), Point(800, 0.3), 'white'))  # Upper road edge
w.add(Painting(Point(60, 16.3), Point(800, 0.3), 'white'))  # Lower road edge

for i in range(40):  # yellow dashed lane markings   
    x_pos = 10 + (i * 12)  # 12m total spacing (3m dash + 9m gap)
    w.add(Painting(Point(x_pos, 20), Point(2, 0.2), 'yellow'))  # 3m long dashes

# Add pedestrian crosswalk
crosswalk_x = 124
crosswalk_width = 2  # 2m wide crosswalk
crosswalk_stripes = 6  # Number of stripes

for i in range(crosswalk_stripes):
    stripe_y = 17 + (i * 1.23)  # Evenly space stripes across road width (7.4m)
    w.add(Painting(Point(crosswalk_x, stripe_y), Point(crosswalk_width, 0.5), 'white'))
### Sim environment setup ###

########################
### Sim agents setup ###
# Add two cars: ego vehicle and stationary target vehicle
def setup_simulation(config):
    # Create cars
    ego_car = Car(Point(config['ego_start_x'], 18.15), 0, 'blue')
    ego_car.velocity = Point(config['ego_speed'], 0)
    w.add(ego_car)

    target_car = Car(Point(config['target_start_x'], 18.15), 0, 'red')
    target_car.velocity = Point(config['target_speed'], 0)
    w.add(target_car)
    
    return ego_car, target_car

# Main simulation execution
if __name__ == "__main__":
    # Use single test configuration
    #27.0,50.0,205.0,15.0,-3.0,31.0
    config = {
        "ego_start_x": 27,          # meters
        "ego_start_speed": 50,      # kph
        "target_start_x": 205,      # meters
        "target_start_speed": 15,    # kph
        "target_decel": -3,          # m/s²
        "target_decel_trigger": 31   # meters
    }
    
    # Convert speeds from kph to m/s
    config['ego_speed'] = config.pop('ego_start_speed') / 3.6
    config['target_speed'] = config.pop('target_start_speed') / 3.6
    
    # Setup simulation with config
    ego_car, target_car = setup_simulation(config)
    
########################


w.render()



### Sim loop ###
collision_occurred = False
impact_speed = 0

for k in range(200):
    current_time = k * dt
    
    # Calculate distance first
    distance = ego_car.distanceTo(target_car)
    
    # Add target vehicle deceleration control
    if distance <= config['target_decel_trigger']:
        target_car.set_control(0, config['target_decel'])
    
    # Always get control info for data collection
    control = aeb.calculate_control(ego_car, target_car, current_time)
    
    # Calculate TTC for speed maintenance
    relative_speed = ego_car.velocity.x - target_car.velocity.x
    ttc = distance / relative_speed if relative_speed > 0 else float('inf')
    

    # Apply control after latency
    if k * dt >= aeb.command_time + SYSTEM_LATENCY:
        aeb.current_deceleration = aeb.commanded_deceleration
        ego_car.set_control(0, aeb.current_deceleration)
    
    # Tick the world to update physics
    w.tick()
    
    # Collect data
    time_data.append(current_time)
    speed_data.append(control['speed_mph'])
    distance_data.append(control['distance'])
    ttc_data.append(min(control['ttc'], 10))
    required_decel_data.append(control['required_decel'])
    applied_decel_data.append(aeb.current_deceleration)
    target_speed_data.append(target_car.velocity.x * 3.6)  # Convert m/s to kph

    ego_speed_kph = ego_car.velocity.x * 3.6
    target_speed_kph = target_car.velocity.x * 3.6
    
    # Add status text to the rendering 
    status_text = f"Ego Speed: {ego_speed_kph:.1f} km/h | Target Speed: {target_speed_kph:.1f} km/h | Distance: {control['distance']:.1f}m | TTC: {control['ttc']:.1f}s | Decel: {aeb.current_deceleration:.1f} m/s²     ||     Time: {current_time:.1f}s"
    w.visualizer.draw_text(status_text, (550, 30))  
    
    # Handle FCW warning display
    if ttc <= FCW_TTC:
        if not warning_visible:
            if warning_square:
                warning_square.undraw()
                warning_text.undraw()
            warning_square, warning_text = w.visualizer.draw_warning()
            warning_visible = True
            warning_start_time = current_time
        elif current_time - warning_start_time >= 3.0:  # 3 second duration
            warning_square.undraw()
            warning_text.undraw()
            warning_square, warning_text = w.visualizer.draw_warning()
            warning_start_time = current_time
    else:
        if warning_visible:
            if warning_square:
                warning_square.undraw()
                warning_text.undraw()
            warning_visible = False
            warning_start_time = None
    

    w.render()
    time.sleep(dt/4)

    if w.collision_exists():
        collision_occurred = True
        # Calculate impact speed (relative velocity at collision)
        impact_speed = abs(ego_car.velocity.x - target_car.velocity.x)
        break

# Replace plotting code with simple result output
if collision_occurred:
    print(f"Collision: True")
    print(f"Impact Speed: {impact_speed * 3.6:.1f} kph")  # Convert m/s to kph
else:
    print("Collision: False")

w.close()

# Create plots after simulation
create_aeb_plots(time_data, distance_data, speed_data, ttc_data, 
                required_decel_data, applied_decel_data, aeb, target_speed_data)

