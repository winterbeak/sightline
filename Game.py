import pygame
import sys

import constants
import events

pygame.init()

final_display = pygame.display.set_mode(constants.SCREEN_SIZE)
clock = pygame.time.Clock()


def screen_update(fps):
    pygame.display.flip()
    final_display.fill(constants.BLACK)
    clock.tick(fps)


pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

while True:
    events.update()
    if events.keys.pressed_key == pygame.K_ESCAPE:
        break

    screen_update(60)

pygame.quit()
sys.exit()
