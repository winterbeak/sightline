import pygame
import math

import utility
import geometry
import constants

pygame.init()


BLACK = constants.BLACK
WHITE = constants.WHITE
RED = constants.RED
GREEN = constants.GREEN
BLUE = constants.BLUE
CYAN = constants.CYAN
MAGENTA = constants.MAGENTA
YELLOW = constants.YELLOW
ORANGE = constants.ORANGE

LIGHT_GREY = constants.LIGHT_GREY
PALE_RED = constants.PALE_RED
PALE_GREEN = constants.PALE_GREEN
PALE_BLUE = constants.PALE_BLUE
PALE_CYAN = constants.PALE_CYAN
PALE_MAGENTA = constants.PALE_MAGENTA
PALE_YELLOW = constants.PALE_YELLOW
PALE_ORANGE = constants.PALE_ORANGE


class Level:
    WALL_DISTANCE = 6

    def __init__(self, collision, goals, start_position, start_orientation):
        self.start_position = start_position
        self.start_orientation = start_orientation

        # Viewable lines.  Does not correspond to what the player actual hits.
        self.collision = collision

        # Actual collision.  Extends outwards from the viewable lines
        # since getting too close to one is disorienting
        self.player_collision = []
        for polygon in collision:
            # One side is "inside" the polygon, the other is "outside".  Though
            # some polygons aren't closed, so there is no "inside" or "outside",
            # only two sides.
            segments_side_1 = []
            segments_side_2 = []
            for segment in polygon.segments:
                segment_angle = geometry.angle_between(segment.point1, segment.point2)
                angle_1 = segment_angle + math.pi / 2
                angle_2 = segment_angle - math.pi / 2

                # Distance of 5 or lower causes player to get stuck on
                # some walls, due to how collision works.  6 is fine.
                difference_1 = geometry.vector_to_difference(angle_1, self.WALL_DISTANCE)
                difference_2 = geometry.vector_to_difference(angle_2, self.WALL_DISTANCE)

                point_1 = utility.add_tuples(segment.point1, difference_1)
                point_2 = utility.add_tuples(segment.point2, difference_1)
                segments_side_1.append(geometry.Segment(point_1, point_2))

                point_1 = utility.add_tuples(segment.point1, difference_2)
                point_2 = utility.add_tuples(segment.point2, difference_2)
                segments_side_2.append(geometry.Segment(point_1, point_2))

            # Non-closed polygons are capped off with a sharp edge.
            if polygon.closed:
                # Side 1
                point_list = []
                for index in range(len(segments_side_1)):
                    segment_1 = segments_side_1[index]
                    segment_2 = segments_side_1[index - 1]
                    point = geometry.segment_extended_intersection(segment_1, segment_2)

                    if point:
                        point_list.append(point)

                segment_list = geometry.points_to_segment_list(point_list)
                self.player_collision.extend(segment_list)

                # Side 2
                point_list = []
                for index in range(len(segments_side_2)):
                    segment_1 = segments_side_2[index]
                    segment_2 = segments_side_2[index - 1]
                    point = geometry.segment_extended_intersection(segment_1, segment_2)

                    if point:
                        point_list.append(point)

                segment_list = geometry.points_to_segment_list(point_list)
                self.player_collision.extend(segment_list)

            else:
                # Side 1
                point_list = [segments_side_1[0].point1]
                for index in range(1, len(segments_side_1)):
                    segment_1 = segments_side_1[index]
                    segment_2 = segments_side_1[index - 1]
                    point = geometry.segment_extended_intersection(segment_1, segment_2)

                    if point:
                        point_list.append(point)
                point_list.append(segments_side_1[-1].point2)

                segment_list = geometry.points_to_segment_list(point_list, False)
                self.player_collision.extend(segment_list)

                # Cap 1
                point_1 = polygon.point_list[1]
                point_2 = polygon.point_list[0]
                cap = self.create_cap(point_1, point_2)
                self.player_collision.extend(cap)

                # Side 2
                point_list = [segments_side_2[0].point1]
                for index in range(1, len(segments_side_2)):
                    segment_1 = segments_side_2[index]
                    segment_2 = segments_side_2[index - 1]
                    point = geometry.segment_extended_intersection(segment_1, segment_2)

                    if point:
                        point_list.append(point)
                point_list.append(segments_side_2[-1].point2)

                segment_list = geometry.points_to_segment_list(point_list, False)
                self.player_collision.extend(segment_list)

                # Cap 2
                point_1 = polygon.point_list[-2]
                point_2 = polygon.point_list[-1]
                cap = self.create_cap(point_1, point_2)
                self.player_collision.extend(cap)

        # Viewable lines.  These are sorted by color so that, when they are
        # drawn, the way they overlap at corners is consistent
        segment_list = []
        for polygon in collision:
            for segment in polygon.segments:
                segment_list.append(segment)
        self.segment_list = sorted(segment_list, key=geometry.segment_priority)

        self.goals = goals
        self.goal_count = len(goals)

    def draw_debug_goals(self, surface, offset=(0, 0), alpha=255):
        for polygon in self.goals:
            if alpha != 255:
                red = 255 - (255 - polygon.color[0]) * (alpha / 255)
                green = 255 - (255 - polygon.color[1]) * (alpha / 255)
                blue = 255 - (255 - polygon.color[2]) * (alpha / 255)
                polygon.draw_debug(surface, offset, (red, green, blue))
            else:
                polygon.draw_debug(surface, offset)

    def draw_debug_outline(self, surface, offset=(0, 0)):
        for segment in self.segment_list:
            segment.draw_debug(surface, offset)

    def set_goal_colors(self, colors_list):
        for index, color in enumerate(colors_list):
            self.goals[index].color = color

    def create_cap(self, point_1, point_2):
        """Creates the sharp end of the collision of a line segment.

        The cap will be created on the end of point_2.
        """
        angle_2 = geometry.angle_between(point_1, point_2)
        angle_1 = angle_2 - math.pi / 2
        angle_3 = angle_2 + math.pi / 2
        angles = (angle_1, angle_2, angle_3)

        point_list = []
        for angle in angles:
            difference = geometry.vector_to_difference(angle, self.WALL_DISTANCE)
            point = utility.add_tuples(point_2, difference)
            point_list.append(point)

        segment_list = geometry.points_to_segment_list(point_list, False)
        return segment_list


