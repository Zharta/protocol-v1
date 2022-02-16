# @version ^0.3.1


import interfaces.ILendingPool as LendingPoolInterface

interface ERC20Token:
  def allowance(_owner: address, _spender: address) -> uint256: view
  def decimals() -> uint256: view
  def transfer(_recipient: address, _amount: uint256) -> bool: nonpayable
  def transferFrom(_sender: address, _recipient: address, _amount: uint256): nonpayable


implements: LendingPoolInterface


struct InvestorFunds:
  currentAmountDeposited: uint256
  totalAmountDeposited: uint256
  totalAmountWithdrawn: uint256
  currentPendingRewards: uint256
  totalRewardsAmount: uint256
  activeForRewards: bool

event Deposit:
  _from: address
  amount: uint256
  erc20TokenContract: address

event Withdrawal:
  _from: address
  amount: uint256
  erc20TokenContract: address

event Compound:
  _from: address
  rewards: uint256
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

funds: public(HashMap[address, InvestorFunds])
depositors: public(DynArray[address, 2**50])

fundsAvailable: public(uint256)
fundsInvested: public(uint256)
totalFundsInvested: public(uint256)

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


# _amount should be passed in wei
@payable
@external
def deposit(_amount: uint256) -> InvestorFunds:
  assert _amount > 0, "Amount deposited has to be higher than 0"
  assert self._fundsAreAllowed(msg.sender, self, _amount), "Insufficient funds allowed to be transfered"

  ERC20Token(self.erc20TokenContract).transferFrom(msg.sender, self, _amount)

  if self.funds[msg.sender].totalAmountDeposited > 0:
    self.funds[msg.sender].totalAmountDeposited += _amount
    self.funds[msg.sender].currentAmountDeposited += _amount
  else:
    self.funds[msg.sender] = InvestorFunds(
      {
        currentAmountDeposited: _amount,
        totalAmountDeposited: _amount,
        totalAmountWithdrawn: 0,
        currentPendingRewards: 0,
        totalRewardsAmount: 0,
        activeForRewards: True
      }
    )
    self.depositors.append(msg.sender)

  self.fundsAvailable += _amount

  log Deposit(msg.sender, _amount, self.erc20TokenContract)

  return self.funds[msg.sender]


# _amount should be passed in wei
@external
def withdraw(_amount: uint256) -> InvestorFunds:
  assert self.funds[msg.sender].currentAmountDeposited > 0, "The sender has no funds deposited"
  assert self.funds[msg.sender].currentAmountDeposited >= _amount, "The sender has less funds deposited than the amount requested"
  assert self.fundsAvailable >= _amount, "Not enough funds in the pool to be withdrawn"

  ERC20Token(self.erc20TokenContract).transfer(msg.sender, _amount)

  self.funds[msg.sender].currentAmountDeposited -= _amount
  self.funds[msg.sender].totalAmountWithdrawn += _amount
  
  if self.funds[msg.sender].currentAmountDeposited == 0:
    ERC20Token(self.erc20TokenContract).transfer(msg.sender, self.funds[msg.sender].currentPendingRewards)
    self.funds[msg.sender].currentPendingRewards = 0
    self.funds[msg.sender].activeForRewards = False
  
  self.fundsAvailable -= _amount

  log Withdrawal(msg.sender, _amount, self.erc20TokenContract)

  return self.funds[msg.sender]


@external
def compoundRewards() -> InvestorFunds:
  assert self.funds[msg.sender].currentAmountDeposited > 0, "The sender has no funds deposited"
  assert self.funds[msg.sender].currentPendingRewards > 0, "The sender has no pending rewards to compound"

  pendingRewards: uint256 = self.funds[msg.sender].currentPendingRewards

  self.funds[msg.sender].currentAmountDeposited += pendingRewards
  self.funds[msg.sender].totalAmountDeposited += pendingRewards
  self.funds[msg.sender].currentPendingRewards = 0

  self.fundsAvailable += pendingRewards

  log Compound(msg.sender, pendingRewards, self.erc20TokenContract)

  return self.funds[msg.sender]


@external
def sendFunds(_to: address, _amount: uint256) -> uint256:
  assert msg.sender == self.loansContract, "The sender's address is not the loans contract address"
  assert _amount > 0, "The amount to send should be higher than 0"
  assert _amount <= self.fundsAvailable, "No sufficient deposited funds to perform the transaction"

  ERC20Token(self.erc20TokenContract).transfer(_to, _amount)

  self.fundsAvailable -= _amount
  self.fundsInvested += _amount
  self.totalFundsInvested += _amount

  log FundsTransfer(_to, _amount, self.erc20TokenContract)

  return self.fundsAvailable


@external
def receiveFunds(_owner: address, _amount: uint256, _rewardsAmount: uint256) -> uint256:
  assert msg.sender == self.loansContract, "The sender's address is not the loans contract address"
  assert self._fundsAreAllowed(_owner, self, _amount + _rewardsAmount), "Insufficient funds allowed to be transfered"
  assert _amount + _rewardsAmount > 0, "The sent value should be higher than 0"
  assert _amount <= self.fundsInvested, "There are more funds being sent than expected by the deposited funds variable"

  ERC20Token(self.erc20TokenContract).transferFrom(_owner, self, _amount + _rewardsAmount)
  
  self.totalRewards += _rewardsAmount

  totalTvl: uint256 = self.fundsAvailable + self.fundsInvested
  rewardsFromUser: uint256 = 0

  for depositor in self.depositors:
    if self.funds[depositor].activeForRewards:
      rewardsFromUser = _rewardsAmount * self.funds[depositor].currentAmountDeposited / totalTvl
      self.funds[depositor].currentPendingRewards += rewardsFromUser
      self.funds[depositor].totalRewardsAmount += rewardsFromUser

  self.fundsAvailable += _amount
  self.fundsInvested -= _amount

  log FundsReceipt(msg.sender, _amount, _rewardsAmount, self.erc20TokenContract)

  return self.fundsAvailable


@external
@payable
def __default__():
  if msg.value > 0:
    send(msg.sender, msg.value)
