# @version ^0.3.6


# Interfaces

from vyper.interfaces import ERC20 as IERC20


# Structs

struct InvestorLock:
    lockPeriodEnd: uint256
    lockPeriodAmount: uint256


# Events

event OwnerProposed:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event OwnershipTransferred:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event LendingPoolPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address


# Global variables

owner: public(address)
proposedOwner: public(address)

lendingPoolPeripheral: public(address)
erc20TokenContract: public(address)

investorLocks: public(HashMap[address, InvestorLock])


##### INTERNAL METHODS #####



##### EXTERNAL METHODS - VIEW #####



##### EXTERNAL METHODS - NON-VIEW #####

@external
def __init__(
    _erc20TokenContract: address
):
    assert _erc20TokenContract != empty(address), "The address is the zero address"

    self.owner = msg.sender
    self.erc20TokenContract = _erc20TokenContract


@external
def proposeOwner(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address it the zero address"
    assert self.owner != _address, "proposed owner addr is the owner"
    assert self.proposedOwner != _address, "proposed owner addr is the same"

    self.proposedOwner = _address

    log OwnerProposed(
        self.owner,
        _address,
        self.owner,
        _address,
        self.erc20TokenContract
    )


@external
def claimOwnership():
    assert msg.sender == self.proposedOwner, "msg.sender is not the proposed"

    log OwnershipTransferred(
        self.owner,
        self.proposedOwner,
        self.owner,
        self.proposedOwner,
        self.erc20TokenContract
    )

    self.owner = self.proposedOwner
    self.proposedOwner = empty(address)


@external
def setLendingPoolPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero address"

    log LendingPoolPeripheralAddressSet(
        self.erc20TokenContract,
        self.lendingPoolPeripheral,
        _address,
        self.erc20TokenContract
    )

    self.lendingPoolPeripheral = _address


@external
def setInvestorLock(_lender: address, _amount: uint256, _lockPeriodEnd: uint256):
    # _amount should be passed in wei
    assert msg.sender == self.lendingPoolPeripheral, "msg.sender is not LP peripheral"
    assert _lender != empty(address), "The _address is the zero address"

    self.investorLocks[_lender] = InvestorLock({
        lockPeriodEnd: _lockPeriodEnd,
        lockPeriodAmount: _amount
    })


