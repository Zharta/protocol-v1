# @version ^0.3.6


# Interfaces

from vyper.interfaces import ERC721 as IERC721

interface CryptoPunksMarket:
    def transferPunk(to: address, punkIndex: uint256): nonpayable
    def buyPunk(punkIndex: uint256): payable
    def punksOfferedForSale(punkIndex: uint256) -> Offer: view
    def punkIndexToAddress(punkIndex: uint256) -> address: view
    def offerPunkForSaleToAddress(punkIndex: uint256, minSalePriceInWei: uint256, toAddress: address): nonpayable


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

event CollateralVaultPeripheralAddressSet:
    currentValue: address
    newValue: address


# Global variables

owner: public(address)
proposedOwner: public(address)

vaultName: constant(String[30]) = "cryptopunks"
collateralVaultPeripheralAddress: public(address)
cryptoPunksMarketAddress: address

##### INTERNAL METHODS #####


##### EXTERNAL METHODS - VIEW #####

@view
@external
def vaultName() -> String[30]:
    return vaultName


@view
@external
def collateralOwner(_tokenId: uint256) -> address:
    return CryptoPunksMarket(self.cryptoPunksMarketAddress).punkIndexToAddress(_tokenId)

@view
@external
def isApproved(_tokenId: uint256, _wallet: address) -> bool:
    offer: Offer = CryptoPunksMarket(self.cryptoPunksMarketAddress).punksOfferedForSale(_tokenId)
    return (
        offer.isForSale and
        offer.punkIndex == _tokenId and
        offer.minValue == 0 and
        (offer.onlySellTo == empty(address) or offer.onlySellTo == _wallet)
    )

##### EXTERNAL METHODS - WRITE #####
@external
def __init__(_cryptoPunksMarketAddress: address):
    self.owner = msg.sender
    self.cryptoPunksMarketAddress = _cryptoPunksMarketAddress


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
    assert _collateralAddress == self.cryptoPunksMarketAddress, "collateral address not supported by vault"

    offer: Offer = CryptoPunksMarket(_collateralAddress).punksOfferedForSale(_tokenId)

    assert offer.isForSale, "collateral not for sale"
    assert offer.punkIndex == _tokenId, "collateral with wrong punkIndex"
    assert offer.seller == _wallet, "collateral now owned by wallet"
    assert offer.minValue == 0, "collateral offer value is not zero"
    assert offer.onlySellTo == empty(address) or offer.onlySellTo == self, "collateral buying not authorized"

    CryptoPunksMarket(_collateralAddress).buyPunk(_tokenId)


@external
def transferCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.collateralVaultPeripheralAddress, "msg.sender is not authorised"
    assert _collateralAddress == self.cryptoPunksMarketAddress, "collateral address not supported by vault"
    assert CryptoPunksMarket(_collateralAddress).punkIndexToAddress(_tokenId) == self, "collateral now owned by vault"

    CryptoPunksMarket(_collateralAddress).transferPunk(_wallet, _tokenId)


@external
def approveOperator(_address: address, _collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.collateralVaultPeripheralAddress, "msg.sender is not authorised"
    assert _collateralAddress == self.cryptoPunksMarketAddress, "collateral address not supported by vault"
    CryptoPunksMarket(_collateralAddress).offerPunkForSaleToAddress(_tokenId, 0, _address) 
