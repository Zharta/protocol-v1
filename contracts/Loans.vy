# @version ^0.3.0

# Interfaces

interface LendingPool:
  def sendFunds(_to: address, _amount: uint256) -> uint256: nonpayable
  def receiveFunds(_owner: address, _amount: uint256, _rewardsAmount: uint256) -> uint256: nonpayable
  def fundsAvailable() -> uint256: nonpayable
  def erc20TokenContract() -> address: nonpayable


interface CollateralContract:
  def supportsInterface(_interfaceID: bytes32) -> bool: view
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
  indexes: uint256[10]
  contracts: address[10]
  ids: uint256[10]

struct Loan:
  id: uint256
  amount: uint256
  interest: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
  maturity: uint256
  collaterals: Collaterals
  paidAmount: uint256
  # approved: bool
  # issued: bool


# Global variables

owner: public(address)
maxAllowedLoans: public(uint256)
bufferToCancelLoan: public(uint256)

loans: public(HashMap[address, Loan[10]])
loanIds: public(HashMap[address, bool[10]])
nextLoanId: public(HashMap[address, uint256])

collateralsUsedByAddress: public(HashMap[address, Collateral[100]])
collateralsSizeUsedByAddress: public(HashMap[address, uint256])

whitelistedCollaterals: public(HashMap[address, address])

lendingPool: LendingPool
lendingPoolAddress: public(address)

# currentApprovedLoans: public(uint256)
# totalApprovedLoans: public(uint256)

currentIssuedLoans: public(uint256)
totalIssuedLoans: public(uint256)

totalPaidLoans: public(uint256)

totalDefaultedLoans: public(uint256)


@external
def __init__(_maxAllowedLoans: uint256, _bufferToCancelLoan: uint256):
  self.owner = msg.sender
  self.maxAllowedLoans = _maxAllowedLoans
  self.bufferToCancelLoan = _bufferToCancelLoan


@internal
def _areCollateralsWhitelisted(_addresses: address[10]) -> bool:
  for _address in _addresses:
    if _address != empty(address):
      if self.whitelistedCollaterals[_address] == empty(address):
        return False
    else:
      break
  return True


@internal
def _areCollateralsNotUsed(
  _borrower: address,
  _collateralsAddresses: address[10],
  _collateralsIds: uint256[10]
) -> bool:
  borrower_collaterals: Collateral[100] = self.collateralsUsedByAddress[_borrower]

  for i in range(100):
    if borrower_collaterals[i].contract in _collateralsAddresses:
      for k in range(10):
        if _collateralsAddresses[k] == empty(address):
          break
        elif _collateralsAddresses[k] == borrower_collaterals[i].contract:
          if _collateralsIds[k] == borrower_collaterals[i].id:
            return False

  return True


@view
@internal
def _checkNextLoanId(_borrower: address) -> uint256:
  for index in range(10):
    if not self.loanIds[_borrower][index]:
      return index
  return self.maxAllowedLoans


@internal
def _hasStartedLoan(_borrower: address, _loanId: uint256) -> bool:
  return self.loans[_borrower][_loanId] != empty(Loan)


@internal
def _checkHasBufferPassed(_blockTimestamp: address, _loanMaturity: uint256) -> bool:
  return _blockTimestamp - _loanMaturity < self.bufferToCancelLoan


@view
@internal
def _isCollateralApproved(_borrower: address, _operator: address, _contractAddress: address) -> bool:
  return CollateralContract(_contractAddress).isApprovedForAll(_borrower, _operator)


@view
@internal
def _areCollateralsApproved(_borrower: address, _loanId: uint256) -> bool:
  for k in range(10):
    if self.loans[_borrower][_loanId].collaterals.contracts[k] != empty(address):
      if not self._isCollateralApproved(_borrower, self, self.loans[_borrower][_loanId].collaterals.contracts[k]):
        return False
    else:
      break

  return True


@view
@internal
def _numberOfCollaterals(_collateralsAddresses: address[10]) -> uint256:
  nCollaterals: uint256 = 0
  for k in range(10):
    if _collateralsAddresses[k] == empty(address):
      break
    nCollaterals += 1

  return nCollaterals


@view
@internal
def _checkNextCollateralIndexes(_borrower: address, _nIndexes: uint256) -> uint256[10]:
  collaterals: Collateral[100] = self.collateralsUsedByAddress[_borrower]
  curIndex: uint256 = 0
  indexes: uint256[10] = empty(uint256[10])
  for index in range(100):
    if collaterals[index] == empty(Collateral):
      indexes[curIndex] = index
      curIndex += 1

      if curIndex == _nIndexes:
        break

  return indexes


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
def setLendingPoolAddress(_address: address) -> address:
  assert msg.sender == self.owner, "Only the contract owner can set the investment pool address"

  self.lendingPool = LendingPool(_address)
  self.lendingPoolAddress = _address
  return self.lendingPoolAddress


@view
@external
def loanIdsFromAddress(_borrower: address) -> bool[10]:
  return self.loanIds[_borrower]


