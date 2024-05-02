# @version 0.3.10

"""
@title CollateralVaultPeripheral
@author [Zharta](https://zharta.io/)
@notice The lending pool contract implements the lending pool logic. Each instance works with a corresponding loans contract to implement an isolated lending market.
@dev Uses a `CollateralVaultCore` to store ERC721 collaterals, and supports different vault cores (eg CryptoPunksVaultCore) as extension points for other protocols.
"""

# Interfaces

from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721

interface ILegacyVault:
    def setCollateralVaultPeripheralAddress(_address: address): nonpayable
    def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256): nonpayable
    def transferCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256): nonpayable

interface IVault:
    def setCollateralVaultPeripheralAddress(_address: address): nonpayable
    def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _delegate_wallet: address): nonpayable
    def transferCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _delegate_wallet: address): nonpayable
    def setDelegation(_wallet: address, _collateralAddress: address, _tokenId: uint256, _value: bool): nonpayable
    def collateralOwner(_collateralAddress: address, _tokenId: uint256) -> address: view
    def ownsCollateral(_collateralAddress: address, _tokenId: uint256) -> bool: view
    def isCollateralApprovedForVault(_borrower: address, _collateralAddress: address, _tokenId: uint256) -> bool: view
    def vaultName() -> String[30]: view

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

owner: public(address)
proposedOwner: public(address)

collateralVaultCoreDefaultAddress: public(address)
collateralVaultCoreAddresses: public(HashMap[address, address])
loansPeripheralAddresses: public(HashMap[address, address]) # mapping between ERC20 contract and LoansCore
liquidationsPeripheralAddress: public(address) # mapping between ERC20 contract and LoansCore


##### INTERNAL METHODS #####

@view
@internal
def _getVaultAddress(_collateralAddress: address, _tokenId: uint256) -> address:
    vault : address = self.collateralVaultCoreAddresses[_collateralAddress]
    if vault != empty(address):
        return vault
    return self.collateralVaultCoreDefaultAddress

##### EXTERNAL METHODS - VIEW #####

@view
@external
def vaultAddress(_collateralAddress: address, _tokenId: uint256) -> address:
    return self._getVaultAddress(_collateralAddress, _tokenId)

@view
@external
def isCollateralInVault(_collateralAddress: address, _tokenId: uint256) -> bool:
    return IVault(self._getVaultAddress(_collateralAddress, _tokenId)).ownsCollateral(_collateralAddress, _tokenId)

@view
@external
def isCollateralApprovedForVault(_borrower: address, _collateralAddress: address, _tokenId: uint256) -> bool:
    return IVault(self._getVaultAddress(_collateralAddress, _tokenId)).isCollateralApprovedForVault(_borrower, _collateralAddress, _tokenId)


##### EXTERNAL METHODS - WRITE #####
@external
def __init__(_collerateralVaultCoreAddress: address):
    assert _collerateralVaultCoreAddress != empty(address), "core address is the zero address"

    self.owner = msg.sender
    self.collateralVaultCoreDefaultAddress = _collerateralVaultCoreAddress



@external
def addVault(_collateral_address: address, _vault_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _collateral_address != empty(address), "contract addr is the zero addr"
    assert _vault_address != empty(address), "vault address is the zero addr"

    log CollateralVaultAdded(
        _collateral_address,
        self.collateralVaultCoreAddresses[_collateral_address],
        _vault_address,
        _collateral_address
    )

    self.collateralVaultCoreAddresses[_collateral_address] = _vault_address


@external
def removeVault(_collateral_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _collateral_address != empty(address), "contract addr is the zero addr"
    assert self.collateralVaultCoreAddresses[_collateral_address] != empty(address), "address not found"

    log CollateralVaultRemoved(
        _collateral_address,
        self.collateralVaultCoreAddresses[_collateral_address],
        _collateral_address
    )

    self.collateralVaultCoreAddresses[_collateral_address] = empty(address)

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
def addLoansPeripheralAddress(_erc20TokenContract: address, _address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
    assert self.loansPeripheralAddresses[_erc20TokenContract] != _address, "new value is the same"

    log LoansPeripheralAddressAdded(
        _erc20TokenContract,
        self.loansPeripheralAddresses[_erc20TokenContract],
        _address,
        _erc20TokenContract
    )

    self.loansPeripheralAddresses[_erc20TokenContract] = _address


@external
def removeLoansPeripheralAddress(_erc20TokenContract: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
    assert self.loansPeripheralAddresses[_erc20TokenContract] != empty(address), "address not found"

    log LoansPeripheralAddressRemoved(
        _erc20TokenContract,
        self.loansPeripheralAddresses[_erc20TokenContract],
        _erc20TokenContract
    )

    self.loansPeripheralAddresses[_erc20TokenContract] = empty(address)


@external
def setLiquidationsPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert self.liquidationsPeripheralAddress != _address, "new value is the same"

    log LiquidationsPeripheralAddressSet(
        self.liquidationsPeripheralAddress,
        _address
    )

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
    assert self.loansPeripheralAddresses[_erc20TokenContract] != empty(address), "mapping not found"
    assert msg.sender == self.loansPeripheralAddresses[_erc20TokenContract], "msg.sender is not authorised"

    vault : address = self._getVaultAddress(_collateralAddress, _tokenId)

    assert IVault(vault).collateralOwner(_collateralAddress, _tokenId) == _wallet, "collateral not owned by wallet"
    assert IVault(vault).isCollateralApprovedForVault(_wallet, _collateralAddress, _tokenId), "transfer is not approved"

    delegate: address = empty(address)
    if _createDelegation:
        delegate = _wallet
    IVault(vault).storeCollateral(_wallet, _collateralAddress, _tokenId, delegate)

    log CollateralStored(
        _collateralAddress,
        _wallet,
        _collateralAddress,
        _tokenId,
        _wallet,
        delegate
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
    assert self.loansPeripheralAddresses[_erc20TokenContract] != empty(address), "mapping not found"
    assert msg.sender == self.loansPeripheralAddresses[_erc20TokenContract], "msg.sender is not authorised"

    IVault(self._getVaultAddress(_collateralAddress, _tokenId)).transferCollateral(_wallet, _collateralAddress, _tokenId, _wallet)

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

    IVault(self._getVaultAddress(_collateralAddress, _tokenId)).transferCollateral(_wallet, _collateralAddress, _tokenId, _wallet)

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
    assert self.loansPeripheralAddresses[_erc20TokenContract] != empty(address), "mapping not found"
    assert msg.sender == self.loansPeripheralAddresses[_erc20TokenContract], "msg.sender is not authorised"

    IVault(self._getVaultAddress(_collateralAddress, _tokenId)).setDelegation(_wallet, _collateralAddress, _tokenId, _value)


@view
@external
def collateralSupportsDelegation(_collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address) -> bool:

    """
    @notice Returns wether a token delegation for the given collateral is supported
    @param _collateralAddress The collateral contract address
    @param _tokenId The token id of the collateral
    @param _erc20TokenContract The token address by which the loans contract is indexed
    """

    return IVault(self._getVaultAddress(_collateralAddress, _tokenId)).ownsCollateral(_collateralAddress, _tokenId)
