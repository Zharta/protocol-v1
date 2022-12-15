# @version ^0.3.6


# Interfaces

interface ILendingPoolCore:
    def currentAmountDeposited(_lender: address) -> uint256: view
    def lockPeriodEnd(_lender: address) -> uint256: view
    def fundsInvested() -> uint256: view

interface ILendingPoolPeripheral:
    def theoreticalMaxFundsInvestable() -> uint256: view
    def theoreticalMaxFundsInvestableAfterDeposit(_amount: uint256) -> uint256: view

interface ILoansCore:
    def borrowedAmount(_borrower: address) -> uint256: view
    def collectionsBorrowedAmount(_collection: address) -> uint256: view

interface ILendingPoolLock:
    def investorLocks(arg0: address) -> InvestorLock: view

# Structs

struct InvestorLock:
    lockPeriodEnd: uint256
    lockPeriodAmount: uint256

# Events

event MaxPoolShareFlagChanged:
    value: bool

event MaxPoolShareChanged:
    value: uint256

event MaxLoansPoolShareFlagChanged:
    value: bool

event MaxLoansPoolShareChanged:
    value: uint256

event MaxCollectionBorrowableAmountFlagChanged:
    value: bool

event MaxCollectionBorrowableAmountChanged:
    collection: address
    value: uint256

event LockPeriodFlagChanged:
    value: bool

event LockPeriodDurationChanged:
    value: uint256


# Global variables

owner: public(address)

maxPoolShare: public(uint256)
maxLoansPoolShare: public(uint256)
lockPeriodDuration: public(uint256)
maxCollectionBorrowableAmount: public(HashMap[address, uint256])

maxPoolShareEnabled: public(bool)
lockPeriodEnabled: public(bool)
maxLoansPoolShareEnabled: public(bool)
maxCollectionBorrowableAmountEnabled: public(bool)


##### INTERNAL METHODS - VIEW #####


##### INTERNAL METHODS - WRITE #####


##### EXTERNAL METHODS - VIEW #####

@view
@external
def withinPoolShareLimit(_lender: address, _amount: uint256, _lpPeripheralContractAddress: address, _lpCoreContractAddress: address, _fundsInvestable: uint256 = 0) -> bool:
    if not self.maxPoolShareEnabled:
        return True

    fundsInvestable: uint256 = _fundsInvestable
    if _fundsInvestable == 0:
        fundsInvestable = ILendingPoolPeripheral(_lpPeripheralContractAddress).theoreticalMaxFundsInvestableAfterDeposit(_amount)
        if fundsInvestable == 0:
            return False

    lenderDepositedAmount: uint256 = ILendingPoolCore(_lpCoreContractAddress).currentAmountDeposited(_lender)

    return (lenderDepositedAmount + _amount) * 10000 / fundsInvestable <= self.maxPoolShare


@view
@external
def withinLoansPoolShareLimit(_borrower: address, _amount: uint256, _loansCoreContractAddress: address, _lpPeripheralContractAddress: address) -> bool:
    if not self.maxLoansPoolShareEnabled:
        return True

    borrowedAmount: uint256 = ILoansCore(_loansCoreContractAddress).borrowedAmount(_borrower)
    fundsInvestable: uint256 = ILendingPoolPeripheral(_lpPeripheralContractAddress).theoreticalMaxFundsInvestable()

    return (borrowedAmount + _amount) * 10000 / fundsInvestable <= self.maxLoansPoolShare


@view
@external
def outOfLockPeriod(_lender: address, _remainingAmount: uint256, _lpLockContractAddress: address) -> bool:
    if not self.lockPeriodEnabled:
        return True
    
    investorLock : InvestorLock = ILendingPoolLock(_lpLockContractAddress).investorLocks(_lender)
    return investorLock.lockPeriodEnd <= block.timestamp or _remainingAmount >= investorLock.lockPeriodAmount


@view
@external
def withinCollectionShareLimit(_amount: uint256, _collectionAddress: address, _loansCoreContractAddress: address, _lpCoreContractAddress: address) -> bool:
    if not self.maxCollectionBorrowableAmountEnabled:
        return True
    
    if self.maxCollectionBorrowableAmount[_collectionAddress] == 0:
        return True

    collectionBorrowedAmount: uint256 = ILoansCore(_loansCoreContractAddress).collectionsBorrowedAmount(_collectionAddress)

    return collectionBorrowedAmount + _amount <= self.maxCollectionBorrowableAmount[_collectionAddress]


##### EXTERNAL METHODS - NON-VIEW #####

@external
def __init__(
    _maxPoolShareEnabled: bool,
    _maxPoolShare: uint256,
    _lockPeriodEnabled: bool,
    _lockPeriodDuration: uint256,
    _maxLoansPoolShareEnabled: bool,
    _maxLoansPoolShare: uint256,
    _maxCollectionBorrowableAmountEnabled: bool
):
    assert _maxPoolShare <= 10000, "max pool share > 10000 bps"
    assert _maxLoansPoolShare <= 10000, "max loans pool share > 10000 bps"

    self.owner = msg.sender

    self.maxPoolShareEnabled = _maxPoolShareEnabled
    self.maxPoolShare = _maxPoolShare

    self.lockPeriodEnabled = _lockPeriodEnabled
    self.lockPeriodDuration = _lockPeriodDuration

    self.maxLoansPoolShareEnabled = _maxLoansPoolShareEnabled
    self.maxLoansPoolShare = _maxLoansPoolShare

    self.maxCollectionBorrowableAmountEnabled = _maxCollectionBorrowableAmountEnabled


@external
def changeMaxPoolShareConditions(_flag: bool, _value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value <= 10000, "max pool share exceeds 10000 bps"
        
    self.maxPoolShare = _value

    log MaxPoolShareChanged(_value)

    self.maxPoolShareEnabled = _flag

    log MaxPoolShareFlagChanged(_flag)


@external
def changeMaxLoansPoolShareConditions(_flag: bool, _value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value <= 10000, "max pool share exceeds 10000 bps"
        
    self.maxLoansPoolShare = _value

    log MaxLoansPoolShareChanged(_value)

    self.maxLoansPoolShareEnabled = _flag

    log MaxLoansPoolShareFlagChanged(_flag)


@external
def changeMaxCollectionBorrowableAmount(_flag: bool, _collectionAddress: address, _value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _collectionAddress != empty(address), "collection addr is empty addr"
        
    self.maxCollectionBorrowableAmount[_collectionAddress] = _value

    log MaxCollectionBorrowableAmountChanged(_collectionAddress, _value)

    self.maxCollectionBorrowableAmountEnabled = _flag

    log MaxCollectionBorrowableAmountFlagChanged(_flag)


@external
def changeLockPeriodConditions(_flag: bool, _value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    
    self.lockPeriodDuration = _value

    log LockPeriodDurationChanged(_value)

    self.lockPeriodEnabled = _flag

    log LockPeriodFlagChanged(_flag)


