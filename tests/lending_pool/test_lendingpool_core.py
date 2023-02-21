from web3 import Web3

import boa

from ..conftest_base import ZERO_ADDRESS, get_last_event, checksummed


LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


def user_balance(token_contract, user):
    return token_contract.balanceOf(user)

def test_set_lending_pool_peripheral_address(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=contract_owner)
    event = get_last_event(lending_pool_core_contract, name="LendingPoolPeripheralAddressSet")

    assert lending_pool_core_contract.lendingPoolPeripheral() == lending_pool_peripheral_contract.address
    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == lending_pool_peripheral_contract.address


def test_set_lending_pool_peripheral_address_same_address(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=contract_owner)

    assert lending_pool_core_contract.lendingPoolPeripheral() == lending_pool_peripheral_contract.address

    with boa.reverts("new value is the same"):
        lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=contract_owner)


def test_load_contract_config(contracts_config):
    pass  # contracts_config fixture active from this point on


def test_initial_state(lending_pool_core_contract, erc20_contract, contract_owner, protocol_wallet):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_core_contract.owner() == contract_owner
    assert lending_pool_core_contract.erc20TokenContract() == erc20_contract.address


def test_propose_owner_wrong_sender(lending_pool_core_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_core_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(lending_pool_core_contract, contract_owner):
    with boa.reverts("_address it the zero address"):
        lending_pool_core_contract.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(lending_pool_core_contract, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        lending_pool_core_contract.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(lending_pool_core_contract, contract_owner, borrower):
    lending_pool_core_contract.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(lending_pool_core_contract, name="OwnerProposed")

    assert lending_pool_core_contract.owner() == contract_owner
    assert lending_pool_core_contract.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(lending_pool_core_contract, contract_owner, borrower):
    lending_pool_core_contract.proposeOwner(borrower, sender=contract_owner)
    
    with boa.reverts("proposed owner addr is the same"):
        lending_pool_core_contract.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(lending_pool_core_contract, contract_owner, borrower):
    lending_pool_core_contract.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        lending_pool_core_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(lending_pool_core_contract, contract_owner, borrower):
    lending_pool_core_contract.proposeOwner(borrower, sender=contract_owner)

    lending_pool_core_contract.claimOwnership(sender=borrower)
    event = get_last_event(lending_pool_core_contract, name="OwnershipTransferred")

    assert lending_pool_core_contract.owner() == borrower
    assert lending_pool_core_contract.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_lending_pool_peripheral_address_wrong_sender(lending_pool_core_contract, lending_pool_peripheral_contract, investor):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=investor)


def test_set_lending_pool_peripheral_address_zero_address(lending_pool_core_contract, contract_owner):
    with boa.reverts("address is the zero address"):
        lending_pool_core_contract.setLendingPoolPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_deposit_wrong_sender(lending_pool_core_contract, investor, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.deposit(investor, investor, 0, sender=borrower)


def test_deposit(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    deposit_amount = Web3.to_wei(1, "ether")

    # erc20_contract.mint(contract_owner, deposit_amount, sender=contract_owner)
    erc20_contract.transfer(lending_pool_peripheral_contract, deposit_amount)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, sender=lending_pool_peripheral_contract.address)

    deposit_result = lending_pool_core_contract.deposit(investor, lending_pool_peripheral_contract, deposit_amount, sender=lending_pool_peripheral_contract.address)
    assert deposit_result

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == deposit_amount
    assert investor_funds[1] == deposit_amount
    assert investor_funds[2] == 0
    assert investor_funds[3] == deposit_amount
    assert investor_funds[4] == True

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount
    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == (investor,)
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount


def test_deposit_twice(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    deposit_amount_one = Web3.to_wei(1, "ether")
    deposit_amount_two = Web3.to_wei(0.5, "ether")

    # erc20_contract.mint(contract_owner, deposit_amount_one + deposit_amount_two, sender=contract_owner)
    erc20_contract.transfer(lending_pool_peripheral_contract, deposit_amount_one + deposit_amount_two, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount_one + deposit_amount_two, sender=lending_pool_peripheral_contract.address)

    lending_pool_core_contract.deposit(investor, lending_pool_peripheral_contract, deposit_amount_one, sender=lending_pool_peripheral_contract.address)
    lending_pool_core_contract.deposit(investor, lending_pool_peripheral_contract, deposit_amount_two, sender=lending_pool_peripheral_contract.address)

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == deposit_amount_one + deposit_amount_two
    assert investor_funds[1] == deposit_amount_one + deposit_amount_two
    assert investor_funds[3] == deposit_amount_one + deposit_amount_two

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount_one + deposit_amount_two
    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == (investor,)
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount_one + deposit_amount_two


def test_withdraw_wrong_sender(lending_pool_core_contract, lending_pool_peripheral_contract, investor, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.withdraw(investor, investor, 100, sender=borrower)


def test_withdraw_lender_zeroaddress(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("The _lender is the zero address"):
        lending_pool_core_contract.withdraw(ZERO_ADDRESS, lending_pool_core_contract, 100, sender=lending_pool_peripheral_contract.address)


def test_withdraw_receiver_zeroaddress(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("The _wallet is the zero address"):
        lending_pool_core_contract.withdraw(lending_pool_core_contract, ZERO_ADDRESS, 100, sender=lending_pool_peripheral_contract.address)


def test_withdraw_noinvestment(lending_pool_core_contract, lending_pool_peripheral_contract, investor, contract_owner):
    with boa.reverts("_amount more than withdrawable"):
        lending_pool_core_contract.withdraw(investor, investor, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral_contract.address)


def test_withdraw_insufficient_investment(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    deposit_amount = Web3.to_wei(1, "ether")

    # erc20_contract.mint(investor, deposit_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, sender=investor)

    lending_pool_core_contract.deposit(investor, investor, deposit_amount, sender=lending_pool_peripheral_contract.address)

    with boa.reverts("_amount more than withdrawable"):
        lending_pool_core_contract.withdraw(investor, investor, int(deposit_amount * 1.5), sender=lending_pool_peripheral_contract.address)


def test_withdraw_with_losses(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, borrower, investor, contract_owner):
    deposit_amount = Web3.to_wei(1, "ether")
    invested_amount = Web3.to_wei(0.5, "ether")
    recovered_amount = Web3.to_wei(0.4, "ether")

    # erc20_contract.mint(investor, deposit_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, sender=investor)

    lending_pool_core_contract.deposit(investor, investor, deposit_amount, sender=lending_pool_peripheral_contract.address)
    lending_pool_core_contract.sendFunds(borrower, invested_amount, sender=lending_pool_peripheral_contract.address)

    # erc20_contract.mint(borrower, recovered_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, recovered_amount, sender=borrower)
    lending_pool_core_contract.receiveFunds(
        borrower,
        recovered_amount,
        0,
        invested_amount,
        sender=lending_pool_peripheral_contract.address
    )
    with boa.reverts("_amount more than withdrawable"):
        lending_pool_core_contract.withdraw(investor, investor, deposit_amount, sender=lending_pool_peripheral_contract.address)

    lending_pool_core_contract.withdraw(
        investor,
        investor,
        deposit_amount - (invested_amount - recovered_amount),
        sender=lending_pool_peripheral_contract.address
    )


def test_withdraw(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    contract_owner
):
    deposit_amount = Web3.to_wei(2, "ether")
    withdraw_amount = Web3.to_wei(1, "ether")

    initial_balance = user_balance(erc20_contract, investor)

    # erc20_contract.mint(contract_owner, deposit_amount, sender=contract_owner)
    erc20_contract.transfer(lending_pool_peripheral_contract, deposit_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, sender=lending_pool_peripheral_contract.address)

    chain_time = boa.eval("block.timestamp")

    lending_pool_core_contract.deposit(investor, lending_pool_peripheral_contract, deposit_amount, sender=lending_pool_peripheral_contract.address)
    assert user_balance(erc20_contract, investor) == initial_balance
    assert lending_pool_core_contract.fundsAvailable() == deposit_amount

    lending_pool_core_contract.withdraw(investor, investor, withdraw_amount, sender=lending_pool_peripheral_contract.address)

    assert user_balance(erc20_contract, investor) == initial_balance + withdraw_amount
    assert lending_pool_core_contract.fundsAvailable() == deposit_amount - withdraw_amount

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == deposit_amount - withdraw_amount
    assert investor_funds[1] == deposit_amount
    assert investor_funds[2] == withdraw_amount
    assert investor_funds[4]

    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == (investor,)


def test_deposit_withdraw_deposit(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    contract_owner
):
    initial_balance = user_balance(erc20_contract, investor)

    # erc20_contract.mint(contract_owner, Web3.to_wei(2, "ether"), sender=contract_owner)
    erc20_contract.transfer(investor, Web3.to_wei(2, "ether"), sender=contract_owner)
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.to_wei(2, "ether")

    erc20_contract.transfer(lending_pool_peripheral_contract, Web3.to_wei(1, "ether"), sender=investor)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral_contract.address)

    chain_time = boa.eval("block.timestamp")

    lending_pool_core_contract.deposit(investor, lending_pool_peripheral_contract, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral_contract.address)
    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(1, "ether")

    lending_pool_core_contract.withdraw(investor, investor, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral_contract.address)

    assert user_balance(erc20_contract, investor) == initial_balance + Web3.to_wei(2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == 0

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == 0
    assert investor_funds[1] == Web3.to_wei(1, "ether")
    assert investor_funds[2] == Web3.to_wei(1, "ether")
    assert investor_funds[4] == False

    assert lending_pool_core_contract.activeLenders() == 0
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == (investor,)

    erc20_contract.transfer(lending_pool_peripheral_contract, Web3.to_wei(1, "ether"), sender=investor)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral_contract.address)
    lending_pool_core_contract.deposit(investor, lending_pool_peripheral_contract, Web3.to_wei(1, "ether"), sender=lending_pool_peripheral_contract.address)
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.to_wei(1, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(1, "ether")

    investor_funds2 = lending_pool_core_contract.funds(investor)
    assert investor_funds2[0] == Web3.to_wei(1, "ether")
    assert investor_funds2[1] == Web3.to_wei(2, "ether")
    assert investor_funds2[2] == Web3.to_wei(1, "ether")
    assert investor_funds2[3] == Web3.to_wei(1, "ether")
    assert investor_funds2[4] == True

    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(1, "ether")
    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == (investor,)
    assert lending_pool_core_contract.totalSharesBasisPoints() == Web3.to_wei(1, "ether")


def test_send_funds_wrong_sender(lending_pool_core_contract, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.sendFunds(borrower, Web3.to_wei(1, "ether"), sender=borrower)


def test_send_funds_zero_amount(lending_pool_core_contract, lending_pool_peripheral_contract, borrower, contract_owner):
    with boa.reverts("_amount has to be higher than 0"):
        lending_pool_core_contract.sendFunds(
            borrower,
            Web3.to_wei(0, "ether"),
            sender=lending_pool_peripheral_contract.address
        )


def test_send_funds_insufficient_balance(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    liquidity_controls_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    # erc20_contract.mint(investor, Web3.to_wei(1, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=investor)

    lending_pool_peripheral_contract.depositWeth(Web3.to_wei(1, "ether"), sender=investor)

    with boa.reverts("Insufficient balance"):
        tx_send = lending_pool_core_contract.sendFunds(
            borrower,
            Web3.to_wei(1.1, "ether"),
            sender=lending_pool_peripheral_contract.address
        )


def test_send_funds(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    liquidity_controls_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    deposit_amount = Web3.to_wei(1, "ether")
    initial_balance = user_balance(erc20_contract, borrower)

    # erc20_contract.mint(investor, deposit_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, sender=investor)
    lending_pool_core_contract.deposit(investor, investor, deposit_amount, sender=lending_pool_peripheral_contract.address)

    lending_pool_core_contract.sendFunds(
        borrower,
        Web3.to_wei(0.2, "ether"),
        sender=lending_pool_peripheral_contract.address
    )

    assert user_balance(erc20_contract, borrower) == initial_balance + Web3.to_wei(0.2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(0.8, "ether")
    assert lending_pool_core_contract.fundsInvested() == Web3.to_wei(0.2, "ether")


def test_receive_funds_wrong_sender(lending_pool_core_contract, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.receiveFunds(
            borrower,
            Web3.to_wei(0.2, "ether"),
            Web3.to_wei(0.05, "ether"),
            Web3.to_wei(0.2, "ether"),
            sender=borrower
        )


def test_receive_funds_zero_value(lending_pool_core_contract, lending_pool_peripheral_contract, borrower, contract_owner):
    with boa.reverts("Amount has to be higher than 0"):
        lending_pool_core_contract.receiveFunds(
            borrower,
            Web3.to_wei(0, "ether"),
            Web3.to_wei(0, "ether"),
            Web3.to_wei(0, "ether"),
            sender=lending_pool_peripheral_contract.address
        )

def test_transfer_protocol_fees_wrong_sender(lending_pool_core_contract, contract_owner, borrower):
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.transferProtocolFees(
            borrower,
            contract_owner,
            Web3.to_wei(0.2, "ether"),
            sender=borrower
        )


def test_transfer_protocol_fees_zero_value(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner, borrower):
    with boa.reverts("_amount should be higher than 0"):
        lending_pool_core_contract.transferProtocolFees(
            borrower,
            contract_owner,
            Web3.to_wei(0, "ether"),
            sender=lending_pool_peripheral_contract.address
        )


def test_transfer_protocol_fees(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner, borrower):
    amount = Web3.to_wei(1, "ether")

    # erc20_contract.mint(contract_owner, amount, sender=contract_owner)
    erc20_contract.transfer(borrower, amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, amount, sender=borrower)

    contract_owner_balance = user_balance(erc20_contract, contract_owner)
    assert user_balance(erc20_contract, lending_pool_core_contract) == 0

    lending_pool_core_contract.transferProtocolFees(
        borrower,
        contract_owner,
        amount,
        sender=lending_pool_peripheral_contract.address
    )

    assert user_balance(erc20_contract, lending_pool_core_contract) == 0
    assert user_balance(erc20_contract, contract_owner) == contract_owner_balance + amount


def test_receive_funds(lending_pool_core_contract, lending_pool_peripheral_contract, liquidity_controls_contract, erc20_contract, investor, borrower, contract_owner):
    deposit_amount = Web3.to_wei(1, "ether")

    # erc20_contract.mint(investor, deposit_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, sender=investor)
    lending_pool_core_contract.deposit(investor, investor, deposit_amount, sender=lending_pool_peripheral_contract.address)

    lending_pool_core_contract.sendFunds(
        borrower,
        Web3.to_wei(0.2, "ether"),
        sender=lending_pool_peripheral_contract.address
    )

    investment_amount = Web3.to_wei(0.2, "ether")
    rewards_amount = Web3.to_wei(0.02, "ether")
    pool_rewards_amount = rewards_amount * (10000 - lending_pool_peripheral_contract.protocolFeesShare()) // 10000

    # erc20_contract.mint(borrower, rewards_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, investment_amount + rewards_amount, sender=borrower)

    initial_balance = user_balance(erc20_contract, lending_pool_core_contract)

    lending_pool_core_contract.receiveFunds(
        borrower,
        investment_amount,
        pool_rewards_amount,
        investment_amount,
        sender=lending_pool_peripheral_contract.address
    )

    assert user_balance(erc20_contract, lending_pool_core_contract) == initial_balance + investment_amount + pool_rewards_amount

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount + pool_rewards_amount
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_core_contract.totalRewards() == pool_rewards_amount
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount

    assert lending_pool_core_contract.funds(contract_owner)[3] == 0
    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == deposit_amount + pool_rewards_amount


def test_receive_funds_with_losses(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    borrower,
    contract_owner
):
    deposit_amount = Web3.to_wei(1, "ether")
    # erc20_contract.mint(investor, deposit_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, sender=investor)
    lending_pool_peripheral_contract.depositWeth(deposit_amount, sender=investor)

    lending_pool_core_contract.sendFunds(
        borrower,
        Web3.to_wei(0.6, "ether"),
        sender=lending_pool_peripheral_contract.address
    )

    investment_amount = Web3.to_wei(0.6, "ether")
    rewards_amount = Web3.to_wei(0, "ether")
    recovered_amount = Web3.to_wei(0.4, "ether")
    pool_rewards_amount = rewards_amount * (10000 - lending_pool_peripheral_contract.protocolFeesShare()) // 10000

    # erc20_contract.mint(borrower, rewards_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract.address, recovered_amount, sender=borrower)

    initial_balance = user_balance(erc20_contract, lending_pool_core_contract.address)

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount - investment_amount
    assert lending_pool_core_contract.fundsInvested() == investment_amount

    lending_pool_core_contract.receiveFunds(
        borrower,
        recovered_amount,
        pool_rewards_amount,
        investment_amount,
        sender=lending_pool_peripheral_contract.address
    )

    assert user_balance(erc20_contract, lending_pool_core_contract.address) == initial_balance + recovered_amount

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount - investment_amount + recovered_amount
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_core_contract.totalRewards() == pool_rewards_amount
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount

    assert lending_pool_core_contract.funds(investor)[3] == deposit_amount
    assert lending_pool_core_contract.funds(contract_owner)[3] == 0

    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == deposit_amount - investment_amount + recovered_amount


def test_withdrawable_precision(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    erc20_contract,
    borrower,
    investor,
    contract_owner
):
    deposit_amount1 = Web3.to_wei(1, "ether")
    deposit_amount2 = Web3.to_wei(1, "wei")

    # erc20_contract.mint(investor, deposit_amount1, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract.address, deposit_amount1, sender=investor)
    lending_pool_core_contract.deposit(investor, investor, deposit_amount1, sender=lending_pool_peripheral_contract.address)

    # erc20_contract.mint(contract_owner, deposit_amount2, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount2, sender=contract_owner)
    lending_pool_core_contract.deposit(contract_owner, contract_owner, deposit_amount2, sender=lending_pool_peripheral_contract.address)

    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == deposit_amount1
    assert lending_pool_core_contract.computeWithdrawableAmount(contract_owner) == deposit_amount2


