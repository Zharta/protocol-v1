# @version ^0.3.1


# import interfaces.ILendingPool as LendingPoolInterface

interface ERC20Token:
  def allowance(_owner: address, _spender: address) -> uint256: view
  def decimals() -> uint256: view
  def transfer(_recipient: address, _amount: uint256) -> bool: nonpayable
  def transferFrom(_sender: address, _recipient: address, _amount: uint256): nonpayable


# implements: LendingPoolInterface


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

maxCapitalEfficienty: public(uint256) # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
isPoolActive: public(bool)
isPoolDeprecated: public(bool)
isPoolInvesting: public(bool)

funds: public(HashMap[address, InvestorFunds])
depositors: public(DynArray[address, 2**50])

fundsAvailable: public(uint256)
fundsInvested: public(uint256)
totalFundsInvested: public(uint256)

totalRewards: public(uint256)

rewardsByDay: public(HashMap[uint256, uint256])
days: public(DynArray[uint256, 8])
nextDaysIndex: public(uint256)


@external
def __init__(_loansContract: address, _erc20TokenContract: address, _maxCapitalEfficienty: uint256):
  self.owner = msg.sender
  self.loansContract = _loansContract
  self.erc20TokenContract = _erc20TokenContract
  self.maxCapitalEfficienty = _maxCapitalEfficienty
  self.isPoolActive = True
  self.isPoolDeprecated = False
  self.isPoolInvesting = False


@view
@internal
def _fundsAreAllowed(_owner: address, _spender: address, _amount: uint256) -> bool:
  amountAllowed: uint256 = ERC20Token(self.erc20TokenContract).allowance(_owner, _spender)
  return _amount <= amountAllowed


@view
@internal
def _hasFundsToInvest() -> bool:
  if self.fundsAvailable + self.fundsInvested == 0:
    return False
  return self.fundsInvested * 10000 / (self.fundsAvailable + self.fundsInvested) < self.maxCapitalEfficienty


@view
@internal
def _maxFundsInvestable() -> int256:
  return convert(self.fundsAvailable, int256) - (convert(self.fundsAvailable, int256) + convert(self.fundsInvested, int256)) * (10000 - convert(self.maxCapitalEfficienty, int256)) / 10000


@internal
def _distribute_rewards(_rewards: uint256):
  totalTvl: uint256 = self.fundsAvailable + self.fundsInvested
  rewardsFromUser: uint256 = 0

  for depositor in self.depositors:
    if self.funds[depositor].activeForRewards:
      rewardsFromUser = _rewards * self.funds[depositor].currentAmountDeposited / totalTvl
      self.funds[depositor].currentPendingRewards += rewardsFromUser
      self.funds[depositor].totalRewardsAmount += rewardsFromUser


@internal
def _updateRewardsCounter(_rewards: uint256):
  initDayTimestamp: uint256 = block.timestamp - block.timestamp % 86400

  if len(self.days) == 7:
    
    if self.rewardsByDay[initDayTimestamp] == 0: # no rewards for this day => new day in the array
      
      if self.nextDaysIndex == 7:
        self.days[0] = initDayTimestamp
        self.nextDaysIndex = 1
      
      else:
        self.days[self.nextDaysIndex] = initDayTimestamp
        self.nextDaysIndex += 1
    
    self.rewardsByDay[initDayTimestamp] += _rewards
  
  else:
    self.rewardsByDay[initDayTimestamp] += _rewards
    
    if initDayTimestamp not in self.days:
      self.days.append(initDayTimestamp)
      
      if self.days[len(self.days) - 1] % 2 != 0:
        self.days[len(self.days) - 1] -= self.days[len(self.days) - 1] % 2
    
    self.nextDaysIndex += 1


@view
@internal
def _sumDailyRewards() -> uint256:
  sum: uint256 = 0
  for day in self.days:
    sum += self.rewardsByDay[day]
  return sum


@external
def changeOwnership(_newOwner: address) -> address:
  assert msg.sender == self.owner, "Only the owner can change the contract ownership"

  self.owner = _newOwner

  return self.owner


@external
def changeMaxCapitalEfficiency(_newMaxCapitalEfficiency: uint256) -> uint256:
  assert msg.sender == self.owner, "Only the owner can change the max capital efficiency"

  self.maxCapitalEfficienty = _newMaxCapitalEfficiency

  return self.maxCapitalEfficienty


@external
def changePoolActive(_flag: bool) -> bool:
  assert msg.sender == self.owner, "Only the owner can change the pool from active to inactive and vice-versa"

  self.isPoolActive = _flag

  return self.isPoolActive


@external
def deprecatePool() -> bool:
  assert msg.sender == self.owner, "Only the owner can change the pool to deprecated"
  assert not self.isPoolDeprecated, "The pool is already deprecated"

  self.isPoolDeprecated = True

  return self.isPoolDeprecated


@view
@external
def hasFundsToInvest() -> bool:
  if self.fundsAvailable + self.fundsInvested == 0:
    return False
  return self.fundsInvested * 10000 / (self.fundsAvailable + self.fundsInvested) < self.maxCapitalEfficienty


