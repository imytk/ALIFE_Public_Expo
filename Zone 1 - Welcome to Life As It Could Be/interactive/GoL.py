import pygame
import numpy as np
import tkinter as tk
from tkinter import ttk
import time
import random
from enum import Enum
import threading
import colorsys
import math

class DrawMode(Enum):
    DRAW = "draw"
    ERASE = "erase"
    TOGGLE = "toggle"

class VisualMode(Enum):
    CLASSIC = "classic"
    AGE = "age"
    RAINBOW = "rainbow"
    DENSITY = "density"
    HEAT = "heat"
    NEON = "neon"

class GameOfLife:
    def __init__(self, width=1200, height=800, cell_size=8):
        pygame.init()
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Enhanced Game of Life with GUI Controls")
        self.clock = pygame.time.Clock()

        # Calculate grid dimensions
        self.grid_width = width // cell_size
        self.grid_height = height // cell_size

        # Create grid (0 = dead, 1 = alive)
        self.grid = np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)
        self.next_grid = np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)

        # Enhanced parameters with GUI control
        self.params = {
            'speed': 10,
            'birth_rule': [3],
            'survival_rule': [2, 3],
            'wrap_edges': True,
            'trail_effect': False,
            'cell_size': cell_size,
            'random_density': 0.3,
            'visual_mode': VisualMode.CLASSIC,
            'show_grid_lines': False,
            'show_statistics': True,
            'color_intensity': 1.0,
            'fade_speed': 0.95,
            'rule_preset': 'Conway'
        }

        # Cell tracking
        self.cell_ages = np.zeros((self.grid_height, self.grid_width), dtype=np.uint16)
        self.cell_history = np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)
        self.generation_born = np.zeros((self.grid_height, self.grid_width), dtype=np.uint32)

        # Control state
        self.running = True
        self.paused = True
        self.drawing = False
        self.draw_mode = DrawMode.TOGGLE
        self.generation = 0
        self.population = 0
        self.max_population = 0
        self.stable_generations = 0

        # Performance tracking
        self.last_update = time.time()
        self.actual_fps = 0

        # Pattern library
        self.patterns = self.load_patterns()

        # Color palettes
        self.color_palettes = self.create_color_palettes()

        # Font initialization for Pygame UI
        pygame.font.init()

    def create_color_palettes(self):
        """Create color palettes for different visual modes"""
        palettes = {}

        palettes[VisualMode.CLASSIC] = {
            'alive': (255, 255, 255),
            'dead': (0, 0, 0),
            'trail': lambda intensity: (int(intensity * 50), int(intensity * 50), int(intensity * 100))
        }

        palettes[VisualMode.AGE] = {
            'dead': (0, 0, 0),
            'trail': lambda intensity: (int(intensity * 30), int(intensity * 30), int(intensity * 60))
        }

        palettes[VisualMode.RAINBOW] = {
            'dead': (0, 0, 0),
            'trail': lambda intensity: (int(intensity * 40), int(intensity * 20), int(intensity * 80))
        }

        palettes[VisualMode.DENSITY] = {
            'dead': (0, 0, 0),
            'trail': lambda intensity: (int(intensity * 60), int(intensity * 30), int(intensity * 120))
        }

        palettes[VisualMode.HEAT] = {
            'dead': (0, 0, 0),
            'trail': lambda intensity: (int(intensity * 80), int(intensity * 40), 0)
        }

        palettes[VisualMode.NEON] = {
            'dead': (5, 5, 15),
            'trail': lambda intensity: (int(intensity * 100), 0, int(intensity * 150))
        }

        return palettes

    def load_patterns(self):
        """Load pattern library"""
        patterns = {
            'Glider': [
                [0, 1, 0],
                [0, 0, 1],
                [1, 1, 1]
            ],
            'Lightweight Spaceship': [
                [0, 1, 1, 1, 1],
                [1, 0, 0, 0, 1],
                [0, 0, 0, 0, 1],
                [1, 0, 0, 1, 0]
            ],
            'Pulsar': [
                [0,0,1,1,1,0,0,0,1,1,1,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0],
                [1,0,0,0,0,1,0,1,0,0,0,0,1],
                [1,0,0,0,0,1,0,1,0,0,0,0,1],
                [1,0,0,0,0,1,0,1,0,0,0,0,1],
                [0,0,1,1,1,0,0,0,1,1,1,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,1,1,1,0,0,0,1,1,1,0,0],
                [1,0,0,0,0,1,0,1,0,0,0,0,1],
                [1,0,0,0,0,1,0,1,0,0,0,0,1],
                [1,0,0,0,0,1,0,1,0,0,0,0,1],
                [0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,1,1,1,0,0,0,1,1,1,0,0]
            ],
            'Block': [
                [1,1],
                [1,1]
            ],
            'Beehive': [
                [0,1,1,0],
                [1,0,0,1],
                [0,1,1,0]
            ],
            'Blinker': [
                [1,1,1]
            ],
            'Toad': [
                [0,1,1,1],
                [1,1,1,0]
            ],
            'R-Pentomino': [
                [0,1,1],
                [1,1,0],
                [0,1,0]
            ]
        }
        return patterns

    def count_neighbors(self, row, col):
        """Count living neighbors of a cell"""
        count = 0
        height, width = self.grid.shape

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue

                if self.params['wrap_edges']:
                    nr = (row + dr) % height
                    nc = (col + dc) % width
                else:
                    nr = row + dr
                    nc = col + dc
                    if nr < 0 or nr >= height or nc < 0 or nc >= width:
                        continue

                count += self.grid[nr, nc]

        return count

    def update_grid(self):
        """Update the grid according to Game of Life rules"""
        height, width = self.grid.shape

        neighbor_count = np.zeros_like(self.grid)
        for i in range(height):
            for j in range(width):
                neighbor_count[i, j] = self.count_neighbors(i, j)

        # Apply rules
        birth_mask = np.isin(neighbor_count, self.params['birth_rule'])
        survival_mask = np.isin(neighbor_count, self.params['survival_rule'])

        # Next generation
        self.next_grid = np.where(self.grid == 1, survival_mask, birth_mask).astype(np.uint8)

        # Update cell ages and history
        self.cell_ages = np.where(self.next_grid == 1, self.cell_ages + 1, 0)
        self.generation_born = np.where((self.grid == 0) & (self.next_grid == 1),
                                       self.generation, self.generation_born)

        if self.params['trail_effect']:
            fade_rate = self.params['fade_speed']
            self.cell_history = np.maximum(self.cell_history * fade_rate,
                                         self.next_grid.astype(np.float32) * 255).astype(np.uint8)

        # Check for stability
        if np.array_equal(self.grid, self.next_grid):
            self.stable_generations += 1
        else:
            self.stable_generations = 0

        # Swap grids
        self.grid, self.next_grid = self.next_grid, self.grid

        self.generation += 1
        self.population = np.sum(self.grid)
        self.max_population = max(self.max_population, self.population)

    def get_cell_color(self, alive, age, history, row, col, neighbor_count):
        """Get color for a cell based on visual mode"""
        visual_mode = self.params['visual_mode']
        intensity = self.params['color_intensity']

        if not alive and not self.params['trail_effect']:
            return self.color_palettes[visual_mode]['dead']

        if visual_mode == VisualMode.CLASSIC:
            if alive:
                return (int(255 * intensity), int(255 * intensity), int(255 * intensity))
            elif self.params['trail_effect'] and history > 0:
                trail_func = self.color_palettes[visual_mode]['trail']
                return trail_func(history / 255.0)
            return self.color_palettes[visual_mode]['dead']

        elif visual_mode == VisualMode.AGE:
            if alive:
                max_age = 50
                age_ratio = min(age / max_age, 1.0)
                red = int(255 * (1 - age_ratio) * intensity)
                green = int(255 * age_ratio * 0.5 * intensity)
                blue = int(255 * age_ratio * intensity)
                return (red, green, blue)
            elif self.params['trail_effect'] and history > 0:
                trail_func = self.color_palettes[visual_mode]['trail']
                return trail_func(history / 255.0 * intensity)
            return self.color_palettes[visual_mode]['dead']

        elif visual_mode == VisualMode.RAINBOW:
            if alive:
                hue = ((row + col + self.generation * 0.1) * 137.5) % 360
                rgb = colorsys.hsv_to_rgb(hue / 360, 0.8, intensity)
                return (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            elif self.params['trail_effect'] and history > 0:
                trail_func = self.color_palettes[visual_mode]['trail']
                return trail_func(history / 255.0 * intensity)
            return self.color_palettes[visual_mode]['dead']

        elif visual_mode == VisualMode.DENSITY:
            if alive:
                density_intensity = min(255, neighbor_count * 32)
                return (int(density_intensity * intensity),
                       int(density_intensity // 2 * intensity),
                       int((255 - density_intensity) * intensity))
            elif self.params['trail_effect'] and history > 0:
                trail_func = self.color_palettes[visual_mode]['trail']
                return trail_func(history / 255.0 * intensity)
            return self.color_palettes[visual_mode]['dead']

        elif visual_mode == VisualMode.HEAT:
            if alive:
                heat = min(255, age * 5)
                return (int(heat * intensity), int(heat * 0.5 * intensity), 0)
            elif self.params['trail_effect'] and history > 0:
                trail_func = self.color_palettes[visual_mode]['trail']
                return trail_func(history / 255.0 * intensity)
            return self.color_palettes[visual_mode]['dead']

        elif visual_mode == VisualMode.NEON:
            if alive:
                glow = int(200 + 55 * math.sin(self.generation * 0.1 + row + col))
                return (int(glow * 0.2 * intensity),
                       int(glow * intensity),
                       int(glow * 0.8 * intensity))
            elif self.params['trail_effect'] and history > 0:
                trail_func = self.color_palettes[visual_mode]['trail']
                return trail_func(history / 255.0 * intensity)
            return self.color_palettes[visual_mode]['dead']

    def draw_grid(self):
        """Draw the current grid state"""
        if self.params['visual_mode'] == VisualMode.NEON:
            self.screen.fill((5, 5, 15))
        else:
            self.screen.fill((0, 0, 0))

        height, width = self.grid.shape
        cell_size = self.params['cell_size']

        neighbor_counts = np.zeros_like(self.grid)
        if self.params['visual_mode'] == VisualMode.DENSITY:
            for row in range(height):
                for col in range(width):
                    neighbor_counts[row, col] = self.count_neighbors(row, col)

        for row in range(height):
            for col in range(width):
                alive = self.grid[row, col]
                age = self.cell_ages[row, col]
                history = self.cell_history[row, col] if self.params['trail_effect'] else 0
                neighbor_count = neighbor_counts[row, col]

                if alive or (self.params['trail_effect'] and history > 0):
                    color = self.get_cell_color(alive, age, history, row, col, neighbor_count)

                    x = col * cell_size
                    y = row * cell_size

                    pygame.draw.rect(self.screen, color, (x, y, cell_size, cell_size))

        # Draw grid lines
        if self.params['show_grid_lines'] and cell_size >= 4:
            grid_color = (64, 64, 64) if self.params['visual_mode'] != VisualMode.NEON else (40, 40, 60)
            for x in range(0, self.width, cell_size):
                pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.height))
            for y in range(0, self.height, cell_size):
                pygame.draw.line(self.screen, grid_color, (0, y), (self.width, y))

        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        """Draw UI information"""
        font = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 24)
        font_tiny = pygame.font.Font(None, 20)

        status = "RUNNING" if not self.paused else "PAUSED"
        if self.stable_generations > 5:
            status += " (STABLE)"

        info_text = f"Gen: {self.generation} | Pop: {self.population} | Max: {self.max_population} | {status} | FPS: {self.actual_fps:.1f}"
        text_surface = font.render(info_text, True, (255, 255, 255))

        text_rect = text_surface.get_rect()
        text_rect.topleft = (10, 10)
        bg_rect = text_rect.inflate(10, 5)
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
        self.screen.blit(text_surface, (10, 10))

        birth_str = ','.join(map(str, self.params['birth_rule']))
        survival_str = ','.join(map(str, self.params['survival_rule']))
        visual_mode_str = self.params['visual_mode'].value.title()

        rules_text = f"Rules: B{birth_str}/S{survival_str} | Speed: {self.params['speed']}/s | Visual: {visual_mode_str}"
        rules_surface = font_small.render(rules_text, True, (200, 200, 200))
        rules_rect = rules_surface.get_rect()
        rules_rect.topleft = (10, 45)
        bg_rect2 = rules_rect.inflate(10, 5)
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect2)
        self.screen.blit(rules_surface, (10, 45))

        if self.params['show_statistics']:
            density = (self.population / (self.grid_width * self.grid_height)) * 100
            stats_text = f"Density: {density:.1f}% | Stable for: {self.stable_generations} gens"
            stats_surface = font_tiny.render(stats_text, True, (180, 180, 180))
            stats_rect = stats_surface.get_rect()
            stats_rect.topleft = (10, 70)
            bg_rect3 = stats_rect.inflate(10, 5)
            pygame.draw.rect(self.screen, (0, 0, 0), bg_rect3)
            self.screen.blit(stats_surface, (10, 70))

        controls = [
            "SPACE: Play/Pause | R: Reset | C: Clear | F: Random Fill",
            "Mouse: Draw/Erase | 1-3: Draw Modes | G: Grid Lines | V: Visual Mode",
            "Arrow Keys: Step | +/-: Speed | Use GUI for advanced controls"
        ]

        y_offset = 95 if self.params['show_statistics'] else 75
        for i, control in enumerate(controls):
            text = font_tiny.render(control, True, (150, 150, 150))
            text_rect = text.get_rect()
            text_rect.topleft = (10, y_offset + i * 18)
            bg_rect = text_rect.inflate(5, 2)
            pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
            self.screen.blit(text, (10, y_offset + i * 18))

    def handle_mouse_input(self):
        """Handle mouse input for drawing"""
        if self.drawing:
            mouse_pos = pygame.mouse.get_pos()
            grid_x = mouse_pos[0] // self.params['cell_size']
            grid_y = mouse_pos[1] // self.params['cell_size']

            if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
                if self.draw_mode == DrawMode.DRAW:
                    self.grid[grid_y, grid_x] = 1
                elif self.draw_mode == DrawMode.ERASE:
                    self.grid[grid_y, grid_x] = 0
                elif self.draw_mode == DrawMode.TOGGLE:
                    self.grid[grid_y, grid_x] = 1 - self.grid[grid_y, grid_x]

                self.cell_ages[grid_y, grid_x] = 0
                self.cell_history[grid_y, grid_x] = 0
                self.generation_born[grid_y, grid_x] = self.generation

    def place_pattern(self, pattern_name, x, y):
        """Place a pattern at coordinates"""
        if pattern_name not in self.patterns:
            return

        pattern = self.patterns[pattern_name]
        height, width = len(pattern), len(pattern[0])

        for i in range(height):
            for j in range(width):
                grid_y = y + i
                grid_x = x + j

                if (0 <= grid_x < self.grid_width and
                    0 <= grid_y < self.grid_height and
                    pattern[i][j]):
                    self.grid[grid_y, grid_x] = 1
                    self.cell_ages[grid_y, grid_x] = 0
                    self.generation_born[grid_y, grid_x] = self.generation

    def random_fill(self):
        """Fill grid with random cells"""
        density = self.params['random_density']
        self.grid = (np.random.random((self.grid_height, self.grid_width)) < density).astype(np.uint8)
        self.cell_ages.fill(0)
        self.cell_history.fill(0)
        self.generation_born.fill(self.generation)
        self.generation = 0
        self.max_population = 0
        self.stable_generations = 0

    def clear_grid(self):
        """Clear the entire grid"""
        self.grid.fill(0)
        self.cell_ages.fill(0)
        self.cell_history.fill(0)
        self.generation_born.fill(0)
        self.generation = 0
        self.population = 0
        self.max_population = 0
        self.stable_generations = 0

    def cycle_visual_mode(self):
        """Cycle through visual modes"""
        modes = list(VisualMode)
        current_idx = modes.index(self.params['visual_mode'])
        next_idx = (current_idx + 1) % len(modes)
        self.params['visual_mode'] = modes[next_idx]

    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.random_fill()
                elif event.key == pygame.K_c:
                    self.clear_grid()
                elif event.key == pygame.K_f:
                    self.random_fill()
                elif event.key == pygame.K_g:
                    self.params['show_grid_lines'] = not self.params['show_grid_lines']
                elif event.key == pygame.K_v:
                    self.cycle_visual_mode()
                elif event.key == pygame.K_RIGHT:
                    if self.paused:
                        self.update_grid()
                elif event.key == pygame.K_1:
                    self.draw_mode = DrawMode.DRAW
                elif event.key == pygame.K_2:
                    self.draw_mode = DrawMode.ERASE
                elif event.key == pygame.K_3:
                    self.draw_mode = DrawMode.TOGGLE
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.params['speed'] = min(60, self.params['speed'] + 1)
                elif event.key == pygame.K_MINUS:
                    self.params['speed'] = max(1, self.params['speed'] - 1)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.drawing = True
                    self.handle_mouse_input()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.drawing = False

            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_input()
        return True

    def run(self):
        """Main Pygame simulation loop"""
        while self.running:
            if not self.handle_events():
                break

            current_time = time.time()

            if not self.paused and current_time - self.last_update >= 1.0 / self.params['speed']:
                self.update_grid()
                self.last_update = current_time

            self.actual_fps = self.clock.get_fps()
            self.draw_grid()
            self.clock.tick(60)

        pygame.quit()

