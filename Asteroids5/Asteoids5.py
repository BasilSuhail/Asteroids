import pygame
import random
import math

# --- Constants ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 120

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
RED_FLASH = (255, 100, 100)
EXPLOSION_YELLOW = (255, 230, 0)
SHIELD_BLUE = (100, 150, 255)
HEALTH_WHITE = (200, 200, 200)
BAR_BACKGROUND = (40, 40, 40)
SHOCKWAVE_COLOR = (173, 216, 230) 
UI_READY_COLOR = (0, 255, 0)
UI_COOLDOWN_COLOR = (255, 0, 0)
UI_BAR_COLOR = (0, 200, 255)
INVINCIBLE_AURA_COLOR = (255, 255, 0)
INVINCIBLE_BAR_COLOR = (255, 200, 0)
STAR_COLOR_1 = (255, 255, 100)
STAR_COLOR_2 = (255, 150, 0)
FIREBALL_COLOR = (255, 255, 200)
EXTRA_LIFE_COLOR = (255, 50, 50)
ENEMY_SHIP_COLOR = (255, 50, 50)
SHIP_GRAY = (150, 150, 150)
COCKPIT_BLUE = (100, 200, 255)
ENGINE_FLAME_YELLOW = (255, 200, 0)

# --- Game Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Asteroids")
clock = pygame.time.Clock()
font = pygame.font.SysFont('arial', 24)
large_font = pygame.font.SysFont('arial', 80)


