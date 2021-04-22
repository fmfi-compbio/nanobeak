import datetime
from multiprocessing import Pool
from typing import Generator, List, NamedTuple, Tuple

import numpy as np
from ont_fast5_api.fast5_interface import get_fast5_file, check_file_type
from ont_fast5_api.fast5_read import Fast5Read

from interface import BasecallerInterface, TaskExecutorInterface, FilePath, OutputData


class CallInputData(NamedTuple):
    """
    Class is a container of input data for _call_read() function.
    Design is motivated by the fact that ONT Fast5 API's Fast5Read
    objects cannot be serialized through communication pipes with CPU workers.
    This data is enough for worker to identify and load its input
    data from fast5 file while avoiding costly transmision of raw data itself.
    """

    read_id: str
    filename: str
    caller: BasecallerInterface


class SequentialTaskExecutor(TaskExecutorInterface):

    def execute_task_batch(self, tasks: List[FilePath]) -> List[OutputData]:

        if self.caller is None:
            raise ValueError('Caller object is NOT set!')

        output_list = []

        try:
            for task in tasks:
                with get_fast5_file(task, mode='r') as fast5_file:

                    for read_id in fast5_file.get_read_ids():
                        output_data = _call_read(CallInputData(read_id, task, self.caller))
                        output_list.append(output_data)

        except OSError as excp:
            _print_exception_warning(str(excp))
            return output_list

        return output_list


class ParallelTaskExecutor(TaskExecutorInterface):

    def __init__(self, cores: int) -> None:

        self.pool = Pool(cores)
        self.chunk_size = 100
        super().__init__()

    def __del__(self) -> None:
        self.pool.terminate()

    def _get_call_inputs_wrapper(self, fast5_list) -> Generator[CallInputData, None, None]:

        for fast5_file in fast5_list:
            for read_id in fast5_file.get_read_ids():
                yield CallInputData(read_id, fast5_file.filename, self.caller)

    def execute_task_batch(self, tasks: List[FilePath]) -> List[OutputData]:
        """
        Method performs parallel basecalling of files from task batch.
        If multifast5 file is being processed, reads of that file are distributed
        to CPU workers by chunks of size = chunk_size and are basecalled in parallel.
        If singlefast5 file is processed, it is appended to list with other
        singlefast5 files and then files themselves are distributed to CPU workers
        by chunks of size = chunk_size and are basecalled in parallel.
        """

        if self.caller is None:
            raise ValueError('Caller object is NOT set!')

        output_list = []
        single_fast5_list = []

        for task in tasks:
            try:
                with get_fast5_file(task, mode='r') as fast5_file:
                    file_type = check_file_type(fast5_file)

                    if file_type == 'single-read':
                        single_fast5_list.append(fast5_file)
                    if file_type == 'multi-read':
                        for output in self.pool.imap_unordered(
                                _call_read,
                                self._get_call_inputs_wrapper([fast5_file]),
                                self.chunk_size):
                            output_list.append(output)

            except OSError as excp:
                _print_exception_warning(str(excp))
                return output_list

        try:
            for output in self.pool.imap_unordered(
                    _call_read,
                    self._get_call_inputs_wrapper(single_fast5_list),
                    self.chunk_size):
                output_list.append(output)

        except OSError as excp:
            _print_exception_warning(str(excp))
            return output_list

        return output_list


def _print_exception_warning(exception_str: str) -> None:

    print(exception_str)
    print('Error encountered! Task execution may be incomplete!')


def _med_mad(signal: np.ndarray, factor=1.4826) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate signal median and median absolute deviation.
    """

    med = np.median(signal)
    mad = np.median(np.absolute(signal - med)) * factor
    return med, mad


def _rescale_signal(signal: np.ndarray) -> np.ndarray:

    signal = signal.astype(np.float32)
    med, mad = _med_mad(signal)
    signal -= med
    signal /= mad
    return signal


def _add_time_seconds(base_time_str: str, delta_seconds: int) -> str:

    base_time = datetime.datetime.strptime(base_time_str, '%Y-%m-%dT%H:%M:%SZ')
    base_time += datetime.timedelta(seconds=delta_seconds)
    return base_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def _call_read(input_data: CallInputData) -> OutputData:

    (read_id, filename, caller) = input_data

    with get_fast5_file(filename, mode='r') as fast5_file:

        file_type = check_file_type(fast5_file)
        read = Fast5Read(fast5_file, read_id) if file_type == 'multi-read' else fast5_file

        run_id = read.run_id.decode('utf-8')
        read_number = read.handle['Raw'].attrs['read_number'] if file_type == 'multi-read' else read.status.read_info[0].read_number
        start_time = read.handle['Raw'].attrs['start_time'] if file_type == 'multi-read' else read.status.read_info[0].start_time
        channel_number = read.handle[read.global_key + 'channel_id'].attrs['channel_number'].decode('utf-8')

        sampling_rate = read.handle[read.global_key + 'channel_id'].attrs['sampling_rate']
        exp_start_time = read.handle[read.global_key + 'tracking_id'].attrs['exp_start_time'].decode('utf-8')

        start_time = _add_time_seconds(exp_start_time, start_time / sampling_rate)

        signal = read.get_raw_data()
        signal = _rescale_signal(signal)

        basecalled_seq, quality_scores = caller.call_raw_signal(signal)

        return OutputData(read_id, run_id, read_number, channel_number, start_time, basecalled_seq, quality_scores)
