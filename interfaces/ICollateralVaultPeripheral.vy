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
event CollateralVaultCoreAddressSet:
    currentValue: address
    newValue: address
event LoansPeripheralAddressAdded:
    erc20TokenContractIndexed: address
    currentValue: address
    newValue: address
    erc20TokenContract: address
event LoansPeripheralAddressRemoved:
    erc20TokenContractIndexed: address
    currentValue: address
    erc20TokenContract: address
event LiquidationsPeripheralAddressSet:
    currentValue: address
    newValue: address
event CollateralStored:
    collateralAddressIndexed: address
    fromIndexed: address
    collateralAddress: address
    tokenId: uint256
    _from: address
event CollateralFromLoanTransferred:
    collateralAddressIndexed: address
    toIndexed: address
    collateralAddress: address
    tokenId: uint256
    _to: address
event CollateralFromLiquidationTransferred:
    collateralAddressIndexed: address
    toIndexed: address
    collateralAddress: address
    tokenId: uint256
    _to: address
event OperatorApproved:
    collateralAddressIndexed: address
    toIndexed: address
    collateralAddress: address
    tokenId: uint256
    operator: address

# Functions

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
def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address):
    pass

@external
def transferCollateralFromLoan(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address):
    pass

@external
def transferCollateralFromLiquidation(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    pass

@external
def approveBackstopBuyer(_address: address, _collateralAddress: address, _tokenId: uint256):
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
def collateralVaultCoreDefaultAddress() -> address:
    pass

@view
@external
def collateralVaultCoreAddresses(_collateralAddress: address) -> address:
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
def vaultAddress(_collateralAddress: address) -> address:
    pass

@view
@external
def isCollateralInVault(_collateralAddress: address, _tokenId: uint256) -> bool:
    pass
