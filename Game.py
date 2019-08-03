import pygame
import sys
import os
# import math

import geometry
import utility
import constants
import events
import player
import levels

import debug

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
pygame.display.set_caption("GMTK 2019")

final_display = pygame.display.set_mode(constants.SCREEN_SIZE)

clock = pygame.time.Clock()


subtitle_font = pygame.font.Font("Raleway-Thin.ttf", 24)
small_font = pygame.font.Font("Raleway-Thin.ttf", 16)


BLACK = constants.BLACK
WHITE = constants.WHITE
RED = constants.RED
GREEN = constants.GREEN
BLUE = constants.BLUE
CYAN = constants.CYAN
MAGENTA = constants.MAGENTA
YELLOW = constants.YELLOW
ORANGE = constants.ORANGE

LIGHT_GREY = constants.LIGHT_GREY
PALE_RED = constants.PALE_RED
PALE_GREEN = constants.PALE_GREEN
PALE_BLUE = constants.PALE_BLUE
PALE_CYAN = constants.PALE_CYAN
PALE_MAGENTA = constants.PALE_MAGENTA
PALE_YELLOW = constants.PALE_YELLOW
PALE_ORANGE = constants.PALE_ORANGE


def screen_update(fps):
    pygame.display.flip()
    final_display.fill(constants.WHITE)
    clock.tick(fps)


FOV = player.FOV


def draw_view(surface, y):
    for x in range(0, constants.SCREEN_WIDTH, 2):
        angle = player_entity.angle - (FOV / 2) + (FOV / constants.SCREEN_WIDTH * x)
        segment = geometry.closest_wall_level(player_entity.position, play_screen.level, angle)
        if segment:
            surface.fill(segment.color, (x, y, 2, 20))


class PlayScreen:
    PAUSE_FADE_SPEED = 5
    OVERLAY_OPACITY = 0.75

    RESUME = 0
    SENSITIVITY_SLIDER = 1
    EXIT = 2
    HITBOXES = (pygame.Rect(200, 100, 100, 40),
                pygame.Rect(230, 150, 150, 40),
                pygame.Rect(200, 400, 100, 40))

    def __init__(self):
        self.mouse_lock = 0  # fixes sudden movement after exiting from pause

        self.level = None

        self.paused = False
        self.pause_alpha = 0
        self.pause_overlay = pygame.Surface(constants.SCREEN_SIZE)
        self.pause_overlay.fill(WHITE)
        self.pause_overlay.set_alpha(self.pause_alpha)

        self.mouse_option = 0

        self.sensitivity_x = 30

        self.quit_game = False

    def update(self):
        if self.mouse_lock:
            self.mouse_lock -= 1
            events.mouse.relative = (0, 0)

        if events.keys.pressed_key == pygame.K_ESCAPE:
            if self.paused:
                self.unpause()
            else:
                self.pause()

        if not self.paused:
            player_entity.update_movement(self.level)

            if self.pause_alpha > 0:
                self.pause_alpha -= self.PAUSE_FADE_SPEED

                if self.pause_alpha < 0:
                    self.pause_alpha = 0

                self.pause_overlay.set_alpha(self.pause_alpha * self.OVERLAY_OPACITY)

        else:
            if self.pause_alpha < 255:
                self.pause_alpha += self.PAUSE_FADE_SPEED

                if self.pause_alpha > 255:
                    self.pause_alpha = 255

                self.pause_overlay.set_alpha(self.pause_alpha * self.OVERLAY_OPACITY)

            for index, hitbox in enumerate(self.HITBOXES):
                if hitbox.collidepoint(events.mouse.position):
                    self.mouse_option = index
                    break

            else:
                if self.mouse_option == self.SENSITIVITY_SLIDER and events.mouse.held:
                    pass
                else:
                    self.mouse_option = -1

            if events.mouse.released:
                if self.mouse_option == self.RESUME:
                    self.unpause()

                elif self.mouse_option == self.EXIT:
                    self.quit_game = True

            if events.mouse.held:
                if self.mouse_option == self.SENSITIVITY_SLIDER:
                    rect = self.HITBOXES[self.SENSITIVITY_SLIDER]
                    x = events.mouse.position[0] - rect.left
                    if x < 0:
                        x = 0
                    elif x > rect.width:
                        x = rect.width

                    self.sensitivity_x = x
                    value = x / rect.width / 200 + 0.001
                    player.sensitivity = value

    def draw(self, surface):
        draw_view(surface, 50)
        self.level.draw_debug(surface, (0, 50))
        player_entity.draw_debug(surface, play_screen.level, (0, 50))

        if self.pause_alpha != 0:
            surface.blit(self.pause_overlay, (0, 0))

            if self.mouse_option != -1:
                rect = self.HITBOXES[self.mouse_option]
                rectangle_surface = pygame.Surface((rect.w, rect.h)).convert_alpha()
                rectangle_surface.fill((255, 255, 255))
                new_surf = utility.black_image_alpha(rectangle_surface, self.pause_alpha * 0.1)
                surface.blit(new_surf, rect.topleft)

            rect = self.HITBOXES[self.SENSITIVITY_SLIDER]
            rect = pygame.Rect(rect.left + self.sensitivity_x, rect.top, 1, rect.h)
            rectangle_surface = pygame.Surface((rect.w, rect.h)).convert_alpha()
            rectangle_surface.fill((255, 255, 255))
            new_surf = utility.black_image_alpha(rectangle_surface, self.pause_alpha * 0.5)
            surface.blit(new_surf, rect.topleft)

            text = utility.black_text_alpha(subtitle_font, "Paused", self.pause_alpha)
            utility.blit_vert_center(surface, text, 46)

            text = utility.black_text_alpha(small_font, "Resume", self.pause_alpha)
            utility.blit_vert_center(surface, text, self.HITBOXES[self.RESUME].top + 10)

            text = utility.black_text_alpha(small_font, "Sensitivity", self.pause_alpha)
            x = constants.SCREEN_MIDDLE[0] - 120
            y = self.HITBOXES[self.SENSITIVITY_SLIDER].top + 10
            surface.blit(text, (x, y))

            text = utility.black_text_alpha(small_font, "Exit", self.pause_alpha)
            utility.blit_vert_center(surface, text, self.HITBOXES[self.EXIT].top + 10)

    def pause(self):
        self.paused = True
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)

    def unpause(self):
        self.paused = False
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        self.mouse_lock = 2


