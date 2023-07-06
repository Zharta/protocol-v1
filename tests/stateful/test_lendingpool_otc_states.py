import boa
import pytest

import hypothesis.strategies as st
from hypothesis import Verbosity, Phase, settings
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule, run_state_machine_as_test
from dataclasses import dataclass


DEPLOYER = boa.env.generate_address()
LENDER = boa.env.generate_address()

PROTOCOL_WALLET = boa.env.generate_address()
PROTOCOL_FEE = 100  # bps


@dataclass
class PoolState():
    deposits: int = 0
    withdrawals: int = 0
    invested: int = 0
    received: int = 0
    claims_value: int = 0
    pool_rewards: int = 0
    protocol_rewards: int = 0


@pytest.fixture(scope="module")
def erc20_token(weth9_contract):
    with boa.env.prank(DEPLOYER):
        contract = weth9_contract.deploy("ERC20", "ERC20", 18, 10**20)
        boa.env.set_balance(contract.address, 10**20)
        return contract


@pytest.fixture(scope="module")
def weth_pool(lendingpool_otc_contract, erc20_token):
    with boa.env.prank(DEPLOYER):
        contract = lendingpool_otc_contract.deploy(erc20_token.address, True)
        proxy_address = contract.create_proxy(PROTOCOL_WALLET, PROTOCOL_FEE, LENDER)
        proxy = lendingpool_otc_contract.at(proxy_address)
        proxy.setLoansPeripheralAddress(boa.env.generate_address())
        proxy.setLiquidationsPeripheralAddress(boa.env.generate_address())
        return proxy


@pytest.fixture(scope="module")
def erc20_pool(lendingpool_otc_contract, erc20_token):
    with boa.env.prank(DEPLOYER):
        contract = lendingpool_otc_contract.deploy(erc20_token.address, False)
        proxy_address = contract.create_proxy(PROTOCOL_WALLET, PROTOCOL_FEE, LENDER)
        proxy = lendingpool_otc_contract.at(proxy_address)
        proxy.setLoansPeripheralAddress(boa.env.generate_address())
        proxy.setLiquidationsPeripheralAddress(boa.env.generate_address())
        return proxy


