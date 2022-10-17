# The MIT License (MIT)
# Copyright (c) 2022 Gamejam.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial
# portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from solana.rpc.api import Client
from solanaetl.services.graph_operations import (GraphOperations,
                                                 OutOfBoundsError, Point)


class SolanaService(object):
    def __init__(self, client: Client) -> None:
        graph = BlockTimestampGraph(client)
        self._graph_operations = GraphOperations(graph)

    def get_block_range_for_timestamps(self, start_timestamp, end_timestamp):
        start_timestamp = int(start_timestamp)
        end_timestamp = int(end_timestamp)
        if start_timestamp > end_timestamp:
            raise ValueError(
                'start_timestamp must be greater or equal to end_timestamp')

        try:
            start_block_bounds = self._graph_operations.get_bounds_for_y_coordinate(
                start_timestamp)
        except OutOfBoundsError:
            start_block_bounds = (0, 0)

        try:
            end_block_bounds = self._graph_operations.get_bounds_for_y_coordinate(
                end_timestamp)
        except OutOfBoundsError as e:
            raise OutOfBoundsError(
                'The existing blocks do not completely cover the given time range') from e

        if start_block_bounds == end_block_bounds and start_block_bounds[0] != start_block_bounds[1]:
            raise ValueError(
                'The given timestamp range does not cover any blocks')

        start_block = start_block_bounds[1]
        end_block = end_block_bounds[0]

        # The genesis block has timestamp 0 but we include it with the 1st block.
        if start_block == 1:
            start_block = 0

        return start_block, end_block


class BlockTimestampGraph(object):
    def __init__(self, client: Client):
        self._client = client

    def get_first_point(self):
        # Ignore the genesis block as its timestamp is 0
        return Point(1, self._get_block_timestamp(1))

    def get_last_point(self):
        latest_block = self._client.get_latest_blockhash().get(
            'result').get('context').get('slot')
        return Point(latest_block, self._get_block_timestamp(latest_block))

    def get_point(self, x):
        return Point(x, self._get_block_timestamp(x))

    def _get_block_timestamp(self, x):
        timestamp = self._client.get_block_time(x).get('result')
        return timestamp if timestamp is not None else 0
