#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
import asyncio
import dataclasses

from aiostream import stream
from airbyte_cdk.models import (
    AirbyteMessage,
    AirbyteRecordMessage,
    AirbyteStream,
    ConfiguredAirbyteCatalog,
    ConfiguredAirbyteStream,
    DestinationSyncMode,
    SyncMode,
)
from airbyte_cdk.models import Type as MessageType
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


@dataclasses.dataclass
class Message:
    prefix: str
    message: AirbyteMessage


@dataclasses.dataclass
class StreamStats:
    stream: str
    record_count = 0

    columns_to_diff_count = {}
    columns_to_right_missing = {}
    columns_to_left_missing = {}
    columns_to_equal = {}

    left_rows_missing = {}
    right_rows_missing = {}


async def main():
    connector = "source-stripe"
    connector_version = "4.5.4"
    config_path = "secrets/config.json"
    command = f"docker run --rm -v $(pwd)/secrets:/secrets -v $(pwd)/integration_tests:/integration_tests airbyte/{connector}:{connector_version} read --config /{config_path} --catalog /secrets/tmp_catalog.json"

    subprocess_left = run_subprocess(command, "left")
    subprocess_right = run_subprocess(command, "right")

    streams_stats = {}
    primary_key = "id"
    # FIXME: need to get pk from catalog
    streams_to_dataframe = {}

    while subprocess_left.__anext__() and subprocess_right.__anext__():
        try:
            left = await subprocess_left.__anext__()
            right = await subprocess_right.__anext__()


            if left.message.type != right.message.type:
                print(f"Type mismatch: {left.message.type} != {right.message.type}")
                print(left)
                print()
                print(right)
                print(left.message.type == right.message.type)
                return
            if left.message.type == MessageType.RECORD:

                assert left.message.record.stream == right.message.record.stream
                if left.message.record.stream not in streams_stats:
                    streams_stats[left.message.record.stream] = StreamStats(left.message.record.stream)

                stream_stats = streams_stats[left.message.record.stream]

                stream_stats.record_count += 1
                if left.message.record.data[primary_key] != right.message.record.data[primary_key]:
                    stream_stats.left_rows_missing[left.message.record.data[primary_key]] = left
                    stream_stats.right_rows_missing[right.message.record.data[primary_key]] = right

                compare_records(left, right, stream_stats)

                if left.message.record.data != right.message.record.data:
                    print(f"Data mismatch: {left.message.record.data} != {right.message.record.data}")

                left_keys = set(stream_stats.left_rows_missing.keys())
                for left_key in left_keys:
                    print(f"missinh {left_key}")
                    if left_key in stream_stats.right_rows_missing:
                        print(f"found {left_key} in right")
                        compare_records(stream_stats.left_rows_missing[left_key], stream_stats.right_rows_missing[left_key], stream_stats)
                        stream_stats.left_rows_missing.pop(left_key)
                        stream_stats.right_rows_missing.pop(left_key)
                    else:
                        print(f"did not find {left_key} in right")
        except StopAsyncIteration:
            #FIXME needd to do another check of missing
            # FIXME need to check if both are done
            for stream_stats in streams_stats.values():
                stats_rows = []
                for column in stream_stats.columns_to_diff_count:
                    stats_rows.append(
                        {
                            "stream": stream_stats.stream,
                            "column": column,
                            "metric": "diff_count",
                            "value": stream_stats.columns_to_diff_count[column],
                        }
                    )
                for column in stream_stats.columns_to_equal:
                    stats_rows.append(
                        {
                            "stream": stream_stats.stream,
                            "column": column,
                            "metric": "equal_count",
                            "value": stream_stats.columns_to_equal[column],
                        }
                    )
                df = pd.DataFrame.from_records(stats_rows)
                streams_to_dataframe[stream_stats.stream] = df
                print(f"done processing {stream_stats.record_count} records")
                print(f"columns_to_diff_count: {stream_stats.columns_to_diff_count}")
                print(f"columns_to_right_missing: {stream_stats.columns_to_right_missing}")
                print(f"columns_to_left_missing: {stream_stats.columns_to_left_missing}")
                print(f"columns_to_equal: {stream_stats.columns_to_equal}")
                # NEED TO VERIFY BOTH ARE DONE

                print(f"left_rows_missing: {stream_stats.left_rows_missing}")
                print(len(stream_stats.left_rows_missing))

                print(f"right_rows_missing: {stream_stats.right_rows_missing}")
                print(len(stream_stats.right_rows_missing))

            break
    generate_plots_single_pdf_per_metric(streams_to_dataframe)

def generate_plots_single_pdf_per_metric(streams_to_dataframe, output_filename='plots_combined_per_metric.pdf'):
    with PdfPages(output_filename) as pdf:

        # Generate summary
        # TODO

        # Generate per stream-column tables
        for stream, group_data in streams_to_dataframe.items():
            grouped = group_data.groupby('column')
            for column, group_data in grouped:
                # Create a table for each stream and column combination
                table = pd.pivot_table(group_data, values='value', index='metric', columns='column')

                # Plotting table using matplotlib
                plt.figure(figsize=(6, 4))
                plt.table(cellText=table.values,
                          colLabels=table.columns,
                          rowLabels=table.index,
                          loc='center')
                plt.title(f"Stream: {stream}, Column: {column}")
                plt.axis('off')  # Hide axis

                # Save the table as a page in the PDF
                pdf.savefig(bbox_inches='tight', pad_inches=1)
                plt.close()

        print(f"Tables saved to {output_filename}")


def compare_records(left, right, stream_stats):
    for column, left_value in left.message.record.data.items():
        if column not in stream_stats.columns_to_diff_count:
            stream_stats.columns_to_diff_count[column] = 0
        if column not in stream_stats.columns_to_right_missing:
            stream_stats.columns_to_right_missing[column] = 0
        if column not in stream_stats.columns_to_left_missing:
            stream_stats.columns_to_left_missing[column] = 0
        if column not in stream_stats.columns_to_equal:
            stream_stats.columns_to_equal[column] = 0

        if column not in right.message.record.data:
            stream_stats.columns_to_right_missing[column] += 1
            continue
        elif left_value != right.message.record.data[column]:
            stream_stats.columns_to_diff_count[column] += 1
        else:
            stream_stats.columns_to_equal[column] += 1
    for column, right_value in right.message.record.data.items():
        if column not in stream_stats.columns_to_diff_count:
            stream_stats.columns_to_diff_count[column] = 0
        if column not in stream_stats.columns_to_right_missing:
            stream_stats.columns_to_right_missing[column] = 0
        if column not in stream_stats.columns_to_left_missing:
            stream_stats.columns_to_left_missing[column] = 0
        if column not in stream_stats.columns_to_equal:
            stream_stats.columns_to_equal[column] = 0
        if column not in left.message.record.data:
            stream_stats.columns_to_left_missing[column] += 1


async def is_next_item_available(generator):
    async for _ in asyncio.as_completed([generator.__anext__()]):
        return True


async def run_subprocess(command, suffix):
    # Create a subprocess
    process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    # Read lines from stdout asynchronously
    async def read_lines(stream):
        async for line in stream:
            yield line.decode().rstrip()

    # Start reading lines from both stdout and stderr
    stdout_lines = read_lines(process.stdout)
    stderr_lines = read_lines(process.stderr)

    # Consume lines from both streams concurrently
    async for line in stdout_lines:
        yield Message(prefix=f"{suffix}: ", message=AirbyteMessage.parse_raw(line))

    # # Wait for the process to finish
    # await process.wait()


if __name__ == "__main__":
    asyncio.run(main())
