import pytest
import boa
import vyper
import os
from web3 import Web3
from functools import cached_property


boa.interpret.set_cache_dir()
boa.env.enable_gas_profiling()
boa.reset_env()
boa.env.fork(url=os.environ["BOA_FORK_RPC_URL"])


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def get_last_event(contract: boa.vyper.contract.VyperContract, name: str = None):
    matching_events = [e for e in contract.get_logs() if isinstance(e, boa.vyper.event.Event) and (name is None or name == e.event_type.name)]
    return EventWrapper(matching_events[-1])


def get_events(contract: boa.vyper.contract.VyperContract, name: str = None):
    return [EventWrapper(e) for e in contract.get_logs() if isinstance(e, boa.vyper.event.Event) and (name is None or name == e.event_type.name)]


class EventWrapper():

    def __init__(self, event: boa.vyper.event.Event):
        self.event = event
        self.event_name = event.event_type.name

    def __getattr__(self, name):
        if name in self.args_dict:
            return self.args_dict[name]
        else:
            raise AttributeError(f"No attr {name} in {self.event_name}. Event data is {self.event}")

    @cached_property
    def args_dict(self):
        # print(f"{self.event=} {self.event.event_type.arguments=}")
        args = self.event.event_type.arguments.keys()
        indexed = self.event.event_type.indexed
        topic_values = (v for v in self.event.topics)
        args_values = (v for v in self.event.args)
        _args = [(arg, next(topic_values) if indexed[i] else next(args_values)) for i, arg in enumerate(args)]

        return {k: self._format_value(v, self.event.event_type.arguments[k]) for k, v in _args}

    def _format_value(self, v, _type):
        # print(f"_format_value {v=} {_type=} {type(v).__name__=} {type(_type)=}")
        if isinstance(_type, vyper.semantics.types.value.address.AddressDefinition):
            return Web3.toChecksumAddress(v)
        elif isinstance(_type, vyper.semantics.types.value.bytes_fixed.Bytes32Definition):
            return f"0x{v.hex()}"
        return v


# TODO: find a better way to do this. also would be useful to get structs attrs by name
def checksummed(obj, vyper_type=None):
    if vyper_type is None and hasattr(obj, "_vyper_type"):
        vyper_type = obj._vyper_type
    print(f"checksummed {obj=} {vyper_type=} {type(obj).__name__=} {type(vyper_type)=}")

    if isinstance(vyper_type, vyper.codegen.types.types.DArrayType):
        return list(checksummed(x, vyper_type.subtype) for x in obj)

    elif isinstance(vyper_type, vyper.codegen.types.types.StructType):
        return tuple(checksummed(*arg) for arg in zip(obj, vyper_type.tuple_members()))

    elif isinstance(vyper_type, vyper.codegen.types.types.BaseType):
        if vyper_type.typ == 'address':
            return Web3.toChecksumAddress(obj)
        elif vyper_type.typ == 'bytes32':
            return f"0x{obj.hex()}"

    return obj
