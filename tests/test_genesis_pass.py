import datetime as dt
import brownie
import time

from brownie.test import given, strategy
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.strategies import sampled_from
from brownie.network import chain
from decimal import Decimal
from web3 import Web3

import pytest
from eth_account.messages import SignableMessage, HexBytes
from eth_account import Account
from eth_utils import keccak
from eth_abi import encode_abi

from hypothesis.stateful import rule, precondition, RuleBasedStateMachine, run_state_machine_as_test, rule, invariant

class StatefulGenesisPass(RuleBasedStateMachine):
    token_id_st = st.integers(min_value=0, max_value=200)
    account_st = strategy('address')

    def __init__(cls, GenesisPass, accounts):
        cls.accounts = accounts
        cls.GenesisPass = GenesisPass


    def setup(self):
        self.owner = self.accounts[0]
        self.distributor = self.accounts[1]
        self.genesis_contract = self.GenesisPass.deploy(self.distributor, {'from': self.owner})
        self.tokens = {id: self.distributor for id in range(1, 101)}
        print(f"{self.owner=} {self.distributor=}")

    def rule_transfer(self, token_id="token_id_st", distributor="account_st", receiver="account_st"):
        if self.tokens.get(token_id) == distributor:
            tx = self.genesis_contract.transferFrom(distributor, receiver, token_id, {'from': distributor})
            assert self.genesis_contract.ownerOf(token_id) == receiver
            self.tokens[token_id] = receiver
        else:
            with brownie.reverts():
                self.genesis_contract.transferFrom(distributor, receiver, token_id, {'from': distributor})

    def invariant_total_supply(self):
        assert self.genesis_contract.totalSupply() == len(self.tokens)

    def invariant_ownership(self):
        for token, owner in self.tokens.items():
            assert self.genesis_contract.ownerOf(token) == owner



def test_stateful_genesis_pass(GenesisPass, accounts, contract_owner, state_machine):
    StatefulGenesisPass.TestCase.settings = settings(max_examples=3, stateful_step_count=20)
    state_machine(StatefulGenesisPass, GenesisPass, accounts)
