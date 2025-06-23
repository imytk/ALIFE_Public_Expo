import pygame
import math
import random
import tkinter as tk
from tkinter import ttk
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

class Vector2D:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar):
        if scalar != 0:
            return Vector2D(self.x / scalar, self.y / scalar)
        return Vector2D(0, 0)
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def magnitude_squared(self):
        # Faster than magnitude() when we only need to compare distances
        return self.x**2 + self.y**2
    
    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return self / mag
        return Vector2D(0, 0)
    
    def limit(self, max_val):
        mag_sq = self.magnitude_squared()
        if mag_sq > max_val * max_val:
            mag = math.sqrt(mag_sq)
            return self / mag * max_val
        return self
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def distance_squared_to(self, other):
        # Faster distance comparison without square root
        return (self.x - other.x)**2 + (self.y - other.y)**2

class SpatialGrid:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = int(width / cell_size) + 1
        self.rows = int(height / cell_size) + 1
        self.grid = defaultdict(list)
    
    def clear(self):
        self.grid.clear()
    
    def get_cell_key(self, x, y):
        col = max(0, min(int(x / self.cell_size), self.cols - 1))
        row = max(0, min(int(y / self.cell_size), self.rows - 1))
        return (col, row)
    
    def add_boid(self, boid):
        key = self.get_cell_key(boid.position.x, boid.position.y)
        self.grid[key].append(boid)
    
    def get_nearby_boids(self, boid, radius):
        # Get all boids in the current cell and neighboring cells
        nearby_boids = []
        center_key = self.get_cell_key(boid.position.x, boid.position.y)
        
        # Check 3x3 grid around the boid's cell
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                col = center_key[0] + dx
                row = center_key[1] + dy
                
                if 0 <= col < self.cols and 0 <= row < self.rows:
                    cell_key = (col, row)
                    if cell_key in self.grid:
                        # Pre-filter by distance squared for performance
                        radius_sq = radius * radius
                        for other_boid in self.grid[cell_key]:
                            if other_boid != boid:
                                dist_sq = boid.position.distance_squared_to(other_boid.position)
                                if dist_sq <= radius_sq:
                                    nearby_boids.append((other_boid, math.sqrt(dist_sq)))
        
        return nearby_boids

