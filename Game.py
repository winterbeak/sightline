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
small_font_dark = pygame.font.Font("Raleway-ExtraLight.ttf", 16)


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


class TutorialText:
    def __init__(self, string, y):
        width = small_font_dark.render(string, False, BLACK).get_width()
        self.position = (constants.SCREEN_MIDDLE_INT[0] - width // 2, y)
        self.string = string

    def draw(self, surface, alpha=255):
        if alpha == 255:
            text = small_font_dark.render(self.string, True, BLACK)
        else:
            text = utility.black_text_alpha(small_font_dark, self.string, alpha)

        surface.blit(text, self.position)


class Signal:
    """Signal is what the placeable circles were originally called.
    However, that name implied they actually *did* something, and
    people might expect some sort of audio cue from them or something.
    """
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
                    self.color = BLACK
                self.satisfied = True
                break

        else:
            self.color = BLACK
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
    SHOW_CIRCLES = 4
    SHOW_PLAYER = 5
    PREVIOUS_LEVEL = 6
    NEXT_LEVEL = 7

    HITBOXES = (pygame.Rect(200, 100, 100, 40),  # Resume
                pygame.Rect(230, 150, 150, 40),  # Volume slider
                pygame.Rect(230, 200, 150, 40),  # Sensitivity slider
                pygame.Rect(200, 250, 100, 40),  # Exit
                pygame.Rect(260, 360, 50, 30),  # Show circles
                pygame.Rect(260, 395, 50, 30),  # Show player
                pygame.Rect(150, 450, 30, 30),  # Previous level
                pygame.Rect(320, 450, 30, 30))  # Next level

    TUTORIAL_TEXT = ((TutorialText("This is your sightline.", 20),
                      TutorialText("This is the map.", 455)),

                     (TutorialText("Use the mouse to look around.", 110),
                      TutorialText("Pay attention to how your sightline changes!", 455)),

                     (TutorialText("Use WASD to move.", 110),
                      TutorialText("Don't rely on the map!", 270),
                      TutorialText("Instead, look at your sightline and", 290),
                      TutorialText("treat movement like an FPS.", 310)),

                     (TutorialText("These colored regions are the goals.", 110),
                      TutorialText("To win, you must place exactly one circle in each goal.", 455),
                      TutorialText("Click to place a circle.", 475)),

                     (TutorialText("Great!  But that was a little easy, wasn't it?", 110),
                      TutorialText("Let's hide your character, and the circles, too.", 455),
                      TutorialText("Click once you're ready.", 475)),

                     (TutorialText("Beat the level again, but this time", 100),
                      TutorialText("using only your sightline to get around!", 120),
                      TutorialText("If you need help, check out the pause menu by pressing Escape.", 455)),

                     (TutorialText("Well done!", 110),
                      TutorialText("Once you're ready, click to move on to the next level.", 465)))

    CONTINUE_TEXT = TutorialText("Click to continue.", 475)
    COMFORTABLE_TEXT = TutorialText("Once you're comfortable, click to continue.", 475)

    def __init__(self):
        self.mouse_lock = 0  # fixes sudden movement after exiting from pause

        self.level = None

        self.previous_signals = []
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

        self.tutorial_stage = 0
        self.changing_tutorial_stage = False
        self.text_alpha = 0.0
        self.text_alpha_change = 255 / 60
        self.continue_text_alpha = 0.0
        self.tutorial_frame = 0

        self.show_player = False
        self.show_circles = False

        self.fade_temp = pygame.Surface(constants.SCREEN_SIZE)
        self.fade_temp.fill(WHITE)
        self.fade_speed = 255 / 120
        self.alpha = 255
        self.next_level_transitioning = False

        self.level_num = 0

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
                if self.level_num == 0 and not self.changing_tutorial_stage:
                    if self.tutorial_stage < 3:
                        self.changing_tutorial_stage = True
                    elif self.tutorial_stage == 4:
                        self.changing_tutorial_stage = True

                        position = utility.add_tuples(player_entity.position, level_offset)
                        ripples.create_ripple(position, BLACK, 30, 30)

                        for signal in self.signals:
                            position = utility.add_tuples(signal.position, level_offset)
                            ripples.create_ripple(position, signal.color, 30, 30)

                        for index in range(self.level.goal_count):
                            x = constants.SCREEN_MIDDLE_INT[0] - self.signals_width // 2
                            x += index * self.SIGNAL_SPACING + Signal.RADIUS

                            ripples.create_ripple((x, 90), self.signals[index].color, 30, 30)

                        self.show_player = False

                        self.clear_signals()
                        self.won = False
                    elif self.tutorial_stage == 6:
                        self.next_level_transitioning = True

                    elif self.placed_signals < self.level.goal_count:
                        self.place_signal(player_entity.position)

                elif self.level_num != 0:
                    if self.placed_signals < self.level.goal_count:
                        self.place_signal(player_entity.position)

            if self.changing_tutorial_stage and self.text_alpha > 0:
                self.text_alpha -= self.text_alpha_change
                self.continue_text_alpha -= self.text_alpha_change

                if self.continue_text_alpha < 0:
                    self.continue_text_alpha = 0
                if self.text_alpha <= 0:
                    self.text_alpha = 0
                    self.changing_tutorial_stage = False
                    self.tutorial_stage += 1
                    self.tutorial_frame = 0

            elif not self.changing_tutorial_stage and self.text_alpha < 255:
                self.text_alpha += self.text_alpha_change
                if self.text_alpha > 255:
                    self.text_alpha = 255

            if self.level_num == 0:
                if not self.changing_tutorial_stage:
                    if self.tutorial_frame < 300:
                        self.tutorial_frame += 1

                    elif self.continue_text_alpha < 255:
                        self.continue_text_alpha += self.text_alpha_change
                        if self.continue_text_alpha > 255:
                            self.continue_text_alpha = 255

            # Win animation
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

                        if self.won or self.show_circles:
                            color = signal.color
                            anchor = utility.add_tuples(level_offset, constants.SCREEN_MIDDLE)
                            position = utility.add_tuples(signal.position, level_offset)
                            position = geometry.scale_position(position, anchor, self.zoom)
                            position = utility.int_tuple(position)

                            ripples.create_ripple(position, color, 30, 30)

                        else:
                            color = BLACK

                        ripples.create_ripple((x, y), color, 30, 30)

                    if self.won:
                        if self.level_num == 0 and (self.tutorial_stage == 3 or self.tutorial_stage == 5):
                            self.changing_tutorial_stage = True
                        else:
                            self.next_level_transitioning = True
                    else:
                        self.previous_signals = self.signals
                        self.clear_signals()

            elif self.resulting:
                if self.result_frame < self.VERDICT_LENGTH:
                    self.result_frame += 1
                    self.zoom = math.sin(self.ZOOM_K * self.result_frame)
                    self.zoom = -self.ZOOM_A * self.zoom + self.ZOOM_MAX
                else:
                    self.resulting = False
                    self.result_frame = 0

            # Next level transitioning
            if self.next_level_transitioning and self.alpha > 0:
                self.alpha -= self.fade_speed

                if self.alpha <= 0:
                    self.alpha = 0
                    self.load_level(self.level_num + 1)

            elif not self.next_level_transitioning and self.alpha < 255:
                self.alpha += self.fade_speed

                if self.alpha > 255:
                    self.alpha = 255

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

                elif self.mouse_option == self.SHOW_PLAYER:
                    self.show_player = not self.show_player

                elif self.mouse_option == self.SHOW_CIRCLES:
                    self.show_circles = not self.show_circles

                elif self.mouse_option == self.PREVIOUS_LEVEL:
                    if self.level_num > 0:
                        self.load_level(self.level_num - 1)

                elif self.mouse_option == self.NEXT_LEVEL:
                    if self.level_num < last_level:
                        self.load_level(self.level_num + 1)

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
        if self.verdicting or self.drama_pausing or self.resulting:
            level_surface = self.zoom_temp
            self.zoom_temp.fill(constants.WHITE)

        else:
            level_surface = surface

        if self.tutorial_stage == 3 and not self.changing_tutorial_stage:
            self.level.draw_debug_goals(level_surface, level_offset, self.text_alpha)
        elif self.tutorial_stage == 3 and self.changing_tutorial_stage:
            self.level.draw_debug_goals(level_surface, level_offset)
        elif self.tutorial_stage > 3:
            self.level.draw_debug_goals(level_surface, level_offset)

        self.level.draw_debug_outline(level_surface, level_offset)

        if self.show_circles and self.previous_signals:
            for signal in self.previous_signals:
                color = signal.color
                position = utility.int_tuple(signal.position)
                position = utility.add_tuples(position, level_offset)
                pygame.draw.circle(level_surface, color, position, Signal.RADIUS)

        tutorial_show = self.tutorial_stage == 3 or self.tutorial_stage == 4
        win_show = self.won and not self.verdicting and not self.drama_pausing
        if tutorial_show or win_show:
            for signal in self.signals:
                color = signal.color
                position = utility.int_tuple(signal.position)
                position = utility.add_tuples(position, level_offset)
                pygame.draw.circle(level_surface, color, position, Signal.RADIUS)

        if self.show_player:
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

        if self.level_num == 0:
            for text in self.TUTORIAL_TEXT[self.tutorial_stage]:
                text.draw(surface, int(self.text_alpha))
            if self.tutorial_stage == 0:
                self.CONTINUE_TEXT.draw(surface, int(self.continue_text_alpha))
            elif self.tutorial_stage == 1 or self.tutorial_stage == 2:
                self.COMFORTABLE_TEXT.draw(surface, int(self.continue_text_alpha))

        if self.alpha < 255:
            self.fade_temp.set_alpha(255 - int(self.alpha))
            surface.blit(self.fade_temp, (0, 0))

        # Pause screen
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

            text = utility.black_text_alpha(subtitle_font, "Stuck?", self.pause_alpha)
            utility.blit_vert_center(surface, text, 320)

            text = utility.black_text_alpha(small_font, "Show circles on fail", self.pause_alpha)
            x = constants.SCREEN_MIDDLE[0] - 150
            y = self.HITBOXES[self.SHOW_CIRCLES].top + 5
            surface.blit(text, (x, y))

            if self.show_circles:
                text = utility.black_text_alpha(small_font, "On", self.pause_alpha)
                x = constants.SCREEN_MIDDLE[0] + 24
                surface.blit(text, (x, y))
            else:
                text = utility.black_text_alpha(small_font, "Off", self.pause_alpha)
                x = constants.SCREEN_MIDDLE[0] + 24
                surface.blit(text, (x, y))

            text = utility.black_text_alpha(small_font, "Show player", self.pause_alpha)
            x = constants.SCREEN_MIDDLE[0] - 100
            y = self.HITBOXES[self.SHOW_PLAYER].top + 5
            surface.blit(text, (x, y))

            if self.show_player:
                text = utility.black_text_alpha(small_font, "On", self.pause_alpha)
                x = constants.SCREEN_MIDDLE[0] + 24
                surface.blit(text, (x, y))
            else:
                text = utility.black_text_alpha(small_font, "Off", self.pause_alpha)
                x = constants.SCREEN_MIDDLE[0] + 24
                surface.blit(text, (x, y))

            text = utility.black_text_alpha(small_font, "Change level", self.pause_alpha)
            utility.blit_vert_center(surface, text, 455)

            text = utility.black_text_alpha(subtitle_font, "<", self.pause_alpha)
            x = constants.SCREEN_MIDDLE[0] - 92
            y = self.HITBOXES[self.PREVIOUS_LEVEL].top - 1
            surface.blit(text, (x, y))

            text = utility.black_text_alpha(subtitle_font, ">", self.pause_alpha)
            x = constants.SCREEN_MIDDLE[0] + 79
            y = self.HITBOXES[self.PREVIOUS_LEVEL].top - 1
            surface.blit(text, (x, y))

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

    def load_level(self, level_num):
        self.next_level_transitioning = False

        if level_num == 0:
            self.tutorial_stage = 0
            self.text_alpha = 0.0
            self.continue_text_alpha = 0.0
            self.changing_tutorial_stage = False
            self.tutorial_frame = 0
            self.show_player = True
        else:
            self.tutorial_stage = 6
            self.show_player = False
            self.show_circles = False

        self.level_num = level_num
        self.level = levels[level_num]

        self.won = False

        self.clear_signals()
        self.signals_width = self.SIGNAL_SPACING * self.level.goal_count - self.SIGNAL_GAP

        player_entity.go_to(self.level.start_position)
        # slightly offset, "gaps" seem to appear at exact 90 degree angles
        player_entity.angle = self.level.start_orientation + 0.0001

    def place_signal(self, position):
        if self.placed_signals < self.level.goal_count:
            self.signals.append(Signal(position, self.level))
            self.placed_signals += 1

        if self.placed_signals == self.level.goal_count:
            if self.show_circles and self.previous_signals:
                for signal in self.previous_signals:
                    position = utility.add_tuples(signal.position, level_offset)
                    ripples.create_ripple(position, signal.color, 30, 30)
            self.previous_signals = []

            self.verdict_frame = 0
            self.drama_pause_frame = 0
            self.result_frame = 0
            self.verdicting = True
            self.drama_pausing = False
            self.resulting = False
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
player_entity = player.Player()


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

L0 = levels.Level(L0_collisions, L0_goals, (250, 250), -math.pi / 2)
L0.set_goal_colors((PALE_BLUE, PALE_ORANGE, PALE_MAGENTA, PALE_RED))


# Level 1: Two spikes
L1C0 = geometry.Polygon(((100, 200), (250, 300), (400, 200),  # indentation
                         (400, 400), (100, 400)))  # bottom
L1C0.set_colors((CYAN, MAGENTA, ORANGE, ORANGE, ORANGE))

L1_collisions = (L1C0, )

L1G0 = geometry.Polygon(((100, 200), (250, 300), (100, 300)))  # left
L1G1 = geometry.Polygon(((400, 200), (250, 300), (400, 300)))  # right
L1G2 = geometry.Polygon(((100, 300), (400, 300), (400, 400), (100, 400)))  # bottom

L1_goals = (L1G0, L1G1, L1G2)

L1 = levels.Level(L1_collisions, L1_goals, (250, 350), math.pi / 2)
L1.set_goal_colors((PALE_CYAN, PALE_MAGENTA, PALE_ORANGE))

# Level template
# L#C0 = geometry.Polygon(((x, y), (x, y), (x, y))))
# L#C0.set_colors((color1, color2, color3))
# L#C1 = geometry.Polygon(((x, y), (x, y), (x, y),
#                          (x, y), (x, y))
# L#C1.set_colors((color1, color2, color3, color4, color5))
# L#C2 = geometry.Polygon(((x, y), (x, y)))
# L#C2.set_colors((color1))
#
# L#_collisions = (L#C0, L#C1, L#C2)
#
# L#G0 = geometry.Polygon(((x, y), (x, y), (x, y)))
# L#G1 = geometry.Polygon(((x, y), (x, y), (x, y),
#                          (x, y), (x, y)))
# L#G2 = geometry.Polygon(((x, y), (x, y), (x, y), (x, y))
#
# L#_goals = (L#G0, L#G1, L#G2)
#
# L# = levels.Level(L#_collisions, L#_goals, (start_x, start_y)
# L#.set_goal_colors((color1, color2, color3))

levels = (L0, L1)
last_level = len(levels) - 1

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

play_screen.load_level(0)
play_screen.show_player = True

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