@external
def start(_loanId: uint256) -> Loan:
  assert block.timestamp <= _maturity, "Maturity can not be in the past"
  assert self.nextLoanId[_borrower] < self.maxAllowedLoans, "Max number of loans already reached"
  assert self._areCollateralsWhitelisted(_collateralsAddresses), "The collaterals are not all whitelisted"
  # TODO: CHECK IF COLLATERALS ARE OWNED BY THE _BORROWER
  assert self._areCollateralsNotUsed(_borrower, _collateralsAddresses, _collateralsIds), "One of the submitted collaterals is already being used"
  assert self._areCollateralsApproved(msg.sender, _loanId) == True, "The collaterals are not all approved to be transferred"
  assert self.lendingPool.fundsAvailable() >= self.loans[msg.sender][_loanId].amount, "Insufficient funds in the lending pool"

  newLoan: Loan = Loan(
    {
      id: self.nextLoanId[_borrower],
      amount: _amount,
      interest: _interest,
      maturity: _maturity,
      paidAmount: 0,
      collaterals: empty(Collaterals),
    }
  )

  nCollaterals: uint256 = self._numberOfCollaterals(_collateralsAddresses)
  indxs: uint256[10] = self._checkNextCollateralIndexes(_borrower, nCollaterals)

  for k in range(10):
    if _collateralsAddresses[k] == empty(address):
      break

    newLoan.collaterals.size += 1
    newLoan.collaterals.contracts[k] = _collateralsAddresses[k]
    newLoan.collaterals.ids[k] = _collateralsIds[k]
    newLoan.collaterals.indexes[k] = indxs[k]

    newCollateral: Collateral = Collateral(
      {
        contract: _collateralsAddresses[k],
        id: _collateralsIds[k]
      }
    )

    self.collateralsUsedByAddress[_borrower][indxs[k]] = newCollateral
    self.collateralsSizeUsedByAddress[_borrower] += 1

    CollateralContract(self.loans[msg.sender][_loanId].collaterals.contracts[k]).transferFrom(
      msg.sender,
      self,
      self.loans[msg.sender][_loanId].collaterals.ids[k]
    )

  self.loans[_borrower][self.nextLoanId[_borrower]] = newLoan
  self.loanIds[_borrower][self.nextLoanId[_borrower]] = True
  self.nextLoanId[_borrower] = self._checkNextLoanId(_borrower)

  self.currentIssuedLoans += 1
  self.totalIssuedLoans += 1
  
  self.lendingPool.sendFunds(msg.sender, self.loans[msg.sender][_loanId].amount)

  log LoanStarted(msg.sender, _loanId)

  return self.loans[msg.sender][_loanId]


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
      if self.loans[msg.sender][_loanId].collaterals.contracts[k] != empty(address):
        CollateralContract(self.loans[msg.sender][_loanId].collaterals.contracts[k]).safeTransferFrom(
          self,
          msg.sender,
          self.loans[msg.sender][_loanId].collaterals.ids[k]
        )

        self.collateralsSizeUsedByAddress[msg.sender] -= 1
        self.collateralsUsedByAddress[msg.sender][self.loans[msg.sender][_loanId].collaterals.indexes[k]] = empty(Collateral)
        # TODO: manage the collateralsSizeUsedByAddress and collateralsUsedByAddress to free space
      else:
        break

    self.loans[msg.sender][_loanId] = empty(Loan)
    self.nextLoanId[msg.sender] = _loanId
    self.loanIds[msg.sender][_loanId] = False
    self.currentIssuedLoans -= 1
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
    if self.loans[_borrower][_loanId].collaterals.contracts[k] != empty(address):
      CollateralContract(self.loans[_borrower][_loanId].collaterals.contracts[k]).safeTransferFrom(
        self,
        self.owner,
        self.loans[_borrower][_loanId].collaterals.ids[k]
      )

      self.collateralsSizeUsedByAddress[_borrower] -= 1
      self.collateralsUsedByAddress[_borrower][self.loans[msg.sender][_loanId].collaterals.indexes[k]] = empty(Collateral)
    else:
      break

  self.loans[_borrower][_loanId] = empty(Loan)
  self.nextLoanId[_borrower] = _loanId
  self.loanIds[_borrower][_loanId] = False

  self.currentIssuedLoans -= 1
  self.totalDefaultedLoans += 1

  return self.loans[_borrower][_loanId]


@external
def cancel(_loanId: uint256) -> Loan:
  assert not self._hasStartedLoan(msg.sender, _loanId), "The sender has not started a loan with the given ID"
  assert self._checkHasBufferPassed(block.timestamp, self.loans[_borrower][_loanId].maturity), "The time buffer to cancel the loan has passed"

  for k in range(10):
    if self.loans[msg.sender][_loanId].collaterals.contracts[k] != empty(address):
      CollateralContract(self.loans[_borrower][_loanId].collaterals.contracts[k]).safeTransferFrom(
        self,
        msg.sender,
        self.loans[_borrower][_loanId].collaterals.ids[k]
      )

      self.collateralsSizeUsedByAddress[msg.sender] -= 1
      self.collateralsUsedByAddress[msg.sender][self.loans[msg.sender][_loanId].collaterals.indexes[k]] = empty(Collateral)

  self.loans[msg.sender][_loanId] = empty(Loan)
  self.nextLoanId[msg.sender] = _loanId
  self.loanIds[msg.sender][_loanId] = False

  log LoanCanceled(msg.sender, _loanId)

  return self.loans[msg.sender][_loanId]


@external
@payable
def __default__():
  raise "No function called!"
