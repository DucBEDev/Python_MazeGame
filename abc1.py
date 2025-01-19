import pygame
import numpy as np  
import random
from queue import PriorityQueue
import os

# Game Configuration
CELL_SIZE = 30
GRID_SIZE = 20
WINDOW_SIZE = CELL_SIZE * GRID_SIZE
BUTTON_HEIGHT = 40
WINDOW_HEIGHT = WINDOW_SIZE + BUTTON_HEIGHT

# Colors
COLORS = {
    'BUTTON': (70, 130, 180),
    'TEXT': (255, 255, 255),
    'HINT': (152, 251, 152, 128),
    'BACKGROUND': (200, 200, 200)
}

# Asset loader
class AssetLoader:
    @staticmethod
    def load_and_scale_image(filename, size):
        try:
            image = pygame.image.load(os.path.join('assets', filename))
            return pygame.transform.scale(image, (size, size))
        except:
            surface = pygame.Surface((size, size))
            surface.fill((200, 200, 200))
            return surface

    @staticmethod
    def load_player_frames(cell_size):
        directions = ['up', 'down', 'left', 'right']
        frames = {}
        for direction in directions:
            frames[direction] = [
                AssetLoader.load_and_scale_image(f'baby_{direction}_{i}.png', cell_size)
                for i in range(4)
            ]
        return frames

