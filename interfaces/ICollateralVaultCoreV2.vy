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

event CollateralVaultPeripheralAddressSet:
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
def collateralVaultPeripheralAddress() -> address:
    pass

@view
@external
def delegationRegistry() -> IDelegationRegistry:
    pass

@view
@external
def vaultName() -> String[30]:
    pass

@view
@external
def onERC721Received(_operator: address, _from: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    pass

@view
@external
def collateralOwner(_collateralAddress: address, _tokenId: uint256) -> address:
    pass

@view
@external
def ownsCollateral(_collateralAddress: address, _tokenId: uint256) -> bool:
    pass

@view
@external
def isCollateralApprovedForVault(_borrower: address, _collateralAddress: address, _tokenId: uint256) -> bool:
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
def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _delegateWallet: address):
    pass

@external
def transferCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _delegateWallet: address):
    pass

@external
def setDelegation(_wallet: address, _collateralAddress: address, _tokenId: uint256, _value: bool):
    pass