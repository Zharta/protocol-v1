# Events

event MaxPoolShareFlagChanged:
    value: bool
event MaxPoolShareChanged:
    value: uint256
event MaxLoansPoolShareFlagChanged:
    value: bool
event MaxLoansPoolShareChanged:
    value: uint256
event MaxCollectionShareFlagChanged:
    value: bool
event MaxCollectionShareChanged:
    value: uint256
event LockPeriodFlagChanged:
    value: bool
event LockPeriodDurationChanged:
    value: uint256

# Functions

@view
@external
def withinPoolShareLimit(_lender: address, _amount: uint256, _lpPeripheralContractAddress: address, _lpCoreContractAddress: address, _fundsInvestable: uint256) -> bool:
    pass

@view
@external
def withinLoansPoolShareLimit(_borrower: address, _amount: uint256, _loansCoreContractAddress: address, _lpPeripheralContractAddress: address) -> bool:
    pass

@view
@external
def outOfLockPeriod(_lender: address, _lpCoreContractAddress: address) -> bool:
    pass

@view
@external
def withinCollectionShareLimit(_collectionAmount: uint256, _collectionAddress: address, _loansCoreContractAddress: address, _lpCoreContractAddress: address) -> bool:
    pass

@external
def changeMaxPoolShareConditions(_flag: bool, _value: uint256):
    pass

@external
def changeMaxLoansPoolShareConditions(_flag: bool, _value: uint256):
    pass

@external
def changeMaxCollectionShareConditions(_flag: bool, _value: uint256):
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
def maxCollectionShare() -> uint256:
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
def maxCollectionShareEnabled() -> bool:
    pass

