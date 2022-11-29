# @version ^0.3.6


# Interfaces

from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721
from interfaces import ICollateralVaultCore

interface IVault:
    def setCollateralVaultPeripheralAddress(_address: address): nonpayable
    def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256): nonpayable
    def transferCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256): nonpayable
    def approveOperator(_address: address, _collateralAddress: address, _tokenId: uint256): nonpayable

interface INonERC721Vault:
    def collateralOwner(_tokenId: uint256) -> address: view
    def isApproved(_tokenId: uint256, _wallet: address) -> bool: view


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

event CollateralVaultCoreAddressSet:
    currentValue: address
    newValue: address

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
def _getVaultAddress(_collateralAddress: address) -> address:
    vault : address = self.collateralVaultCoreAddresses[_collateralAddress]
    if vault == empty(address):
        vault = self.collateralVaultCoreDefaultAddress
    return vault

##### EXTERNAL METHODS - VIEW #####

@view
@external
def vaultAddress(_collateralAddress: address) -> address:
    return self._getVaultAddress(_collateralAddress)

@view
@external
def isCollateralInVault(_collateralAddress: address, _tokenId: uint256) -> bool:
    vault : address = self._getVaultAddress(_collateralAddress)
    if vault == self.collateralVaultCoreDefaultAddress:
        return IERC721(_collateralAddress).ownerOf(_tokenId) == self.collateralVaultCoreDefaultAddress
    else:
        return INonERC721Vault(vault).collateralOwner(_tokenId) == self.collateralVaultCoreDefaultAddress


##### EXTERNAL METHODS - WRITE #####
@external
def __init__(_collerateralVaultCoreAddress: address):
    assert _collerateralVaultCoreAddress != empty(address), "address is the zero address"
    assert _collerateralVaultCoreAddress.is_contract, "address is not a contract"

    self.owner = msg.sender
    self.collateralVaultCoreDefaultAddress = _collerateralVaultCoreAddress


@external
def addVault(_collateral_address: address, _vault_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _collateral_address != empty(address), "contract address is the zero addr"
    assert _vault_address != empty(address), "vault address is the zero addr"
    assert _collateral_address.is_contract, "contract address is not a contract"
    assert _vault_address.is_contract, "vault address is not a contract"
    assert self.collateralVaultCoreAddresses[_collateral_address] != _vault_address, "new value is the same"

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
    assert _collateral_address != empty(address), "contract address is the zero addr"
    assert _collateral_address.is_contract, "contract address is not a contract"
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
    assert _address.is_contract, "address is not a contract"
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
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
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
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
    assert _address.is_contract, "address is not a contract"
    assert self.liquidationsPeripheralAddress != _address, "new value is the same"

    log LiquidationsPeripheralAddressSet(
        self.liquidationsPeripheralAddress,
        _address
    )

    self.liquidationsPeripheralAddress = _address


@external
def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address):
    assert _wallet != empty(address), "address is the zero addr"
    assert _collateralAddress != empty(address), "collat addr is the zero addr"
    assert _erc20TokenContract != empty(address), "address is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"
    assert _erc20TokenContract.is_contract, "address is not a contract"
    assert self.loansPeripheralAddresses[_erc20TokenContract] != empty(address), "mapping not found"
    assert msg.sender == self.loansPeripheralAddresses[_erc20TokenContract], "msg.sender is not authorised"

    vault : address = self._getVaultAddress(_collateralAddress)
    if vault == self.collateralVaultCoreDefaultAddress:
        assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
        assert IERC721(_collateralAddress).ownerOf(_tokenId) == _wallet, "collateral not owned by wallet"
        assert IERC721(_collateralAddress).getApproved(_tokenId) == self.collateralVaultCoreDefaultAddress or IERC721(_collateralAddress).isApprovedForAll(_wallet, self.collateralVaultCoreDefaultAddress), "transfer is not approved"
    else:
        assert INonERC721Vault(vault).collateralOwner(_tokenId) == _wallet, "collateral not owned by wallet"
        assert INonERC721Vault(vault).isApproved(_tokenId, self.collateralVaultCoreDefaultAddress), "transfer is not approved"

    IVault(vault).storeCollateral(_wallet, _collateralAddress, _tokenId)

    log CollateralStored(
        _collateralAddress,
        _wallet,
        _collateralAddress,
        _tokenId,
        _wallet
    )


@external
def transferCollateralFromLoan(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address):
    assert _wallet != empty(address), "address is the zero addr"
    assert _collateralAddress != empty(address), "collat addr is the zero addr"
    assert _erc20TokenContract != empty(address), "address is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"
    assert _erc20TokenContract.is_contract, "address is not a contract"
    assert self.loansPeripheralAddresses[_erc20TokenContract] != empty(address), "mapping not found"
    assert msg.sender == self.loansPeripheralAddresses[_erc20TokenContract], "msg.sender is not authorised"

    vault : address = self._getVaultAddress(_collateralAddress)
    if vault == self.collateralVaultCoreDefaultAddress:
        assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
        assert IERC721(_collateralAddress).ownerOf(_tokenId) == self.collateralVaultCoreDefaultAddress, "collateral not owned by CVCore"
    else:
        assert INonERC721Vault(vault).collateralOwner(_tokenId) == self.collateralVaultCoreDefaultAddress, "collateral not owned by CVCore"

    IVault(vault).transferCollateral(_wallet, _collateralAddress, _tokenId)

    log CollateralFromLoanTransferred(
        _collateralAddress,
        _wallet,
        _collateralAddress,
        _tokenId,
        _wallet
    )


@external
def transferCollateralFromLiquidation(_wallet: address, _collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.liquidationsPeripheralAddress, "msg.sender is not authorised"
    assert _wallet != empty(address), "address is the zero addr"
    assert _collateralAddress != empty(address), "collat addr is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"

    vault : address = self._getVaultAddress(_collateralAddress)
    if vault == self.collateralVaultCoreDefaultAddress:
        assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
        assert IERC721(_collateralAddress).ownerOf(_tokenId) == self.collateralVaultCoreDefaultAddress, "collateral not owned by CVCore"
    else:
        assert INonERC721Vault(vault).collateralOwner(_tokenId) == self.collateralVaultCoreDefaultAddress, "collateral not owned by CVCore"

    IVault(vault).transferCollateral(_wallet, _collateralAddress, _tokenId)

    log CollateralFromLiquidationTransferred(
        _collateralAddress,
        _wallet,
        _collateralAddress,
        _tokenId,
        _wallet
    )


@external
def approveBackstopBuyer(_address: address, _collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.liquidationsPeripheralAddress, "msg.sender is not authorised"
    assert _address != empty(address), "address is the zero addr"
    assert _collateralAddress != empty(address), "collat addr is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"

    vault : address = self._getVaultAddress(_collateralAddress)
    if vault == self.collateralVaultCoreDefaultAddress:
        assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
        assert IERC721(_collateralAddress).ownerOf(_tokenId) == self.collateralVaultCoreDefaultAddress, "collateral not owned by CVCore"
    else:
        assert INonERC721Vault(vault).collateralOwner(_tokenId) == self.collateralVaultCoreDefaultAddress, "collateral not owned by CVCore"

    IVault(vault).approveOperator(_address, _collateralAddress, _tokenId)

    log OperatorApproved(
        _collateralAddress,
        _address,
        _collateralAddress,
        _tokenId,
        _address
    )
