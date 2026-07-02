import pygame
import sys
import random
import threading
import speech_recognition as sr

pygame.init()

# ---------------- SCREEN ----------------
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Voice Controlled Running Girl Game")

clock = pygame.time.Clock()

# ---------------- THEMED FONTS & COLORS ----------------
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

# ---------------- BACKGROUND HELPER FUNCTION ----------------
def load_and_scale_bg(filename, target_height):
    img = pygame.image.load(filename).convert_alpha()
    img_rect = img.get_rect()
    aspect_ratio = img_rect.width / img_rect.height
    target_width = int(target_height * aspect_ratio)
    if target_width < WIDTH:
        target_width = WIDTH
    return pygame.transform.smoothscale(img, (target_width, target_height)), target_width

bg1, bg1_width = load_and_scale_bg("Layer_1.png", HEIGHT)
bg2, bg2_width = load_and_scale_bg("Layer_2.png", HEIGHT)
bg3, bg3_width = load_and_scale_bg("Layer_3.png", HEIGHT)
bg4, bg4_width = load_and_scale_bg("Layer_4.png", HEIGHT)

bg1_x = bg2_x = bg3_x = bg4_x = 0

bg4_speed = 0.0
bg3_speed = 0.5
bg2_speed = 1.2
bg1_speed = 2.5

# ---------------- LOAD SPRITE SHEET ----------------
sprite_sheet = pygame.image.load("girl.png").convert_alpha()
frame_width, frame_height = 128, 128
num_frames = 6

frames = []
for i in range(num_frames):
    frame = sprite_sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
    frame = pygame.transform.scale(frame, (120, 120))
    frames.append(frame)

# ---------------- PLAYER ----------------
x, y = 100, 400
velocity_y = 0
gravity = 1
jump_power = -18
on_ground = True

current_frame = 0
animation_speed = 0.2

# ---------------- OBSTACLES ----------------
obstacles = []
obstacle_width, obstacle_height = 50, 80
obstacle_speed = 6

SPAWN_OBSTACLE = pygame.USEREVENT
pygame.time.set_timer(SPAWN_OBSTACLE, 1500)

running = True
game_over = False

# ---------------- HIGH-SPEED GOOGLE VOICE PROCESSOR ----------------
voice_jump_triggered = False
last_heard_text = "Calibrating Mic..."

def ultra_fast_speech_listener():
    global voice_jump_triggered, last_heard_text, running
    
    recognizer = sr.Recognizer()
    
    # Settings to lower processing lag for single words
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = 600  # High threshold ignores normal breathing/typing noises
    recognizer.pause_threshold = 0.3   # Instantly process audio 300ms after you stop speaking
    
    try:
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
        last_heard_text = "Mic Online: Say 'JUMP'"
    except Exception as e:
        last_heard_text = "Mic Error! Grant OS Mic Access."
        return

    while running:
        try:
            with mic as source:
                # Capture microscopic speech bursts (max 1 second chunks)
                audio = recognizer.listen(source, timeout=0.8, phrase_time_limit=1.0)
            
            # Send small audio burst up to Google API
            text = recognizer.recognize_google(audio).lower()
            last_heard_text = f"Heard: '{text}'"
            
            # Look for explicit intent or common phonetically close words
            if "jump" in text or "up" in text or "gump" in text or "job" in text:
                voice_jump_triggered = True
                
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            # Keeps scanning quietly through empty background gaps
            continue
        except Exception:
            continue

# Launch the word recognition background thread
voice_thread = threading.Thread(target=ultra_fast_speech_listener, daemon=True)
voice_thread.start()

