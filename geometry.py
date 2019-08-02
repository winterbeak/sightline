import pygame
import math

import constants

pygame.init()


def mod_angle(angle):
    while angle < -math.pi:
        angle += math.pi * 2

    while angle > math.pi:
        angle -= math.pi * 2

    return angle


def angle_to_slope(angle):
    return math.tan(angle)


def angle_between(from_position, to_position):
    delta_x = to_position[0] - from_position[0]
    delta_y = to_position[1] - from_position[1]
    return math.atan2(delta_y, delta_x)


def angles_close(angle1, angle2):
    absolute_difference = abs(angle1 - angle2)
    if absolute_difference < 0.001:
        return True
    elif abs(absolute_difference - math.pi * 2) < 0.001:
        return True

    return False


def closest_wall(position, level, angle):
    line = Line(position, angle_to_slope(angle))
    shortest_distance = 10000000.0
    closest = None

    for polygon in level.polygons:
        for segment in polygon.segments:
            intersection = line_segment_intersection(line, segment)
            if intersection:
                distance_between = distance(position, intersection)
                angle_check = angle_between(position, intersection)
                if distance_between < shortest_distance:
                    if angles_close(angle, angle_check):
                        shortest_distance = distance_between
                        closest = segment

    return closest


def min_and_max(num1, num2):
    """Returns a tuple, which is the (minimum, maximum) of the two numbers."""
    if num1 < num2:
        return num1, num2
    else:
        return num2, num1


def on_segment(point, segment, know_on_line=False):
    """Checks if a point is on a given segment.
    If the point is already known to be on the line of the segment (i.e. the
    point is on the line you get from stretching the segment infinitely), then
    you can skip some calculations by setting know_on_line to True.
    """
    if math.isinf(segment.slope):
        if know_on_line or math.isclose(segment.x_intercept, point[0]):
            min_y, max_y = min_and_max(segment.point1[1], segment.point2[1])

            if min_y < point[1] < max_y:
                return True

        return False

    if not know_on_line:
        check_y = segment.slope * point[0] + segment.y_intercept

        if not math.isclose(point[1], check_y):
            return False

    min_x, max_x = min_and_max(segment.point1[0], segment.point2[0])

    if min_x < point[0] < max_x:
        return True
    return False


def line_segment_intersection(line, segment):
    if math.isclose(line.slope, segment.slope):
        return None

    m1 = line.slope
    m2 = segment.slope
    b1 = line.y_intercept
    b2 = segment.y_intercept

    if math.isinf(line.slope):
        x = line.x_intercept
        y = m2 * x + b2

    elif math.isinf(segment.slope):
        x = segment.x_intercept
        y = m1 * x + b1

    else:
        x = (b2 - b1) / (m1 - m2)
        y = m1 * x + b1

    if on_segment((x, y), segment, True):
        return x, y

    return None


def poi(slope_1, y_intercept_1, slope_2, y_intercept_2):
    x = (y_intercept_2 - y_intercept_1) / (slope_1 - slope_2)
    y = slope_1 * x + y_intercept_1
    return x, y


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


class Line:
    def __init__(self, point, slope):
        self.slope = slope
        if math.isinf(slope):
            self.y_intercept = None
        else:
            self.y_intercept = point[1] - slope * point[0]
        if slope == 0.0:
            self.x_intercept = None
        else:
            self.x_intercept = -self.y_intercept / slope


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
