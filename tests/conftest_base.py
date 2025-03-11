from collections import namedtuple
from functools import cached_property
from itertools import starmap

import boa
import pytest
import vyper
from boa.contracts.event_decoder import RawLogEntry
from boa.contracts.vyper.vyper_contract import VyperContract
from web3 import Web3

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def get_last_event(contract: VyperContract, name: str | None = None):
    matching_events = [
        e
        for e in contract.get_logs(strict=False)
        if not isinstance(e, RawLogEntry) and (name is None or name == type(e).__name__)
    ]
    return EventWrapper(matching_events[-1])


def get_events(contract: VyperContract, name: str | None = None):
    return [
        EventWrapper(e)
        for e in contract.get_logs(strict=False)
        if not isinstance(e, RawLogEntry) and (name is None or name == type(e).__name__)
    ]


class EventWrapper:
    def __init__(self, event: namedtuple):  # noqa: PYI024
        self.event = event
        self.event_name = type(event).__name__
        self.args_dict = event._asdict()
        print(f"EventWrapper {self.event_name=} {self.args_dict=}")

    def __getattr__(self, name):
        if name in self.args_dict:
            return self.args_dict[name]
        raise AttributeError(f"No attr {name} in {self.event_name}. Event data is {self.event}")

    def __repr__(self):
        return f"<EventWrapper {self.event_name} {self.args_dict}>"


# TODO: find a better way to do this. also would be useful to get structs attrs by name
def checksummed(obj, vyper_type=None):
    if vyper_type is None and hasattr(obj, "_vyper_type"):
        vyper_type = obj._vyper_type
    print(f"checksummed {obj=} {vyper_type=} {type(obj).__name__=} {type(vyper_type)=}")

    if isinstance(vyper_type, vyper.codegen.types.types.DArrayType):
        return [checksummed(x, vyper_type.subtype) for x in obj]

    if isinstance(vyper_type, vyper.codegen.types.types.StructType):
        return tuple(starmap(checksummed, zip(obj, vyper_type.tuple_members())))

    if isinstance(vyper_type, vyper.codegen.types.types.BaseType):
        if vyper_type.typ == "address":
            return Web3.toChecksumAddress(obj)
        if vyper_type.typ == "bytes32":
            return f"0x{obj.hex()}"

    return obj
