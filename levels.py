import pygame

import geometry
import constants

pygame.init()


class Level:
    def __init__(self, collision, goals):
        self.collision = collision
        self.goals = goals

    def draw_debug(self, surface, offset=(0, 0)):
        for polygon in self.goals:
            polygon.draw_debug(surface, offset)

        for polygon in self.collision:
            for segment in polygon.segments:
                segment.draw_debug(surface, offset)

    def set_goal_colors(self, colors_list):
        for index, color in enumerate(colors_list):
            self.goals[index].color = color
