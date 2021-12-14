# @version ^0.3.0


import interfaces.IInvestmentPool as InvPoolInterface

implements: InvPoolInterface


struct InvestorFunds:
  totalAmountInvested: uint256
  rewards: uint256
  currentAmountInvested: uint256
  totalAmountWithdrawn: uint256

event Investment:
  _from: address
  amount: uint256

event Withdrawal:
  _from: address
  amount: uint256

event FundsTransfer:
  _to: address
  amount: uint256

event FundsReceipt:
  _from: address
  amount: uint256
  interestAmount: uint256

owner: public(address)
loansContract: public(address)

funds: HashMap[address, InvestorFunds]
fundsAvailable: public(uint256)
fundsInvested: public(uint256)
totalRewards: public(uint256)


@external
def __init__(_loansContract: address):
  self.owner = msg.sender
  self.loansContract = _loansContract


@view
@external
def fundsFromAddress(_walletAddress: address) -> InvestorFunds:
  assert msg.sender == _walletAddress, "The sender's address is not the same as the passed _walletAddress!"

  return self.funds[_walletAddress]


@payable
@external
def invest() -> InvestorFunds:
  assert msg.value > 0, "Amount invested has to be higher than 0!"

  if self.funds[msg.sender].totalAmountInvested > 0:
    self.funds[msg.sender].totalAmountInvested += msg.value
    self.funds[msg.sender].currentAmountInvested += msg.value
  else:
    self.funds[msg.sender] = InvestorFunds({totalAmountInvested: msg.value, rewards: 0, currentAmountInvested: msg.value, totalAmountWithdrawn: 0})

  self.fundsAvailable += msg.value

  log Investment(msg.sender, msg.value)

  return self.funds[msg.sender]


# _amount should be passed in wei
@external
def withdrawFunds(_amount: uint256) -> InvestorFunds:
  assert self.funds[msg.sender].currentAmountInvested > 0, "The sender has no funds invested!"
  assert self.funds[msg.sender].currentAmountInvested >= _amount, "The sender has less funds invested than the amount requested!"
  assert self.fundsAvailable >= _amount, "Not enough funds in the pool to be withdrawn!"

  send(msg.sender, _amount)
  
  self.funds[msg.sender].currentAmountInvested -= _amount
  self.funds[msg.sender].totalAmountWithdrawn += _amount
  
  self.fundsAvailable -= _amount

  log Withdrawal(msg.sender, _amount)

  return self.funds[msg.sender]


@external
def sendFunds(_to: address, _amount: uint256) -> uint256:
  assert msg.sender == self.loansContract, "The sender's address is not the loans contract address!"
  assert _amount > 0, "The amount to send should be higher than 0!"
  assert _amount <= self.fundsAvailable, "No sufficient invested funds to perform the transaction!"

  send(_to, _amount)

  self.fundsAvailable -= _amount
  self.fundsInvested += _amount

  log FundsTransfer(_to, _amount)

  return self.fundsAvailable


@payable
@external
def receiveFunds(_amount: uint256, _interestAmount: uint256) -> uint256:
  assert msg.sender == self.loansContract, "The sender's address is not the loans contract address!"
  assert msg.value == _amount + _interestAmount, "The sent value is different than the sum of _amount and _interestAmount!"
  assert msg.value > 0, "The sent value should be higher than 0!"
  assert _amount <= self.fundsInvested, "There are more funds being sent than expected by the invested funds variable!"

  self.fundsAvailable += msg.value
  self.fundsInvested -= _amount
  self.totalRewards += _interestAmount

  log FundsReceipt(msg.sender, _amount, _interestAmount)

  return self.fundsAvailable


@external
@payable
def __default__():
  raise "No function called!"
