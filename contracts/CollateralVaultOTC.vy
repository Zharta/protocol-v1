
# @version 0.3.9

"""
@title CollateralVaultOTC
@author [Zharta](https://zharta.io/)
@notice The lending pool contract implements the lending pool logic. Each instance works with a corresponding loans contract to implement an isolated lending market.
@dev Uses a `CollateralVaultCore` to store ERC721 collaterals, and supports different vault cores (eg CryptoPunksVaultCore) as extension points for other protocols.
"""



# Interfaces


from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721

interface CryptoPunksMarket:
    def transferPunk(to: address, punkIndex: uint256): nonpayable
    def buyPunk(punkIndex: uint256): payable
    def punksOfferedForSale(punkIndex: uint256) -> Offer: view
    def punkIndexToAddress(punkIndex: uint256) -> address: view
    def offerPunkForSaleToAddress(punkIndex: uint256, minSalePriceInWei: uint256, toAddress: address): nonpayable

interface IDelegationRegistry:
    def delegateForToken(delegate: address, contract_: address, tokenId: uint256, value_: bool): nonpayable

interface ISelf:
    def initialize(_owner: address): nonpayable



# Structs


# cryptopunks Offer
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

event LoansPeripheralAddressSet:
    currentValue: address
    newValue: address

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



# Global variables


vaultName: constant(String[3]) = "otc"

owner: public(address)
proposedOwner: public(address)

loansAddress: public(address)
liquidationsPeripheralAddress: public(address)

cryptoPunksMarketAddress: public(immutable(CryptoPunksMarket))
delegationRegistry: public(immutable(IDelegationRegistry))



##### INTERNAL METHODS - VIEW #####


@pure
@internal
def _is_punk(_collateralAddress: address) -> bool:
    return _collateralAddress == cryptoPunksMarketAddress.address


@view
@internal
def _is_erc721(_collateralAddress: address) -> bool:
    return IERC165(_collateralAddress).supportsInterface(0x80ac58cd)


@view
@internal
def _punk_owner(_collateralAddress: address, _tokenId: uint256) -> address:
    return CryptoPunksMarket(_collateralAddress).punkIndexToAddress(_tokenId)


@view
@internal
def _erc721_owner(_collateralAddress: address, _tokenId: uint256) -> address:
    return IERC721(_collateralAddress).ownerOf(_tokenId)


@view
@internal
def _is_punk_approved_for_vault(_borrower: address, _collateralAddress: address, _tokenId: uint256) -> bool:
    offer: Offer = cryptoPunksMarketAddress.punksOfferedForSale(_tokenId)
    return (
        offer.isForSale and
        offer.punkIndex == _tokenId and
        offer.minValue == 0 and
        (offer.onlySellTo == empty(address) or offer.onlySellTo == self)
    )


@view
@internal
def _is_erc721_approved_for_vault(_borrower: address, _collateralAddress: address, _tokenId: uint256) -> bool:
    return IERC721(_collateralAddress).isApprovedForAll(_borrower, self) or IERC721(_collateralAddress).getApproved(_tokenId) == self


@view
@internal
def _vault_owns_collateral(_collateralAddress: address, _tokenId: uint256) -> bool:
    if self._is_punk(_collateralAddress):
        return self._punk_owner(_collateralAddress, _tokenId) == self
    elif self._is_erc721(_collateralAddress):
        return self._erc721_owner(_collateralAddress, _tokenId) == self
    else:
        return False



##### INTERNAL METHODS - WRITE #####



@internal
def _setDelegation(_wallet: address, _collateralAddress: address, _tokenId: uint256, _value: bool):
    delegationRegistry.delegateForToken(_wallet, _collateralAddress, _tokenId, _value)


