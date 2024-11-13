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
from ACC_algo import ACCController
from plots import create_aeb_plots
import os
from scipy.interpolate import interp1d



# Function to run AEB simulation
def run_aeb_simulation(config, visualize=True):
    # Initialize data collection lists for plotting
    dt = 0.1  # time steps in seconds
    time_data, speed_data, distance_data = [], [], []
    ttc_data, required_decel_data, applied_decel_data = [], [], []
    target_speed_data = []

    # Initialize collision flags
    collision_occurred = False
    impact_speed = 0
    
    # Create controllers
    acc = ACCController()
    acc.set_desired_cruise_speed(config['ego_speed'] * 3.6)  # Convert m/s to kph
    aeb = AEBController()

    # Set up simulation environment
    w = World(dt, width=400, height=40, ppm=6)
    w.visualizer.window_title = os.path.basename(__file__)

    # Road configuration plot
    w.add(Painting(Point(60, 33.7), Point(800, 20), 'dark green'))  # Upper grass
    w.add(Painting(Point(60, 6.3), Point(800, 20), 'dark green'))   # Lower grass
    w.add(Painting(Point(60, 20), Point(800, 7.4), 'gray80'))  # Main road surface
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

    # Use ego and target start positions from config
    ego_start_x = config['ego_start_x']
    target_start_x = config['target_start_x']
    
    # Create interpolation function for target speed profile
    target_speed_profile = interp1d(
        np.array(config['time_profile']['times']), 
        np.array(config['time_profile']['speeds']), 
        kind='linear', 
        fill_value='extrapolate'
    )
    
    # Set up ego and target vehicles
    ego_car = Car(Point(config['ego_start_x'], 18.15), 0, 'blue')
    ego_car.velocity = Point(config['ego_speed'], 0)
    w.add(ego_car)

    target_car = Car(Point(config['target_start_x'], 18.15), 0, 'red')
    # Initialize target car with first speed from profile
    target_car.velocity = Point(config['time_profile']['speeds'][0], 0)
    w.add(target_car)

    # Initialize warning display variables
    warning_visible = False
    warning_square = None
    warning_text = None
    warning_start_time = None
    aeb_was_triggered = False

    # Simulation loop
    for k in range(200):
        current_time = k * dt
        distance = ego_car.distanceTo(target_car)

        # Update target vehicle speed based on time profile
        target_speed = target_speed_profile(current_time)
        current_target_speed = target_car.velocity.x
        
        # Simple P controller for target vehicle to follow speed profile
        speed_error = target_speed - current_target_speed
        target_acceleration = np.clip(speed_error / dt, -6, 6)  # limit acceleration/deceleration
        target_car.set_control(0, target_acceleration)
        
        # Update target car velocity directly for smoother transitions
        target_car.velocity = Point(target_speed, 0)

        # Get ACC and AEB commands
        acc_command = acc.acc_control_loop(ego_car, target_car)
        aeb_command = aeb.calculate_control(ego_car, target_car, current_time)
        
        # Extract the deceleration value from AEB command dictionary
        aeb_decel = aeb_command['applied_decel']
        
        # Check if AEB is active (when AEB deceleration is more aggressive than ACC)
        if aeb_decel < acc_command:
            final_command = aeb_decel
            # Set AEB triggered flag if deceleration is significant
            if abs(aeb_decel) > 0.1:  # threshold to avoid false positives
                aeb_was_triggered = True
        else:
            final_command = acc_command

        # Apply control after latency
        if k * dt >= aeb.command_time + SYSTEM_LATENCY:
            ego_car.set_control(0, final_command)
        
        # Collect data
        time_data.append(current_time)
        distance_data.append(distance)
        speed_data.append(ego_car.velocity.x * 2.237)  # Convert to mph
        ttc_data.append(min(aeb_command['ttc'], 10))
        required_decel_data.append(aeb_command['required_decel'])
        applied_decel_data.append(final_command)
        target_speed_data.append(target_car.velocity.x * 3.6)  # Convert m/s to kph

        # Update visualization
        if visualize:
            w.render()
            
            # Add status text
            ego_speed_kph = ego_car.velocity.x * 3.6
            target_speed_kph = target_car.velocity.x * 3.6
            status_text = f"Ego Speed: {ego_speed_kph:.1f} km/h | Target Speed: {target_speed_kph:.1f} km/h | "
            status_text += f"Distance: {distance:.1f}m | TTC: {aeb_command['ttc']:.1f}s | "
            status_text += f"Decel: {final_command:.1f} m/s² || Time: {current_time:.1f}s"
            w.visualizer.draw_text(status_text, (550, 30))

            # Handle FCW warning display
            if aeb_command['ttc'] <= FCW_TTC:
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

            time.sleep(dt/4)  # Slow down visualization

        # Tick the world
        w.tick()

        # Check for collision
        if w.collision_exists():
            collision_occurred = True
            impact_speed = abs(ego_car.velocity.x - target_car.velocity.x) * 3.6  # Convert to kph
            break

    w.close()

    # # Create plots after simulation, commented out to test passing data to LLM_scn_gen.py
    # if visualize:
    #     create_aeb_plots(time_data, distance_data, speed_data, ttc_data, 
    #                     required_decel_data, applied_decel_data, aeb, target_speed_data)

    # # Return result in dictionary format
    initial_speed = config['ego_speed'] * 3.6  # Convert to kph
    final_speed = ego_car.velocity.x * 3.6     # Convert to kph
    speed_reduction = initial_speed - final_speed

    result = {
        'collision_occurred': collision_occurred,
        'impact_speed': f"{round(impact_speed, 2)} kph",
        'aeb_triggered': aeb_was_triggered,
        'speed_reduction': f"{round(speed_reduction, 2)} kph",
        # Add plotting data
        'plot_data': {
            'time_data': time_data,
            'distance_data': distance_data,
            'speed_data': speed_data,
            'ttc_data': ttc_data,
            'required_decel_data': required_decel_data,
            'applied_decel_data': applied_decel_data,
            'target_speed_data': target_speed_data,
            'aeb_controller': aeb
        }
    }

    return result


# # Example configuration
# config = {
#     "ego_start_x": 0,
#     "ego_start_speed": 60,  # kph, starting from stop
#     "target_start_x": 50,   
#     "time_profile": {
#         "times": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
#         "speeds": [0.00, 2.78, 5.56, 8.33, 11.11, 13.89, 16.67, 19.44, 22.22, 25.00, 27.78, 27.78, 27.78, 27.78, 27.78, 27.78, 27.78, 27.78, 27.78, 27.78, 27.78]
#     }
# }

# # Convert ego speed from kph to m/s
# config['ego_speed'] = config.pop('ego_start_speed') / 3.6

# # Run simulation
# result = run_aeb_simulation(config)
# print(result)