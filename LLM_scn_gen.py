import tkinter as tk
from tkinter import scrolledtext
import requests
import json
from Combined_SIM_speedprofile import run_aeb_simulation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class SimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AEB Scenario Simulator")
        self.OPENROUTER_API_KEY = "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"

        # Create main container
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(expand=True, fill='both')

        # Prompt input section
        tk.Label(main_frame, text="Enter scenario description:", font=("Arial", 20, "bold")).pack(anchor='center', pady=(20, 10))
        self.prompt_text = tk.Text(main_frame, height=4, width=80)
        self.prompt_text.pack(pady=(0, 20))
        self.prompt_text.insert('1.0', "Enter a detailed scenario description: (example: The ego vehicle is traveling at 120 kph towards a target that is traveling at 80 kph. Target vehicle begins to decelerate after 5s at -2 m/s^2.)")
        
        # Add this binding for click event
        self.prompt_text.bind('<Button-1>', self.clear_prompt_text)

        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(0, 20))

        # Add a container frame for buttons and center it
        buttons_container = tk.Frame(button_frame)
        buttons_container.pack(anchor='center')
        
        tk.Button(buttons_container, text="Simulate", command=self.run_simulation).pack(side='left', padx=10)
        tk.Button(buttons_container, text="Clear", command=self.clear_all).pack(side='left')

        # Output area
        tk.Label(main_frame, text="Output:").pack(anchor='w')
        self.output_area = scrolledtext.ScrolledText(main_frame, height=20, width=60)
        self.output_area.pack(expand=True, fill='both')

        # Create frame for plots
        self.plot_frame = tk.Frame(main_frame)
        self.plot_frame.pack(expand=True, fill='both', pady=10)
        
        # Create figure and canvas for plots
        self.fig = plt.figure(figsize=(10, 30))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')

    def create_embedded_plots(self, time_data, distance_data, speed_data, ttc_data, 
                            required_decel_data, applied_decel_data, aeb_controller, target_speed_data):
        # Clear previous plots
        self.fig.clear()

        # Distance plot
        ax1 = self.fig.add_subplot(511)
        ax1.plot(time_data, distance_data, label="Distance to Target (m)")
        ax1.axhline(y=3, color='r', linestyle='--', label="Target Stopping Distance (3m)")
        if aeb_controller.fcw_activation:
            ax1.scatter(aeb_controller.fcw_activation[0], aeb_controller.fcw_activation[1], 
                       color='blue', label="FCW Activated", zorder=5)
        if aeb_controller.soft_brake_activation:
            ax1.scatter(aeb_controller.soft_brake_activation[0], aeb_controller.soft_brake_activation[1], 
                       color='orange', label="Soft Brake Activated", zorder=5)
        if aeb_controller.hard_brake_activation:
            ax1.scatter(aeb_controller.hard_brake_activation[0], aeb_controller.hard_brake_activation[1], 
                       color='purple', label="Hard Brake Activated", zorder=5)
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Distance (m)")
        ax1.grid(True)
        ax1.legend()

        # Speed plot
        ax2 = self.fig.add_subplot(512)
        ax2.plot(time_data, [s * 1.60934 for s in speed_data], color="orange", label="Ego Vehicle Speed (km/h)")
        ax2.plot(time_data, target_speed_data, color="blue", label="Target Vehicle Speed (km/h)")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Speed (km/h)")
        ax2.set_ylim(bottom=0)
        ax2.grid(True)
        ax2.legend()

        # TTC plot
        ax3 = self.fig.add_subplot(513)
        ax3.plot(time_data, ttc_data, color="green", label="TTC (s)")
        ax3.axhline(y=2.5, color='blue', linestyle='--', label="FCW Threshold")
        ax3.axhline(y=1.7, color='orange', linestyle='--', label="Soft Brake Threshold")
        ax3.axhline(y=1.0, color='red', linestyle='--', label="Hard Brake Threshold")
        ax3.set_ylim(bottom=0, top=6)
        ax3.set_xlabel("Time (s)")
        ax3.set_ylabel("TTC (s)")
        ax3.grid(True)
        ax3.legend()

        # Deceleration plot
        ax4 = self.fig.add_subplot(514)
        ax4.plot(time_data, required_decel_data, color="green", linestyle='--', 
                label="Required Decel")
        ax4.plot(time_data, applied_decel_data, color="red", label="Applied Decel")
        ax4.axhline(y=-3.0, color='orange', linestyle=':', label="Soft Brake Limit")
        ax4.axhline(y=-6.0, color='red', linestyle=':', label="Hard Brake Limit")
        ax4.set_ylim(top=1, bottom=-10)
        ax4.set_xlabel("Time (s)")
        ax4.set_ylabel("Decel (m/s²)")
        ax4.grid(True)
        ax4.legend()

        # Adjust layout and display
        self.fig.tight_layout()
        self.canvas.draw()

    def run_simulation(self):
        self.output_area.delete('1.0', tk.END)
        self.output_area.insert(tk.END, "Processing your request...\n")
        # Force update the display immediately
        self.output_area.update_idletasks()
        
        user_prompt = self.prompt_text.get('1.0', 'end-1c')
        
        try:
            # Call LLM API
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "meta-llama/llama-3.2-90b-vision-instruct:free",
                            "messages": [
                            {
                                "role": "system",
                                "content": """
                                You are an expert in ADAS systems testing and simulation, your job is to provide a scenario configuration in a JSON format based on user input. Ensure the scenario created is realistic and critical. Only provide the JSON configuration, no other text, no explanation.

                                Rules: 
                                - All vehicles are traveling in the same direction (x-axis)
                                - The unit system for ego_start_speed is kph
                                - The unit system for speeds is m/s
                                - The unit system for distance is meters
                                - All JSON values must be numbers, if value is None, use 0
                                - Target vehicle must be ahead of ego vehicle, meaning target_start_x > ego_start_x
                                - Ensure the ego and target distances are not too close or too far, for example, if its too far, AEB will never activate
                                - Ensure the times and speeds must be the same length
                                - The max array length for both speed and time is 20
                                - The user may use the term ego and target, which refers to the ego vehicle and target vehicle respectively
                                - If the user says 'a slower moving target', it means the target vehicle's speed is less than the ego vehicle's speed
                                - Target vehicle speeds should never be negative, if it is negative, then use 0
                                - Always return a scenario configuration, to the best of your ability
                                - You may not generate negative speeds, if it is negative, then use 0

                                Example user input:
                                "Ego and target vehicles both traveling at 60 kph, then after some time, the target decelerates at -4 m/s^2"
                                
                                Example JSON:
                                config = {
                                    "ego_start_x": 0,
                                    "ego_start_speed": 60,  # kph
                                    "target_start_x": 50,   
                                    "time_profile": {
                                        "times": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
                                        "speeds": [16.67, 16.67, 16.67, 16.67, 16.67, 12.67, 8.67, 4.67, 0.67, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
                                    }
                                }

                                # Example user input:
                                "Ego vehicle traveling at 50 kph towards a stationary target vehicle"

                                # Example JSON:
                                config = {
                                    "ego_start_x": 0,
                                    "ego_start_speed": 50,  # kph
                                    "target_start_x": 50,   
                                    "time_profile": {
                                        "times": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
                                        "speeds": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
                                    }
                                }

                                """
                            },
                            {
                                "role": "user",
                                "content": user_prompt
                        }
                    ],
                })
            )

            # Add response debugging
            if response.status_code != 200:
                self.output_area.insert(tk.END, f"API Error: Status {response.status_code}\n")
                self.output_area.insert(tk.END, f"Response: {response.text}\n")
                return
                
            response_json = response.json()
            if 'choices' not in response_json:
                self.output_area.insert(tk.END, f"Unexpected API response format:\n{json.dumps(response_json, indent=2)}\n")
                return
                
            config = json.loads(response_json['choices'][0]['message']['content'])
            
            self.output_area.insert(tk.END, "Generated Configuration:\n")
            self.output_area.insert(tk.END, json.dumps(config, indent=2) + "\n\n")

            # Run simulation
            sim_config = config.copy()
            sim_config['ego_speed'] = sim_config.pop('ego_start_speed') / 3.6
            
            result = run_aeb_simulation(sim_config)
            
            self.output_area.insert(tk.END, "Simulation Results:\n")
            self.output_area.insert(tk.END, json.dumps(
                {k: v for k, v in result.items() if k != 'plot_data'}, 
                indent=2
            ))

            # Create plots with the simulation data
            plot_data = result['plot_data']
            self.create_embedded_plots(
                plot_data['time_data'],
                plot_data['distance_data'],
                plot_data['speed_data'],
                plot_data['ttc_data'],
                plot_data['required_decel_data'],
                plot_data['applied_decel_data'],
                plot_data['aeb_controller'],
                plot_data['target_speed_data']
            )

            # Add this after the API response
            if response.status_code == 200:
                response_json = response.json()
                token_usage = response_json.get('usage', {})
                self.output_area.insert(tk.END, "\nToken Usage:\n")
                self.output_area.insert(tk.END, f"Prompt tokens: {token_usage.get('prompt_tokens', 'N/A')}\n")
                self.output_area.insert(tk.END, f"Completion tokens: {token_usage.get('completion_tokens', 'N/A')}\n")
                self.output_area.insert(tk.END, f"Total tokens: {token_usage.get('total_tokens', 'N/A')}\n\n")

        except json.JSONDecodeError as e:
            self.output_area.insert(tk.END, f"JSON Parse Error: {str(e)}\nResponse: {response.text}\n")
        except Exception as e:
            self.output_area.insert(tk.END, f"Error Type: {type(e).__name__}\nError Details: {str(e)}\n")

    def clear_all(self):
        self.prompt_text.delete('1.0', tk.END)
        self.output_area.delete('1.0', tk.END)

    def clear_prompt_text(self, event=None):
        if self.prompt_text.get('1.0', 'end-1c') == "Enter scenario description: (ex: Ego vehicle is traveling towards a slower moving target vehicle that begins decelerating at -6m/s^2 when they are 15m apart.)":
            self.prompt_text.delete('1.0', tk.END)

def main():
    root = tk.Tk()
    app = SimulatorGUI(root)
    
    # Add this line to handle window closure
    root.protocol("WM_DELETE_WINDOW", root.quit)
    
    root.mainloop()

if __name__ == "__main__":
    main()