# Note: these level numbers are in order of creation, not in order of appearance
# Level 0: Plus
def generate_plus_level():
    collision_1 = geometry.Polygon(((200, 300), (100, 300), (100, 200), (200, 200),  # left arm
                                    (200, 100), (300, 100), (300, 200),  # top arm
                                    (400, 200), (400, 300), (300, 300),  # right arm
                                    (300, 400), (200, 400)))  # bottom arm
    collision_1.set_colors((GREEN, BLUE, GREEN, GREEN, ORANGE, GREEN,
                            GREEN, MAGENTA, GREEN, GREEN, RED, GREEN))

    collisions = (collision_1,)

    goal_1 = geometry.Polygon(((200, 300), (100, 300), (100, 200), (200, 200)))  # left goal
    goal_2 = geometry.Polygon(((200, 200), (200, 100), (300, 100), (300, 200)))  # top goal
    goal_3 = geometry.Polygon(((300, 200), (400, 200), (400, 300), (300, 300)))  # right goal
    goal_4 = geometry.Polygon(((300, 300), (300, 400), (200, 400), (200, 300)))  # bottom goal

    goals = (goal_1, goal_2, goal_3, goal_4)

    level = Level(collisions, goals, (250, 250), -math.pi / 2)
    level.set_goal_colors((PALE_BLUE, PALE_ORANGE, PALE_MAGENTA, PALE_RED))

    return level


# Level 1: Two spikes
def generate_jesters_hat_level():
    collision_1 = geometry.Polygon(((100, 125), (250, 225), (400, 125),  # indentation
                                    (400, 325), (100, 325)))  # bottom
    collision_1.set_colors((CYAN, MAGENTA, ORANGE, ORANGE, ORANGE))

    collisions = (collision_1, )

    goal_1 = geometry.Polygon(((100, 125), (250, 225), (100, 225)))  # left
    goal_2 = geometry.Polygon(((400, 125), (250, 225), (400, 225)))  # right
    goal_3 = geometry.Polygon(((100, 225), (400, 225), (400, 325), (100, 325)))  # bottom

    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (250, 275), math.pi / 2)
    level.set_goal_colors((PALE_CYAN, PALE_MAGENTA, PALE_ORANGE))

    return level


# Level 2: Outside of a triangle
def generate_triangle_level():
    collision_1 = geometry.Polygon(((250, 150), (175, 280), (325, 280)))
    collision_1.set_colors((MAGENTA, YELLOW, RED))

    collisions = (collision_1, )

    goal_1 = geometry.Polygon(((250, 150), (175, 280), (48, 205), (122, 77)))
    goal_2 = geometry.Polygon(((250, 150), (325, 280), (452, 205), (378, 77)))
    goal_3 = geometry.Polygon(((325, 280), (175, 280), (175, 430), (325, 430)))

    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (457, 100), math.pi / 4 * 3)
    level.set_goal_colors((PALE_MAGENTA, PALE_RED, PALE_YELLOW))

    return level


# Level 3: Three boxes
def generate_three_boxes_level():
    collision_1 = geometry.Polygon(((50, 50), (50, 400), (450, 400)), False)  # Right angle
    collision_1.set_colors((YELLOW, RED))
    collision_2 = geometry.Polygon(((140, 175), (190, 175), (190, 225), (140, 225)))  # Left box
    collision_2.set_colors((CYAN, MAGENTA, CYAN, MAGENTA))
    collision_3 = geometry.Polygon(((225, 175), (275, 175), (275, 225), (225, 225)))  # Middle box
    collision_3.set_colors((CYAN, MAGENTA, CYAN, MAGENTA))
    collision_4 = geometry.Polygon(((310, 175), (360, 175), (360, 225), (310, 225)))  # Right box
    collision_4.set_colors((CYAN, MAGENTA, CYAN, MAGENTA))

    collisions = (collision_1, collision_2, collision_3, collision_4)

    goal_1 = geometry.Polygon(((50, 175), (100, 175), (100, 225), (50, 225)))  # Left goal
    goal_2 = geometry.Polygon(((225, 350), (275, 350), (275, 400), (225, 400)))  # Bottom goal

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (250, 312), -math.pi / 2)
    level.set_goal_colors((PALE_MAGENTA, PALE_CYAN))

    return level


# Level 4: Single line
def generate_single_line_level():
    collision_1 = geometry.Polygon(((200, 200), (300, 300)), False)
    collision_1.set_colors((GREEN, ))

    collisions = (collision_1, )

    goal_1 = geometry.Polygon(((200, 200), (300, 300), (350, 250), (250, 150)))  # Top right goal
    goal_2 = geometry.Polygon(((200, 200), (300, 300), (250, 350), (150, 250)))  # Bottom left goal

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (120, 350), -math.pi / 2)
    level.set_goal_colors((PALE_YELLOW, PALE_GREEN))

    return level


