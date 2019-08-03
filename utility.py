import pygame
import constants

def int_tuple(tuple_):
    return int(tuple_[0]), int(tuple_[1])


def add_tuples(tuple1, tuple2):
    return tuple1[0] + tuple2[0], tuple1[1] + tuple2[1]


def average(*args):
    if type(args[0]) == tuple or type(args[0] == list):
        args = args[0]

    total = 0
    for arg in args:
        total += arg

    return total / len(args)


def blit_vert_center(destination, surface, y):
    x = (destination.get_width() - surface.get_width()) // 2
    destination.blit(surface, (x, y))


def black_text_alpha(font, string, alpha):
    text_surface = font.render(string, True, constants.BLACK)

    return black_image_alpha(text_surface, alpha)


def black_image_alpha(surface, alpha):
    """For a surface that only uses shades of black, this returns a surface
    setting that image to the specified alpha value."""

    temp_surface = pygame.Surface(surface.get_size()).convert_alpha()
    temp_surface.fill((0, 0, 0, alpha))
    surface.blit(temp_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    return surface.convert_alpha()
