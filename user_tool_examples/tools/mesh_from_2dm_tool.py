"""MeshFrom2dmTool class."""

# 1. Standard Python modules
from pathlib import Path

# 2. Third party modules

# 3. Aquaveo modules
from xms.constraint import Grid, UGridBuilder
from xms.grid.ugrid import UGrid
from xms.tool_core import IoDirection, Tool

# 4. Local modules


class MeshFrom2dmTool(Tool):
    """A tool that imports a .2dm file as a 2D mesh."""
    ARG_INPUT_2DM_FILE = 0
    ARG_INPUT_OVERRIDE_NAME = 1
    ARG_INPUT_MESHNAME = 2
    ARG_OUTPUT_GRID = 3
    MIN_NODE_LINE_CARDS = 5

    def __init__(self):
        """Constructor."""
        super().__init__(name='2D Mesh from 2dm')
        self._nodes: dict[int, tuple[float, float, float]] = {}  # ID -> location
        self._node_map: dict[int, int] = {}  # ID -> index
        self._cells: list[list[int]] = []
        self._mesh_name = ''

    def initial_arguments(self):
        """Define initial arguments for the tool.

        Returns:
            List[Argument]: The list of initial arguments.
        """
        # Set up the dialog arguments
        args = [
            self.file_argument(
                name='two_dm_file', description='The .2dm file to import', file_filter='2dm geometry files (*.2dm)'
            ),
            self.bool_argument(name='override_name', description='Override the mesh name specified in the .2dm file',
                               value=False),
            self.string_argument(name='mesh_name', description='Mesh name', value='', optional=True),
            self.grid_argument(name='imported_geom', description='Imported 2D Mesh/UGrid', hide=True, optional=True,
                               io_direction=IoDirection.OUTPUT)
        ]
        return args

    def validate_arguments(self, arguments):
        """Called to determine if arguments are valid.

        Args:
            arguments (list): The tool arguments.

        Returns:
            (dict): Dictionary of errors for arguments.
        """
        # No validation required for this tool.
        return {}

    def enable_arguments(self, arguments):
        """Called to show/hide arguments, change argument values and add new arguments.

        Args:
            arguments(list): The tool arguments.
        """
        # Only show the input field for the mesh's name if the user has chosen to ignore the name from the file.
        arguments[self.ARG_INPUT_MESHNAME].show = arguments[self.ARG_INPUT_OVERRIDE_NAME].value

    def _add_node(self, line: list[str]):
        """Parse a node location from a line in the file.

        Args:
            line: The line, split on whitespace
        """
        if len(line) < self.MIN_NODE_LINE_CARDS:
            self.fail(f'Unable to parse node: {" ".join(line)}')  # Use self.fail instead of logging module error
            return  # Bad file
        # ND <ID> <X> <Y> <Z>
        self._nodes[int(line[1])] = (float(line[2]), float(line[3]), float(line[4]))  # Preserve ID to handle gaps

    def _add_cell(self, line: list[str]):
        """Parse a cell definition from a line in the file.

        Args:
            line: The line, split on whitespace
        """
        num_pts = 3
        if line[0].lower() == 'e4q':
            num_pts = 4  # quad
        if len(line) < num_pts + 2:  # Word for each point plus the cell id and card
            self.fail(f'Unable to parse element: {" ".join(line)}')  # Use self.fail instead of logging module error
            return  # Bad file
        # <E3T | E4Q> <ID> <PT1> <PT2> <PT3> [PT4]
        self._cells.append([int(word) for word in line[2: num_pts + 2]])  # Don't care about the cell type or ID

    def _parse(self, filename: str):
        """Parse the .2dm file.

        Args:
            filename: Path to the file
        """
        with open(filename) as f:
            lines = f.readlines()

        mesh_name_card = 'MESHNAME'.casefold()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.casefold().startswith(mesh_name_card):  # Parse the geometry name
                self._mesh_name = line[len(mesh_name_card):].strip().strip('"')
                continue
            line_words = line.split()
            card = line_words[0].lower()
            if card in ['e3t', 'e4q']:  # Parse a cell definition
                self._add_cell(line_words)
            elif card == 'nd':  # Parse a node location
                self._add_node(line_words)

    def _build_points(self) -> list[tuple[float, float, float]]:
        """Build the locations list for the grid."""
        locs = []
        for idx, (node_id, node_locs) in enumerate(self._nodes.items()):
            self._node_map[node_id] = idx  # Map ID to index so we can handle node numbering gaps when building cells.
            locs.append(node_locs)
        return locs

    def _build_cellstream(self) -> list[int]:
        """Build the cellstream for the grid."""
        cellstream = []
        for cell in self._cells:
            cell_type = UGrid.cell_type_enum.TRIANGLE  # Only tris and quads in a .2dm
            if len(cell) == 4:
                cell_type = UGrid.cell_type_enum.QUAD
            # <cell_type> <num_pts> <PT1> <PT2> <PT3> [PT4]
            cellstream.extend((cell_type, len(cell)))
            cellstream.extend([self._node_map[node_id] for node_id in cell])
        return cellstream

    def _build_cogrid(self) -> Grid:
        """Build the constrained UGrid for XMS consumption."""
        locations = self._build_points()
        cellstream = self._build_cellstream()
        ugrid = UGrid(locations, cellstream)
        ugrid_builder = UGridBuilder()
        ugrid_builder.set_is_2d()
        ugrid_builder.set_ugrid(ugrid)
        return ugrid_builder.build_grid()

    def run(self, arguments):
        """Override to run the tool.

        Args:
            arguments (list): The tool arguments.
        """
        filename = arguments[self.ARG_INPUT_2DM_FILE].text_value
        self._mesh_name = Path(filename).name  # Use basename of the file as a fallback
        self.logger.info(f'Parsing {filename}')
        self._parse(filename)
        self.logger.info(f'Building geometry')
        cogrid = self._build_cogrid()

        # Set the output grid with the right name
        if arguments[self.ARG_INPUT_OVERRIDE_NAME].value and arguments[self.ARG_INPUT_MESHNAME].value:
            self._mesh_name = arguments[self.ARG_INPUT_MESHNAME].value
        arguments[self.ARG_OUTPUT_GRID].value = self._mesh_name
        # force_ugrid=False tells SMS to create the grid in the 2D Mesh module instead of UGrid.
        self.set_output_grid(cogrid, arguments[self.ARG_OUTPUT_GRID], force_ugrid=False)
