import pygame
import math

import geometry
import events
import constants

pygame.init()

FOV = math.pi / 2


class Player:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.position = (0.0, 0.0)
        self.angle = 0.0

    def update_movement(self, level):
        self.angle += (float(events.mouse.relative[0]) / 200)
        self.angle = geometry.mod_angle(self.angle)

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
            angle = geometry.mod_angle(angle)
            difference = geometry.vector_to_difference(angle, 1.0)

            next_position = constants.add_tuples(difference, self.position)

            collide = False

            move_segment = geometry.Segment(self.position, next_position)
            for polygon in level.polygons:
                for segment in polygon.segments:
                    if geometry.segments_collide(segment, move_segment):
                        collide = True

                        to_wall = geometry.point_and_segment(next_position, segment)
                        if to_wall:
                            vector = geometry.points_to_vector(next_position, to_wall.point1)
                            difference = geometry.vector_to_difference(vector[0], vector[1] + 1.0)
                            position = constants.add_tuples(next_position, difference)

                            move_segment_2 = geometry.Segment(self.position, position)

                            valid_move = True

                            for polygon_2 in level.polygons:
                                for segment_2 in polygon_2.segments:
                                    if geometry.segments_collide(segment_2, move_segment_2):
                                        valid_move = False

                            if valid_move:
                                self.go_to(position)

            if not collide:
                self.move(difference)

    def go_to(self, position):
        self.position = position
        self.x = position[0]
        self.y = position[1]

    def move(self, difference):
        self.position = constants.add_tuples(self.position, difference)
        self.x = self.position[0]
        self.y = self.position[1]

    def draw_debug(self, surface, level):
        x = int(self.x)
        y = int(self.y)
        pygame.draw.circle(surface, constants.MAGENTA, (x, y), 5)

        self.draw_visor_line(surface, self.angle - FOV / 2, level)
        self.draw_visor_line(surface, self.angle + FOV / 2, level)

    def draw_visor_line(self, surface, angle, level):
        difference = geometry.vector_to_difference(angle, 5)
        point1 = constants.add_tuples(self.position, difference)
        point2 = geometry.closest_wall_level_intersection(self.position, level, angle)

        if point2:
            pygame.draw.line(surface, constants.BLACK, point1, point2)
        else:
            point2 = geometry.screen_edge(self.position, angle)
            pygame.draw.line(surface, constants.BLACK, point1, point2)
