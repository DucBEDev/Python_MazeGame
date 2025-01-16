import pygame
import numpy as np
import random
from queue import PriorityQueue
import os

# Khởi tạo Pygame
pygame.init()

# Các thông số
CELL_SIZE = 40
GRID_SIZE = 20
WINDOW_SIZE = CELL_SIZE * GRID_SIZE
BUTTON_HEIGHT = 40
WINDOW_HEIGHT = WINDOW_SIZE + BUTTON_HEIGHT

# Màu sắc
BUTTON_COLOR = (70, 130, 180)
TEXT_COLOR = (255, 255, 255)
HINT_COLOR = (152, 251, 152, 128)  # Added alpha for transparency

# Tạo cửa sổ
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_HEIGHT))
pygame.display.set_caption("Maze Adventure")

# Load hình ảnh
def load_and_scale_image(filename, size):
    try:
        image = pygame.image.load(os.path.join('assets', filename))
        return pygame.transform.scale(image, (size, size))
    except:
        # Tạo surface màu tạm thời nếu không tìm thấy hình ảnh
        surface = pygame.Surface((size, size))
        surface.fill((200, 200, 200))
        return surface

# Load và scale các hình ảnh
PLAYER_IMG = load_and_scale_image('baby.png', CELL_SIZE)
WALL_IMG = load_and_scale_image('wall.png', CELL_SIZE)
EXIT_IMG = load_and_scale_image('exit.png', CELL_SIZE)
GROUND_IMG = load_and_scale_image('ground.png', CELL_SIZE)

# Animation frames cho player (giả sử có 4 frame cho mỗi hướng)
PLAYER_FRAMES = {
    'up': [load_and_scale_image(f'baby_up_{i}.png', CELL_SIZE) for i in range(4)],
    'down': [load_and_scale_image(f'baby_down_{i}.png', CELL_SIZE) for i in range(4)],
    'left': [load_and_scale_image(f'baby_left_{i}.png', CELL_SIZE) for i in range(4)],
    'right': [load_and_scale_image(f'baby_right_{i}.png', CELL_SIZE) for i in range(4)]
}

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = BUTTON_COLOR
        self.font = pygame.font.Font(None, 32)
        self.hover = False
        
    def draw(self, surface):
        color = (min(self.color[0] + 20, 255), 
                min(self.color[1] + 20, 255), 
                min(self.color[2] + 20, 255)) if self.hover else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = 'down'
        self.frame = 0
        self.animation_speed = 0.2
        self.animation_time = 0
        self.moving = False
        
    def update(self, dt):
        if self.moving:
            self.animation_time += dt
            if self.animation_time >= self.animation_speed:
                self.frame = (self.frame + 1) % len(PLAYER_FRAMES[self.direction])
                self.animation_time = 0
        else:
            self.frame = 0
            
    def draw(self, surface):
        current_frame = PLAYER_FRAMES[self.direction][self.frame]
        surface.blit(current_frame, (self.x * CELL_SIZE, self.y * CELL_SIZE))

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
        for particle in self.particles[:]:
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            particle['lifetime'] -= dt
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
                
    def draw(self, surface):
        for particle in self.particles:
            alpha = int(255 * particle['lifetime'])
            color = (*particle['color'], alpha)
            pos = (int(particle['x']), int(particle['y']))
            particle_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color, (2, 2), 2)
            surface.blit(particle_surface, pos)

def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def find_path(maze, start, end):
    rows, cols = len(maze), len(maze[0])
    pq = PriorityQueue()
    pq.put((0, start))
    came_from = {start: None}
    g_score = {start: 0}
    
    while not pq.empty():
        current = pq.get()[1]
        
        if current == end:
            path = []
            while current:
                path.append(current)
                current = came_from[current]
            return path[::-1]
        
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            x, y = current[0] + dx, current[1] + dy
            if 0 <= x < rows and 0 <= y < cols and maze[x][y] != 1:
                new_g = g_score[current] + 1
                if (x, y) not in g_score or new_g < g_score[(x, y)]:
                    g_score[(x, y)] = new_g
                    f_score = new_g + manhattan_distance((x, y), end)
                    pq.put((f_score, (x, y)))
                    came_from[(x, y)] = current
    return None

