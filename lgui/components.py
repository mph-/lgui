"""
Defines the components that lgui can simulate
"""

import numpy as np
import ipycanvas as canvas
import math

class Node:

    """
    Describes the node that joins components.
    """

    def __init__(self):

        self.position: tuple(int, int) = (0, 0)

    def __eq__(self, other: 'Node') -> bool:

        return self.position == other.position

class Component:

    """
    Describes an lgui component.

    Parameters
    ----------

    ctype: str
        The type of the component selected from Component.TYPES
    """

    NAMES = (
        "Resistor",
        "Inductor",
        "Capacitor",
        "Wire",
        "Voltage",
        "Current",
        "Ground"
    )

    TYPES = ("R", "L", "C", "W", "V", "I", "G")
    """Component types"""
    R, L, C, W, V, I, G = TYPES

    HEIGHT = 4

    next_ids: dict[str, int] = {ctype: 0 for ctype in TYPES}

    def __init__(self, ctype: str, value: int | float | str):

        self.type = ctype
        self.value = value
        self.ports: list[Node] = [Node(), Node()]
        self.id = Component.next_ids[self.type]
        Component.next_ids[self.type] += 1

    def along(self, p: float) -> np.array:
        """
        Computes the point some proportion along the line of the component.
        This is relative to the position of the zero-th port.

        Parameters
        ----------

        p: float
            Proportion of length along component.
        """
        delta = np.array(self.ports[1].position) - np.array(self.ports[0].position)
        return p*delta

    def orthog(self, p: float) -> np.array:
        """
        Computes the point some proportion to the right (anti-clockwise) of the self.
        This is relative to the position of the zero-th port.

        Parameters
        ----------

        p: float
            Proportion of the length of the component.
        """
        delta = np.array(self.ports[0].position) - np.array(self.ports[1].position) 
        theta = np.pi/2
        rot = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
        return p*np.dot(rot, delta)

    def draw_on(self, editor, layer: canvas.Canvas):
        """
        Draws a single component on a canvas.

        Parameters
        ----------

        editor: Editor
            The editor object to draw on
        layer: Canvas = None
            Layer to draw component on
        """

        start_x, start_y = self.ports[0].position
        end_x, end_y = self.ports[1].position

        with canvas.hold_canvas():

            layer.stroke_style = "#252525"

            match self.type:
                case Component.R: # Resistors
                    
                    ZIGS = 6
                    LEAD_LENGTH = 0.2
                    ZIG_WIDTH = (1 - 2*LEAD_LENGTH)/(ZIGS + 1)
                    ZIG_HEIGHT = 0.15

                    zig_shift = self.along(ZIG_WIDTH)
                    zig_orthog = self.orthog(ZIG_HEIGHT)

                    # lead 1
                    offset = self.along(LEAD_LENGTH)
                    mid = offset + (start_x, start_y)
                    layer.stroke_line(start_x, start_y, mid[0], mid[1])
                    # flick 1
                    layer.stroke_line(mid[0], mid[1], 
                        mid[0] - zig_orthog[0] + 0.5*zig_shift[0], 
                        mid[1] - zig_orthog[1] + 0.5*zig_shift[1]
                    )

                    # lead 2
                    mid = (end_x, end_y) - offset
                    layer.stroke_line(mid[0], mid[1], end_x, end_y)
                    # flick 2
                    layer.stroke_line(mid[0], mid[1], 
                        mid[0] - zig_orthog[0] - 0.5*zig_shift[0], 
                        mid[1] - zig_orthog[1] - 0.5*zig_shift[1]
                    )

                    for z in range(ZIGS):
                        mid = self.along(LEAD_LENGTH + (z + 1/2)*ZIG_WIDTH) + (start_x, start_y)
                        if z % 2 == 0:
                            start = mid - zig_orthog
                            end = mid + zig_shift + zig_orthog
                        else:
                            start = mid + zig_orthog
                            end = mid + zig_shift - zig_orthog

                        layer.stroke_line(start[0], start[1], end[0], end[1])

                case Component.L: # Inductors

                    LOOPS = 4
                    LEAD_LENGTH = 0.2
                    LOOP_RADIUS = (1 - 2*LEAD_LENGTH)/(2*LOOPS)

                    # leads
                    offset = self.along(LEAD_LENGTH)
                    mid = offset + (start_x, start_y)
                    layer.stroke_line(start_x, start_y, mid[0], mid[1])
                    mid = (end_x, end_y) - offset
                    layer.stroke_line(mid[0], mid[1], end_x, end_y)

                    angle_offset = np.arccos(
                        np.clip(
                            np.dot(
                                offset/np.linalg.norm(offset), np.array([1, 0])
                            ), 
                        -1.0, 1.0)
                    ) % np.pi

                    # loops
                    for l in range(LOOPS):
                        mid = self.along(LEAD_LENGTH + (2*l + 1)*LOOP_RADIUS) + (start_x, start_y)
                        layer.stroke_arc(
                            mid[0], mid[1], 
                            LOOP_RADIUS*editor.STEP/editor.SCALE, 
                            np.pi - angle_offset, -angle_offset 
                        )
                    
                case Component.C: # Capacitors

                    PLATE_WIDTH = 0.4
                    PLATE_SEP = 0.03

                    # lead 1
                    mid = self.along(0.5 - PLATE_SEP) + (start_x, start_y)
                    layer.stroke_line(start_x, start_y, mid[0], mid[1])

                    # plate 1
                    plate = self.orthog(PLATE_WIDTH)
                    shift = mid - 0.5*plate
                    layer.stroke_line(shift[0], shift[1], shift[0] + plate[0], shift[1] + plate[1])

                    # lead 2
                    mid = self.along(0.5 + PLATE_SEP) + (start_x, start_y)
                    layer.stroke_line(mid[0], mid[1], end_x, end_y)

                    # plate 2
                    plate = self.orthog(PLATE_WIDTH)
                    shift = mid - 0.5*plate
                    layer.stroke_line(shift[0], shift[1], shift[0] + plate[0], shift[1] + plate[1])

                case Component.W: # Wires

                    layer.stroke_line(start_x, start_y, end_x, end_y)

                case Component.V: # Voltage supply
                    
                    RADIUS = 0.3
                    OFFSET = 0.05

                    # lead 1
                    mid = self.along(0.5 - RADIUS) + (start_x, start_y)
                    layer.stroke_line(start_x, start_y, mid[0], mid[1])

                    # circle
                    mid = self.along(0.5) + (start_x, start_y)
                    layer.stroke_arc(mid[0], mid[1], RADIUS*Component.HEIGHT*editor.STEP, 0, 2*np.pi)

                    # positive symbol
                    mid = self.along(0.5 - RADIUS/2) + (start_x, start_y)
                    shift = self.along(OFFSET)
                    orthog = self.orthog(OFFSET)

                    start = mid - shift
                    end = mid + shift
                    layer.stroke_line(start[0], start[1], end[0], end[1])
                    start = mid - orthog
                    end = mid + orthog
                    layer.stroke_line(start[0], start[1], end[0], end[1])

                    # negative symbol
                    mid = self.along(0.5 + RADIUS/2) + (start_x, start_y)
                    start = mid - orthog
                    end = mid + orthog
                    layer.stroke_line(start[0], start[1], end[0], end[1])

                    # lead 1
                    mid = self.along(0.5 + RADIUS) + (start_x, start_y)
                    layer.stroke_line(mid[0], mid[1], end_x, end_y)

                case Component.I: # Current supply
                    
                    RADIUS = 0.3
                    OFFSET = 0.05

                    # lead 1
                    mid = self.along(0.5 - RADIUS) + (start_x, start_y)
                    layer.stroke_line(start_x, start_y, mid[0], mid[1])

                    # circle
                    mid = self.along(0.5) + (start_x, start_y)
                    layer.stroke_arc(mid[0], mid[1], RADIUS*Component.HEIGHT*editor.STEP, 0, 2*np.pi)

                    # arrow body
                    arrow_start = self.along(0.5 + RADIUS/2) + (start_x, start_y)
                    arrow_end = self.along(0.5 - RADIUS/2) + (start_x, start_y)
                    layer.stroke_line(arrow_start[0], arrow_start[1], arrow_end[0], arrow_end[1])

                    # arrow head
                    arrow_shift = self.along(OFFSET)
                    arrow_orthog = self.orthog(-OFFSET)
                    layer.stroke_line(arrow_end[0], arrow_end[1], 
                        arrow_end[0]+arrow_shift[0]+arrow_orthog[0],
                        arrow_end[1]+arrow_shift[1]+arrow_orthog[1]
                    )
                    layer.stroke_line(arrow_end[0], arrow_end[1], 
                        arrow_end[0]+arrow_shift[0]-arrow_orthog[0],
                        arrow_end[1]+arrow_shift[1]-arrow_orthog[1]
                    )

                    # lead 1
                    mid = self.along(0.5 + RADIUS) + (start_x, start_y)
                    layer.stroke_line(mid[0], mid[1], end_x, end_y)

            # node dots
            layer.fill_arc(start_x, start_y, editor.STEP // 5, 0, 2 * math.pi)
            layer.fill_arc(end_x, end_y, editor.STEP // 5, 0, 2 * math.pi)
        