class StateMachine(RuleBasedStateMachine):
    weth_pool = None
    erc20_pool = None
    erc20_token = None

    @initialize()
    def setup(self):
        self.eth = PoolState()
        self.erc20 = PoolState()

        self.borrower = boa.env.generate_address()
        boa.env.set_balance(self.borrower, 10**50)
        self.erc20_token.eval(f"self.balanceOf[{self.borrower}] = {10**50}")

        self.lender_initial_eth = 10**50
        self.lender_initial_erc20 = 10**50
        boa.env.set_balance(LENDER, self.lender_initial_eth)
        self.erc20_token.eval(f"self.balanceOf[{LENDER}] = {self.lender_initial_erc20}")

    @rule(amount=st.integers(min_value=1, max_value=10**20))
    def deposit_eth(self, amount):
        self.weth_pool.depositEth(value=amount, sender=LENDER)
        self.eth.deposits += amount

    @rule(amount=st.integers(min_value=1, max_value=10**20))
    def deposit_erc20(self, amount):
        self.erc20_token.approve(self.erc20_pool.address, amount, sender=LENDER)
        self.erc20_pool.deposit(amount, sender=LENDER)
        self.erc20.deposits += amount

    @rule(amount=st.integers(min_value=1, max_value=10**20))
    def withdraw_eth(self, amount):
        if amount <= self.weth_pool.fundsAvailable():
            self.weth_pool.withdrawEth(amount, sender=LENDER)
            self.eth.withdrawals += amount
        else:
            with boa.reverts():
                self.weth_pool.withdrawEth(amount, sender=LENDER)

    @rule(amount=st.integers(min_value=1, max_value=10**20))
    def withdraw_erc20(self, amount):
        if amount <= self.erc20_pool.fundsAvailable():
            self.erc20_pool.withdraw(amount, sender=LENDER)
            self.erc20.withdrawals += amount
        else:
            with boa.reverts():
                self.erc20_pool.withdraw(amount, sender=LENDER)

    @rule(amount=st.integers(min_value=1, max_value=10**20))
    def send_eth(self, amount):
        if amount <= self.weth_pool.fundsAvailable():
            self.weth_pool.sendFundsEth(self.borrower, amount, sender=self.weth_pool.loansContract())
            self.eth.invested += amount
        else:
            with boa.reverts():
                self.weth_pool.sendFundsEth(self.borrower, amount, sender=self.weth_pool.loansContract())

    @rule(amount=st.integers(min_value=1, max_value=10**20))
    def send_erc20(self, amount):
        if amount <= self.erc20_pool.fundsAvailable():
            self.erc20_pool.sendFunds(self.borrower, amount, sender=self.erc20_pool.loansContract())
            self.erc20.invested += amount
        else:
            with boa.reverts():
                self.erc20_pool.sendFunds(self.borrower, amount, sender=self.erc20_pool.loansContract())

    @rule(amount=st.integers(min_value=1, max_value=10**20), rewards=st.integers(min_value=1, max_value=10**20))
    def receive_eth(self, amount, rewards):
        loans = self.weth_pool.loansContract()
        boa.env.set_balance(loans, amount + rewards)
        if amount <= self.weth_pool.fundsInvested():
            self.weth_pool.receiveFundsEth(self.borrower, amount, rewards, value=amount + rewards, sender=loans)
            protocol_fee = rewards * self.weth_pool.protocolFeesShare() // 10000
            self.eth.received += amount
            self.eth.pool_rewards += rewards - protocol_fee
            self.eth.protocol_rewards += protocol_fee
        else:
            with boa.reverts():
                self.weth_pool.receiveFundsEth(self.borrower, amount, rewards, value=amount + rewards, sender=loans)

    @rule(amount=st.integers(min_value=1, max_value=10**20), rewards=st.integers(min_value=1, max_value=10**20))
    def receive_erc20(self, amount, rewards):
        loans = self.erc20_pool.loansContract()
        self.erc20_token.approve(self.erc20_pool, amount + rewards, sender=self.borrower)
        if amount <= self.erc20_pool.fundsInvested():
            self.erc20_pool.receiveFunds(self.borrower, amount, rewards, sender=loans)
            protocol_fee = rewards * self.erc20_pool.protocolFeesShare() // 10000
            self.erc20.received += amount
            self.erc20.pool_rewards += rewards - protocol_fee
            self.erc20.protocol_rewards += protocol_fee
        else:
            with boa.reverts():
                self.erc20_pool.receiveFunds(self.borrower, amount, rewards, sender=loans)

    @rule(
        amount=st.integers(min_value=1, max_value=10**20),
        rewards=st.integers(min_value=1, max_value=10**20),
        distribute=st.booleans(),
    )
    def receive_from_liquidation_eth(self, amount, rewards, distribute):
        liquidation = self.weth_pool.liquidationsPeripheralContract()
        boa.env.set_balance(liquidation, amount + rewards)
        if amount <= self.weth_pool.fundsInvested():
            self.weth_pool.receiveFundsFromLiquidationEth(
                self.borrower,
                amount,
                rewards,
                distribute,
                "grace",
                value=amount + rewards,
                sender=liquidation
            )
            protocol_fee = rewards * self.erc20_pool.protocolFeesShare() // 10000 if distribute else 0
            self.eth.received += amount
            self.eth.pool_rewards += rewards - protocol_fee
            self.eth.protocol_rewards += protocol_fee
        else:
            with boa.reverts():
                self.weth_pool.receiveFundsFromLiquidationEth(
                    self.borrower,
                    amount,
                    rewards,
                    distribute,
                    "grace",
                    value=amount + rewards,
                    sender=liquidation
                )

    @rule(
        amount=st.integers(min_value=1, max_value=10**20),
        rewards=st.integers(min_value=1, max_value=10**20),
        distribute=st.booleans(),
    )
    def receive_from_liquidation_erc20(self, amount, rewards, distribute):
        liquidation = self.erc20_pool.liquidationsPeripheralContract()
        self.erc20_token.approve(self.erc20_pool, amount + rewards, sender=self.borrower)
        if amount <= self.erc20_pool.fundsInvested():
            self.erc20_pool.receiveFundsFromLiquidation(self.borrower, amount, rewards, distribute, "grace", sender=liquidation)
            protocol_fee = rewards * self.erc20_pool.protocolFeesShare() // 10000 if distribute else 0
            self.erc20.received += amount
            self.erc20.pool_rewards += rewards - protocol_fee
            self.erc20.protocol_rewards += protocol_fee
        else:
            with boa.reverts():
                self.erc20_pool.receiveFundsFromLiquidation(self.borrower, amount, rewards, distribute, "grace", sender=liquidation)

    @rule(amount=st.integers(min_value=1, max_value=10**20))
    def receive_collateral_eth(self, amount):
        liquidation = self.weth_pool.liquidationsPeripheralContract()
        if amount <= self.weth_pool.fundsInvested():
            self.weth_pool.receiveCollateralFromLiquidation(self.borrower, amount, "claim", sender=liquidation)
            self.eth.claims_value += amount
        else:
            with boa.reverts():
                self.weth_pool.receiveCollateralFromLiquidation(self.borrower, amount, "claim", sender=liquidation)

    @rule(amount=st.integers(min_value=1, max_value=10**20))
    def receive_collateral_erc20(self, amount):
        liquidation = self.erc20_pool.liquidationsPeripheralContract()
        if amount <= self.erc20_pool.fundsInvested():
            self.erc20_pool.receiveCollateralFromLiquidation(self.borrower, amount, "claim", sender=liquidation)
            self.erc20.claims_value += amount
        else:
            with boa.reverts():
                self.erc20_pool.receiveCollateralFromLiquidation(self.borrower, amount, "claim", sender=liquidation)

    @invariant()
    def total_deposits(self):
        assert self.weth_pool.totalAmountDeposited(LENDER) == self.eth.deposits
        assert self.erc20_pool.totalAmountDeposited(LENDER) == self.erc20.deposits

    @invariant()
    def total_withdrawals(self):
        assert self.weth_pool.totalAmountWithdrawn(LENDER) == self.eth.withdrawals
        assert self.erc20_pool.totalAmountWithdrawn(LENDER) == self.erc20.withdrawals

    @invariant()
    def current_deposits(self):
        assert self.weth_pool.currentAmountDeposited(LENDER) == self.eth.deposits + self.eth.pool_rewards - self.eth.withdrawals
        assert self.erc20_pool.currentAmountDeposited(LENDER) == self.erc20.deposits + self.erc20.pool_rewards - self.erc20.withdrawals

    @invariant()
    def claims_value(self):
        assert self.weth_pool.collateralClaimsValue() == self.eth.claims_value
        assert self.erc20_pool.collateralClaimsValue() == self.erc20.claims_value

    @invariant()
    def funds_available(self):
        assert self.weth_pool.fundsAvailable() == self.eth.deposits + self.eth.received + self.eth.pool_rewards - self.eth.withdrawals - self.eth.invested
        assert self.erc20_pool.fundsAvailable() == self.erc20.deposits + self.erc20.received + self.erc20.pool_rewards - self.erc20.withdrawals - self.erc20.invested

    @invariant()
    def total_rewards(self):
        assert self.weth_pool.totalRewards() == self.eth.pool_rewards
        assert self.erc20_pool.totalRewards() == self.erc20.pool_rewards

    @invariant()
    def pool_state(self):
        assert self.weth_pool.totalAmountDeposited(LENDER) + self.weth_pool.totalRewards() == self.weth_pool.collateralClaimsValue() + self.weth_pool.totalAmountWithdrawn(LENDER) + self.weth_pool.fundsInvested() + self.weth_pool.fundsAvailable()
        assert self.erc20_pool.totalAmountDeposited(LENDER) + self.erc20_pool.totalRewards() == self.erc20_pool.collateralClaimsValue() + self.erc20_pool.totalAmountWithdrawn(LENDER) + self.erc20_pool.fundsInvested() + self.erc20_pool.fundsAvailable()

    @invariant()
    def lender_balance(self):
        assert boa.env.get_balance(LENDER) - self.lender_initial_eth == self.eth.withdrawals - self.eth.deposits
        assert self.erc20_token.balanceOf(LENDER) - self.lender_initial_erc20 == self.erc20.withdrawals - self.erc20.deposits

    @invariant()
    def pool_balance(self):
        assert self.weth_pool.fundsAvailable() == self.erc20_token.balanceOf(self.weth_pool.address)
        assert self.erc20_pool.fundsAvailable() == self.erc20_token.balanceOf(self.erc20_pool.address)

    def teardown(self):
        pass


def test_lendingpool_otc_states(weth_pool, erc20_pool, erc20_token):
    StateMachine.weth_pool = weth_pool
    StateMachine.erc20_pool = erc20_pool
    StateMachine.erc20_token = erc20_token
    StateMachine.TestCase.settings = settings(
        max_examples = 1000,
        stateful_step_count = 10,
        # verbosity = Verbosity.verbose,
        phases = tuple(Phase)[:Phase.shrink],
        deadline = None,
    )
    run_state_machine_as_test(StateMachine)