# ---------------- GAME LOOP ----------------
while running:
    clock.tick(60)

    # -------- EVENTS --------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if not game_over and event.type == SPAWN_OBSTACLE:
            obstacles.append([WIDTH, 450])
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                obstacles.clear()
                y = 400
                velocity_y = 0
                bg1_x = bg2_x = bg3_x = bg4_x = 0
                game_over = False

    # -------- INPUT (KEYBOARD + VOICE WORD DETECTION) --------
    keys = pygame.key.get_pressed()
    
    if not game_over and on_ground:
        if keys[pygame.K_SPACE] or voice_jump_triggered:
            velocity_y = jump_power
            on_ground = False
            
    voice_jump_triggered = False  # Reset flag immediately

    # -------- PHYSICS --------
    if not game_over:
        velocity_y += gravity
        y += velocity_y
        if y >= 400:
            y = 400
            velocity_y = 0
            on_ground = True

    # -------- ANIMATION --------
    if not game_over:
        current_frame += animation_speed
        if current_frame >= num_frames:
            current_frame = 0

    # -------- BACKGROUND SCROLLING --------
    if not game_over:
        bg1_x -= bg1_speed
        bg2_x -= bg2_speed
        bg3_x -= bg3_speed
        bg4_x -= bg4_speed

        if bg1_x <= -bg1_width: bg1_x = 0
        if bg2_x <= -bg2_width: bg2_x = 0
        if bg3_x <= -bg3_width: bg3_x = 0
        if bg4_x <= -bg4_width: bg4_x = 0

    # -------- OBSTACLES PHYSICS --------
    if not game_over:
        for obs in obstacles:
            obs[0] -= obstacle_speed
        obstacles = [obs for obs in obstacles if obs[0] > -obstacle_width]

    # -------- COLLISION --------
    player_rect = pygame.Rect(x + 25, y + 20, 70, 90)
    if not game_over:
        for obs in obstacles:
            obstacle_rect = pygame.Rect(obs[0] + 5, obs[1] + 5, obstacle_width - 10, obstacle_height - 10)
            if player_rect.colliderect(obstacle_rect):
                game_over = True

    # -------- DRAW --------
    screen.fill((0, 0, 0))

    # Parallax Background Blitting
    screen.blit(bg4, (bg4_x, 0))
    screen.blit(bg4, (bg4_x + bg4_width, 0))
    screen.blit(bg3, (bg3_x, 0))
    screen.blit(bg3, (bg3_x + bg3_width, 0))
    screen.blit(bg2, (bg2_x, 0))
    screen.blit(bg2, (bg2_x + bg2_width, 0))
    screen.blit(bg1, (bg1_x, 0))
    screen.blit(bg1, (bg1_x + bg1_width, 0))

    # Draw Player
    frame_index = int(current_frame) % num_frames
    screen.blit(frames[frame_index], (x, y))

    # Draw Obstacles (White Cloud Shape)
    for obs in obstacles:
        ox, oy = obs[0], obs[1]
        cloud_color = (255, 255, 255)
        pygame.draw.circle(screen, cloud_color, (ox + 15, oy + 45), 25)
        pygame.draw.circle(screen, cloud_color, (ox + 30, oy + 30), 30)
        pygame.draw.circle(screen, cloud_color, (ox + 45, oy + 45), 22)
        pygame.draw.rect(screen, cloud_color, (ox + 10, oy + 35, 35, 25))

    # --- REAL-TIME SPEECH STATUS OVERLAY ---
    # Shows exactly what the system processes
    status_color = (255, 0, 0) if "Error" in last_heard_text else (0, 255, 0)
    status_surf = font_debug.render(last_heard_text, True, status_color)
    screen.blit(status_surf, (15, 15))

    # Game Over Overlay
    if game_over:
        draw_text_with_shadow(
            screen, "GAME OVER", font_large, 
            COLOR_TEXT_MAIN, COLOR_SHADOW, (210, 180)
        )
        draw_text_with_shadow(
            screen, "Press [R] to Restart", font_small, 
            COLOR_TEXT_SUB, COLOR_SHADOW, (245, 280)
        )

    pygame.display.update()

pygame.quit()
sys.exit()