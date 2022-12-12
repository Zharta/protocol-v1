from brownie import chain
from web3 import Web3

import brownie


LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


def user_balance(token_contract, user):
    return token_contract.balanceOf(user)

def test_set_lending_pool_peripheral_address(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    assert lending_pool_core_contract.lendingPoolPeripheral() == lending_pool_peripheral_contract

    event = tx.events["LendingPoolPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == lending_pool_peripheral_contract


def test_set_lending_pool_peripheral_address_same_address(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    assert lending_pool_core_contract.lendingPoolPeripheral() == lending_pool_peripheral_contract

    with brownie.reverts("new value is the same"):
        lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})


def test_load_contract_config(contracts_config):
    pass  # contracts_config fixture active from this point on


def test_initial_state(lending_pool_core_contract, erc20_contract, contract_owner, protocol_wallet):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_core_contract.owner() == contract_owner
    assert lending_pool_core_contract.erc20TokenContract() == erc20_contract


def test_propose_owner_wrong_sender(lending_pool_core_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_core_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(lending_pool_core_contract, contract_owner):
    with brownie.reverts("_address it the zero address"):
        lending_pool_core_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(lending_pool_core_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        lending_pool_core_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(lending_pool_core_contract, contract_owner, borrower):
    tx = lending_pool_core_contract.proposeOwner(borrower, {"from": contract_owner})

    assert lending_pool_core_contract.owner() == contract_owner
    assert lending_pool_core_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(lending_pool_core_contract, contract_owner, borrower):
    lending_pool_core_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        lending_pool_core_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(lending_pool_core_contract, contract_owner, borrower):
    lending_pool_core_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        lending_pool_core_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(lending_pool_core_contract, contract_owner, borrower):
    lending_pool_core_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = lending_pool_core_contract.claimOwnership({"from": borrower})

    assert lending_pool_core_contract.owner() == borrower
    assert lending_pool_core_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_lending_pool_peripheral_address_wrong_sender(lending_pool_core_contract, lending_pool_peripheral_contract, investor):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": investor})


def test_set_lending_pool_peripheral_address_zero_address(lending_pool_core_contract, contract_owner):
    with brownie.reverts("address is the zero address"):
        lending_pool_core_contract.setLendingPoolPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_deposit_wrong_sender(lending_pool_core_contract, investor, borrower):
    with brownie.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.deposit(investor, 0, {"from": borrower})


def test_deposit(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    deposit_amount = Web3.toWei(1, "ether")

    erc20_contract.mint(contract_owner, deposit_amount, {"from": contract_owner})
    erc20_contract.transfer(lending_pool_peripheral_contract, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": lending_pool_peripheral_contract})

    tx_deposit = lending_pool_core_contract.deposit(investor, deposit_amount, {"from": lending_pool_peripheral_contract})
    assert tx_deposit.return_value

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == deposit_amount
    assert investor_funds["totalAmountDeposited"] == deposit_amount
    assert investor_funds["totalAmountWithdrawn"] == 0
    assert investor_funds["sharesBasisPoints"] == deposit_amount
    assert investor_funds["activeForRewards"] == True

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount
    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount


def test_deposit_twice(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    deposit_amount_one = Web3.toWei(1, "ether")
    deposit_amount_two = Web3.toWei(0.5, "ether")

    erc20_contract.mint(contract_owner, deposit_amount_one + deposit_amount_two, {"from": contract_owner})
    erc20_contract.transfer(lending_pool_peripheral_contract, deposit_amount_one + deposit_amount_two, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount_one + deposit_amount_two, {"from": lending_pool_peripheral_contract})

    tx_deposit = lending_pool_core_contract.deposit(investor, deposit_amount_one, {"from": lending_pool_peripheral_contract})
    tx_deposit_twice = lending_pool_core_contract.deposit(investor, deposit_amount_two, {"from": lending_pool_peripheral_contract})

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == deposit_amount_one + deposit_amount_two
    assert investor_funds["totalAmountDeposited"] == deposit_amount_one + deposit_amount_two
    assert investor_funds["sharesBasisPoints"] == deposit_amount_one + deposit_amount_two

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount_one + deposit_amount_two
    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount_one + deposit_amount_two


def test_withdraw_wrong_sender(lending_pool_core_contract, lending_pool_peripheral_contract, investor, borrower):
    with brownie.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.withdraw(investor, 100, {"from": borrower})


def test_withdraw_lender_zeroaddress(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("The _lender is the zero address"):
        lending_pool_core_contract.withdraw(brownie.ZERO_ADDRESS, 100, {"from": lending_pool_peripheral_contract})


def test_withdraw_noinvestment(lending_pool_core_contract, lending_pool_peripheral_contract, investor, contract_owner):
    with brownie.reverts("_amount more than withdrawable"):
        lending_pool_core_contract.withdraw(investor, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})


def test_withdraw_insufficient_investment(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    deposit_amount = Web3.toWei(1, "ether")

    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})

    lending_pool_core_contract.deposit(investor, deposit_amount, {"from": lending_pool_peripheral_contract})

    with brownie.reverts("_amount more than withdrawable"):
        lending_pool_core_contract.withdraw(investor, deposit_amount * 1.5, {"from": lending_pool_peripheral_contract})


def test_withdraw_with_losses(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, borrower, investor, contract_owner):
    deposit_amount = Web3.toWei(1, "ether")
    invested_amount = Web3.toWei(0.5, "ether")
    recovered_amount = Web3.toWei(0.4, "ether")

    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})

    lending_pool_core_contract.deposit(investor, deposit_amount, {"from": lending_pool_peripheral_contract})
    lending_pool_core_contract.sendFunds(borrower, invested_amount, {"from": lending_pool_peripheral_contract})

    erc20_contract.mint(borrower, recovered_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, recovered_amount, {"from": borrower})
    lending_pool_core_contract.receiveFunds(
        borrower,
        recovered_amount,
        0,
        invested_amount,
        {"from": lending_pool_peripheral_contract}
    )
    with brownie.reverts("_amount more than withdrawable"):
        lending_pool_core_contract.withdraw(investor, deposit_amount, {"from": lending_pool_peripheral_contract})

    lending_pool_core_contract.withdraw(investor, deposit_amount - (invested_amount - recovered_amount), {"from": lending_pool_peripheral_contract})


def test_withdraw(lending_pool_core_contract, lending_pool_peripheral_contract, liquidity_controls_contract, erc20_contract, investor, contract_owner):
    deposit_amount = Web3.toWei(2, "ether")
    withdraw_amount = Web3.toWei(1, "ether")

    initial_balance = user_balance(erc20_contract, investor)

    erc20_contract.mint(contract_owner, deposit_amount, {"from": contract_owner})
    erc20_contract.transfer(lending_pool_peripheral_contract, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": lending_pool_peripheral_contract})

    chain_time = chain.time()

    lending_pool_core_contract.deposit(investor, deposit_amount, 0, {"from": lending_pool_peripheral_contract})
    assert user_balance(erc20_contract, investor) == initial_balance
    assert lending_pool_core_contract.fundsAvailable() == deposit_amount

    lending_pool_core_contract.withdraw(investor, withdraw_amount, {"from": lending_pool_peripheral_contract})
    erc20_contract.transfer(investor, withdraw_amount, {"from": lending_pool_peripheral_contract})

    assert user_balance(erc20_contract, investor) == initial_balance + withdraw_amount
    assert lending_pool_core_contract.fundsAvailable() == deposit_amount - withdraw_amount

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == deposit_amount - withdraw_amount
    assert investor_funds["totalAmountDeposited"] == deposit_amount
    assert investor_funds["totalAmountWithdrawn"] == withdraw_amount
    assert investor_funds["activeForRewards"]

    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]


def test_deposit_withdraw_deposit(lending_pool_core_contract, lending_pool_peripheral_contract, liquidity_controls_contract, erc20_contract, investor, contract_owner):
    initial_balance = user_balance(erc20_contract, investor)

    erc20_contract.mint(contract_owner, Web3.toWei(2, "ether"), {"from": contract_owner})
    erc20_contract.transfer(investor, Web3.toWei(2, "ether"), {"from": contract_owner})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")

    erc20_contract.transfer(lending_pool_peripheral_contract, Web3.toWei(2, "ether"), {"from": investor})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(2, "ether"), {"from": lending_pool_peripheral_contract})

    chain_time = chain.time()

    lending_pool_core_contract.deposit(investor, Web3.toWei(1, "ether"), chain_time + LOCK_PERIOD_DURATION, {"from": lending_pool_peripheral_contract})
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")

    lending_pool_core_contract.withdraw(investor, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})
    erc20_contract.transfer(investor, Web3.toWei(2, "ether"), {"from": lending_pool_peripheral_contract})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == 0

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == 0
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountWithdrawn"] == Web3.toWei(1, "ether")
    assert investor_funds["activeForRewards"] == False

    assert lending_pool_core_contract.activeLenders() == 0
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]

    erc20_contract.transfer(lending_pool_peripheral_contract, Web3.toWei(1, "ether"), {"from": investor})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})
    lending_pool_core_contract.deposit(investor, Web3.toWei(1, "ether"), chain_time + LOCK_PERIOD_DURATION, {"from": lending_pool_peripheral_contract})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")

    investor_funds2 = lending_pool_core_contract.funds(investor)
    assert investor_funds2["currentAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds2["totalAmountDeposited"] == Web3.toWei(2, "ether")
    assert investor_funds2["totalAmountWithdrawn"] == Web3.toWei(1, "ether")
    assert investor_funds2["sharesBasisPoints"] == Web3.toWei(1, "ether")
    assert investor_funds2["activeForRewards"] == True

    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]
    assert lending_pool_core_contract.totalSharesBasisPoints() == Web3.toWei(1, "ether")


