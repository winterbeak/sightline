import sound

import pygame
# import sys
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
pygame.display.set_caption("Sightline")
pygame.display.set_icon(pygame.image.load("icon.png"))

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
win_sound.set_volume(0.8)
lose_sound = sound.load("lose")
lose_sound.set_volume(0.8)
pause_sound = sound.load("pause")
pause_sound.set_volume(0.75)
circle_sounds = tuple(sound.load("circle%i" % i) for i in range(1, 9))

level_offset = (0, 50)


def screen_update(fps):
    pygame.display.flip()
    final_display.fill(constants.WHITE)
    clock.tick(fps)


FOV = player.FOV


def new_ray(position, level, angle):
    segment = geometry.closest_wall_level(position, level, angle)
    if segment:
        color = segment.color
    else:
        color = constants.WHITE

    return angle, color


def draw_view(surface, y):
    # # Optimizes LEVEL_GRID by abusing the fact that it only has one color
    # if play_screen.level is LEVEL_GRID:
    #     for x in range(0, constants.SCREEN_WIDTH, 2):
    #         angle = player_entity.angle - (FOV / 2) + (FOV / constants.SCREEN_WIDTH * x)
    #         if geometry.level_wall_in_direction(player_entity.position, play_screen.level, angle):
    #             surface.fill(constants.RED, (x, y, 2, 20))
    #
    #     return
    #
    # for x in range(0, constants.SCREEN_WIDTH, 2):
    #     angle = player_entity.angle - (FOV / 2) + (FOV / constants.SCREEN_WIDTH * x)
    #     segment = geometry.closest_wall_level(player_entity.position, play_screen.level, angle)
    #     if segment:
    #         surface.fill(segment.color, (x, y, 2, 20))
    rays = []

    position = player_entity.position
    level = play_screen.level

    for polygon in play_screen.level.collision:
        for segment in polygon.segments:
            angle = geometry.angle_between(position, segment.point1)
            rays.append(new_ray(position, level, angle - 0.00001))
            rays.append(new_ray(position, level, angle))
            rays.append(new_ray(position, level, angle + 0.00001))

            angle = geometry.angle_between(position, segment.point2)
            rays.append(new_ray(position, level, angle - 0.00001))
            rays.append(new_ray(position, level, angle))
            rays.append(new_ray(position, level, angle + 0.00001))

    rays.sort()  # sorts rays by their angle

    lowest_angle = player_entity.angle - (FOV / 2.0)
    highest_angle = player_entity.angle + (FOV / 2.0)

    first_index = 0
    lowest_difference = 10.0
    for index, ray in enumerate(rays):
        angle = ray[0]
        while angle < lowest_angle:
            angle += math.pi * 2
        difference = angle - lowest_angle
        if difference < lowest_difference:
            lowest_difference = difference
            first_index = index

        while angle < lowest_angle + math.pi * 2:
            angle += math.pi * 2
        difference = angle - (lowest_angle + math.pi * 2)
        if difference < lowest_difference:
            lowest_difference = difference
            first_index = index

    previous_x = 0
    previous_index = first_index - 1

    current_index = first_index

    # range(1000) rather than while True to prevent freezing.  If a level
    # somehow has more than 166 segments, increase this number
    for _ in range(1000):
        if rays[current_index][1] != rays[previous_index][1]:
            current_angle = rays[current_index - 1][0]
            if current_angle > lowest_angle + math.pi * 2:
                current_x = current_angle - (lowest_angle + math.pi * 2)
            elif current_angle > lowest_angle:
                current_x = current_angle - lowest_angle
            else:
                current_x = current_angle + math.pi * 2 - lowest_angle
            current_x /= (FOV / constants.SCREEN_WIDTH)
            current_x = int(current_x)

            color = rays[previous_index][1]
            if color != constants.WHITE:
                width = current_x - previous_x
                surface.fill(color, (previous_x, y, width, 20))

            previous_x = current_x
            previous_index = current_index

        current_index += 1
        if current_index >= len(rays):
            current_index = 0

        if current_index == first_index:
            break

        if lowest_angle > highest_angle:
            normal_check = highest_angle < rays[current_index][0] < lowest_angle
        elif lowest_angle < -math.pi:
            normal_check = highest_angle < rays[current_index][0] < lowest_angle + math.pi * 2
        else:
            normal_check = highest_angle < rays[current_index][0]
        modded_check = highest_angle - math.pi * 2 < rays[current_index][0] < lowest_angle
        if normal_check or modded_check:
            color = rays[current_index - 1][1]
            if color != constants.WHITE:
                width = constants.SCREEN_WIDTH - previous_x
                surface.fill(color, (previous_x, y, width, 20))
            break

    else:
        print("a")


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
                      TutorialText("Don't rely on the map!", 285),
                      TutorialText("Instead, look at your sightline and", 305),
                      TutorialText("treat movement like an FPS.", 325)),

                     (TutorialText("These colored regions are the goals.", 110),
                      TutorialText("To win, you must place exactly one circle in each goal.", 455),
                      TutorialText("Click to place a circle.", 475)),

                     (TutorialText("Great!  But that was a little easy, wasn't it?", 110),
                      TutorialText("Let's hide your character, and the circles, too.", 455),
                      TutorialText("Click once you're ready.", 475)),

                     (TutorialText("Beat the level again, but this time", 100),
                      TutorialText("using only your sightline to get around!", 120),
                      TutorialText("If you need help, check out the pause menu by pressing Escape.", 465)),

                     (TutorialText("Well done!", 110),
                      TutorialText("Once you're ready, click to move on to the next level.", 465)))

    CONTINUE_TEXT = TutorialText("Click to continue.", 475)
    COMFORTABLE_TEXT = TutorialText("Once you're comfortable, click to continue.", 475)

    CREDITS_TEXT = (TutorialText("Thanks for playing!", 160),
                    TutorialText("Programming and visuals by winterbeak.", 200),
                    TutorialText("winterbeak.itch.io", 220),
                    TutorialText("Audio by saiziju.", 280),
                    TutorialText("saiziju.itch.io", 300))

    CLICK_CONTINUE_LENGTH = 240

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
                    if self.tutorial_frame < self.CLICK_CONTINUE_LENGTH:
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
                    if self.level_num <= last_level:
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
        if self.level_num <= last_level:
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

        elif self.level_num > last_level:
            for text in self.CREDITS_TEXT:
                text.draw(surface)

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

        # sound.play(pause_sound)

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
        self.won = False

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

        self.level_num = level_num
        if level_num <= last_level:
            self.level = levels[level_num]

            self.clear_signals()
            self.signals_width = self.SIGNAL_SPACING * self.level.goal_count - self.SIGNAL_GAP

            player_entity.go_to(self.level.start_position)
            # slightly offset, "gaps" seem to appear at exact 90 degree angles
            player_entity.angle = self.level.start_orientation + 0.000001

    def place_signal(self, position):
        if self.placed_signals < self.level.goal_count:
            sound.play(circle_sounds[self.placed_signals])
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

