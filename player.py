import pygame
import math

import utility
import geometry
import events
import constants

pygame.init()

FOV = math.pi / 2
sensitivity = 0.002


class Player:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.position = (0.0, 0.0)
        self.angle = 0.0

    def update_movement(self, level):
        self.angle += (float(events.mouse.relative[0]) * sensitivity)
        self.angle = geometry.mod_angle(self.angle)

        key_a = pygame.K_a in events.keys.queue
        key_w = pygame.K_w in events.keys.queue
        key_d = pygame.K_d in events.keys.queue
        key_s = pygame.K_s in events.keys.queue

        key_a = key_a and not key_d
        key_d = key_d and not key_a
        key_w = key_w and not key_s
        key_s = key_s and not key_w

        angle = self.angle

        if key_a and key_w:
            angle -= math.pi / 4
        elif key_w and key_d:
            angle += math.pi / 4
        elif key_d and key_s:
            angle += math.pi / 4 * 3
        elif key_s and key_a:
            angle -= math.pi / 4 * 3

        elif key_a:
            angle -= math.pi / 2
        elif key_w:
            pass
        elif key_d:
            angle += math.pi / 2
        elif key_s:
            angle += math.pi
        else:
            return

        angle = geometry.mod_angle(angle)
        difference = geometry.vector_to_difference(angle, 1.2)

        next_position = utility.add_tuples(difference, self.position)

        collide = False

        move_segment = geometry.Segment(self.position, next_position)
        for polygon in level.collision:
            for segment in polygon.segments:
                if geometry.segments_collide(segment, move_segment):
                    collide = True

                    to_wall = geometry.point_and_segment(next_position, segment)
                    if to_wall:
                        vector = geometry.points_to_vector(next_position, to_wall.point1)
                        difference = geometry.vector_to_difference(vector[0], vector[1] + 1.0)
                        position = utility.add_tuples(next_position, difference)

                        move_segment_2 = geometry.Segment(self.position, position)

                        valid_move = True

                        for polygon_2 in level.collision:
                            for segment_2 in polygon_2.segments:
                                if geometry.segments_collide(segment_2, move_segment_2):
                                    valid_move = False

                        if valid_move:
                            self.go_to(position)

        if not collide:
            self.move(difference)

    def go_to(self, position):
        self.position = position
        self.x = float(position[0])
        self.y = float(position[1])

    def move(self, difference):
        self.position = utility.add_tuples(self.position, difference)
        self.x = float(self.position[0])
        self.y = float(self.position[1])

    def draw_debug(self, surface, level, offset=(0, 0)):
        position = utility.int_tuple(self.position)

        if offset != (0, 0):
            position = utility.add_tuples(position, offset)

        self.draw_visor_line(surface, self.angle - FOV / 2, level, offset)
        self.draw_visor_line(surface, self.angle + FOV / 2, level, offset)

        pygame.draw.circle(surface, constants.BLACK, position, 5)

    def draw_visor_line(self, surface, angle, level, offset=(0, 0)):
        point1 = self.position
        point2 = geometry.closest_wall_level_intersection(self.position, level, angle)

        if offset != (0, 0):
            point1 = utility.add_tuples(point1, offset)
            point2 = utility.add_tuples(point2, offset)

        if point2:
            pygame.draw.line(surface, constants.BLACK, point1, point2)
        else:
            point2 = geometry.screen_edge(self.position, angle)
            pygame.draw.line(surface, constants.BLACK, point1, point2)
