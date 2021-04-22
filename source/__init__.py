from sys import platform

from .input_reader import DirectoryReader

if platform == 'linux':
    from .input_reader import DirectoryWatcherLinux as DirectoryWatcher
elif platform == 'win32':
    from .input_reader import DirectoryWatcherWindows as DirectoryWatcher
elif platform == 'darwin':
    from .input_reader import DirectoryWatcherDarwin as DirectoryWatcher

from .output_formatter import OutputFormatterFasta, OutputFormatterFastq
from .task_executor import SequentialTaskExecutor, ParallelTaskExecutor
from .argument_parser import ArgumentParser