# Level 5: Box in a box
def generate_boxception_level():
    collision_1 = geometry.Polygon(((100, 100), (400, 100), (400, 400), (100, 400)))
    collision_1.set_colors((CYAN, CYAN, RED, RED))
    collision_2 = geometry.Polygon(((225, 225), (275, 225), (275, 275), (225, 275)))
    collision_2.set_colors((RED, CYAN, CYAN, RED))

    collisions = (collision_1, collision_2)

    goal_1 = geometry.Polygon(((100, 100), (400, 100), (275, 225), (225, 225)))
    goal_2 = geometry.Polygon(((400, 400), (100, 400), (225, 275), (275, 275)))

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (300, 300), math.pi / 5)
    level.set_goal_colors((PALE_CYAN, PALE_RED))

    return level


# Level 6: Five lines
def generate_pentagon_level():
    collision_1 = geometry.Polygon(((199, 133), (149, 169)), False)  # Top left
    collision_1.set_colors((ORANGE, ))
    collision_2 = geometry.Polygon(((301, 133), (351, 169)), False)  # Top right
    collision_2.set_colors((ORANGE, ))
    collision_3 = geometry.Polygon(((383, 266), (363, 325)), False)  # Bottom right
    collision_3.set_colors((ORANGE, ))
    collision_4 = geometry.Polygon(((281, 386), (219, 386)), False)  # Bottom
    collision_4.set_colors((ORANGE, ))
    collision_5 = geometry.Polygon(((117, 266), (137, 325)), False)  # Bottom left
    collision_5.set_colors((ORANGE, ))

    collisions = (collision_1, collision_2, collision_3, collision_4, collision_5)

    goal_1 = geometry.regular_polygon(5, 24, (250, 250), -math.pi / 2)

    goals = (goal_1, )

    level = Level(collisions, goals, (39, 404), -math.pi / 3)
    level.set_goal_colors((PALE_ORANGE, ))

    return level


# Level 7: Two buckets
def generate_buckets_level():
    collision_1 = geometry.Polygon(((160, 160), (160, 340), (340, 340), (340, 160)), False)  # outside
    collision_1.set_colors((RED, GREEN, BLUE))
    collision_2 = geometry.Polygon(((220, 220), (220, 280), (280, 280), (280, 220)), False)  # inside
    collision_2.set_colors((RED, GREEN, BLUE))

    collisions = (collision_1, collision_2)

    goal_1 = geometry.two_point_square((220, 220), (280, 220), False)  # Center
    goal_2 = geometry.two_point_square((160, 160), (220, 160), False)  # Top left
    goal_3 = geometry.two_point_square((280, 160), (340, 160), False)  # Top right
    goal_4 = geometry.two_point_square((160, 280), (220, 280), False)  # Bottom left
    goal_5 = geometry.two_point_square((280, 280), (340, 280), False)  # Bottom right
    goals = (goal_1, goal_2, goal_3, goal_4, goal_5)

    level = Level(collisions, goals, (357, 137), math.pi / 3 * 2)
    level.set_goal_colors((PALE_GREEN, PALE_RED, PALE_BLUE, PALE_CYAN, PALE_MAGENTA))

    return level


# Level 8: Two lines
def generate_two_lines_level():
    collision_1 = geometry.Polygon(((200, 200), (400, 200)), False)  # top
    collision_1.set_colors((CYAN, ))
    collision_2 = geometry.Polygon(((100, 300), (300, 300)), False)  # bottom
    collision_2.set_colors((YELLOW, ))

    collisions = (collision_1, collision_2)

    goal_1 = geometry.Polygon(((200, 200), (200, 300), (300, 300), (300, 200)))  # Center
    goal_2 = geometry.Polygon(((300, 100), (400, 100), (400, 200), (300, 200)))  # Top right
    goal_3 = geometry.Polygon(((100, 300), (200, 300), (200, 400), (100, 400)))  # Bottom left
    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (65, 357), -math.pi / 3)
    level.set_goal_colors((PALE_ORANGE, PALE_CYAN, PALE_YELLOW))

    return level


# Level 9: Barrier/Wings
def generate_wings_level():
    collision_1 = geometry.Polygon(((113, 275), (200, 225), (300, 225), (387, 275)), False)
    collision_1.set_colors((MAGENTA, CYAN, MAGENTA))

    collisions = (collision_1, )

    goal_1 = geometry.two_point_square((200, 225), (300, 225), False)  # Bottom
    goal_2 = geometry.two_point_square((113, 275), (200, 225), True)  # Top left
    goal_3 = geometry.two_point_square((300, 225), (387, 275), True)  # Top right

    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (50, 250), 0.0)
    level.set_goal_colors((PALE_CYAN, PALE_MAGENTA, PALE_YELLOW))

    return level


# Level 10: Hexagon
def generate_hexagon_level():
    collision_1 = geometry.Polygon(((250, 108), (374, 179), (374, 321),
                                    (250, 392), (127, 321), (127, 179)))  # Hexagon
    collision_1.set_colors((RED, MAGENTA, RED, RED, MAGENTA, RED))
    collision_2 = geometry.Polygon(((250, 250), (250, 199)), False)  # Up
    collision_2.set_colors((ORANGE, ))
    collision_3 = geometry.Polygon(((250, 250), (205, 276)), False)  # Bottom left
    collision_3.set_colors((ORANGE, ))
    collision_4 = geometry.Polygon(((250, 250), (295, 276)), False)  # Bottom right
    collision_4.set_colors((ORANGE, ))

    collisions = (collision_1, collision_2, collision_3, collision_4)

    goal_1 = geometry.Polygon(((250, 250), (250, 199), (205, 225), (205, 276)))  # Top left
    goal_2 = geometry.Polygon(((250, 250), (250, 199), (295, 225), (295, 276)))  # Top right

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (240, 275), math.pi)
    level.set_goal_colors((PALE_ORANGE, PALE_MAGENTA))

    return level