LEVEL_PLUS = levels.Level(L0_collisions, L0_goals, (250, 250), -math.pi / 2)
LEVEL_PLUS.set_goal_colors((PALE_BLUE, PALE_ORANGE, PALE_MAGENTA, PALE_RED))


# Level 1: Two spikes
L1C0 = geometry.Polygon(((100, 125), (250, 225), (400, 125),  # indentation
                         (400, 325), (100, 325)))  # bottom
L1C0.set_colors((CYAN, MAGENTA, ORANGE, ORANGE, ORANGE))

L1_collisions = (L1C0, )

L1G0 = geometry.Polygon(((100, 125), (250, 225), (100, 225)))  # left
L1G1 = geometry.Polygon(((400, 125), (250, 225), (400, 225)))  # right
L1G2 = geometry.Polygon(((100, 225), (400, 225), (400, 325), (100, 325)))  # bottom

L1_goals = (L1G0, L1G1, L1G2)

LEVEL_TWO_SPIKES = levels.Level(L1_collisions, L1_goals, (250, 275), math.pi / 2)
LEVEL_TWO_SPIKES.set_goal_colors((PALE_CYAN, PALE_MAGENTA, PALE_ORANGE))


# Level 2: Outside of a triangle
L2C0 = geometry.Polygon(((250, 150), (175, 280), (325, 280)))
L2C0.set_colors((MAGENTA, YELLOW, RED))