def test_send_funds_wrong_sender(lending_pool_core_contract, borrower):
    with brownie.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.sendFunds(borrower, Web3.toWei(1, "ether"), {"from": borrower})


def test_send_funds_zero_amount(lending_pool_core_contract, lending_pool_peripheral_contract, borrower, contract_owner):
    with brownie.reverts("_amount has to be higher than 0"):
        lending_pool_core_contract.sendFunds(
            borrower,
            Web3.toWei(0, "ether"),
            {"from": lending_pool_peripheral_contract}
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
    contract_owner.transfer(to=investor, amount=Web3.toWei(1, "ether"))
    lending_pool_peripheral_contract.deposit({"from": investor, 'value': Web3.toWei(1, "ether")})
    contract_owner.transfer(to=lending_pool_peripheral_contract, amount=Web3.toWei(2, "ether"))

    with brownie.reverts("Insufficient balance"):
        tx_send = lending_pool_core_contract.sendFunds(
            borrower,
            Web3.toWei(1.1, "ether"),
            {"from": lending_pool_peripheral_contract}
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
    deposit_amount = Web3.toWei(1, "ether")
    initial_balance = user_balance(erc20_contract, borrower)

    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.transfer(lending_pool_peripheral_contract, deposit_amount, {"from": investor})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": lending_pool_peripheral_contract})
    lending_pool_core_contract.deposit(investor, deposit_amount, 0, {"from": lending_pool_peripheral_contract})

    contract_owner.transfer(to=lending_pool_peripheral_contract, amount=Web3.toWei(2, "ether"))

    lending_pool_core_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": lending_pool_peripheral_contract}
    )

    assert user_balance(erc20_contract, borrower) == initial_balance + Web3.toWei(0.2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(0.8, "ether")
    assert lending_pool_core_contract.fundsInvested() == Web3.toWei(0.2, "ether")


def test_receive_funds_wrong_sender(lending_pool_core_contract, borrower):
    with brownie.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.receiveFunds(
            borrower,
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            Web3.toWei(0.2, "ether"),
            {"from": borrower}
        )


def test_receive_funds_zero_value(lending_pool_core_contract, lending_pool_peripheral_contract, borrower, contract_owner):
    with brownie.reverts("Amount has to be higher than 0"):
        lending_pool_core_contract.receiveFunds(
            borrower,
            Web3.toWei(0, "ether"),
            Web3.toWei(0, "ether"),
            Web3.toWei(0, "ether"),
            {"from": lending_pool_peripheral_contract}
        )

def test_transfer_protocol_fees_wrong_sender(lending_pool_core_contract, contract_owner, borrower):
    with brownie.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.transferProtocolFees(
            borrower,
            contract_owner,
            Web3.toWei(0.2, "ether"),
            {"from": borrower}
        )


def test_transfer_protocol_fees_zero_value(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner, borrower):
    with brownie.reverts("_amount should be higher than 0"):
        lending_pool_core_contract.transferProtocolFees(
            borrower,
            contract_owner,
            Web3.toWei(0, "ether"),
            {"from": lending_pool_peripheral_contract}
        )


def test_transfer_protocol_fees(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner, borrower):
    amount = Web3.toWei(1, "ether")

    erc20_contract.mint(contract_owner, amount, {"from": contract_owner})
    erc20_contract.transfer(borrower, amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount, {"from": borrower})

    # erc20_contract.transfer(lending_pool_peripheral_contract, amount, {"from": borrower})
    # erc20_contract.approve(lending_pool_core_contract, amount, {"from": lending_pool_peripheral_contract})

    contract_owner_balance = user_balance(erc20_contract, contract_owner)
    assert user_balance(erc20_contract, lending_pool_core_contract) == 0

    lending_pool_core_contract.transferProtocolFees(
        borrower,
        contract_owner,
        amount,
        {"from": lending_pool_peripheral_contract}
    )

    assert user_balance(erc20_contract, lending_pool_core_contract) == 0
    assert user_balance(erc20_contract, contract_owner) == contract_owner_balance + amount


def test_receive_funds(lending_pool_core_contract, lending_pool_peripheral_contract, liquidity_controls_contract, erc20_contract, investor, borrower, contract_owner):
    deposit_amount = Web3.toWei(1, "ether")

    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.transfer(lending_pool_peripheral_contract, deposit_amount, {"from": investor})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": lending_pool_peripheral_contract})
    lending_pool_core_contract.deposit(investor, deposit_amount, 0, {"from": lending_pool_peripheral_contract})

    lending_pool_core_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": lending_pool_peripheral_contract}
    )

    investment_amount = Web3.toWei(0.2, "ether")
    rewards_amount = Web3.toWei(0.02, "ether")
    pool_rewards_amount = rewards_amount * (10000 - lending_pool_peripheral_contract.protocolFeesShare()) / 10000

    erc20_contract.mint(borrower, rewards_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, investment_amount + rewards_amount, {"from": borrower})
    # erc20_contract.approve(lending_pool_core_contract, investment_amount + rewards_amount, {"from": lending_pool_peripheral_contract})

    initial_balance = user_balance(erc20_contract, lending_pool_core_contract)

    lending_pool_core_contract.receiveFunds(
        borrower,
        investment_amount,
        pool_rewards_amount,
        investment_amount,
        {"from": lending_pool_peripheral_contract}
    )

    assert user_balance(erc20_contract, lending_pool_core_contract) == initial_balance + investment_amount + pool_rewards_amount

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount + pool_rewards_amount
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_core_contract.totalRewards() == pool_rewards_amount
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount

    assert lending_pool_core_contract.funds(contract_owner)["sharesBasisPoints"] == 0
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
    deposit_amount = Web3.toWei(1, "ether")
    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})
    lending_pool_peripheral_contract.deposit(deposit_amount, {"from": investor})

    lending_pool_core_contract.sendFunds(
        borrower,
        Web3.toWei(0.6, "ether"),
        {"from": lending_pool_peripheral_contract}
    )

    investment_amount = Web3.toWei(0.6, "ether")
    rewards_amount = Web3.toWei(0, "ether")
    recovered_amount = Web3.toWei(0.4, "ether")
    pool_rewards_amount = rewards_amount * (10000 - lending_pool_peripheral_contract.protocolFeesShare()) / 10000

    erc20_contract.mint(borrower, rewards_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, recovered_amount, {"from": borrower})

    initial_balance = user_balance(erc20_contract, lending_pool_core_contract)

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount - investment_amount
    assert lending_pool_core_contract.fundsInvested() == investment_amount

    lending_pool_core_contract.receiveFunds(
        borrower,
        recovered_amount,
        pool_rewards_amount,
        investment_amount,
        {"from": lending_pool_peripheral_contract}
    )

    assert user_balance(erc20_contract, lending_pool_core_contract) == initial_balance + recovered_amount

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount - investment_amount + recovered_amount
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_core_contract.totalRewards() == pool_rewards_amount
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount

    assert lending_pool_core_contract.funds(investor)["sharesBasisPoints"] == deposit_amount
    assert lending_pool_core_contract.funds(contract_owner)["sharesBasisPoints"] == 0

    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == deposit_amount - investment_amount + recovered_amount


def test_withdrawable_precision(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, borrower, investor, contract_owner):
    deposit_amount1 = Web3.toWei(1, "ether")
    deposit_amount2 = Web3.toWei(1, "wei")

    erc20_contract.mint(investor, deposit_amount1, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount1, {"from": investor})
    lending_pool_core_contract.deposit(investor, deposit_amount1, {"from": lending_pool_peripheral_contract})

    erc20_contract.mint(contract_owner, deposit_amount2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount2, {"from": contract_owner})
    lending_pool_core_contract.deposit(contract_owner, deposit_amount2, {"from": lending_pool_peripheral_contract})

    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == deposit_amount1
    assert lending_pool_core_contract.computeWithdrawableAmount(contract_owner) == deposit_amount2


