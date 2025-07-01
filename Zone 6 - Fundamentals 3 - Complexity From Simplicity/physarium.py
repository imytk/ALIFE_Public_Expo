class EnhancedControlPanel:
    def __init__(self, simulation):
        self.simulation = simulation
        self.root = tk.Tk()
        self.root.title("Physarum Controls - Complexity from Simplicity")
        self.root.geometry("350x500")
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Complexity from Simplicity", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Physarum Slime Mold Simulation", 
                                  font=('Arial', 10))
        subtitle_label.pack(pady=(0, 15)) 

import pygame
import numpy as np
import math
import random
import tkinter as tk
from tkinter import ttk
import threading
import time
from enum import Enum

class InteractionMode(Enum):
    PLACE_FOOD = "place_food"
    REMOVE_FOOD = "remove_food"
    OBSERVE = "observe"

class PhysarumAgent:
    def __init__(self, x, y, angle, width, height):
        self.x = x
        self.y = y
        self.angle = angle
        self.width = width
        self.height = height
        
    def update(self, trail_map, food_map, params):
        """Enhanced agent update with food attraction"""
        sensor_dist = 8
        sensor_angle = 0.5  # radians
        
        # Get three sensor positions (left, forward, right)
        forward_x = self.x + math.cos(self.angle) * sensor_dist
        forward_y = self.y + math.sin(self.angle) * sensor_dist
        
        left_angle = self.angle - sensor_angle
        left_x = self.x + math.cos(left_angle) * sensor_dist
        left_y = self.y + math.sin(left_angle) * sensor_dist
        
        right_angle = self.angle + sensor_angle
        right_x = self.x + math.cos(right_angle) * sensor_dist
        right_y = self.y + math.sin(right_angle) * sensor_dist
        
        # Sample trail and food at each sensor
        def sample_at(x, y):
            x, y = int(max(0, min(self.width - 1, x))), int(max(0, min(self.height - 1, y)))
            trail_strength = trail_map[y, x]
            food_strength = food_map[y, x] * params['food_attraction']
            return trail_strength + food_strength
        
        forward_signal = sample_at(forward_x, forward_y)
        left_signal = sample_at(left_x, left_y)
        right_signal = sample_at(right_x, right_y)
        
        # Decision making
        turn_strength = params['turn_speed']
        if forward_signal > left_signal and forward_signal > right_signal:
            # Continue forward
            pass
        elif left_signal > right_signal:
            # Turn left
            self.angle -= turn_strength
        elif right_signal > left_signal:
            # Turn right
            self.angle += turn_strength
        else:
            # Random turn when equal
            self.angle += random.uniform(-turn_strength, turn_strength)
        
        # Add some randomness
        self.angle += random.uniform(-params['randomness'], params['randomness'])
        
        # Move forward
        self.x += math.cos(self.angle) * params['agent_speed']
        self.y += math.sin(self.angle) * params['agent_speed']
        
        # Wrap boundaries
        if self.x < 0: self.x = self.width - 1
        if self.x >= self.width: self.x = 0
        if self.y < 0: self.y = self.height - 1
        if self.y >= self.height: self.y = 0
    
    def deposit_trail(self, trail_map, amount):
        """Deposit trail at current position"""
        x, y = int(self.x), int(self.y)
        if 0 <= x < self.width and 0 <= y < self.height:
            trail_map[y, x] = min(255, trail_map[y, x] + amount)