L2_collisions = (L2C0, )

L2G0 = geometry.Polygon(((250, 150), (175, 280), (48, 205), (122, 77)))
L2G1 = geometry.Polygon(((250, 150), (325, 280), (452, 205), (378, 77)))
L2G2 = geometry.Polygon(((325, 280), (175, 280), (175, 430), (325, 430)))

L2_goals = (L2G0, L2G1, L2G2)

LEVEL_TRIANGLE = levels.Level(L2_collisions, L2_goals, (457, 100), math.pi / 4 * 3)
LEVEL_TRIANGLE.set_goal_colors((PALE_MAGENTA, PALE_RED, PALE_YELLOW))


# Level 3: Three boxes
L3C0 = geometry.Polygon(((50, 50), (50, 400), (450, 400)), False)  # Right angle
L3C0.set_colors((YELLOW, RED))
L3C1 = geometry.Polygon(((140, 175), (190, 175), (190, 225), (140, 225)))  # Left box
L3C1.set_colors((CYAN, MAGENTA, CYAN, MAGENTA))
L3C2 = geometry.Polygon(((225, 175), (275, 175), (275, 225), (225, 225)))  # Middle box
L3C2.set_colors((CYAN, MAGENTA, CYAN, MAGENTA))
L3C3 = geometry.Polygon(((310, 175), (360, 175), (360, 225), (310, 225)))  # Right box
L3C3.set_colors((CYAN, MAGENTA, CYAN, MAGENTA))

L3_collisions = (L3C0, L3C1, L3C2, L3C3)

L3G0 = geometry.Polygon(((50, 175), (100, 175), (100, 225), (50, 225)))  # Left goal
L3G1 = geometry.Polygon(((225, 350), (275, 350), (275, 400), (225, 400)))  # Bottom goal

L3_goals = (L3G0, L3G1)

LEVEL_THREE_BOXES = levels.Level(L3_collisions, L3_goals, (250, 312), -math.pi / 2)
LEVEL_THREE_BOXES.set_goal_colors((PALE_MAGENTA, PALE_CYAN))


# Level 4: Single line
L4C0 = geometry.Polygon(((200, 200), (300, 300)), False)
L4C0.set_colors((GREEN, ))

L4_collisions = (L4C0, )

L4G0 = geometry.Polygon(((200, 200), (300, 300), (350, 250), (250, 150)))  # Top right goal
L4G1 = geometry.Polygon(((200, 200), (300, 300), (250, 350), (150, 250)))  # Bottom left goal

L4_goals = (L4G0, L4G1)

LEVEL_SINGLE_LINE = levels.Level(L4_collisions, L4_goals, (120, 350), -math.pi / 2)
LEVEL_SINGLE_LINE.set_goal_colors((PALE_YELLOW, PALE_GREEN))


# Level 5: Box in a box
L5C0 = geometry.Polygon(((100, 100), (400, 100), (400, 400), (100, 400)))
L5C0.set_colors((CYAN, CYAN, RED, RED))
L5C1 = geometry.Polygon(((225, 225), (275, 225), (275, 275), (225, 275)))
L5C1.set_colors((RED, CYAN, CYAN, RED))

L5_collisions = (L5C0, L5C1)

L5G0 = geometry.Polygon(((100, 100), (400, 100), (275, 225), (225, 225)))
L5G1 = geometry.Polygon(((400, 400), (100, 400), (225, 275), (275, 275)))

L5_goals = (L5G0, L5G1)

LEVEL_BOXCEPTION = levels.Level(L5_collisions, L5_goals, (300, 300), math.pi / 5)
LEVEL_BOXCEPTION.set_goal_colors((PALE_CYAN, PALE_RED))