# --- Classes ---

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_image = pygame.Surface((40, 30), pygame.SRCALPHA)
        body_points = [(40, 15), (10, 0), (10, 30)]
        pygame.draw.polygon(self.base_image, SHIP_GRAY, body_points)
        left_wing = [(10, 0), (0, 5), (10, 15)]
        pygame.draw.polygon(self.base_image, SHIP_GRAY, left_wing)
        right_wing = [(10, 30), (0, 25), (10, 15)]
        pygame.draw.polygon(self.base_image, SHIP_GRAY, right_wing)
        cockpit_points = [(35, 15), (28, 12), (28, 18)]
        pygame.draw.polygon(self.base_image, COCKPIT_BLUE, cockpit_points)

        self.original_image = self.base_image.copy()
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.mask = pygame.mask.from_surface(self.image)
        self.pos = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.speed = 5
        self.direction_vector = pygame.math.Vector2(1, 0)
        
        self.max_health = 100
        self.health = 100
        
        self.shockwave_cooldown = 1000 
        self.last_shockwave_time = -self.shockwave_cooldown
        self.invincible = False
        self.invincibility_duration = 5000
        self.invincible_timer = 0
        
        self.damage_flash_timer = 0
        self.is_thrusting = False

    def update(self, *args):
        if self.invincible and pygame.time.get_ticks() - self.invincible_timer > self.invincibility_duration:
            self.invincible = False
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1
        
        keys = pygame.key.get_pressed()
        move_vector = pygame.math.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_vector.x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_vector.x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_vector.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_vector.y = 1
        
        self.is_thrusting = move_vector.length() > 0
        
        if self.is_thrusting:
            move_vector.normalize_ip(); self.pos += move_vector * self.speed
        
        mouse_pos = pygame.mouse.get_pos()
        if (pygame.math.Vector2(mouse_pos) - self.pos).length() > 0:
            self.direction_vector = (pygame.math.Vector2(mouse_pos) - self.pos).normalize()
        
        angle = self.direction_vector.angle_to(pygame.math.Vector2(1, 0))
        self.image = pygame.transform.rotate(self.base_image, angle)
        
        if self.pos.x > SCREEN_WIDTH: self.pos.x = 0
        if self.pos.x < 0: self.pos.x = SCREEN_WIDTH
        if self.pos.y > SCREEN_HEIGHT: self.pos.y = 0
        if self.pos.y < 0: self.pos.y = SCREEN_HEIGHT

        self.rect = self.image.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.image)

    def shoot(self):
        return Bullet(self.pos + self.direction_vector * 25, self.direction_vector)
    
    def activate_shockwave(self):
        now = pygame.time.get_ticks()
        if now - self.last_shockwave_time > self.shockwave_cooldown:
            self.last_shockwave_time = now; return Shockwave(self.pos)
        return None 
    
    def activate_invincibility(self):
        self.invincible = True; self.invincible_timer = pygame.time.get_ticks()

    def take_damage(self, amount):
        if not self.invincible:
            self.health -= amount
            self.damage_flash_timer = 10 
            if self.health <= 0:
                self.health = 0
                return True
        return False
    
    def reset_health(self):
        self.health = self.max_health
    
    def draw(self, surface):
        if self.is_thrusting:
            angle = self.direction_vector.angle_to(pygame.math.Vector2(1, 0))
            flame_length = 15 + random.randint(0, 7)
            flame_points = [(0,0), (-flame_length, -5), (-flame_length, 5)]
            flame_surf = pygame.Surface((flame_length, 10), pygame.SRCALPHA)
            pygame.draw.polygon(flame_surf, ENGINE_FLAME_YELLOW, flame_points)
            rotated_flame = pygame.transform.rotate(flame_surf, angle)
            offset = pygame.math.Vector2(-20, 0).rotate(-angle)
            flame_rect = rotated_flame.get_rect(center = self.pos + offset)
            surface.blit(rotated_flame, flame_rect)

        if self.invincible:
            aura_radius = self.rect.width * 0.8
            aura_surf = pygame.Surface((aura_radius * 2, aura_radius * 2), pygame.SRCALPHA)
            alpha = 128 + math.sin(pygame.time.get_ticks() * 0.01) * 64
            pygame.draw.circle(aura_surf, (*INVINCIBLE_AURA_COLOR, alpha), (aura_radius, aura_radius), aura_radius)
            surface.blit(aura_surf, aura_surf.get_rect(center=self.rect.center))

        surface.blit(self.image, self.rect)

        if self.damage_flash_timer > 0:
            flash_surf = self.image.copy()
            flash_surf.fill(WHITE, special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(flash_surf, self.rect)
        
        bar_width = self.rect.width
        bar_height = 7
        bar_x = self.rect.left
        bar_y = self.rect.bottom + 5
        health_percentage = self.health / self.max_health
        current_bar_width = bar_width * health_percentage
        pygame.draw.rect(surface, BAR_BACKGROUND, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, HEALTH_WHITE, (bar_x, bar_y, current_bar_width, bar_height))

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, size, pos=None, target_pos=None):
        super().__init__()
        self.size = size
        if self.size == 3: self.radius = 45
        elif self.size == 2: self.radius = 25
        else: self.radius = 12
        self.points = self._create_irregular_shape(self.radius)
        surface_size = self.radius * 2.5
        self.original_image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center_offset = pygame.math.Vector2(surface_size / 2, surface_size / 2)
        translated_points = [p + center_offset for p in self.points]
        pygame.draw.polygon(self.original_image, WHITE, translated_points, 2)
        self.image = self.original_image; self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        if pos is None:
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            if edge == 'top': self.rect.center = (random.randint(0, SCREEN_WIDTH), -self.radius)
            elif edge == 'bottom': self.rect.center = (random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + self.radius)
            elif edge == 'left': self.rect.center = (-self.radius, random.randint(0, SCREEN_HEIGHT))
            else: self.rect.center = (SCREEN_WIDTH + self.radius, random.randint(0, SCREEN_HEIGHT))
        else: self.rect.center = pos
        speed_tiers = [(0.5, 1.5), (1.5, 3.0), (3.0, 4.5), (5.0, 7.0)]
        speed = random.uniform(*random.choice(speed_tiers))
        if target_pos:
            direction = (pygame.math.Vector2(target_pos) - self.rect.center).normalize()
            direction.rotate_ip(random.uniform(-20, 20)); self.vel = direction * speed
        else: self.vel = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * speed
        self.health = 1
        if self.size == 3 and random.random() < 0.50: self.health = random.randint(3, 10)
        elif self.size == 2 and random.random() < 0.35: self.health = random.randint(3, 10)
        elif self.size == 1 and random.random() < 0.20: self.health = random.randint(3, 10)
        self.is_shielded = self.health > 1; self.max_health = self.health
        self.hit_timer = 0

    def _create_irregular_shape(self, radius):
        num_vertices = random.randint(9, 14)
        points = []
        for i in range(num_vertices):
            angle = (i / num_vertices) * 2 * math.pi
            rand_radius = random.uniform(radius * 0.7, radius * 1.3)
            points.append(pygame.math.Vector2(rand_radius * math.cos(angle), rand_radius * math.sin(angle)))
        return points

    def update(self, *args):
        self.rect.move_ip(self.vel)
        if self.rect.top > SCREEN_HEIGHT + 100 or self.rect.bottom < -100 or \
           self.rect.left > SCREEN_WIDTH + 100 or self.rect.right < -100: self.kill()
        self.angle += self.rotation_speed
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)
        if self.hit_timer > 0: self.hit_timer -= 1
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.is_shielded and self.hit_timer > 0:
            flash_surf = self.image.copy()
            flash_surf.fill(RED_FLASH, special_flags=pygame.BLEND_ADD)
            surface.blit(flash_surf, self.rect)
        if self.health > 0 and self.max_health > 1:
            bar_width = self.rect.width * 0.8; bar_height = 5
            bar_x = self.rect.centerx - bar_width / 2; bar_y = self.rect.bottom + 5
            health_percentage = self.health / self.max_health
            current_bar_width = bar_width * health_percentage
            pygame.draw.rect(surface, BAR_BACKGROUND, (bar_x, bar_y, bar_width, bar_height))
            bar_color = SHIELD_BLUE if self.is_shielded else HEALTH_WHITE
            pygame.draw.rect(surface, bar_color, (bar_x, bar_y, current_bar_width, bar_height))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction_vector):
        super().__init__()
        self.original_core_image = pygame.Surface((15, 4), pygame.SRCALPHA)
        self.original_core_image.fill(LIGHT_GRAY)
        self.glow_layers = []
        glow_colors = [(180, 180, 180, 40), (220, 220, 220, 70), (255, 255, 255, 100)]
        glow_sizes = [(25, 8), (20, 6), (18, 5)]
        for i in range(len(glow_colors)):
            glow_surf = pygame.Surface(glow_sizes[i], pygame.SRCALPHA)
            glow_surf.fill(glow_colors[i]); self.glow_layers.append(glow_surf)
        self.image = self.original_core_image
        self.rect = self.image.get_rect(center=pos)
        self.direction_vector = direction_vector.normalize()
        self.vel = self.direction_vector * 10

    def update(self, *args):
        self.rect.move_ip(self.vel)
        if not self.rect.colliderect(screen.get_rect()): self.kill()

    def draw(self, surface):
        angle = self.direction_vector.angle_to(pygame.math.Vector2(1, 0))
        for glow_surf in self.glow_layers:
            rotated_glow = pygame.transform.rotate(glow_surf, angle)
            surface.blit(rotated_glow, rotated_glow.get_rect(center=self.rect.center))
        rotated_core = pygame.transform.rotate(self.original_core_image, angle)
        surface.blit(rotated_core, rotated_core.get_rect(center=self.rect.center))

