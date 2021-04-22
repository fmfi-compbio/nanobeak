"""
This module defines public library data containers and type aliases.
See test/sample_app.py for example usage.
"""

from __future__ import annotations
from typing import NamedTuple


class OutputData(NamedTuple):
    """
    Class is a container for basecaller output.
    All fields are mandatory and filled by this library,
    so MinKnow-like output can be provided.
    """

    read_id: str
    run_id: str
    read_number: int
    channel_number: str
    start_time: str
    basecalled_sequence: str
    quality_scores: str


class LibraryComponents(NamedTuple):
    """
    Class is a container for class objects executing
    library functionality.
    Library components can be obtained from ArgumentParser object.
    Components are always returned initialized and ready for use
    (i.e. their initialize() method has been called).
    """

    input_reader: InputReaderInterface
    task_executor: TaskExecutorInterface
    output_formatter: OutputFormatterInterface


class Arguments(NamedTuple):
    """
    Class is a container for parsed user arguments unrelated
    to configuration of library compnents.
    Those arguments are rather relevant for configuration
    on integrator side (i.e. basecaller object configuration).
    Arguments can be obtained from ArgumentParser object.
    """

    watch_directory: bool
    network_type: str
    weights_path: FilePath
    beam_size: int
    beam_cut_threshold: float


FilePath = str
Path = str
