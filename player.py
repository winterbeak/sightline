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
    MOVEMENT_SPEED = 1.3

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.position = (0.0, 0.0)
        self.angle = 0.0

    def update_movement(self, level):
        self.angle += (float(events.mouse.relative[0]) * sensitivity)
        self.angle = geometry.mod_angle(self.angle)

        key_a_pressed = pygame.K_a in events.keys.queue
        key_w_pressed = pygame.K_w in events.keys.queue
        key_d_pressed = pygame.K_d in events.keys.queue
        key_s_pressed = pygame.K_s in events.keys.queue

        key_a = key_a_pressed and not key_d_pressed
        key_d = key_d_pressed and not key_a_pressed
        key_w = key_w_pressed and not key_s_pressed
        key_s = key_s_pressed and not key_w_pressed

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
        difference = geometry.vector_to_difference(angle, self.MOVEMENT_SPEED)

        next_position = utility.add_tuples(difference, self.position)

        collide = False

        move_segment = geometry.Segment(self.position, next_position)
        for segment in level.player_collision:
            if geometry.segments_collide(segment, move_segment):
                collide = True

                # note: to_wall is None when next_position is on
                # the wall.
                to_wall = geometry.point_and_segment(next_position, segment)
                if to_wall:
                    vector = geometry.points_to_vector(next_position, to_wall.point1)
                    difference = geometry.vector_to_difference(vector[0], vector[1] + 1.0)
                    position = utility.add_tuples(next_position, difference)

                    # bug: sometimes you get stuck trying to slide off the
                    # end of a line segment
                    if not self.movement_collides_level(position, level):
                        self.go_to(position)

                else:
                    # the next position will either be 1.0 away on one
                    # side of the wall, or the other.  the correct position
                    # is chosen by looking at which position doesn't cross
                    # the wall.
                    perpendicular = geometry.inverse(segment.slope)
                    angle = geometry.slope_to_angle(perpendicular)

                    difference_1 = geometry.vector_to_difference(angle, 1.0)
                    difference_2 = geometry.vector_to_difference(angle - math.pi, 1.0)
                    position_1 = utility.add_tuples(next_position, difference_1)
                    position_2 = utility.add_tuples(next_position, difference_2)

                    segment_1 = geometry.Segment(self.position, position_1)
                    if geometry.segments_collide(segment, segment_1):
                        position = position_2
                    else:
                        position = position_1

                    if not self.movement_collides_level(position, level):
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

        pygame.draw.circle(surface, constants.BLACK, position, 7)

    def draw_visor_line(self, surface, angle, level, offset=(0, 0)):
        point1 = self.position
        point2 = geometry.closest_wall_level_intersection(self.position, level, angle)

        if point2:
            if offset != (0, 0):
                point1 = utility.add_tuples(point1, offset)
                point2 = utility.add_tuples(point2, offset)

            # Experimented with line thickness 2, reduces game-feel but
            # increases visibility of lines
            pygame.draw.line(surface, constants.BLACK, point1, point2)
        else:
            point2 = geometry.screen_edge(self.position, angle, offset)
            if point2:
                if offset != (0, 0):
                    point1 = utility.add_tuples(point1, offset)

                # Line thickness 2 here as well
                pygame.draw.line(surface, constants.BLACK, point1, point2)

    def movement_collides_level(self, position, level):
        move_segment = geometry.Segment(self.position, position)
        for segment in level.player_collision:
            if geometry.segments_collide(segment, move_segment):
                return True
        return False
