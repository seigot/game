import pygame
import sys
import random
import math

# Initialize the game
pygame.init()

# Set screen size
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong Game")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Game element settings
BALL_SIZE = 15
PADDLE_WIDTH, PADDLE_HEIGHT = 15, 80
PADDLE_SPEED = 7
BALL_SPEED = 10  # Increased ball speed from 7 to 10
COMPUTER_PADDLE_SPEED = 10  # Increased computer paddle speed

# Paddle class
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = PADDLE_SPEED
        self.score = 0

    def move_up(self):
        if self.rect.top > 0:
            self.rect.y -= self.speed

    def move_down(self):
        if self.rect.bottom < HEIGHT:
            self.rect.y += self.speed

    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)

# Ball class
class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)
        self.speed = BALL_SPEED
        self.dx = self.speed * random.choice([-1, 1])
        self.dy = 0

    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Collision with top and bottom walls
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.dy *= -1

    def bounce(self, paddle):
        # Calculate bounce angle based on collision position
        relative_intersect_y = (paddle.rect.centery - self.rect.centery) / (PADDLE_HEIGHT / 2)
        # Limit angle between -60 and 60 degrees
        bounce_angle = relative_intersect_y * 60
        
        # Convert angle to radians
        bounce_radians = math.radians(bounce_angle)
        
        # Calculate new velocity vector
        self.dx = -self.dx  # Reverse horizontal velocity
        self.dy = -self.speed * math.sin(bounce_radians)  # Set vertical velocity based on angle
        self.dx = self.speed * math.cos(bounce_radians) * (1 if self.dx > 0 else -1)  # Adjust horizontal velocity

    def reset(self):
        self.rect.center = (WIDTH//2, HEIGHT//2)
        self.dx = self.speed * random.choice([-1, 1])
        self.dy = 0

    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)

# Create game objects
player_paddle = Paddle(20, HEIGHT//2 - PADDLE_HEIGHT//2)
computer_paddle = Paddle(WIDTH - 20 - PADDLE_WIDTH, HEIGHT//2 - PADDLE_HEIGHT//2)
ball = Ball()

# Set font
try:
    font = pygame.font.SysFont('arial', 36)  # Use Arial font
except:
    font = pygame.font.Font(None, 36)  # Fallback to default font if Arial is not available

# Game loop
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Handle key input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        player_paddle.move_up()
    if keys[pygame.K_DOWN]:
        player_paddle.move_down()

    # Computer AI (track the ball)
    if computer_paddle.rect.centery < ball.rect.centery:
        computer_paddle.move_down()
    elif computer_paddle.rect.centery > ball.rect.centery:
        computer_paddle.move_up()

    # Move the ball
    ball.move()

    # Check paddle and ball collisions
    if ball.rect.colliderect(player_paddle.rect):
        ball.bounce(player_paddle)
    elif ball.rect.colliderect(computer_paddle.rect):
        ball.bounce(computer_paddle)

    # Score points
    if ball.rect.left <= 0:
        computer_paddle.score += 1
        ball.reset()
    elif ball.rect.right >= WIDTH:
        player_paddle.score += 1
        ball.reset()

    # Draw the screen
    screen.fill(BLACK)
    
    # Draw center line
    for y in range(0, HEIGHT, 20):
        pygame.draw.rect(screen, WHITE, pygame.Rect(WIDTH//2 - 5, y, 5, 10))
    
    # Display scores
    player_score_text = font.render(f"Player: {player_paddle.score}", True, WHITE)
    computer_score_text = font.render(f"Computer: {computer_paddle.score}", True, WHITE)
    screen.blit(player_score_text, (WIDTH//4 - 50, 20))
    screen.blit(computer_score_text, (3*WIDTH//4 - 100, 20))
    
    # Draw game elements
    player_paddle.draw()
    computer_paddle.draw()
    ball.draw()
    
    pygame.display.flip()
    clock.tick(60)  # Set FPS