# Level 11A: Elbow
def generate_elbow_level():
    collision_1 = geometry.Polygon(((200, 200), (300, 200), (200, 300)), False)
    collision_1.set_colors((CYAN, CYAN))

    collisions = (collision_1, )

    goal_1 = geometry.Polygon(((200, 200), (300, 200), (200, 300)))  # Inside
    goal_2 = geometry.Polygon(((200, 200), (250, 200), (250, 150), (200, 150)))  # Top

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (400, 50), math.pi / 4 * 3)
    level.set_goal_colors((PALE_CYAN, PALE_ORANGE))

    return level


# Level 11B: Square
def generate_square_level():
    collision_1 = geometry.Polygon(((200, 300), (200, 200),
                                    (300, 200), (300, 300)), False)
    collision_1.set_colors((CYAN, CYAN, CYAN))

    collisions = (collision_1, )

    goal_1 = geometry.Polygon(((200, 300), (200, 200), (300, 200), (300, 300)))  # Inside
    goal_2 = geometry.Polygon(((100, 200), (200, 200), (200, 300), (100, 300)))  # Left
    goal_3 = geometry.Polygon(((300, 200), (400, 200), (400, 300), (300, 300)))  # Right

    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (400, 50), math.pi / 4 * 3)
    level.set_goal_colors((PALE_CYAN, PALE_BLUE, PALE_YELLOW))

    return level


# Level 12: Grid
def generate_grid_level():
    margin = 50
    spacing = 400 / 11
    collision = []

    # horizontal lines
    for row in range(4):
        for column in range(3):
            x1 = int(spacing * column * 3 + spacing * 2) + margin
            x2 = x1 + int(spacing)
            y = int(spacing * row * 3 + spacing) + margin
            collision.append(geometry.Polygon(((x1, y), (x2, y)), False))

    collision.pop(-2)  # removal of middle-bottom line

    # vertical lines
    for column in range(4):
        for row in range(3):
            x = int(spacing * column * 3 + spacing) + margin
            y1 = int(spacing * row * 3 + spacing * 2) + margin
            y2 = y1 + int(spacing)
            collision.append(geometry.Polygon(((x, y1), (x, y2)), False))

    for polygon in collision:
        polygon.set_colors((RED, ))

    # bottom middle
    x1 = int(spacing * 4 + margin)
    y1 = int(spacing * 7 + margin)
    x2 = x1 + int(spacing * 3)
    y2 = y1 + int(spacing * 3)

    goal_1 = geometry.Polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2)))

    # middle left
    x1 = int(spacing + margin)
    y1 = int(spacing * 4 + margin)
    x2 = x1 + int(spacing * 3)
    y2 = y1 + int(spacing * 3)

    goal_2 = geometry.Polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2)))

    # top right
    x1 = int(spacing * 7 + margin)
    y1 = int(spacing + margin)
    x2 = x1 + int(spacing * 3)
    y2 = y1 + int(spacing * 3)

    goal_3 = geometry.Polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2)))

    goals = (goal_1, goal_2, goal_3)

    level = Level(collision, goals, (250, 250), math.pi)
    level.set_goal_colors((PALE_RED, PALE_CYAN, PALE_ORANGE))

    return level


# Level 13: Warning sign/keyhole
def generate_keyhole_level():
    collision_1 = geometry.Polygon(((131, 100), (390, 250), (131, 400)))  # Triangle
    collision_1.set_colors((GREEN, GREEN, GREEN))
    collision_2 = geometry.Polygon(((203, 239), (260, 239), (260, 260), (203, 260)))  # Rectangle
    collision_2.set_colors((CYAN, CYAN, CYAN, CYAN))

    collisions = (collision_1, collision_2)

    goal_1 = geometry.Polygon(((390, 250), (341, 222), (341, 278)))  # Right corner
    goal_2 = geometry.Polygon(((203, 239), (203, 260), (182, 260), (182, 239)))  # Left of rectangle
    goal_3 = geometry.Polygon(((203, 239), (260, 239), (260, 218), (203, 218)))  # Top of rectangle

    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (150, 150), math.pi / 4)
    level.set_goal_colors((PALE_GREEN, PALE_CYAN, PALE_YELLOW))

    return level


# Level 14: H
def generate_h_level():
    collision_1 = geometry.Polygon(((100, 100), (200, 100), (200, 200),  # Starts with top left horizontal,
                                    (300, 200), (300, 100), (400, 100),  # travels clockwise
                                    (400, 200), (400, 300), (400, 400),  # Bottom right
                                    (300, 400), (300, 300), (200, 300),
                                    (200, 400), (100, 400), (100, 300),
                                    (100, 200)))
    collision_1.set_colors((YELLOW,
                            GREEN, GREEN, GREEN,  # Bucket at top of the H
                            YELLOW, GREEN, YELLOW, GREEN, YELLOW,
                            GREEN, GREEN, GREEN,  # Bucket at bottom of the H
                            YELLOW, GREEN, YELLOW, GREEN))

    collisions = (collision_1, )

    goal_1 = geometry.Polygon(((100, 200), (200, 200), (200, 300), (100, 300)))  # Left
    goal_2 = geometry.Polygon(((300, 200), (400, 200), (400, 300), (300, 300)))  # Right

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (350, 250), math.pi)
    level.set_goal_colors((PALE_GREEN, PALE_YELLOW))

    return level


