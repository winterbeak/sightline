import pygame

import geometry
import constants

pygame.init()


class Level:
    def __init__(self, collision, goals, start_position, start_orientation):
        self.start_position = start_position
        self.start_orientation = start_orientation
        self.collision = collision
        self.goals = goals
        self.goal_count = len(goals)

    def draw_debug_goals(self, surface, offset=(0, 0), alpha=255):
        for polygon in self.goals:
            if alpha != 255:
                red = 255 - (255 - polygon.color[0]) * (alpha / 255)
                green = 255 - (255 - polygon.color[1]) * (alpha / 255)
                blue = 255 - (255 - polygon.color[2]) * (alpha / 255)
                polygon.draw_debug(surface, offset, (red, green, blue))
            else:
                polygon.draw_debug(surface, offset)

    def draw_debug_outline(self, surface, offset=(0, 0)):
        for polygon in self.collision:
            for segment in polygon.segments:
                segment.draw_debug(surface, offset)

    def set_goal_colors(self, colors_list):
        for index, color in enumerate(colors_list):
            self.goals[index].color = color