class PhysarumSimulation:
    def __init__(self, width=1200, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Enhanced Physarum Simulation - Complexity from Simplicity")
        self.clock = pygame.time.Clock()
        
        # Create maps
        self.trail_map = np.zeros((height, width), dtype=np.float32)
        self.food_map = np.zeros((height, width), dtype=np.float32)
        
        # Enhanced parameters - optimized
        self.params = {
            'num_agents': 250,  # Reduced from 300
            'agent_speed': 0.8,
            'turn_speed': 0.2,
            'randomness': 0.05,
            'deposit_amount': 3.0,
            'decay_rate': 0.996,  # Slightly faster decay
            'food_attraction': 5.0,
            'show_agents': True,
            'show_food': True,
            'color_mode': 'plasma',
            'trail_intensity': 1.2  # Reduced from 1.5
        }
        
        # Food sources and interaction
        self.food_sources = []
        self.interaction_mode = InteractionMode.PLACE_FOOD
        self.drawing = False
        
        # Create agents
        self.agents = []
        self.create_agents()
        
        # Add initial food sources for demo
        self.add_demo_food()
        
        # Control state
        self.running = True
        self.paused = False
        
        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.last_time = time.time()
        
        # Color palettes
        self.color_palettes = {
            'plasma': self.create_plasma_palette(),
            'fire': self.create_fire_palette(),
            'ocean': self.create_ocean_palette(),
            'forest': self.create_forest_palette()
        }
    
    def create_plasma_palette(self):
        """Create beautiful plasma color palette"""
        palette = []
        for i in range(256):
            t = i / 255.0
            r = int(255 * max(0, min(1, 0.5 + 0.5 * math.sin(2 * math.pi * t + 0))))
            g = int(255 * max(0, min(1, 0.5 + 0.5 * math.sin(2 * math.pi * t + 2))))
            b = int(255 * max(0, min(1, 0.5 + 0.5 * math.sin(2 * math.pi * t + 4))))
            palette.append((r, g, b))
        return palette
    
    def create_fire_palette(self):
        """Create fire color palette"""
        palette = []
        for i in range(256):
            t = i / 255.0
            if t < 0.25:
                r, g, b = int(t * 4 * 255), 0, 0
            elif t < 0.5:
                r, g, b = 255, int((t - 0.25) * 4 * 255), 0
            elif t < 0.75:
                r, g, b = 255, 255, int((t - 0.5) * 4 * 128)
            else:
                r, g, b = 255, 255, int(128 + (t - 0.75) * 4 * 127)
            palette.append((r, g, b))
        return palette
    
    def create_ocean_palette(self):
        """Create ocean color palette"""
        palette = []
        for i in range(256):
            t = i / 255.0
            r = int(255 * t * 0.3)
            g = int(255 * t * 0.8)
            b = int(255 * (0.4 + t * 0.6))
            palette.append((r, g, b))
        return palette
    
    def create_forest_palette(self):
        """Create forest color palette"""
        palette = []
        for i in range(256):
            t = i / 255.0
            r = int(255 * t * 0.6)
            g = int(255 * (0.3 + t * 0.7))
            b = int(255 * t * 0.4)
            palette.append((r, g, b))
        return palette
    
    def add_demo_food(self):
        """Add some initial food sources for immediate visual impact"""
        self.food_sources = [
            (200, 150),
            (600, 150),
            (400, 450),
            (150, 400),
            (650, 400)
        ]
    
    def update_food_map(self):
        """Optimized food map update"""
        self.food_map.fill(0)
        for food_x, food_y in self.food_sources:
            # Smaller, more efficient food influence area
            radius = 30  # Reduced from 40
            strength = 50
            x_start = max(0, int(food_x - radius))
            x_end = min(self.width, int(food_x + radius))
            y_start = max(0, int(food_y - radius))
            y_end = min(self.height, int(food_y + radius))
            
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    dx = x - food_x
                    dy = y - food_y
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance <= radius:
                        # Simpler falloff calculation
                        value = strength * (1 - distance/radius)
                        self.food_map[y, x] = max(self.food_map[y, x], value)
        
    def create_agents(self):
        """Create agents around food sources or in center"""
        self.agents = []
        
        if len(self.food_sources) > 0:
            # Spawn agents near food sources
            agents_per_food = self.params['num_agents'] // len(self.food_sources)
            remaining_agents = self.params['num_agents'] % len(self.food_sources)
            
            for i, (food_x, food_y) in enumerate(self.food_sources):
                agent_count = agents_per_food + (1 if i < remaining_agents else 0)
                for _ in range(agent_count):
                    x = food_x + random.uniform(-30, 30)
                    y = food_y + random.uniform(-30, 30)
                    x = max(0, min(self.width - 1, x))
                    y = max(0, min(self.height - 1, y))
                    angle = random.uniform(0, 2 * math.pi)
                    agent = PhysarumAgent(x, y, angle, self.width, self.height)
                    self.agents.append(agent)
        else:
            # Spawn in center if no food
            center_x, center_y = self.width // 2, self.height // 2
            for _ in range(self.params['num_agents']):
                x = center_x + random.uniform(-50, 50)
                y = center_y + random.uniform(-50, 50)
                x = max(0, min(self.width - 1, x))
                y = max(0, min(self.height - 1, y))
                angle = random.uniform(0, 2 * math.pi)
                agent = PhysarumAgent(x, y, angle, self.width, self.height)
                self.agents.append(agent)
    
    def update_simulation(self):
        """Enhanced simulation update"""
        if self.paused:
            return
        
        # Update food map
        self.update_food_map()
        
        # Update agents with enhanced behavior
        for agent in self.agents:
            agent.update(self.trail_map, self.food_map, self.params)
            agent.deposit_trail(self.trail_map, self.params['deposit_amount'])
        
        # Apply trail decay
        self.trail_map *= self.params['decay_rate']
    
    def get_trail_color(self, intensity):
        """Get color for trail intensity using selected palette"""
        intensity = max(0, min(1, intensity * self.params['trail_intensity']))
        color_index = int(intensity * 255)
        color_index = max(0, min(255, color_index))
        palette = self.color_palettes[self.params['color_mode']]
        return palette[color_index]
    
    def draw_simulation(self):
        """Enhanced drawing with beautiful graphics - restored"""
        self.screen.fill((0, 0, 0))
        
        # Draw trails with enhanced graphics
        max_trail = np.max(self.trail_map)
        if max_trail > 0.1:
            # Find all pixels with significant trails
            trail_positions = np.where(self.trail_map > max_trail * 0.05)
            
            # Limit number of pixels drawn for performance
            num_pixels = min(2000, len(trail_positions[0]))  # Reasonable limit
            indices = np.random.choice(len(trail_positions[0]), num_pixels, replace=False) if len(trail_positions[0]) > num_pixels else range(len(trail_positions[0]))
            
            for i in indices:
                y, x = trail_positions[0][i], trail_positions[1][i]
                intensity = self.trail_map[y, x] / max_trail
                color = self.get_trail_color(intensity)
                
                # Draw slightly larger pixels for better visibility
                if intensity > 0.4:
                    pygame.draw.rect(self.screen, color, (x-1, y-1, 3, 3))
                else:
                    self.screen.set_at((x, y), color)
        
        # Draw food sources with attractive graphics - simplified but still beautiful
        if self.params['show_food']:
            for food_x, food_y in self.food_sources:
                # Simplified glow - just 2 layers instead of many
                pygame.draw.circle(self.screen, (255, 200, 0), (int(food_x), int(food_y)), 18, 2)
                pygame.draw.circle(self.screen, (255, 255, 0), (int(food_x), int(food_y)), 12)
                pygame.draw.circle(self.screen, (255, 255, 150), (int(food_x), int(food_y)), 8)
                pygame.draw.circle(self.screen, (255, 255, 200), (int(food_x), int(food_y)), 4)
        
        # Draw agents as small glowing dots
        if self.params['show_agents']:
            for agent in self.agents[::3]:  # Draw every 3rd agent for performance
                x, y = int(agent.x), int(agent.y)
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Simple agent rendering
                    pygame.draw.circle(self.screen, (150, 150, 255), (x, y), 1)
        
        # Draw enhanced UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        """Draw enhanced user interface"""
        # Create semi-transparent background for UI
        ui_surface = pygame.Surface((self.width, 90), pygame.SRCALPHA)
        pygame.draw.rect(ui_surface, (0, 0, 0, 150), (0, 0, self.width, 90))
        self.screen.blit(ui_surface, (0, 0))
        
        font = pygame.font.Font(None, 32)
        font_small = pygame.font.Font(None, 20)
        
        # Main status
        status = "RUNNING" if not self.paused else "PAUSED"
        main_text = f"FPS: {self.fps:.1f} | Agents: {len(self.agents)} | Food: {len(self.food_sources)} | {status}"
        text_surface = font.render(main_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))
        
        # Current mode
        mode_text = f"Mode: {self.interaction_mode.value.replace('_', ' ').title()} | Color: {self.params['color_mode'].title()}"
        mode_surface = font_small.render(mode_text, True, (200, 200, 200))
        self.screen.blit(mode_surface, (10, 40))
        
        # Controls
        controls = [
            "SPACE: Pause | R: Reset | C: Clear | 1-3: Modes | Mouse: Place/Remove Food",
            "+/-: Agents | TAB: Colors | Demo shows: Simple Rules → Complex Networks"
        ]
        
        for i, control in enumerate(controls):
            text = font_small.render(control, True, (180, 180, 180))
            self.screen.blit(text, (10, 60 + i * 15))
    
    def draw_ui(self):
        """Draw enhanced user interface"""
        # Create semi-transparent background for UI
        ui_surface = pygame.Surface((self.width, 100), pygame.SRCALPHA)
        pygame.draw.rect(ui_surface, (0, 0, 0, 150), (0, 0, self.width, 100))
        self.screen.blit(ui_surface, (0, 0))
        
        font = pygame.font.Font(None, 32)
        font_small = pygame.font.Font(None, 20)
        
        # Main status
        status = "RUNNING" if not self.paused else "PAUSED"
        main_text = f"FPS: {self.fps:.1f} | Agents: {len(self.agents)} | Food: {len(self.food_sources)} | {status}"
        text_surface = font.render(main_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))
        
        # Current mode
        mode_text = f"Mode: {self.interaction_mode.value.replace('_', ' ').title()} | Color: {self.params['color_mode'].title()}"
        mode_surface = font_small.render(mode_text, True, (200, 200, 200))
        self.screen.blit(mode_surface, (10, 40))
        
        # Controls
        controls = [
            "SPACE: Pause | R: Reset | C: Clear Trails | 1-3: Modes",
            "Mouse: Place/Remove Food | +/-: Agents | Tab: Color Mode"
        ]
        
        for i, control in enumerate(controls):
            text = font_small.render(control, True, (180, 180, 180))
            self.screen.blit(text, (10, 60 + i * 15))
    
    def handle_mouse_input(self):
        """Handle mouse interactions for food placement"""
        if self.drawing:
            mouse_pos = pygame.mouse.get_pos()
            x, y = mouse_pos
            
            if self.interaction_mode == InteractionMode.PLACE_FOOD:
                # Check if not too close to existing food
                min_distance = 60
                too_close = any(math.sqrt((x - fx)**2 + (y - fy)**2) < min_distance 
                               for fx, fy in self.food_sources)
                if not too_close and len(self.food_sources) < 10:
                    self.food_sources.append((x, y))
                    
            elif self.interaction_mode == InteractionMode.REMOVE_FOOD:
                # Remove nearby food sources
                self.food_sources = [(fx, fy) for fx, fy in self.food_sources
                                   if math.sqrt((x - fx)**2 + (y - fy)**2) > 40]
    
    def handle_events(self):
        """Enhanced event handling"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.trail_map.fill(0)
                    self.create_agents()
                elif event.key == pygame.K_c:
                    self.trail_map.fill(0)
                elif event.key == pygame.K_1:
                    self.interaction_mode = InteractionMode.PLACE_FOOD
                elif event.key == pygame.K_2:
                    self.interaction_mode = InteractionMode.REMOVE_FOOD
                elif event.key == pygame.K_3:
                    self.interaction_mode = InteractionMode.OBSERVE
                elif event.key == pygame.K_TAB:
                    # Cycle through color modes
                    modes = list(self.color_palettes.keys())
                    current_idx = modes.index(self.params['color_mode'])
                    next_idx = (current_idx + 1) % len(modes)
                    self.params['color_mode'] = modes[next_idx]
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    if len(self.agents) < 1000:
                        for _ in range(20):
                            if len(self.food_sources) > 0:
                                food_x, food_y = random.choice(self.food_sources)
                                x = food_x + random.uniform(-40, 40)
                                y = food_y + random.uniform(-40, 40)
                            else:
                                x = random.uniform(0, self.width)
                                y = random.uniform(0, self.height)
                            x = max(0, min(self.width - 1, x))
                            y = max(0, min(self.height - 1, y))
                            angle = random.uniform(0, 2 * math.pi)
                            agent = PhysarumAgent(x, y, angle, self.width, self.height)
                            self.agents.append(agent)
                        self.params['num_agents'] = len(self.agents)
                elif event.key == pygame.K_MINUS:
                    if len(self.agents) > 50:
                        self.agents = self.agents[:-20]
                        self.params['num_agents'] = len(self.agents)
                        
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.drawing = True
                    self.handle_mouse_input()
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.drawing = False
                    
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_input()
        
        return True
    
    def update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_time)
            self.frame_count = 0
            self.last_time = current_time
    
    def run(self):
        """Main loop"""
        while self.running:
            if not self.handle_events():
                break
            
            self.update_simulation()
            self.draw_simulation()
            self.update_fps()
            self.clock.tick(60)  # Target 60 FPS
        
        pygame.quit()

class EnhancedControlPanel:
    def __init__(self, simulation):
        self.simulation = simulation
        self.root = tk.Tk()
        self.root.title("Physarum Controls - Complexity from Simplicity")
        self.root.geometry("350x500")
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Complexity from Simplicity", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Physarum Slime Mold Simulation", 
                                  font=('Arial', 10))
        subtitle_label.pack(pady=(0, 15))
        
        # Agent controls
        ttk.Label(main_frame, text="Agents:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.num_agents_var = tk.IntVar(value=len(self.simulation.agents))
        agents_scale = ttk.Scale(main_frame, from_=50, to=800, variable=self.num_agents_var,
                                command=self.update_agents, orient=tk.HORIZONTAL)
        agents_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Speed
        ttk.Label(main_frame, text="Agent Speed:").pack(anchor=tk.W)
        self.speed_var = tk.DoubleVar(value=self.simulation.params['agent_speed'])
        speed_scale = ttk.Scale(main_frame, from_=0.1, to=2.0, variable=self.speed_var,
                               command=self.update_speed, orient=tk.HORIZONTAL)
        speed_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Trail strength
        ttk.Label(main_frame, text="Trail Strength:").pack(anchor=tk.W)
        self.deposit_var = tk.DoubleVar(value=self.simulation.params['deposit_amount'])
        deposit_scale = ttk.Scale(main_frame, from_=1.0, to=10.0, variable=self.deposit_var,
                                 command=self.update_deposit, orient=tk.HORIZONTAL)
        deposit_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Food attraction
        ttk.Label(main_frame, text="Food Attraction:").pack(anchor=tk.W)
        self.food_attraction_var = tk.DoubleVar(value=self.simulation.params['food_attraction'])
        food_scale = ttk.Scale(main_frame, from_=0.0, to=10.0, variable=self.food_attraction_var,
                              command=self.update_food_attraction, orient=tk.HORIZONTAL)
        food_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Trail persistence
        ttk.Label(main_frame, text="Trail Persistence:").pack(anchor=tk.W)
        self.decay_var = tk.DoubleVar(value=self.simulation.params['decay_rate'])
        decay_scale = ttk.Scale(main_frame, from_=0.98, to=0.999, variable=self.decay_var,
                               command=self.update_decay, orient=tk.HORIZONTAL)
        decay_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Color mode
        ttk.Label(main_frame, text="Color Palette:").pack(anchor=tk.W)
        self.color_var = tk.StringVar(value=self.simulation.params['color_mode'])
        color_combo = ttk.Combobox(main_frame, textvariable=self.color_var,
                                  values=['plasma', 'fire', 'ocean', 'forest'],
                                  state="readonly")
        color_combo.bind('<<ComboboxSelected>>', self.update_color)
        color_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Control buttons
        button_frame1 = ttk.Frame(main_frame)
        button_frame1.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame1, text="Pause/Play", 
                  command=self.toggle_pause).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame1, text="Reset", 
                  command=self.reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame1, text="Clear Trails", 
                  command=self.clear_trails).pack(side=tk.LEFT, padx=5)
        
        # Food buttons
        button_frame2 = ttk.Frame(main_frame)
        button_frame2.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame2, text="Add Food", 
                  command=self.add_random_food).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame2, text="Clear Food", 
                  command=self.clear_food).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame2, text="Demo Setup", 
                  command=self.demo_setup).pack(side=tk.LEFT, padx=5)
        
        # Mode selection
        ttk.Label(main_frame, text="Mouse Mode:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(15, 5))
        
        self.mode_var = tk.StringVar(value=self.simulation.interaction_mode.value)
        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(mode_frame, text="Place Food", variable=self.mode_var,
                       value="place_food", command=self.update_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Remove Food", variable=self.mode_var,
                       value="remove_food", command=self.update_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Observe", variable=self.mode_var,
                       value="observe", command=self.update_mode).pack(anchor=tk.W)
        
        # Instructions
        instructions_text = """