# Level 6: Five lines
L6C0 = geometry.Polygon(((199, 133), (149, 169)), False)  # Top left
L6C0.set_colors((ORANGE, ))
L6C1 = geometry.Polygon(((301, 133), (351, 169)), False)  # Top right
L6C1.set_colors((ORANGE, ))
L6C2 = geometry.Polygon(((383, 266), (363, 325)), False)  # Bottom right
L6C2.set_colors((ORANGE, ))
L6C3 = geometry.Polygon(((281, 386), (219, 386)), False)  # Bottom
L6C3.set_colors((ORANGE, ))
L6C4 = geometry.Polygon(((117, 266), (137, 325)), False)  # Bottom left
L6C4.set_colors((ORANGE, ))


L6_collisions = (L6C0, L6C1, L6C2, L6C3, L6C4)

L6G0 = geometry.Polygon(((250, 231), (273, 248), (264, 275),
                         (236, 275), (227, 248)))

L6_goals = (L6G0, )

LEVEL_PENTAGON = levels.Level(L6_collisions, L6_goals, (39, 404), -math.pi / 3)
LEVEL_PENTAGON.set_goal_colors((PALE_ORANGE, ))


# Level 7: Two buckets
L7C0 = geometry.Polygon(((100, 100), (100, 400), (400, 400), (400, 100)), False)  # outside
L7C0.set_colors((RED, GREEN, BLUE))
L7C1 = geometry.Polygon(((200, 200), (200, 300), (300, 300), (300, 200)), False)
L7C1.set_colors((RED, GREEN, BLUE))

L7_collisions = (L7C0, L7C1)

L7G0 = geometry.Polygon(((200, 200), (200, 300), (300, 300), (300, 200)))  # Center
L7G1 = geometry.Polygon(((100, 100), (200, 100), (200, 200), (100, 200)))  # Top left
L7G2 = geometry.Polygon(((300, 100), (400, 100), (400, 200), (300, 200)))  # Top right
L7G3 = geometry.Polygon(((100, 300), (200, 300), (200, 400), (100, 400)))  # Bottom left
L7G4 = geometry.Polygon(((300, 300), (300, 400), (400, 400), (400, 300)))  # Bottom right
L7_goals = (L7G0, L7G1, L7G2, L7G3, L7G4)

LEVEL_BUCKETS = levels.Level(L7_collisions, L7_goals, (357, 137), math.pi / 3 * 2)
LEVEL_BUCKETS.set_goal_colors((PALE_GREEN, PALE_RED, PALE_BLUE, PALE_CYAN, PALE_MAGENTA))


# Level 8: Two lines
L8C0 = geometry.Polygon(((200, 200), (400, 200)), False)  # top
L8C0.set_colors((CYAN, ))
L8C1 = geometry.Polygon(((100, 300), (300, 300)), False)  # bottom
L8C1.set_colors((YELLOW, ))

L8_collisions = (L8C0, L8C1)

L8G0 = geometry.Polygon(((200, 200), (200, 300), (300, 300), (300, 200)))  # Center
L8G1 = geometry.Polygon(((300, 100), (400, 100), (400, 200), (300, 200)))  # Top right
L8G2 = geometry.Polygon(((100, 300), (200, 300), (200, 400), (100, 400)))  # Bottom left
L8_goals = (L8G0, L8G1, L8G2)

LEVEL_TWO_LINES = levels.Level(L8_collisions, L8_goals, (65, 357), -math.pi / 3)
LEVEL_TWO_LINES.set_goal_colors((PALE_ORANGE, PALE_CYAN, PALE_YELLOW))


# Level 9: Barrier
L9C0 = geometry.Polygon(((113, 260), (200, 240), (300, 240), (387, 260)), False)
L9C0.set_colors((MAGENTA, CYAN, MAGENTA))

L9_collisions = (L9C0, )

L9G0 = geometry.Polygon(((200, 240), (300, 240), (300, 340), (200, 340)))  # Bottom
L9G1 = geometry.Polygon(((113, 260), (200, 240), (180, 153), (93, 173)))  # Top left
L9G2 = geometry.Polygon(((387, 260), (300, 240), (320, 153), (407, 173)))  # Top right

