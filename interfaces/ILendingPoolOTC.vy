# Structs

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool

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

event ProtocolWalletChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event ProtocolFeesShareChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event LoansPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LiquidationsPeripheralAddressSet:
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

event Deposit:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256
    erc20TokenContract: address

event Withdrawal:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256
    erc20TokenContract: address

event FundsTransfer:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256
    erc20TokenContract: address

event FundsReceipt:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256
    rewardsPool: uint256
    rewardsProtocol: uint256
    investedAmount: uint256
    erc20TokenContract: address
    fundsOrigin: String[30]

event PaymentSent:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256

event PaymentReceived:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256

event CollateralClaimReceipt:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256
    erc20TokenContract: address
    fundsOrigin: String[30]

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
def loansContract() -> address:
    pass

@view
@external
def erc20TokenContract() -> address:
    pass

@view
@external
def allowEth() -> bool:
    pass

@view
@external
def liquidationsPeripheralContract() -> address:
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
def isPoolActive() -> bool:
    pass

@view
@external
def isPoolDeprecated() -> bool:
    pass

@view
@external
def funds() -> InvestorFunds:
    pass

@view
@external
def lender() -> address:
    pass

@view
@external
def fundsAvailable() -> uint256:
    pass

@view
@external
def fundsInvested() -> uint256:
    pass

@view
@external
def totalFundsInvested() -> uint256:
    pass

@view
@external
def totalRewards() -> uint256:
    pass

@view
@external
def collateralClaimsValue() -> uint256:
    pass

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

@view
@external
def lendersArray() -> DynArray[address, 1]:
    pass

@view
@external
def computeWithdrawableAmount(_lender: address) -> uint256:
    pass

@view
@external
def fundsInPool() -> uint256:
    pass

@view
@external
def currentAmountDeposited(_lender: address) -> uint256:
    pass

@view
@external
def totalAmountDeposited(_lender: address) -> uint256:
    pass

@view
@external
def totalAmountWithdrawn(_lender: address) -> uint256:
    pass

@external
def initialize(_owner: address, _lender: address, _protocolWallet: address, _protocolFeesShare: uint256):
    pass

@external
def create_proxy(_protocolWallet: address, _protocolFeesShare: uint256, _lender: address) -> address:
    pass

@external
def proposeOwner(_address: address):
    pass

@external
def claimOwnership():
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
def changePoolStatus(_flag: bool):
    pass

@external
def deprecate():
    pass

@external
def deposit(_amount: uint256):
    pass

@external
@payable
def depositEth():
    pass

@external
def withdraw(_amount: uint256):
    pass

@external
def withdrawEth(_amount: uint256):
    pass

@external
def sendFunds(_to: address, _amount: uint256):
    pass

@external
def sendFundsEth(_to: address, _amount: uint256):
    pass

@payable
@external
def receiveFundsEth(_borrower: address, _amount: uint256, _rewardsAmount: uint256):
    pass

@external
def receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256):
    pass

@external
def receiveFundsFromLiquidation(_borrower: address, _amount: uint256, _rewardsAmount: uint256, _distributeToProtocol: bool, _origin: String[30]):
    pass

@payable
@external
def receiveFundsFromLiquidationEth(_borrower: address, _amount: uint256, _rewardsAmount: uint256, _distributeToProtocol: bool, _origin: String[30]):
    pass

@external
def receiveCollateralFromLiquidation(_borrower: address, _amount: uint256, _origin: String[30]):
    pass