import tkinter as tk
import math

class HighwayGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Highway Structures")

        # Create a canvas with larger dimensions
        self.canvas = tk.Canvas(root, width=1000, height=800, bg='white')
        self.canvas.pack(expand=True, fill='both')

        # Calculate center coordinates and circle size
        self.canvas_width = 1000
        self.canvas_height = 800
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        circle_size = 200  # Diameter of the circle

        # Create the main highway circle (centered)
        self.main_circle = self.canvas.create_oval(
            center_x - circle_size//2,  # x1
            center_y - circle_size//2,  # y1
            center_x + circle_size//2,  # x2
            center_y + circle_size//2,  # y2
            fill="lightblue", 
            tags="main_circle"
        )
        
        # Center the text
        self.canvas.create_text(
            center_x,
            center_y,
            text="Highway\nStructures", 
            tags="main_circle",
            font=("Arial", 20, "bold"),
            fill="black"
        )

        # Bind hover and click events
        self.canvas.tag_bind("main_circle", "<Enter>", self.on_hover)
        self.canvas.tag_bind("main_circle", "<Leave>", self.on_leave)
        self.canvas.tag_bind("main_circle", "<Button-1>", self.on_click)

        # State to track if sub-circles are displayed
        self.sub_circles_displayed = False

        # Add animation parameters
        self.animation_frames = 20
        self.animation_speed = 20  # milliseconds between frames
        self.jiggle_amplitude = 5  # pixels for jiggle effect

        # Define the subcategories data
        self.subcategories = {
            "Basic Road\nTypes": [
                "Straight\nSegments",
                "Curved\nSegments",
                "Upgrades\n(Inclines)",
                "Downgrades\n(Declines)"
            ],
            "Lane\nConfigurations": [
                "Single Lane",
                "Multi-Lane",
                "Express/HOV\nLanes",
                "Shoulders"
            ],
            "Entry/Exit\nConfigs": [
                "On-Ramps",
                "Off-Ramps",
                "Collector-\nDistributor",
                "Weaving\nZones"
            ],
            "Merging/\nDiverging": [
                "Merging\nLanes",
                "Splitting\nLanes"
            ],
            "Interchange\nGeometries": [
                "Diamond",
                "Cloverleaf",
                "Stack",
                "T-Interchange"
            ],
            "Special\nZones": [
                "Toll Plazas",
                "Rest Areas",
                "Service\nStations",
                "Construction\nZones"
            ]
        }

        # Track active circles and their states
        self.active_parent = None
        self.secondary_circles = []
        self.secondary_texts = []
        self.secondary_displayed = False

        # Add color schemes for different layers
        self.colors = {
            'main': {
                'fill': 'lightblue',
                'hover_outline': 'blue',
                'outline': 'black'
            },
            'sub': {
                'fill': '#e6ffe6',  # Light green
                'hover_outline': 'darkgreen',
                'outline': 'darkgreen'
            },
            'secondary': {
                'fill': '#ffe6e6',  # Light pink
                'hover_outline': 'darkred',
                'outline': 'darkred'
            }
        }

        # Add this line with the other initialization parameters
        self.circle_radius = 150  # Base radius for circle positioning

        # Add path tracking
        self.current_path = []

    def on_hover(self, event):
        # Enhanced hover effect
        self.canvas.itemconfig(self.main_circle, 
                             outline="blue", 
                             width=3)

    def on_leave(self, event):
        # Enhanced leave effect
        self.canvas.itemconfig(self.main_circle, 
                             outline="black", 
                             width=1)

    def on_click(self, event):
        if not self.sub_circles_displayed:
            self.current_path = ["Highway Structures"]
            print(self.current_path[0])
            self.display_sub_circles()
        else:
            # First hide secondary circles if they're displayed
            if self.secondary_displayed:
                self.hide_secondary_circles()
                self.secondary_displayed = False
            # Then hide sub circles
            self.hide_sub_circles()
            self.current_path = []

    def display_sub_circles(self):
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        
        # Define circle parameters
        radius = 180  # Reduced from 250 to 180 for closer positioning
        circle_size = 100  # Size of each sub-circle
        num_circles = 6
        
        # Calculate positions around a circle
        self.final_positions = []
        for i in range(num_circles):
            angle = i * (2 * math.pi / num_circles) - math.pi/2  # Start from top
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            # Add circle coordinates
            self.final_positions.append((
                x - circle_size/2,
                y - circle_size/2,
                x + circle_size/2,
                y + circle_size/2
            ))

        # Start positions (all at main circle's center)
        size = 20  # Initial small size
        start_positions = [(center_x - size, center_y - size, 
                           center_x + size, center_y + size)] * 6

        # Create sub-circles at starting positions
        self.sub_circles = []
        self.sub_circle_texts = []
        
        labels = [
            "Basic Road\nTypes",
            "Lane\nConfigurations",
            "Entry/Exit\nConfigs",
            "Merging/\nDiverging",
            "Interchange\nGeometries",
            "Special\nZones"
        ]

        # Create initial circles (small and centered)
        for i, (coords, label) in enumerate(zip(start_positions, labels)):
            # Create a unique tag for this circle group
            circle_tag = f"circle_{i}"
            
            circle = self.canvas.create_oval(coords, 
                                          fill=self.colors['sub']['fill'],
                                          outline=self.colors['sub']['outline'],
                                          width=2,
                                          state='hidden',
                                          tags=circle_tag)
            self.sub_circles.append(circle)

            # Create text with the same tag
            x = (coords[0] + coords[2]) / 2
            y = (coords[1] + coords[3]) / 2
            text = self.canvas.create_text(x, y,
                                         text=label,
                                         font=("Arial", 12, "bold"),
                                         fill="black",
                                         justify="center",
                                         state='hidden',
                                         tags=circle_tag)  # Add same tag to text
            self.sub_circle_texts.append(text)

            # Bind click event to the tag instead of just the circle
            self.canvas.tag_bind(circle_tag, '<Button-1>', self.on_sub_circle_click)

            # Add hover bindings for sub circles
            self.canvas.tag_bind(circle_tag, '<Enter>', lambda e, tag=circle_tag: self.on_sub_hover(tag))
            self.canvas.tag_bind(circle_tag, '<Leave>', lambda e, tag=circle_tag: self.on_sub_leave(tag))

        # Start animation
        self.frame = 0
        self.animate_circles()
        self.sub_circles_displayed = True

    def animate_circles(self):
        if self.frame <= self.animation_frames:
            progress = self.frame / self.animation_frames
            
            # Easing function for smooth animation
            ease_progress = 1 - (1 - progress) * (1 - progress)
            
            # Add jiggle effect
            jiggle = self.jiggle_amplitude * math.sin(progress * math.pi * 2) * (1 - progress)
            
            for i, (circle, text) in enumerate(zip(self.sub_circles, self.sub_circle_texts)):
                # Make items visible on first frame
                if self.frame == 0:
                    self.canvas.itemconfig(circle, state='normal')
                    self.canvas.itemconfig(text, state='normal')

                # Calculate current position
                start = self.canvas.coords(circle)
                final = self.final_positions[i]
                
                # Interpolate between start and final positions
                current = [
                    start[0] + (final[0] - start[0]) * ease_progress + jiggle,
                    start[1] + (final[1] - start[1]) * ease_progress + jiggle,
                    start[2] + (final[2] - start[2]) * ease_progress + jiggle,
                    start[3] + (final[3] - start[3]) * ease_progress + jiggle
                ]
                
                # Update positions
                self.canvas.coords(circle, *current)
                self.canvas.coords(text, 
                                 (current[0] + current[2]) / 2,
                                 (current[1] + current[3]) / 2)

            self.frame += 1
            self.root.after(self.animation_speed, self.animate_circles)

    def hide_sub_circles(self):
        # Animate circles back to center before removing
        self.frame = self.animation_frames
        self.animate_circles_reverse()

    def animate_circles_reverse(self):
        if self.frame >= 0:
            progress = self.frame / self.animation_frames
            
            # Easing function for smooth animation
            ease_progress = progress * progress
            
            # Add jiggle effect
            jiggle = self.jiggle_amplitude * math.sin(progress * math.pi * 2) * progress
            
            center_x = self.canvas_width // 2
            center_y = self.canvas_height // 2
            
            for i, (circle, text) in enumerate(zip(self.sub_circles, self.sub_circle_texts)):
                final = self.final_positions[i]
                
                # Interpolate between current and center positions
                current = [
                    final[0] + (center_x - final[0]) * (1 - ease_progress) + jiggle,
                    final[1] + (center_y - final[1]) * (1 - ease_progress) + jiggle,
                    final[2] + (center_x - final[2]) * (1 - ease_progress) + jiggle,
                    final[3] + (center_y - final[3]) * (1 - ease_progress) + jiggle
                ]
                
                # Update positions
                self.canvas.coords(circle, *current)
                self.canvas.coords(text, 
                                 (current[0] + current[2]) / 2,
                                 (current[1] + current[3]) / 2)

            self.frame -= 1
            self.root.after(self.animation_speed, self.animate_circles_reverse)
        else:
            # Clean up after animation
            for circle in self.sub_circles:
                self.canvas.delete(circle)
            for text in self.sub_circle_texts:
                self.canvas.delete(text)
            self.sub_circles_displayed = False

    def on_sub_circle_click(self, event):
        # Find which circle was clicked using tags
        clicked_tags = self.canvas.gettags(self.canvas.find_closest(event.x, event.y)[0])
        
        for tag in clicked_tags:
            if tag.startswith('circle_'):
                idx = int(tag.split('_')[1])
                clicked_text = self.canvas.itemcget(self.sub_circle_texts[idx], 'text')
                
                # Update path for sub-circle
                self.current_path = ["Highway Structures", clicked_text.replace('\n', ' ')]
                print(", ".join(self.current_path))
                
                # If this category has subcategories
                if clicked_text in self.subcategories:
                    if not self.secondary_displayed:
                        self.active_parent = self.sub_circles[idx]
                        self.display_secondary_circles(clicked_text)
                    else:
                        self.current_path = self.current_path[:2]  # Keep only main and sub paths
                        self.hide_secondary_circles()
                break

    def display_secondary_circles(self, parent_category):
        # Get the parent circle's position
        parent_coords = self.canvas.coords(self.active_parent)
        parent_center_x = (parent_coords[0] + parent_coords[2]) / 2
        parent_center_y = (parent_coords[1] + parent_coords[3]) / 2

        subcategories = self.subcategories[parent_category]
        num_items = len(subcategories)
        
        radius = 130  # Distance from parent circle
        circle_size = 80  # Size of secondary circles
        initial_radius = 50  # Starting radius
        
        # Calculate and store both start and final positions
        start_positions = []
        self.secondary_final_positions = []  # Add this line to store final positions
        
        for i in range(num_items):
            angle = i * (2 * math.pi / num_items) - math.pi/2
            
            # Calculate start positions (closer to parent)
            x_start = parent_center_x + initial_radius * math.cos(angle)
            y_start = parent_center_y + initial_radius * math.sin(angle)
            start_positions.append((
                x_start - circle_size/2,
                y_start - circle_size/2,
                x_start + circle_size/2,
                y_start + circle_size/2
            ))
            
            # Calculate final positions
            x_final = parent_center_x + radius * math.cos(angle)
            y_final = parent_center_y + radius * math.sin(angle)
            self.secondary_final_positions.append((
                x_final - circle_size/2,
                y_final - circle_size/2,
                x_final + circle_size/2,
                y_final + circle_size/2
            ))

        # Create secondary circles
        self.secondary_circles = []
        self.secondary_texts = []

        for i, (coords, label) in enumerate(zip(start_positions, subcategories)):
            # Create a unique tag for this secondary circle group
            circle_tag = f"secondary_{i}"
            
            circle = self.canvas.create_oval(coords,
                                          fill=self.colors['secondary']['fill'],
                                          outline=self.colors['secondary']['outline'],
                                          width=2,
                                          state='hidden',
                                          tags=circle_tag)
            self.secondary_circles.append(circle)

            text = self.canvas.create_text((coords[0] + coords[2]) / 2,
                                         (coords[1] + coords[3]) / 2,
                                         text=label,
                                         font=("Arial", 12, "bold"),
                                         fill="black",
                                         justify="center",
                                         state='hidden',
                                         tags=circle_tag)
            self.secondary_texts.append(text)

            # Modify the click binding to include path tracking
            self.canvas.tag_bind(
                circle_tag, 
                '<Button-1>', 
                lambda e, label=label: self.on_secondary_circle_click(label)
            )

            # Add hover bindings for secondary circles
            self.canvas.tag_bind(circle_tag, '<Enter>', lambda e, tag=circle_tag: self.on_secondary_hover(tag))
            self.canvas.tag_bind(circle_tag, '<Leave>', lambda e, tag=circle_tag: self.on_secondary_leave(tag))

        # Start animation
        self.secondary_frame = 0
        self.animate_secondary_circles()
        self.secondary_displayed = True

    def animate_secondary_circles(self):
        if self.secondary_frame <= self.animation_frames:
            progress = self.secondary_frame / self.animation_frames
            ease_progress = progress * (2 - progress)
            jiggle = self.jiggle_amplitude * math.sin(progress * math.pi * 2) * (1 - progress)
            
            parent_coords = self.canvas.coords(self.active_parent)
            center_x = (parent_coords[0] + parent_coords[2]) / 2
            center_y = (parent_coords[1] + parent_coords[3]) / 2
            
            for i, (circle, text) in enumerate(zip(self.secondary_circles, self.secondary_texts)):
                final = self.secondary_final_positions[i]
                
                # Calculate current position with start point being the parent's center
                current = [
                    center_x + (final[0] - center_x) * ease_progress + jiggle,
                    center_y + (final[1] - center_y) * ease_progress + jiggle,
                    center_x + (final[2] - center_x) * ease_progress + jiggle,
                    center_y + (final[3] - center_y) * ease_progress + jiggle
                ]
                
                self.canvas.coords(circle, *current)
                self.canvas.coords(text, 
                                 (current[0] + current[2]) / 2,
                                 (current[1] + current[3]) / 2)
                
                if self.secondary_frame == 0:
                    self.canvas.itemconfig(circle, state='normal')
                    self.canvas.itemconfig(text, state='normal')
            
            self.secondary_frame += 1
            self.root.after(self.animation_speed, self.animate_secondary_circles)

    def hide_secondary_circles(self):
        if not hasattr(self, 'secondary_circles') or not self.secondary_circles:
            return
        # Animate circles back to center before removing
        self.secondary_frame = self.animation_frames
        self.animate_secondary_circles_reverse()

    def animate_secondary_circles_reverse(self):
        if self.secondary_frame >= 0:
            progress = self.secondary_frame / self.animation_frames
            
            # Smoother easing function for reverse animation
            ease_progress = progress * progress * (3 - 2 * progress)
            
            # Reduce jiggle amplitude for reverse animation
            jiggle = (self.jiggle_amplitude * 0.5) * math.sin(progress * math.pi * 2) * progress
            
            parent_coords = self.canvas.coords(self.active_parent)
            center_x = (parent_coords[0] + parent_coords[2]) / 2
            center_y = (parent_coords[1] + parent_coords[3]) / 2
            
            for i, (circle, text) in enumerate(zip(self.secondary_circles, self.secondary_texts)):
                final = self.secondary_final_positions[i]
                
                # Simplified position calculation for smoother animation
                current = [
                    final[0] + (center_x - final[0]) * (1 - ease_progress) + jiggle,
                    final[1] + (center_y - final[1]) * (1 - ease_progress) + jiggle,
                    final[2] + (center_x - final[2]) * (1 - ease_progress) + jiggle,
                    final[3] + (center_y - final[3]) * (1 - ease_progress) + jiggle
                ]
                
                self.canvas.coords(circle, *current)
                self.canvas.coords(text, 
                                 (current[0] + current[2]) / 2,
                                 (current[1] + current[3]) / 2)

            self.secondary_frame -= 1
            # Increase animation speed for reverse animation
            self.root.after(int(self.animation_speed * 0.8), self.animate_secondary_circles_reverse)
        else:
            # Clean up
            for circle in self.secondary_circles:
                self.canvas.delete(circle)
            for text in self.secondary_texts:
                self.canvas.delete(text)
            self.secondary_displayed = False

    # Add new hover methods for sub circles
    def on_sub_hover(self, tag):
        # Find the circle within the tag
        items = self.canvas.find_withtag(tag)
        for item in items:
            if self.canvas.type(item) == "oval":  # Only modify the circle, not the text
                self.canvas.itemconfig(item,
                                     outline=self.colors['sub']['hover_outline'],
                                     width=3)

    def on_sub_leave(self, tag):
        items = self.canvas.find_withtag(tag)
        for item in items:
            if self.canvas.type(item) == "oval":
                self.canvas.itemconfig(item,
                                     outline=self.colors['sub']['outline'],
                                     width=1)

    # Add new hover methods for secondary circles
    def on_secondary_hover(self, tag):
        items = self.canvas.find_withtag(tag)
        for item in items:
            if self.canvas.type(item) == "oval":
                self.canvas.itemconfig(item,
                                     outline=self.colors['secondary']['hover_outline'],
                                     width=3)

    def on_secondary_leave(self, tag):
        items = self.canvas.find_withtag(tag)
        for item in items:
            if self.canvas.type(item) == "oval":
                self.canvas.itemconfig(item,
                                     outline=self.colors['secondary']['outline'],
                                     width=1)

    def on_secondary_circle_click(self, label):
        # Update path for secondary circle and print
        self.current_path = self.current_path[:2] + [label.replace('\n', ' ')]
        print(", ".join(self.current_path))

    def create_main_circle(self):
        # Calculate center coordinates
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        radius = 50  # or whatever radius you're using

        # Create circle using center coordinates
        self.main_circle = self.canvas.create_oval(
            center_x - radius,  # x1
            center_y - radius,  # y1
            center_x + radius,  # x2
            center_y + radius,  # y2
            fill=self.colors['main']['fill'],
            outline=self.colors['main']['outline'],
            tags="main"
        )

        # Center the text
        self.canvas.create_text(
            center_x,  # x
            center_y,  # y
            text="Highway",
            tags="main"
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = HighwayGUI(root)
    root.mainloop()