play_screen = PlayScreen()

# Level 0: Plus
L0C0 = geometry.Polygon(((200, 300), (100, 300), (100, 200), (200, 200),  # left arm
                         (200, 100), (300, 100), (300, 200),  # top arm
                         (400, 200), (400, 300), (300, 300),  # right arm
                         (300, 400), (200, 400)))  # bottom arm
L0C0.set_colors((GREEN, BLUE, GREEN, GREEN, ORANGE, GREEN,
                 GREEN, MAGENTA, GREEN, GREEN, RED, GREEN))

L0_collisions = (L0C0,)

L0G0 = geometry.Polygon(((200, 300), (100, 300), (100, 200), (200, 200)))  # left goal
L0G1 = geometry.Polygon(((200, 200), (200, 100), (300, 100), (300, 200)))  # top goal
L0G2 = geometry.Polygon(((300, 200), (400, 200), (400, 300), (300, 300)))  # right goal
L0G3 = geometry.Polygon(((300, 300), (300, 400), (200, 400), (200, 300)))  # bottom goal

L0_goals = (L0G0, L0G1, L0G2, L0G3)

L0 = levels.Level(L0_collisions, L0_goals)
L0.set_goal_colors((PALE_BLUE, PALE_ORANGE, PALE_MAGENTA, PALE_RED))

# level_test_shape1_points = ((100, 100), (400, 200), (350, 400), (100, 200))
# level_test_polygon1 = geometry.Polygon(level_test_shape1_points, False)
# level_test_polygon1.set_colors((constants.GREEN, constants.ORANGE,
#                                 constants.RED))
#
# level_test_shape2_points = ((240, 240), (240, 260), (260, 260), (240, 240))
# level_test_polygon2 = geometry.Polygon(level_test_shape2_points)
# level_test_polygon2.set_colors((constants.CYAN, ) * 3)
#
# level_test_shape3_points = ((10, 450), (250, 460), (490, 450))
# level_test_polygon3 = geometry.Polygon(level_test_shape3_points, False)
# level_test_polygon3.set_colors((constants.MAGENTA, constants.YELLOW))
#
# level_test = levels.Level((level_test_polygon1, level_test_polygon2,
#                            level_test_polygon3))

play_screen.level = L0

player_entity = player.Player()
player_entity.go_to((250, 250))

pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

while True:
    events.update()

    play_screen.update()
    if play_screen.quit_game:
        break
    play_screen.draw(final_display)
    debug.debug(clock.get_fps())
    debug.debug(play_screen.mouse_option)
    debug.draw(final_display)

    screen_update(60)

pygame.quit()
sys.exit()
