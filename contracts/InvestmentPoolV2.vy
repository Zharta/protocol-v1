# @version ^0.3.0


import interfaces.IInvestmentPoolV2 as InvPoolInterface

interface ERC20Token:
  def allowance(_owner: address, _spender: address) -> uint256: view
  def transfer(_recipient: address, _amount: uint256) -> bool: nonpayable
  def transferFrom(_sender: address, _recipient: address, _amount:uint256): nonpayable


implements: InvPoolInterface


struct InvestorFunds:
  totalAmountInvested: uint256
  rewards: uint256
  currentAmountInvested: uint256
  totalAmountWithdrawn: uint256

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

owner: public(address)
loansContract: public(address)
erc20TokenContract: public(address)

funds: HashMap[address, InvestorFunds]
fundsAvailable: public(uint256)
fundsInvested: public(uint256)
totalRewards: public(uint256)


@external
def __init__(_loansContract: address, _erc20TokenContract: address):
  self.owner = msg.sender
  self.loansContract = _loansContract
  self.erc20TokenContract = _erc20TokenContract


@view
@internal
def _fundsAreAllowed(_owner: address, _spender: address, _amount: uint256) -> bool:
  amountAllowed: uint256 = ERC20Token(self.erc20TokenContract).allowance(_owner, _spender)
  return _amount <= amountAllowed


@view
@external
def fundsFromAddress(_walletAddress: address) -> InvestorFunds:
  assert msg.sender == _walletAddress, "The sender address is not the same as the passed _walletAddress"

  return self.funds[_walletAddress]


# _amount should be passed in wei
@payable
@external
def invest(_amount: uint256) -> InvestorFunds:
  assert _amount > 0, "Amount invested has to be higher than 0"
  assert self._fundsAreAllowed(msg.sender, self, _amount), "Insufficient funds allowed to be transfered"

  ERC20Token(self.erc20TokenContract).transferFrom(msg.sender, self, _amount)

  if self.funds[msg.sender].totalAmountInvested > 0:
    self.funds[msg.sender].totalAmountInvested += _amount
    self.funds[msg.sender].currentAmountInvested += _amount
  else:
    self.funds[msg.sender] = InvestorFunds({totalAmountInvested: _amount, rewards: 0, currentAmountInvested: _amount, totalAmountWithdrawn: 0})

  self.fundsAvailable += _amount

  log Investment(msg.sender, _amount, self.erc20TokenContract)

  return self.funds[msg.sender]


# _amount should be passed in wei
@external
def withdrawFunds(_amount: uint256) -> InvestorFunds:
  assert self.funds[msg.sender].currentAmountInvested > 0, "The sender has no funds invested!"
  assert self.funds[msg.sender].currentAmountInvested >= _amount, "The sender has less funds invested than the amount requested!"
  assert self.fundsAvailable >= _amount, "Not enough funds in the pool to be withdrawn!"

  ERC20Token(self.erc20TokenContract).transfer(msg.sender, _amount)
  
  self.funds[msg.sender].currentAmountInvested -= _amount
  self.funds[msg.sender].totalAmountWithdrawn += _amount
  
  self.fundsAvailable -= _amount

  log Withdrawal(msg.sender, _amount, self.erc20TokenContract)

  return self.funds[msg.sender]


@external
def sendFunds(_to: address, _amount: uint256) -> uint256:
  assert msg.sender == self.loansContract, "The sender's address is not the loans contract address!"
  assert _amount > 0, "The amount to send should be higher than 0!"
  assert _amount <= self.fundsAvailable, "No sufficient invested funds to perform the transaction!"

  ERC20Token(self.erc20TokenContract).transfer(_to, _amount)

  self.fundsAvailable -= _amount
  self.fundsInvested += _amount

  log FundsTransfer(_to, _amount, self.erc20TokenContract)

  return self.fundsAvailable


@payable
@external
def receiveFunds(_owner: address, _amount: uint256, _interestAmount: uint256) -> uint256:
  assert msg.sender == self.loansContract, "The sender's address is not the loans contract address!"
  assert self._fundsAreAllowed(_owner, self, _amount + _interestAmount), "Insufficient funds allowed to be transfered"
  assert _amount + _interestAmount > 0, "The sent value should be higher than 0!"
  assert _amount <= self.fundsInvested, "There are more funds being sent than expected by the invested funds variable!"

  ERC20Token(self.erc20TokenContract).transferFrom(_owner, self, _amount + _interestAmount)

  self.fundsAvailable += _amount + _interestAmount
  self.fundsInvested -= _amount
  self.totalRewards += _interestAmount

  log FundsReceipt(msg.sender, _amount, _interestAmount, self.erc20TokenContract)

  return self.fundsAvailable


@external
@payable
def __default__():
  raise "No function called!"
