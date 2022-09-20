# Structs

struct InvestorFunds:
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

@view
@external
def lendersArray() -> DynArray[address, 1125899906842624]:
    pass

@view
@external
def computeWithdrawableAmount(_lender: address) -> uint256:
    pass

@view
@external
def fundsInPool() -> uint256:
    pass

@view
@external
def currentAmountDeposited(_lender: address) -> uint256:
    pass

@view
@external
def totalAmountDeposited(_lender: address) -> uint256:
    pass

@view
@external
def totalAmountWithdrawn(_lender: address) -> uint256:
    pass

@view
@external
def sharesBasisPoints(_lender: address) -> uint256:
    pass

@view
@external
def lockPeriodEnd(_lender: address) -> uint256:
    pass

@view
@external
def activeForRewards(_lender: address) -> bool:
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
def deposit(_lender: address, _amount: uint256, _lockPeriodEnd: uint256) -> bool:
    pass

@external
def withdraw(_lender: address, _amount: uint256) -> bool:
    pass

@external
def sendFunds(_to: address, _amount: uint256) -> bool:
    pass

@external
def receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256) -> bool:
    pass

@external
def transferProtocolFees(_borrower: address, _protocolWallet: address, _amount: uint256) -> bool:
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
def funds(arg0: address) -> InvestorFunds:
    pass

@view
@external
def knownLenders(arg0: address) -> bool:
    pass

@view
@external
def activeLenders() -> uint256:
    pass

@view
@external
def fundsAvailable() -> uint256:
    pass

@view
@external
def fundsInvested() -> uint256:
    pass

@view
@external
def totalFundsInvested() -> uint256:
    pass

@view
@external
def totalRewards() -> uint256:
    pass

@view
@external
def totalSharesBasisPoints() -> uint256:
    pass


