"""
This module defines public interface for OutputFormatter class family.
See test/sample_app.py for example usage.
"""

import gzip
from typing import List

from .data_types import OutputData


class OutputFormatterInterface:

    def __init__(self, output_name: str, compressed_output: bool) -> None:

        self.compressed_output = compressed_output

        if self.compressed_output:
            self.output_stream = gzip.open(output_name, "wt")
        else:
            self.output_stream = open(output_name, "w")

    def __del__(self) -> None:
        self.output_stream.close()

    def write_output(self, output_data: List[OutputData]) -> None:
        """
        Method implements printing of output batch in various formats.
        Output is flushed immediately and fsync is called after
        every batch is printed.
        """
        raise NotImplementedError
