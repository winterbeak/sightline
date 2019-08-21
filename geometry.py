import pygame
import math
import os

import constants
import utility

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()


def mod_angle(angle):
    while angle < -math.pi:
        angle += math.pi * 2

    while angle > math.pi:
        angle -= math.pi * 2

    return angle


def angle_to_slope(angle):
    return math.tan(angle)


def slope_to_angle(slope):
    return math.atan(slope)


def angle_between(from_position, to_position):
    delta_x = to_position[0] - from_position[0]
    delta_y = to_position[1] - from_position[1]
    return math.atan2(delta_y, delta_x)


def angles_close(angle1, angle2, threshold=0.001):
    absolute_difference = abs(angle1 - angle2)
    if absolute_difference < threshold:
        return True
    elif abs(absolute_difference - math.pi * 2) < threshold:
        return True

    return False


def closest_wall(position, polygon, angle):
    """Returns the closest segment in polygon that collides with a ray.

    The ray starts at position and has an angle of angle (in radians).
    """
    line = Line(position, angle_to_slope(angle))
    shortest_distance = 10000000.0
    closest = None

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


def closest_wall_intersection(position, polygon, angle):
    """Returns the point of intersection of the closest segment in the polygon
    that collides with a ray.

    The ray starts at position and has an angle of angle (in radians).
    """
    line = Line(position, angle_to_slope(angle))
    shortest_distance = 10000000.0
    closest_intersection = None

    for segment in polygon.segments:
        intersection = line_segment_intersection(line, segment)
        if intersection:
            distance_between = distance(position, intersection)
            angle_check = angle_between(position, intersection)
            if distance_between < shortest_distance:
                if angles_close(angle, angle_check):
                    shortest_distance = distance_between
                    closest_intersection = intersection

    return closest_intersection


def closest_wall_level(position, level, angle):
    """Same as closest_wall, except using a level instead of a polygon."""
    line = Line(position, angle_to_slope(angle))
    shortest_distance = 10000000.0
    closest = None

    for polygon in level.collision:
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


def closest_wall_level_intersection(position, level, angle):
    """Same as closest_wall_intersection, except using a level instead
    of a polygon.
    """
    line = Line(position, angle_to_slope(angle))
    shortest_distance = 10000000.0
    closest_intersection = None

    for polygon in level.collision:
        for segment in polygon.segments:
            intersection = line_segment_intersection(line, segment)
            if intersection:
                distance_between = distance(position, intersection)
                angle_check = angle_between(position, intersection)
                if distance_between < shortest_distance:
                    if angles_close(angle, angle_check):
                        shortest_distance = distance_between
                        closest_intersection = intersection

    return closest_intersection


def level_wall_in_direction(position, level, angle):
    line = Line(position, angle_to_slope(angle))
    for polygon in level.collision:
        for segment in polygon.segments:
            intersection = line_segment_intersection(line, segment)
            if intersection:
                angle_check = angle_between(position, intersection)
                if angles_close(angle, angle_check):
                    return True

    return False


def component_in_direction(vector, direction):
    """Returns the magnitude of the component of a vector that points in
    the given direction.
    NOTE: sometimes is negative, which I take advantage of when
    calculating angular velocity
    vector is an (angle, magnitude) pair.
    """
    angle, magnitude = vector
    delta_angle = abs(direction - angle)
    return magnitude * math.cos(delta_angle)


def min_and_max(num1, num2):
    """Returns a tuple, which is the (minimum, maximum) of the two numbers."""
    if num1 < num2:
        return num1, num2
    else:
        return num2, num1


def on_segment(point, segment):
    """Checks if a point is on a given segment."""
    distance_1 = distance(point, segment.point1)
    distance_2 = distance(point, segment.point2)
    segment_length = distance(segment.point1, segment.point2)

    if abs(distance_1 + distance_2 - segment_length) < 0.0001:
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

    if on_segment((x, y), segment):
        return x, y

    return None


def poi(slope_1, y_intercept_1, slope_2, y_intercept_2):
    """Returns the point of intersection, given the properties of two lines."""
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


def points_to_vector(from_point, to_point):
    x1, y1 = from_point
    x2, y2 = to_point
    return difference_to_vector((x2 - x1, y2 - y1))


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

    def draw_debug(self, surface, offset=(0, 0)):
        if offset != (0, 0):
            point1 = utility.add_tuples(self.point1, offset)
            point2 = utility.add_tuples(self.point2, offset)
        else:
            point1 = self.point1
            point2 = self.point2
        pygame.draw.line(surface, self.color, point1, point2)


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
    def __init__(self, point_list, closed=True):
        self.point_list = tuple(point_list)
        self.segments = tuple(points_to_segment_list(point_list, closed))
        self.closed = closed
        self.color = constants.WHITE

    def set_colors(self, colors_list):
        for index, color in enumerate(colors_list):
            self.segments[index].color = color

    def draw_debug(self, surface, offset=(0, 0), color=None):
        if not color:
            color = self.color
        """Draws the polygon.  Does not come with an outline."""
        point_list = self.point_list
        if offset != (0, 0):
            point_list = tuple(utility.add_tuples(offset, point) for point in point_list)
        pygame.draw.polygon(surface, color, point_list)


def points_to_segment_list(point_list, closed=True):
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
    if closed:
        segment_list.append(Segment(point_list[last_point], point_list[0]))

    return segment_list


