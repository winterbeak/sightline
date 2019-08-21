import pygame

import constants

pygame.init()

TAHOMA = pygame.font.SysFont("Tahoma", 10)

strings = []
lines = []


def debug(*args):
    string = ""
    for arg in args:
        string += repr(arg) + " "
    strings.append(string)


def new_line(point1, point2, color=constants.RED):
    lines.append((point1, point2, color))


def draw(surface):
    for line in lines:
        x1 = line[0][0]
        y1 = line[0][1]
        x2 = line[1][0]
        y2 = line[1][1]
        pygame.draw.line(surface, line[2], (x1, y1), (x2, y2), 1)

    for string_num, string in enumerate(strings):
        text = TAHOMA.render(string, False, (255, 255, 255), (0, 0, 0))
        surface.blit(text, (10, string_num * 10 + 10))

    strings.clear()
    lines.clear()
