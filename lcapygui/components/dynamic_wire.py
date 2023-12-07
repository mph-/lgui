from .wire import Wire
from .picture import Picture
from astar import AStar
import math
import numpy as np


class WireSolver(AStar):

    """
    Implementation of the python-astar package for finding a path between two points, with least turns

    Attributes
    ==========
    lines : list[list[int]]
        The list representation of the nodes in the circuit
    width : int
        The width of the circuit
    height : int
        The height of the circuit
    """

    def __init__(self, graph):
        self.lines = graph
        self.width = len(self.lines[0])
        self.height = len(self.lines)

    def heuristic_cost_estimate(self, node_A, node_B):
        """
        Computes the "least turns" distance between two nodes

        Explanation
        ===========
        Two points that are aligned on the same grid line have a distance of 1
        if not, they have a weight of near infinity, ensuring that paths in straight lines are preferred.

        Parameters
        ==========
        node_A : tuple[int, int]
            A tuple containing the x, y position of the first node
        node_B : tuple[int, int]
            A tuple containing the x, y position of the second node

        Returns
        =======
        int
            The distance between the two nodes
        """
        (x_1, y_1) = node_A
        (x_2, y_2) = node_B
        if x_1 == x_2 or y_1 == y_2:
            return 1
        else:
            return 100000

    def distance_between(self, node_1, node_2):
        """
        Computes the distance between two neighbouring nodes.
        Since neighbouring nodes are always adjacent, this function always returns 1
        """
        return 1

    def neighbors(self, node):
        """
        Returns the neighbours of a given node, provided they are not an existing node.

        Parameters
        ==========
        node : tuple[int, int]
            A tuple containing the x, y position of the node

        Returns
        =======
        list[tuple[int, int]]
            A list of tuples containing the x, y position of the neighbouring nodes
        """
        x, y = node
        neighbours = [
            (nx, ny)
            # Get each neighbouring node
            for nx, ny in [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
            # Check the points are within the bounds of the graph, and that they are not an existing node
            if (0 <= nx < self.width and 0 <= ny < self.height)
            and (self.lines[ny][nx] == 0)
        ]
        return neighbours


class DynamicWire(Wire):
    type = "DW"
    args = ()
    has_value = False

    def __init__(self, simplify_path=True, *args, **kwargs):
        """
        Initializes the DynamicWire class
        TODO: Remove magic numbers in WireSolver
        Parameters
        ==========
        args
        kwargs
        """

        # Perform regular initialization
        super().__init__(*args, **kwargs)

        # Initialize the path and pathfinder
        self.__path = []
        # Default with some large graph
        self.__path_finder = WireSolver(
            [[0 for x in range(0, 36)] for y in range(0, 22)]
        )
        self.__simplified = simplify_path

    def update_path(self):
        # Get start and end nodes
        start = (int(self.node1.x), int(self.node1.y))
        end = (int(self.node2.x), int(self.node2.y))

        # perform A* search to find the path between the nodes
        path = self.__path_finder.astar(start, end)

        # If no path could be found return none
        if path is None:
            print("ERROR: No path found")
            self.__path = [start, end]
            return

        self.__path = list(path)

        # optionally simplify the path
        if self.__simplified:
            self.simplify_path()

    def simplify_path(self):
        """
        Simplifies the path by removing unnecessary nodes along straight paths.
        """
        # First value is always in the path
        simplified = [self.__path[0]]
        for i in range(1, len(self.__path) - 1):
            # Get the neighbouring nodes
            previous = self.__path[i - 1]
            current = self.__path[i]
            next = self.__path[i + 1]
            # Check if the current node is not aligned with the previous or next node
            if (previous[0] != current[0] or current[0] != next[0]) and (
                previous[1] != current[1] or current[1] != next[1]
            ):
                # If it is not aligned, add it to the simplified path
                simplified.append(self.__path[i])
        simplified.append(self.__path[-1])

        self.__path = simplified

    def update_graph(self, model=None):
        """
        Updates the graph representation of the circuit
        Parameters
        ----------
        model : lcapy.circuit.Circuit or None
            The circuit to update the graph from the existing circuit
            If circuit is none, it assumes a blank screen
        """
        if model is None:
            return
        # Get the graph size
        x_size = model.preferences.xsize
        y_size = model.preferences.ysize
        self.__path_finder.width = x_size
        self.__path_finder.height = y_size

        # generate a blank graph
        self.__path_finder.lines = [[0 for x in range(0, x_size)] for y in range(0, y_size)]


        for x in range(0, x_size):
            for y in range(0, y_size):
                for cpt in model.circuit.elements.values():
                    if cpt.gcpt is not self and cpt.gcpt.is_within_bbox(x, y):
                        self.__path_finder.lines[y][x] = 1

    def draw(self, model, **kwargs):
        """
        Draws a dynamic wire, following a path between two nodes

        Parameters
        ==========
        model : lcapygui.ui.uimodelbase.UIModelBase or lcapygui.ui.uimodelmph.UIModelMPH or lcapygui.ui.uimodeldnd.UIModelDnD
            UI Model to draw to

        """
        sketcher = model.ui.sketcher
        kwargs = self.make_kwargs(model, **kwargs)
        self.picture = Picture()

        self.update_graph(model)
        self.update_path()

        for start, end in self.point_pairs:
            self.picture.add(
                sketcher.stroke_line(start[0], start[1], end[0], end[1], **kwargs)
            )

    def convert_to_wires(self, model, **kwargs):
        self.update_path()

        previous = self.__path[0]
        for node in self.__path[1:]:
            model.cpt_create("W", previous[0], previous[1], node[0], node[1])
            previous = node
        model.delete(self)

    @property
    def point_pairs(self):
        pairs = []
        previous = self.__path[0]
        for node in self.__path[1:]:
            pairs.append([previous, node])
            previous = node
        return pairs

    def is_within_bbox(self, x, y):
        mouse = np.array([x, y])
        # Get the list of points in the wire
        for start, end in np.array(self.point_pairs):
            # Get the absolute distance between the mouse and that segment of the wire
            r = np.linalg.norm(np.cross(end - start, start - mouse)) / np.linalg.norm(
                end - start
            )
            # Assume less than half a square is "close enough"
            if r < 0.5:
                return True
        return False
