# Structs

struct Collateral:
  contract: address
  id: uint256

struct Collaterals:
  size: uint256
  contracts: address[10]
  ids: uint256[10]

struct Loan:
  id: uint256
  amount: uint256
  interest: uint256
  maturity: uint256
  startTime: uint256
  collaterals: Collaterals
  paidAmount: uint256

# Events

event LoanStarted:
    borrower: address
    loanId: uint256
event LoanPaid:
    borrower: address
    loanId: uint256
    amount: uint256
event LoanCanceled:
    borrower: address
    loanId: uint256

# Functions

@external
def changeOwnership(_newOwner: address) -> address:
    pass

@external
def addCollateralToWhitelist(_address: address) -> bool:
    pass

@external
def removeCollateralFromWhitelist(_address: address) -> bool:
    pass

@external
def changeMinLoanAmount(_newMinLoanAmount: uint256) -> uint256:
    pass

@external
def changeMaxLoanAmount(_newMaxLoanAmount: uint256) -> uint256:
    pass

@external
def setLendingPoolAddress(_address: address) -> address:
    pass

@external
def changeContractStatus(_flag: bool) -> bool:
    pass

@external
def deprecate() -> bool:
    pass

@view
@external
def loanIdsUsedByAddress(_borrower: address) -> bool[10]:
    pass

@view
@external
def collateralKeysArray() -> DynArray[bytes32, 1125899906842624]:
    pass

@external
def start(_amount: uint256, _interest: uint256, _maturity: uint256, _collateralAddresses: address[10], _collateralIds: uint256[10]) -> Loan:
    pass

@external
def pay(_loanId: uint256, _amountPaid: uint256) -> Loan:
    pass

@external
def settleDefault(_borrower: address, _loanId: uint256) -> Loan:
    pass

@external
def cancel(_loanId: uint256) -> Loan:
    pass

@payable
@external
def __default__():
    pass

@view
@external
def owner() -> address:
    pass

@view
@external
def maxAllowedLoans() -> uint256:
    pass

@view
@external
def bufferToCancelLoan() -> uint256:
    pass

@view
@external
def minLoanAmount() -> uint256:
    pass

@view
@external
def maxLoanAmount() -> uint256:
    pass

@view
@external
def isAcceptingLoans() -> bool:
    pass

@view
@external
def isDeprecated() -> bool:
    pass

@view
@external
def loans(arg0: address, arg1: uint256) -> Loan:
    pass

@view
@external
def loanIdsUsed(arg0: address, arg1: uint256) -> bool:
    pass

@view
@external
def nextLoanId(arg0: address) -> uint256:
    pass

@view
@external
def collateralsInLoans(arg0: bytes32, arg1: address) -> uint256:
    pass

@view
@external
def collateralsInLoansUsed(arg0: bytes32, arg1: address, arg2: uint256) -> bool:
    pass

@view
@external
def collateralsUsed(arg0: bytes32) -> bool:
    pass

@view
@external
def collateralsData(arg0: bytes32) -> Collateral:
    pass

@view
@external
def whitelistedCollaterals(arg0: address) -> address:
    pass

@view
@external
def lendingPoolAddress() -> address:
    pass

@view
@external
def currentStartedLoans() -> uint256:
    pass

@view
@external
def totalStartedLoans() -> uint256:
    pass

@view
@external
def totalPaidLoans() -> uint256:
    pass

@view
@external
def totalDefaultedLoans() -> uint256:
    pass

@view
@external
def totalDefaultedLoansAmount() -> uint256:
    pass

@view
@external
def totalCanceledLoans() -> uint256:
    pass
