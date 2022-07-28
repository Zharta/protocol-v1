# Structs

struct Collateral:
    contractAddress: address
    tokenId: uint256

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool

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
event GracePeriodDurationChanged:
    currentValue: uint256
    newValue: uint256
event BuyNowPeriodDurationChanged:
    currentValue: uint256
    newValue: uint256
event AuctionPeriodDurationChanged:
    currentValue: uint256
    newValue: uint256
event BuyNowCoreAddressSet:
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
event LendingPoolPeripheralAddressAdded:
    erc20TokenContractIndexed: address
    currentValue: address
    newValue: address
    erc20TokenContract: address
event LendingPoolPeripheralAddressRemoved:
    erc20TokenContractIndexed: address
    currentValue: address
    erc20TokenContract: address
event CollateralVaultPeripheralAddressSet:
    currentValue: address
    newValue: address
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
event NFTPurchased:
    erc20TokenContractIndexed: address
    collateralAddressIndexed: address
    collateralAddress: address
    tokenId: uint256
    amount: uint256
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
def setGracePeriodDuration(_duration: uint256):
    pass

@external
def setBuyNowPeriodDuration(_duration: uint256):
    pass

@external
def setAuctionPeriodDuration(_duration: uint256):
    pass

@external
def setBuyNowCoreAddress(_address: address):
    pass

@external
def addLoansCoreAddress(_erc20TokenContract: address, _address: address):
    pass

@external
def removeLoansCoreAddress(_erc20TokenContract: address):
    pass

@external
def addLendingPoolPeripheralAddress(_erc20TokenContract: address, _address: address):
    pass

@external
def removeLendingPoolPeripheralAddress(_erc20TokenContract: address):
    pass

@external
def setCollateralVaultPeripheralAddress(_address: address):
    pass

@external
def addLiquidation(_collateralAddress: address, _tokenId: uint256, _principal: uint256, _interestAmount: uint256, _apr: uint256, _borrower: address, _loanId: uint256, _erc20TokenContract: address):
    pass

@external
def buyNFT(_collateralAddress: address, _tokenId: uint256):
    pass

@external
def liquidateNFTX():
    pass

@external
def liquidateOpenSea():
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
def gracePeriodDuration() -> uint256:
    pass

@view
@external
def buyNowPeriodDuration() -> uint256:
    pass

@view
@external
def auctionPeriodDuration() -> uint256:
    pass

@view
@external
def buyNowCoreAddress() -> address:
    pass

@view
@external
def loansCoreAddresses(arg0: address) -> address:
    pass

@view
@external
def lendingPoolPeripheralAddresses(arg0: address) -> address:
    pass

@view
@external
def collateralVaultPeripheralAddress() -> address:
    pass

@view
@external
def lenderMinDepositAmount() -> uint256:
    pass