L9_goals = (L9G0, L9G1, L9G2)

LEVEL_WINGS = levels.Level(L9_collisions, L9_goals, (50, 250), 0.0)
LEVEL_WINGS.set_goal_colors((PALE_CYAN, PALE_MAGENTA, PALE_YELLOW))


# Level 10: Hexagon
L10C0 = geometry.Polygon(((250, 108), (374, 179), (374, 321),
                          (250, 392), (127, 321), (127, 179)))  # Hexagon
L10C0.set_colors((RED, MAGENTA, RED, RED, MAGENTA, RED))
L10C1 = geometry.Polygon(((250, 250), (250, 199)), False)  # Up
L10C1.set_colors((ORANGE, ))
L10C2 = geometry.Polygon(((250, 250), (205, 276)), False)  # Bottom left
L10C2.set_colors((ORANGE, ))
L10C3 = geometry.Polygon(((250, 250), (295, 276)), False)  # Bottom right
L10C3.set_colors((ORANGE, ))

L10_collisions = (L10C0, L10C1, L10C2, L10C3)

L10G0 = geometry.Polygon(((250, 250), (250, 199), (205, 225), (205, 276)))  # Top left
L10G1 = geometry.Polygon(((250, 250), (250, 199), (295, 225), (295, 276)))  # Top right

L10_goals = (L10G0, L10G1)

LEVEL_HEXAGON = levels.Level(L10_collisions, L10_goals, (240, 275), math.pi)
LEVEL_HEXAGON.set_goal_colors((PALE_ORANGE, PALE_MAGENTA))


# Level 11: Elbow
L11C0 = geometry.Polygon(((200, 200), (300, 200), (200, 300)), False)
L11C0.set_colors((CYAN, CYAN))

L11_collisions = (L11C0, )

L11G0 = geometry.Polygon(((200, 200), (300, 200), (200, 300)))  # Inside
L11G1 = geometry.Polygon(((200, 200), (250, 200), (250, 150), (200, 150)))  # Top

L11_goals = (L11G0, L11G1)

LEVEL_ELBOW = levels.Level(L11_collisions, L11_goals, (400, 50), math.pi / 4 * 3)
LEVEL_ELBOW.set_goal_colors((PALE_CYAN, PALE_ORANGE))


# Level 12: Grid
def generate_level_12():
    margin = 50
    spacing = 400 / 11
    collision = []

    # horizontal lines
    for row in range(4):
        for column in range(3):
            x1 = int(spacing * column * 3 + spacing * 2) + margin
            x2 = x1 + int(spacing)
            y = int(spacing * row * 3 + spacing) + margin
            collision.append(geometry.Polygon(((x1, y), (x2, y)), False))

    collision.pop(-2)  # removal of middle-bottom line

    # vertical lines
    for column in range(4):
        for row in range(3):
            x = int(spacing * column * 3 + spacing) + margin
            y1 = int(spacing * row * 3 + spacing * 2) + margin
            y2 = y1 + int(spacing)
            collision.append(geometry.Polygon(((x, y1), (x, y2)), False))

    for polygon in collision:
        polygon.set_colors((RED, ))

    # bottom middle
    x1 = int(spacing * 4 + margin)
    y1 = int(spacing * 7 + margin)
    x2 = x1 + int(spacing * 3)
    y2 = y1 + int(spacing * 3)

    goal_1 = geometry.Polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2)))

    # middle left
    x1 = int(spacing + margin)
    y1 = int(spacing * 4 + margin)
    x2 = x1 + int(spacing * 3)
    y2 = y1 + int(spacing * 3)

    goal_2 = geometry.Polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2)))

    # top right
    x1 = int(spacing * 7 + margin)
    y1 = int(spacing + margin)
    x2 = x1 + int(spacing * 3)
    y2 = y1 + int(spacing * 3)

    goal_3 = geometry.Polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2)))

    goals = (goal_1, goal_2, goal_3)

    level = levels.Level(collision, goals, (250, 250), math.pi)
    level.set_goal_colors((PALE_RED, PALE_CYAN, PALE_ORANGE))

    return level


