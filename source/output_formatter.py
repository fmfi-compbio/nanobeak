from os import fsync
from typing import List

from interface import OutputFormatterInterface, OutputData


class OutputFormatterFasta(OutputFormatterInterface):

    def write_output(self, output_data: List[OutputData]) -> None:

        for output in output_data:

            (read_id, _, _, _, _, basecalled_seq, _) = output

            if len(basecalled_seq) == 0:
                return

            print(">%s" % read_id, file=self.output_stream)
            print(basecalled_seq, file=self.output_stream, flush=True)

        fsync(self.output_stream.fileno())


class OutputFormatterFastq(OutputFormatterInterface):

    def write_output(self, output_data: List[OutputData]) -> None:

        for output in output_data:

            (read_id, run_id, read_num, channel_num, start_time, basecalled_seq, quality_scores) = output

            print("@%s runid=%s read=%d ch=%s start_time=%s"
                  % (read_id, run_id, read_num, channel_num, start_time), file=self.output_stream)

            print(basecalled_seq, file=self.output_stream)
            print("+", file=self.output_stream)
            print(quality_scores, file=self.output_stream, flush=True)

        fsync(self.output_stream.fileno())
