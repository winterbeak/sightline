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

title_text = pygame.image.load(os.path.join("images", "title.png"))

level_offset = (0, 50)

zoomed_ripples = ripples.RippleHandler()
unzoomed_ripples = ripples.RippleHandler()


def create_debug_mode_file():
    file = open("Debug Mode.txt", "w+")
    file.write("False\n")
    file.close()


if os.path.exists("Debug Mode.txt"):
    if open("Debug Mode.txt").read().strip() == "True":
        debug_mode = True
    else:
        debug_mode = False
else:
    create_debug_mode_file()
    debug_mode = False


def screen_update(fps):
    pygame.display.flip()
    final_display.fill(constants.WHITE)
    clock.tick(fps)


FOV = player.FOV


def new_ray(position, level, angle):
    segment = geometry.closest_wall_level(position, level, angle)

    if segment:
        color = segment.color
        if debug_mode:
            debug_point_1 = geometry.closest_wall_level_intersection(position, level, angle)
            debug_point_1 = utility.add_tuples(debug_point_1, level_offset)
            debug_point_2 = player_entity.position
            debug_point_2 = utility.add_tuples(debug_point_2, level_offset)
            debug.new_line(debug_point_1, debug_point_2)
    else:
        color = constants.WHITE
        if debug_mode:
            debug_point_1 = geometry.screen_edge(position, angle)
            debug_point_1 = utility.add_tuples(debug_point_1, level_offset)
            debug_point_2 = player_entity.position
            debug_point_2 = utility.add_tuples(debug_point_2, level_offset)
            debug.new_line(debug_point_1, debug_point_2)

    return angle, color


def draw_view(surface, y):
    rays = []

    position = player_entity.position
    level = play_screen.level

    # Note: there is a bug that happens on corners where the player can
    # seemingly be surrounded by colors despite not actually being so
    # One "fix" involves increasing the 0.00001 threshold, but it never
    # out right fixes it, only reduces its chances of happening.  Also, it
    # makes your view shakier when you rub against walls
    # A potential fix I haven't tried is making it so you can't get too close
    # to a wall
    for polygon in play_screen.level.collision:
        for point in polygon.point_list:
            angle = geometry.angle_between(position, point)
            rays.append(new_ray(position, level, angle - 0.00007))
            rays.append(new_ray(position, level, angle))
            rays.append(new_ray(position, level, angle + 0.00007))

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