# Level 15: Perspective Pegs
def generate_pegs_level():
    collision = []
    points = geometry.regular_polygon(5, 150, (250, 250), -math.pi / 2)
    for point in points.point_list:
        collision.append(geometry.regular_polygon(5, 50, point, math.pi / 2))
    collision[0].set_colors((GREEN, RED, BLUE, YELLOW, MAGENTA))
    collision[1].set_colors((GREEN, RED, BLUE, YELLOW, MAGENTA))
    collision[2].set_colors((BLUE, YELLOW, MAGENTA, GREEN, RED))
    collision[3].set_colors((MAGENTA, GREEN, RED, BLUE, YELLOW))
    collision[4].set_colors((RED, BLUE, YELLOW, MAGENTA, GREEN))

    segment = collision[0].segments[4]
    goal_1 = geometry.two_point_square(segment.point1, segment.point2, False)
    segment = collision[3].segments[2]
    goal_2 = geometry.two_point_square(segment.point1, segment.point2, True)
    segment = collision[2].segments[3]
    goal_3 = geometry.two_point_square(segment.point1, segment.point2, True)

    goals = (goal_1, goal_2, goal_3)

    level = Level(collision, goals, (317, 439), -math.pi / 4 * 3)
    level.set_goal_colors((PALE_MAGENTA, PALE_RED, PALE_GREEN))

    return level


# Level 16: Reticles
def generate_reticles_level():
    # Crosshairs
    center_x = 150
    center_y = 150
    center_radius = 50
    outer_radius = 100

    collision_1 = geometry.Polygon(((center_x - center_radius, center_y),
                                    (center_x - outer_radius, center_y)),
                                   False)  # Left

    collision_2 = geometry.Polygon(((center_x + center_radius, center_y),
                                    (center_x + outer_radius, center_y)),
                                   False)  # Right

    collision_3 = geometry.Polygon(((center_x, center_y - center_radius),
                                    (center_x, center_y - outer_radius)),
                                   False)  # Up

    collision_4 = geometry.Polygon(((center_x, center_y + center_radius),
                                    (center_x, center_y + outer_radius)),
                                   False)  # Down

    # Boxhairs
    size = 100
    quarter = size // 4
    x1 = 250
    y1 = 250
    x2 = x1 + size
    y2 = y1 + size
    collision_5 = geometry.Polygon(((x1, y1 + quarter), (x1, y2 - quarter)), False)  # Left
    collision_6 = geometry.Polygon(((x2, y1 + quarter), (x2, y2 - quarter)), False)  # Right
    collision_7 = geometry.Polygon(((x1 + quarter, y1), (x2 - quarter, y1)), False)  # Up
    collision_8 = geometry.Polygon(((x1 + quarter, y2), (x2 - quarter, y2)), False)  # Down

    collisions = (collision_1, collision_2, collision_3, collision_4,
                  collision_5, collision_6, collision_7, collision_8)

    for collision in collisions:
        collision.set_colors((BLUE, ))

    goal_1 = geometry.two_point_square((center_x - quarter, center_y - quarter),  # Crosshair center
                                       (center_x + quarter, center_y - quarter), False)
    goal_2 = geometry.two_point_square((x1, y1 + quarter), (x1, y2 - quarter), True)  # Boxhairs left
    goal_3 = geometry.two_point_square((x1 + quarter, y1), (x2 - quarter, y1), True)  # Boxhairs up

    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (400, 400), math.pi)
    level.set_goal_colors((PALE_BLUE, PALE_CYAN, PALE_GREEN))

    return level


# Level 17: Missing corner
def generate_missing_corner_level():
    collision_1 = geometry.two_point_square((100, 100), (150, 100), False)  # Top left
    collision_1.set_colors((GREEN, GREEN, GREEN, GREEN))
    collision_2 = geometry.two_point_square((100, 350), (150, 350), False)  # Bottom left
    collision_2.set_colors((GREEN, GREEN, GREEN, GREEN))
    collision_3 = geometry.two_point_square((350, 350), (400, 350), False)  # Bottom right
    collision_3.set_colors((GREEN, GREEN, GREEN, GREEN))

    collisions = (collision_1, collision_2, collision_3)

    goal_1 = geometry.two_point_square((350, 350), (300, 350), False)  # Left
    goal_2 = geometry.two_point_square((350, 300), (400, 300), False)  # Top

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (53, 86), math.pi / 5)
    level.set_goal_colors((PALE_GREEN, PALE_CYAN))

    return level


# Level 18: Z
def generate_z_level():
    collision_1 = geometry.Polygon(((200, 200), (300, 200), (200, 300), (250, 300)), False)
    collision_1.set_colors((MAGENTA, ORANGE, MAGENTA))

    collisions = (collision_1, )

    goal_1 = geometry.Polygon(((200, 300), (250, 300), (250, 250)))
    goal_2 = geometry.two_point_square((250, 200), (300, 200), True)

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (389, 243), math.pi + 0.3)
    level.set_goal_colors((PALE_ORANGE, PALE_MAGENTA))

    return level


# Level 19: Increasing
def generate_increasing_level():
    collisions = []

    for line in range(5):
        x = line * 50 + 150
        y1 = line * 20 + 300
        y2 = 200 - line * 20

        polygon = geometry.Polygon(((x, y1), (x, y2)), False)
        polygon.set_colors((ORANGE, ))
        collisions.append(polygon)

    collisions = tuple(collisions)

    goal_1 = geometry.two_point_square((200, 225), (250, 225), False)
    goal_2 = geometry.two_point_square((300, 225), (350, 225), False)

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (345, 412), -math.pi / 3 * 2)
    level.set_goal_colors((PALE_MAGENTA, PALE_CYAN))

    return level