class Boid:
    def __init__(self, x, y, width, height):
        self.position = Vector2D(x, y)
        self.velocity = Vector2D(random.uniform(-2, 2), random.uniform(-2, 2))
        self.acceleration = Vector2D(0, 0)
        self.max_speed = 4
        self.max_force = 0.1
        self.width = width
        self.height = height
        self.size = 8
        
        # Cached forces for threading
        self.cached_separation = Vector2D(0, 0)
        self.cached_alignment = Vector2D(0, 0)
        self.cached_cohesion = Vector2D(0, 0)
        
    def update(self):
        # Update velocity and position
        self.velocity = self.velocity + self.acceleration
        self.velocity = self.velocity.limit(self.max_speed)
        self.position = self.position + self.velocity
        self.acceleration = Vector2D(0, 0)  # Reset acceleration
        
        # Wrap around screen edges
        if self.position.x < 0:
            self.position.x = self.width
        elif self.position.x > self.width:
            self.position.x = 0
            
        if self.position.y < 0:
            self.position.y = self.height
        elif self.position.y > self.height:
            self.position.y = 0
    
    def apply_cached_forces(self, params):
        # Apply the cached forces calculated in separate threads
        sep = self.cached_separation * params['separation_weight']
        ali = self.cached_alignment * params['alignment_weight']
        coh = self.cached_cohesion * params['cohesion_weight']
        
        self.acceleration = self.acceleration + sep + ali + coh
    
    def seek(self, target):
        # Steering force towards target
        desired = target - self.position
        desired = desired.normalize() * self.max_speed
        steer = desired - self.velocity
        return steer.limit(self.max_force)
    
    def separate(self, nearby_boids, separation_radius):
        steer = Vector2D(0, 0)
        count = 0
        
        for other_boid, distance in nearby_boids:
            if distance < separation_radius and distance > 0:
                diff = self.position - other_boid.position
                diff = diff.normalize()
                diff = diff / distance  # Weight by distance
                steer = steer + diff
                count += 1
        
        if count > 0:
            steer = steer / count
            steer = steer.normalize() * self.max_speed
            steer = steer - self.velocity
            steer = steer.limit(self.max_force)
        
        return steer
    
    def align(self, nearby_boids, alignment_radius):
        sum_velocity = Vector2D(0, 0)
        count = 0
        
        for other_boid, distance in nearby_boids:
            if distance < alignment_radius and distance > 0:
                sum_velocity = sum_velocity + other_boid.velocity
                count += 1
        
        if count > 0:
            sum_velocity = sum_velocity / count
            sum_velocity = sum_velocity.normalize() * self.max_speed
            steer = sum_velocity - self.velocity
            return steer.limit(self.max_force)
        
        return Vector2D(0, 0)
    
    def cohesion(self, nearby_boids, cohesion_radius):
        sum_position = Vector2D(0, 0)
        count = 0
        
        for other_boid, distance in nearby_boids:
            if distance < cohesion_radius and distance > 0:
                sum_position = sum_position + other_boid.position
                count += 1
        
        if count > 0:
            sum_position = sum_position / count
            return self.seek(sum_position)
        
        return Vector2D(0, 0)
    
    def calculate_forces(self, spatial_grid, params):
        # Get maximum radius for spatial grid query
        max_radius = max(params['separation_radius'], 
                        params['alignment_radius'], 
                        params['cohesion_radius'])
        
        nearby_boids = spatial_grid.get_nearby_boids(self, max_radius)
        
        # Calculate and cache forces
        self.cached_separation = self.separate(nearby_boids, params['separation_radius'])
        self.cached_alignment = self.align(nearby_boids, params['alignment_radius'])
        self.cached_cohesion = self.cohesion(nearby_boids, params['cohesion_radius'])
    
    def draw(self, screen):
        # Calculate heading angle
        angle = math.atan2(self.velocity.y, self.velocity.x)
        
        # Triangle points representing the boid
        points = []
        # Front point
        front_x = self.position.x + math.cos(angle) * self.size
        front_y = self.position.y + math.sin(angle) * self.size
        points.append((front_x, front_y))
        
        # Back left point
        back_left_x = self.position.x + math.cos(angle + 2.5) * (self.size * 0.6)
        back_left_y = self.position.y + math.sin(angle + 2.5) * (self.size * 0.6)
        points.append((back_left_x, back_left_y))
        
        # Back right point
        back_right_x = self.position.x + math.cos(angle - 2.5) * (self.size * 0.6)
        back_right_y = self.position.y + math.sin(angle - 2.5) * (self.size * 0.6)
        points.append((back_right_x, back_right_y))
        
        pygame.draw.polygon(screen, (255, 255, 255), points)

def calculate_boid_forces_batch(boids_batch, spatial_grid, params):
    """Calculate forces for a batch of boids in a separate thread"""
    for boid in boids_batch:
        boid.calculate_forces(spatial_grid, params)

