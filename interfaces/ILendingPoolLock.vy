# Structs

struct InvestorLock:
    lockPeriodEnd: uint256
    lockPeriodAmount: uint256

struct LegacyInvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    lockPeriodEnd: uint256
    activeForRewards: bool

# Events

event OwnerProposed:
    ownerIndexed: address
    proposedOwnerIndexed: address
    owner: address
    proposedOwner: address
    erc20TokenContract: address
event OwnershipTransferred:
    ownerIndexed: address
    proposedOwnerIndexed: address
    owner: address
    proposedOwner: address
    erc20TokenContract: address
event LendingPoolPeripheralAddressSet:
    erc20TokenContractIndexed: address
    currentValue: address
    newValue: address
    erc20TokenContract: address

# Functions

@external
def migrate(_lendingPoolCoreAddress: address, _lenders: DynArray[address, 100]):
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


