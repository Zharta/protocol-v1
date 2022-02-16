# @version ^0.3.0

# Interfaces

interface LendingPool:
  def sendFunds(_to: address, _amount: uint256) -> uint256: nonpayable
  def receiveFunds(_owner: address, _amount: uint256, _rewardsAmount: uint256) -> uint256: nonpayable
  def fundsAvailable() -> uint256: nonpayable
  def erc20TokenContract() -> address: nonpayable


interface CollateralContract:
  def supportsInterface(_interfaceID: bytes32) -> bool: view
  def ownerOf(tokenId: uint256) -> address: view
  def getApproved(tokenId: uint256) -> address: view
  def isApprovedForAll(owner: address, operator: address) -> bool: view
  def safeTransferFrom(_from: address, _to: address, tokenId: uint256): nonpayable
  def transferFrom(_from: address, _to: address, tokenId: uint256): nonpayable


interface ERC20Token:
  def allowance(_owner: address, _spender: address) -> uint256: view
  def balanceOf(_account: address) -> uint256: view


# Events

event LoanStarted:
  borrower: address
  loanId: uint256

event LoanPaid:
  borrower: address
  loanId: uint256
  amount: uint256

event LoanCanceled:
  borrower: address
  loanId: uint256


# Structs

struct Collateral:
  contract: address
  id: uint256

struct Collaterals:
  size: uint256
  contracts: address[10]
  ids: uint256[10]

struct Loan:
  id: uint256
  amount: uint256
  interest: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
  maturity: uint256
  startTime: uint256
  collaterals: Collaterals
  paidAmount: uint256


# Global variables

owner: public(address)
maxAllowedLoans: public(uint256)
bufferToCancelLoan: public(uint256)

minLoanAmount: public(uint256)
maxLoanAmount: public(uint256)

loans: public(HashMap[address, Loan[10]])
loanIdsUsed: public(HashMap[address, bool[10]])
nextLoanId: public(HashMap[address, uint256])

# concat(token_address, token_id) -> map(borrower_address, loan_id)
collateralsInLoans: public(HashMap[Bytes[64], HashMap[address, uint256]])
collateralsInLoansUsed: public(HashMap[Bytes[64], HashMap[address, HashMap[uint256, bool]]])

whitelistedCollaterals: public(HashMap[address, address])

lendingPool: LendingPool
lendingPoolAddress: public(address)

currentStartedLoans: public(uint256)
totalStartedLoans: public(uint256)

totalPaidLoans: public(uint256)
totalDefaultedLoans: public(uint256)
totalCanceledLoans: public(uint256)


@external
def __init__(_maxAllowedLoans: uint256, _bufferToCancelLoan: uint256, _minLoanAmount: uint256, _maxLoanAmount: uint256):
  self.owner = msg.sender
  self.maxAllowedLoans = _maxAllowedLoans
  self.bufferToCancelLoan = _bufferToCancelLoan
  self.minLoanAmount = _minLoanAmount
  self.maxLoanAmount = _maxLoanAmount


@internal
def _areCollateralsWhitelisted(_collateralAddresses: address[10]) -> bool:
  for addr in _collateralAddresses:
    if addr != empty(address):
      if self.whitelistedCollaterals[addr] == empty(address):
        return False
    else:
      break
  return True


@internal
def _areCollateralsOwned(
  _borrower: address,
  _collateralAddresses: address[10],
  _collateralIds: uint256[10]
) -> bool:
  for i in range(10):
    if _collateralAddresses[i] == empty(address):
      break

    if CollateralContract(_collateralAddresses[i]).ownerOf(_collateralIds[i]) != _borrower:
      return False

  return True


@view
@internal
def _checkNextLoanId(_borrower: address) -> uint256:
  for index in range(10):
    if not self.loanIdsUsed[_borrower][index]:
      return index
  return self.maxAllowedLoans


@view
@internal
def _hasStartedLoan(_borrower: address, _loanId: uint256) -> bool:
  return self.loans[_borrower][_loanId].startTime != empty(uint256)


@view
@internal
def _checkHasBufferNotPassed(_blockTimestamp: uint256, _loanStartTime: uint256) -> bool:
  if _loanStartTime == 0:
    return False
  return _blockTimestamp - _loanStartTime < self.bufferToCancelLoan


@view
@internal
def _isCollateralApproved(_borrower: address, _operator: address, _contractAddress: address) -> bool:
  return CollateralContract(_contractAddress).isApprovedForAll(_borrower, _operator)


@view
@internal
def _areCollateralsApproved(_borrower: address, _collateralsAddresses: address[10]) -> bool:
  for k in range(10):
    if _collateralsAddresses[k] == empty(address):
      break
    
    if not self._isCollateralApproved(_borrower, self, _collateralsAddresses[k]):
      return False

  return True


