import pygame
import sys

pygame.init()


class MouseHandler:
    def __init__(self):
        self.clicked = False
        self.released = False
        self.held = False
        self.position = (0, 0)
        self.relative = (0, 0)


class KeyHandler:
    def __init__(self):
        self.held = False
        self.held_key = None
        self.pressed = False
        self.pressed_key = None
        self.released = False
        self.released_key = None
        self.queue = []


quit_program = False


def update():
    global quit_program

    mouse.clicked = False
    mouse.released = False
    mouse.position = pygame.mouse.get_pos()
    mouse.relative = pygame.mouse.get_rel()

    keys.released = False
    keys.released_key = None
    keys.pressed = False
    keys.pressed_key = None

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse.held = True
            mouse.clicked = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mouse.held = False
            mouse.released = True

        elif event.type == pygame.KEYDOWN:
            keys.queue.append(event.key)
            keys.pressed = True
            keys.pressed_key = event.key

        elif event.type == pygame.KEYUP:
            keys.queue.remove(event.key)

            keys.released = True
            keys.released_key = event.key

        elif event.type == pygame.QUIT:
            quit_program = True

    keys.held = len(keys.queue) > 0
    if keys.held:
        keys.held_key = keys.queue[-1]
    else:
        keys.held_key = None


mouse = MouseHandler()
keys = KeyHandler()