class Debris(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * random.uniform(1, 4)
        self.image = pygame.Surface((3, 3)); self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=self.pos)
        self.lifespan = random.randint(20, 50)

    def update(self, *args):
        self.pos += self.vel; self.rect.center = self.pos
        self.lifespan -= 1
        if self.lifespan <= 0: self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        super().__init__()
        self.center = center; self.size = size; self.lifespan = 20
        self.image = pygame.Surface((0, 0)); self.rect = self.image.get_rect(center=self.center)
        if self.size == 'large': self.max_radius = 60
        elif self.size == 'medium': self.max_radius = 40
        else: self.max_radius = 20
            
    def update(self, *args):
        self.lifespan -= 1
        if self.lifespan <= 0: self.kill(); return
        progress = (20 - self.lifespan) / 20; self.current_radius = int(self.max_radius * progress)
        alpha = 255 * (self.lifespan / 20)
        self.image = pygame.Surface((self.current_radius * 2, self.current_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*EXPLOSION_YELLOW, alpha), (self.current_radius, self.current_radius), self.current_radius)
        self.rect = self.image.get_rect(center=self.center)

class Shockwave(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pygame.math.Vector2(pos); self.max_lifespan = 45; self.lifespan = self.max_lifespan
        self.max_scale = 300; self.image = pygame.Surface((0, 0), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos); self.mask = pygame.mask.from_surface(self.image)
        self.hit_targets = set()

    def update(self, *args):
        self.lifespan -= 1
        if self.lifespan <= 0: self.kill(); return
        progress = (self.max_lifespan - self.lifespan) / self.max_lifespan
        current_size = int(self.max_scale * progress) + 1; alpha = 255 * (self.lifespan / self.max_lifespan)
        self.image = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*SHOCKWAVE_COLOR, alpha), (current_size, current_size), current_size, 4)
        self.rect = self.image.get_rect(center=self.pos); self.mask = pygame.mask.from_surface(self.image)

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos, type):
        super().__init__()
        self.type = type; self.lifespan = 600
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        if self.type == 'invincible':
            pygame.draw.circle(self.image, INVINCIBLE_AURA_COLOR, (15, 15), 15, 4)
            pygame.draw.circle(self.image, WHITE, (15, 15), 10, 2)
        elif self.type == 'extralife':
            pygame.draw.rect(self.image, EXTRA_LIFE_COLOR, (10, 2, 10, 26))
            pygame.draw.rect(self.image, EXTRA_LIFE_COLOR, (2, 10, 26, 10))
        self.rect = self.image.get_rect(center=pos)

    def update(self, *args):
        self.lifespan -= 1
        if self.lifespan <= 0: self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, pos, target_pos):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, FIREBALL_COLOR, (6, 6), 6)
        pygame.draw.circle(self.image, WHITE, (6, 6), 3)
        self.rect = self.image.get_rect(center=pos); self.mask = pygame.mask.from_surface(self.image)
        if (pygame.math.Vector2(target_pos) - pos).length() > 0:
            direction = (pygame.math.Vector2(target_pos) - pos).normalize()
            self.vel = direction * 4
        else:
            self.vel = pygame.math.Vector2(0, -1) * 4

    def update(self, *args):
        self.rect.move_ip(self.vel)
        if not self.rect.colliderect(screen.get_rect()): self.kill()

class StarEnemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 500
        self.original_image = self.create_star_surface(self.size)
        self.base_image = self.original_image.copy()
        self.image = self.original_image; self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.state = 'entering'; self.spawn_side = random.choice(['left', 'right'])
        if self.spawn_side == 'left':
            self.rect.center = (-self.size / 2, SCREEN_HEIGHT / 2)
            self.vel = pygame.math.Vector2(2, 0); self.linger_pos_x = self.size / 4
        else:
            self.rect.center = (SCREEN_WIDTH + self.size / 2, SCREEN_HEIGHT / 2)
            self.vel = pygame.math.Vector2(-2, 0); self.linger_pos_x = SCREEN_WIDTH - (self.size / 4)
        self.linger_duration = 10000; self.linger_timer = 0
        self.health = 100; self.max_health = 100; self.hit_timer = 0
        self.fire_rate = 1000; self.last_shot_time = pygame.time.get_ticks()

    def create_star_surface(self, size):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size / 2
        points1 = self.get_star_points(center, center, 5, size / 2, size / 4, 0)
        points2 = self.get_star_points(center, center, 5, size / 2, size / 4, 36)
        pygame.draw.polygon(surf, STAR_COLOR_1, points1); pygame.draw.polygon(surf, STAR_COLOR_2, points2)
        return surf

    def get_star_points(self, cx, cy, num_points, outer_r, inner_r, start_angle):
        points = []; angle_step = 360 / (num_points * 2)
        for i in range(num_points * 2):
            radius = inner_r if i % 2 == 0 else outer_r
            angle = math.radians(i * angle_step + start_angle)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return points

    def update(self, player_pos):
        new_bullet = None
        if self.state == 'entering':
            self.rect.move_ip(self.vel)
            if (self.spawn_side == 'left' and self.rect.centerx >= self.linger_pos_x) or \
               (self.spawn_side == 'right' and self.rect.centerx <= self.linger_pos_x):
                self.vel.x = 0; self.state = 'lingering'; self.linger_timer = pygame.time.get_ticks()
        elif self.state == 'lingering':
            now = pygame.time.get_ticks()
            if now - self.last_shot_time > self.fire_rate:
                self.last_shot_time = now; new_bullet = EnemyBullet(self.rect.center, player_pos)
            if now - self.linger_timer > self.linger_duration:
                self.state = 'leaving'; self.vel.x = -2 if self.spawn_side == 'left' else 2
        elif self.state == 'leaving':
            self.rect.move_ip(self.vel)
            if not self.rect.colliderect(screen.get_rect()): self.kill()
        pulse_scale = 1 + math.sin(pygame.time.get_ticks() * 0.005) * 0.05
        center = self.rect.center
        scaled_size = (int(self.size * pulse_scale), int(self.size * pulse_scale))
        self.image = pygame.transform.scale(self.original_image, scaled_size)
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)
        if self.hit_timer > 0: self.hit_timer -= 1
        return new_bullet
            
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.hit_timer > 0:
            flash_surf = self.image.copy(); flash_surf.fill(RED_FLASH, special_flags=pygame.BLEND_ADD)
            surface.blit(flash_surf, self.rect)
        bar_width = self.rect.width * 0.9; bar_height = 10
        bar_x = self.rect.centerx - bar_width / 2; bar_y = self.rect.top - 20
        health_percentage = self.health / self.max_health
        current_bar_width = bar_width * health_percentage
        pygame.draw.rect(surface, BAR_BACKGROUND, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, RED_FLASH, (bar_x, bar_y, current_bar_width, bar_height))