# Level 20: Star
def generate_star_level():
    triangle = geometry.regular_polygon(3, 50, (250, 200), -math.pi / 2)
    near_points = triangle.point_list
    far_points = []

    for index, segment in enumerate(triangle.segments):
        middle_x = int((segment.point1[0] + segment.point2[0]) / 2)
        middle_y = int((segment.point1[1] + segment.point2[1]) / 2)

        segment_angle = geometry.angle_between(segment.point1, segment.point2)
        perpendicular_angle = segment_angle - math.pi / 2

        difference = geometry.vector_to_difference(perpendicular_angle, index * 50 + 100)
        far_points.append(utility.add_tuples((middle_x, middle_y), difference))

    point_list = []
    for index in range(3):
        point_list.append(near_points[index])
        point_list.append(far_points[index])

    collision_1 = geometry.Polygon(point_list)
    collision_1.set_colors((GREEN, MAGENTA, GREEN, MAGENTA, GREEN, MAGENTA))

    collisions = (collision_1, )

    # Goal 1 (Between bottom and left spike)
    # The corner itself
    point_1 = near_points[2]

    # The point on the green wall
    angle_2 = geometry.angle_between(point_1, far_points[2])
    difference_2 = geometry.vector_to_difference(angle_2, 50)
    point_2 = utility.add_tuples(point_1, difference_2)

    # The point on the magenta wall
    angle_4 = geometry.angle_between(point_1, far_points[1])
    difference_4 = geometry.vector_to_difference(angle_4, 50)
    point_4 = utility.add_tuples(point_1, difference_4)

    # The point not touching any walls
    angle_3 = (angle_2 + angle_4) / 2
    difference_3 = geometry.vector_to_difference(angle_3 - math.pi, 50)
    point_3 = utility.add_tuples(point_1, difference_3)

    goal_1 = geometry.Polygon((point_1, point_2, point_3, point_4))

    # Goal 2 (Top of right spike)
    point_1 = far_points[0]

    angle_2 = geometry.angle_between(point_1, near_points[0])
    difference_2 = geometry.vector_to_difference(angle_2, 50)
    point_2 = utility.add_tuples(point_1, difference_2)

    goal_2 = geometry.two_point_square(point_1, point_2, True)

    # Goal 3 (Bottom of right spike)
    point_1 = far_points[0]

    angle_2 = geometry.angle_between(point_1, near_points[1])
    difference_2 = geometry.vector_to_difference(angle_2, 50)
    point_2 = utility.add_tuples(point_1, difference_2)

    goal_3 = geometry.two_point_square(point_1, point_2, False)

    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (300, 400), -math.pi / 2)
    level.set_goal_colors((PALE_MAGENTA, PALE_GREEN, PALE_CYAN))

    return level


# Level 21: Spiral
def generate_spiral_level():
    colors = []
    points = [(250, 250)]

    for point in range(10):
        angle = math.pi * 2 / 5 * point + 0.6
        angle = geometry.mod_angle(angle)
        magnitude = point * 20 + 20

        difference = geometry.vector_to_difference(angle, magnitude)

        points.append(utility.add_tuples((250, 250), difference))

        if point % 2 == 0:
            colors.append(RED)
        else:
            colors.append(BLUE)

    collision_1 = geometry.Polygon(points, False)
    collision_1.set_colors(colors)

    collisions = (collision_1, )

    # Goal 1: Inside-most
    segments = collision_1.segments

    point_1 = geometry.segment_extended_intersection(segments[0], segments[3])
    goal_1 = geometry.Polygon(collision_1.point_list[1:4] + (point_1, ))

    # Goal 2: Slightly more outside than goal 1
    slope = segments[7].slope
    y_intercept = segments[7].y_intercept - 60

    point_1 = geometry.poi(segments[6].slope, segments[6].y_intercept, slope, y_intercept)
    point_2 = geometry.poi(segments[8].slope, segments[8].y_intercept, slope, y_intercept)

    goal_2 = geometry.Polygon((point_1, point_2, segments[7].point2, segments[7].point1))

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (200, 300), -math.pi / 7 * 3)
    level.set_goal_colors((PALE_RED, PALE_BLUE))

    return level


# Level 22: Diamond
def generate_diamond_level():
    collision_1 = geometry.Polygon(((325, 250), (325, 325), (250, 325)), False)  # Bottom right
    collision_1.set_colors((YELLOW, YELLOW))
    collision_2 = geometry.Polygon(((150, 250), (150, 200), (200, 150), (250, 150)), False)  # Top left
    collision_2.set_colors((YELLOW, YELLOW, YELLOW))

    collisions = (collision_1, collision_2)

    goal_1 = geometry.two_point_square((275, 275), (325, 275), False)
    goal_2 = geometry.two_point_square((150, 250), (150, 200), True)
    goal_3 = geometry.two_point_square((200, 150), (250, 150), True)

    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (250, 250), math.pi)
    level.set_goal_colors((PALE_CYAN, PALE_GREEN, PALE_YELLOW))

    return level


# Level 23A: Positioning
def generate_positioning_level():
    collision_1 = geometry.Polygon(((100, 100), (325, 100), (400, 100)), False)  # Top horizontal
    collision_1.set_colors((MAGENTA, GREEN))
    collision_2 = geometry.Polygon(((270, 100), (270, 250)), False)  # Middle vertical
    collision_2.set_colors((MAGENTA, ))
    collision_3 = geometry.Polygon(((100, 350), (400, 350)), False)  # Bottom horizontal
    collision_3.set_colors((MAGENTA, ))

    collision_4 = geometry.Polygon(((175, 100), (175, 150)), False)  # Left vertical
    collision_4.set_colors((YELLOW, ))

    collisions = (collision_1, collision_2, collision_3, collision_4)

    goal_1 = geometry.two_point_square((155, 150), (195, 150), False)  # Top left
    goal_2 = geometry.two_point_square((230, 150), (270, 150), False)  # Top middle
    goal_3 = geometry.two_point_square((230, 310), (270, 310), False)  # Bottom middle
    goal_4 = geometry.two_point_square((305, 310), (345, 310), False)  # Bottom right

    goals = (goal_1, goal_2, goal_3, goal_4)

    level = Level(collisions, goals, (250, 20), math.pi / 2)
    level.set_goal_colors((PALE_YELLOW, PALE_CYAN, PALE_MAGENTA, PALE_RED))

    return level


