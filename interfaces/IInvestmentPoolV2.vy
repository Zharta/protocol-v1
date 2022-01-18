# Structs

struct InvestorFunds:
  totalAmountInvested: uint256
  rewards: uint256
  currentAmountInvested: uint256
  totalAmountWithdrawn: uint256

# Events

event Investment:
    _from: address
    amount: uint256
    erc20TokenContract: address
event Withdrawal:
    _from: address
    amount: uint256
    erc20TokenContract: address
event FundsTransfer:
    _to: address
    amount: uint256
    erc20TokenContract: address
event FundsReceipt:
    _from: address
    amount: uint256
    interestAmount: uint256
    erc20TokenContract: address

# Functions

@view
@external
def fundsFromAddress(_walletAddress: address) -> InvestorFunds:
    pass

@payable
@external
def invest(_amount: uint256) -> InvestorFunds:
    pass

@external
def withdrawFunds(_amount: uint256) -> InvestorFunds:
    pass

@external
def sendFunds(_to: address, _amount: uint256) -> uint256:
    pass

@payable
@external
def receiveFunds(_owner: address, _amount: uint256, _interestAmount: uint256) -> uint256:
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
def loansContract() -> address:
    pass

@view
@external
def erc20TokenContract() -> address:
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
def totalRewards() -> uint256:
    pass