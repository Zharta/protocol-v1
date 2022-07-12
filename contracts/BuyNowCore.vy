# @version ^0.3.3


# Interfaces

from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721

interface ILoansCore:
    def getLoanDefaulted(_borrower: address, _loanId: uint256) -> bool: view


# Structs

struct Liquidation:
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    buyNowPeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    borrower: address
    erc20TokenContract: address
    inAuction: bool


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

event CollateralVaultAddressSet:
    currentValue: address
    newValue: address

event BuyNowPeripheralAddressSet:
    currentValue: address
    newValue: address

event LoansCoreAddressAdded:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LoansCoreAddressRemoved:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    erc20TokenContract: address

event LiquidationAdded:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address

event LiquidationRemoved:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address


# Global variables

owner: public(address)
proposedOwner: public(address)

collateralVaultAddress: public(address)
buyNowPeripheralAddress: public(address)
loansCoreAddresses: public(HashMap[address, address]) # mapping between ERC20 contract and LoansCore

liquidations: HashMap[bytes32, Liquidation]


##### INTERNAL METHODS #####

@view
@internal
def _computeLiquidationKey(_collateralAddress: address, _collateralId: uint256) -> bytes32:
  return keccak256(_abi_encode(_collateralAddress, convert(_collateralId, bytes32)))


##### EXTERNAL METHODS - VIEW #####

@view
@external
def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)]


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
def setCollateralVaultAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert self.collateralVaultAddress != _address, "new value is the same"

    log CollateralVaultAddressSet(
        self.collateralVaultAddress,
        _address
    )

    self.collateralVaultAddress = _address


@external
def setBuyNowPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert self.buyNowPeripheralAddress != _address, "new value is the same"

    log BuyNowPeripheralAddressSet(
        self.buyNowPeripheralAddress,
        _address
    )

    self.buyNowPeripheralAddress = _address


@external
def addLoansCoreAddress(_erc20TokenContract: address, _address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.loansCoreAddresses[_erc20TokenContract] != _address, "new value is the same"

    log LoansCoreAddressAdded(
        _erc20TokenContract,
        self.loansCoreAddresses[_erc20TokenContract],
        _address,
        _erc20TokenContract
    )

    self.loansCoreAddresses[_erc20TokenContract] = _address


@external
def removeLoansCoreAddress(_erc20TokenContract: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.loansCoreAddresses[_erc20TokenContract] != ZERO_ADDRESS, "address not found"

    log LoansCoreAddressRemoved(
        _erc20TokenContract,
        self.loansCoreAddresses[_erc20TokenContract],
        _erc20TokenContract
    )
    
    self.loansCoreAddresses[_erc20TokenContract] = ZERO_ADDRESS


@external
def addLiquidation(
    _collateralAddress: address,
    _tokenId: uint256,
    _startTime: uint256,
    _gracePeriodMaturity: uint256,
    _buyNowPeriodMaturity: uint256,
    _principal: uint256,
    _interestAmount: uint256,
    _apr: uint256,
    _borrower: address,
    _erc20TokenContract: address
):
    assert msg.sender == self.buyNowPeripheralAddress, "msg.sender is not BNPeriph addr"
    
    liquidationKey: bytes32 = self._computeLiquidationKey(_collateralAddress, _tokenId)
    assert self.liquidations[liquidationKey].startTime == 0, "liquidation already exists"

    assert _collateralAddress != ZERO_ADDRESS, "collat addr is the zero address"
    assert _collateralAddress.is_contract, "collat addr is not a contract"
    assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == self.collateralVaultAddress, "collateral not owned by vault"

    assert _startTime > 0, "startTime is 0"
    assert _gracePeriodMaturity > 0, "gpmaturity is 0"
    assert _buyNowPeriodMaturity > 0, "bnpmaturity is 0"
    assert _principal > 0, "principal is 0"
    assert _interestAmount > 0, "interestAmount is 0"
    assert _apr > 0, "apr is 0"
    assert _borrower != ZERO_ADDRESS, "borrower is the zero addr"
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"

    self.liquidations[liquidationKey] = Liquidation(
        {
            collateralAddress: _collateralAddress,
            tokenId: _tokenId,
            startTime: _startTime,
            gracePeriodMaturity: _gracePeriodMaturity,
            buyNowPeriodMaturity: _buyNowPeriodMaturity,
            principal: _principal,
            interestAmount: _interestAmount,
            apr: _apr,
            borrower: _borrower,
            erc20TokenContract: _erc20TokenContract,
            inAuction: False,
        }
    )

    log LiquidationAdded(
        _erc20TokenContract,
        _collateralAddress,
        _collateralAddress,
        _tokenId,
        _erc20TokenContract
    )


@external
def removeLiquidation(_collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.buyNowPeripheralAddress, "msg.sender is not BNPeriph addr"

    assert self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].startTime > 0, "liquidation not found"

    liquidationKey: bytes32 = self._computeLiquidationKey(_collateralAddress, _tokenId)
    log LiquidationRemoved(
        self.liquidations[liquidationKey].erc20TokenContract,
        self.liquidations[liquidationKey].collateralAddress,
        self.liquidations[liquidationKey].collateralAddress,
        self.liquidations[liquidationKey].tokenId,
        self.liquidations[liquidationKey].erc20TokenContract
    )

    self.liquidations[liquidationKey] = empty(Liquidation)