@external
def addCollateralToWhitelist(_address: address) -> bool:
  assert msg.sender == self.owner, "Only the contract owner can add collateral addresses to the whitelist"
  assert _address.is_contract == True, "The _address sent does not have a contract deployed"

  self.whitelistedCollaterals[_address] = _address

  return True


@external
def removeCollateralFromWhitelist(_address: address) -> bool:
  assert msg.sender == self.owner, "Only the contract owner can add collateral addresses to the whitelist"

  self.whitelistedCollaterals[_address] = empty(address)

  return True


@external
def changeMinLoanAmount(_newMinLoanAmount: uint256) -> uint256:
  assert msg.sender == self.owner, "Only the contract owner can change this setting"
  assert _newMinLoanAmount <= self.maxLoanAmount, "The min loan amount can not be higher than the max loan amount"

  self.minLoanAmount = _newMinLoanAmount

  return self.minLoanAmount


@external
def changeMaxLoanAmount(_newMaxLoanAmount: uint256) -> uint256:
  assert msg.sender == self.owner, "Only the contract owner can change this setting"
  assert _newMaxLoanAmount >= self.minLoanAmount, "The max loan amount can not be lower than the min loan amount"

  self.maxLoanAmount = _newMaxLoanAmount

  return self.maxLoanAmount


@external
def setLendingPoolAddress(_address: address) -> address:
  assert msg.sender == self.owner, "Only the contract owner can set the investment pool address"

  self.lendingPool = LendingPool(_address)
  self.lendingPoolAddress = _address
  return self.lendingPoolAddress


@view
@external
def loanIdsUsedByAddress(_borrower: address) -> bool[10]:
  return self.loanIdsUsed[_borrower]


@external
def start(
  _amount: uint256,
  _interest: uint256,
  _maturity: uint256,
  _collateralAddresses: address[10],
  _collateralIds: uint256[10]
) -> Loan:
  assert block.timestamp <= _maturity, "Maturity can not be in the past"
  assert self.nextLoanId[msg.sender] < self.maxAllowedLoans, "Max number of loans already reached"
  assert self._areCollateralsWhitelisted(_collateralAddresses), "Not all collaterals are whitelisted"
  assert self._areCollateralsOwned(msg.sender, _collateralAddresses, _collateralIds), "Not all collaterals are owned by the sender"
  assert self._areCollateralsApproved(msg.sender, _collateralAddresses) == True, "Not all collaterals are approved to be transferred"
  assert self.lendingPool.fundsAvailable() >= _amount, "Insufficient funds in the lending pool"
  assert _amount >= self.minLoanAmount, "Loan amount is less than the min loan amount"
  assert _amount <= self.maxLoanAmount, "Loan amount is more than the max loan amount"

  newLoan: Loan = Loan(
    {
      id: self.nextLoanId[msg.sender],
      amount: _amount,
      interest: _interest,
      maturity: _maturity,
      startTime: block.timestamp,
      paidAmount: 0,
      collaterals: empty(Collaterals),
    }
  )

  for k in range(10):
    if _collateralAddresses[k] == empty(address):
      break

    newLoan.collaterals.size += 1
    newLoan.collaterals.contracts[k] = _collateralAddresses[k]
    newLoan.collaterals.ids[k] = _collateralIds[k]

    newCollateral: Collateral = Collateral(
      {
        contract: _collateralAddresses[k],
        id: _collateralIds[k]
      }
    )

    key: Bytes[64] = concat(convert(_collateralAddresses[k], bytes32), convert(_collateralIds[k], bytes32))
    self.collateralsInLoans[key][msg.sender] = newLoan.id
    self.collateralsInLoansUsed[key][msg.sender][newLoan.id] = True

    CollateralContract(_collateralAddresses[k]).transferFrom(
      msg.sender,
      self,
      _collateralIds[k]
    )

  self.loans[msg.sender][self.nextLoanId[msg.sender]] = newLoan
  self.loanIdsUsed[msg.sender][self.nextLoanId[msg.sender]] = True
  self.nextLoanId[msg.sender] = self._checkNextLoanId(msg.sender)

  self.currentStartedLoans += 1
  self.totalStartedLoans += 1
  
  self.lendingPool.sendFunds(msg.sender, _amount)

  log LoanStarted(msg.sender, newLoan.id)

  return newLoan