def regular_polygon(sides, radius, center_point, angle=0.0):
    """Returns a regular Polygon with a given amount of sign.

    radius is the distance from the center to any vertex.
    angle is the rotation of the shape, in radians.  At angle 0.0, the first
    point is drawn to the very right.
    """
    points = []
    for point in range(sides):
        point_angle = angle + point * (math.pi * 2 / sides)
        difference = vector_to_difference(point_angle, radius)

        position = utility.add_tuples(center_point, difference)
        position = utility.int_tuple(position)

        points.append(position)

    return Polygon(points)


def two_point_square(point1, point2, extend_upwards):
    """Returns a 4-sided regular Polygon, using two points as the base segment
    and extending.

    If extend_upwards is True, the square will extend in the direction
    of the most upwards angled side.  If False, it will extend downwards.

    If the points make a vertical line, left will be considered the most
    upwards side.
    """
    slope = two_point_slope(point1, point2)
    if math.isinf(slope):
        if extend_upwards:
            angle = math.pi
        else:
            angle = 0.0
    else:
        if extend_upwards:
            angle = slope_to_angle(slope) - math.pi / 2
        else:
            angle = slope_to_angle(slope) + math.pi / 2

    difference = vector_to_difference(angle, distance(point1, point2))
    point3 = utility.add_tuples(point2, difference)
    point4 = utility.add_tuples(point1, difference)
    point3 = utility.int_tuple(point3)
    point4 = utility.int_tuple(point4)

    return Polygon((point1, point2, point3, point4))


def segment_extended_intersection(segment_1, segment_2):
    """Returns the intersection of two segments, as if the segments were
    extended infinitely.
    Note that if there are infinite intersection points, or if there are
    no intersection points, the function will return None.
    """
    if math.isclose(segment_1.slope, segment_2.slope):
        return None

    m1 = segment_1.slope
    m2 = segment_2.slope
    b1 = segment_1.y_intercept
    b2 = segment_2.y_intercept

    if math.isinf(segment_1.slope):
        x = segment_1.x_intercept
        y = m2 * x + b2

    elif math.isinf(segment_2.slope):
        x = segment_2.x_intercept
        y = m1 * x + b1

    else:
        x = (b2 - b1) / (m1 - m2)
        y = m1 * x + b1
    return x, y


def segments_collide(segment_1, segment_2):
    intersection = segment_extended_intersection(segment_1, segment_2)
    if intersection:
        if on_segment(intersection, segment_1):
            if on_segment(intersection, segment_2):
                return True

    return False


def inverse(num):
    """Returns the inverse of a number.
    Interestingly, Python automatically handles 1.0 / inf.
    """
    if num == 0.0:
        return math.inf
    return 1.0 / num


def point_and_segment(point, segment):
    """Previously known as shortest_segment_between_point_and_segment().
    Returns the shortest line segment that would connect a given point and
    a given Segment.
    Returns None if the point is already on the segment.
    """
    if on_segment(point, segment):
        return None

    check_slope = -inverse(segment.slope)
    if math.isinf(check_slope):
        # generates a segment that is arbitrarily 10 unit long
        check_segment = Segment(point, (point[0], point[1] + 10))
    else:
        check_y_intercept = y_intercept(point, check_slope)
        check_segment = Segment(point, (0.0, check_y_intercept))

    intersection = segment_extended_intersection(check_segment, segment)
    if not intersection:
        return None

    if on_segment(intersection, segment):
        return Segment(intersection, point)

    else:
        distance1 = distance(point, segment.point1)
        distance2 = distance(point, segment.point2)
        if distance1 < distance2:
            return Segment(point, segment.point1)
        else:
            return Segment(point, segment.point2)


def point_in_polygon(point, polygon):
    total = 0
    line = Line(point, 1.0)
    angle = slope_to_angle(line.slope)
    for segment in polygon.segments:
        intersection = line_segment_intersection(line, segment)

        if intersection:
            check_angle = angle_between(point, intersection)
            if angles_close(angle, check_angle):
                total += 1

    if total % 2 == 0:
        return False
    return True


SCREEN_CORNERS = ((0, 0), (constants.SCREEN_WIDTH, 0),
                  (constants.SCREEN_WIDTH, constants.SCREEN_WIDTH),
                  (0, constants.SCREEN_WIDTH))
SCREEN_POLYGON = Polygon(SCREEN_CORNERS)


def farthest_wall_intersection(position, polygon, angle):
    """Returns the point of intersection of the farthest segment in the polygon
    that collides with a ray.

    The ray starts at position and has an angle of angle (in radians).
    """
    line = Line(position, angle_to_slope(angle))
    farthest_distance = 0.0
    farthest_intersection = None

    for segment in polygon.segments:
        intersection = line_segment_intersection(line, segment)
        if intersection:
            distance_between = distance(position, intersection)
            angle_check = angle_between(position, intersection)
            if distance_between > farthest_distance:
                if angles_close(angle, angle_check):
                    farthest_distance = distance_between
                    farthest_intersection = intersection

    return farthest_intersection


def screen_edge(point, angle, offset=(0, 0)):
    """Given a ray, this finds the farthest screen edge that the ray
    collides with.

    Can return None if the ray does not collide with any edge.
    """
    if offset != (0, 0):
        point = utility.add_tuples(point, offset)

    return farthest_wall_intersection(point, SCREEN_POLYGON, angle)
