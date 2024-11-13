import numpy as np
from world import World
from agents import Car, Painting
from geometry import Point
import time
from ACC_algo import ACCController, DETECTION_RANGE
from AEB_algo import AEBController, SYSTEM_LATENCY
import os

### Initialize simulation ###
dt = 0.1  # Time step (seconds)
w = World(dt, width=400, height=40, ppm=6)
w.visualizer.window_title = "ACC Simulation"

### Road setup ###
# Add grass
w.add(Painting(Point(60, 33.7), Point(800, 20), 'dark green'))  # Upper grass
w.add(Painting(Point(60, 6.3), Point(800, 20), 'dark green'))   # Lower grass

# Add road
w.add(Painting(Point(60, 20), Point(800, 7.4), 'gray80'))      # Road surface
w.add(Painting(Point(60, 23.7), Point(800, 0.3), 'white'))     # Upper edge
w.add(Painting(Point(60, 16.3), Point(800, 0.3), 'white'))     # Lower edge

# Add center line (dashed yellow)
for i in range(40):
    x_pos = 10 + (i * 12)  # 12m spacing (3m dash + 9m gap)
    w.add(Painting(Point(x_pos, 20), Point(2, 0.2), 'yellow'))

### Vehicle setup ###
# Configuration
config = {
    "initial_gap": 100,
    "ego_start_speed": 55,    # kph
    "target_start_speed": 0, # kph
    "target_decel": 0,    # m/s² - deceleration rate
    "decel_start_time": 6,   # seconds into simulation when deceleration begins
    "decel_duration": 4     # seconds - how long deceleration lasts
}


# Convert speeds from kph to m/s
config['ego_speed'] = config['ego_start_speed'] / 3.6
config['target_speed'] = config['target_start_speed'] / 3.6

# Create vehicles
ego_car = Car(Point(config['ego_start_x'], 18.15), 0, 'blue')
ego_car.velocity = Point(config['ego_speed'], 0)
w.add(ego_car)

target_car = Car(Point(config['target_start_x'], 18.15), 0, 'red')
target_car.velocity = Point(config['target_speed'], 0)
w.add(target_car)

# Create controllers
acc = ACCController()
acc.set_desired_cruise_speed(config['ego_start_speed'])
aeb = AEBController()

# Initialize warning display variables
warning_visible = False
warning_square = None
warning_text = None
warning_start_time = None

# Initialize data collection lists
time_data = []
speed_data = []
distance_data = []
ttc_data = []
required_decel_data = []
applied_decel_data = []
target_speed_data = []

### Simulation loop ###
for k in range(300):  # 30 seconds at 0.1s timestep
    current_time = k * dt
    
    # Control target vehicle deceleration/acceleration based on time
    if (current_time >= config['decel_start_time'] and 
        current_time <= config['decel_start_time'] + config['decel_duration']):
        # Apply deceleration during specified window
        target_car.set_control(0, config['target_decel'])
    else:
        # After deceleration period, return to initial speed
        speed_diff = config['target_speed'] - target_car.velocity.x
        if abs(speed_diff) > 0.1:  # Small threshold to prevent oscillation
            acceleration = np.clip(speed_diff, -2.0, 2.0)  # Limit acceleration
            target_car.set_control(0, acceleration)
        else:
            target_car.set_control(0, 0)  # Maintain speed when close to target
    
    # Get ACC and AEB commands
    acc_command = acc.acc_control_loop(ego_car, target_car)
    aeb_command = aeb.calculate_control(ego_car, target_car, current_time)
    
    # Extract the deceleration value from AEB command dictionary
    aeb_decel = aeb_command['applied_decel']
    
    # Apply the more aggressive deceleration between ACC and AEB
    if aeb_decel < acc_command:
        final_command = aeb_decel
    else:
        final_command = acc_command
    
    # Apply control after latency
    if k * dt >= aeb.command_time + SYSTEM_LATENCY:
        ego_car.set_control(0, final_command)
    
    # Collect data
    time_data.append(current_time)
    distance_data.append(ego_car.distanceTo(target_car))
    speed_data.append(ego_car.velocity.x * 2.237)  # Convert to mph
    
    # Calculate TTC
    relative_speed = ego_car.velocity.x - target_car.velocity.x
    ttc = distance_data[-1] / relative_speed if relative_speed > 0 else float('inf')
    ttc_data.append(min(ttc, 10))
    
    # Store deceleration data
    required_decel_data.append(aeb_command['required_decel'])
    applied_decel_data.append(final_command)
    target_speed_data.append(target_car.velocity.x * 3.6)  # Convert m/s to kph
    
    # Update simulation
    w.tick()
    
    # Display status
    status_text = (
        f"Distance: {ego_car.distanceTo(target_car):.1f}m | "
        f"Ego Speed: {ego_car.velocity.x*3.6:.1f}km/h | "
        f"Target Speed: {target_car.velocity.x*3.6:.1f}km/h | "
        f"Command: {final_command:.2f}m/s² | "
        f"Time: {current_time:.1f}s"
    )
    w.visualizer.draw_text(status_text, (550, 30))
    
    # Handle FCW warning display
    if aeb.fcw_activation is not None and current_time >= aeb.fcw_activation[0]:
        if not warning_visible:
            if warning_square:
                warning_square.undraw()
                warning_text.undraw()
            warning_square, warning_text = w.visualizer.draw_warning()
            warning_visible = True
            warning_start_time = current_time
        elif current_time - warning_start_time >= 3.0:  # 3 second warning duration
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
    
    # Render and add small delay for visualization
    w.render()
    time.sleep(dt/4)
    
    # Check for collision
    if w.collision_exists():
        print("Collision occurred!")
        break

# Clean up warning display if still visible
if warning_visible and warning_square:
    warning_square.undraw()
    warning_text.undraw()

# Create plots after simulation
from plots import create_aeb_plots
create_aeb_plots(time_data, distance_data, speed_data, ttc_data, 
                required_decel_data, applied_decel_data, aeb, target_speed_data)

w.close()
