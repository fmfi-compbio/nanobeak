import argparse

from interface import (ArgumentParserInterface, InputReaderInterface, OutputFormatterInterface,
                       TaskExecutorInterface, Arguments, LibraryComponents)

from source import (DirectoryReader, DirectoryWatcher, OutputFormatterFasta,
                    OutputFormatterFastq, SequentialTaskExecutor, ParallelTaskExecutor)


class ArgumentParser(ArgumentParserInterface):

    def __init__(self) -> None:

        self.parser = argparse.ArgumentParser(description='Fast caller for ONT reads')
        self.library_components = None

    def parse_arguments(self) -> Arguments:

        self.parser.add_argument('--directory', type=str, nargs='*',
                                 help='One or more directories with reads')
        self.parser.add_argument('--watch-directory', action='store_true', default=False,
                                 help='Watch directories for new reads')
        self.parser.add_argument('--reads', type=str, nargs='*',
                                 help='One or more read files')

        self.parser.add_argument("--cores", type=int, default=1,
                                 help="Number of cores available for basecalling, defaults to 1")

        self.parser.add_argument("--output", type=str, required=True,
                                 help="Output FASTA/FASTQ file name")
        self.parser.add_argument("--output-format", choices=["fasta", "fastq"], default="fasta")
        self.parser.add_argument("--gzip-output", action="store_true",
                                 help="Compress output with gzip")

        self.parser.add_argument("--weights", type=str, default=None,
                                 help="Path to network weights; only used for custom weights")
        self.parser.add_argument("--network-type", choices=["48", "56", "64", "80", "96", "256"], default="48",
                                 help="Size of network. Default 48")
        self.parser.add_argument("--beam-size", type=int, default=None,
                                 help="Beam size (defaults 5 for 48,56,64,80,96 and 20 for 256). Use 1 for greedy decoding.")
        self.parser.add_argument("--beam-cut-threshold", type=float, default=None,
                                 help="Threshold for creating beams (higher means faster beam search, but smaller accuracy). \
                                 Values higher than 0.2 might lead to weird errors. Default 0.1 for 48,...,96 and 0.0001 for 256")

        arguments = self.parser.parse_args()

        input_reader = _initialize_input_reader(arguments)
        task_executor = _initialize_task_executor(arguments)
        output_formatter = _initialize_output_formatter(arguments)

        self.library_components = LibraryComponents(input_reader, task_executor, output_formatter)

        return Arguments(arguments.watch_directory, arguments.network_type, arguments.weights,
                         arguments.beam_size, arguments.beam_cut_threshold)

    def get_library_components(self) -> LibraryComponents:
        return self.library_components


def _initialize_input_reader(arguments: argparse.Namespace) -> InputReaderInterface:

    if arguments.watch_directory:
        watcher = DirectoryWatcher(arguments.directory, arguments.reads)
    else:
        watcher = DirectoryReader(arguments.directory, arguments.reads)

    watcher.initialize()
    return watcher


def _initialize_task_executor(arguments: argparse.Namespace) -> TaskExecutorInterface:

    if arguments.cores <= 1:
        return SequentialTaskExecutor()

    return ParallelTaskExecutor(arguments.cores)


def _initialize_output_formatter(arguments: argparse.Namespace) -> OutputFormatterInterface:

    if arguments.output_format == 'fasta':
        return OutputFormatterFasta(arguments.output, arguments.gzip_output)
    if arguments.output_format == 'fastq':
        return OutputFormatterFastq(arguments.output, arguments.gzip_output)

    return None
