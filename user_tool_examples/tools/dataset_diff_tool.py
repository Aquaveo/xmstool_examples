"""DatasetDiffTool class."""

# 1. Standard Python modules

# 2. Third party modules
import numpy as np

# 3. Aquaveo modules
from xms.tool_core import ALLOW_ONLY_SCALARS, IoDirection, Tool

# 4. Local modules


class DatasetDiffTool(Tool):
    """A tool that computes a standard deviation dataset."""
    ARG_INPUT_DATASET1 = 0
    ARG_INPUT_DATASET2 = 1
    ARG_OUTPUT_DATASET = 2

    def __init__(self):
        """Constructor."""
        super().__init__(name='Compute Dataset Difference')
        self._reader1 = None
        self._reader2 = None
        self._null_value = None
        self._writer = None

    def initial_arguments(self):
        """Define initial arguments for the tool.

        Returns:
            List[Argument]: The list of initial arguments.
        """
        # Set up the dialog arguments
        args = [
            self.dataset_argument(name='input_dataset1', description='First input scalar dataset',
                                  filters=ALLOW_ONLY_SCALARS),  # Don't allow vector datasets
            self.dataset_argument(name='input_dataset2', description='Second input scalar dataset',
                                  filters=ALLOW_ONLY_SCALARS),  # Don't allow vector datasets
            self.dataset_argument(name='output_dataset', description='Diff Dataset', hide=True, optional=True,
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
        errors = {}
        # _validate_input_dataset() returns a DatasetReader so we don't have to retrieve it again in run(). Inspect
        # the DatasetReader class in xmsdatasets for more details on the dataset interface provided to tools.
        self._reader1 = self._validate_input_dataset(arguments[self.ARG_INPUT_DATASET1], errors)
        self._reader2 = self._validate_input_dataset(arguments[self.ARG_INPUT_DATASET2], errors)
        if self._reader1.geom_uuid != self._reader2.geom_uuid:
            errors[arguments[self.ARG_INPUT_DATASET1].name] = 'Datasets must be on the same geometry.'
        if self._reader1.num_values != self._reader2.num_values:
            errors[arguments[self.ARG_INPUT_DATASET1].name] = 'Datasets must have the same dataset location.'
        if self._reader1.num_times != self._reader2.num_times:
            errors[arguments[self.ARG_INPUT_DATASET1].name] = 'Datasets must have matching number of timesteps.'
        return errors

    def enable_arguments(self, arguments):
        """Called to show/hide arguments, change argument values and add new arguments.

        Args:
            arguments(list): The tool arguments.
        """
        # No GUI dependencies for this tool.
        pass

    def _init_writer(self):
        """Create the output dataset writer using metadata from the input dataset."""
        # If either of the input datasets have a defined null value, grab one so we can define it in the output dataset.
        # Note that datasets may alternatively define activity arrays. Reading and writing those datasets is beyond
        # the scope of this example.
        self._null_value = self._reader2.null_value if self._reader1.null_value is None else self._reader1.null_value

        # Create the writer, using attributes from the inputs.
        self._writer = self.get_output_dataset_writer(
            name=f'{self._reader1.name} - {self._reader2.name}',
            geom_uuid=self._reader1.geom_uuid,
            # Potentially could be a mismatch between inputs for reference time and time units. We could check in
            # validate_arguments() if we wanted to disallow that.
            ref_time=self._reader1.ref_time,
            time_units=self._reader1.time_units,
            null_value=self._null_value,  # Will be None if not defined on either input dataset
        )

    def run(self, arguments):
        """Override to run the tool.

        Args:
            arguments (list): The tool arguments.
        """
        self._init_writer()

        for ts_idx in range(self._reader1.num_times):  # Loop through timesteps of the input datasets.
            self.logger.info(f'Processing timestep {ts_idx + 1} of {self._reader1.num_times}')
            # Read a timestep from inputs. If the dataset has a null value defined, make it NaN.
            ts_data1, _ = self._reader1.timestep_with_activity(ts_idx, nan_null_values=True)
            ts_data2, _ = self._reader2.timestep_with_activity(ts_idx, nan_null_values=True)
            ts_diff = ts_data1 - ts_data2
            ts_diff[np.isnan(ts_diff)] = self._null_value  # Reset NaN locations to null value, if there were any.
            self._writer.append_timestep(self._reader1.times[ts_idx], ts_diff)  # Write timestep to output
        # Finialize output dataset, and send it back to XMS. Note that for steady-state or small transient
        # datasets we can write the entire dataset with one call to write_xmdf_dataset().
        self._writer.appending_finished()
        self.set_output_dataset(self._writer)
