"""
This module defines public interface from TaskExecutor class family.
Also defines interface that basecaller dependency injection MUST implement.
See test/sample_app.py for example usage.
"""

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from .data_types import FilePath, OutputData

@dataclass
class BasecallerInterface:
    """
    Task executors in this library can use any injected
    basecaller object that implements following interface.
    No default basecaller is available.
    """

    def call_raw_signal(self, signal: np.ndarray) -> Tuple[str, str]:
        """
        Method implements signal basecalling. Takes one argument
        of numpy.ndarray of numpy.float32 values.
        Please note that input signal is already normalized by library.
        This can be discussed in the future (see source/task_executor.py).

        Method returns a tuple of strings. Those are basecalled sequence
        and quality scores (as defined in fastq file format) respectively.
        """
        raise NotImplementedError


class TaskExecutorInterface:

    def __init__(self) -> None:
        self.caller = None

    def set_caller(self, caller: BasecallerInterface) -> None:
        """
        Method lets integrator to inject a custom basecaller object and
        verifies at least partially whether it implements required interface.
        """

        obj_type = type(caller)

        if hasattr(obj_type, 'call_raw_signal') and callable(obj_type.call_raw_signal):
            self.caller = caller
        else:
            raise ValueError('Caller object does NOT implement BasecallerInterface!')

    def execute_task_batch(self, tasks: List[FilePath]) -> List[OutputData]:
        """
        Method performs basecalling using custom basecaller object on all files in task batch.
        Returns list of filled OutputData objects ready for output formatting.
        """
        raise NotImplementedError
