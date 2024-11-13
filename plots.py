import matplotlib.pyplot as plt
from AEB_algo import FCW_TTC, SOFT_BRAKE_TTC, FULL_BRAKE_TTC, MAX_SOFT_BRAKE, MAX_FULL_BRAKE, TARGET_FINAL_DISTANCE

def create_aeb_plots(time_data, distance_data, speed_data, ttc_data, required_decel_data, 
                    applied_decel_data, aeb_controller, target_speed_data):
    plt.figure(figsize=(10, 15))

    # Distance plot
    plt.subplot(5, 1, 1)
    plt.plot(time_data, distance_data, label="Distance to Target (m)")
    plt.axhline(y=TARGET_FINAL_DISTANCE, color='r', linestyle='--', label="Target Stopping Distance (3m)")
    plt.xlabel("Time (s)")
    plt.ylabel("Distance to Target (m)")
    plt.legend()
    plt.grid()

    # Add activation markers
    if aeb_controller.fcw_activation:
        plt.scatter(aeb_controller.fcw_activation[0], aeb_controller.fcw_activation[1], 
                   color='blue', label="FCW Activated", zorder=5)
    if aeb_controller.soft_brake_activation:
        plt.scatter(aeb_controller.soft_brake_activation[0], aeb_controller.soft_brake_activation[1], 
                   color='orange', label="Soft Brake Activated", zorder=5)
    if aeb_controller.hard_brake_activation:
        plt.scatter(aeb_controller.hard_brake_activation[0], aeb_controller.hard_brake_activation[1], 
                   color='purple', label="Hard Brake Activated", zorder=5)
    plt.legend()
    
    # Speed plot
    plt.subplot(5, 1, 2)
    plt.plot(time_data, [s * 1.60934 for s in speed_data], color="orange", label="Ego Vehicle Speed (km/h)")
    plt.plot(time_data, target_speed_data, color="blue", label="Target Vehicle Speed (km/h)")
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (km/h)")
    plt.ylim(bottom=0)
    plt.legend()
    plt.grid()

    # TTC plot
    plt.subplot(5, 1, 3)
    plt.plot(time_data, ttc_data, color="green", label="TTC (s)")
    plt.axhline(y=FCW_TTC, color='blue', linestyle='--', label="FCW Threshold")
    plt.axhline(y=SOFT_BRAKE_TTC, color='orange', linestyle='--', label="Soft Brake Threshold")
    plt.axhline(y=FULL_BRAKE_TTC, color='red', linestyle='--', label="Hard Brake Threshold")
    plt.ylim(bottom=0, top=6)
    plt.xlabel("Time (s)")
    plt.ylabel("Time-to-Collision (s)")
    plt.legend()
    plt.grid()

    # Deceleration plot
    plt.subplot(5, 1, 4)
    plt.plot(time_data, required_decel_data, color="green", linestyle='--', 
            label="Required Decel (minimum needed)")
    plt.plot(time_data, applied_decel_data, color="red", label="Applied Decel (actual)")
    plt.axhline(y=MAX_SOFT_BRAKE, color='orange', linestyle=':', label="Soft Brake Limit")
    plt.axhline(y=MAX_FULL_BRAKE, color='red', linestyle=':', label="Hard Brake Limit")
    plt.ylim(top=1, bottom=-10)
    plt.xlabel("Time (s)")
    plt.ylabel("Deceleration (mph/s)")
    plt.legend()
    plt.grid()

    plt.tight_layout()
    plt.show()
