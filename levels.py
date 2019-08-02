import pygame

import geometry
import constants

pygame.init()


class Level:
    def __init__(self, polygons):
        self.polygons = polygons

    def draw_debug(self, surface):
        for polygon in self.polygons:
            for segment in polygon.segments:
                segment.draw_debug(surface)
