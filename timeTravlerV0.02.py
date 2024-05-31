import pygame
import random

pygame.init()
player_images = {
    'idle_right': pygame.image.load('playerImgR.png'),
    'idle_left': pygame.image.load('playerImgL.png'),
    'slice_right': pygame.image.load('playerImgRslice.png'),
    'slice_left': pygame.image.load('playerImgLslice.png')
}

class Player(pygame.sprite.Sprite):
    def __init__(self, x=100, y=100, hp=5):
        super().__init__()
        self.x = x
        self.y = y
        self.hp = hp
        self.swing = False
        self.swiFrame = 0
        self.direction = 'right'  
        self.image = player_images['idle_right']
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.x_change = 0
        self.y_change = 0
        self.invulnerable = False
        self.invuln_timer = 0
        self.invuln_duration = 120 #in frames NOT ms
        self.dashTime = 0

    def update(self, x_change, y_change):
        self.x = max(0, min(self.x + x_change, 1000 - self.rect.width))
        self.y = max(0, min(self.y + y_change, 800 - self.rect.height))
        self.x_change = x_change
        self.y_change = y_change
        self.rect.topleft = (self.x, self.y)
        if self.swing:
            self.image = player_images[f'slice_{self.direction}']
        else:
            self.image = player_images[f'idle_{self.direction}']
        if self.invulnerable:
            self.invuln_timer -= 1
            if self.invuln_timer <= 0:
                self.invulnerable = False
        if self.dashTime <= 0:
            self.dashTime = 0
        else:
            self.dashTime -= 1

    def hit(self):
        if not self.invulnerable:
            print("player hit")
            self.hp -= 1
            self.invulnerable = True
            self.invuln_timer = self.invuln_duration

    def slice(self):
        self.swing = True
        self.swiFrame = 100
        self.image = player_images['slice_right'] if self.x_change > 0 else player_images['slice_left']

    def sheath(self):
        if self.swiFrame == 0:
            self.swing = False
            self.image = player_images['idle_right'] if self.x_change < 0 else player_images['idle_left']
        else:
            self.swiFrame -= 1
    
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x=200, y=100, hp=1, varname=''):
        super().__init__()
        self.x = x
        self.y = y
        self.hp = hp
        self.varname = varname
        self.image = pygame.image.load('EnemyL.png')
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.y_change = 0

    def update(self, player, platforms):
        # Basic AI to move towards the player
        if self.rect.x < player.rect.x:
            self.image = pygame.image.load('EnemyR.png')
            self.rect.x += 2  # Move right towards the player
        elif self.rect.x > player.rect.x:
            self.image = pygame.image.load('EnemyL.png')
            self.rect.x -= 2  # Move left towards the player

        # If the enemy is below the player, it can jump
        self.y_change += 0.5
        self.rect.y += int(self.y_change)

        # Check for collision with platforms
        platform_collision = pygame.sprite.spritecollide(self, platforms, False)
        if platform_collision:
            # If the enemy hits the top of a platform, adjust its position
            self.rect.bottom = platform_collision[0].rect.top
            self.y_change = 0

        # Check if the enemy is on the ground or a platform before jumping
        on_ground_or_platform = self.rect.bottom >= 700 or platform_collision
        if on_ground_or_platform:
            # The enemy will jump if it's within 50px of the player on the x-axis
            if abs(self.rect.x - player.rect.x) <= 50 and (self.rect.bottom == 700 or platform_collision):
                if player.rect.bottom < self.rect.bottom - 50:
                    self.y_change = -15

        # Update the enemy's y position after all checks
        self.rect.y += int(self.y_change)

    def __str__(self):
        return(f"name: {self.varname}, x: {self.x}, y: {self.y}, hp: {self.hp}")
    
def check_collisions(player, enemies):
    # Check for collision between player and all enemies
    hits = pygame.sprite.spritecollide(player, enemies, False)
    for hit in hits:
        if player.swing:
            # Player is slicing, enemy takes damage
            hit.hp -= 1
            if hit.hp <= 0:
                enemies.remove(hit)  # Remove enemy if hp is 0 or less
        else:
            # Player is not slicing, player takes damage
            player.hit()
            if player.hp <= 0:
                return True  # Return True if player is out of hp
    return False  # Return False if player is still alive

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((255, 255, 255))  # White color for the platform, change as needed
        self.rect = self.image.get_rect(topleft=(x, y))

