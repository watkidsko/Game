import pygame
import sys
import math

# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Bloons TD")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Path for bloons (list of waypoints)
path = [(50, 300), (200, 300), (200, 100), (600, 100), (600, 500), (750, 500)]

# Tower types and costs
TOWER_TYPES = [
    {"name": "Basic", "color": BLUE, "range": 120, "cooldown": 60, "cost": 100},
    {"name": "Fast", "color": GREEN, "range": 100, "cooldown": 30, "cost": 150},
    {"name": "Long Range", "color": (128,0,128), "range": 180, "cooldown": 80, "cost": 200},
]
MENU_WIDTH = 200
FONT = pygame.font.SysFont(None, 28)

money = 300
selected_tower = 0
round_num = 1
bloons_per_round = 5
bloons_spawned = 0
bloons_cleared = 0
round_in_progress = True
round_reward = 100

class Bloon:
    def __init__(self):
        self.radius = 15
        self.color = RED
        self.speed = 2
        self.path_index = 0
        self.x, self.y = path[0]

    def move(self):
        if self.path_index < len(path) - 1:
            target_x, target_y = path[self.path_index + 1]
            dx, dy = target_x - self.x, target_y - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed:
                self.x, self.y = target_x, target_y
                self.path_index += 1
            else:
                self.x += self.speed * dx / dist
                self.y += self.speed * dy / dist

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

class Tower:
    def __init__(self, x, y, tower_type=0):
        t = TOWER_TYPES[tower_type]
        self.x = x
        self.y = y
        self.range = t["range"]
        self.cooldown = t["cooldown"]
        self.timer = 0
        self.color = t["color"]
        self.type = tower_type

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), 20)
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.range, 1)

    def can_shoot(self):
        return self.timer <= 0

    def shoot(self, bloons):
        for bloon in bloons:
            dist = math.hypot(bloon.x - self.x, bloon.y - self.y)
            if dist <= self.range:
                self.timer = self.cooldown
                return Projectile(self.x, self.y, bloon)
        return None

    def update(self):
        if self.timer > 0:
            self.timer -= 1

class Projectile:
    def __init__(self, x, y, target):
        self.x = x
        self.y = y
        self.target = target
        self.speed = 8
        self.radius = 5
        self.color = YELLOW
        self.active = True

    def move(self):
        dx, dy = self.target.x - self.x, self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < self.speed or not self.active:
            self.active = False
            return
        self.x += self.speed * dx / dist
        self.y += self.speed * dy / dist

    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def check_collision(self):
        if not self.active:
            return False
        dist = math.hypot(self.target.x - self.x, self.target.y - self.y)
        if dist < self.target.radius:
            self.active = False
            return True
        return False

def draw_path(surface):
    for i in range(len(path) - 1):
        pygame.draw.line(surface, BLACK, path[i], path[i+1], 8)

def draw_menu(surface, money, selected_tower):
    pygame.draw.rect(surface, (220,220,220), (WIDTH, 0, MENU_WIDTH, HEIGHT))
    y = 40
    surface.blit(FONT.render(f"Money: ${money}", True, BLACK), (WIDTH+20, 10))
    surface.blit(FONT.render(f"Round: {round_num}", True, BLACK), (WIDTH+20, 35))
    for i, t in enumerate(TOWER_TYPES):
        color = (0,0,0) if i != selected_tower else (255,0,0)
        pygame.draw.rect(surface, color, (WIDTH+10, y, MENU_WIDTH-20, 50), 2)
        pygame.draw.circle(surface, t["color"], (WIDTH+35, y+25), 15)
        surface.blit(FONT.render(f"{t['name']} (${t['cost']})", True, BLACK), (WIDTH+60, y+10))
        y += 60
    surface.blit(FONT.render("Click to place", True, BLACK), (WIDTH+20, HEIGHT-40))

clock = pygame.time.Clock()
bloons = []
towers = []
projectiles = []
spawn_timer = 0
selected_tower = 0
money = 300
round_num = 1
bloons_per_round = 5
bloons_spawned = 0
bloons_cleared = 0
round_in_progress = True
round_reward = 100

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            # Click in menu to select tower
            if mx > WIDTH:
                menu_y = 40
                for i, t in enumerate(TOWER_TYPES):
                    if menu_y < my < menu_y+50:
                        selected_tower = i
                    menu_y += 60
            else:
                # Place tower if enough money
                cost = TOWER_TYPES[selected_tower]["cost"]
                if money >= cost:
                    towers.append(Tower(mx, my, selected_tower))
                    money -= cost
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not round_in_progress:
                round_in_progress = True
                round_num += 1
                bloons_per_round += 2
                round_reward += 25
                bloons_spawned = 0
                bloons_cleared = 0

    # Spawn new bloons for round
    if round_in_progress and bloons_spawned < bloons_per_round:
        spawn_timer += 1
        if spawn_timer > 40:
            bloons.append(Bloon())
            bloons_spawned += 1
            spawn_timer = 0

    # Move bloons
    for bloon in bloons:
        bloon.move()

    # Update towers and shoot
    for tower in towers:
        tower.update()
        if tower.can_shoot():
            proj = tower.shoot(bloons)
            if proj:
                projectiles.append(proj)

    # Move projectiles
    for proj in projectiles:
        proj.move()

    # Check collisions
    for proj in projectiles:
        if proj.check_collision():
            if proj.target in bloons:
                bloons.remove(proj.target)
                bloons_cleared += 1

    # Remove inactive projectiles
    projectiles = [p for p in projectiles if p.active]

    # End round if all bloons cleared
    if round_in_progress and bloons_cleared >= bloons_per_round and bloons_spawned >= bloons_per_round and not bloons:
        round_in_progress = False
        money += round_reward

    # Draw everything
    screen.fill(WHITE)
    draw_path(screen)
    for bloon in bloons:
        bloon.draw(screen)
    for tower in towers:
        tower.draw(screen)
    for proj in projectiles:
        proj.draw(screen)
    draw_menu(screen, money, selected_tower)
    pygame.display.flip()
    clock.tick(60)