class BoidSimulation:
    def __init__(self, width=1200, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Optimized Boids Simulation - Spatial Grid + Multi-threading")
        self.clock = pygame.time.Clock()
        
        # Initialize parameters
        self.params = {
            'separation_weight': 1.5,
            'alignment_weight': 1.0,
            'cohesion_weight': 1.0,
            'separation_radius': 25,
            'alignment_radius': 50,
            'cohesion_radius': 50,
            'max_speed': 4,
            'max_force': 0.1,
            'num_boids': 100,
            'num_threads': 4,  # Number of threads for parallel processing
            'grid_cell_size': 50  # Size of spatial grid cells
        }
        
        # Create spatial grid
        self.spatial_grid = SpatialGrid(width, height, self.params['grid_cell_size'])
        
        # Thread pool for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=self.params['num_threads'])
        self.recreate_thread_pool = False  # Flag to safely recreate thread pool
        
        # Create boids
        self.boids = []
        self.create_boids()
        
        # Performance tracking
        self.frame_times = []
        self.last_time = time.time()
        
        # Control flags
        self.running = True
        self.paused = False
        
    def create_boids(self):
        self.boids = []
        for _ in range(self.params['num_boids']):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            boid = Boid(x, y, self.width, self.height)
            boid.max_speed = self.params['max_speed']
            boid.max_force = self.params['max_force']
            self.boids.append(boid)
    
    def update_boid_params(self):
        for boid in self.boids:
            boid.max_speed = self.params['max_speed']
            boid.max_force = self.params['max_force']
    
    def update_spatial_grid(self):
        """Update spatial grid cell size if needed"""
        max_radius = max(self.params['separation_radius'], 
                        self.params['alignment_radius'], 
                        self.params['cohesion_radius'])
        
        # Optimal cell size is roughly 2x the maximum perception radius
        optimal_cell_size = max_radius * 2
        
        if abs(self.spatial_grid.cell_size - optimal_cell_size) > 10:
            self.spatial_grid = SpatialGrid(self.width, self.height, optimal_cell_size)
            self.params['grid_cell_size'] = optimal_cell_size
    
    def update(self):
        if not self.paused:
            start_time = time.time()
            
            # Safely recreate thread pool if needed
            if self.recreate_thread_pool:
                self.thread_pool.shutdown(wait=True)
                self.thread_pool = ThreadPoolExecutor(max_workers=self.params['num_threads'])
                self.recreate_thread_pool = False
            
            self.update_boid_params()
            self.update_spatial_grid()
            
            # Clear and populate spatial grid
            self.spatial_grid.clear()
            for boid in self.boids:
                self.spatial_grid.add_boid(boid)
            
            # Divide boids into batches for parallel processing
            num_threads = min(self.params['num_threads'], len(self.boids))
            if num_threads > 1 and len(self.boids) > 50:  # Only use threading for larger simulations
                batch_size = max(1, len(self.boids) // num_threads)
                batches = []
                
                for i in range(0, len(self.boids), batch_size):
                    batch = self.boids[i:i + batch_size]
                    if batch:  # Only add non-empty batches
                        batches.append(batch)
                
                # Submit batches to thread pool with error handling
                futures = []
                try:
                    for batch in batches:
                        future = self.thread_pool.submit(calculate_boid_forces_batch, 
                                                       batch, self.spatial_grid, self.params)
                        futures.append(future)
                    
                    # Wait for all threads to complete
                    for future in futures:
                        future.result(timeout=1.0)  # Add timeout to prevent hanging
                        
                except Exception as e:
                    print(f"Threading error: {e}")
                    # Fall back to single-threaded processing
                    for boid in self.boids:
                        boid.calculate_forces(self.spatial_grid, self.params)
            else:
                # Single-threaded fallback
                for boid in self.boids:
                    boid.calculate_forces(self.spatial_grid, self.params)
            
            # Apply forces and update positions
            for boid in self.boids:
                boid.apply_cached_forces(self.params)
                boid.update()
            
            # Track performance
            frame_time = time.time() - start_time
            self.frame_times.append(frame_time)
            if len(self.frame_times) > 60:  # Keep last 60 frame times
                self.frame_times.pop(0)
    
    def get_performance_stats(self):
        if not self.frame_times:
            return 0, 0, 0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        min_frame_time = min(self.frame_times)
        max_frame_time = max(self.frame_times)
        
        return avg_frame_time * 1000, min_frame_time * 1000, max_frame_time * 1000  # Convert to ms
    
    def draw(self):
        self.screen.fill((0, 0, 0))  # Black background
        
        for boid in self.boids:
            boid.draw(self.screen)
        
        # Draw performance info
        font = pygame.font.Font(None, 36)
        fps = int(self.clock.get_fps())
        info_text = f"Boids: {len(self.boids)} | FPS: {fps}"
        if self.paused:
            info_text += " | PAUSED"
        text_surface = font.render(info_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))
        
        # Performance stats
        avg_time, min_time, max_time = self.get_performance_stats()
        perf_text = f"Frame Time: {avg_time:.1f}ms avg | Threads: {self.params['num_threads']} | Grid: {self.params['grid_cell_size']}"
        font_small = pygame.font.Font(None, 24)
        perf_surface = font_small.render(perf_text, True, (200, 200, 200))
        self.screen.blit(perf_surface, (10, 45))
        
        # Spatial grid visualization (optional - can be toggled)
        if hasattr(self, 'show_grid') and self.show_grid:
            self.draw_spatial_grid()
        
        # Controls info
        controls = [
            "SPACE: Pause/Resume",
            "R: Reset Boids",
            "G: Toggle Grid Visualization",
            "Use GUI controls to adjust parameters"
        ]
        for i, control in enumerate(controls):
            text = font_small.render(control, True, (150, 150, 150))
            self.screen.blit(text, (10, 80 + i * 20))
        
        pygame.display.flip()
    
    def draw_spatial_grid(self):
        """Draw spatial grid lines for debugging"""
        grid_color = (50, 50, 50)
        cell_size = self.spatial_grid.cell_size
        
        # Draw vertical lines
        for x in range(0, self.width, int(cell_size)):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.height))
        
        # Draw horizontal lines
        for y in range(0, self.height, int(cell_size)):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.width, y))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.create_boids()
                elif event.key == pygame.K_g:
                    self.show_grid = not hasattr(self, 'show_grid') or not self.show_grid
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        
        self.thread_pool.shutdown(wait=True)
        pygame.quit()

