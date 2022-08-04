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

# Functions

@view
@external
def withinPoolShareLimit(_lender: address, _amount: uint256, _lpContractAddress: address) -> bool:
    pass

@view
@external
def withinLoansPoolShareLimit(_borrower: address, _amount: uint256, _loansCoreContractAddress: address, _lpContractAddress: address) -> bool:
    pass

@view
@external
def outOfLockPeriod(_lender: address, _lpContractAddress: address) -> bool:
    pass

@external
def changeMaxPoolShareConditions(_flag: bool, _value: uint256):
    pass

@external
def changeMaxLoansPoolShareConditions(_flag: bool, _value: uint256):
    pass

@external
def changeMaxCollateralsShareConditions(_flag: bool, _value: uint256):
    pass

@external
def changeLockPeriodConditions(_flag: bool, _value: uint256):
    pass

@view
@external
def owner() -> address:
    pass

@view
@external
def maxPoolShare() -> uint256:
    pass

@view
@external
def maxLoansPoolShare() -> uint256:
    pass

@view
@external
def maxCollateralsShare() -> uint256:
    pass

@view
@external
def lockPeriodDuration() -> uint256:
    pass

@view
@external
def maxPoolShareEnabled() -> bool:
    pass

@view
@external
def lockPeriodEnabled() -> bool:
    pass

@view
@external
def maxLoansPoolShareEnabled() -> bool:
    pass

@view
@external
def maxCollateralsShareEnabled() -> bool:
    pass


