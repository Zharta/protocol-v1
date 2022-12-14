# Structs

struct Liquidation:
    lid: bytes32
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    lenderPeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256
    gracePeriodPrice: uint256
    lenderPeriodPrice: uint256
    borrower: address
    loanId: uint256
    loansCoreContract: address
    erc20TokenContract: address
    inAuction: bool

# Events

event OwnershipTransferred:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address

event OwnerProposed:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address

event LiquidationsPeripheralAddressSet:
    currentValue: address
    newValue: address

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
def liquidationsPeripheralAddress() -> address:
    pass

@view
@external
def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    pass

@view
@external
def getLiquidationStartTime(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationGracePeriodMaturity(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationLenderPeriodMaturity(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationPrincipal(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationInterestAmount(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationAPR(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationBorrower(_collateralAddress: address, _tokenId: uint256) -> address:
    pass

@view
@external
def getLiquidationERC20Contract(_collateralAddress: address, _tokenId: uint256) -> address:
    pass

@view
@external
def isLiquidationInAuction(_collateralAddress: address, _tokenId: uint256) -> bool:
    pass

@view
@external
def isLoanLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256) -> bool:
    pass

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass

@external
def setLiquidationsPeripheralAddress(_address: address):
    pass

@external
def addLiquidation(_collateralAddress: address, _tokenId: uint256, _startTime: uint256, _gracePeriodMaturity: uint256, _lenderPeriodMaturity: uint256, _principal: uint256, _interestAmount: uint256, _apr: uint256, _gracePeriodPrice: uint256, _lenderPeriodPrice: uint256, _borrower: address, _loanId: uint256, _loansCoreContract: address, _erc20TokenContract: address) -> bytes32:
    pass

@external
def addLoanToLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256):
    pass

@external
def removeLiquidation(_collateralAddress: address, _tokenId: uint256):
    pass