class EnhancedControlPanel:
    def __init__(self, game):
        self.game = game
        self.root = tk.Tk()
        self.root.title("Game of Life - Touch Controls")
        self.root.geometry("450x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start Pygame in a separate thread
        self.game_thread = threading.Thread(target=self.game.run)
        self.game_thread.start()

        self.create_widgets()

        # Periodically update display
        self.update_stats_display()

    def on_closing(self):
        """Handle window closing for both Tkinter and Pygame"""
        self.game.running = False
        self.game_thread.join(timeout=1.0)
        if self.game_thread.is_alive():
            print("Pygame thread did not terminate gracefully.")
        self.root.destroy()

    def create_widgets(self):
        # Create scrollable canvas for all controls
        canvas = tk.Canvas(self.root, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main_frame = ttk.Frame(scrollable_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(main_frame, text="Game of Life Controls",
                              font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 25))

        # Main Action Buttons (Extra Large)
        action_section = tk.Frame(main_frame, bg='#f0f0f0')
        action_section.pack(fill=tk.X, pady=(0, 20))

        tk.Label(action_section, text="Main Controls", font=('Arial', 14, 'bold'),
                bg='#f0f0f0', fg='#34495e').pack(pady=(0, 10))

        action_row1 = tk.Frame(action_section, bg='#f0f0f0')
        action_row1.pack(fill=tk.X, pady=5)

        self.pause_button = tk.Button(action_row1, text="▶ PLAY", font=('Arial', 14, 'bold'),
                                     bg='#27ae60', fg='white', padx=20, pady=15,
                                     command=self.toggle_pause, relief='raised', bd=3)
        self.pause_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        tk.Button(action_row1, text="⏭ STEP", font=('Arial', 14, 'bold'),
                 bg='#3498db', fg='white', padx=20, pady=15,
                 command=self.step_forward, relief='raised', bd=3).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        action_row2 = tk.Frame(action_section, bg='#f0f0f0')
        action_row2.pack(fill=tk.X, pady=5)

        tk.Button(action_row2, text="🗑 CLEAR", font=('Arial', 14, 'bold'),
                 bg='#e74c3c', fg='white', padx=20, pady=15,
                 command=self.clear_grid, relief='raised', bd=3).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        tk.Button(action_row2, text="🎲 RANDOM", font=('Arial', 14, 'bold'),
                 bg='#9b59b6', fg='white', padx=20, pady=15,
                 command=self.random_fill, relief='raised', bd=3).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Visual Mode Buttons
        visual_section = tk.Frame(main_frame, bg='#f0f0f0')
        visual_section.pack(fill=tk.X, pady=(0, 20))

        tk.Label(visual_section, text="Visual Modes", font=('Arial', 14, 'bold'),
                bg='#f0f0f0', fg='#34495e').pack(pady=(0, 10))

        visual_modes = [
            ("Classic", "classic", "#95a5a6"),
            ("Age", "age", "#e67e22"),
            ("Rainbow", "rainbow", "#8e44ad")
        ]
        
        visual_row1 = tk.Frame(visual_section, bg='#f0f0f0')
        visual_row1.pack(fill=tk.X, pady=2)
        
        for text, value, color in visual_modes:
            btn = tk.Button(visual_row1, text=text, font=('Arial', 12, 'bold'),
                           bg=color, fg='white', padx=15, pady=12,
                           command=lambda v=value: self.set_visual_mode(v),
                           relief='raised', bd=2)
            btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        visual_modes2 = [
            ("Density", "density", "#2980b9"),
            ("Heat", "heat", "#d35400"),
            ("Neon", "neon", "#16a085")
        ]
        
        visual_row2 = tk.Frame(visual_section, bg='#f0f0f0')
        visual_row2.pack(fill=tk.X, pady=2)
        
        for text, value, color in visual_modes2:
            btn = tk.Button(visual_row2, text=text, font=('Arial', 12, 'bold'),
                           bg=color, fg='white', padx=15, pady=12,
                           command=lambda v=value: self.set_visual_mode(v),
                           relief='raised', bd=2)
            btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        # Rule Preset Buttons
        rules_section = tk.Frame(main_frame, bg='#f0f0f0')
        rules_section.pack(fill=tk.X, pady=(0, 20))

        tk.Label(rules_section, text="Game Rules", font=('Arial', 14, 'bold'),
                bg='#f0f0f0', fg='#34495e').pack(pady=(0, 10))

        rule_presets = [
            ("Conway", "Conway", "#2c3e50"),
            ("HighLife", "HighLife", "#e74c3c")
        ]
        
        rules_row1 = tk.Frame(rules_section, bg='#f0f0f0')
        rules_row1.pack(fill=tk.X, pady=2)
        
        for text, value, color in rule_presets:
            btn = tk.Button(rules_row1, text=text, font=('Arial', 12, 'bold'),
                           bg=color, fg='white', padx=15, pady=12,
                           command=lambda v=value: self.set_rule_preset(v),
                           relief='raised', bd=2)
            btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        rule_presets2 = [
            ("Seeds", "Seeds", "#f39c12"),
            ("Maze", "Maze", "#27ae60")
        ]
        
        rules_row2 = tk.Frame(rules_section, bg='#f0f0f0')
        rules_row2.pack(fill=tk.X, pady=2)
        
        for text, value, color in rule_presets2:
            btn = tk.Button(rules_row2, text=text, font=('Arial', 12, 'bold'),
                           bg=color, fg='white', padx=15, pady=12,
                           command=lambda v=value: self.set_rule_preset(v),
                           relief='raised', bd=2)
            btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        # Speed Control with Large Buttons
        speed_section = tk.Frame(main_frame, bg='#f0f0f0')
        speed_section.pack(fill=tk.X, pady=(0, 20))

        tk.Label(speed_section, text="Speed Control", font=('Arial', 14, 'bold'),
                bg='#f0f0f0', fg='#34495e').pack(pady=(0, 10))

        speed_frame = tk.Frame(speed_section, bg='#f0f0f0')
        speed_frame.pack(fill=tk.X)

        tk.Button(speed_frame, text="◀◀\nSLOWER", font=('Arial', 11, 'bold'),
                 bg='#34495e', fg='white', padx=15, pady=10,
                 command=self.decrease_speed, relief='raised', bd=2).pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        self.speed_label = tk.Label(speed_frame, text=f"{self.game.params['speed']}/sec",
                                   font=('Arial', 12, 'bold'), bg='#ecf0f1', padx=15, pady=10,
                                   relief='sunken', bd=2)
        self.speed_label.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        tk.Button(speed_frame, text="▶▶\nFASTER", font=('Arial', 11, 'bold'),
                 bg='#34495e', fg='white', padx=15, pady=10,
                 command=self.increase_speed, relief='raised', bd=2).pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        # Pattern Buttons
        pattern_section = tk.Frame(main_frame, bg='#f0f0f0')
        pattern_section.pack(fill=tk.X, pady=(0, 20))

        tk.Label(pattern_section, text="Famous Patterns", font=('Arial', 14, 'bold'),
                bg='#f0f0f0', fg='#34495e').pack(pady=(0, 10))

        patterns = [
            ("Glider", "#3498db"),
            ("Pulsar", "#9b59b6"),
            ("R-Pentomino", "#e67e22")
        ]
        
        pattern_row1 = tk.Frame(pattern_section, bg='#f0f0f0')
        pattern_row1.pack(fill=tk.X, pady=2)
        
        for pattern_name, color in patterns:
            btn = tk.Button(pattern_row1, text=pattern_name, font=('Arial', 11, 'bold'),
                           bg=color, fg='white', padx=10, pady=10,
                           command=lambda p=pattern_name: self.place_pattern_center_by_name(p),
                           relief='raised', bd=2)
            btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        patterns2 = [
            ("Blinker", "#1abc9c"),
            ("Block", "#95a5a6"),
            ("Beehive", "#f39c12")
        ]
        
        pattern_row2 = tk.Frame(pattern_section, bg='#f0f0f0')
        pattern_row2.pack(fill=tk.X, pady=2)
        
        for pattern_name, color in patterns2:
            btn = tk.Button(pattern_row2, text=pattern_name, font=('Arial', 11, 'bold'),
                           bg=color, fg='white', padx=10, pady=10,
                           command=lambda p=pattern_name: self.place_pattern_center_by_name(p),
                           relief='raised', bd=2)
            btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        # Toggle Options
        options_section = tk.Frame(main_frame, bg='#f0f0f0')
        options_section.pack(fill=tk.X, pady=(0, 20))

        tk.Label(options_section, text="Display Options", font=('Arial', 14, 'bold'),
                bg='#f0f0f0', fg='#34495e').pack(pady=(0, 10))

        # Trail Effect Toggle
        self.trail_button = tk.Button(options_section, text="Trail Effect: OFF", font=('Arial', 12),
                                     bg='#95a5a6', fg='white', padx=15, pady=10,
                                     command=self.toggle_trail_effect, relief='raised', bd=2)
        self.trail_button.pack(fill=tk.X, pady=2)

        # Grid Lines Toggle
        self.grid_button = tk.Button(options_section, text="Grid Lines: OFF", font=('Arial', 12),
                                    bg='#95a5a6', fg='white', padx=15, pady=10,
                                    command=self.toggle_grid_lines, relief='raised', bd=2)
        self.grid_button.pack(fill=tk.X, pady=2)

        # Statistics Toggle
        self.stats_button = tk.Button(options_section, text="Statistics: ON", font=('Arial', 12),
                                     bg='#27ae60', fg='white', padx=15, pady=10,
                                     command=self.toggle_statistics, relief='raised', bd=2)
        self.stats_button.pack(fill=tk.X, pady=2)

        # Draw Mode Buttons
        draw_section = tk.Frame(main_frame, bg='#f0f0f0')
        draw_section.pack(fill=tk.X, pady=(0, 20))

        tk.Label(draw_section, text="Draw Mode", font=('Arial', 14, 'bold'),
                bg='#f0f0f0', fg='#34495e').pack(pady=(0, 10))

        self.draw_mode_var = tk.StringVar(value=self.game.draw_mode.value)

        draw_modes = [
            ("✏ DRAW", "draw", "#27ae60"),
            ("⌫ ERASE", "erase", "#e74c3c"),
            ("⚡ TOGGLE", "toggle", "#3498db")
        ]

        draw_frame = tk.Frame(draw_section, bg='#f0f0f0')
        draw_frame.pack(fill=tk.X)

        self.draw_buttons = {}
        for text, value, color in draw_modes:
            btn = tk.Button(draw_frame, text=text, font=('Arial', 11, 'bold'),
                           bg=color if value == self.draw_mode_var.get() else '#bdc3c7',
                           fg='white', padx=10, pady=10,
                           command=lambda v=value: self.set_draw_mode(v),
                           relief='raised', bd=2)
            btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
            self.draw_buttons[value] = btn

        # Statistics display
        stats_section = tk.Frame(main_frame, bg='#f0f0f0')
        stats_section.pack(fill=tk.X, pady=(0, 10))

        tk.Label(stats_section, text="Current Status", font=('Arial', 14, 'bold'),
                bg='#f0f0f0', fg='#34495e').pack(pady=(0, 10))

        self.stats_label = tk.Label(stats_section, text="", font=('Arial', 11),
                                   bg='#ecf0f1', fg='#2c3e50', justify=tk.LEFT,
                                   padx=15, pady=10, relief='sunken', bd=2)
        self.stats_label.pack(fill=tk.X)

        # Update button states
        self.update_button_states()

    def set_visual_mode(self, mode):
        """Set visual mode via button"""
        for visual_mode in VisualMode:
            if visual_mode.value == mode:
                self.game.params['visual_mode'] = visual_mode
                break

    def set_rule_preset(self, preset):
        """Set rule preset via button"""
        presets = {
            'Conway': ([3], [2, 3]),
            'HighLife': ([3, 6], [2, 3]),
            'Seeds': ([2], []),
            'Maze': ([3], [1, 2, 3, 4, 5])
        }

        if preset in presets:
            birth, survival = presets[preset]
            self.game.params['birth_rule'] = birth
            self.game.params['survival_rule'] = survival
            self.game.params['rule_preset'] = preset

    def increase_speed(self):
        """Increase simulation speed"""
        self.game.params['speed'] = min(60, self.game.params['speed'] + 5)
        self.speed_label.config(text=f"{self.game.params['speed']}/sec")

    def decrease_speed(self):
        """Decrease simulation speed"""
        self.game.params['speed'] = max(1, self.game.params['speed'] - 5)
        self.speed_label.config(text=f"{self.game.params['speed']}/sec")

    def place_pattern_center_by_name(self, pattern_name):
        """Place a pattern at center by name"""
        if pattern_name in self.game.patterns:
            pattern = self.game.patterns[pattern_name]
            pattern_height, pattern_width = len(pattern), len(pattern[0])
            offset_x = pattern_width // 2
            offset_y = pattern_height // 2

            center_x = self.game.grid_width // 2 - offset_x
            center_y = self.game.grid_height // 2 - offset_y
            self.game.place_pattern(pattern_name, center_x, center_y)

    def toggle_trail_effect(self):
        """Toggle trail effect"""
        self.game.params['trail_effect'] = not self.game.params['trail_effect']
        if not self.game.params['trail_effect']:
            self.game.cell_history.fill(0)
        self.update_button_states()

    def toggle_grid_lines(self):
        """Toggle grid lines"""
        self.game.params['show_grid_lines'] = not self.game.params['show_grid_lines']
        self.update_button_states()

    def toggle_statistics(self):
        """Toggle statistics display"""
        self.game.params['show_statistics'] = not self.game.params['show_statistics']
        self.update_button_states()

    def set_draw_mode(self, mode):
        """Set draw mode via button"""
        self.draw_mode_var.set(mode)
        if mode == "draw":
            self.game.draw_mode = DrawMode.DRAW
        elif mode == "erase":
            self.game.draw_mode = DrawMode.ERASE
        elif mode == "toggle":
            self.game.draw_mode = DrawMode.TOGGLE
        self.update_button_states()

    def update_button_states(self):
        """Update button appearance based on current state"""
        # Update pause/play button
        if self.game.paused:
            self.pause_button.config(text="▶ PLAY", bg='#27ae60')
        else:
            self.pause_button.config(text="⏸ PAUSE", bg='#e67e22')

        # Update trail effect button
        if self.game.params['trail_effect']:
            self.trail_button.config(text="Trail Effect: ON", bg='#27ae60')
        else:
            self.trail_button.config(text="Trail Effect: OFF", bg='#95a5a6')

        # Update grid lines button
        if self.game.params['show_grid_lines']:
            self.grid_button.config(text="Grid Lines: ON", bg='#27ae60')
        else:
            self.grid_button.config(text="Grid Lines: OFF", bg='#95a5a6')

        # Update statistics button
        if self.game.params['show_statistics']:
            self.stats_button.config(text="Statistics: ON", bg='#27ae60')
        else:
            self.stats_button.config(text="Statistics: OFF", bg='#95a5a6')

        # Update draw mode buttons
        for mode, button in self.draw_buttons.items():
            if mode == self.draw_mode_var.get():
                if mode == "draw":
                    button.config(bg='#27ae60')
                elif mode == "erase":
                    button.config(bg='#e74c3c')
                else:  # toggle
                    button.config(bg='#3498db')
            else:
                button.config(bg='#bdc3c7')

    def toggle_pause(self):
        self.game.paused = not self.game.paused
        self.update_button_states()

    def step_forward(self):
        if self.game.paused:
            self.game.update_grid()

    def clear_grid(self):
        self.game.clear_grid()

    def random_fill(self):
        self.game.random_fill()

    def update_stats_display(self):
        """Update statistics display"""
        if self.game.running:
            density = (self.game.population / (self.game.grid_width * self.game.grid_height)) * 100 if (self.game.grid_width * self.game.grid_height) > 0 else 0

            stats_text = f"""Generation: {self.game.generation}
Population: {self.game.population}
Max Population: {self.game.max_population}
Density: {density:.1f}%
Stable for: {self.game.stable_generations} generations
Grid Size: {self.game.grid_width}x{self.game.grid_height}
Visual Mode: {self.game.params['visual_mode'].value.title()}
Current Rule: {self.game.params['rule_preset']}"""

            self.stats_label.config(text=stats_text)

            # Update button states periodically
            self.update_button_states()

            # Schedule next update
            self.root.after(500, self.update_stats_display)


def run_enhanced_game_of_life():
    print("Starting Enhanced Game of Life with Touch Controls...")
    print("\nFeatures:")
    print("  - 6 Visual modes: Classic, Age, Rainbow, Density, Heat, Neon")
    print("  - Multiple rule presets: Conway, HighLife, Seeds, Maze")
    print("  - Touch-friendly large button interface")
    print("  - Pattern library with classic Life patterns")
    print("  - Real-time visual feedback")
    print("  - Advanced statistics tracking")
    print("\nTouch Controls:")
    print("  - Large buttons for all functions")
    print("  - Visual feedback with color changes")
    print("  - Easy pattern placement")
    print("  - Simple speed adjustment")
    print("\nKeyboard Controls (in simulation window):")
    print("  SPACE: Play/Pause | V: Cycle visual modes | G: Toggle grid lines")
    print("  R: Random fill | C: Clear grid | Mouse: Draw/Erase cells")
    print("  1-3: Change draw mode | Arrow keys: Step simulation | +/-: Adjust speed")

    try:
        # Create game instance
        game = GameOfLife()

        # Create control panel, which will start the game thread
        control_panel = EnhancedControlPanel(game)

        # Run the main Tkinter GUI loop
        control_panel.root.mainloop()

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install pygame numpy")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_enhanced_game_of_life()