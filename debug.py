import pygame

pygame.init()

TAHOMA = pygame.font.SysFont("Tahoma", 10)

strings = []


def debug(*args):
    string = ""
    for arg in args:
        string += repr(arg) + " "
    strings.append(string)


def draw(surface):
    for string_num, string in enumerate(strings):
        text = TAHOMA.render(string, False, (255, 255, 255), (0, 0, 0))
        surface.blit(text, (10, string_num * 10 + 10))

    strings.clear()