class TitleScreen:
    FADE_SPEED = 255 / 120

    def __init__(self):
        self.text_frame = 0
        self.fade_wait_frame = 0

        self.alpha = 0.0
        self.text_alpha = 0.0

        self.fading_out = False
        self.finished = False
        self.quit_game = False

    def update(self):
        if events.mouse.released and not self.fading_out:
            self.fading_out = True
            sound.play(circle_sounds[0], 0.8)

        if self.fading_out:
            self.alpha -= self.FADE_SPEED

            if self.text_alpha > 0.0:
                self.text_alpha -= self.FADE_SPEED
                if self.text_alpha < 0.0:
                    self.text_alpha = 0.0

            if self.alpha <= 0.0:
                self.alpha = 0.0
                if self.fade_wait_frame < 15:
                    self.fade_wait_frame += 1
                else:
                    self.finished = True

        elif self.alpha < 255.0:
            self.alpha += self.FADE_SPEED
            if self.alpha > 255.0:
                self.alpha = 255.0

        title_text.set_alpha(self.alpha)

        if self.text_frame < 150.0:
            self.text_frame += 1
        elif not self.fading_out and self.text_alpha < 255.0:
            self.text_alpha += self.FADE_SPEED
            if self.text_alpha > 255.0:
                self.text_alpha = 255.0

    def draw(self, surface):
        utility.blit_vert_center(surface, title_text, 100)

        credits_text = utility.black_text_alpha(subtitle_font, "A game by winterbeak and saiziju.", self.alpha)
        utility.blit_vert_center(surface, credits_text, 200)

        click_text = utility.black_text_alpha(subtitle_font, "Click to start.", self.text_alpha)
        utility.blit_vert_center(surface, click_text, 350)


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
                pygame.Rect(130, 440, 30, 30),  # Previous level
                pygame.Rect(340, 440, 30, 30))  # Next level

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
                    TutorialText("Programming and visuals by winterbeak.", 220),
                    TutorialText("winterbeak.itch.io", 240),
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
            zoomed_ripples.update()
            unzoomed_ripples.update()

            if self.pause_alpha > 0:
                self.pause_alpha -= self.PAUSE_FADE_SPEED

                if self.pause_alpha < 0:
                    self.pause_alpha = 0

                self.pause_overlay.set_alpha(self.pause_alpha * self.OVERLAY_OPACITY)

            player_entity.update_movement(self.level)

            if events.mouse.released:
                if self.level_num == 0 and not self.changing_tutorial_stage:
                    if self.tutorial_stage < 3:
                        self.next_tutorial_stage()
                    elif self.tutorial_stage == 4:
                        self.next_tutorial_stage()

                        position = utility.add_tuples(player_entity.position, level_offset)
                        zoomed_ripples.create_ripple(position, BLACK, 30, 30)

                        for signal in self.signals:
                            position = utility.add_tuples(signal.position, level_offset)
                            zoomed_ripples.create_ripple(position, signal.color, 30, 30)

                        for index in range(self.level.goal_count):
                            x = constants.SCREEN_MIDDLE_INT[0] - self.signals_width // 2
                            x += index * self.SIGNAL_SPACING + Signal.RADIUS

                            unzoomed_ripples.create_ripple((x, 90), self.signals[index].color, 30, 30)

                        self.show_player = False

                        self.clear_signals()
                        self.won = False
                    elif self.tutorial_stage == 6:
                        self.next_level_transitioning = True
                        sound.play(circle_sounds[0], 0.8)

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
                            position = utility.add_tuples(signal.position, level_offset)
                            position = utility.int_tuple(position)

                            zoomed_ripples.create_ripple(position, color, 30, 30)

                        if self.won:
                            color = signal.color
                        else:
                            color = BLACK

                        unzoomed_ripples.create_ripple((x, y), color, 30, 30)

                    if self.won:
                        if self.level_num == 0 and (self.tutorial_stage == 3 or self.tutorial_stage == 5):
                            self.changing_tutorial_stage = True
                        else:
                            self.next_level_transitioning = True

                        completion_data[self.level_num] = True
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

            zoomed_ripples.draw(self.zoom_temp)

            if self.verdicting or self.drama_pausing or self.resulting:
                width = int(self.zoom * constants.SCREEN_WIDTH)
                height = int(self.zoom * constants.SCREEN_HEIGHT)
                zoom_surface = pygame.transform.scale(self.zoom_temp, (width, height))
                x = -(width - constants.SCREEN_WIDTH) // 2
                y = -(height - constants.SCREEN_HEIGHT) // 2
                surface.blit(zoom_surface, (x, y))

            draw_view(surface, 50)

            unzoomed_ripples.draw(surface)

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

            text = utility.black_text_alpha(subtitle_font, "Change level", self.pause_alpha)
            utility.blit_vert_center(surface, text, 441)

            text = utility.black_text_alpha(subtitle_font, "<", self.pause_alpha)
            x = constants.SCREEN_MIDDLE[0] - 112
            y = self.HITBOXES[self.PREVIOUS_LEVEL].top - 1
            surface.blit(text, (x, y))

            text = utility.black_text_alpha(subtitle_font, ">", self.pause_alpha)
            x = constants.SCREEN_MIDDLE[0] + 99
            y = self.HITBOXES[self.PREVIOUS_LEVEL].top - 1
            surface.blit(text, (x, y))

            if self.level_num <= last_level and completion_data[self.level_num]:
                text = utility.black_text_alpha(small_font, "Completed", self.pause_alpha)
                utility.blit_vert_center(surface, text, 470)

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
        zoomed_ripples.clear()
        unzoomed_ripples.clear()

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
            self.level = all_levels[level_num]

            self.clear_signals()
            self.signals_width = self.SIGNAL_SPACING * self.level.goal_count - self.SIGNAL_GAP

            player_entity.go_to(self.level.start_position)
            # slightly offset, "gaps" seem to appear at exact 90 degree angles
            player_entity.angle = self.level.start_orientation + 0.000001

        self.previous_signals = []

    def place_signal(self, position):
        """Places a circle (known as a Signal earlier in development) onto
        the level, at the given position.
        """

        # This fixes a bug where, if you use the Change Level buttons to go to
        # the credits, you can still place signals for some reason.
        if self.level_num > last_level:
            return

        if self.placed_signals < self.level.goal_count:
            sound.play(circle_sounds[self.placed_signals])
            self.signals.append(Signal(position, self.level))
            self.placed_signals += 1

        if self.placed_signals == self.level.goal_count:
            if self.show_circles and self.previous_signals:
                for signal in self.previous_signals:
                    position = utility.add_tuples(signal.position, level_offset)
                    zoomed_ripples.create_ripple(position, signal.color, 30, 30)
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

    def next_tutorial_stage(self):
        self.changing_tutorial_stage = True
        sound.play(circle_sounds[0], 0.8)


