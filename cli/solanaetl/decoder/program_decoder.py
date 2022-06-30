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


import logging
from abc import abstractmethod
from inspect import isfunction, signature
from typing import Any, Callable

from base58 import b58decode


class ProgramDecoder(object):
    def __init__(self, name: str, can_decode=False) -> None:
        self.name = name
        self.can_decode = can_decode

    @abstractmethod
    def discrim(self) -> Callable[[bytes, int], tuple[int, int]]:
        """
        :return: buffer layout lambda (u32, u64,...)
        """
        raise NotImplementedError

    @abstractmethod
    def instruction(self, discrim: int) -> str:
        """
        :param discrim: instruction index
        :return: instruction name 
        """
        raise NotImplementedError

    @abstractmethod
    def params(self) -> dict[int, dict[str, Any]]:
        """
        :return: instruction unpack params (ordered)
        """
        raise NotImplementedError

    def decode(self, b58_data: str, accounts: list[str] = [], initial_offset: int = 0) -> tuple[str, dict[str, object]]:
        """
        :return: instruction name, decoded params
        """
        data = b58decode(b58_data.encode())
        # some program have the first bytes is versioned bytes, we should remove them before decode
        data = data[initial_offset:]
        # decoding params must be ordered and start from bytes 0
        offset = 0
        # decode instruction index
        discrim, offset = self.discrim()(data, offset)
        decoded_params = {}
        for property, handler in self.params().get(discrim).items():
            if isfunction(handler):
                params = signature(handler).parameters
                if len(params) == 2:
                    # decode bytes buffer
                    decoded_params[property], offset = handler(data, offset)
                elif len(params) == 1:
                    # decode accounts
                    decoded_params[property] = handler(accounts)
                else:
                    decoded_params[property] = handler()
            else:
                decoded_params[property] = handler

        if offset != len(data):
            logging.warning(
                f"Decoded data of intruction {self.instruction(discrim)} of {self.name} not fit to original data\texpected = {len(data)}\tactual = {offset}")

        return self.instruction(discrim), decoded_params
