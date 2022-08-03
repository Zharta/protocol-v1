from brownie import chain
from web3 import Web3

import brownie


LOCK_PERIOD_DURATION = 10


def user_balance(token_contract, user):
    return token_contract.balanceOf(user)


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


def test_deposit_wrong_sender(lending_pool_core_contract, investor, borrower):
    with brownie.reverts("msg.sender is not LP peripheral"):
        lending_pool_core_contract.deposit(investor, 0, 0, {"from": borrower})


def test_deposit(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    deposit_amount = Web3.toWei(1, "ether")
    
    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + deposit_amount

    tx_deposit = lending_pool_core_contract.deposit(investor, deposit_amount, 0, {"from": lending_pool_peripheral_contract})
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
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    
    deposit_amount_one = Web3.toWei(1, "ether")
    deposit_amount_two = Web3.toWei(0.5, "ether")
    
    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, deposit_amount_one + deposit_amount_two, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount_one + deposit_amount_two, {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + deposit_amount_one + deposit_amount_two

    tx_deposit = lending_pool_core_contract.deposit(investor, deposit_amount_one, 0, {"from": lending_pool_peripheral_contract})
    tx_deposit_twice = lending_pool_core_contract.deposit(investor, deposit_amount_two, 0, {"from": lending_pool_peripheral_contract})

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
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("The _lender is the zero address"):
        lending_pool_core_contract.withdraw(brownie.ZERO_ADDRESS, 100, {"from": lending_pool_peripheral_contract})


def test_withdraw_noinvestment(lending_pool_core_contract, lending_pool_peripheral_contract, investor, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})    
    
    with brownie.reverts("_amount more than withdrawable"):
        lending_pool_core_contract.withdraw(investor, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})


def test_withdraw_insufficient_investment(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    deposit_amount = Web3.toWei(1, "ether")
    
    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})
    
    lending_pool_core_contract.deposit(investor, deposit_amount, 0, {"from": lending_pool_peripheral_contract})
    
    with brownie.reverts("_amount more than withdrawable"):
        lending_pool_core_contract.withdraw(investor, deposit_amount * 1.5, {"from": lending_pool_peripheral_contract})


def test_withdraw(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    deposit_amount = Web3.toWei(2, "ether")
    withdraw_amount = Web3.toWei(1, "ether")

    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + deposit_amount

    chain_time = chain.time()

    lending_pool_peripheral_contract.deposit(deposit_amount, {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance
    assert lending_pool_core_contract.fundsAvailable() == deposit_amount

    lending_pool_core_contract.withdraw(investor, withdraw_amount, {"from": lending_pool_peripheral_contract})
    assert user_balance(erc20_contract, investor) == initial_balance + withdraw_amount
    assert lending_pool_core_contract.fundsAvailable() == deposit_amount - withdraw_amount

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == deposit_amount - withdraw_amount
    assert investor_funds["totalAmountDeposited"] == deposit_amount
    assert investor_funds["totalAmountWithdrawn"] == withdraw_amount
    assert investor_funds["activeForRewards"]
    assert investor_funds["lockPeriodEnd"] == chain_time + LOCK_PERIOD_DURATION

    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]


def test_deposit_withdraw_deposit(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, Web3.toWei(2, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(2, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")

    chain_time = chain.time()

    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")

    assert lending_pool_core_contract.funds(investor)["lockPeriodEnd"] == chain_time + LOCK_PERIOD_DURATION

    lending_pool_core_contract.withdraw(investor, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == 0

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == 0
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountWithdrawn"] == Web3.toWei(1, "ether")
    assert investor_funds["activeForRewards"] == False
    assert investor_funds["lockPeriodEnd"] == 0

    assert lending_pool_core_contract.activeLenders() == 0
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]

    tx_deposit2 = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
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
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("_amount has to be higher than 0"):
        lending_pool_core_contract.sendFunds(
            borrower,
            Web3.toWei(0, "ether"),
            {"from": lending_pool_peripheral_contract}
        )


def test_send_funds_insufficient_balance(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    with brownie.reverts("Insufficient balance"):
        tx_send = lending_pool_core_contract.sendFunds(
            borrower,
            Web3.toWei(1.1, "ether"),
            {"from": lending_pool_peripheral_contract}
        )


def test_send_funds(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    initial_balance = user_balance(erc20_contract, borrower)
    
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    tx_send = lending_pool_core_contract.sendFunds(
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
            {"from": borrower}
        )


def test_receive_funds_zero_value(lending_pool_core_contract, lending_pool_peripheral_contract, borrower, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("Amount has to be higher than 0"):
        lending_pool_core_contract.receiveFunds(
            borrower,
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
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("_amount should be higher than 0"):
        lending_pool_core_contract.transferProtocolFees(
            borrower,
            contract_owner,
            Web3.toWei(0, "ether"),
            {"from": lending_pool_peripheral_contract}
        )


def test_transfer_protocol_fees(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner, borrower):  
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    amount = Web3.toWei(1, "ether")

    erc20_contract.mint(borrower, amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount, {"from": borrower})

    assert user_balance(erc20_contract, lending_pool_core_contract) == 0

    lending_pool_core_contract.transferProtocolFees(
        borrower,
        contract_owner,
        amount,
        {"from": lending_pool_peripheral_contract}
    )

    assert user_balance(erc20_contract, lending_pool_core_contract) == 0
    assert user_balance(erc20_contract, contract_owner) == amount


def test_receive_funds(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, borrower, contract_owner):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    deposit_amount = Web3.toWei(1, "ether")

    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})
    lending_pool_peripheral_contract.deposit(deposit_amount, {"from": investor})

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

    initial_balance = user_balance(erc20_contract, lending_pool_core_contract)

    lending_pool_core_contract.receiveFunds(
        borrower,
        investment_amount,
        pool_rewards_amount,
        {"from": lending_pool_peripheral_contract}
    )

    assert user_balance(erc20_contract, lending_pool_core_contract) == initial_balance + investment_amount + pool_rewards_amount

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount + pool_rewards_amount
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_core_contract.totalRewards() == pool_rewards_amount
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount

    assert lending_pool_core_contract.funds(contract_owner)["sharesBasisPoints"] == 0
    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == deposit_amount + pool_rewards_amount
