"""
This module defines public interface of InputReader class family.
See test/sample_app.py for example usage.
"""

from typing import List

from .data_types import FilePath, Path


class InputReaderInterface:

    def __init__(self, input_directories: List[Path], input_files: List[FilePath]) -> None:

        self.input_directories = input_directories
        self.input_files = input_files
        self.task_batch = None

    def initialize(self) -> None:
        """
        Method initializes class object.
        This method is always called by ArgumentParser and should NOT be
        called by integrator.
        """
        raise NotImplementedError

    def get_next_batch(self) -> List[FilePath]:
        """
        Method returns next batch of files ready to be processed
        by task executor.
        This method can be called as many times as necessary on
        DirectoryWatcher family, but should be called only ONCE
        on basic DirectoryReaders.
        """
        raise NotImplementedError