@internal
def _store_punk(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    offer: Offer = CryptoPunksMarket(_collateralAddress).punksOfferedForSale(_tokenId)

    assert offer.isForSale, "collateral not for sale"
    assert offer.punkIndex == _tokenId, "collateral with wrong punkIndex"
    assert offer.seller == _wallet, "collateral now owned by wallet"
    assert offer.minValue == 0, "collateral offer is not zero"
    assert offer.onlySellTo == empty(address) or offer.onlySellTo == self, "collateral buying not authorized"

    CryptoPunksMarket(_collateralAddress).buyPunk(_tokenId)


@internal
def _store_erc721(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    IERC721(_collateralAddress).safeTransferFrom(_wallet, self, _tokenId, b"")


@internal
def _transfer_punk(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    assert self._punk_owner(_collateralAddress, _tokenId) == self, "collateral not owned by vault"
    CryptoPunksMarket(_collateralAddress).transferPunk(_wallet, _tokenId)


@internal
def _transfer_erc721(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    assert self._erc721_owner(_collateralAddress, _tokenId) == self, "collateral not owned by vault"
    IERC721(_collateralAddress).safeTransferFrom(self, _wallet, _tokenId, b"")


@internal
def _transfer_collateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _delegateWallet: address):
    assert _delegateWallet != empty(address), "delegate is zero addr"

    if self._is_punk(_collateralAddress):
        self._transfer_punk(_wallet, _collateralAddress, _tokenId)
    elif self._is_erc721(_collateralAddress):
        self._transfer_erc721(_wallet, _collateralAddress, _tokenId)
    else:
        raise "address not supported by vault"

    self._setDelegation(_delegateWallet, _collateralAddress, _tokenId, False)



##### EXTERNAL METHODS - VIEW #####



@view
@external
def onERC721Received(_operator: address, _from: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    return method_id("onERC721Received(address,address,uint256,bytes)", output_type=bytes4)

@view
@external
def isCollateralInVault(_collateralAddress: address, _tokenId: uint256) -> bool:
    return self._vault_owns_collateral(_collateralAddress, _tokenId)

@view
@external
def isCollateralApprovedForVault(_borrower: address, _collateralAddress: address, _tokenId: uint256) -> bool:
    if self._is_punk(_collateralAddress):
        return self._is_punk_approved_for_vault(_borrower, _collateralAddress, _tokenId)
    elif self._is_erc721(_collateralAddress):
        return self._is_erc721_approved_for_vault(_borrower, _collateralAddress, _tokenId)
    else:
        raise "address not supported by vault"


@view
@external
def vaultName() -> String[3]:
    return vaultName

##### EXTERNAL METHODS - WRITE #####

@external
def __init__(_cryptoPunksMarketAddress: address, _delegationRegistryAddress: address):
    self.owner = msg.sender
    cryptoPunksMarketAddress = CryptoPunksMarket(_cryptoPunksMarketAddress)
    delegationRegistry = IDelegationRegistry(_delegationRegistryAddress)


@external
def initialize(_owner: address):
    assert _owner != empty(address), "owner is the zero address"
    assert self.owner == empty(address), "already initialized"
    self.owner = _owner


@external
def create_proxy() -> address:
    proxy: address = create_minimal_proxy_to(self)
    ISelf(proxy).initialize(msg.sender)
    return proxy


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
def setLoansAddress(_address: address):
    assert msg.sender == self.owner  # reason: msg.sender is not the owner
    assert _address != empty(address)  # reason: address is the zero addr

    log LoansPeripheralAddressSet(self.loansAddress, _address)

    self.loansAddress = _address

@external
def setLiquidationsPeripheralAddress(_address: address):
    assert msg.sender == self.owner  # reason: msg.sender is not the owner
    assert _address != empty(address)  # reason: address is the zero addr

    log LiquidationsPeripheralAddressSet(self.liquidationsPeripheralAddress, _address)

    self.liquidationsPeripheralAddress = _address



@external
def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address, _createDelegation: bool):

    """
    @notice Stores the given collateral
    @dev Logs the `CollateralStored` event
    @param _wallet The wallet to transfer the collateral from
    @param _collateralAddress The collateral contract address
    @param _tokenId The token id of the collateral
    @param _erc20TokenContract The token address by which the loans contract is indexed
    @param _createDelegation Wether to set _wallet as a delegate for the token
    """

    assert _wallet != empty(address), "address is the zero addr"
    assert _collateralAddress != empty(address), "collat addr is the zero addr"
    assert _erc20TokenContract != empty(address), "address is the zero addr"
    assert self.loansAddress != empty(address), "mapping not found"
    assert msg.sender == self.loansAddress, "msg.sender is not authorised"

    if self._is_punk(_collateralAddress):
        assert self._punk_owner(_collateralAddress, _tokenId) == _wallet, "collateral not owned by wallet"
        assert self._is_punk_approved_for_vault(_wallet, _collateralAddress, _tokenId), "transfer is not approved"
        self._store_punk(_wallet, _collateralAddress, _tokenId)

    elif  self._is_erc721(_collateralAddress):
        assert self._erc721_owner(_collateralAddress, _tokenId) == _wallet, "collateral not owned by wallet"
        assert self._is_erc721_approved_for_vault(_wallet, _collateralAddress, _tokenId), "transfer is not approved"
        self._store_erc721(_wallet, _collateralAddress, _tokenId)

    else:
        raise "address not supported by vault"

    if _createDelegation:
        self._setDelegation(_wallet, _collateralAddress, _tokenId, True)

    log CollateralStored(
        _collateralAddress,
        _wallet,
        _collateralAddress,
        _tokenId,
        _wallet,
        _wallet if _createDelegation else empty(address)
    )



@external
def transferCollateralFromLoan(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address):

    """
    @notice Transfers the given collateral from the vault to a wallet
    @dev Logs the `CollateralFromLoanTransferred` event; to be used by `LoansPeripheral`
    @param _wallet The wallet to transfer the collateral to
    @param _collateralAddress The collateral contract address
    @param _tokenId The token id of the collateral
    @param _erc20TokenContract The token address by which the loans contract is indexed
    """

    assert _wallet != empty(address), "address is the zero addr"
    assert _collateralAddress != empty(address), "collat addr is the zero addr"
    assert _erc20TokenContract != empty(address), "address is the zero addr"
    assert self.loansAddress != empty(address), "mapping not found"
    assert msg.sender == self.loansAddress, "msg.sender is not authorised"

    self._transfer_collateral(_wallet, _collateralAddress, _tokenId, _wallet)

    log CollateralFromLoanTransferred(
        _collateralAddress,
        _wallet,
        _collateralAddress,
        _tokenId,
        _wallet
    )



@external
def transferCollateralFromLiquidation(_wallet: address, _collateralAddress: address, _tokenId: uint256):

    """
    @notice Transfers the given collateral from the vault to a wallet, as part of a liquidation
    @dev Logs the `CollateralFromLiquidationTransferred` event; to be used by `LiquidationsPeripheral`
    @param _wallet The wallet to transfer the collateral to
    @param _collateralAddress The collateral contract address
    @param _tokenId The token id of the collateral
    """

    assert msg.sender == self.liquidationsPeripheralAddress, "msg.sender is not authorised"
    assert _wallet != empty(address), "address is the zero addr"
    assert _collateralAddress != empty(address), "collat addr is the zero addr"

    self._transfer_collateral(_wallet, _collateralAddress, _tokenId, _wallet)

    log CollateralFromLiquidationTransferred(
        _collateralAddress,
        _wallet,
        _collateralAddress,
        _tokenId,
        _wallet
    )



@external
def setCollateralDelegation(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address, _value: bool):

    """
    @notice Creates or removes a token delegation for the given collateral
    @param _wallet The wallet to delegate the collateral to
    @param _collateralAddress The collateral contract address
    @param _tokenId The token id of the collateral
    @param _erc20TokenContract The token address by which the loans contract is indexed
    @param _value Wether to set or unset the delegation
    """

    assert _wallet != empty(address), "address is the zero addr"
    assert _collateralAddress != empty(address), "collat addr is the zero addr"
    assert self.loansAddress != empty(address), "mapping not found"
    assert msg.sender == self.loansAddress, "msg.sender is not authorised"

    self._setDelegation(_wallet, _collateralAddress, _tokenId, _value)



@view
@external
def collateralSupportsDelegation(_collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address) -> bool:

    """
    @notice Returns wether a token delegation for the given collateral is supported
    @param _collateralAddress The collateral contract address
    @param _tokenId The token id of the collateral
    @param _erc20TokenContract The token address by which the loans contract is indexed
    """

    return self._vault_owns_collateral(_collateralAddress, _tokenId)


