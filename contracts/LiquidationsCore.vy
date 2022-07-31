# @version ^0.3.4


# Interfaces

from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721

interface ILoansCore:
    def getLoanDefaulted(_borrower: address, _loanId: uint256) -> bool: view


# Structs

struct Liquidation:
    lid: bytes32
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    buyNowPeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    gracePeriodPrice: uint256
    buyNowPeriodPrice: uint256
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

event LiquidationsPeripheralAddressSet:
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


# Global variables

owner: public(address)
proposedOwner: public(address)

liquidationsPeripheralAddress: public(address)
loansCoreAddresses: public(HashMap[address, address]) # mapping between ERC20 contract and LoansCore

liquidations: HashMap[bytes32, Liquidation]


##### INTERNAL METHODS #####

@pure
@internal
def _computeLiquidationId(_collateralAddress: address, _collateralId: uint256, _timestamp: uint256) -> bytes32:
  return keccak256(_abi_encode(_collateralAddress, convert(_collateralId, bytes32), convert(_timestamp, bytes32)))


@pure
@internal
def _computeLiquidationKey(_collateralAddress: address, _collateralId: uint256) -> bytes32:
  return keccak256(_abi_encode(_collateralAddress, convert(_collateralId, bytes32)))


##### EXTERNAL METHODS - VIEW #####

@view
@external
def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)]


@view
@external
def getLiquidationStartTime(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].startTime

@view
@external
def getLiquidationGracePeriodMaturity(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].gracePeriodMaturity

@view
@external
def getLiquidationBuyNowPeriodMaturity(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].buyNowPeriodMaturity

@view
@external
def getLiquidationPrincipal(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].principal

@view
@external
def getLiquidationInterestAmount(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].interestAmount

@view
@external
def getLiquidationAPR(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].apr

@view
@external
def getLiquidationBorrower(_collateralAddress: address, _tokenId: uint256) -> address:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].borrower

@view
@external
def getLiquidationERC20Contract(_collateralAddress: address, _tokenId: uint256) -> address:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].erc20TokenContract

@view
@external
def isLiquidationInAuction(_collateralAddress: address, _tokenId: uint256) -> bool:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].inAuction


##### EXTERNAL METHODS - WRITE #####
@external
def __init__():
    self.owner = msg.sender


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
def addLoansCoreAddress(_erc20TokenContract: address, _address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
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
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.loansCoreAddresses[_erc20TokenContract] != empty(address), "address not found"

    log LoansCoreAddressRemoved(
        _erc20TokenContract,
        self.loansCoreAddresses[_erc20TokenContract],
        _erc20TokenContract
    )
    
    self.loansCoreAddresses[_erc20TokenContract] = empty(address)


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
    _gracePeriodPrice: uint256,
    _buyNowPeriodPrice: uint256,
    _borrower: address,
    _erc20TokenContract: address
) -> bytes32:
    assert msg.sender == self.liquidationsPeripheralAddress, "msg.sender is not BNPeriph addr"
    
    liquidationKey: bytes32 = self._computeLiquidationKey(_collateralAddress, _tokenId)
    assert self.liquidations[liquidationKey].startTime == 0, "liquidation already exists"

    lid: bytes32 = self._computeLiquidationId(_collateralAddress, _tokenId, block.timestamp)
    self.liquidations[liquidationKey] = Liquidation(
        {
            lid: lid,
            collateralAddress: _collateralAddress,
            tokenId: _tokenId,
            startTime: _startTime,
            gracePeriodMaturity: _gracePeriodMaturity,
            buyNowPeriodMaturity: _buyNowPeriodMaturity,
            principal: _principal,
            interestAmount: _interestAmount,
            apr: _apr,
            gracePeriodPrice: _gracePeriodPrice,
            buyNowPeriodPrice: _buyNowPeriodPrice,
            borrower: _borrower,
            erc20TokenContract: _erc20TokenContract,
            inAuction: False,
        }
    )

    return lid


@external
def removeLiquidation(_collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.liquidationsPeripheralAddress, "msg.sender is not BNPeriph addr"

    liquidationKey: bytes32 = self._computeLiquidationKey(_collateralAddress, _tokenId)
    
    assert self.liquidations[liquidationKey].startTime > 0, "liquidation not found"

    self.liquidations[liquidationKey] = empty(Liquidation)