# ui.py
class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = COLORS['BUTTON']
        self.font = pygame.font.Font(None, 32)
        self.hover = False
        
    def draw(self, surface):
        color = tuple(min(c + 20, 255) for c in self.color) if self.hover else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        text_surface = self.font.render(self.text, True, COLORS['TEXT'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

# entities.py
class Player:
    def __init__(self, x, y, frames):
        self.x = x
        self.y = y
        self.direction = 'down'
        self.frame = 0
        self.animation_speed = 0.2
        self.animation_time = 0
        self.moving = False
        self.frames = frames
        
    def update(self, dt):
        if self.moving:
            self.animation_time += dt
            if self.animation_time >= self.animation_speed:
                self.frame = (self.frame + 1) % len(self.frames[self.direction])
                self.animation_time = 0
        else:
            self.frame = 0
            
    def draw(self, surface):
        current_frame = self.frames[self.direction][self.frame]
        surface.blit(current_frame, (self.x * CELL_SIZE, self.y * CELL_SIZE))

    def move(self, dx, dy, maze):
        new_x, new_y = self.x + dx, self.y + dy
        if (0 <= new_x < GRID_SIZE and 
            0 <= new_y < GRID_SIZE and 
            not maze[new_y][new_x]):
            self.x, self.y = new_x, new_y
            return True
        return False

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def create_victory_particles(self, x, y):
        for _ in range(50):
            angle = random.uniform(0, 2 * np.pi)
            speed = random.uniform(2, 5)
            self.particles.append({
                'x': x,
                'y': y,
                'dx': np.cos(angle) * speed,
                'dy': np.sin(angle) * speed,
                'lifetime': 1.0,
                'color': (random.randint(0, 255), 
                         random.randint(0, 255), 
                         random.randint(0, 255))
            })
            
    def update(self, dt):
        self.particles = [p for p in self.particles if self.update_particle(p, dt)]
                
    def update_particle(self, particle, dt):
        particle['x'] += particle['dx'] * dt
        particle['y'] += particle['dy'] * dt
        particle['lifetime'] -= dt
        return particle['lifetime'] > 0
                
    def draw(self, surface):
        for particle in self.particles:
            alpha = int(255 * particle['lifetime'])
            color = (*particle['color'], alpha)
            pos = (int(particle['x']), int(particle['y']))
            particle_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color, (2, 2), 2)
            surface.blit(particle_surface, pos)

# maze.py
class MazeGenerator:
    @staticmethod
    def manhattan_distance(p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    @staticmethod
    def find_path(maze, start, end):
        rows, cols = len(maze), len(maze[0])
        pq = PriorityQueue()
        pq.put((0, start))
        came_from = {start: None}
        g_score = {start: 0}
        
        while not pq.empty():
            current = pq.get()[1]
            
            if current == end:
                return MazeGenerator._reconstruct_path(came_from, current)
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                x, y = current[0] + dx, current[1] + dy
                if (0 <= x < rows and 0 <= y < cols and maze[x][y] != 1):
                    new_g = g_score[current] + 1
                    if (x, y) not in g_score or new_g < g_score[(x, y)]:
                        g_score[(x, y)] = new_g
                        f_score = new_g + MazeGenerator.manhattan_distance((x, y), end)
                        pq.put((f_score, (x, y)))
                        came_from[(x, y)] = current
        return None

    @staticmethod
    def _reconstruct_path(came_from, current):
        path = []
        while current:
            path.append(current)
            current = came_from[current]
        return path[::-1]

    @staticmethod
    def create_maze(size):
        while True:
            maze = np.zeros((size, size), dtype=int)
            
            # Random walls
            for _ in range(size * 10):
                x, y = random.randint(0, size-1), random.randint(0, size-1)
                if not ((x == 0 and y == 0) or (x == size-1 and y == size-1)):
                    maze[x][y] = 1
            
            maze[0][0] = 0  # Start point
            exits = [(size-1, size-1)]  # Default exit
            
            if MazeGenerator.find_path(maze, (0, 0), (size-1, size-1)):
                return maze, exits

# game.py
class MazeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_HEIGHT))
        pygame.display.set_caption("Maze Adventure")
        
        # Load assets
        self.assets = {
            'PLAYER': AssetLoader.load_and_scale_image('baby.png', CELL_SIZE),
            'WALL': AssetLoader.load_and_scale_image('wall.png', CELL_SIZE),
            'EXIT': AssetLoader.load_and_scale_image('exit.png', CELL_SIZE),
            'GROUND': AssetLoader.load_and_scale_image('ground.png', CELL_SIZE),
            'PLAYER_FRAMES': AssetLoader.load_player_frames(CELL_SIZE)
        }
        
        self.init_game()
        
    def init_game(self):
        self.maze, self.exits = MazeGenerator.create_maze(GRID_SIZE)
        self.player = Player(0, 0, self.assets['PLAYER_FRAMES'])
        self.particles = ParticleSystem()
        self.hint_path = None
        self.show_hint = False
        
        # Initialize buttons
        self.new_game_btn = Button(10, WINDOW_SIZE + 5, 150, 30, "New Game")
        self.hint_btn = Button(170, WINDOW_SIZE + 5, 100, 30, "Hint")
        
    def handle_input(self, event):
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            self.new_game_btn.hover = self.new_game_btn.rect.collidepoint(mouse_pos)
            self.hint_btn.hover = self.hint_btn.rect.collidepoint(mouse_pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_click(event.pos)
            
        elif event.type == pygame.KEYDOWN:
            self.handle_player_movement(event.key)
            
        elif event.type == pygame.KEYUP:
            self.player.moving = False

    def handle_mouse_click(self, pos):
        if self.new_game_btn.rect.collidepoint(pos):
            self.init_game()
        elif self.hint_btn.rect.collidepoint(pos):
            self.show_hint = True
            current_pos = (self.player.y, self.player.x)
            nearest_exit = min(self.exits, 
                             key=lambda x: MazeGenerator.manhattan_distance(current_pos, x))
            self.hint_path = MazeGenerator.find_path(self.maze, current_pos, nearest_exit)

    def handle_player_movement(self, key):
        self.player.moving = True
        if key == pygame.K_UP:
            self.player.direction = 'up'
            moved = self.player.move(0, -1, self.maze)
        elif key == pygame.K_DOWN:
            self.player.direction = 'down'
            moved = self.player.move(0, 1, self.maze)
        elif key == pygame.K_LEFT:
            self.player.direction = 'left'
            moved = self.player.move(-1, 0, self.maze)
        elif key == pygame.K_RIGHT:
            self.player.direction = 'right'
            moved = self.player.move(1, 0, self.maze)
        else:
            return
            
        if moved:
            self.show_hint = False

    def update(self, dt):
        self.player.update(dt)
        self.particles.update(dt)
        
        # Check victory
        if (self.player.y, self.player.x) in self.exits:
            self.handle_victory()

    def handle_victory(self):
        self.particles.create_victory_particles(
            self.player.x * CELL_SIZE + CELL_SIZE/2,
            self.player.y * CELL_SIZE + CELL_SIZE/2
        )
        self.draw_victory_message()
        pygame.display.flip()
        pygame.time.wait(1000)
        self.init_game()

    def draw_victory_message(self):
        font = pygame.font.Font(None, 74)
        text = font.render('Victory!', True, (0, 255, 0))
        text_rect = text.get_rect(center=(WINDOW_SIZE/2, WINDOW_SIZE/2))
        self.screen.blit(text, text_rect)

    def draw(self):
        self.screen.fill(COLORS['BACKGROUND'])
        
        # Draw ground and maze
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.screen.blit(self.assets['GROUND'], (x * CELL_SIZE, y * CELL_SIZE))
                if self.maze[y][x] == 1:
                    self.screen.blit(self.assets['WALL'], (x * CELL_SIZE, y * CELL_SIZE))
        
        # Draw exits
        for exit_pos in self.exits:
            self.screen.blit(self.assets['EXIT'], 
                           (exit_pos[1] * CELL_SIZE, exit_pos[0] * CELL_SIZE))
        
        # Draw hint path
        if self.show_hint and self.hint_path:
            self.draw_hint_path()
        
        self.player.draw(self.screen)
        self.particles.draw(self.screen)
        
        # Draw UI
        self.new_game_btn.draw(self.screen)
        self.hint_btn.draw(self.screen)
        
        pygame.display.flip()

    def draw_hint_path(self):
        hint_surface = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        for cell in self.hint_path[1:]:
            pygame.draw.rect(hint_surface, COLORS['HINT'],
                           (cell[1] * CELL_SIZE, cell[0] * CELL_SIZE,
                            CELL_SIZE, CELL_SIZE))
        self.screen.blit(hint_surface, (0, 0))

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            dt = clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_input(event)
            
            self.update(dt)
            self.draw()
        
        pygame.quit()

# main.py
if __name__ == "__main__":
    game = MazeGame()
    game.run()