# Level 23B: Alignment
def generate_alignment_level():
    collision_1 = geometry.Polygon(((250, 150), (250, 200)), False)  # Middle vertical
    collision_2 = geometry.Polygon(((150, 250), (200, 250)), False)  # Middle horizontal
    collision_3 = geometry.Polygon(((50, 350), (100, 350)), False)  # Bottom left
    collision_4 = geometry.Polygon(((350, 50), (350, 100)), False)  # Top right

    collisions = (collision_1, collision_2, collision_3, collision_4)
    for collision in collisions:
        collision.set_colors((MAGENTA, ))

    goal_1 = geometry.two_point_square((225, 225), (275, 225), False)  # Middle
    goal_2 = geometry.two_point_square((225, 325), (275, 325), False)  # Bottom
    goal_3 = geometry.two_point_square((325, 225), (375, 225), False)  # Right

    goals = (goal_1, goal_2, goal_3)

    level = Level(collisions, goals, (250, 20), math.pi / 2)
    level.set_goal_colors((PALE_MAGENTA, PALE_YELLOW, PALE_RED))

    return level


# Level 24: Staircase
def generate_staircase_level():
    collision_1 = geometry.Polygon(((100, 100), (200, 100), (200, 200),
                                    (300, 200), (300, 300), (400, 300),
                                    (400, 400)), False)
    collision_1.set_colors((ORANGE, BLUE, ORANGE, BLUE, ORANGE, BLUE))

    collisions = (collision_1, )

    goal_1 = geometry.two_point_square((100, 300), (200, 300), False)
    goal_2 = geometry.two_point_square((300, 100), (400, 100), False)

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (258, 367), -math.pi / 2)
    level.set_goal_colors((PALE_BLUE, PALE_ORANGE))

    return level


# Level 25: Heart
def generate_heart_level():
    collision_1 = geometry.Polygon(((50, 200), (150, 100), (250, 200),
                                    (350, 100), (450, 200), (250, 400)))
    collision_1.set_colors((MAGENTA, RED, MAGENTA, RED, MAGENTA, RED))

    collisions = (collision_1, )

    goal_1 = geometry.Polygon(((150, 250), (200, 200), (250, 250), (250, 350)))  # Left
    goal_2 = geometry.Polygon(((350, 250), (300, 200), (250, 250), (250, 350)))  # Right

    goals = (goal_1, goal_2)

    level = Level(collisions, goals, (328, 173), -math.pi / 2)
    level.set_goal_colors((PALE_MAGENTA, PALE_RED))

    return level


# Level 26: Cube
def generate_cube_level():
    hexagon = geometry.regular_polygon(6, 150, (250, 250), -math.pi / 2)
    points = hexagon.point_list

    collisions = []
    goals = []
    for index in range(0, 5, 2):
        # Elbow
        angle_1 = geometry.angle_between(points[index], points[index - 1])
        angle_2 = geometry.angle_between(points[index], points[index + 1])
        difference_1 = geometry.vector_to_difference(angle_1, 100)
        difference_2 = geometry.vector_to_difference(angle_2, 100)

        point_1 = utility.add_tuples(points[index], difference_1)
        point_3 = utility.add_tuples(points[index], difference_2)

        collisions.append(geometry.Polygon((point_1, points[index], point_3), False))

        # Thing sticking out of elbow
        angle = geometry.angle_between(points[index], (250, 250))
        difference = geometry.vector_to_difference(angle, 80)

        point = utility.add_tuples(points[index], difference)

        collisions.append(geometry.Polygon((point, points[index]), False))

        # Goal
        angle_1 = angle + math.pi / 2
        angle_2 = angle - math.pi / 2
        difference_1 = geometry.vector_to_difference(angle_1, 25)
        difference_2 = geometry.vector_to_difference(angle_2, 25)

        point_1 = utility.add_tuples(point, difference_1)
        point_2 = utility.add_tuples(point, difference_2)

        if index == 0:
            goals.append(geometry.two_point_square(point_1, point_2, False))
        else:
            goals.append(geometry.two_point_square(point_1, point_2, True))

    triangle_points = []
    for index in range(3):
        segment_1 = goals[index].segments[2]
        segment_2 = goals[index - 1].segments[2]
        point = geometry.poi(segment_1.slope, segment_1.y_intercept,
                             segment_2.slope, segment_2.y_intercept)
        triangle_points.append(point)

    goals.append(geometry.Polygon(triangle_points))

    collisions[0].set_colors((RED, RED))
    collisions[1].set_colors((RED, ))
    collisions[2].set_colors((ORANGE, ORANGE))
    collisions[3].set_colors((ORANGE, ))
    collisions[4].set_colors((CYAN, CYAN))
    collisions[5].set_colors((CYAN,))

    level = Level(collisions, goals, (405, 103), math.pi / 5 * 4)
    level.set_goal_colors((PALE_RED, PALE_ORANGE, PALE_CYAN, PALE_MAGENTA))

    return level