@external
def pay(_loanId: uint256, _amountPaid: uint256) -> Loan:
  assert self._hasStartedLoan(msg.sender, _loanId), "The sender has not started a loan with the given ID"
  assert block.timestamp <= self.loans[msg.sender][_loanId].maturity, "The maturity of the loan has already been reached and it defaulted"
  assert _amountPaid > 0, "The amount paid needs to be higher than 0"

  maxPayment: uint256 = self.loans[msg.sender][_loanId].amount * (10000 + self.loans[msg.sender][_loanId].interest) / 10000
  allowedPayment: uint256 = maxPayment - self.loans[msg.sender][_loanId].paidAmount
  borrowerBalance: uint256 = ERC20Token(self.lendingPool.erc20TokenContract()).balanceOf(msg.sender)
  lendingPoolAllowance: uint256 = ERC20Token(self.lendingPool.erc20TokenContract()).allowance(msg.sender, self.lendingPoolAddress)
  assert _amountPaid <= allowedPayment, "The amount paid is higher than the amount left to be paid"
  assert borrowerBalance >= _amountPaid, "User has insufficient balance for the payment"
  assert lendingPoolAllowance >= _amountPaid, "User did not allow funds to be transferred"

  paidAmount: uint256 = _amountPaid * 10000 / (10000 + self.loans[msg.sender][_loanId].interest)
  paidAmountInterest: uint256 = _amountPaid - paidAmount

  if _amountPaid == allowedPayment:
    for k in range(10):
      if self.loans[msg.sender][_loanId].collaterals.contracts[k] == empty(address):
        break
        
      CollateralContract(self.loans[msg.sender][_loanId].collaterals.contracts[k]).safeTransferFrom(
        self,
        msg.sender,
        self.loans[msg.sender][_loanId].collaterals.ids[k]
      )

      key: Bytes[64] = concat(
        convert(
          self.loans[msg.sender][_loanId].collaterals.contracts[k],
          bytes32
        ),
        convert(
          self.loans[msg.sender][_loanId].collaterals.ids[k],
          bytes32
        )
      )
      self.collateralsInLoansUsed[key][msg.sender][_loanId] = False


    self.loans[msg.sender][_loanId] = empty(Loan)
    self.nextLoanId[msg.sender] = _loanId
    self.loanIdsUsed[msg.sender][_loanId] = False
    self.currentStartedLoans -= 1
    self.totalPaidLoans += 1
  else:
    self.loans[msg.sender][_loanId].paidAmount += paidAmount + paidAmountInterest

  self.lendingPool.receiveFunds(msg.sender, paidAmount, paidAmountInterest)

  log LoanPaid(msg.sender, _loanId, _amountPaid)

  return self.loans[msg.sender][_loanId]


@external
def settleDefault(_borrower: address, _loanId: uint256) -> Loan:
  assert msg.sender == self.owner, "Only the contract owner can default loans"
  assert self._hasStartedLoan(_borrower, _loanId), "The _borrower has not started a loan with the given ID"
  assert block.timestamp > self.loans[_borrower][_loanId].maturity, "The maturity of the loan has not been reached yet"

  for k in range(10):
    if self.loans[_borrower][_loanId].collaterals.contracts[k] == empty(address):
      break
    
    CollateralContract(self.loans[_borrower][_loanId].collaterals.contracts[k]).safeTransferFrom(
      self,
      self.owner,
      self.loans[_borrower][_loanId].collaterals.ids[k]
    )

    key: Bytes[64] = concat(
      convert(
        self.loans[_borrower][_loanId].collaterals.contracts[k],
        bytes32
      ),
      convert(
        self.loans[_borrower][_loanId].collaterals.ids[k],
        bytes32
      )
    )
    self.collateralsInLoansUsed[key][_borrower][_loanId] = False


  self.loans[_borrower][_loanId] = empty(Loan)
  self.nextLoanId[_borrower] = _loanId
  self.loanIdsUsed[_borrower][_loanId] = False

  self.currentStartedLoans -= 1
  self.totalDefaultedLoans += 1

  return self.loans[_borrower][_loanId]


@external
def cancel(_loanId: uint256) -> Loan:
  assert self._checkHasBufferNotPassed(block.timestamp, self.loans[msg.sender][_loanId].startTime), "The sender has not started a loan with the given ID or the time buffer to cancel the loan has passed"

  for k in range(10):
    if self.loans[msg.sender][_loanId].collaterals.contracts[k] == empty(address):
      break
    
    CollateralContract(self.loans[msg.sender][_loanId].collaterals.contracts[k]).safeTransferFrom(
      self,
      msg.sender,
      self.loans[msg.sender][_loanId].collaterals.ids[k]
    )

    key: Bytes[64] = concat(
      convert(
        self.loans[msg.sender][_loanId].collaterals.contracts[k],
        bytes32
      ),
      convert(
        self.loans[msg.sender][_loanId].collaterals.ids[k],
        bytes32
      )
    )
    self.collateralsInLoansUsed[key][msg.sender][_loanId] = False

  
  self.lendingPool.receiveFunds(msg.sender, self.loans[msg.sender][_loanId].amount, 0)

  self.loans[msg.sender][_loanId] = empty(Loan)
  self.nextLoanId[msg.sender] = _loanId
  self.loanIdsUsed[msg.sender][_loanId] = False

  self.totalCanceledLoans += 1

  log LoanCanceled(msg.sender, _loanId)

  return self.loans[msg.sender][_loanId]


@external
@payable
def __default__():
  raise "No function called!"
