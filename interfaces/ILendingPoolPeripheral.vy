# Structs

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool

struct InvestorLock:
    lockPeriodEnd: uint256
    lockPeriodAmount: uint256

# Events

event OwnerProposed:
    ownerIndexed: address
    proposedOwnerIndexed: address
    owner: address
    proposedOwner: address
    erc20TokenContract: address
event OwnershipTransferred:
    ownerIndexed: address
    proposedOwnerIndexed: address
    owner: address
    proposedOwner: address
    erc20TokenContract: address
event MaxCapitalEfficiencyChanged:
    erc20TokenContractIndexed: address
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address
event ProtocolWalletChanged:
    erc20TokenContractIndexed: address
    currentValue: address
    newValue: address
    erc20TokenContract: address
event ProtocolFeesShareChanged:
    erc20TokenContractIndexed: address
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address
event LoansPeripheralAddressSet:
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
event WhitelistStatusChanged:
    erc20TokenContractIndexed: address
    value: bool
    erc20TokenContract: address
event WhitelistAddressAdded:
    erc20TokenContractIndexed: address
    value: address
    erc20TokenContract: address
event WhitelistAddressRemoved:
    erc20TokenContractIndexed: address
    value: address
    erc20TokenContract: address
event ContractStatusChanged:
    erc20TokenContractIndexed: address
    value: bool
    erc20TokenContract: address
event InvestingStatusChanged:
    erc20TokenContractIndexed: address
    value: bool
    erc20TokenContract: address
event ContractDeprecated:
    erc20TokenContractIndexed: address
    erc20TokenContract: address
event Deposit:
    walletIndexed: address
    wallet: address
    amount: uint256
    erc20TokenContract: address
event Withdrawal:
    walletIndexed: address
    wallet: address
    amount: uint256
    erc20TokenContract: address
event FundsTransfer:
    walletIndexed: address
    wallet: address
    amount: uint256
    erc20TokenContract: address
event FundsReceipt:
    walletIndexed: address
    wallet: address
    amount: uint256
    rewardsPool: uint256
    rewardsProtocol: uint256
    investedAmount: uint256
    erc20TokenContract: address
    fundsOrigin: String[30]
event PaymentSent:
    walletIndexed: address
    wallet: address
    amount: uint256
event PaymentReceived:
    walletIndexed: address
    wallet: address
    amount: uint256

# Functions

@view
@external
def maxFundsInvestable() -> uint256:
    pass

@view
@external
def theoreticalMaxFundsInvestable() -> uint256:
    pass

@view
@external
def theoreticalMaxFundsInvestableAfterDeposit(_amount: uint256) -> uint256:
    pass

@view
@external
def lenderFunds(_lender: address) -> InvestorFunds:
    pass

@payable
@external
def __default__():
    pass

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
    pass

@external
def changeMaxCapitalEfficiency(_value: uint256):
    pass

@external
def changeProtocolWallet(_address: address):
    pass

@external
def changeProtocolFeesShare(_value: uint256):
    pass

@external
def setLoansPeripheralAddress(_address: address):
    pass

@external
def setLiquidationsPeripheralAddress(_address: address):
    pass

@external
def setLiquidityControlsAddress(_address: address):
    pass

@external
def changeWhitelistStatus(_flag: bool):
    pass

@external
def addWhitelistedAddress(_address: address):
    pass

@external
def removeWhitelistedAddress(_address: address):
    pass

@external
def changePoolStatus(_flag: bool):
    pass

@external
def deprecate():
    pass

@external
def depositWeth(_amount: uint256):
    pass

@payable
@external
def depositEth():
    pass

@external
def withdrawWeth(_amount: uint256):
    pass

@external
def withdrawEth(_amount: uint256):
    pass

@external
def sendFundsWeth(_to: address, _amount: uint256):
    pass

@external
def sendFundsEth(_to: address, _amount: uint256):
    pass

@payable
@external
def receiveFundsEth(_borrower: address, _amount: uint256, _rewardsAmount: uint256):
    pass

@external
def receiveFundsWeth(_borrower: address, _amount: uint256, _rewardsAmount: uint256):
    pass

@external
def receiveFundsFromLiquidationWeth(_borrower: address, _amount: uint256, _rewardsAmount: uint256, _distributeToProtocol: bool, _investedAmount: uint256, _origin: String[30]):
    pass

@payable
@external
def receiveFundsFromLiquidationEth(_borrower: address, _amount: uint256, _rewardsAmount: uint256, _distributeToProtocol: bool, _investedAmount: uint256, _origin: String[30]):
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
def loansContract() -> address:
    pass

@view
@external
def lendingPoolCoreContract() -> address:
    pass

@view
@external
def lendingPoolLockContract() -> address:
    pass

@view
@external
def erc20TokenContract() -> address:
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
def protocolWallet() -> address:
    pass

@view
@external
def protocolFeesShare() -> uint256:
    pass

@view
@external
def maxCapitalEfficienty() -> uint256:
    pass

@view
@external
def isPoolActive() -> bool:
    pass

@view
@external
def isPoolDeprecated() -> bool:
    pass

@view
@external
def isPoolInvesting() -> bool:
    pass

@view
@external
def whitelistEnabled() -> bool:
    pass

@view
@external
def whitelistedAddresses(arg0: address) -> bool:
    pass


