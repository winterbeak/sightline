import pygame
import math

import constants

pygame.init()


def vector_to_difference(angle, magnitude):
    """Converts a vector into a difference of x and a difference of y."""
    delta_x = math.cos(angle) * magnitude
    delta_y = math.sin(angle) * magnitude
    return delta_x, delta_y


def difference_to_vector(difference):
    """Converts a (delta_x, delta_y) pair into an (angle, magnitude) pair.
    Note that the y axis is inverted, since that's what pygame does."""
    delta_x, delta_y = difference
    magnitude = math.sqrt(delta_x ** 2 + delta_y ** 2)

    angle = math.atan2(delta_y, delta_x)

    # print("%.2f / %.2f" % (delta_y, delta_x))

    return angle, magnitude


def distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def two_point_slope(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    if x1 == x2:
        return math.inf
    return float(y2 - y1) / float(x2 - x1)


def y_intercept(point, slope):
    if math.isinf(slope):
        return None
    x, y = point
    return y - slope * x


class Segment:
    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2

        self.length = distance(point1, point2)
        self.slope = two_point_slope(point1, point2)

        # y_intercept is stored as if the segment was infinite
        self.y_intercept = y_intercept(point1, self.slope)
        if self.slope == 0.0:
            self.x_intercept = None
        elif math.isinf(self.slope):
            self.x_intercept = point1[0]
        else:
            self.x_intercept = -self.y_intercept / self.slope

        self.color = constants.BLACK

    def print(self):
        print(self.point1, self.point2)

    def draw_debug(self, surface):
        pygame.draw.line(surface, self.color, self.point1, self.point2)


class Polygon:
    def __init__(self, point_list):
        self.segments = points_to_segment_list(point_list)

    def set_colors(self, colors_list):
        for index, color in enumerate(colors_list):
            self.segments[index].color = color


def points_to_segment_list(point_list):
    """Returns a list of segments from point 1 to point 2, point 2 to point 3
    all the way to point N to point 1.  All points are (x, y) pairs.
    Sending one or less points returns an empty list.  Sending two points
    returns a single segment between point 1 and point 2.
    """
    last_point = len(point_list) - 1
    if last_point <= 0:
        return []
    if last_point == 1:
        return [Segment(point_list[0], point_list[1])]

    segment_list = []
    for i in range(last_point):
        segment_list.append(Segment(point_list[i], point_list[i + 1]))
    segment_list.append(Segment(point_list[last_point], point_list[0]))

    return segment_list
