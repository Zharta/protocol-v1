import ape
from datetime import datetime as dt

LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


def test_set_lending_pool_peripheral_address(lending_pool_lock_contract, lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_lock_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    assert lending_pool_lock_contract.lendingPoolPeripheral() == lending_pool_peripheral_contract

    event = tx.events["LendingPoolPeripheralAddressSet"]
    assert event["currentValue"] == ape.ZERO_ADDRESS
    assert event["newValue"] == lending_pool_peripheral_contract


def test_load_contract_config(contracts_config):
    pass  # contracts_config fixture active from this point on


def test_initial_state(lending_pool_lock_contract, erc20_contract, contract_owner, protocol_wallet):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_lock_contract.owner() == contract_owner
    assert lending_pool_lock_contract.erc20TokenContract() == erc20_contract


def test_propose_owner_wrong_sender(lending_pool_lock_contract, borrower):
    with ape.reverts("msg.sender is not the owner"):
        lending_pool_lock_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(lending_pool_lock_contract, contract_owner):
    with ape.reverts("_address it the zero address"):
        lending_pool_lock_contract.proposeOwner(ape.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(lending_pool_lock_contract, contract_owner):
    with ape.reverts("proposed owner addr is the owner"):
        lending_pool_lock_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(lending_pool_lock_contract, contract_owner, borrower):
    tx = lending_pool_lock_contract.proposeOwner(borrower, {"from": contract_owner})

    assert lending_pool_lock_contract.owner() == contract_owner
    assert lending_pool_lock_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(lending_pool_lock_contract, contract_owner, borrower):
    lending_pool_lock_contract.proposeOwner(borrower, {"from": contract_owner})
    with ape.reverts("proposed owner addr is the same"):
        lending_pool_lock_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(lending_pool_lock_contract, contract_owner, borrower):
    lending_pool_lock_contract.proposeOwner(borrower, {"from": contract_owner})

    with ape.reverts("msg.sender is not the proposed"):
        lending_pool_lock_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(lending_pool_lock_contract, contract_owner, borrower):
    lending_pool_lock_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = lending_pool_lock_contract.claimOwnership({"from": borrower})

    assert lending_pool_lock_contract.owner() == borrower
    assert lending_pool_lock_contract.proposedOwner() == ape.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_lending_pool_peripheral_address_wrong_sender(
    lending_pool_lock_contract,
    lending_pool_peripheral_contract,
    investor
):
    with ape.reverts("msg.sender is not the owner"):
        lending_pool_lock_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": investor})


def test_set_lending_pool_peripheral_address_zero_address(lending_pool_lock_contract, contract_owner):
    with ape.reverts("address is the zero address"):
        lending_pool_lock_contract.setLendingPoolPeripheralAddress(ape.ZERO_ADDRESS, {"from": contract_owner})


def test_set_investor_lock_wrong_sender(lending_pool_lock_contract, lending_pool_peripheral_contract, investor):
    lockPeriodEnd = int(dt.now().timestamp()) + LOCK_PERIOD_DURATION
    with ape.reverts("msg.sender is not LP peripheral"):
        lending_pool_lock_contract.setInvestorLock(
            investor,
            1e18,
            lockPeriodEnd,
            {"from": investor}
        )


def test_set_investor_lock(lending_pool_lock_contract, lending_pool_peripheral_contract, investor):
    lockPeriodEnd = int(dt.now().timestamp()) + LOCK_PERIOD_DURATION
    lockPeriodAmount = 1e18
    lending_pool_lock_contract.setInvestorLock(
        investor,
        lockPeriodAmount,
        lockPeriodEnd,
        {"from": lending_pool_peripheral_contract}
    )

    lock = lending_pool_lock_contract.investorLocks(investor)
    assert lock[0] == lockPeriodEnd
    assert lock[1] == lockPeriodAmount
