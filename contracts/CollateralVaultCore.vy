# @version ^0.3.3


# Interfaces

from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721


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


# Global variables

owner: public(address)
proposedOwner: public(address)

collateralVaultPeripheralAddress: public(address)

##### INTERNAL METHODS #####




##### EXTERNAL METHODS - VIEW #####

@view
@external
def onERC721Received(_operator: address, _from: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    return convert(method_id("onERC721Received(address,address,uint256,bytes)", output_type=Bytes[4]), bytes4)


##### EXTERNAL METHODS - WRITE #####
@external
def __init__():
    self.owner = msg.sender


@external
def proposeOwner(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address it the zero address"
    assert self.owner != _address, "proposed owner addr is the owner"
    assert self.proposedOwner != _address, "proposed owner addr is the same"

    self.proposedOwner = _address

    log OwnerProposed(
        self.owner,
        _address,
        self.owner,
        _address
    )


@external
def claimOwnership():
    assert msg.sender == self.proposedOwner, "msg.sender is not the proposed"

    log OwnershipTransferred(
        self.owner,
        self.proposedOwner,
        self.owner,
        self.proposedOwner
    )

    self.owner = self.proposedOwner
    self.proposedOwner = ZERO_ADDRESS


@external
def setCollateralVaultPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert self.collateralVaultPeripheralAddress != _address, "new value is the same"

    log CollateralVaultPeripheralAddressSet(
        self.collateralVaultPeripheralAddress,
        _address
    )

    self.collateralVaultPeripheralAddress = _address


@external
def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.collateralVaultPeripheralAddress, "msg.sender is not authorised"

    IERC721(_collateralAddress).safeTransferFrom(_wallet, self, _tokenId, b"")


@external
def transferCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.collateralVaultPeripheralAddress, "msg.sender is not authorised"

    IERC721(_collateralAddress).safeTransferFrom(self, _wallet,  _tokenId, b"")