class EnemyShip(pygame.sprite.Sprite):
    def __init__(self, target):
        super().__init__()
        self.target = target
        self.image_orig = pygame.Surface((30, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.image_orig, ENEMY_SHIP_COLOR, [(30, 10), (0, 0), (0, 20)])
        self.image = self.image_orig; self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top': self.rect.center = (random.randint(0, SCREEN_WIDTH), -20)
        elif edge == 'bottom': self.rect.center = (random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 20)
        elif edge == 'left': self.rect.center = (-20, random.randint(0, SCREEN_HEIGHT))
        else: self.rect.center = (SCREEN_WIDTH + 20, random.randint(0, SCREEN_HEIGHT))
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = random.uniform(2.5, 4.0); self.health = 3
        self.state = 'approaching'; self.fire_rate = 1500
        self.last_shot_time = pygame.time.get_ticks(); self.strafe_timer = 0
        self.strafe_duration = 3000; self.strafe_direction = pygame.math.Vector2(1, 0)

    def update(self, player_pos):
        new_bullet = None
        direction_to_player = (player_pos - self.pos)
        distance = direction_to_player.length()
        if self.state == 'approaching':
            if distance > 250:
                self.vel = direction_to_player.normalize() * self.speed
            else:
                self.state = 'strafing'; self.strafe_timer = pygame.time.get_ticks()
                self.strafe_direction = direction_to_player.normalize().rotate(random.choice([-90, 90]))
                self.vel = self.strafe_direction * self.speed / 2
        elif self.state == 'strafing':
            self.vel = self.strafe_direction * self.speed / 2
            if pygame.time.get_ticks() - self.strafe_timer > self.strafe_duration:
                self.state = 'approaching'
            now = pygame.time.get_ticks()
            if now - self.last_shot_time > self.fire_rate:
                self.last_shot_time = now; new_bullet = EnemyBullet(self.pos, player_pos)
        self.pos += self.vel; self.rect.center = self.pos
        if distance > 0:
            angle = direction_to_player.angle_to(pygame.math.Vector2(1, 0))
            self.image = pygame.transform.rotate(self.image_orig, angle)
            self.rect = self.image.get_rect(center=self.pos)
            self.mask = pygame.mask.from_surface(self.image)
        if not self.rect.colliderect(screen.get_rect().inflate(100, 100)):
            self.kill()
        return new_bullet

    def draw(self, surface):
        surface.blit(self.image, self.rect)

def draw_text(text, x, y, font_obj=font, color=WHITE):
    text_surface = font_obj.render(text, True, color)
    screen.blit(text_surface, (x, y))

def draw_text_center(text, x, y, font_obj=font, color=WHITE):
    text_surface = font_obj.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def main():
    running = True
    game_over = False
    all_sprites = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    shockwaves = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    star_enemy_group = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    enemy_ships = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)
    score = 0
    lives = 3

    for _ in range(5):
        new_asteroid = Asteroid(3); all_sprites.add(new_asteroid); asteroids.add(new_asteroid)
    
    spawn_interval = 1000; last_spawn_time = pygame.time.get_ticks()
    fire_rate = 150; last_shot_time = 0
    powerup_spawn_interval = random.randint(10000, 30000); last_powerup_spawn_time = pygame.time.get_ticks()
    star_spawn_interval = random.randint(45000, 60000); last_star_spawn_time = pygame.time.get_ticks()
    enemy_ship_spawn_interval = random.randint(5000, 10000); last_enemy_ship_spawn = pygame.time.get_ticks()
    
    elapsed_time = 0; start_time = pygame.time.get_ticks()

    while running:
        clock.tick(FPS)
        
        now = pygame.time.get_ticks()
        
        if not game_over:
            elapsed_time = now - start_time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    main()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3 and not game_over:
                    new_shockwave = player.activate_shockwave()
                    if new_shockwave:
                        all_sprites.add(new_shockwave)
                        shockwaves.add(new_shockwave)

        if not game_over:
            if not star_enemy_group:
                if now - last_spawn_time > spawn_interval:
                    last_spawn_time = now; target = player.pos if random.random() < 0.5 else None
                    new_asteroid = Asteroid(3, target_pos=target)
                    all_sprites.add(new_asteroid); asteroids.add(new_asteroid)
                
                if now - last_enemy_ship_spawn > enemy_ship_spawn_interval:
                    last_enemy_ship_spawn = now; enemy_ship_spawn_interval = random.randint(5000, 15000)
                    num_to_spawn = random.choice([1, 2, 2, 3])
                    for _ in range(num_to_spawn):
                        ship = EnemyShip(player); all_sprites.add(ship); enemy_ships.add(ship)

            if now - last_star_spawn_time > star_spawn_interval and not star_enemy_group:
                last_star_spawn_time = now; star_spawn_interval = random.randint(45000, 60000)
                star = StarEnemy(); all_sprites.add(star); star_enemy_group.add(star)
                for ast in asteroids:
                    all_sprites.add(Explosion(ast.rect.center, 'small')); ast.kill()

            keys = pygame.key.get_pressed(); mouse_buttons = pygame.mouse.get_pressed()
            if keys[pygame.K_SPACE] or mouse_buttons[0]:
                if now - last_shot_time > fire_rate:
                    last_shot_time = now; bullet = player.shoot()
                    all_sprites.add(bullet); bullets.add(bullet)

            for sprite in all_sprites:
                if isinstance(sprite, (StarEnemy, EnemyShip)):
                    new_bullet = sprite.update(player.pos)
                    if new_bullet: all_sprites.add(new_bullet); enemy_bullets.add(new_bullet)
                else: sprite.update()
            
            hits_on_asteroids = pygame.sprite.groupcollide(asteroids, bullets, False, True)
            for hit_asteroid in hits_on_asteroids:
                hit_asteroid.health -= 1; hit_asteroid.hit_timer = 5
                if hit_asteroid.health <= 0:
                    score += 10
                    if hit_asteroid.size == 3 and now - last_powerup_spawn_time > powerup_spawn_interval and not star_enemy_group:
                        last_powerup_spawn_time = now; powerup_spawn_interval = random.randint(10000, 30000)
                        powerup_type = random.choice(['invincible', 'extralife'])
                        powerup = PowerUp(hit_asteroid.rect.center, powerup_type)
                        all_sprites.add(powerup); powerups.add(powerup)
                    for _ in range(random.randint(5, 10)): all_sprites.add(Debris(hit_asteroid.rect.center))
                    size_map = {3: 'large', 2: 'medium', 1: 'small'}
                    all_sprites.add(Explosion(hit_asteroid.rect.center, size_map.get(hit_asteroid.size, 'small')))
                    if hit_asteroid.size > 1:
                        for _ in range(2):
                            new_asteroid = Asteroid(hit_asteroid.size - 1, pos=hit_asteroid.rect.center, target_pos=player.pos if random.random() < 0.5 else None)
                            all_sprites.add(new_asteroid); asteroids.add(new_asteroid)
                    hit_asteroid.kill()
            
            hits_on_star = pygame.sprite.groupcollide(star_enemy_group, bullets, False, True)
            for star in hits_on_star:
                star.health -= 1; star.hit_timer = 5
                if star.health <= 0:
                    score += 500;
                    for _ in range(50): all_sprites.add(Debris(star.rect.center))
                    all_sprites.add(Explosion(star.rect.center, 'large')); all_sprites.add(Explosion(star.rect.center, 'large'))
                    star.kill()
            
            hits_on_ships = pygame.sprite.groupcollide(enemy_ships, bullets, False, True)
            for ship in hits_on_ships:
                ship.health -= 1
                if ship.health <= 0: score += 50; all_sprites.add(Explosion(ship.rect.center, 'medium')); ship.kill()
            
            for shockwave in shockwaves:
                sw_hits_asteroids = pygame.sprite.spritecollide(shockwave, asteroids, False, pygame.sprite.collide_mask)
                for hit_asteroid in sw_hits_asteroids:
                    if hit_asteroid not in shockwave.hit_targets:
                        hit_asteroid.health -= 3; hit_asteroid.hit_timer = 5
                        if hit_asteroid.health <= 0:
                            score += 10;
                            for _ in range(random.randint(5, 10)): all_sprites.add(Debris(hit_asteroid.rect.center))
                            size_map = {3: 'large', 2: 'medium', 1: 'small'}
                            all_sprites.add(Explosion(hit_asteroid.rect.center, size_map.get(hit_asteroid.size, 'small')))
                            if hit_asteroid.size > 1:
                                for _ in range(2):
                                    new_asteroid = Asteroid(hit_asteroid.size - 1, pos=hit_asteroid.rect.center, target_pos=player.pos if random.random() < 0.5 else None)
                                    all_sprites.add(new_asteroid); asteroids.add(new_asteroid)
                            hit_asteroid.kill()
                        shockwave.hit_targets.add(hit_asteroid)
                
                sw_hits_ships = pygame.sprite.spritecollide(shockwave, enemy_ships, False, pygame.sprite.collide_mask)
                for ship in sw_hits_ships:
                    if ship not in shockwave.hit_targets:
                        ship.health -= 3
                        if ship.health <= 0:
                            score += 50; all_sprites.add(Explosion(ship.rect.center, 'medium')); ship.kill()
                        shockwave.hit_targets.add(ship)

            powerup_hits = pygame.sprite.spritecollide(player, powerups, True)
            for hit in powerup_hits:
                if hit.type == 'invincible': player.activate_invincibility()
                elif hit.type == 'extralife': lives += 2

            if not player.invincible:
                if pygame.sprite.spritecollide(player, asteroids, True):
                    if player.take_damage(25):
                        lives -= 1
                        if lives <= 0: game_over = True
                        else: player.pos = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2); player.reset_health()
                
                if pygame.sprite.spritecollide(player, star_enemy_group, False, pygame.sprite.collide_mask):
                    if player.take_damage(25):
                        lives -= 1
                        if lives <= 0: game_over = True
                        else: player.pos = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2); player.reset_health()
                
                if pygame.sprite.spritecollide(player, enemy_bullets, True, pygame.sprite.collide_mask):
                    if player.take_damage(25):
                        lives -= 1
                        if lives <= 0: game_over = True
                        else: player.pos = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2); player.reset_health()
                
                player_ship_hits = pygame.sprite.spritecollide(player, enemy_ships, True, pygame.sprite.collide_mask)
                if player_ship_hits:
                    if player.take_damage(25):
                        lives -= 1
                        if lives <= 0: game_over = True
                        else: player.pos = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2); player.reset_health()
                    for ship in player_ship_hits:
                        score += 50; all_sprites.add(Explosion(ship.rect.center, 'medium'))

        screen.fill(BLACK)
        for sprite in all_sprites:
            if hasattr(sprite, 'draw'): sprite.draw(screen)
            else: screen.blit(sprite.image, sprite.rect)
        
        draw_text(f"Score: {score}", 10, 10); draw_text(f"Lives: {lives}", SCREEN_WIDTH - 100, 10)
        
        total_seconds = elapsed_time // 1000; minutes = total_seconds // 60; seconds = total_seconds % 60
        time_str = f"{minutes:02}:{seconds:02}"; time_surf = font.render(time_str, True, WHITE)
        screen.blit(time_surf, time_surf.get_rect(centerx=SCREEN_WIDTH / 2, top=10))

        bar_x = SCREEN_WIDTH - 180; bar_y = SCREEN_HEIGHT - 30; bar_total_width = 150; bar_height = 20
        pygame.draw.rect(screen, BAR_BACKGROUND, (bar_x, bar_y, bar_total_width, bar_height), 2)
        cooldown_elapsed = now - player.last_shockwave_time
        if cooldown_elapsed < player.shockwave_cooldown:
            fill_percentage = cooldown_elapsed / player.shockwave_cooldown; fill_width = bar_total_width * fill_percentage
            pygame.draw.rect(screen, UI_BAR_COLOR, (bar_x + 1, bar_y + 1, fill_width - 2, bar_height - 2))
            draw_text_center("Shockwave", bar_x + bar_total_width / 2, bar_y + bar_height / 2, large_font)
        else:
            pygame.draw.rect(screen, UI_READY_COLOR, (bar_x + 1, bar_y + 1, bar_total_width - 2, bar_height - 2))
            draw_text_center("SHOCKWAVE READY", bar_x + bar_total_width / 2, bar_y + bar_height / 2, large_font, BLACK)
            
        if player.invincible:
            remaining_time = player.invincibility_duration - (now - player.invincible_timer)
            if remaining_time > 0:
                fill_percentage = remaining_time / player.invincibility_duration; bar_width = SCREEN_WIDTH * 0.4; bar_height = 10
                bar_x = (SCREEN_WIDTH - bar_width) / 2; bar_y = 35
                pygame.draw.rect(screen, BAR_BACKGROUND, (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(screen, INVINCIBLE_BAR_COLOR, (bar_x, bar_y, bar_width * fill_percentage, bar_height))

        if game_over:
            draw_text_center("GAME OVER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20, large_font)
            draw_text_center("Press 'R' to Restart", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40, font)
        
        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()