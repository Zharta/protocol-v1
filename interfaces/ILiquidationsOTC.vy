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

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool

struct Liquidation:
    lid: bytes32
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256
    gracePeriodPrice: uint256
    borrower: address
    loanId: uint256
    loansCoreContract: address
    erc20TokenContract: address

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

event GracePeriodDurationChanged:
    currentValue: uint256
    newValue: uint256

event LoansCoreAddressAdded:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LoansCoreAddressRemoved:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    erc20TokenContract: address

event LendingPoolPeripheralAddressAdded:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LendingPoolPeripheralAddressRemoved:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    erc20TokenContract: address

event CollateralVaultPeripheralAddressSet:
    currentValue: address
    newValue: address

event LiquidationAdded:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address
    gracePeriodPrice: uint256
    lenderPeriodPrice: uint256
    gracePeriodMaturity: uint256
    lenderPeriodMaturity: uint256
    loansCoreContract: address
    loanId: uint256
    borrower: address

event LiquidationRemoved:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address
    loansCoreContract: address
    loanId: uint256
    borrower: address

event NFTPurchased:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    buyerAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    amount: uint256
    buyerAddress: address
    erc20TokenContract: address
    loansCoreContract: address
    method: String[30]

event NFTClaimed:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    buyerAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    amount: uint256
    buyerAddress: address
    erc20TokenContract: address
    loansCoreContract: address
    method: String[30]

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
def admin() -> address:
    pass

@view
@external
def proposedOwner() -> address:
    pass

@view
@external
def gracePeriodDuration() -> uint256:
    pass

@view
@external
def loansCoreAddresses(arg0: address) -> address:
    pass

@view
@external
def lendingPoolPeripheralAddresses(arg0: address) -> address:
    pass

@view
@external
def collateralVaultPeripheralAddress() -> address:
    pass

@view
@external
def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    pass

@view
@external
def getLiquidationStartTime(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationGracePeriodMaturity(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationPrincipal(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationInterestAmount(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationAPR(_collateralAddress: address, _tokenId: uint256) -> uint256:
    pass

@view
@external
def getLiquidationBorrower(_collateralAddress: address, _tokenId: uint256) -> address:
    pass

@view
@external
def getLiquidationERC20Contract(_collateralAddress: address, _tokenId: uint256) -> address:
    pass

@view
@external
def isLoanLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256) -> bool:
    pass

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass

@external
def setGracePeriodDuration(_duration: uint256):
    pass

@external
def addLoansCoreAddress(_erc20TokenContract: address, _address: address):
    pass

@external
def removeLoansCoreAddress(_erc20TokenContract: address):
    pass

@external
def addLendingPoolPeripheralAddress(_erc20TokenContract: address, _address: address):
    pass

@external
def removeLendingPoolPeripheralAddress(_erc20TokenContract: address):
    pass

@external
def setCollateralVaultPeripheralAddress(_address: address):
    pass

@external
def addLiquidation(_borrower: address, _loanId: uint256, _erc20TokenContract: address):
    pass

@payable
@external
def payLoanLiquidationsGracePeriod(_loanId: uint256, _erc20TokenContract: address):
    pass

@external
def claim(_collateralAddress: address, _tokenId: uint256):
    pass