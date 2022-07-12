# Structs

struct Liquidation:
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    buyNowPeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    borrower: address
    erc20TokenContract: address
    inAuction: bool

# Events

event OwnershipTransferred:
    ownerIndexed: address
    proposedOwnerIndexed: address
    owner: address
    proposedOwner: address
event OwnerProposed:
    ownerIndexed: address
    proposedOwnerIndexed: address
    owner: address
    proposedOwner: address
event CollateralVaultAddressSet:
    currentValue: address
    newValue: address
event BuyNowPeripheralAddressSet:
    currentValue: address
    newValue: address
event LoansCoreAddressAdded:
    erc20TokenContractIndexed: address
    currentValue: address
    newValue: address
    erc20TokenContract: address
event LoansCoreAddressRemoved:
    erc20TokenContractIndexed: address
    currentValue: address
    erc20TokenContract: address
event LiquidationAdded:
    erc20TokenContractIndexed: address
    collateralAddressIndexed: address
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address
event LiquidationRemoved:
    erc20TokenContractIndexed: address
    collateralAddressIndexed: address
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address

# Functions

@view
@external
def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    pass

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass

@external
def setCollateralVaultAddress(_address: address):
    pass

@external
def setBuyNowPeripheralAddress(_address: address):
    pass

@external
def addLoansCoreAddress(_erc20TokenContract: address, _address: address):
    pass

@external
def removeLoansCoreAddress(_erc20TokenContract: address):
    pass

@external
def addLiquidation(_collateralAddress: address, _tokenId: uint256, _startTime: uint256, _gracePeriodMaturity: uint256, _buyNowPeriodMaturity: uint256, _principal: uint256, _interestAmount: uint256, _apr: uint256, _borrower: address, _erc20TokenContract: address):
    pass

@external
def removeLiquidation(_collateralAddress: address, _tokenId: uint256):
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
def collateralVaultAddress() -> address:
    pass

@view
@external
def buyNowPeripheralAddress() -> address:
    pass

@view
@external
def loansCoreAddresses(arg0: address) -> address:
    pass


