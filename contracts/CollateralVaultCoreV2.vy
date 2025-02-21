# @version 0.4.0


# Interfaces

from ethereum.ercs import IERC165
from ethereum.ercs import IERC721

interface IDelegationRegistry:
    def delegateForToken(delegate: address, contract_: address, tokenId: uint256, value_: bool): nonpayable

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

vaultName: public(constant(String[30])) = "erc721"

owner: public(address)
proposedOwner: public(address)

collateralVaultPeripheralAddress: public(address)
delegationRegistry: public(IDelegationRegistry)

##### INTERNAL METHODS #####


@internal
def _setDelegation(_wallet: address, _collateralAddress: address, _tokenId: uint256, _value: bool):
    extcall self.delegationRegistry.delegateForToken(_wallet, _collateralAddress, _tokenId, _value)

@view
@internal
def _collateralOwner(_collateralAddress: address, _tokenId: uint256) -> address:
    assert staticcall IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
    return staticcall IERC721(_collateralAddress).ownerOf(_tokenId)

##### EXTERNAL METHODS - VIEW #####


@view
@external
def onERC721Received(_operator: address, _from: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    return method_id("onERC721Received(address,address,uint256,bytes)", output_type=bytes4)


@view
@external
def collateralOwner(_collateralAddress: address, _tokenId: uint256) -> address:
    return self._collateralOwner(_collateralAddress, _tokenId)

@view
@external
def ownsCollateral(_collateralAddress: address, _tokenId: uint256) -> bool:
    return self._collateralOwner(_collateralAddress, _tokenId) == self


@view
@external
def isCollateralApprovedForVault(_borrower: address, _collateralAddress: address, _tokenId: uint256) -> bool:
    return staticcall IERC721(_collateralAddress).isApprovedForAll(_borrower, self) or staticcall IERC721(_collateralAddress).getApproved(_tokenId) == self


##### EXTERNAL METHODS - WRITE #####
@deploy
def __init__(_delegationRegistryAddress: address):
    self.owner = msg.sender
    self.delegationRegistry = IDelegationRegistry(_delegationRegistryAddress)


@external
def proposeOwner(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address it the zero address"
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
    self.proposedOwner = empty(address)


@external
def setCollateralVaultPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert self.collateralVaultPeripheralAddress != _address, "new value is the same"

    log CollateralVaultPeripheralAddressSet(
        self.collateralVaultPeripheralAddress,
        _address
    )

    self.collateralVaultPeripheralAddress = _address


@external
def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _delegateWallet: address):
    assert msg.sender == self.collateralVaultPeripheralAddress, "msg.sender is not authorised"

    extcall IERC721(_collateralAddress).safeTransferFrom(_wallet, self, _tokenId, b"")
    if _delegateWallet != empty(address):
        self._setDelegation(_delegateWallet, _collateralAddress, _tokenId, True)


@external
def transferCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _delegateWallet: address):
    assert msg.sender == self.collateralVaultPeripheralAddress, "msg.sender is not authorised"
    assert _delegateWallet != empty(address), "delegate is zero addr"
    assert self._collateralOwner(_collateralAddress, _tokenId) == self, "collateral not owned by vault"

    extcall IERC721(_collateralAddress).safeTransferFrom(self, _wallet, _tokenId, b"")
    self._setDelegation(_delegateWallet, _collateralAddress, _tokenId, False)


@external
def setDelegation(_wallet: address, _collateralAddress: address, _tokenId: uint256, _value: bool):
    assert msg.sender == self.collateralVaultPeripheralAddress, "msg.sender is not authorised"

    self._setDelegation(_wallet, _collateralAddress, _tokenId, _value)
