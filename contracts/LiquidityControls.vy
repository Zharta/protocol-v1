# @version ^0.3.3


# Interfaces

interface ILendingPoolCore:
    def fundsInPool() -> uint256: view
    def currentAmountDeposited(_lender: address) -> uint256: view
    def lockPeriodEnd(_lender: address) -> uint256: view

interface ILoansCore:
    def borrowedAmount(_borrower: address) -> uint256: view


# Structs


# Events

event MaxPoolShareFlagChanged:
    value: bool

event MaxPoolShareChanged:
    value: uint256

event MaxLoansPoolShareFlagChanged:
    value: bool

event MaxLoansPoolShareChanged:
    value: uint256

event MaxCollateralsShareFlagChanged:
    value: bool

event MaxCollateralsShareChanged:
    value: uint256

event LockPeriodFlagChanged:
    value: bool

event LockPeriodDurationChanged:
    value: uint256


# Global variables

owner: public(address)

maxPoolShare: public(uint256)
maxLoansPoolShare: public(uint256)
maxCollateralsShare: public(uint256)
lockPeriodDuration: public(uint256)

maxPoolShareEnabled: public(bool)
lockPeriodEnabled: public(bool)
maxLoansPoolShareEnabled: public(bool)
maxCollateralsShareEnabled: public(bool)


##### INTERNAL METHODS - VIEW #####


##### INTERNAL METHODS - WRITE #####


##### EXTERNAL METHODS - VIEW #####

@view
@external
def withinPoolShareLimit(_lender: address, _amount: uint256, _lpCoreContractAddress: address) -> bool:
    if not self.maxPoolShareEnabled:
        return True

    fundsInPool: uint256 = ILendingPoolCore(_lpCoreContractAddress).fundsInPool()

    lenderDepositedAmount: uint256 = ILendingPoolCore(_lpCoreContractAddress).currentAmountDeposited(_lender)

    return (lenderDepositedAmount + _amount) * 10000 / (fundsInPool + _amount) <= self.maxPoolShare


@view
@external
def withinLoansPoolShareLimit(_borrower: address, _amount: uint256, _loansCoreContractAddress: address, _lpCoreContractAddress: address) -> bool:
    if not self.maxPoolShareEnabled:
        return True

    borrowedAmount: uint256 = ILoansCore(_loansCoreContractAddress).borrowedAmount(_borrower)
    fundsInPool: uint256 = ILendingPoolCore(_lpCoreContractAddress).fundsInPool()

    return (borrowedAmount + _amount) * 10000 / fundsInPool <= self.maxLoansPoolShare


@view
@external
def outOfLockPeriod(_lender: address, _lpCoreContractAddress: address) -> bool:
    if not self.lockPeriodEnabled:
        return True
    
    return ILendingPoolCore(_lpCoreContractAddress).lockPeriodEnd(_lender) <= block.timestamp


##### EXTERNAL METHODS - NON-VIEW #####

@external
def __init__(
    _maxPoolShareEnabled: bool,
    _maxPoolShare: uint256,
    _lockPeriodEnabled: bool,
    _lockPeriodDuration: uint256,
    _maxLoansPoolShareEnabled: bool,
    _maxLoansPoolShare: uint256,
    _maxCollateralsShareEnabled: bool,
    _maxCollateralsShare: uint256
):
    assert _maxPoolShare <= 10000, "max pool share > 10000 bps"
    assert _maxLoansPoolShare <= 10000, "max loans pool share > 10000 bps"
    assert _maxCollateralsShare <= 10000, "max collats share > 10000 bps"
    
    self.owner = msg.sender

    if _maxPoolShareEnabled:
        self.maxPoolShareEnabled = _maxPoolShareEnabled
        self.maxPoolShare = _maxPoolShare

    if _lockPeriodEnabled:
        self.lockPeriodEnabled = _lockPeriodEnabled
    self.lockPeriodDuration = _lockPeriodDuration

    if _maxLoansPoolShareEnabled:
        self.maxLoansPoolShareEnabled = _maxLoansPoolShareEnabled
        self.maxLoansPoolShare = _maxLoansPoolShare

    if _maxCollateralsShareEnabled:
        self.maxCollateralsShareEnabled = _maxCollateralsShareEnabled
        self.maxCollateralsShare = _maxCollateralsShare


@external
def changeMaxPoolShareConditions(_flag: bool, _value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.maxPoolShareEnabled != _flag, "new value is the same"
    
    if _flag:
        assert _value <= 10000, "max pool share exceeds 10000 bps"
        self.maxPoolShare = _value

        log MaxPoolShareChanged(_value)

    self.maxPoolShareEnabled = _flag

    log MaxPoolShareFlagChanged(_flag)


@external
def changeMaxLoansPoolShareConditions(_flag: bool, _value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.maxLoansPoolShareEnabled != _flag, "new value is the same"
    
    if _flag:
        assert _value <= 10000, "max pool share exceeds 10000 bps"
        self.maxLoansPoolShare = _value

        log MaxLoansPoolShareChanged(_value)

    self.maxLoansPoolShareEnabled = _flag

    log MaxLoansPoolShareFlagChanged(_flag)


@external
def changeMaxCollateralsShareConditions(_flag: bool, _value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.maxCollateralsShareEnabled != _flag, "new value is the same"
    
    if _flag:
        assert _value <= 10000, "max pool share exceeds 10000 bps"
        self.maxCollateralsShare = _value

        log MaxLoansPoolShareChanged(_value)

    self.maxCollateralsShareEnabled = _flag

    log MaxLoansPoolShareFlagChanged(_flag)


@external
def changeLockPeriodConditions(_flag: bool, _value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.lockPeriodEnabled != _flag, "new value is the same"
    
    if _flag:
        if self.lockPeriodDuration != _value:
            self.lockPeriodDuration = _value

            log LockPeriodDurationChanged(_value)
        else:
            raise "new value is the same"

    self.lockPeriodEnabled = _flag

    log LockPeriodFlagChanged(_flag)


