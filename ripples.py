import pygame
import math

import constants

pygame.init()
pygame.display.set_mode(constants.SCREEN_SIZE)


class Ripple:
    def __init__(self, position, color, final_radius=20, duration=30):
        self.frame = 0
        self.last_frame = duration

        self.position = (int(position[0]), int(position[1]))
        self.radius = 1.0
        self.final_radius = final_radius
        self.alpha = 0

        self.expand_a = abs(final_radius - 1.0)
        self.expand_k = math.pi / (2 * duration)
        self.color = color

    def update(self):
        self.radius = math.sin(self.expand_k * self.frame)
        self.radius = self.expand_a * self.radius + 1.0

        self.alpha = 255 - int((self.frame / self.last_frame) * 255)

        self.frame += 1

    def draw(self, surface, offset=(0, 0)):
        position = (self.position[0] + offset[0], self.position[1] + offset[1])

        color = (self.color[0], self.color[1], self.color[2], self.alpha)
        radius = int(self.radius)
        pygame.draw.circle(surface, color, position, radius, 1)


temp_surface = pygame.Surface(constants.SCREEN_SIZE).convert_alpha()


class RippleHandler:
    def __init__(self):
        self.ripples = []

    def update(self):
        ripple_num = len(self.ripples)
        for ripple in reversed(self.ripples):
            ripple_num -= 1
            ripple.update()

            if ripple.frame == ripple.last_frame:
                del self.ripples[ripple_num]

    def draw(self, surface, offset=(0, 0)):
        temp_surface.fill((0, 0, 0, 0))
        for ripple in self.ripples:
            ripple.draw(temp_surface)
        surface.blit(temp_surface, offset)

    def create_ripple(self, position, color, final_radius=20, duration=30):
        self.ripples.append(Ripple(position, color, final_radius, duration))

    def clear(self):
        self.ripples.clear()