# Level 27: Triangle array
def generate_triangle_array_level():
    collisions = []

    horizontal_spacing = 100
    vertical_spacing = horizontal_spacing / 2 * math.sqrt(3)

    array_dimensions = 4
    colors = (RED, GREEN, MAGENTA, YELLOW, CYAN, YELLOW, RED, GREEN, MAGENTA, CYAN)
    color_index = 0

    topmost = 250 - ((array_dimensions - 1) * vertical_spacing / 2)
    for row in range(array_dimensions):
        leftmost = 250 - (row * horizontal_spacing / 2)
        for column in range(row + 1):
            x = leftmost + column * horizontal_spacing
            y = topmost + row * vertical_spacing

            polygon = geometry.regular_polygon(3, 10, (x, y), -math.pi / 2)

            polygon.set_colors((colors[color_index], ) * 3)
            color_index += 1

            collisions.append(polygon)

    goals = []

    x = 250 + horizontal_spacing / 2
    y = 265
    goals.append(geometry.regular_polygon(3, 30, (x, y), math.pi / 2))
    x = 250 - horizontal_spacing / 2
    y = 265
    goals.append(geometry.regular_polygon(3, 30, (x, y), math.pi / 2))

    level = Level(collisions, goals, (300, 250), math.pi / 4 * 3)
    level.set_goal_colors((PALE_GREEN, PALE_MAGENTA))

    return level


# Level 28: Tunnel
def generate_tunnel_level():
    collision_1 = geometry.Polygon(((200, 100), (200, 275), (250, 275), (250, 400)), False)  # Left
    collision_1.set_colors((RED, GREEN, RED))
    collision_2 = geometry.Polygon(((250, 100), (250, 225), (300, 225), (300, 400)), False)  # Right
    collision_2.set_colors((RED, GREEN, RED))

    collisions = (collision_1, collision_2)

    goal_1 = geometry.two_point_square((200, 100), (250, 100), False)  # Top
    goal_2 = geometry.two_point_square((200, 225), (250, 225), False)  # Middle left
    goal_3 = geometry.two_point_square((250, 225), (300, 225), False)  # Middle right
    goal_4 = geometry.two_point_square((250, 350), (300, 350), False)  # Bottom

    goals = (goal_1, goal_2, goal_3, goal_4)

    level = Level(collisions, goals, (312, 430), -math.pi / 4 * 3)
    level.set_goal_colors((PALE_CYAN, PALE_RED, PALE_GREEN, PALE_ORANGE))

    return level


# Level 29: Shapes
def generate_shapes_level():
    triangle_points = geometry.regular_polygon(3, 100, (250, 250), 0.4).point_list

    collision_1 = geometry.regular_polygon(4, 40, triangle_points[0], 1.232804)
    collision_1.set_colors((BLUE, MAGENTA) * 2)

    collision_2 = geometry.regular_polygon(6, 48, triangle_points[1], 0.429323)
    collision_2.set_colors((BLUE, MAGENTA) * 3)

    collision_3 = geometry.regular_polygon(8, 56, triangle_points[2], 2.139367)
    collision_3.set_colors((BLUE, MAGENTA) * 4)

    collisions = (collision_1, collision_2, collision_3)

    segment = collision_1.segments[2]
    goal_1 = geometry.two_point_square(segment.point1, segment.point2, True)

    segment = collision_2.segments[3]
    goal_2 = geometry.two_point_square(segment.point1, segment.point2, True)

    segment = collision_2.segments[5]
    goal_3 = geometry.two_point_square(segment.point1, segment.point2, True)

    segment = collision_3.segments[1]
    goal_4 = geometry.two_point_square(segment.point1, segment.point2, True)

    goals = (goal_1, goal_2, goal_3, goal_4)

    level = Level(collisions, goals, (100, 430), -math.pi / 4)
    level.set_goal_colors((PALE_BLUE, PALE_CYAN, PALE_YELLOW, PALE_MAGENTA))

    return level


# Level template
# def generate_<name>_level():
#     collision_1 = geometry.Polygon(((x, y), (x, y), (x, y)))
#     collision_1.set_colors((color1, color2, color3))
#     collision_2 = geometry.Polygon(((x, y), (x, y), (x, y)))
#     collision_2.set_colors((color1, color2, color3))
#     collision_3 = geometry.Polygon(((x, y), (x, y), (x, y)))
#     collision_3.set_colors((color1, color2, color3))
#
#     collisions = (collision_1, collision_2, collision_3)
#
#     goal_1 = geometry.Polygon(((x, y), (x, y), (x, y)))
#     goal_2 = geometry.Polygon(((x, y), (x, y), (x, y)))
#     goal_3 = geometry.Polygon(((x, y), (x, y), (x, y)))
#
#     goals = (goal_1, goal_2, goal_3)
#
#     level = Level(collisions, goals, (start_x, start_y), orientation)
#     level.set_goal_colors((color1, color2, color3))
#
#     return level


# Test level used to test that the basic mechanics worked
# level_test_shape1_points = ((100, 100), (400, 200), (350, 400), (100, 200))
# level_test_polygon1 = geometry.Polygon(level_test_shape1_points, False)
# level_test_polygon1.set_colors((constants.GREEN, constants.ORANGE,
#                                 constants.RED))
#
# level_test_shape2_points = ((240, 240), (240, 260), (260, 260), (240, 240))
# level_test_polygon2 = geometry.Polygon(level_test_shape2_points)
# level_test_polygon2.set_colors((constants.CYAN, ) * 3)
#
# level_test_shape3_points = ((10, 450), (250, 460), (490, 450))
# level_test_polygon3 = geometry.Polygon(level_test_shape3_points, False)
# level_test_polygon3.set_colors((constants.MAGENTA, constants.YELLOW))
#
# level_test = Level((level_test_polygon1, level_test_polygon2,
#                            level_test_polygon3))
