import pygame
import math

import geometry
import events
import constants

pygame.init()


class Player:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.position = (0.0, 0.0)
        self.angle = 0.0

    def update_movement(self):
        self.angle += (float(events.mouse.relative[0]) / 100)

        key_a = pygame.K_a in events.keys.queue
        key_w = pygame.K_w in events.keys.queue
        key_d = pygame.K_d in events.keys.queue
        key_s = pygame.K_s in events.keys.queue

        angle = self.angle
        move = False
        if key_a and not key_d:
            angle -= math.pi / 2
            move = True
        elif key_d and not key_a:
            angle += math.pi / 2
            move = True

        if key_w and not key_s:
            move = True
        elif key_s and not key_w:
            move = True
            angle += math.pi

        if move:
            difference = geometry.vector_to_difference(angle, 1.0)
            self.move(difference)

    def go_to(self, position):
        self.position = position
        self.x = position[0]
        self.y = position[1]

    def move(self, difference):
        self.position = constants.add_tuples(self.position, difference)
        self.x = self.position[0]
        self.y = self.position[1]

    def draw_debug(self, surface):
        x = int(self.x)
        y = int(self.y)
        pygame.draw.circle(surface, constants.MAGENTA, (x, y), 5)

        blip_difference = geometry.vector_to_difference(self.angle, 5)
        blip_position = constants.add_tuples((x, y), blip_difference)
        pygame.draw.line(surface, constants.CYAN, (x, y), blip_position)
