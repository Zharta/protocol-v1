# Structs

struct Collateral:
    contractAddress: address
    tokenId: uint256
    amount: uint256

struct Loan:
    id: uint256
    amount: uint256
    interest: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    maturity: uint256
    startTime: uint256
    collaterals: DynArray[Collateral, 100]
    paidPrincipal: uint256
    paidInterestAmount: uint256
    started: bool
    invalidated: bool
    paid: bool
    defaulted: bool
    canceled: bool

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    lockPeriodEnd: uint256
    activeForRewards: bool

struct Liquidation:
    lid: bytes32
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    lenderPeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    gracePeriodPrice: uint256
    lenderPeriodPrice: uint256
    borrower: address
    loanId: uint256
    loansCoreContract: address
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
event LendersPeriodDurationChanged:
    currentValue: uint256
    newValue: uint256
event AuctionPeriodDurationChanged:
    currentValue: uint256
    newValue: uint256
event LiquidationsCoreAddressSet:
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
event NFTXVaultFactoryAddressSet:
    currentValue: address
    newValue: address
event NFTXMarketplaceZapAddressSet:
    currentValue: address
    newValue: address
event SushiRouterAddressSet:
    currentValue: address
    newValue: address
event LiquidationAdded:
    erc20TokenContractIndexed: address
    collateralAddressIndexed: address
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address
    gracePeriodPrice: uint256
    lenderPeriodPrice: uint256
    gracePeriodMaturity: uint256
    lenderPeriodMaturity: uint256
    loansCoreContract: address
    loanId: uint256
    borrower: address
event LiquidationRemoved:
    erc20TokenContractIndexed: address
    collateralAddressIndexed: address
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address
    loansCoreContract: address
    loanId: uint256
    borrower: address
event NFTPurchased:
    erc20TokenContractIndexed: address
    collateralAddressIndexed: address
    buyerAddressIndexed: address
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    amount: uint256
    buyerAddress: address
    erc20TokenContract: address
    method: String[30]
event AdminWithdrawal:
    collateralAddressIndexed: address
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    wallet: address

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
def setLendersPeriodDuration(_duration: uint256):
    pass

@external
def setAuctionPeriodDuration(_duration: uint256):
    pass

@external
def setLiquidationsCoreAddress(_address: address):
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
def setNFTXVaultFactoryAddress(_address: address):
    pass

@external
def setNFTXMarketplaceZapAddress(_address: address):
    pass

@external
def setSushiRouterAddress(_address: address):
    pass

@external
def addLiquidation(_borrower: address, _loanId: uint256, _erc20TokenContract: address):
    pass

@external
def payLoanLiquidationsGracePeriod(_loanId: uint256, _erc20TokenContract: address):
    pass

@external
def buyNFTGracePeriod(_collateralAddress: address, _tokenId: uint256):
    pass

@external
def buyNFTLenderPeriod(_collateralAddress: address, _tokenId: uint256):
    pass

@external
def liquidateNFTX(_collateralAddress: address, _tokenId: uint256):
    pass

@external
def adminWithdrawal(_walletAddress: address, _collateralAddress: address, _tokenId: uint256):
    pass

@external
def adminLiquidation(_principal: uint256, _interestAmount: uint256, _liquidationId: bytes32, _erc20TokenContract: address, _collateralAddress: address, _tokenId: uint256):
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
def lenderPeriodDuration() -> uint256:
    pass

@view
@external
def auctionPeriodDuration() -> uint256:
    pass

@view
@external
def liquidationsCoreAddress() -> address:
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
def nftxVaultFactoryAddress() -> address:
    pass

@view
@external
def nftxMarketplaceZapAddress() -> address:
    pass

@view
@external
def sushiRouterAddress() -> address:
    pass


