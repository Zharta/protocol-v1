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

# Functions

@view
@external
def owner() -> address:
    pass

@view
@external
def proposedOwner() -> address:
    pass

@view
@external
def lendingPoolPeripheral() -> address:
    pass

@view
@external
def erc20TokenContract() -> address:
    pass

@view
@external
def investorLocks(arg0: address) -> InvestorLock:
    pass

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass

@external
def setLendingPoolPeripheralAddress(_address: address):
    pass

@external
def setInvestorLock(_lender: address, _amount: uint256, _lockPeriodEnd: uint256):
    pass