How it works:
• Each agent follows 3 simple rules:
  1. Sense chemical trails ahead
  2. Turn toward strongest signal  
  3. Deposit trail behind

• Simple rules → Complex networks!
• Place food and watch adaptation
• Perfect demo of emergence

Controls:
• Mouse: Place/remove food sources
• SPACE: Pause simulation
• +/-: Add/remove agents
• TAB: Change colors
        """
        
        instructions_label = ttk.Label(main_frame, text=instructions_text, 
                                     justify=tk.LEFT, font=('Arial', 8))
        instructions_label.pack(pady=(15, 0), fill=tk.BOTH)
    
    def update_agents(self, value):
        target = int(float(value))
        current = len(self.simulation.agents)
        
        if target > current:
            for _ in range(target - current):
                if len(self.simulation.food_sources) > 0:
                    food_x, food_y = random.choice(self.simulation.food_sources)
                    x = food_x + random.uniform(-40, 40)
                    y = food_y + random.uniform(-40, 40)
                else:
                    x = random.uniform(0, self.simulation.width)
                    y = random.uniform(0, self.simulation.height)
                x = max(0, min(self.simulation.width - 1, x))
                y = max(0, min(self.simulation.height - 1, y))
                angle = random.uniform(0, 2 * math.pi)
                agent = PhysarumAgent(x, y, angle, self.simulation.width, self.simulation.height)
                self.simulation.agents.append(agent)
        elif target < current:
            self.simulation.agents = self.simulation.agents[:target]
        
        self.simulation.params['num_agents'] = target
    
    def update_speed(self, value):
        self.simulation.params['agent_speed'] = float(value)
    
    def update_deposit(self, value):
        self.simulation.params['deposit_amount'] = float(value)
    
    def update_food_attraction(self, value):
        self.simulation.params['food_attraction'] = float(value)
    
    def update_decay(self, value):
        self.simulation.params['decay_rate'] = float(value)
    
    def update_color(self, event=None):
        self.simulation.params['color_mode'] = self.color_var.get()
    
    def update_mode(self):
        mode_str = self.mode_var.get()
        for mode in InteractionMode:
            if mode.value == mode_str:
                self.simulation.interaction_mode = mode
                break
    
    def toggle_pause(self):
        self.simulation.paused = not self.simulation.paused
    
    def reset(self):
        self.simulation.trail_map.fill(0)
        self.simulation.create_agents()
    
    def clear_trails(self):
        self.simulation.trail_map.fill(0)
    
    def clear_food(self):
        self.simulation.food_sources.clear()
    
    def add_random_food(self):
        if len(self.simulation.food_sources) < 8:
            x = random.uniform(100, self.simulation.width - 100)
            y = random.uniform(100, self.simulation.height - 100)
            self.simulation.food_sources.append((x, y))
    
    def demo_setup(self):
        """Perfect setup for expo demonstration"""
        self.simulation.trail_map.fill(0)
        self.simulation.food_sources.clear()
        self.simulation.add_demo_food()
        self.simulation.create_agents()
        self.color_var.set('plasma')
        self.simulation.params['color_mode'] = 'plasma'
        self.num_agents_var.set(400)
        self.update_agents(400)

def run_enhanced_physarum():
    print("Starting Enhanced Physarum Simulation")
    print("='Complexity from Simplicity' Demo=")
    print("\nDemonstrates emergent intelligence from simple rules:")
    print("• Each agent: Sense → Turn → Deposit")
    print("• Result: Intelligent network formation")
    print("\nControls:")
    print("  Mouse: Place/remove food (modes 1-3)")
    print("  SPACE: Pause/Resume")
    print("  +/-: Add/Remove agents")
    print("  TAB: Cycle color palettes")
    print("  R: Reset, C: Clear trails")
    print("\nPerfect for demonstrating emergence!")
    
    simulation = PhysarumSimulation()
    
    # Start control panel in thread
    def control_thread():
        try:
            control = EnhancedControlPanel(simulation)
            control.root.mainloop()
        except Exception as e:
            print(f"Control panel error: {e}")
    
    threading.Thread(target=control_thread, daemon=True).start()
    
    # Run simulation
    try:
        simulation.run()
    except Exception as e:
        print(f"Simulation error: {e}")

if __name__ == "__main__":
    run_enhanced_physarum()
    def __init__(self, simulation):
        self.simulation = simulation
        self.root = tk.Tk()
        self.root.title("Simple Controls")
        self.root.geometry("300x400")
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Simple Physarum Controls", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 20))
        
        # Agent count
        ttk.Label(main_frame, text="Agents:").pack(anchor=tk.W)
        self.num_agents_var = tk.IntVar(value=len(self.simulation.agents))
        agents_scale = ttk.Scale(main_frame, from_=50, to=500, variable=self.num_agents_var,
                                command=self.update_agents, orient=tk.HORIZONTAL)
        agents_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Speed
        ttk.Label(main_frame, text="Speed:").pack(anchor=tk.W)
        self.speed_var = tk.DoubleVar(value=self.simulation.params['agent_speed'])
        speed_scale = ttk.Scale(main_frame, from_=0.1, to=2.0, variable=self.speed_var,
                               command=self.update_speed, orient=tk.HORIZONTAL)
        speed_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Deposit
        ttk.Label(main_frame, text="Trail Strength:").pack(anchor=tk.W)
        self.deposit_var = tk.DoubleVar(value=self.simulation.params['deposit_amount'])
        deposit_scale = ttk.Scale(main_frame, from_=0.5, to=10.0, variable=self.deposit_var,
                                 command=self.update_deposit, orient=tk.HORIZONTAL)
        deposit_scale.pack(fill=tk.X, pady=(0, 10))
        
        # Decay
        ttk.Label(main_frame, text="Trail Persistence:").pack(anchor=tk.W)
        self.decay_var = tk.DoubleVar(value=self.simulation.params['decay_rate'])
        decay_scale = ttk.Scale(main_frame, from_=0.95, to=0.999, variable=self.decay_var,
                               command=self.update_decay, orient=tk.HORIZONTAL)
        decay_scale.pack(fill=tk.X, pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Pause/Play", 
                  command=self.toggle_pause).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset", 
                  command=self.reset).pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = """
