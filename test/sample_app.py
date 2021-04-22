"""
This module provides example integration of nanobeak library.
Also provides an easy way of testing library functionality during its development.
"""

from sys import path
path[0] += ('/../')

from typing import Tuple

from interface import BasecallerInterface
from source import ArgumentParser


class BasecallerMock(BasecallerInterface):

    def call_raw_signal(self, signal) -> Tuple[str, str]:

        basecalled_sequence = 'ACGT'
        quality_scores = 'Quite a score!'

        return basecalled_sequence, quality_scores


def basecall_input() -> None:

    task_batch = components.input_reader.get_next_batch()
    output_data = components.task_executor.execute_task_batch(task_batch)
    components.output_formatter.write_output(output_data)


def basecall_watched_input() -> None:
    while True:
        basecall_input()


if __name__ == '__main__':

    arg_parser = ArgumentParser()

    arguments = arg_parser.parse_arguments()
    components = arg_parser.get_library_components()

    components.task_executor.set_caller(BasecallerMock())

    if arguments.watch_directory:
        basecall_watched_input()
    else:
        basecall_input()