class ControlPanel:
    def __init__(self, simulation):
        self.simulation = simulation
        self.root = tk.Tk()
        self.root.title("Optimized Boids Simulation Controls")
        self.root.geometry("450x700")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame with scrollbar
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Optimized Boids Controls", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        row = 1
        
        # Performance section
        ttk.Label(main_frame, text="Performance Settings", 
                 font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=2, pady=(10, 5))
        row += 1
        
        # Number of threads
        ttk.Label(main_frame, text="Number of Threads:").grid(row=row, column=0, sticky=tk.W)
        self.threads_var = tk.IntVar(value=self.simulation.params['num_threads'])
        threads_scale = ttk.Scale(main_frame, from_=1, to=8, variable=self.threads_var,
                                command=self.update_num_threads)
        threads_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Behavior weights
        ttk.Label(main_frame, text="Behavior Weights", 
                 font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=2, pady=(10, 5))
        row += 1
        
        # Separation weight
        ttk.Label(main_frame, text="Separation Weight:").grid(row=row, column=0, sticky=tk.W)
        self.sep_weight_var = tk.DoubleVar(value=self.simulation.params['separation_weight'])
        sep_scale = ttk.Scale(main_frame, from_=0, to=5, variable=self.sep_weight_var,
                             command=self.update_separation_weight)
        sep_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Alignment weight
        ttk.Label(main_frame, text="Alignment Weight:").grid(row=row, column=0, sticky=tk.W)
        self.ali_weight_var = tk.DoubleVar(value=self.simulation.params['alignment_weight'])
        ali_scale = ttk.Scale(main_frame, from_=0, to=5, variable=self.ali_weight_var,
                             command=self.update_alignment_weight)
        ali_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Cohesion weight
        ttk.Label(main_frame, text="Cohesion Weight:").grid(row=row, column=0, sticky=tk.W)
        self.coh_weight_var = tk.DoubleVar(value=self.simulation.params['cohesion_weight'])
        coh_scale = ttk.Scale(main_frame, from_=0, to=5, variable=self.coh_weight_var,
                             command=self.update_cohesion_weight)
        coh_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Perception radii
        ttk.Label(main_frame, text="Perception Radii", 
                 font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=2, pady=(20, 5))
        row += 1
        
        # Separation radius
        ttk.Label(main_frame, text="Separation Radius:").grid(row=row, column=0, sticky=tk.W)
        self.sep_radius_var = tk.DoubleVar(value=self.simulation.params['separation_radius'])
        sep_radius_scale = ttk.Scale(main_frame, from_=10, to=100, variable=self.sep_radius_var,
                                   command=self.update_separation_radius)
        sep_radius_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Alignment radius
        ttk.Label(main_frame, text="Alignment Radius:").grid(row=row, column=0, sticky=tk.W)
        self.ali_radius_var = tk.DoubleVar(value=self.simulation.params['alignment_radius'])
        ali_radius_scale = ttk.Scale(main_frame, from_=10, to=150, variable=self.ali_radius_var,
                                   command=self.update_alignment_radius)
        ali_radius_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Cohesion radius
        ttk.Label(main_frame, text="Cohesion Radius:").grid(row=row, column=0, sticky=tk.W)
        self.coh_radius_var = tk.DoubleVar(value=self.simulation.params['cohesion_radius'])
        coh_radius_scale = ttk.Scale(main_frame, from_=10, to=150, variable=self.coh_radius_var,
                                   command=self.update_cohesion_radius)
        coh_radius_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Movement parameters
        ttk.Label(main_frame, text="Movement Parameters", 
                 font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=2, pady=(20, 5))
        row += 1
        
        # Max speed
        ttk.Label(main_frame, text="Max Speed:").grid(row=row, column=0, sticky=tk.W)
        self.max_speed_var = tk.DoubleVar(value=self.simulation.params['max_speed'])
        speed_scale = ttk.Scale(main_frame, from_=1, to=10, variable=self.max_speed_var,
                               command=self.update_max_speed)
        speed_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Max force
        ttk.Label(main_frame, text="Max Force:").grid(row=row, column=0, sticky=tk.W)
        self.max_force_var = tk.DoubleVar(value=self.simulation.params['max_force'])
        force_scale = ttk.Scale(main_frame, from_=0.01, to=0.5, variable=self.max_force_var,
                               command=self.update_max_force)
        force_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Number of boids
        ttk.Label(main_frame, text="Number of Boids:").grid(row=row, column=0, sticky=tk.W)
        self.num_boids_var = tk.IntVar(value=self.simulation.params['num_boids'])
        boids_scale = ttk.Scale(main_frame, from_=10, to=1000, variable=self.num_boids_var,
                               command=self.update_num_boids)
        boids_scale.grid(row=row, column=1, sticky=(tk.W, tk.E))
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_defaults).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Randomize", 
                  command=self.randomize_params).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Performance Test", 
                  command=self.performance_test).pack(side=tk.LEFT, padx=2)
        
        # Configure scrolling
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configure column weights
        main_frame.columnconfigure(1, weight=1)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def update_num_threads(self, value):
        new_thread_count = int(float(value))
        if new_thread_count != self.simulation.params['num_threads']:
            self.simulation.params['num_threads'] = new_thread_count
            # Set flag to recreate thread pool on next update cycle
            self.simulation.recreate_thread_pool = True
    
    def update_separation_weight(self, value):
        self.simulation.params['separation_weight'] = float(value)
    
    def update_alignment_weight(self, value):
        self.simulation.params['alignment_weight'] = float(value)
    
    def update_cohesion_weight(self, value):
        self.simulation.params['cohesion_weight'] = float(value)
    
    def update_separation_radius(self, value):
        self.simulation.params['separation_radius'] = float(value)
    
    def update_alignment_radius(self, value):
        self.simulation.params['alignment_radius'] = float(value)
    
    def update_cohesion_radius(self, value):
        self.simulation.params['cohesion_radius'] = float(value)
    
    def update_max_speed(self, value):
        self.simulation.params['max_speed'] = float(value)
    
    def update_max_force(self, value):
        self.simulation.params['max_force'] = float(value)
    
    def update_num_boids(self, value):
        new_count = int(float(value))
        self.simulation.params['num_boids'] = new_count
        
        current_count = len(self.simulation.boids)
        if new_count > current_count:
            # Add more boids
            for _ in range(new_count - current_count):
                x = random.randint(0, self.simulation.width)
                y = random.randint(0, self.simulation.height)
                boid = Boid(x, y, self.simulation.width, self.simulation.height)
                boid.max_speed = self.simulation.params['max_speed']
                boid.max_force = self.simulation.params['max_force']
                self.simulation.boids.append(boid)
        elif new_count < current_count:
            # Remove boids
            self.simulation.boids = self.simulation.boids[:new_count]
    
    def reset_defaults(self):
        defaults = {
            'separation_weight': 1.5,
            'alignment_weight': 1.0,
            'cohesion_weight': 1.0,
            'separation_radius': 25,
            'alignment_radius': 50,
            'cohesion_radius': 50,
            'max_speed': 4,
            'max_force': 0.1,
            'num_boids': 100,
            'num_threads': 4
        }
        
        self.sep_weight_var.set(defaults['separation_weight'])
        self.ali_weight_var.set(defaults['alignment_weight'])
        self.coh_weight_var.set(defaults['cohesion_weight'])
        self.sep_radius_var.set(defaults['separation_radius'])
        self.ali_radius_var.set(defaults['alignment_radius'])
        self.coh_radius_var.set(defaults['cohesion_radius'])
        self.max_speed_var.set(defaults['max_speed'])
        self.max_force_var.set(defaults['max_force'])
        self.num_boids_var.set(defaults['num_boids'])
        self.threads_var.set(defaults['num_threads'])
        
        self.simulation.params.update(defaults)
        self.simulation.create_boids()
    
    def randomize_params(self):
        self.sep_weight_var.set(random.uniform(0.5, 3.0))
        self.ali_weight_var.set(random.uniform(0.5, 3.0))
        self.coh_weight_var.set(random.uniform(0.5, 3.0))
        self.sep_radius_var.set(random.uniform(15, 60))
        self.ali_radius_var.set(random.uniform(30, 100))
        self.coh_radius_var.set(random.uniform(30, 100))
        self.max_speed_var.set(random.uniform(2, 8))
        self.max_force_var.set(random.uniform(0.05, 0.3))
    
    def performance_test(self):
        """Run a performance test with increasing boid counts"""
        import tkinter.messagebox as msgbox
        
        original_count = self.simulation.params['num_boids']
        test_counts = [100, 200, 500, 1000]
        results = []
        
        for count in test_counts:
            self.num_boids_var.set(count)
            time.sleep(1)  # Let simulation stabilize
            
            # Measure performance for 30 frames
            start_time = time.time()
            frame_count = 0
            while frame_count < 30:
                if not self.simulation.paused:
                    frame_count += 1
                time.sleep(0.016)  # ~60 FPS
            
            elapsed = time.time() - start_time
            avg_fps = frame_count / elapsed
            results.append(f"{count} boids: {avg_fps:.1f} FPS")
        
        # Restore original count
        self.num_boids_var.set(original_count)
        
        # Show results
        result_text = "Performance Test Results:\n" + "\n".join(results)
        msgbox.showinfo("Performance Test", result_text)

def run_simulation():
    simulation = BoidSimulation()
    
    # Create and start control panel in separate thread
    def control_panel_thread():
        control_panel = ControlPanel(simulation)
        control_panel.root.mainloop()
    
    control_thread = threading.Thread(target=control_panel_thread, daemon=True)
    control_thread.start()
    
    # Run simulation
    simulation.run()

if __name__ == "__main__":
    print("Starting Optimized Boids Simulation...")
    print("Optimizations:")
    print("  - Spatial partitioning grid for O(n) neighbor finding")
    print("  - Multi-threaded force calculations")
    print("  - Distance squared comparisons (no square root)")
    print("  - Cached force calculations")
    print("  - Adaptive grid cell sizing")
    print("\nControls:")
    print("  SPACE: Pause/Resume simulation")
    print("  R: Reset boids to random positions")
    print("  G: Toggle spatial grid visualization")
    print("  Use the GUI control panel to adjust parameters in real-time")
    print("\nA separate control window will open for parameter adjustment.")
    print("Try testing with 500-1000+ boids to see the performance improvements!")
    
    run_simulation()