import pygame
import sys
import math

import geometry
import constants
import events
import player
import levels

import debug

pygame.init()

final_display = pygame.display.set_mode(constants.SCREEN_SIZE)
clock = pygame.time.Clock()


def screen_update(fps):
    pygame.display.flip()
    final_display.fill(constants.WHITE)
    clock.tick(fps)


FOV = player.FOV


def draw_view(surface, y):
    for x in range(0, constants.SCREEN_WIDTH, 2):
        angle = player.angle - (FOV / 2) + (FOV / constants.SCREEN_WIDTH * x)
        segment = geometry.closest_wall_level(player.position, play_screen.level, angle)
        if segment:
            surface.fill(segment.color, (x, y, 2, 20))


class PlayScreen:
    def __init__(self):
        self.level = None

    def update(self):
        player.update_movement(self.level)

    def draw(self, surface):
        draw_view(surface, 400)
        self.level.draw_debug(surface)
        player.draw_debug(surface, play_screen.level)


player = player.Player()
player.go_to((200, 200))
play_screen = PlayScreen()

# Testing level
level_test_shape1_points = ((100, 100), (400, 200), (350, 400), (100, 200))
level_test_polygon1 = geometry.Polygon(level_test_shape1_points, False)
level_test_polygon1.set_colors((constants.GREEN, constants.ORANGE,
                                constants.RED))

level_test_shape2_points = ((240, 240), (240, 260), (260, 260), (240, 240))
level_test_polygon2 = geometry.Polygon(level_test_shape2_points)
level_test_polygon2.set_colors((constants.CYAN, ) * 3)

level_test_shape3_points = ((10, 450), (250, 460), (490, 450))
level_test_polygon3 = geometry.Polygon(level_test_shape3_points, False)
level_test_polygon3.set_colors((constants.MAGENTA, constants.YELLOW))

level_test = levels.Level((level_test_polygon1, level_test_polygon2,
                           level_test_polygon3))

play_screen.level = level_test

pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

while True:
    events.update()
    if events.keys.pressed_key == pygame.K_ESCAPE:
        break

    play_screen.update()
    play_screen.draw(final_display)
    debug.debug(clock.get_fps())
    debug.draw(final_display)

    screen_update(60)

pygame.quit()
sys.exit()
