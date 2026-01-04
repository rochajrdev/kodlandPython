import pgzrun
import math
import random
from pygame import Rect

# Configurações da Janela
WIDTH = 800
HEIGHT = 600
TITLE = "Kenney Platformer Adventure - Final"

# Estados e Variáveis Globais
MENU, GAME, WIN = 0, 1, 2
state = MENU
audio_active = True
score = 0
door_open = False
BLOCK_SIZE = 64  # Tamanho padrão dos blocos Kenney

class SpriteAnimator:
    """Animação cíclica para atender aos requisitos de animação de sprite."""
    def __init__(self, frames, interval=0.15):
        self.frames = frames
        self.interval = interval
        self.index = 0
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.interval:
            self.timer = 0
            self.index = (self.index + 1) % len(self.frames)

    @property
    def current(self):
        return self.frames[self.index]

class Player:
    """Herói com física de pulo ajustada e animações obrigatórias."""
    def __init__(self):
        self.idle_anim = SpriteAnimator(['character_beige_idle', 'character_beige_front'], 0.4)
        self.walk_anim = SpriteAnimator(['character_beige_walk_a', 'character_beige_walk_b'], 0.1)
        self.actor = Actor(self.idle_anim.current, (100, 450))
        self.hitbox = Rect(100, 450, 40, 60)
        self.vel_y = 0
        self.on_ground = False
        self.speed = 250

    def jump(self):
        if self.on_ground:
            self.vel_y = -18 
            self.on_ground = False
            if audio_active: sounds.sfx_jump.play()

    def update(self, dt, platforms):
        dx = 0
        if keyboard.left or keyboard.a: dx = -self.speed * dt
        elif keyboard.right or keyboard.d: dx = self.speed * dt

        # Movimento horizontal com bloqueio de bordas da tela
        self.hitbox.x += dx
        
        # --- BLOQUEIO LATERAIS DA TELA ---
        if self.hitbox.left < 0:
            self.hitbox.left = 0
        if self.hitbox.right > WIDTH:
            self.hitbox.right = WIDTH

        # Colisão horizontal com plataformas
        for p in platforms:
            if self.hitbox.colliderect(p):
                if dx > 0: self.hitbox.right = p.left
                if dx < 0: self.hitbox.left = p.right

        # Gravidade e vertical
        self.vel_y = min(self.vel_y + 0.8, 12)
        self.hitbox.y += self.vel_y
        self.on_ground = False

        for p in platforms:
            if self.hitbox.colliderect(p):
                if self.vel_y > 0:
                    self.hitbox.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.hitbox.top = p.bottom
                    self.vel_y = 0

        # Atualizar imagem do Actor conforme animação
        if dx != 0:
            self.walk_anim.update(dt)
            self.actor.image = self.walk_anim.current
        else:
            self.idle_anim.update(dt)
            self.actor.image = self.idle_anim.current
        
        self.actor.center = self.hitbox.center

class Enemy:
    """Inimigo que se move em seu território."""
    def __init__(self, platform_rect):
        self.anim = SpriteAnimator(['slime_normal_walk_a', 'slime_normal_walk_b'], 0.15)
        self.rect = Rect(platform_rect.centerx, platform_rect.top - 30, 40, 30)
        self.actor = Actor(self.anim.current)
        self.limit_l = platform_rect.left
        self.limit_r = platform_rect.right
        self.dir = 1

    def update(self, dt):
        self.rect.x += self.dir * 120 * dt
        if self.rect.right > self.limit_r or self.rect.left < self.limit_l:
            self.dir *= -1
        self.anim.update(dt)
        self.actor.image = self.anim.current
        self.actor.pos = self.rect.center

# Ajuste das plataformas: Cada uma com 256px de largura (4 blocos de 64px)
PLAT_WIDTH = BLOCK_SIZE * 4

player = Player()
PLATFORMS = [
    Rect(0, 550, WIDTH, 50),         # Chão (tela inteira)
    Rect(100, 420, PLAT_WIDTH, 25),  # Plat 1
    Rect(450, 320, PLAT_WIDTH, 25),  # Plat 2
    Rect(100, 220, PLAT_WIDTH, 25),  # Plat 3
    Rect(450, 130, PLAT_WIDTH, 25)   # Plat 4
]

enemies = [Enemy(PLATFORMS[2]), Enemy(PLATFORMS[3])]
coins = [Actor('block_coin', center=(p.centerx, p.top - 40)) for p in PLATFORMS[1:]]
exit_door = Actor('door_closed', (650, 90))

btn_start = Rect(300, 200, 200, 60)
btn_audio = Rect(300, 300, 200, 60)
btn_exit = Rect(300, 400, 200, 60)

def reset_game():
    global score, door_open, coins, state
    score = 0
    door_open = False
    exit_door.image = 'door_closed'
    player.hitbox.topleft = (100, 450)
    coins = [Actor('block_coin', center=(p.centerx, p.top - 40)) for p in PLATFORMS[1:]]
    state = GAME

def on_key_down(key):
    if state == GAME and key in (keys.SPACE, keys.UP, keys.W):
        player.jump()

def update(dt):
    global state, score, door_open
    if state == GAME:
        player.update(dt, PLATFORMS)
        for e in enemies:
            e.update(dt)
            if player.hitbox.colliderect(e.rect):
                if audio_active: sounds.sfx_hurt.play()
                player.hitbox.topleft = (100, 450)
        
        for c in coins[:]:
            if player.hitbox.colliderect(c._rect):
                coins.remove(c)
                score += 10
                if audio_active: sounds.sfx_coin.play()

        if not coins and not door_open:
            door_open = True
            exit_door.image = 'door_open'
        
        if door_open and player.hitbox.colliderect(exit_door._rect):
            state = WIN

def draw():
    global state, audio_active
    screen.clear()
    screen.fill((135, 206, 235))

    if state == MENU:
        screen.draw.filled_rect(btn_start, (46, 204, 113))
        screen.draw.text("JOGAR", center=btn_start.center, color="white", fontsize=40)
        color_audio = (52, 152, 219) if audio_active else (149, 165, 166)
        screen.draw.filled_rect(btn_audio, color_audio)
        screen.draw.text("SOM: ON" if audio_active else "SOM: OFF", center=btn_audio.center, color="white", fontsize=40)
        screen.draw.filled_rect(btn_exit, (231, 76, 60))
        screen.draw.text("SAIR", center=btn_exit.center, color="white", fontsize=40)
    
    elif state == GAME:
        for p in PLATFORMS:
            for x in range(p.left, p.right, BLOCK_SIZE):
                screen.blit("terrain_grass_block", (x, p.top))
        
        exit_door.draw()
        for c in coins: c.draw()
        for e in enemies: e.actor.draw()
        player.actor.draw()
        screen.draw.text(f"Moedas: {score}", (20, 20), color="white", fontsize=30)

    elif state == WIN:
        screen.draw.text("VOCÊ VENCEU!", center=(400, 250), fontsize=80, color="orange")
        screen.draw.text("SPACE para o Menu", center=(400, 350), fontsize=30)
        if keyboard.space: state = MENU

def on_mouse_down(pos):
    global audio_active, state
    if state == MENU:
        if btn_start.collidepoint(pos): reset_game()
        elif btn_audio.collidepoint(pos): audio_active = not audio_active
        elif btn_exit.collidepoint(pos): exit()

pgzrun.go()