# Structs

struct Collateral:
    contractAddress: address
    tokenId: uint256
    amount: uint256

struct Loan:
    id: uint256
    amount: uint256
    interest: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
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

# Events

event OwnershipTransferred:
    ownerIndexed: address
    proposedOwnerIndexed: address
    owner: address
    proposedOwner: address
    erc20TokenContract: address
event OwnerProposed:
    ownerIndexed: address
    proposedOwnerIndexed: address
    owner: address
    proposedOwner: address
    erc20TokenContract: address
event MaxAllowedLoansChanged:
    erc20TokenContractIndexed: address
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address
event MaxLoansChanged:
    erc20TokenContractIndexed: address
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address
event MaxLoanDurationChanged:
    erc20TokenContractIndexed: address
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address
event MaxLoanAmountChanged:
    erc20TokenContractIndexed: address
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address
event InterestAccrualPeriodChanged:
    erc20TokenContractIndexed: address
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address
event CollateralToWhitelistAdded:
    erc20TokenContractIndexed: address
    value: address
    erc20TokenContract: address
event CollateralToWhitelistRemoved:
    erc20TokenContractIndexed: address
    value: address
    erc20TokenContract: address
event LendingPoolPeripheralAddressSet:
    erc20TokenContractIndexed: address
    currentValue: address
    newValue: address
    erc20TokenContract: address
event CollateralVaultPeripheralAddressSet:
    erc20TokenContractIndexed: address
    currentValue: address
    newValue: address
    erc20TokenContract: address
event LiquidationsPeripheralAddressSet:
    erc20TokenContractIndexed: address
    currentValue: address
    newValue: address
    erc20TokenContract: address
event LiquidityControlsAddressSet:
    erc20TokenContractIndexed: address
    currentValue: address
    newValue: address
    erc20TokenContract: address
event WalletsWhitelistStatusChanged:
    erc20TokenContractIndexed: address
    value: bool
    erc20TokenContract: address
event WhitelistedWalletAdded:
    erc20TokenContractIndexed: address
    value: address
    erc20TokenContract: address
event WhitelistedWalletRemoved:
    erc20TokenContractIndexed: address
    value: address
    erc20TokenContract: address
event ContractStatusChanged:
    erc20TokenContractIndexed: address
    value: bool
    erc20TokenContract: address
event ContractDeprecated:
    erc20TokenContractIndexed: address
    erc20TokenContract: address
event LoanCreated:
    walletIndexed: address
    wallet: address
    loanId: uint256
    erc20TokenContract: address
event LoanPayment:
    walletIndexed: address
    wallet: address
    loanId: uint256
    principal: uint256
    interestAmount: uint256
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
def changeMaxLoanAmount(_value: uint256):
    pass

@external
def changeInterestAccrualPeriod(_value: uint256):
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
def setCollateralVaultPeripheralAddress(_address: address):
    pass

@external
def setLiquidationsPeripheralAddress(_address: address):
    pass

@external
def setLiquidityControlsAddress(_address: address):
    pass

@external
def changeWalletsWhitelistStatus(_flag: bool):
    pass

@external
def addWhitelistedWallet(_address: address):
    pass

@external
def removeWhitelistedWallet(_address: address):
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
def getLoanPayableAmount(_borrower: address, _loanId: uint256, _timestamp: uint256) -> uint256:
    pass

@external
def reserve(_amount: uint256, _interest: uint256, _maturity: uint256, _collaterals: DynArray[Collateral, 100], _deadline: uint256, _v: uint256, _r: uint256, _s: uint256) -> uint256:
    pass

@external
def pay(_loanId: uint256):
    pass

@external
def settleDefault(_borrower: address, _loanId: uint256):
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
def maxLoanAmount() -> uint256:
    pass

@view
@external
def interestAccrualPeriod() -> uint256:
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
def loansCoreContract() -> address:
    pass

@view
@external
def lendingPoolPeripheralContract() -> address:
    pass

@view
@external
def collateralVaultPeripheralContract() -> address:
    pass

@view
@external
def liquidationsPeripheralContract() -> address:
    pass

@view
@external
def liquidityControlsContract() -> address:
    pass

@view
@external
def walletWhitelistEnabled() -> bool:
    pass

@view
@external
def walletsWhitelisted(arg0: address) -> bool:
    pass


