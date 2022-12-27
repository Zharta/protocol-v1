# Structs

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
def collateralVaultCoreDefaultAddress() -> address:
    pass

@view
@external
def collateralVaultCoreAddresses(arg0: address) -> address:
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

@external
def addVault(_collateral_address: address, _vault_address: address):
    pass

@external
def removeVault(_collateral_address: address):
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