# Structs

struct Offer:
    isForSale: bool
    punkIndex: uint256
    seller: address
    minValue: uint256
    onlySellTo: address

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

event CollateralVaultAdded:
    collateralContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    collateralContract: address

event CollateralVaultRemoved:
    collateralContractIndexed: indexed(address)
    currentValue: address
    collateralContract: address

event LoansPeripheralAddressAdded:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LoansPeripheralAddressRemoved:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    erc20TokenContract: address

event LiquidationsPeripheralAddressSet:
    currentValue: address
    newValue: address

event CollateralStored:
    collateralAddressIndexed: indexed(address)
    fromIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    _from: address
    delegate: address

event CollateralFromLoanTransferred:
    collateralAddressIndexed: indexed(address)
    toIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    _to: address

event CollateralFromLiquidationTransferred:
    collateralAddressIndexed: indexed(address)
    toIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    _to: address

event OperatorApproved:
    collateralAddressIndexed: indexed(address)
    toIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    operator: address

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
def loansPeripheralAddresses(arg0: address) -> address:
    pass

@view
@external
def liquidationsPeripheralAddress() -> address:
    pass

@view
@external
def cryptoPunksMarketAddress() -> CryptoPunksMarket:
    pass

@view
@external
def delegationRegistry() -> IDelegationRegistry:
    pass

@view
@external
def onERC721Received(_operator: address, _from: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    pass

@view
@external
def isCollateralInVault(_collateralAddress: address, _tokenId: uint256) -> bool:
    pass

@view
@external
def isCollateralApprovedForVault(_borrower: address, _collateralAddress: address, _tokenId: uint256) -> bool:
    pass

@view
@external
def vaultName() -> String[3]:
    pass

@external
def initialize(_owner: address):
    pass

@external
def create_proxy() -> address:
    pass

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass

@external
def addLoansPeripheralAddress(_erc20TokenContract: address, _address: address):
    pass

@external
def removeLoansPeripheralAddress(_erc20TokenContract: address):
    pass

@external
def setLiquidationsPeripheralAddress(_address: address):
    pass

@external
def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address, _createDelegation: bool):
    pass

@external
def transferCollateralFromLoan(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address):
    pass

@external
def transferCollateralFromLiquidation(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    pass

@external
def setCollateralDelegation(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address, _value: bool):
    pass

@view
@external
def collateralSupportsDelegation(_collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address) -> bool:
    pass