def create_maze(size):
    while True: 
        maze = np.zeros((size, size), dtype=int)
        
        # Tạo tường ngẫu nhiên
        for _ in range(size * 10):
            x, y = random.randint(0, size-1), random.randint(0, size-1)
            if not ((x == 0 and y == 0) or (x == (size - 1) and y == (size - 1))):
                maze[x][y] = 1
        
        # Đặt điểm bắt đầu
        maze[0][0] = 0
        
        # Tạo điểm thoát
        exits = [(size-1, size-1)]  # Exit mặc định
        
        start = (0, 0)
        exit_pos = (size-1, size-1)
        
        # Kiểm tra xem có đường đi không
        if find_path(maze, start, exit_pos) is not None:
            return maze, exits
        
        # Nếu không có đường đi, vòng lặp sẽ tiếp tục và tạo ma trận mới


# Khởi tạo game
player = Player(0, 0)
maze, exits = create_maze(GRID_SIZE)
particles = ParticleSystem()
hint_path = None
show_hint = False

# Tạo buttons với giao diện mới
new_game_btn = Button(10, WINDOW_SIZE + 5, 150, 30, "New Game")
hint_btn = Button(170, WINDOW_SIZE + 5, 100, 30, "Hint")

# Game loop
clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(60) / 1000.0  # Delta time in seconds
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            new_game_btn.hover = new_game_btn.rect.collidepoint(mouse_pos)
            hint_btn.hover = hint_btn.rect.collidepoint(mouse_pos)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if new_game_btn.rect.collidepoint(mouse_pos):
                maze, exits = create_maze(GRID_SIZE)
                player = Player(0, 0)
                show_hint = False
                hint_path = None
            elif hint_btn.rect.collidepoint(mouse_pos):
                show_hint = True
                current_pos = (player.y, player.x)
                nearest_exit = min(exits, key=lambda x: manhattan_distance(current_pos, x))
                hint_path = find_path(maze, current_pos, nearest_exit)
        
        if event.type == pygame.KEYDOWN:
            player.moving = True
            new_x, new_y = player.x, player.y
            
            if event.key == pygame.K_UP and player.y > 0 and not maze[player.y-1][player.x]:
                new_y -= 1
                player.direction = 'up'
            elif event.key == pygame.K_DOWN and player.y < GRID_SIZE-1 and not maze[player.y+1][player.x]:
                new_y += 1
                player.direction = 'down'
            elif event.key == pygame.K_LEFT and player.x > 0 and not maze[player.y][player.x-1]:
                new_x -= 1
                player.direction = 'left'
            elif event.key == pygame.K_RIGHT and player.x < GRID_SIZE-1 and not maze[player.y][player.x+1]:
                new_x += 1
                player.direction = 'right'
                
            if (new_x, new_y) != (player.x, player.y):
                player.x, player.y = new_x, new_y
                show_hint = False
        
        if event.type == pygame.KEYUP:
            player.moving = False

    # Update
    player.update(dt)
    particles.update(dt)
    
    # Draw
    screen.fill((200, 200, 200))  # Light gray background
    
    # Draw ground tiles
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            screen.blit(GROUND_IMG, (x * CELL_SIZE, y * CELL_SIZE))
    
    # Draw walls
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if maze[y][x] == 1:
                screen.blit(WALL_IMG, (x * CELL_SIZE, y * CELL_SIZE))
    
    # Draw exits
    for exit_pos in exits:
        screen.blit(EXIT_IMG, (exit_pos[1] * CELL_SIZE, exit_pos[0] * CELL_SIZE))
    
    # Draw hint path
    if show_hint and hint_path:
        hint_surface = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        for cell in hint_path[1:]:
            pygame.draw.rect(hint_surface, HINT_COLOR,
                           (cell[1] * CELL_SIZE, cell[0] * CELL_SIZE,
                            CELL_SIZE, CELL_SIZE))
        screen.blit(hint_surface, (0, 0))
    
    # Draw player
    player.draw(screen)
    
    # Draw particles
    particles.draw(screen)
    
    # Draw buttons
    new_game_btn.draw(screen)
    hint_btn.draw(screen)
    
    pygame.display.flip()
    
    # Check victory
    if (player.y, player.x) in exits:
        particles.create_victory_particles(
            player.x * CELL_SIZE + CELL_SIZE/2,
            player.y * CELL_SIZE + CELL_SIZE/2
        )
        font = pygame.font.Font(None, 74)
        text = font.render('Victory!', True, (0, 255, 0))
        text_rect = text.get_rect(center=(WINDOW_SIZE/2, WINDOW_SIZE/2))
        screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.wait(1000)
        maze, exits = create_maze(GRID_SIZE)
        player = Player(0, 0)
        show_hint = False
        hint_path = None

pygame.quit()