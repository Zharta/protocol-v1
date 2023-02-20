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



def get_last_event(contract: boa.vyper.contract.VyperContract, name: str = None):
    matching_events = [e for e in contract.get_logs() if name is None or name == e.event_type.name]
    return EventWrapper(matching_events[-1])


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
        # print(f"build event args {dict(_args)}")

        return {k: self._format_value(v, self.event.event_type.arguments[k]) for k, v in _args}

    def _format_value(self, v, _type):
        if isinstance(_type, vyper.semantics.types.value.address.AddressDefinition):
            return Web3.toChecksumAddress(v)
        return v