# Create platforms by specifying the x, y, width, and height
platform_group = pygame.sprite.Group()
platform1 = Platform(200, 500, 200, 10)
platform_group.add(platform1)

platform2 = Platform(600, 200, 200, 10)
platform_group.add(platform2)

# Add more platforms as needed
# platform2 = Platform(x, y, width, height)
# platform_group.add(platform2)

black = (0,0,0)
gameDisplay = pygame.display.set_mode((1000,800))
pygame.display.set_caption('TTv0.02')
clock = pygame.time.Clock()
quit = False
_map = 1
hitBackground = pygame.image.load('hitBKG.png')
jump = 0
player_group = pygame.sprite.Group()
p1 = Player()
player_group.add(p1)
x_change = 0
y_change = 0
y_reached = False
enemy_group = pygame.sprite.Group()
enemies = [Enemy(random.randint(400, 900), 600, varname=f'E{i+1}') for i in range(3)]
enemy_group.add(*enemies)
enemy_group = pygame.sprite.Group()
spawn_rate = 1000  # Initial spawn rate in milliseconds
last_spawn = pygame.time.get_ticks()

while not quit:
    
     # Gravity logic for the player
    if p1.y < 700 - p1.rect.height:  # Assuming 700 is the new ground level
        y_change += 0.5  # Gravity effect
    else:
        y_change = 0
        p1.y = 700 - p1.rect.height  # Adjust position to ground level
        jump = 0  # Allow the player to jump again

    # Apply gravity to the player
    p1.y += y_change

    # Gravity logic for enemies
    for enemy in enemy_group:
        if enemy.rect.bottom < 700:
            enemy.y_change += 0.5  # Gravity effect
        else:
            enemy.y_change = 0
            enemy.rect.bottom = 700  # Adjust position to ground level

        # Apply gravity to each enemy
        enemy.rect.y += enemy.y_change
    #time, what makes slash work
    p1.sheath()
    #event manager
    for event in pygame.event.get():
        if event.type == pygame.QUIT or p1.hp < 1:
            quit = True
        ############################
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:    
                x_change = -5
                p1.direction = 'left'
            elif event.key == pygame.K_d:
                x_change = 5
                p1.direction = 'right'
            if event.key == pygame.K_w and not jump:
                y_change -= 15
                jump = 1
            if event.key == pygame.K_SPACE:
                p1.slice()
            if event.key == pygame.K_LSHIFT:
                if p1.dashTime == 0:
                    if x_change != 0:
                        x_change *= 10
                        p1.dashTime = 90
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a or event.key == pygame.K_d:
                x_change = 0
        ######################
    current_time = pygame.time.get_ticks()
    if current_time - last_spawn > spawn_rate and len(enemy_group) < 6:
        enemy = Enemy(random.randint(0, 1000), 600)
        enemy_group.add(enemy)
        last_spawn = current_time
        spawn_rate = max(500, spawn_rate * 0.95)  # Increase spawn rate, but not less than 500ms
    #game updater
    
    game_over = check_collisions(p1, enemy_group)
    if game_over:
        quit = True  # End the game if player is out of hp
    platform_hits = pygame.sprite.spritecollide(p1, platform_group, False)
    if platform_hits and p1.y_change >= 0:
        p1.y = platform_hits[0].rect.top - p1.rect.height
        y_change = 0
        jump = 0
    p1.update(x_change,y_change)
    for enemy in enemy_group:
        platform_hits = pygame.sprite.spritecollide(enemy, platform_group, False)
        if platform_hits and enemy.y_change >= 0:
            enemy.y = platform_hits[0].rect.top - enemy.rect.height
        enemy.update(p1, platform_group)

    gameDisplay.fill(black)
    #background updater
    if p1.invuln_timer > 90:
        gameDisplay.blit(hitBackground, (0,0))
    else:
        gameDisplay.blit(pygame.image.load('Map1.png'), (0,0))
    platform_group.draw(gameDisplay)
    player_group.draw(gameDisplay)
    enemy_group.draw(gameDisplay)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
exit()