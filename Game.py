import sound

import pygame
import sys
import os
import math

import geometry
import utility
import constants
import events
import player
import levels
import ripples

import debug

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
pygame.display.set_caption("GMTK 2019")

final_display = pygame.display.set_mode(constants.SCREEN_SIZE)
final_display.convert_alpha()

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

win_sound = sound.load("win")
lose_sound = sound.load("lose")

level_offset = (0, 50)


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


class Signal:
    RADIUS = 5

    def __init__(self, position, level):
        self.position = position
        self.x = position[0]
        self.y = position[1]

        for polygon in level.goals:
            if geometry.point_in_polygon(position, polygon):
                if polygon.color in utility.saturated_counterpart:
                    self.color = utility.saturated_counterpart[polygon.color]
                else:
                    self.color = WHITE
                self.satisfied = True
                break

        else:
            self.color = WHITE
            self.satisfied = False


class PlayScreen:
    PAUSE_LENGTH = 30
    VERDICT_LENGTH = 75
    ZOOM_MAX = 1.2
    ZOOM_A = abs(ZOOM_MAX - 1.0)
    ZOOM_K = math.pi / (2 * VERDICT_LENGTH)

    SIGNAL_SPACING = 30
    SIGNAL_GAP = SIGNAL_SPACING - Signal.RADIUS * 2

    PAUSE_FADE_SPEED = 5
    OVERLAY_OPACITY = 0.75

    RESUME = 0
    VOLUME_SLIDER = 1
    SENSITIVITY_SLIDER = 2
    EXIT = 3

    HITBOXES = (pygame.Rect(200, 100, 100, 40),
                pygame.Rect(230, 150, 150, 40),
                pygame.Rect(230, 200, 150, 40),
                pygame.Rect(200, 250, 100, 40))

    def __init__(self):
        self.mouse_lock = 0  # fixes sudden movement after exiting from pause

        self.level = None

        self.signals = []
        self.placed_signals = 0
        self.signals_width = 0

        self.paused = False
        self.pause_alpha = 0
        self.pause_overlay = pygame.Surface(constants.SCREEN_SIZE)
        self.pause_overlay.fill(WHITE)
        self.pause_overlay.set_alpha(self.pause_alpha)

        self.mouse_option = 0

        self.volume_x = 150
        self.sensitivity_x = 30

        self.won = True
        self.verdicting = False
        self.verdict_frame = 0
        self.drama_pausing = False
        self.drama_pause_frame = 0
        self.resulting = False
        self.result_frame = 0
        self.zoom = 1.0
        self.zoom_temp = pygame.Surface(constants.SCREEN_SIZE)
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

            if events.mouse.released:
                self.place_signal(player_entity.position)

            if self.verdicting:
                if self.verdict_frame < self.VERDICT_LENGTH:
                    self.verdict_frame += 1
                    self.zoom = math.sin(self.ZOOM_K * self.verdict_frame)
                    self.zoom = self.ZOOM_A * self.zoom + 1.0
                else:
                    self.verdicting = False
                    self.verdict_frame = 0
                    self.drama_pausing = True

            elif self.drama_pausing:
                if self.drama_pause_frame < self.PAUSE_LENGTH:
                    self.drama_pause_frame += 1

                else:
                    sound.music_volume.fade_to(1.0)

                    self.drama_pausing = False
                    self.drama_pause_frame = 0
                    self.resulting = True

                    y = 90
                    for index, signal in enumerate(self.signals):
                        x = constants.SCREEN_MIDDLE_INT[0] - self.signals_width // 2
                        x += index * self.SIGNAL_SPACING + Signal.RADIUS

                        if self.won:
                            color = signal.color
                            anchor = utility.add_tuples(level_offset, constants.SCREEN_MIDDLE)
                            position = utility.add_tuples(signal.position, level_offset)
                            position = geometry.scale_position(position, anchor, self.zoom)
                            position = utility.int_tuple(position)

                            ripples.create_ripple(position, color, 30, 30)
                        else:
                            color = BLACK

                        ripples.create_ripple((x, y), color, 30, 30)

                    if not self.won:
                        self.clear_signals()

            elif self.resulting:
                if self.result_frame < self.VERDICT_LENGTH:
                    self.result_frame += 1
                    self.zoom = math.sin(self.ZOOM_K * self.result_frame)
                    self.zoom = -self.ZOOM_A * self.zoom + self.ZOOM_MAX
                else:
                    self.resulting = False
                    self.result_frame = 0

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
                is_volume = self.mouse_option == self.VOLUME_SLIDER
                is_sensitivity = self.mouse_option == self.SENSITIVITY_SLIDER

                if (is_volume or is_sensitivity) and events.mouse.held:
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

                elif self.mouse_option == self.VOLUME_SLIDER:
                    rect = self.HITBOXES[self.SENSITIVITY_SLIDER]
                    x = events.mouse.position[0] - rect.left
                    if x < 0:
                        x = 0
                    elif x > rect.width:
                        x = rect.width

                    self.volume_x = x
                    value = x / rect.width
                    sound.volume_control.fade_to(value)

    def draw(self, surface):
        if self.verdicting or self.resulting:
            level_surface = self.zoom_temp
            self.zoom_temp.fill(constants.WHITE)

        else:
            level_surface = surface

        self.level.draw_debug(level_surface, level_offset)

        if self.won and not self.verdicting and not self.drama_pausing:
            for signal in self.signals:
                color = signal.color
                position = utility.int_tuple(signal.position)
                position = utility.add_tuples(position, level_offset)
                pygame.draw.circle(level_surface, color, position, Signal.RADIUS)

        player_entity.draw_debug(level_surface, play_screen.level, level_offset)

        if self.verdicting or self.drama_pausing or self.resulting:
            width = int(self.zoom * constants.SCREEN_WIDTH)
            height = int(self.zoom * constants.SCREEN_HEIGHT)
            zoom_surface = pygame.transform.scale(self.zoom_temp, (width, height))
            x = -(width - constants.SCREEN_WIDTH) // 2
            y = -(height - constants.SCREEN_HEIGHT) // 2
            surface.blit(zoom_surface, (x, y))

        draw_view(surface, 50)

        y = 90
        for index in range(self.level.goal_count):
            x = constants.SCREEN_MIDDLE_INT[0] - self.signals_width // 2
            x += index * self.SIGNAL_SPACING + Signal.RADIUS

            if index < self.placed_signals:
                width = 0
            else:
                width = 1

            if self.won and not self.verdicting and not self.drama_pausing:
                color = self.signals[index].color
            else:
                color = BLACK

            pygame.draw.circle(surface, color, (x, y), Signal.RADIUS, width)

        if self.pause_alpha != 0:
            surface.blit(self.pause_overlay, (0, 0))

            if self.mouse_option != -1:
                rect = self.HITBOXES[self.mouse_option]
                rectangle_surface = pygame.Surface((rect.w, rect.h)).convert_alpha()
                rectangle_surface.fill((255, 255, 255))
                new_surf = utility.black_image_alpha(rectangle_surface, self.pause_alpha * 0.1)
                surface.blit(new_surf, rect.topleft)

            text = utility.black_text_alpha(subtitle_font, "Paused", self.pause_alpha)
            utility.blit_vert_center(surface, text, 46)

            text = utility.black_text_alpha(small_font, "Resume", self.pause_alpha)
            utility.blit_vert_center(surface, text, self.HITBOXES[self.RESUME].top + 10)

            rect = self.HITBOXES[self.SENSITIVITY_SLIDER]
            rect = pygame.Rect(rect.left + self.sensitivity_x, rect.top, 1, rect.h)
            rectangle_surface = pygame.Surface((rect.w, rect.h)).convert_alpha()
            rectangle_surface.fill((255, 255, 255))
            new_surf = utility.black_image_alpha(rectangle_surface, self.pause_alpha * 0.5)
            surface.blit(new_surf, rect.topleft)

            text = utility.black_text_alpha(small_font, "Sensitivity", self.pause_alpha)
            x = constants.SCREEN_MIDDLE[0] - 120
            y = self.HITBOXES[self.SENSITIVITY_SLIDER].top + 9
            surface.blit(text, (x, y))

            rect = self.HITBOXES[self.VOLUME_SLIDER]
            rect = pygame.Rect(rect.left + self.volume_x, rect.top, 1, rect.h)
            rectangle_surface = pygame.Surface((rect.w, rect.h)).convert_alpha()
            rectangle_surface.fill((255, 255, 255))
            new_surf = utility.black_image_alpha(rectangle_surface, self.pause_alpha * 0.5)
            surface.blit(new_surf, rect.topleft)

            text = utility.black_text_alpha(small_font, "Volume", self.pause_alpha)
            x = constants.SCREEN_MIDDLE[0] - 100
            y = self.HITBOXES[self.VOLUME_SLIDER].top + 9
            surface.blit(text, (x, y))

            text = utility.black_text_alpha(small_font, "Exit", self.pause_alpha)
            utility.blit_vert_center(surface, text, self.HITBOXES[self.EXIT].top + 10)

            text = utility.black_text_alpha(subtitle_font, "Help", self.pause_alpha)
            utility.blit_vert_center(surface, text, 320)

    def pause(self):
        self.paused = True
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)

    def unpause(self):
        self.paused = False
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        self.mouse_lock = 2

    def clear_signals(self):
        self.signals = []
        self.placed_signals = 0

    def load_level(self, level):
        self.level = level

        self.won = False

        self.clear_signals()
        self.signals_width = self.SIGNAL_SPACING * level.goal_count - self.SIGNAL_GAP

    def place_signal(self, position):
        if self.placed_signals < self.level.goal_count:
            self.signals.append(Signal(position, self.level))
            self.placed_signals += 1

        if self.placed_signals == self.level.goal_count:
            self.verdicting = True
            sound.music_volume.fade_to(0.35)
            if self.check_win():
                sound.play(win_sound)
                self.won = True
            else:
                sound.play(lose_sound)

    def check_win(self):
        for polygon in self.level.goals:
            for signal in self.signals:
                if geometry.point_in_polygon(signal.position, polygon):
                    break
            else:
                break
        else:
            return True

        return False


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

play_screen.load_level(L0)

player_entity = player.Player()
player_entity.go_to((250, 250))

sound.load_music("music")
sound.play_music()

pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

while True:
    events.update()
    sound.update()

    if not play_screen.paused:
        ripples.update()

    play_screen.update()
    if play_screen.quit_game:
        break
    play_screen.draw(final_display)

    ripples.draw(final_display)

    debug.debug(clock.get_fps())
    debug.debug(play_screen.mouse_option)
    debug.draw(final_display)

    screen_update(60)

pygame.quit()
sys.exit()
