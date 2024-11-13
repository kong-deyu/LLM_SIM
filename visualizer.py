from graphics import *
from entities import RectangleEntity, CircleEntity, RingEntity

class Visualizer:
    def __init__(self, width: float, height: float, ppm: int, window_title: str = 'CARLO'):
        # width (meters)
        # height (meters)
        # ppm is the number of pixels per meters
        
        self.ppm = ppm
        self.display_width, self.display_height = int(width*ppm), int(height*ppm)
        self.window_created = False
        self.visualized_imgs = []
        self.window_title = window_title
        
        
    def create_window(self, bg_color: str = 'gray80'):
        if not self.window_created or self.win.isClosed():
            # Create main window with custom title
            self.win = GraphWin(self.window_title, self.display_width, self.display_height)
            self.win.setBackground(bg_color)
            self.window_created = True
            self.visualized_imgs = []
            
    def update_agents(self, agents: list):
        new_visualized_imgs = []
        
        # Remove the movable agents from the window
        for imgItem in self.visualized_imgs:
            if imgItem['movable']:
                imgItem['graphics'].undraw()
            else:
                new_visualized_imgs.append({'movable': False, 'graphics': imgItem['graphics']})
                
        # Add the updated movable agents (and the unmovable ones if they were not rendered before)
        for agent in agents:
            if agent.movable or not self.visualized_imgs:
                if isinstance(agent, RectangleEntity):
                    C = [self.ppm*c for c in agent.corners]
                    img = Polygon([Point(c.x, self.display_height-c.y) for c in C])
                elif isinstance(agent, CircleEntity):
                    img = Circle(Point(self.ppm*agent.center.x, self.display_height - self.ppm*agent.center.y), self.ppm*agent.radius)
                elif isinstance(agent, RingEntity):
                    img = CircleRing(Point(self.ppm*agent.center.x, self.display_height - self.ppm*agent.center.y), self.ppm*agent.inner_radius, self.ppm*agent.outer_radius)
                else:
                    raise NotImplementedError
                img.setFill(agent.color)
                img.draw(self.win)
                new_visualized_imgs.append({'movable': agent.movable, 'graphics': img})
                
        self.visualized_imgs = new_visualized_imgs

    def close(self):
        self.window_created = False
        self.win.close()
        self.visualized_imgs = []

    def draw_text(self, text: str, position: tuple):
        if self.window_created:
            # Check if we already have a text object
            existing_text = None
            for img in self.visualized_imgs:
                if isinstance(img['graphics'], Text):
                    existing_text = img
                    break
                    
            if existing_text:
                # Update existing text
                existing_text['graphics'].setText(text)
            else:
                # Create new text object
                text_obj = Text(Point(position[0], position[1]), text)
                text_obj.setSize(20)
                text_obj.setTextColor('black')
                text_obj.draw(self.win)
                self.visualized_imgs.append({'movable': False, 'graphics': text_obj})  # Set movable to False

    def draw_warning(self):
        # Create a compact red rectangle at the top center of the window
        rect_height = 30
        rect_width = 100  # Width to accommodate "BRAKE!" text plus padding
        
        # Center the rectangle horizontally at the top
        x_start = (self.display_width - rect_width) // 2
        warning = Rectangle(Point(x_start, 0), 
                           Point(x_start + rect_width, rect_height))
        warning.setFill('red')
        warning.draw(self.win)
        
        # Add white "BRAKE!" text centered in the rectangle
        warning_text = Text(Point(self.display_width//2, rect_height//2), "BRAKE!")
        warning_text.setTextColor('white')
        warning_text.setSize(16)
        warning_text.setStyle('bold')
        warning_text.draw(self.win)
        
        return (warning, warning_text)  # Return both objects for cleanup