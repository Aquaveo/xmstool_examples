"""DatasetFromDatTool class."""

# 1. Standard Python modules

# 2. Third party modules

# 3. Aquaveo modules
from xms.datasets.dat_reader import parse_dat_file
from xms.tool_core import IoDirection, Tool

# 4. Local modules


class DatasetFromDatTool(Tool):
    """A tool that imports a .2dm file as a UGrid."""
    ARG_INPUT_DAT_FILE = 0
    ARG_OUTPUT_DATASET = 1

    def __init__(self):
        """Constructor."""
        super().__init__(name='Dataset from dat')

    def initial_arguments(self):
        """Define initial arguments for the tool.

        Returns:
            List[Argument]: The list of initial arguments.
        """
        # Set up the dialog arguments
        args = [
            self.file_argument(
                name='dat_file', description='The .dat file to import', file_filter='DAT dataset files (*.dat)'
            ),
            self.dataset_argument(name='imported_dataset', description='Imported Dataset', hide=True, optional=True,
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
        filename = arguments[self.ARG_INPUT_DAT_FILE].text_value
        self.logger.info(f'Reading {filename}')
        dset = parse_dat_file(filename)  # This will create an XMDF file and return a reaer to it.
        # set_output_dataset() is typically called with a DatasetWriter instead of a DatasetReader.
        self.set_output_dataset(dset)
