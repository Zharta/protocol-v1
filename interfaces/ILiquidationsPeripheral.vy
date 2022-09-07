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
    method: String[20]

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
def addLiquidation(_collateralAddress: address, _tokenId: uint256, _borrower: address, _loanId: uint256, _erc20TokenContract: address):
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

@view
@external
def lenderMinDepositAmount() -> uint256:
    pass