title_screen = TitleScreen()
play_screen = PlayScreen()
player_entity = player.Player()

all_levels = (levels.generate_three_boxes_level(),
              levels.generate_triangle_level(),
              levels.generate_jesters_hat_level(),
              levels.generate_plus_level(),
              levels.generate_single_line_level(),
              levels.generate_pentagon_level(),
              levels.generate_wings_level(),
              levels.generate_reticles_level(),
              levels.generate_two_lines_level(),
              levels.generate_tunnel_level(),
              levels.generate_z_level(),
              levels.generate_buckets_level(),
              levels.generate_shapes_level(),
              levels.generate_missing_corner_level(),
              levels.generate_spiral_level(),
              levels.generate_increasing_level(),
              levels.generate_pegs_level(),
              levels.generate_h_level(),
              levels.generate_staircase_level(),
              levels.generate_hexagon_level(),
              levels.generate_triangle_array_level(),
              levels.generate_boxception_level(),
              levels.generate_cube_level(),
              levels.generate_positioning_level(),
              levels.generate_square_level(),
              levels.generate_keyhole_level(),
              levels.generate_diamond_level(),
              levels.generate_star_level(),
              levels.generate_grid_level(),
              levels.generate_heart_level()
              )
last_level = len(all_levels) - 1


def create_save_data():
    file = open("Easily Editable Save Data.txt", "w+")
    file.write("0 " + " ".join(("False", ) * len(all_levels)) + "\n")
    file.close()


def load_save_data():
    if os.path.exists("Easily Editable Save Data.txt"):
        file = open("Easily Editable Save Data.txt", "r")
        data = file.read().strip().split()

        # The first number indicates the last level the player was viewing,
        # so it's useless in this case
        if len(data) == len(all_levels) + 1:
            data.pop(0)
            level_complete = []

            for data in data:
                if data == "True":
                    level_complete.append(True)
                else:
                    level_complete.append(False)

            return level_complete

        else:
            create_save_data()
            return [False, ] * len(all_levels)
    else:
        create_save_data()
        return [False, ] * len(all_levels)


def get_last_exited_level():
    """Returns the level that the player was on when they last
    exited the application.
    """
    if os.path.exists("Easily Editable Save Data.txt"):
        file = open("Easily Editable Save Data.txt", "r")
        data = file.read().split()
        if len(data) == len(all_levels) + 1:
            if data[0].isnumeric():
                return int(data[0])

    create_save_data()
    return 0


def save_save_data():
    string = str(play_screen.level_num) + " "
    string += " ".join(tuple(str(data) for data in completion_data))
    string += "\n"

    file = open("Easily Editable Save Data.txt", "w+")
    file.write(string)
    file.close()


completion_data = load_save_data()

TITLE = 0
GAME = 1

current_screen = TITLE

last_exited_level = get_last_exited_level()
if last_exited_level == last_level + 1:
    last_exited_level = last_level

play_screen.load_level(last_exited_level)

if last_exited_level == 0:
    play_screen.show_player = True
    play_screen.mouse_lock = 20
else:
    play_screen.show_player = False

sound.load_music("music")
sound.play_music()

while True:
    events.update()
    if events.quit_program:
        break
    sound.update()

    if current_screen == TITLE:
        title_screen.update()
        title_screen.draw(final_display)
        if title_screen.finished:
            current_screen = GAME

            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)
            play_screen.alpha = 0.0

        if title_screen.quit_game:
            break

    elif current_screen == GAME:
        play_screen.update()
        if play_screen.quit_game:
            break
        play_screen.draw(final_display)

    if debug_mode:
        debug.debug(clock.get_fps())
        debug.draw(final_display)

    screen_update(60)

save_save_data()
