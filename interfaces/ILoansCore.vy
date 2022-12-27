# Structs

struct Collateral:
    contractAddress: address
    tokenId: uint256
    amount: uint256

struct Loan:
    id: uint256
    amount: uint256
    interest: uint256
    maturity: uint256
    startTime: uint256
    collaterals: DynArray[Collateral, 100]
    paidPrincipal: uint256
    paidInterestAmount: uint256
    started: bool
    invalidated: bool
    paid: bool
    defaulted: bool
    canceled: bool

struct TopStats:
    highestSingleCollateralLoan: Loan
    highestCollateralBundleLoan: Loan
    highestRepayment: Loan
    highestDefaultedLoan: Loan

# Events

event OwnerProposed:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event OwnershipTransferred:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event LoansPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

# Functions

@view
@external
def owner() -> address:
    pass

@view
@external
def proposedOwner() -> address:
    pass

@view
@external
def loansPeripheral() -> address:
    pass

@view
@external
def borrowedAmount(arg0: address) -> uint256:
    pass

@view
@external
def ongoingLoans(arg0: address) -> uint256:
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
def collectionsBorrowedAmount(arg0: address) -> uint256:
    pass

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass

@external
def setLoansPeripheral(_address: address):
    pass

@view
@external
def isLoanCreated(_borrower: address, _loanId: uint256) -> bool:
    pass

@view
@external
def isLoanStarted(_borrower: address, _loanId: uint256) -> bool:
    pass

@view
@external
def getLoanAmount(_borrower: address, _loanId: uint256) -> uint256:
    pass

@view
@external
def getLoanMaturity(_borrower: address, _loanId: uint256) -> uint256:
    pass

@view
@external
def getLoanInterest(_borrower: address, _loanId: uint256) -> uint256:
    pass

@view
@external
def getLoanCollaterals(_borrower: address, _loanId: uint256) -> DynArray[Collateral, 100]:
    pass

@view
@external
def getLoanStartTime(_borrower: address, _loanId: uint256) -> uint256:
    pass

@view
@external
def getLoanPaidPrincipal(_borrower: address, _loanId: uint256) -> uint256:
    pass

@view
@external
def getLoanPaidInterestAmount(_borrower: address, _loanId: uint256) -> uint256:
    pass

@view
@external
def getLoanStarted(_borrower: address, _loanId: uint256) -> bool:
    pass

@view
@external
def getLoanInvalidated(_borrower: address, _loanId: uint256) -> bool:
    pass

@view
@external
def getLoanPaid(_borrower: address, _loanId: uint256) -> bool:
    pass

@view
@external
def getLoanDefaulted(_borrower: address, _loanId: uint256) -> bool:
    pass

@view
@external
def getLoanCanceled(_borrower: address, _loanId: uint256) -> bool:
    pass

@view
@external
def getPendingLoan(_borrower: address, _loanId: uint256) -> Loan:
    pass

@view
@external
def getLoan(_borrower: address, _loanId: uint256) -> Loan:
    pass

@view
@external
def getHighestSingleCollateralLoan() -> Loan:
    pass

@view
@external
def getHighestCollateralBundleLoan() -> Loan:
    pass

@view
@external
def getHighestRepayment() -> Loan:
    pass

@view
@external
def getHighestDefaultedLoan() -> Loan:
    pass

@view
@external
def collateralKeysArray() -> DynArray[bytes32, 1048576]:
    pass

@view
@external
def getCollateralsIdsByAddress(_address: address) -> DynArray[uint256, 1048576]:
    pass

@external
def addCollateralToLoan(_borrower: address, _collateral: Collateral, _loanId: uint256):
    pass

@external
def removeCollateralFromLoan(_borrower: address, _collateral: Collateral, _loanId: uint256):
    pass

@external
def updateCollaterals(_collateral: Collateral, _toRemove: bool):
    pass

@external
def addLoan(_borrower: address, _amount: uint256, _interest: uint256, _maturity: uint256, _collaterals: DynArray[Collateral, 100]) -> uint256:
    pass

@external
def updateLoanStarted(_borrower: address, _loanId: uint256):
    pass

@external
def updateLoanPaidAmount(_borrower: address, _loanId: uint256, _paidPrincipal: uint256, _paidInterestAmount: uint256):
    pass

@external
def updatePaidLoan(_borrower: address, _loanId: uint256):
    pass

@external
def updateDefaultedLoan(_borrower: address, _loanId: uint256):
    pass

@external
def updateHighestSingleCollateralLoan(_borrower: address, _loanId: uint256):
    pass

@external
def updateHighestCollateralBundleLoan(_borrower: address, _loanId: uint256):
    pass

@external
def updateHighestRepayment(_borrower: address, _loanId: uint256):
    pass

@external
def updateHighestDefaultedLoan(_borrower: address, _loanId: uint256):
    pass