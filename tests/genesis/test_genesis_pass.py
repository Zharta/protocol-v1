import boa
import pytest

from hypothesis import settings
from hypothesis import strategies as st

from hypothesis.stateful import RuleBasedStateMachine, rule, initialize
from boa.test import strategy


@pytest.fixture
def genesis(genesis_contract):
    with boa.env.anchor():
        yield genesis_contract


class StatefulGenesisPass(RuleBasedStateMachine):
    token_id_st = st.integers(min_value=0, max_value=200)
    account_st = strategy("address")

    def __init__(self):
        super().__init__()

    @initialize(owner=account_st)
    def setup(self, owner):
        self.owner = owner
        self.genesis = boa.load("contracts/GenesisPass.vy", owner)
        self.distributor = genesis.ownerOf(1)
        self.tokens = {id: self.distributor for id in range(1, genesis.totalSupply() + 1)}
        print(f"{self.owner=} {self.distributor=}")

    @rule(token_id=token_id_st, distributor=account_st, receiver=account_st)
    def rule_transfer(self, token_id, distributor, receiver):
        if self.tokens.get(token_id) == distributor:
            self.genesis_contract.transferFrom(distributor, receiver, token_id, sender=distributor)
            assert self.genesis_contract.ownerOf(token_id) == receiver
            self.tokens[token_id] = receiver
        else:
            with boa.reverts():
                self.genesis_contract.transferFrom(distributor, receiver, token_id, sender=distributor)

    def invariant_total_supply(self):
        assert self.genesis_contract.totalSupply() == len(self.tokens)

    def invariant_ownership(self):
        for token, owner in self.tokens.items():
            assert self.genesis_contract.ownerOf(token) == owner


# StatefulGenesisPass.TestCase.settings = settings(max_examples=3, stateful_step_count=20)
TestGenesis = StatefulGenesisPass.TestCase


# def test_stateful_genesis_pass(genesis, accounts, contract_owner):
#     state_machine(StatefulGenesisPass, genesis, accounts)
