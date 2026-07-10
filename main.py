import pygame
import sys
import speech_recognition as sr

pygame.init()

# ---------------- SCREEN ----------------
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Voice Controlled Running Girl Game")
clock = pygame.time.Clock()

# ---------------- FONTS & COLORS ----------------
FONT_NAME = "comicsansms"
font_large = pygame.font.SysFont(FONT_NAME, 72, bold=True)
font_small = pygame.font.SysFont(FONT_NAME, 36, bold=True)
font_debug = pygame.font.SysFont("arial", 20, bold=True)

COLOR_TEXT_MAIN = (255, 235, 100)
COLOR_TEXT_SUB = (255, 255, 255)
COLOR_SHADOW = (40, 70, 130)

def draw_text_with_shadow(surface, text, font, color, shadow_color, position):
    shadow_surface = font.render(text, True, shadow_color)
    surface.blit(shadow_surface, (position[0] + 3, position[1] + 3))
    main_surface = font.render(text, True, color)
    surface.blit(main_surface, position)

# ---------------- BACKGROUND HELPER ----------------
def load_and_scale_bg(filename, target_height):
    try:
        img = pygame.image.load(filename).convert_alpha()
        aspect_ratio = img.get_rect().width / img.get_rect().height
        target_width = int(target_height * aspect_ratio)
        return pygame.transform.smoothscale(img, (max(target_width, WIDTH), target_height)), max(target_width, WIDTH)
    except:
        surf = pygame.Surface((WIDTH, HEIGHT))
        surf.fill((50, 50, 80))
        return surf, WIDTH

bg1, bg1_width = load_and_scale_bg("Layer_1.png", HEIGHT)
bg2, bg2_width = load_and_scale_bg("Layer_2.png", HEIGHT)
bg3, bg3_width = load_and_scale_bg("Layer_3.png", HEIGHT)
bg4, bg4_width = load_and_scale_bg("Layer_4.png", HEIGHT)

bg1_x = bg2_x = bg3_x = bg4_x = 0
bg4_speed, bg3_speed, bg2_speed, bg1_speed = 0.0, 0.5, 1.2, 2.5

# ---------------- PLAYER ----------------
try:
    sprite_sheet = pygame.image.load("girl.png").convert_alpha()
    frames = [pygame.transform.scale(sprite_sheet.subsurface((i * 128, 0, 128, 128)), (120, 120)) for i in range(6)]
except:
    frames = [pygame.Surface((120, 120))]
x, y = 100, 400
velocity_y, gravity, jump_power = 0, 1, -20
on_ground, current_frame, animation_speed = True, 0, 0.2

# ---------------- OBSTACLES ----------------
obstacles = []
SPAWN_OBSTACLE = pygame.USEREVENT
pygame.time.set_timer(SPAWN_OBSTACLE, 1500)

# ---------------- VOICE RECOGNITION ----------------
voice_jump_triggered = False
last_heard_text = "Mic Online: Say 'JUMP'"

def start_voice_recognition():
    global voice_jump_triggered, last_heard_text
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
    
    def callback(recognizer, audio):
        global voice_jump_triggered, last_heard_text
        try:
            text = recognizer.recognize_google(audio).lower()
            last_heard_text = f"Heard: '{text}'"
            if any(w in text for w in ["jump", "up", "gump", "job"]):
                voice_jump_triggered = True
        except: pass
    return recognizer.listen_in_background(mic, callback)

stop_listening = start_voice_recognition()

# ---------------- GAME LOOP ----------------
running, game_over = True, False

while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if not game_over and event.type == SPAWN_OBSTACLE: obstacles.append([WIDTH, 440]) # Adjusted spawn Y
        if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            obstacles.clear(); y = 400; game_over = False

    keys = pygame.key.get_pressed()
    if not game_over and on_ground and (keys[pygame.K_SPACE] or voice_jump_triggered):
        velocity_y = jump_power
        on_ground = False
        voice_jump_triggered = False

    if not game_over:
        velocity_y += gravity
        y += velocity_y
        if y >= 400: y = 400; velocity_y = 0; on_ground = True
        current_frame = (current_frame + animation_speed) % len(frames)
        
        bg1_x -= bg1_speed; bg2_x -= bg2_speed; bg3_x -= bg3_speed; bg4_x -= bg4_speed
        if bg1_x <= -bg1_width: bg1_x = 0
        
        for obs in obstacles:
            obs[0] -= 7
            # Updated collision box to match lower position
            if pygame.Rect(x + 40, y + 30, 40, 80).colliderect(pygame.Rect(obs[0], obs[1], 50, 40)):
                game_over = True
        obstacles = [obs for obs in obstacles if obs[0] > -50]

    screen.fill((0, 0, 0))
    for b, bx in [(bg4, bg4_x), (bg3, bg3_x), (bg2, bg2_x), (bg1, bg1_x)]:
        screen.blit(b, (bx, 0)); screen.blit(b, (bx + bg1_width, 0))
    
    screen.blit(frames[int(current_frame)], (x, y))
    
    # Draw Lowered White Cloud
    for ox, oy in obstacles:
        pygame.draw.circle(screen, (255, 255, 255), (ox + 15, oy + 25), 20)
        pygame.draw.circle(screen, (255, 255, 255), (ox + 35, oy + 25), 25)
        pygame.draw.circle(screen, (255, 255, 255), (ox + 25, oy + 10), 20)
        pygame.draw.rect(screen, (255, 255, 255), (ox + 15, oy + 25, 20, 15))
    
    screen.blit(font_debug.render(last_heard_text, True, (0, 255, 0)), (15, 15))
    
    if game_over:
        draw_text_with_shadow(screen, "GAME OVER", font_large, COLOR_TEXT_MAIN, COLOR_SHADOW, (210, 180))
        draw_text_with_shadow(screen, "Press [R] to Restart", font_small, COLOR_TEXT_SUB, COLOR_SHADOW, (245, 280))
    
    pygame.display.update()

stop_listening(wait_for_stop=False)
pygame.quit()
sys.exit()