LEVEL_GRID = generate_level_12()


# Level 13: Warning sign/keyhole
L13C0 = geometry.Polygon(((131, 100), (390, 250), (131, 400)))  # Triangle
L13C0.set_colors((GREEN, GREEN, GREEN))
L13C1 = geometry.Polygon(((203, 239), (260, 239), (260, 260), (203, 260)))  # Rectangle
L13C1.set_colors((CYAN, CYAN, CYAN, CYAN))

L13_collisions = (L13C0, L13C1)

L13G0 = geometry.Polygon(((390, 250), (341, 222), (341, 278)))  # Right corner
L13G1 = geometry.Polygon(((203, 239), (203, 260), (182, 260), (182, 239)))  # Left of rectangle
L13G2 = geometry.Polygon(((203, 239), (260, 239), (260, 182), (203, 182)))  # Top of rectangle

L13_goals = (L13G0, L13G1, L13G2)

LEVEL_KEYHOLE = levels.Level(L13_collisions, L13_goals, (150, 150), math.pi / 4)
LEVEL_KEYHOLE.set_goal_colors((PALE_GREEN, PALE_CYAN, PALE_ORANGE))


# Level 14: H
L14C0 = geometry.Polygon(((100, 100), (200, 100), (200, 200), # Starts with top left horizontal,
                          (300, 200), (300, 100), (400, 100), # travels clockwise
                          (400, 200), (400, 300), (400, 400), # Bottom right
                          (300, 400), (300, 300), (200, 300),
                          (200, 400), (100, 400), (100, 300),
                          (100, 200)))
L14C0.set_colors((YELLOW,
                  GREEN, GREEN, GREEN,  # Bucket at top of the H
                  YELLOW, GREEN, YELLOW, GREEN, YELLOW,
                  GREEN, GREEN, GREEN,  # Bucket at bottom of the H
                  YELLOW, GREEN, YELLOW, GREEN))

L14_collisions = (L14C0, )

L14G0 = geometry.Polygon(((100, 100), (200, 100), (200, 200), (100, 200)))  # Top left
L14G1 = geometry.Polygon(((300, 100), (400, 100), (400, 200), (300, 200)))  # Top right
L14G2 = geometry.Polygon(((100, 300), (200, 300), (200, 400), (100, 400)))  # Bottom left
L14G3 = geometry.Polygon(((300, 300), (400, 300), (400, 400), (300, 400)))  # Bottom right

L14_goals = (L14G0, L14G1, L14G2, L14G3)

LEVEL_H = levels.Level(L14_collisions, L14_goals, (350, 250), math.pi)
LEVEL_H.set_goal_colors((PALE_GREEN, PALE_MAGENTA, PALE_CYAN, PALE_YELLOW))


# Level template
# L#C0 = geometry.Polygon(((x, y), (x, y), (x, y)))
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
# L# = levels.Level(L#_collisions, L#_goals, (start_x, start_y), orientation)
# L#.set_goal_colors((color1, color2, color3))


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

# Note: the levels are actually out of order
levels = (LEVEL_THREE_BOXES,
          LEVEL_TWO_SPIKES,
          LEVEL_TRIANGLE,
          LEVEL_PLUS,
          LEVEL_SINGLE_LINE,
          LEVEL_PENTAGON,
          LEVEL_WINGS,
          LEVEL_TWO_LINES,
          LEVEL_BUCKETS,
          LEVEL_H,
          LEVEL_BOXCEPTION,
          LEVEL_HEXAGON,
          LEVEL_ELBOW,
          LEVEL_KEYHOLE,
          LEVEL_GRID
          )
last_level = len(levels) - 1

play_screen.load_level(0)
play_screen.show_player = True

sound.load_music("music")
sound.play_music()

pygame.event.set_grab(True)
pygame.mouse.set_visible(False)
play_screen.mouse_lock = 5

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
