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

struct EIP712Domain:
    name: String[100]
    version: String[10]
    chain_id: uint256
    verifying_contract: address

struct ReserveMessageContent:
    amount: uint256
    interest: uint256
    maturity: uint256
    collaterals: DynArray[Collateral, 100]
    delegations: DynArray[bool, 100]
    deadline: uint256

# Events

event OwnershipTransferred:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event OwnerProposed:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event InterestAccrualPeriodChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event LendingPoolPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event CollateralVaultPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LiquidationsPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LiquidityControlsAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event ContractStatusChanged:
    erc20TokenContractIndexed: indexed(address)
    value: bool
    erc20TokenContract: address

event ContractDeprecated:
    erc20TokenContractIndexed: indexed(address)
    erc20TokenContract: address

event LoanCreated:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    erc20TokenContract: address
    apr: uint256
    amount: uint256
    duration: uint256
    collaterals: DynArray[Collateral, 100]

event LoanPayment:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    principal: uint256
    interestAmount: uint256
    erc20TokenContract: address

event LoanPaid:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanDefaulted:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    amount: uint256
    erc20TokenContract: address

event PaymentSent:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256

event PaymentReceived:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256

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

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass

@external
def changeInterestAccrualPeriod(_value: uint256):
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
def reserveWeth(_amount: uint256, _interest: uint256, _maturity: uint256, _collaterals: DynArray[Collateral, 100], _delegations: DynArray[bool, 100], _deadline: uint256, _nonce: uint256, _v: uint256, _r: uint256, _s: uint256) -> uint256:
    pass

@external
def reserveEth(_amount: uint256, _interest: uint256, _maturity: uint256, _collaterals: DynArray[Collateral, 100], _delegations: DynArray[bool, 100], _deadline: uint256, _nonce: uint256, _v: uint256, _r: uint256, _s: uint256) -> uint256:
    pass

@payable
@external
def pay(_loanId: uint256):
    pass

@external
def settleDefault(_borrower: address, _loanId: uint256):
    pass

@external
def setDelegation(_loanId: uint256, _contractAddress: address, _tokenId: uint256, _value: bool):
    pass