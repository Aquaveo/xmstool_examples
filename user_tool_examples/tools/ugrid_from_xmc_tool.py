"""UGridFromXmcTool class."""

# 1. Standard Python modules
from pathlib import Path

# 2. Third party modules

# 3. Aquaveo modules
from xms.constraint import read_grid_from_file
from xms.tool_core import IoDirection, Tool

# 4. Local modules


class UGridFromXmcTool(Tool):
    """A tool that imports a .xmc file as a UGrid."""
    ARG_INPUT_XMC_FILE = 0
    ARG_OUTPUT_GRID = 1

    def __init__(self):
        """Constructor."""
        super().__init__(name='UGrid from xmc')

    def initial_arguments(self):
        """Define initial arguments for the tool.

        Returns:
            List[Argument]: The list of initial arguments.
        """
        # Set up the dialog arguments
        args = [
            self.file_argument(
                name='xmc_file', description='The .xmc file to import', file_filter='XMS constraint geometry files (*.xmc)'
            ),
            self.grid_argument(name='imported_geom', description='Imported UGrid name', optional=True, value='',
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
        # No GUI dependencies for this tool.
        pass

    def run(self, arguments):
        """Override to run the tool.

        Args:
            arguments (list): The tool arguments.
        """
        filename = arguments[self.ARG_INPUT_XMC_FILE].text_value
        self.logger.info(f'Reading {filename}')
        cogrid = read_grid_from_file(filename)
        # Set the output grid with the name specified by the user or the file basename if it wasn't.
        arguments[self.ARG_OUTPUT_GRID].value = arguments[self.ARG_OUTPUT_GRID].text_value or Path(filename).name
        self.set_output_grid(cogrid, arguments[self.ARG_OUTPUT_GRID])