@view
@external
def maxFundsInvestable() -> int256:
  return convert(self.fundsAvailable, int256) - (convert(self.fundsAvailable, int256) + convert(self.fundsInvested, int256)) * (10000 - convert(self.maxCapitalEfficienty, int256)) / 10000


@view
@external
def currentApr() -> uint256:
  # returns in parts per 10000, e.g. 2.5% is represented by 250
  if len(self.days) == 0:
    return 0
  return self._sumDailyRewards() * 365 * 10000 / (len(self.days) * (self.fundsAvailable + self.fundsInvested)) - 10000







@view
@external
def allDays() -> DynArray[uint256, 8]:
  return self.days

@view
@external
def blockTimestamp() -> uint256:
  return block.timestamp

@view
@external
def initDay() -> uint256:
  return block.timestamp - block.timestamp % 86400

@view
@external
def sumDailyRewards() -> uint256:
  return self._sumDailyRewards()

@view
@external
def xpto() -> uint256:
  return self.days[6] % 2






@external
def deposit(_amount: uint256) -> InvestorFunds:
  # _amount should be passed in wei
  
  assert not self.isPoolDeprecated, "Pool is deprecated"
  assert self.isPoolActive, "Pool is not active"
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

  if not self.isPoolInvesting and self._hasFundsToInvest():
    self.isPoolInvesting = True

  log Deposit(msg.sender, _amount, self.erc20TokenContract)

  return self.funds[msg.sender]


@external
def withdraw(_amount: uint256) -> InvestorFunds:
  # _amount should be passed in wei

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

  if self.isPoolInvesting and not self._hasFundsToInvest():
    self.isPoolInvesting = False

  log Withdrawal(msg.sender, _amount, self.erc20TokenContract)

  return self.funds[msg.sender]


@external
def compoundRewards() -> InvestorFunds:
  assert not self.isPoolDeprecated, "Pool is deprecated"
  assert self.funds[msg.sender].currentAmountDeposited > 0, "The sender has no funds deposited"
  assert self.funds[msg.sender].currentPendingRewards > 0, "The sender has no pending rewards to compound"

  pendingRewards: uint256 = self.funds[msg.sender].currentPendingRewards

  self.funds[msg.sender].currentAmountDeposited += pendingRewards
  self.funds[msg.sender].totalAmountDeposited += pendingRewards
  self.funds[msg.sender].currentPendingRewards = 0

  self.fundsAvailable += pendingRewards

  if not self.isPoolInvesting and self._hasFundsToInvest():
    self.isPoolInvesting = True

  log Compound(msg.sender, pendingRewards, self.erc20TokenContract)

  return self.funds[msg.sender]


@external
def sendFunds(_to: address, _amount: uint256) -> uint256:
  # _amount should be passed in wei

  assert not self.isPoolDeprecated, "Pool is deprecated"
  assert msg.sender == self.loansContract, "Only the loans contract address can request to send funds"
  assert _amount > 0, "The amount to send should be higher than 0"
  assert self.isPoolActive, "The pool is not active"
  assert self.isPoolInvesting, "Max capital efficiency reached"
  assert convert(_amount, int256) <= self._maxFundsInvestable(), "No sufficient deposited funds to perform the transaction"

  ERC20Token(self.erc20TokenContract).transfer(_to, _amount)

  self.fundsAvailable -= _amount
  self.fundsInvested += _amount
  self.totalFundsInvested += _amount

  if self.isPoolInvesting and not self._hasFundsToInvest():
    self.isPoolInvesting = False

  log FundsTransfer(_to, _amount, self.erc20TokenContract)

  return self.fundsAvailable


@external
def receiveFunds(_owner: address, _amount: uint256, _rewardsAmount: uint256) -> uint256:
  # _amount and _rewardsAmount should be passed in wei

  assert msg.sender == self.loansContract, "The sender's address is not the loans contract address"
  assert self._fundsAreAllowed(_owner, self, _amount + _rewardsAmount), "Insufficient funds allowed to be transfered"
  assert _amount + _rewardsAmount > 0, "The sent value should be higher than 0"
  assert _amount <= self.fundsInvested, "There are more funds being sent than expected by the deposited funds variable"

  ERC20Token(self.erc20TokenContract).transferFrom(_owner, self, _amount + _rewardsAmount)
  
  self.totalRewards += _rewardsAmount

  self._distribute_rewards(_rewardsAmount)

  self._updateRewardsCounter(_rewardsAmount)

  self.fundsAvailable += _amount
  self.fundsInvested -= _amount

  if not self.isPoolInvesting and self._hasFundsToInvest():
    self.isPoolInvesting = True

  log FundsReceipt(msg.sender, _amount, _rewardsAmount, self.erc20TokenContract)

  return self.fundsAvailable


@external
@payable
def __default__():
  if msg.value > 0:
    send(msg.sender, msg.value)
