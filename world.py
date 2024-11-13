from agents import Car, Pedestrian, RectangleBuilding
from entities import Entity
from typing import Union
from visualizer import Visualizer
from graphics import Text, Point
import os

class World:
    def __init__(self, dt: float, width: float = 100, height: float = 100, ppm: int = 8):
        self.dynamic_agents = []
        self.static_agents = []
        self.t = 0 # simulation time
        self.dt = dt # simulation time step
        self.width = width # store width
        self.height = height # store height
        self.ppm = ppm # store ppm
        
        # Get the name of the running script
        current_file = os.path.basename(__file__)
        
        # Initialize visualizer with file name as window title
        self.visualizer = Visualizer(width, height, ppm, window_title=current_file)
        
    def add(self, entity: Entity):
        if entity.movable:
            self.dynamic_agents.append(entity)
        else:
            self.static_agents.append(entity)
        
    def tick(self):
        for agent in self.dynamic_agents:
            agent.tick(self.dt)
        self.t += self.dt
    
    def render(self):
        self.visualizer.create_window(bg_color = 'gray')
        self.visualizer.update_agents(self.agents)
        
    @property
    def agents(self):
        return self.static_agents + self.dynamic_agents
        
    def collision_exists(self, agent = None):
        if agent is None:
            for i in range(len(self.dynamic_agents)):
                for j in range(i+1, len(self.dynamic_agents)):
                    if self.dynamic_agents[i].collidable and self.dynamic_agents[j].collidable:
                        if self.dynamic_agents[i].collidesWith(self.dynamic_agents[j]):
                            return True
                for j in range(len(self.static_agents)):
                    if self.dynamic_agents[i].collidable and self.static_agents[j].collidable:
                        if self.dynamic_agents[i].collidesWith(self.static_agents[j]):
                            return True
            return False
            
        if not agent.collidable: return False
        
        for i in range(len(self.agents)):
            if self.agents[i] is not agent and self.agents[i].collidable and agent.collidesWith(self.agents[i]):
                return True
        return False
    
    def close(self):
        self.reset()
        self.static_agents = []
        if self.visualizer.window_created:
            self.visualizer.close()
        
    def reset(self):
        self.dynamic_agents = []
        self.t = 0
    
    def draw_text(self, text: str, position: tuple, size: int = 10, anchor: str = 'center'):
        if self.visualizer.window_created:
            # Create text object at the specified position
            text_obj = Text(Point(position[0], position[1]), text)
            text_obj.setSize(size)  # Set font size
            if anchor == 'center':
                text_obj.setJustify('center')
            text_obj.setTextColor('black')
            text_obj.draw(self.visualizer.win)
            # Store the text object so we can remove it later
            self.visualizer.visualized_imgs.append({'movable': True, 'graphics': text_obj})