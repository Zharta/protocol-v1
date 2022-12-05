
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

event CollateralVaultPeripheralAddressSet:
    currentValue: address
    newValue: address


# Functions

@view
def vaultName() -> String[30]:
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
def collateralVaultPeripheralAddress() -> address:
    pass

@view
@external
def collateralOwner(_tokenId: uint256) -> address:
    pass

@view
@external
def isApproved(_tokenId: uint256, _wallet: address) ->
    pass

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass


@external
def setCollateralVaultPeripheralAddress(_address: address):
    pass


@external
def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    pass


@external
def transferCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    pass


@external
def approveOperator(_address: address, _collateralAddress: address, _tokenId: uint256):
    pass

