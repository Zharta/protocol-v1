# @version ^0.3.3


# Interfaces

from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721
from interfaces import ICollateralVaultCore


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

collateralVaultCoreAddress: public(address)
loansPeripheralAddresses: public(HashMap[address, address]) # mapping between ERC20 contract and LoansCore
liquidationsPeripheralAddress: public(address) # mapping between ERC20 contract and LoansCore


##### INTERNAL METHODS #####


##### EXTERNAL METHODS - VIEW #####


##### EXTERNAL METHODS - WRITE #####
@external
def __init__(_collerateralVaultCoreAddress: address):
    assert _collerateralVaultCoreAddress != ZERO_ADDRESS, "address is the zero address"
    assert _collerateralVaultCoreAddress.is_contract, "address is not a contract"

    self.owner = msg.sender
    self.collateralVaultCoreAddress = _collerateralVaultCoreAddress


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
def addLoansPeripheralAddress(_erc20TokenContract: address, _address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
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
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.loansPeripheralAddresses[_erc20TokenContract] != ZERO_ADDRESS, "address not found"

    log LoansPeripheralAddressRemoved(
        _erc20TokenContract,
        self.loansPeripheralAddresses[_erc20TokenContract],
        _erc20TokenContract
    )

    self.loansPeripheralAddresses[_erc20TokenContract] = ZERO_ADDRESS


@external
def setLiquidationsPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert self.liquidationsPeripheralAddress != _address, "new value is the same"

    log LiquidationsPeripheralAddressSet(
        self.liquidationsPeripheralAddress,
        _address
    )

    self.liquidationsPeripheralAddress = _address


@external
def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address):
    assert _wallet != ZERO_ADDRESS, "address is the zero addr"
    assert _collateralAddress != ZERO_ADDRESS, "collat addr is the zero addr"
    assert _erc20TokenContract != ZERO_ADDRESS, "address is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"
    assert _erc20TokenContract.is_contract, "address is not a contract"
    assert self.loansPeripheralAddresses[_erc20TokenContract] != ZERO_ADDRESS, "mapping not found"
    assert msg.sender == self.loansPeripheralAddresses[_erc20TokenContract], "msg.sender is not authorised"
    assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == _wallet, "collateral not owned by wallet"
    assert IERC721(_collateralAddress).getApproved(_tokenId) == self.collateralVaultCoreAddress or IERC721(_collateralAddress).isApprovedForAll(_wallet, self.collateralVaultCoreAddress), "transfer is not approved"

    ICollateralVaultCore(self.collateralVaultCoreAddress).storeCollateral(_wallet, _collateralAddress, _tokenId)

    log CollateralStored(
        _collateralAddress,
        _wallet,
        _collateralAddress,
        _tokenId,
        _wallet
    )


@external
def transferCollateralFromLoan(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address):
    assert _wallet != ZERO_ADDRESS, "address is the zero addr"
    assert _collateralAddress != ZERO_ADDRESS, "collat addr is the zero addr"
    assert _erc20TokenContract != ZERO_ADDRESS, "address is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"
    assert _erc20TokenContract.is_contract, "address is not a contract"
    assert self.loansPeripheralAddresses[_erc20TokenContract] != ZERO_ADDRESS, "mapping not found"
    assert msg.sender == self.loansPeripheralAddresses[_erc20TokenContract], "msg.sender is not authorised"
    assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == self.collateralVaultCoreAddress, "collateral not owned by CVCore"

    ICollateralVaultCore(self.collateralVaultCoreAddress).transferCollateral(_wallet, _collateralAddress, _tokenId)

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
    assert _wallet != ZERO_ADDRESS, "address is the zero addr"
    assert _collateralAddress != ZERO_ADDRESS, "collat addr is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"
    assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == self.collateralVaultCoreAddress, "collateral not owned by CVCore"

    ICollateralVaultCore(self.collateralVaultCoreAddress).transferCollateral(_wallet, _collateralAddress, _tokenId)

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
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert _collateralAddress != ZERO_ADDRESS, "collat addr is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"
    assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == self.collateralVaultCoreAddress, "collateral not owned by CVCore"

    ICollateralVaultCore(self.collateralVaultCoreAddress).approveOperator(_address, _collateralAddress, _tokenId)

    log OperatorApproved(
        _collateralAddress,
        _address,
        _collateralAddress,
        _tokenId,
        _address
    )