Instructions:
• Mouse: Click and drag to attract agents
• +/-: Add/remove agents
• SPACE: Pause
• R: Reset

This demonstrates how simple rules
create complex emergent behavior!
        """
        
        ttk.Label(main_frame, text=instructions, justify=tk.LEFT,
                 font=('Arial', 9)).pack(pady=(20, 0))
    
    def update_agents(self, value):
        target = int(float(value))
        current = len(self.simulation.agents)
        
        if target > current:
            for _ in range(target - current):
                x = random.uniform(0, self.simulation.width)
                y = random.uniform(0, self.simulation.height)
                angle = random.uniform(0, 2 * math.pi)
                agent = PhysarumAgent(x, y, angle, self.simulation.width, self.simulation.height)
                self.simulation.agents.append(agent)
        elif target < current:
            self.simulation.agents = self.simulation.agents[:target]
    
    def update_speed(self, value):
        self.simulation.params['agent_speed'] = float(value)
    
    def update_deposit(self, value):
        self.simulation.params['deposit_amount'] = float(value)
    
    def update_decay(self, value):
        self.simulation.params['decay_rate'] = float(value)
    
    def toggle_pause(self):
        self.simulation.paused = not self.simulation.paused
    
    def reset(self):
        self.simulation.trail_map.fill(0)
        self.simulation.create_agents()

def run_simple_physarum():
    print("Starting Simple Physarum Simulation...")
    print("This is a minimal version optimized for performance.")
    print("Controls:")
    print("  Mouse: Click to attract agents")
    print("  SPACE: Pause/Resume")
    print("  R: Reset")
    print("  +/-: Add/Remove agents")
    
    simulation = PhysarumSimulation()
    
    # Start control panel in thread
    def control_thread():
        try:
            control = SimpleControlPanel(simulation)
            control.root.mainloop()
        except:
            pass
    
    threading.Thread(target=control_thread, daemon=True).start()
    
    # Run simulation
    simulation.run()

if __name__ == "__main__":
    run_simple_physarum()