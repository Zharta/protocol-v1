import boa
import pytest

from hypothesis import strategies as st

from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule, run_state_machine_as_test
from boa.test import strategy


@pytest.fixture
def owner():
    yield boa.env.generate_address()


@pytest.fixture
def genesis_contract(owner):
    return boa.load("contracts/GenesisPass.vy", owner)


class StatefulGenesisPass(RuleBasedStateMachine):
    token_id_st = st.integers(min_value=0, max_value=200)
    account_st = strategy("address")
    owner = None
    genesis = None

    @initialize()
    def setup(self):
        self.distributor = self.genesis.ownerOf(1)
        self.tokens = {id: self.distributor for id in range(1, self.genesis.totalSupply() + 1)}
        print(f"{self.owner=} {self.distributor=}")

    @rule(token_id=token_id_st, distributor=account_st, receiver=account_st)
    def rule_transfer(self, token_id, distributor, receiver):
        if self.tokens.get(token_id) == distributor:
            self.genesis.transferFrom(distributor, receiver, token_id, sender=distributor)
            assert self.genesis.ownerOf(token_id) == receiver
            self.tokens[token_id] = receiver
        else:
            with boa.reverts():
                self.genesis.transferFrom(distributor, receiver, token_id, sender=distributor)

    @invariant()
    def total_supply(self):
        assert self.genesis.totalSupply() == len(self.tokens)

    @invariant()
    def ownership(self):
        for token, owner in self.tokens.items():
            assert self.genesis.ownerOf(token) == owner


def test_genesis_contract(genesis_contract, owner):
    StatefulGenesisPass.owner = owner
    StatefulGenesisPass.genesis = genesis_contract
    run_state_machine_as_test(StatefulGenesisPass)
