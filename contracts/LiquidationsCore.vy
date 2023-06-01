# @version 0.3.9


# Interfaces

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
    lenderPeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    gracePeriodPrice: uint256
    lenderPeriodPrice: uint256
    borrower: address
    loanId: uint256
    loansCoreContract: address
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


# Global variables

owner: public(address)
proposedOwner: public(address)

liquidationsPeripheralAddress: public(address)

liquidations: HashMap[bytes32, Liquidation]
liquidatedLoans: HashMap[bytes32, bool]


##### INTERNAL METHODS #####

@pure
@internal
def _computeLiquidationId(_collateralAddress: address, _collateralId: uint256, _timestamp: uint256) -> bytes32:
    return keccak256(_abi_encode(_collateralAddress, convert(_collateralId, bytes32), convert(_timestamp, bytes32)))


@pure
@internal
def _computeLiquidationKey(_collateralAddress: address, _collateralId: uint256) -> bytes32:
    return keccak256(_abi_encode(_collateralAddress, convert(_collateralId, bytes32)))


@pure
@internal
def _computeLiquidatedLoansKey(_borrower: address, _loansCoreContract: address, _loanId: uint256) -> bytes32:
    return keccak256(_abi_encode(_borrower, _loansCoreContract, convert(_loanId, bytes32)))


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
def getLiquidationLenderPeriodMaturity(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].lenderPeriodMaturity

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


@view
@external
def isLoanLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256) -> bool:
    return self.liquidatedLoans[self._computeLiquidatedLoansKey(_borrower, _loansCoreContract, _loanId)]


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
def addLiquidation(
    _collateralAddress: address,
    _tokenId: uint256,
    _startTime: uint256,
    _gracePeriodMaturity: uint256,
    _lenderPeriodMaturity: uint256,
    _principal: uint256,
    _interestAmount: uint256,
    _apr: uint256,
    _gracePeriodPrice: uint256,
    _lenderPeriodPrice: uint256,
    _borrower: address,
    _loanId: uint256,
    _loansCoreContract: address,
    _erc20TokenContract: address
) -> bytes32:
    assert msg.sender == self.liquidationsPeripheralAddress, "msg.sender is not LiqPeriph addr"
    
    liquidationKey: bytes32 = self._computeLiquidationKey(_collateralAddress, _tokenId)
    assert self.liquidations[liquidationKey].startTime == 0, "liquidation already exists"
    assert not self.liquidatedLoans[self._computeLiquidatedLoansKey(_borrower, _loansCoreContract, _loanId)], "loan already liquidated"

    lid: bytes32 = self._computeLiquidationId(_collateralAddress, _tokenId, block.timestamp)
    self.liquidations[liquidationKey] = Liquidation(
        {
            lid: lid,
            collateralAddress: _collateralAddress,
            tokenId: _tokenId,
            startTime: _startTime,
            gracePeriodMaturity: _gracePeriodMaturity,
            lenderPeriodMaturity: _lenderPeriodMaturity,
            principal: _principal,
            interestAmount: _interestAmount,
            apr: _apr,
            gracePeriodPrice: _gracePeriodPrice,
            lenderPeriodPrice: _lenderPeriodPrice,
            borrower: _borrower,
            loanId: _loanId,
            loansCoreContract: _loansCoreContract,
            erc20TokenContract: _erc20TokenContract,
            inAuction: False,
        }
    )

    return lid


@external
def addLoanToLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256):
    assert msg.sender == self.liquidationsPeripheralAddress, "msg.sender is not LiqPeriph addr"
    
    self.liquidatedLoans[self._computeLiquidatedLoansKey(_borrower, _loansCoreContract, _loanId)] = True


@external
def removeLiquidation(_collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.liquidationsPeripheralAddress, "msg.sender is not LiqPeriph addr"

    liquidationKey: bytes32 = self._computeLiquidationKey(_collateralAddress, _tokenId)
    
    assert self.liquidations[liquidationKey].startTime > 0, "liquidation not found"

    self.liquidations[liquidationKey] = empty(Liquidation)


