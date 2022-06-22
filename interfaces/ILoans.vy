# Structs

struct Collateral:
    contractAddress: address
    tokenId: uint256

struct Loan:
    id: uint256
    amount: uint256
    interest: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    maturity: uint256
    startTime: uint256
    collaterals: DynArray[Collateral, 100]
    paidAmount: uint256
    started: bool
    invalidated: bool
    paid: bool
    defaulted: bool
    canceled: bool

# Events

event OwnershipTransferred:
    ownerIndexed: address
    proposedOwnerIndexed: address
    owner: address
    proposedOwner: address
    erc20TokenContract: address
event LoanCreated:
    walletIndexed: address
    wallet: address
    loanId: uint256
    erc20TokenContract: address
event LoanValidated:
    walletIndexed: address
    wallet: address
    loanId: uint256
    erc20TokenContract: address
event LoanInvalidated:
    walletIndexed: address
    wallet: address
    loanId: uint256
    erc20TokenContract: address
event LoanPayment:
    walletIndexed: address
    wallet: address
    loanId: uint256
    amount: uint256
    erc20TokenContract: address
event LoanPaid:
    walletIndexed: address
    wallet: address
    loanId: uint256
    erc20TokenContract: address
event LoanDefaulted:
    walletIndexed: address
    wallet: address
    loanId: uint256
    amount: uint256
    erc20TokenContract: address
event PendingLoanCanceled:
    walletIndexed: address
    wallet: address
    loanId: uint256
    erc20TokenContract: address

# Functions

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass

@external
def changeMaxAllowedLoans(_value: uint256):
    pass

@external
def changeMaxAllowedLoanDuration(_value: uint256):
    pass

@external
def changeMinLoanAmount(_value: uint256):
    pass

@external
def changeMaxLoanAmount(_value: uint256):
    pass

@external
def addCollateralToWhitelist(_address: address):
    pass

@external
def removeCollateralFromWhitelist(_address: address):
    pass

@external
def setLendingPoolPeripheralAddress(_address: address):
    pass

@external
def changeContractStatus(_flag: bool):
    pass

@external
def deprecate():
    pass

@view
@external
def erc20TokenSymbol() -> String[100]:
    pass

@view
@external
def getPendingLoan(_borrower: address, _loanId: uint256) -> Loan:
    pass

@view
@external
def getLoan(_borrower: address, _loanId: uint256) -> Loan:
    pass

@external
def reserve(_amount: uint256, _interest: uint256, _maturity: uint256, _collaterals: DynArray[Collateral, 100]) -> uint256:
    pass

@external
def validate(_borrower: address, _loanId: uint256):
    pass

@external
def invalidate(_borrower: address, _loanId: uint256):
    pass

@external
def pay(_loanId: uint256, _amount: uint256):
    pass

@external
def settleDefault(_borrower: address, _loanId: uint256):
    pass

@external
def cancelPendingLoan(_loanId: uint256):
    pass

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
def maxAllowedLoans() -> uint256:
    pass

@view
@external
def maxAllowedLoanDuration() -> uint256:
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
def ongoingLoans(arg0: address) -> uint256:
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
def whitelistedCollaterals(arg0: address) -> bool:
    pass

@view
@external
def loansCoreAddress() -> address:
    pass

@view
@external
def lendingPoolAddress() -> address:
    pass

@view
@external
def lendingPoolCoreAddress() -> address:
    pass


