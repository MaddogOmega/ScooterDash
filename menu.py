import pygame
import pickle
import os
import time
import RPi.GPIO as GPIO # rpi-lgpio

# buttons
ACCEPT_PIN = 25
SELECT_PIN = 22

GPIO.setmode(GPIO.BCM)

GPIO.setup(ACCEPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # 0 is button pressed
GPIO.setup(SELECT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # 0 is button pressed
# Setup pygame window position
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,0) #(x,y)
# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1080, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT),pygame.FULLSCREEN)
pygame.display.set_caption("Menu")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BACKGROUND = (102, 50, 25)

# Fonts
font = pygame.font.Font("Westerngames.ttf", 74)
text_font = pygame.font.Font("Westerngames2.ttf", 120)

# Button dimensions
BUTTON_WIDTH, BUTTON_HEIGHT = 300, 100

# Button positions
button1_pos = (30, 410)
button2_pos = (30, 530)

# Screen options
screens = ["digital", "classic", "analog"]
selected_screen = None

# Load last saved screen
last_saved_screen = None
if os.path.exists("lastdash.txt"):
    with open("lastdash.txt", "rb") as f:
        data = pickle.load(f)
        last_saved_screen = data.get('Dash')
        
# Timer
start_time = time.time()

def draw_button(text, position):
    pygame.draw.rect(screen, (160, 99, 53), (*position, BUTTON_WIDTH, BUTTON_HEIGHT))
    text_surface = font.render(text, True, BLACK)
    text_rect = text_surface.get_rect(center=(position[0] + BUTTON_WIDTH // 2, position[1] + BUTTON_HEIGHT // 2))
    screen.blit(text_surface, text_rect)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

running = True
while running:
    screen.fill(BACKGROUND)
    
    draw_button("Select", button1_pos)
    draw_button("Accept", button2_pos)
    draw_text("Amigo il Bello 150", text_font, (10, 85, 163), 160, 220)
    draw_text(f"Current Dash: {last_saved_screen}", text_font, (10, 85, 163), 100, 720)
    
    if GPIO.input(SELECT_PIN) == GPIO.LOW:  # Button pressed
        selected_screen = screens[(screens.index(selected_screen) + 1) % len(screens)] if selected_screen else screens[0]
        time.sleep(0.3)  # Debounce delay

    if GPIO.input(ACCEPT_PIN) == GPIO.LOW:  # Button pressed
        if selected_screen:
            with open("lastdash.txt", "wb") as f:
                pickle.dump({'Dash': selected_screen}, f)
            GPIO.cleanup()  # Clean up GPIO
            print(f"load: {selected_screen}")
            if selected_screen == "analog":
                os.system("python analog.py")
                pygame.quit()
            if selected_screen == "classic":
                os.system("python classic.py")
                pygame.quit()
            if selected_screen == "digital":
                os.system("python digital.py")
                pygame.quit()
              # Quit Pygame to prevent GPIO busy error
            running = False
        time.sleep(0.3)  # Debounce delay
    
    if selected_screen:
        selected_text = font.render(f"Selected: {selected_screen}", True, BLACK)
        screen.blit(selected_text, (440, 500))
    
    if time.time() - start_time > 10: #30 for normal but testing 100
        if last_saved_screen:
            GPIO.cleanup()  # Clean up GPIO
            print(f"Auto-loaded screen: {last_saved_screen}")
            if last_saved_screen == "analog":
                os.system("python analog.py") and pygame.quit()
            if last_saved_screen == "classic":
                os.system("python classic.py") and pygame.quit()
            if last_saved_screen == "digital":
                os.system("python digital.py") and pygame.quit()
              # Quit Pygame to prevent GPIO busy error
        running = False
    
    pygame.display.flip()

pygame.quit()

