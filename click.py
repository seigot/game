import pygame
import sys
import time
import random
import math

# Initialize the game
pygame.init()

# Set screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("30-Second Click Counter Game")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
GOLD = (255, 215, 0)
PURPLE = (147, 112, 219)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
PINK = (255, 105, 180)
ORANGE = (255, 165, 0)
NEON_GREEN = (57, 255, 20)

# より鮮やかな色のパレット
RAINBOW_COLORS = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, MAGENTA, CYAN, PINK, NEON_GREEN]

# Set up fonts
title_font = pygame.font.Font(None, 64)
font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 36)

# Game variables
click_count = 0
game_active = False
start_time = 0
remaining_time = 30
high_score = 0
title_angle = 0  # For title animation
celebration_active = False
celebration_start_time = 0
celebration_duration = 3  # seconds

# 派手なパーティクルシステム
class Particle:
    def __init__(self, x, y, color=None, size_range=(2, 5), speed_range=(2, 5), lifetime_range=(20, 40)):
        self.x = x
        self.y = y
        self.size = random.randint(*size_range)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(*speed_range)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.randint(*lifetime_range)
        self.color = color if color else random.choice(RAINBOW_COLORS)
        self.alpha = 255  # For fade effect
        self.start_size = self.size  # 初期サイズを保存

        # パーティクルのタイプをランダムに選択
        self.particle_type = random.choice(["circle", "star", "square", "flash"])
        
        # 軌道修正用の変数
        self.angle_change = random.uniform(-0.1, 0.1)  # 軌道の曲がり具合
        self.pulse_speed = random.uniform(0.05, 0.2)   # 脈動のスピード
        self.pulse_phase = random.uniform(0, 2 * math.pi)  # 脈動の初期フェーズ

    def update(self):
        # 軌道の変更（曲がる動き）
        angle = math.atan2(self.vy, self.vx)
        angle += self.angle_change
        speed = math.sqrt(self.vx**2 + self.vy**2)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        # 通常の移動更新
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        
        # サイズの脈動
        pulse = math.sin(time.time() * self.pulse_speed * 10 + self.pulse_phase)
        pulse_multiplier = 1 + pulse * 0.3  # サイズを±30%変化させる
        self.size = max(0, self.start_size * pulse_multiplier * (self.lifetime / 40))
        
        # フェードアウト効果
        self.alpha = int((self.lifetime / 40) * 255)

    def draw(self):
        if self.size > 0:
            # パーティクル用のサーフェスを作成（アルファチャンネル付き）
            size_int = int(self.size * 2)
            if size_int < 1:
                size_int = 1  # 最小サイズを確保
            particle_surface = pygame.Surface((size_int, size_int), pygame.SRCALPHA)
            
            try:
                # カラー値を確保（RGB値のみ取得）
                if isinstance(self.color, tuple) and len(self.color) >= 3:
                    r, g, b = self.color[0], self.color[1], self.color[2]
                else:
                    r, g, b = 255, 255, 255  # デフォルト色（白）
                
                # アルファ値が範囲内にあることを確認
                alpha = max(0, min(255, self.alpha))
                
                # パーティクルのタイプに応じて描画
                if self.particle_type == "circle":
                    pygame.draw.circle(particle_surface, (r, g, b, alpha),
                                     (size_int//2, size_int//2), self.size)
                elif self.particle_type == "star":
                    # 簡易的な星形
                    points = []
                    for i in range(10):
                        angle = math.pi/5 * i
                        radius = self.size if i % 2 == 0 else self.size/2
                        x = size_int//2 + radius * math.cos(angle)
                        y = size_int//2 + radius * math.sin(angle)
                        points.append((x, y))
                    if len(points) >= 3:  # 少なくとも3点必要
                        pygame.draw.polygon(particle_surface, (r, g, b, alpha), points)
                elif self.particle_type == "square":
                    rect_size = int(self.size * 1.5)
                    if rect_size < 1:
                        rect_size = 1  # 最小サイズを確保
                        
                    # 回転効果を加える
                    rot_angle = (time.time() * 100) % 360
                    rot_surface = pygame.Surface((rect_size, rect_size), pygame.SRCALPHA)
                    
                    # 四角形を描画
                    pygame.draw.rect(rot_surface, (r, g, b, alpha), pygame.Rect(0, 0, rect_size, rect_size))
                    
                    # 回転させて描画
                    rot_surface = pygame.transform.rotate(rot_surface, rot_angle)
                    rot_rect = rot_surface.get_rect(center=(size_int//2, size_int//2))
                    particle_surface.blit(rot_surface, rot_rect)
                elif self.particle_type == "flash":
                    # 光のフラッシュ効果
                    glow_radius = int(self.size * 3)
                    for i in range(glow_radius, 0, -1):
                        # 中心に向かって徐々に明るくなる
                        brightness = 1 - (i / glow_radius)
                        flash_alpha = int(alpha * brightness)
                        # アルファ値の範囲チェック
                        flash_alpha = max(0, min(255, flash_alpha))
                        pygame.draw.circle(particle_surface, (r, g, b, flash_alpha),
                                         (size_int//2, size_int//2), i)
                
                screen.blit(particle_surface, (int(self.x - size_int//2), int(self.y - size_int//2)))
            except Exception as e:
                # エラー時は安全に白色で円を描画
                try:
                    pygame.draw.circle(particle_surface, (255, 255, 255, 100),
                                     (size_int//2, size_int//2), max(1, self.size))
                    screen.blit(particle_surface, (int(self.x - size_int//2), int(self.y - size_int//2)))
                except:
                    pass  # 最後の安全策：描画をスキップ

class CelebrationParticle(Particle):
    def __init__(self, x, y):
        super().__init__(x, y, color=random.choice(RAINBOW_COLORS), 
                        size_range=(5, 12), speed_range=(4, 10), lifetime_range=(60, 100))
        self.vy -= random.uniform(2, 5)  # 初期上向き速度
        self.gravity = 0.1
        self.trail_particles = []
        self.trail_counter = 0

    def update(self):
        # 基本的な動きの更新
        self.x += self.vx
        self.vy += self.gravity
        self.y += self.vy
        self.lifetime -= 1
        
        # サイズの脈動
        pulse = math.sin(time.time() * self.pulse_speed * 10 + self.pulse_phase)
        pulse_multiplier = 1 + pulse * 0.3
        self.size = max(0, self.start_size * pulse_multiplier * (self.lifetime / 80))
        
        # アルファ値の更新
        self.alpha = min(255, int((self.lifetime / 80) * 255))
        
        # 軌跡パーティクルの追加
        self.trail_counter += 1
        if self.trail_counter >= 2:  # 2フレームごとに軌跡を追加
            self.trail_counter = 0
            if random.random() < 0.5:  # 50%の確率で軌跡を追加
                trail = Particle(self.x, self.y, color=self.color, 
                               size_range=(1, 3), speed_range=(0.5, 1.5), lifetime_range=(10, 20))
                trail.vx = trail.vx * 0.2  # 軌跡の速度を遅くする
                trail.vy = trail.vy * 0.2
                self.trail_particles.append(trail)
        
        # 軌跡パーティクルの更新
        for particle in self.trail_particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.trail_particles.remove(particle)
    
    def draw(self):
        # 軌跡パーティクルの描画
        for particle in self.trail_particles:
            particle.draw()
        
        # メインパーティクルの描画
        super().draw()

particles = []
celebration_particles = []

# Button setup
start_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 25, 200, 50)

# Game loop
clock = pygame.time.Clock()

def draw_text(text, font, color, x, y, centered=True):
    text_surface = font.render(text, True, color)
    if centered:
        text_rect = text_surface.get_rect(center=(x, y))
    else:
        text_rect = text_surface.get_rect(topleft=(x, y))
    screen.blit(text_surface, text_rect)

def create_particles(x, y, count=40):  # パーティクル数を増加
    # メインの爆発を作成
    for _ in range(count):
        particles.append(Particle(x, y, 
                                size_range=(5, 12),  # より大きなパーティクル
                                speed_range=(5, 12),  # より速いパーティクル
                                lifetime_range=(40, 80)))  # より長い寿命
    
    # リング状の爆発エフェクト
    num_ring_particles = 24
    for i in range(num_ring_particles):
        angle = 2 * math.pi * i / num_ring_particles
        speed = random.uniform(8, 15)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        particle = Particle(x, y, color=random.choice(RAINBOW_COLORS),
                          size_range=(4, 8), speed_range=(1, 1), lifetime_range=(30, 60))
        particle.vx = vx
        particle.vy = vy
        particles.append(particle)
    
    # 第二爆発を作成（異なる色）
    for _ in range(count // 2):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(15, 30)
        new_x = x + math.cos(angle) * distance
        new_y = y + math.sin(angle) * distance
        particles.append(Particle(new_x, new_y,
                                color=random.choice([GOLD, CYAN, PINK, NEON_GREEN]),
                                size_range=(3, 9),
                                speed_range=(3, 9),
                                lifetime_range=(30, 60)))
    
    # フラッシュエフェクト（クリック位置に大きな光の輪）
    flash = pygame.Surface((200, 200), pygame.SRCALPHA)
    for radius in range(100, 0, -10):
        alpha = int(150 * (1 - radius/100))
        pygame.draw.circle(flash, (*GOLD[:3], alpha), (100, 100), radius)
    screen.blit(flash, (x - 100, y - 100))

def create_celebration_effect():
    global celebration_active, celebration_start_time
    celebration_active = True
    celebration_start_time = time.time()
    
    # お祝いパーティクルを作成
    for _ in range(150):  # パーティクル数を増加
        x = random.randint(0, WIDTH)
        y = random.randint(HEIGHT//3, HEIGHT)
        celebration_particles.append(CelebrationParticle(x, y))
    
    # 画面全体にフラッシュエフェクト
    flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(flash, (255, 255, 255, 100), flash.get_rect())
    screen.blit(flash, (0, 0))

def draw_gradient_text(text, font, start_color, end_color, x, y, angle=0):
    # テキスト用のサーフェスを作成
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=(x, y))
    
    # グラデーションサーフェスを作成
    gradient_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
    width, height = text_surface.get_size()
    
    # 時間依存のグラデーション
    t = time.time() % 5  # 5秒周期
    phase = t / 5
    
    for i in range(width):
        # グラデーション色を計算
        ratio = (i / width + phase) % 1
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        color = (r, g, b, 255)
        
        # 現在のグラデーション色で垂直線を描画
        pygame.draw.line(gradient_surface, color, (i, 0), (i, height))
    
    # テキストにグラデーションを適用
    gradient_surface.blit(text_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    # アニメーション用に回転
    rotated_surface = pygame.transform.rotate(gradient_surface, math.sin(angle) * 3)
    rotated_rect = rotated_surface.get_rect(center=text_rect.center)
    
    # テキストを描画
    screen.blit(rotated_surface, rotated_rect)

def draw_celebration_text(text, y_offset=0):
    current_time = time.time() - celebration_start_time
    scale = 1 + math.sin(current_time * 5) * 0.3  # 拡大縮小効果
    color_index = int(current_time * 15) % len(RAINBOW_COLORS)  # 色の変化を速く
    
    # スケーリングされたテキストを作成
    text_surface = title_font.render(text, True, RAINBOW_COLORS[color_index])
    scaled_width = int(text_surface.get_width() * scale)
    scaled_height = int(text_surface.get_height() * scale)
    scaled_surface = pygame.transform.scale(text_surface, (scaled_width, scaled_height))
    
    # テキストの位置決め
    text_rect = scaled_surface.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
    
    # グロー効果の追加
    glow_radius = 10
    for i in range(glow_radius, 0, -1):
        alpha = 10 + i * 5
        glow_color = RAINBOW_COLORS[(color_index + 2) % len(RAINBOW_COLORS)]
        glow_surface = title_font.render(text, True, glow_color)
        glow_rect = glow_surface.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
        glow_rect.x -= i // 2
        glow_rect.y -= i // 2
        glow_surface = pygame.transform.scale(glow_surface, (scaled_width + i, scaled_height + i))
        glow_rect = glow_surface.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
        screen.blit(glow_surface, glow_rect)
    
    screen.blit(scaled_surface, text_rect)

def draw_game():
    global celebration_active
    screen.fill(BLACK)
    
    if not game_active:
        # ゲーム開始前または終了後の画面
        # グラデーションとアニメーション付きのタイトルを描画
        draw_gradient_text("30-Second Click Counter Game", title_font, 
                         GOLD, MAGENTA, WIDTH//2, HEIGHT//4, title_angle)
        
        # お祝いエフェクトがアクティブの場合
        if celebration_active:
            current_time = time.time() - celebration_start_time
            if current_time < celebration_duration:
                # お祝いパーティクルの更新と描画
                for particle in celebration_particles[:]:
                    particle.update()
                    particle.draw()
                    if particle.lifetime <= 0:
                        celebration_particles.remove(particle)
                
                # お祝いテキストを描画
                draw_celebration_text("NEW RECORD!", -50)
                draw_celebration_text(f"{high_score} CLICKS!", 50)
            else:
                celebration_active = False
                celebration_particles.clear()
        
        # グロー効果付きのスタートボタンを描画
        pulse = (math.sin(time.time() * 3) + 1) / 2  # 0～1の間で脈動
        glow_radius = int(5 + pulse * 10)  # 5～15の間で変化
        for i in range(glow_radius, 0, -1):
            alpha = 100 - i * 5
            glow_surface = pygame.Surface((start_button.width + i*2, start_button.height + i*2), pygame.SRCALPHA)
            glow_color = (int(GREEN[0] * (1-pulse) + CYAN[0] * pulse),
                         int(GREEN[1] * (1-pulse) + CYAN[1] * pulse),
                         int(GREEN[2] * (1-pulse) + CYAN[2] * pulse), alpha)
            pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=10+i)
            screen.blit(glow_surface, (start_button.x - i, start_button.y - i))
        
        pygame.draw.rect(screen, GREEN, start_button, border_radius=10)
        draw_text("START", font, BLACK, WIDTH//2, HEIGHT//2)
        
        # 前回のスコアとハイスコアを強調表示
        if click_count > 0:
            draw_text(f"Last Score: {click_count} clicks", small_font, GOLD, WIDTH//2, HEIGHT//2 + 100)
        draw_text(f"High Score: {high_score} clicks", small_font, MAGENTA, WIDTH//2, HEIGHT//2 + 150)
        
        # 遊び方の説明を強調表示
        instruction_y1 = HEIGHT - 80
        instruction_y2 = HEIGHT - 40
        draw_text("How to play: Press the START button and click", small_font, WHITE, WIDTH//2, instruction_y1)
        draw_text("anywhere on the screen as many times as possible in 30 seconds!", small_font, WHITE, WIDTH//2, instruction_y2)
    else:
        # ゲームプレイ中の画面
        # 残り時間を表示
        time_color = WHITE
        if remaining_time <= 5:
            # 残り時間が少ない場合は点滅効果
            if int(time.time() * 4) % 2:
                time_color = RED
        draw_text(f"Time Left: {int(remaining_time)} seconds", font, time_color, WIDTH//2, 40)
        
        # クリック数を表示（数字が大きくなるとサイズも大きく）
        click_scale = min(1.5, 1 + click_count / 200)  # 最大1.5倍まで大きく
        click_font = pygame.font.Font(None, int(48 * click_scale))
        draw_text(f"Clicks: {click_count}", click_font, WHITE, WIDTH//2, 100)
        
        # パーティクルの更新と描画
        for particle in particles[:]:
            particle.update()
            particle.draw()
            if particle.lifetime <= 0:
                particles.remove(particle)
        
        # 残り時間に応じた励ましメッセージ
        if remaining_time > 20:
            draw_text("Keep clicking!", small_font, NEON_GREEN, WIDTH//2, HEIGHT - 40)
        elif remaining_time > 10:
            draw_text("Maintain that pace!", small_font, CYAN, WIDTH//2, HEIGHT - 40)
        elif remaining_time > 5:
            draw_text("Time is running out! Hurry!", small_font, ORANGE, WIDTH//2, HEIGHT - 40)
        else:
            # 残り時間が少ない場合は点滅効果
            if int(time.time() * 4) % 2:
                draw_text("FINAL SPRINT!!", title_font, RED, WIDTH//2, HEIGHT - 40)
            else:
                draw_text("FINAL SPRINT!!", title_font, YELLOW, WIDTH//2, HEIGHT - 40)

running = True
while running:
    current_time = time.time()
    
    # タイトルアニメーションの更新
    title_angle += 0.05
    
    # 残り時間の計算（ゲーム中のみ）
    if game_active:
        elapsed_time = current_time - start_time
        remaining_time = 30 - elapsed_time
        
        # 時間切れの処理
        if remaining_time <= 0:
            game_active = False
            remaining_time = 0
            # ハイスコアの更新とお祝いエフェクトの発動
            if click_count > high_score:
                high_score = click_count
                create_celebration_effect()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            if game_active:
                # ゲームプレイ中のクリック処理
                click_count += 1
                create_particles(mouse_pos[0], mouse_pos[1])  # クリック位置でパーティクルを作成
            elif start_button.collidepoint(mouse_pos):
                # ゲーム開始
                game_active = True
                click_count = 0
                start_time = time.time()
                remaining_time = 30
                particles.clear()  # 既存のパーティクルをクリア
    
    # ゲーム画面の描画
    draw_game()
    
    pygame.display.flip()
    clock.tick(60)  # FPSの設定

pygame.quit()
sys.exit()