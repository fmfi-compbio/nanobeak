from multiprocessing import Pool
import os
import re
from sys import platform
from typing import NamedTuple, List, Tuple

if platform == 'linux':
    import inotify.adapters
    import inotify.constants
elif platform == 'win32':
    from win32file import CreateFile, ReadDirectoryChangesW
    from win32security import SECURITY_ATTRIBUTES
    from win32con import (FILE_SHARE_DELETE, FILE_SHARE_READ, FILE_SHARE_WRITE, OPEN_EXISTING,
                          FILE_FLAG_BACKUP_SEMANTICS, FILE_NOTIFY_CHANGE_FILE_NAME)

from interface import InputReaderInterface, FilePath, Path


class DirectoryReader(InputReaderInterface):

    def initialize(self) -> None:
        self.task_batch, _ = _process_inputs(self.input_directories, self.input_files)

    def get_next_batch(self) -> List[FilePath]:
        return self.task_batch


if platform == 'linux':

    class DirectoryWatcherLinux(InputReaderInterface):

        def __init__(self, input_directories: List[Path], input_files: List[FilePath]) -> None:

            self.notifier = inotify.adapters.Inotify(block_duration_s=None)
            super().__init__(input_directories, input_files)

        def _fast5_filter_predicate(self, _: str, event: Tuple[str]) -> bool:

            (_, _, _, filename) = event
            return _is_fast5_file(filename)

        def initialize(self) -> None:

            self.task_batch, directories = _process_inputs(self.input_directories, self.input_files)

            for directory in directories:
                self.notifier.add_watch(directory, inotify.constants.IN_CREATE | inotify.constants.IN_MOVED_TO)

        def get_next_batch(self) -> List[FilePath]:

            task_batch_local = []

            if self.task_batch:
                task_batch_local.extend(self.task_batch)
                self.task_batch.clear()

            while True:

                for event in self.notifier.event_gen(filter_predicate=self._fast5_filter_predicate):

                    if event is None:
                        break

                    (_, _, path, filename) = event
                    task_batch_local.append(os.path.join(path, filename))

                if task_batch_local:
                    return task_batch_local


elif platform == 'win32':

    class DirectoryWatcherWindows(InputReaderInterface):

        DirectoryEvents = Tuple[List[Tuple[str]], FilePath]

        class DirectoryHandle(NamedTuple):

            handle: PyHANDLE
            directory_path: FilePath


        def __init__(self, input_directories: List[Path], input_files: List[FilePath]) -> None:

            self.directory_handles = []
            self.pool = None
            super().__init__(input_directories, input_files)

        def __del__(self) -> None:

            for directory_handle in self.directory_handles:
                directory_handle.handle.Close()

            self.pool.terminate()

        def _get_directory_handle(self, directory_path: FilePath) -> self.DirectoryHandle:

            FILE_LIST_DIRECTORY = 0x0001

            security_attributes = SECURITY_ATTRIBUTES()
            security_attributes.bInheritHandle = True

            handle = CreateFile(
                directory_path,
                FILE_LIST_DIRECTORY,
                FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                security_attributes,
                OPEN_EXISTING,
                FILE_FLAG_BACKUP_SEMANTICS,
                None)

            return self.DirectoryHandle(handle, directory_path)

        def _get_events(self, directory_handle: self.DirectoryHandle) -> self.DirectoryEvents:

            BUFFER_SIZE = 65536

            events = ReadDirectoryChangesW(
                directory_handle.handle,
                BUFFER_SIZE,
                False,
                FILE_NOTIFY_CHANGE_FILE_NAME,
                None,
                None)

            return events, directory_handle.directory_path

        def initialize(self) -> None:

            self.task_batch, directories = _process_inputs(self.input_directories, self.input_files)

            for directory in directories:
                self.directory_handles.append(self._get_directory_handle(directory))

            self.pool = Pool(len(self.directory_handles))

        def get_next_batch(self) -> List[FilePath]:

            task_batch_local = []

            if self.task_batch:
                task_batch_local.extend(self.task_batch)
                self.task_batch.clear()

            while True:

                for events, directory_path in self.pool.imap_unordered(
                        self._get_events,
                        self.directory_handles):

                    for _, filename in events:
                        if _is_fast5_file(filename):
                            task_batch_local.append(os.path.join(directory_path, filename))

                    return task_batch_local


elif platform == 'darwin':

    class DirectoryWatcherDarwin(InputReaderInterface):

        def initialize(self) -> None:
            raise NotImplementedError

        def get_next_batch(self) -> List[FilePath]:
            raise NotImplementedError


def _is_fast5_file(filename: str) -> bool:
    return re.search('.fast5$', filename) is not None


def _process_inputs(input_directories: List[Path], input_files: List[FilePath]) -> Tuple[List[FilePath], List[Path]]:

    task_batch = [file for file in input_files or [] if os.path.isfile(file) and _is_fast5_file(file)]
    directories = [dirc for dirc in input_directories or [] if os.path.isdir(dirc)]

    for dirc in directories:
        task_batch += [os.path.join(dirc, file) for file in os.listdir(dirc) if _is_fast5_file(file)]

    return task_batch, directories
