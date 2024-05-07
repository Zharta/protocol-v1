import boa
import pytest
from web3 import Web3

from ..conftest_base import ZERO_ADDRESS

LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


@pytest.fixture(scope="module", autouse=True)
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def investor():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def erc20(weth9_contract, contract_owner):
    with boa.env.prank(contract_owner):
        contract = weth9_contract.deploy("ERC20", "ERC20", 18, 10**20)
        boa.env.set_balance(contract.address, 10**20)
        return contract


@pytest.fixture(scope="module")
def lending_pool_core(lendingpool_core_contract, erc20, contract_owner):
    with boa.env.prank(contract_owner):
        return lendingpool_core_contract.deploy(erc20)


def user_balance(token, user):
    return token.balanceOf(user)


def test_deposit_wrong_sender(lending_pool_core, investor, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core.deposit(investor, investor, 0, sender=borrower)


def test_deposit(lending_pool_core, erc20, investor, contract_owner):
    lending_pool_peripheral = boa.env.generate_address()
    lending_pool_core.setLendingPoolPeripheralAddress(lending_pool_peripheral, sender=contract_owner)
    deposit_amount = Web3.to_wei(1, "ether")

    erc20.mint(lending_pool_peripheral, deposit_amount, sender=contract_owner)
    erc20.approve(lending_pool_core, deposit_amount, sender=lending_pool_peripheral)

    deposit_result = lending_pool_core.deposit(
        investor, lending_pool_peripheral, deposit_amount, sender=lending_pool_peripheral
    )
    assert deposit_result

    investor_funds = lending_pool_core.funds(investor)
    assert investor_funds[0] == deposit_amount
    assert investor_funds[1] == deposit_amount
    assert investor_funds[2] == 0
    assert investor_funds[3] == deposit_amount
    assert investor_funds[4] is True

    assert lending_pool_core.fundsAvailable() == deposit_amount
    assert lending_pool_core.activeLenders() == 1
    assert lending_pool_core.knownLenders(investor)
    assert lending_pool_core.lendersArray() == [investor]
    assert lending_pool_core.totalSharesBasisPoints() == deposit_amount


def test_deposit_twice(lending_pool_core, erc20, investor, contract_owner):
    lending_pool_peripheral = boa.env.generate_address()
    lending_pool_core.setLendingPoolPeripheralAddress(lending_pool_peripheral, sender=contract_owner)
    deposit_amount_one = Web3.to_wei(1, "ether")
    deposit_amount_two = Web3.to_wei(0.5, "ether")

    erc20.transfer(lending_pool_peripheral, deposit_amount_one + deposit_amount_two, sender=contract_owner)
    erc20.approve(lending_pool_core, deposit_amount_one + deposit_amount_two, sender=lending_pool_peripheral)

    lending_pool_core.deposit(investor, lending_pool_peripheral, deposit_amount_one, sender=lending_pool_peripheral)
    lending_pool_core.deposit(investor, lending_pool_peripheral, deposit_amount_two, sender=lending_pool_peripheral)

    investor_funds = lending_pool_core.funds(investor)
    assert investor_funds[0] == deposit_amount_one + deposit_amount_two
    assert investor_funds[1] == deposit_amount_one + deposit_amount_two
    assert investor_funds[3] == deposit_amount_one + deposit_amount_two

    assert lending_pool_core.fundsAvailable() == deposit_amount_one + deposit_amount_two
    assert lending_pool_core.activeLenders() == 1
    assert lending_pool_core.knownLenders(investor)
    assert lending_pool_core.lendersArray() == [investor]
    assert lending_pool_core.totalSharesBasisPoints() == deposit_amount_one + deposit_amount_two


def test_withdraw_wrong_sender(lending_pool_core, investor, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core.withdraw(investor, investor, 100, sender=borrower)


def test_withdraw_lender_zeroaddress(lending_pool_core, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    with boa.reverts("The _lender is the zero address"):
        lending_pool_core.withdraw(ZERO_ADDRESS, lending_pool_core, 100, sender=lending_pool_peripheral)


def test_withdraw_receiver_zeroaddress(lending_pool_core, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    with boa.reverts("The _wallet is the zero address"):
        lending_pool_core.withdraw(lending_pool_core, ZERO_ADDRESS, 100, sender=lending_pool_peripheral)


def test_withdraw_noinvestment(lending_pool_core, investor, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    with boa.reverts("_amount more than withdrawable"):
        lending_pool_core.withdraw(investor, investor, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral)


def test_withdraw_insufficient_investment(lending_pool_core, erc20, investor, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    deposit_amount = Web3.to_wei(1, "ether")

    erc20.mint(investor, deposit_amount, sender=contract_owner)
    erc20.approve(lending_pool_core, deposit_amount, sender=investor)

    lending_pool_core.deposit(investor, investor, deposit_amount, sender=lending_pool_peripheral)
    amount = int(deposit_amount * 1.5)

    with boa.reverts("_amount more than withdrawable"):
        lending_pool_core.withdraw(investor, investor, amount, sender=lending_pool_peripheral)


def test_withdraw_with_losses(lending_pool_core, erc20, borrower, investor, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    deposit_amount = Web3.to_wei(1, "ether")
    invested_amount = Web3.to_wei(0.5, "ether")
    recovered_amount = Web3.to_wei(0.4, "ether")

    erc20.mint(investor, deposit_amount, sender=contract_owner)
    erc20.approve(lending_pool_core, deposit_amount, sender=investor)

    lending_pool_core.deposit(investor, investor, deposit_amount, sender=lending_pool_peripheral)
    lending_pool_core.sendFunds(borrower, invested_amount, sender=lending_pool_peripheral)

    erc20.approve(lending_pool_core, recovered_amount, sender=borrower)
    lending_pool_core.receiveFunds(borrower, recovered_amount, 0, invested_amount, sender=lending_pool_peripheral)
    with boa.reverts("_amount more than withdrawable"):
        lending_pool_core.withdraw(investor, investor, deposit_amount, sender=lending_pool_peripheral)

    lending_pool_core.withdraw(
        investor, investor, deposit_amount - (invested_amount - recovered_amount), sender=lending_pool_peripheral
    )


def test_withdraw(lending_pool_core, erc20, investor, contract_owner):
    lending_pool_peripheral = boa.env.generate_address()
    lending_pool_core.setLendingPoolPeripheralAddress(lending_pool_peripheral, sender=contract_owner)
    deposit_amount = Web3.to_wei(2, "ether")
    withdraw_amount = Web3.to_wei(1, "ether")

    initial_balance = user_balance(erc20, investor)

    erc20.transfer(lending_pool_peripheral, deposit_amount, sender=contract_owner)
    erc20.approve(lending_pool_core, deposit_amount, sender=lending_pool_peripheral)

    lending_pool_core.deposit(investor, lending_pool_peripheral, deposit_amount, sender=lending_pool_peripheral)
    assert user_balance(erc20, investor) == initial_balance
    assert lending_pool_core.fundsAvailable() == deposit_amount

    lending_pool_core.withdraw(investor, investor, withdraw_amount, sender=lending_pool_peripheral)

    assert user_balance(erc20, investor) == initial_balance + withdraw_amount
    assert lending_pool_core.fundsAvailable() == deposit_amount - withdraw_amount

    investor_funds = lending_pool_core.funds(investor)
    assert investor_funds[0] == deposit_amount - withdraw_amount
    assert investor_funds[1] == deposit_amount
    assert investor_funds[2] == withdraw_amount
    assert investor_funds[4]

    assert lending_pool_core.activeLenders() == 1
    assert lending_pool_core.knownLenders(investor)
    assert lending_pool_core.lendersArray() == [investor]


def test_deposit_withdraw_deposit(lending_pool_core, erc20, investor, contract_owner):
    lending_pool_peripheral = boa.env.generate_address()
    lending_pool_core.setLendingPoolPeripheralAddress(lending_pool_peripheral, sender=contract_owner)
    initial_balance = user_balance(erc20, investor)

    erc20.transfer(investor, Web3.to_wei(2, "ether"), sender=contract_owner)
    assert user_balance(erc20, investor) == initial_balance + Web3.to_wei(2, "ether")

    erc20.transfer(lending_pool_peripheral, Web3.to_wei(1, "ether"), sender=investor)
    erc20.approve(lending_pool_core, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral)

    lending_pool_core.deposit(investor, lending_pool_peripheral, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral)
    assert lending_pool_core.fundsAvailable() == Web3.to_wei(1, "ether")

    lending_pool_core.withdraw(investor, investor, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral)

    assert user_balance(erc20, investor) == initial_balance + Web3.to_wei(2, "ether")
    assert lending_pool_core.fundsAvailable() == 0

    investor_funds = lending_pool_core.funds(investor)
    assert investor_funds[0] == 0
    assert investor_funds[1] == Web3.to_wei(1, "ether")
    assert investor_funds[2] == Web3.to_wei(1, "ether")
    assert investor_funds[4] is False

    assert lending_pool_core.activeLenders() == 0
    assert lending_pool_core.knownLenders(investor)
    assert lending_pool_core.lendersArray() == [investor]

    erc20.transfer(lending_pool_peripheral, Web3.to_wei(1, "ether"), sender=investor)
    erc20.approve(lending_pool_core, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral)
    lending_pool_core.deposit(investor, lending_pool_peripheral, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral)
    assert user_balance(erc20, investor) == initial_balance + Web3.to_wei(1, "ether")
    assert lending_pool_core.fundsAvailable() == Web3.to_wei(1, "ether")

    investor_funds2 = lending_pool_core.funds(investor)
    assert investor_funds2[0] == Web3.to_wei(1, "ether")
    assert investor_funds2[1] == Web3.to_wei(2, "ether")
    assert investor_funds2[2] == Web3.to_wei(1, "ether")
    assert investor_funds2[3] == Web3.to_wei(1, "ether")
    assert investor_funds2[4] is True

    assert lending_pool_core.fundsAvailable() == Web3.to_wei(1, "ether")
    assert lending_pool_core.activeLenders() == 1
    assert lending_pool_core.knownLenders(investor)
    assert lending_pool_core.lendersArray() == [investor]
    assert lending_pool_core.totalSharesBasisPoints() == Web3.to_wei(1, "ether")


def test_send_funds_wrong_sender(lending_pool_core, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core.sendFunds(borrower, Web3.to_wei(1, "ether"), sender=borrower)


def test_send_funds_zero_amount(lending_pool_core, borrower, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    with boa.reverts("_amount has to be higher than 0"):
        lending_pool_core.sendFunds(borrower, Web3.to_wei(0, "ether"), sender=lending_pool_peripheral)


def test_send_funds_insufficient_balance(lending_pool_core, erc20, contract_owner, investor, borrower):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    erc20.mint(investor, Web3.to_wei(1, "ether"), sender=contract_owner)
    erc20.approve(lending_pool_core, Web3.to_wei(1, "ether"), sender=investor)

    lending_pool_core.deposit(investor, investor, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral)

    with boa.reverts("Insufficient balance"):
        lending_pool_core.sendFunds(borrower, Web3.to_wei(1.1, "ether"), sender=lending_pool_peripheral)


def test_send_funds(lending_pool_core, erc20, contract_owner, investor, borrower):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    deposit_amount = Web3.to_wei(1, "ether")
    initial_balance = user_balance(erc20, borrower)

    erc20.mint(investor, deposit_amount, sender=contract_owner)
    erc20.approve(lending_pool_core, deposit_amount, sender=investor)
    lending_pool_core.deposit(investor, investor, deposit_amount, sender=lending_pool_peripheral)

    lending_pool_core.sendFunds(borrower, Web3.to_wei(0.2, "ether"), sender=lending_pool_peripheral)

    assert user_balance(erc20, borrower) == initial_balance + Web3.to_wei(0.2, "ether")
    assert lending_pool_core.fundsAvailable() == Web3.to_wei(0.8, "ether")
    assert lending_pool_core.fundsInvested() == Web3.to_wei(0.2, "ether")


def test_receive_funds_wrong_sender(lending_pool_core, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core.receiveFunds(
            borrower, Web3.to_wei(0.2, "ether"), Web3.to_wei(0.05, "ether"), Web3.to_wei(0.2, "ether"), sender=borrower
        )


def test_receive_funds_zero_value(lending_pool_core, borrower, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    with boa.reverts("Amount has to be higher than 0"):
        lending_pool_core.receiveFunds(
            borrower, Web3.to_wei(0, "ether"), Web3.to_wei(0, "ether"), Web3.to_wei(0, "ether"), sender=lending_pool_peripheral
        )


def test_transfer_protocol_fees_wrong_sender(lending_pool_core, contract_owner, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core.transferProtocolFees(borrower, contract_owner, Web3.to_wei(0.2, "ether"), sender=borrower)


def test_transfer_protocol_fees_zero_value(lending_pool_core, contract_owner, borrower):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    with boa.reverts("_amount should be higher than 0"):
        lending_pool_core.transferProtocolFees(
            borrower, contract_owner, Web3.to_wei(0, "ether"), sender=lending_pool_peripheral
        )


def test_transfer_protocol_fees(lending_pool_core, erc20, contract_owner, borrower):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    amount = Web3.to_wei(1, "ether")

    erc20.transfer(borrower, amount, sender=contract_owner)
    erc20.approve(lending_pool_core, amount, sender=borrower)

    contract_owner_balance = user_balance(erc20, contract_owner)
    assert user_balance(erc20, lending_pool_core) == 0

    lending_pool_core.transferProtocolFees(borrower, contract_owner, amount, sender=lending_pool_peripheral)

    assert user_balance(erc20, lending_pool_core) == 0
    assert user_balance(erc20, contract_owner) == contract_owner_balance + amount


def test_receive_funds(lending_pool_core, erc20, investor, borrower, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    deposit_amount = Web3.to_wei(1, "ether")
    protocol_fees_share = 100

    erc20.mint(investor, deposit_amount, sender=contract_owner)
    erc20.approve(lending_pool_core, deposit_amount, sender=investor)
    lending_pool_core.deposit(investor, investor, deposit_amount, sender=lending_pool_peripheral)

    lending_pool_core.sendFunds(borrower, Web3.to_wei(0.2, "ether"), sender=lending_pool_peripheral)

    investment_amount = Web3.to_wei(0.2, "ether")
    rewards_amount = Web3.to_wei(0.02, "ether")
    pool_rewards_amount = rewards_amount * (10000 - protocol_fees_share) // 10000

    erc20.mint(borrower, rewards_amount, sender=contract_owner)
    erc20.approve(lending_pool_core, investment_amount + rewards_amount, sender=borrower)

    initial_balance = user_balance(erc20, lending_pool_core)

    lending_pool_core.receiveFunds(
        borrower, investment_amount, pool_rewards_amount, investment_amount, sender=lending_pool_peripheral
    )

    assert user_balance(erc20, lending_pool_core) == initial_balance + investment_amount + pool_rewards_amount

    assert lending_pool_core.fundsAvailable() == deposit_amount + pool_rewards_amount
    assert lending_pool_core.fundsInvested() == 0

    assert lending_pool_core.totalRewards() == pool_rewards_amount
    assert lending_pool_core.totalSharesBasisPoints() == deposit_amount

    assert lending_pool_core.funds(contract_owner)[3] == 0
    assert lending_pool_core.computeWithdrawableAmount(investor) == deposit_amount + pool_rewards_amount


def test_receive_funds_with_losses(lending_pool_core, erc20, investor, borrower, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    deposit_amount = Web3.to_wei(1, "ether")
    erc20.eval(f"self.balanceOf[{lending_pool_core.address}] = {10**18}")

    erc20.mint(investor, deposit_amount, sender=contract_owner)
    erc20.approve(lending_pool_core, deposit_amount, sender=investor)
    lending_pool_core.deposit(investor, investor, deposit_amount, sender=lending_pool_peripheral)

    lending_pool_core.sendFunds(borrower, Web3.to_wei(0.6, "ether"), sender=lending_pool_peripheral)

    investment_amount = Web3.to_wei(0.6, "ether")
    rewards_amount = Web3.to_wei(0, "ether")
    recovered_amount = Web3.to_wei(0.4, "ether")
    protocol_fees_share = 100
    pool_rewards_amount = rewards_amount * (10000 - protocol_fees_share) // 10000

    erc20.approve(lending_pool_core.address, recovered_amount, sender=borrower)

    initial_balance = user_balance(erc20, lending_pool_core.address)

    assert lending_pool_core.fundsAvailable() == deposit_amount - investment_amount
    assert lending_pool_core.fundsInvested() == investment_amount

    lending_pool_core.receiveFunds(
        borrower, recovered_amount, pool_rewards_amount, investment_amount, sender=lending_pool_peripheral
    )

    assert user_balance(erc20, lending_pool_core.address) == initial_balance + recovered_amount

    assert lending_pool_core.fundsAvailable() == deposit_amount - investment_amount + recovered_amount
    assert lending_pool_core.fundsInvested() == 0

    assert lending_pool_core.totalRewards() == pool_rewards_amount
    assert lending_pool_core.totalSharesBasisPoints() == deposit_amount

    assert lending_pool_core.funds(investor)[3] == deposit_amount
    assert lending_pool_core.funds(contract_owner)[3] == 0

    assert lending_pool_core.computeWithdrawableAmount(investor) == deposit_amount - investment_amount + recovered_amount


def test_withdrawable_precision(lending_pool_core, erc20, borrower, investor, contract_owner):
    lending_pool_peripheral = lending_pool_core.lendingPoolPeripheral()
    deposit_amount1 = Web3.to_wei(1, "ether")
    deposit_amount2 = Web3.to_wei(1, "wei")

    erc20.mint(investor, deposit_amount1, sender=contract_owner)
    erc20.approve(lending_pool_core.address, deposit_amount1, sender=investor)
    lending_pool_core.deposit(investor, investor, deposit_amount1, sender=lending_pool_peripheral)

    erc20.mint(contract_owner, deposit_amount2, sender=contract_owner)
    erc20.approve(lending_pool_core, deposit_amount2, sender=contract_owner)
    lending_pool_core.deposit(contract_owner, contract_owner, deposit_amount2, sender=lending_pool_peripheral)

    assert lending_pool_core.computeWithdrawableAmount(investor) == deposit_amount1
    assert lending_pool_core.computeWithdrawableAmount(contract_owner) == deposit_amount2
