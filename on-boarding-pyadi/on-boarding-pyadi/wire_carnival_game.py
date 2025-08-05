import math
import time
import argparse
import adi
import pygame
import sys
import random

parser = argparse.ArgumentParser(description="Wire Carnival Game using ADXL355")
parser.add_argument (
    "-u",
    default =["ip:analog.local"], #Tto do:ipi
    help="-u (arg) URI of target device;s context, eg: 'ip:analog.local',\'ip:192.168.2.1',\'serial:COM4,115200,8n1n'",
    action="store",
    nargs="*",
)

args =parser.parse_args()
my_uri = args.u[0]

#screen and game configuration
screen_width = 800
screen_height = 600

#colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)

#Set up ADXL355
print("uri: " + str(my_uri))

my_acc = adi.adxl355(uri=my_uri)

#Setup the acceleration values

def get_accel():
    accel_x = (my_acc.accel_x.raw * my_acc.accel_x.scale)
    accel_y = (my_acc.accel_y.raw * my_acc.accel_y.scale)
    accel_z = (my_acc.accel_z.raw * my_acc.accel_z.scale)
    return accel_x, accel_y

#Setup pygame
pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()
running = True
gameover = False
font = pygame.font.Font(None, 36) 

# Timer setup
import time
start_time = time.time()
final_time = None

#initialize game variables
player_radius = 10
wire_width = 200 
scroll_speed = 2
sensitivity = 0.4

# path settings
import math
amplitude = 100  
frequency = 2 * math.pi / screen_height * 3
wire_path = [
    int(screen_width // 2 + amplitude * math.sin(frequency * y))
    for y in range(screen_height)
]

# phase for moving sine wave
phase = 0

# player position
player_y = screen_height - 50
player_x = float(wire_path[int(player_y)])

#game loop

while running:

    screen.fill(white)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not gameover:


        accel_x, accel_y = get_accel()

        # Apply deadzone to both axes
        if abs(accel_x) < 0.2:
            accel_x = 0
        if abs(accel_y) < 0.2:
            accel_y = 0

        #player movement using adxl355 accelerometer
        player_x += accel_y * sensitivity
        player_y += accel_x * sensitivity

        player_x = max(0, min(screen_width, player_x))
        player_y = max(0, min(screen_height - 1, player_y))

        #draw the wire path as a moving sine wave
        wire_path.pop(0)
        phase += 0.05
        new_y = screen_height - 1
        new_x = int(screen_width // 2 + amplitude * math.sin(frequency * new_y + phase))
        wire_path.append(new_x)

        # Prepare points for the left and right boundaries of the road
        left_edge = [(center_x - wire_width // 2, y) for y, center_x in enumerate(wire_path)]
        right_edge = [(center_x + wire_width // 2, y) for y, center_x in enumerate(wire_path)]
        # Draw only the two boundary lines
        if len(left_edge) > 1:
            pygame.draw.aalines(screen, black, False, left_edge)
        if len(right_edge) > 1:
            pygame.draw.aalines(screen, black, False, right_edge)
        
        #draw player
        pygame.draw.circle(screen, red, (int(player_x), player_y), player_radius)

        #check for collision
        current_y = int(player_y)
        if 0 <= current_y < screen_height:
            wire_center = wire_path[current_y]
            left_edge_x = wire_center - wire_width // 2
            right_edge_x = wire_center + wire_width // 2
            # Check collision using the player's radius
            if (player_x - player_radius) < left_edge_x or (player_x + player_radius) > right_edge_x:
                gameover = True
                if final_time is None:
                    final_time = int(time.time() - start_time)


    # Draw timer/clock
    if gameover and final_time is not None:
        display_time = final_time
    else:
        display_time = int(time.time() - start_time)
    timer_text = font.render(f"Time: {display_time}s", True, black)
    screen.blit(timer_text, (10, 10))

    if gameover:
        text = font.render("Game Over! Press R to Restart", True, red)
        screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()    


