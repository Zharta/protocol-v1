# @version ^0.3.0

# Interfaces

interface InvestmentPool:
  def sendFunds(_to: address, _amount: uint256) -> uint256: nonpayable
  def receivePayback(_amount: uint256, _interestAmount: uint256) -> uint256: payable


interface CollateralContract:
  def supportsInterface(_interfaceID: bytes32) -> bool: view
  def getApproved(tokenId: uint256) -> address: view
  def isApprovedForAll(owner: address, operator: address) -> bool: view
  def safeTransferFrom(_from: address, _to: address, tokenId: uint256): nonpayable
  def transferFrom(_from: address, _to: address, tokenId: uint256): nonpayable


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
  collaterals: Collaterals
  paidAmount: uint256
  approved: bool
  issued: bool


# Global variables

owner: public(address)
maxAllowedLoans: public(uint256)

loans: public(HashMap[address, Loan[10]])
nextLoanId: public(HashMap[address, uint256])

collateralsUsedByAddress: public(HashMap[address, Collateral[100]])
collateralsSizeUsedByAddress: public(HashMap[address, uint256])

whitelistedCollaterals: public(HashMap[address, address])

invPool: InvestmentPool
invPoolAddress: public(address)

currentApprovedLoans: public(uint256)
totalApprovedLoans: public(uint256)

currentIssuedLoans: public(uint256)
totalIssuedLoans: public(uint256)

totalPaidLoans: public(uint256)

totalDefaultedLoans: public(uint256)


@external
def __init__(_maxAllowedLoans: uint256):
  self.owner = msg.sender
  self.maxAllowedLoans = _maxAllowedLoans


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
    if borrower_collaterals[i].contract == empty(address):
      break

    if borrower_collaterals[i].contract in _collateralsAddresses:
      for k in range(10):
        if _collateralsAddresses[k] == empty(address):
          break
        elif _collateralsAddresses[k] == borrower_collaterals[i].contract:
          if _collateralsIds[k] == borrower_collaterals[i].id:
            return False

  return True


@internal
def _hasApprovedLoan(_borrower: address, _loanId: uint256) -> bool:
  if self.loans[_borrower][_loanId].approved:
    return True
  return False


@internal
def _hasStartedLoan(_borrower: address, _loanId: uint256) -> bool:
  if self.loans[_borrower][_loanId].issued:
    return True
  return False


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
def setInvestmentPoolAddress(_address: address) -> address:
  assert msg.sender == self.owner, "Only the contract owner can set the investment pool address"

  self.invPool = InvestmentPool(_address)
  self.invPoolAddress = _address
  return self.invPoolAddress


@external
def newLoan(
  _borrower: address,
  _amount: uint256,
  _interest: uint256,
  _maturity: uint256,
  _collateralsAddresses: address[10],
  _collateralsIds: uint256[10]
) -> Loan:
  assert msg.sender == self.owner, "Only the contract owner can create loans"
  assert block.timestamp <= _maturity, "Maturity can not be in the past"
  assert self.nextLoanId[_borrower] < self.maxAllowedLoans - 1, "Max number of loans already reached"
  assert self._areCollateralsWhitelisted(_collateralsAddresses), "The collaterals are not all whitelisted"
  # TODO: CHECK IF COLLATERALS ARE OWNED BY THE _BORROWER
  assert self._areCollateralsNotUsed(_borrower, _collateralsAddresses, _collateralsIds), "One of the submitted collaterals is already being used"

  newLoan: Loan = Loan(
    {
      id: self.nextLoanId[_borrower],
      amount: _amount,
      interest: _interest,
      maturity: _maturity,
      paidAmount: 0,
      collaterals: empty(Collaterals),
      approved: True,
      issued: False
    }
  )

  for k in range(10):
    if _collateralsAddresses[k] != empty(address):
      newLoan.collaterals.size += 1
      newLoan.collaterals.contracts[k] = _collateralsAddresses[k]
      newLoan.collaterals.ids[k] = _collateralsIds[k]

      nextIndex: uint256 = self.collateralsSizeUsedByAddress[_borrower]
      newCollateral: Collateral = Collateral(
        {
          contract: _collateralsAddresses[k],
          id: _collateralsIds[k]
        }
      )
      self.collateralsUsedByAddress[_borrower][nextIndex] = newCollateral
      self.collateralsSizeUsedByAddress[_borrower] += 1
    else:
      break

  self.loans[_borrower][self.nextLoanId[_borrower]] = newLoan
  self.nextLoanId[_borrower] += 1

  self.currentApprovedLoans += 1
  self.totalApprovedLoans += 1

  return newLoan


@external
def startApprovedLoan(_loanId: uint256) -> Loan:
  assert self._hasApprovedLoan(msg.sender, _loanId) == True, "The sender does not have an approved loan"
  assert not self._hasStartedLoan(msg.sender, _loanId) == True, "The sender already started the loan"
  assert self._areCollateralsApproved(msg.sender, _loanId) == True, "The collaterals are not all approved to be transferred"

  self.loans[msg.sender][_loanId].issued = True
  self.currentIssuedLoans += 1
  self.totalIssuedLoans += 1

  # TODO
  # Use safeTransferFrom instead of the less secure transferFrom
  # CollateralContract(self.loans[msg.sender].collateral.contract).safeTransferFrom(
  #   msg.sender,
  #   self,
  #   self.loans[msg.sender].collateral.id
  # )
  for k in range(10):
    if self.loans[msg.sender][_loanId].collaterals.contracts[k] != empty(address):
      CollateralContract(self.loans[msg.sender][_loanId].collaterals.contracts[k]).transferFrom(
        msg.sender,
        self,
        self.loans[msg.sender][_loanId].collaterals.ids[k]
      )
    else:
      break
  
  self.invPool.sendFunds(msg.sender, self.loans[msg.sender][_loanId].amount)

  log LoanStarted(msg.sender, _loanId)

  return self.loans[msg.sender][_loanId]


@payable
@external
def payLoan(_loanId: uint256) -> Loan:
  assert self._hasStartedLoan(msg.sender, _loanId), "The sender does not have an issued loan"
  assert block.timestamp <= self.loans[msg.sender][_loanId].maturity, "The maturity of the loan has already been reached. The loan is defaulted"
  assert msg.value > 0, "The value sent needs to be higher than 0"

  maxPayment: uint256 = self.loans[msg.sender][_loanId].amount * (10000 + self.loans[msg.sender][_loanId].interest) / 10000
  allowedPayment: uint256 = maxPayment - self.loans[msg.sender][_loanId].paidAmount
  assert msg.value <= allowedPayment, "The value sent is higher than the amount left to be paid"

  paidAmount: uint256 = msg.value * 10000 / (10000 + self.loans[msg.sender][_loanId].interest)
  paidAmountInterest: uint256 = msg.value - paidAmount

  if msg.value == allowedPayment:
    for k in range(10):
      if self.loans[msg.sender][_loanId].collaterals.contracts[k] != empty(address):
        CollateralContract(self.loans[msg.sender][_loanId].collaterals.contracts[k]).safeTransferFrom(
          self,
          msg.sender,
          self.loans[msg.sender][_loanId].collaterals.ids[k]
        )
      else:
        break

    self.loans[msg.sender][_loanId] = empty(Loan)
    self.currentApprovedLoans -= 1
    self.currentIssuedLoans -= 1
    self.totalPaidLoans += 1
  else:
    self.loans[msg.sender][_loanId].paidAmount += paidAmount + paidAmountInterest

  raw_call(self.invPoolAddress, _abi_encode(paidAmount, paidAmountInterest, method_id=method_id("receiveFunds(uint256,uint256)")), value=msg.value)

  log LoanPaid(msg.sender, _loanId, msg.value)

  return self.loans[msg.sender][_loanId]


@external
def settleDefaultedLoan(_borrower: address, _loanId: uint256) -> Loan:
  assert msg.sender == self.owner, "Only the contract owner can default loans"
  assert self._hasStartedLoan(_borrower, _loanId), "The sender does not have an issued loan"
  assert block.timestamp > self.loans[_borrower][_loanId].maturity, "The maturity of the loan has not been reached yet"

  for k in range(10):
    if self.loans[_borrower][_loanId].collaterals.contracts[k] != empty(address):
      CollateralContract(self.loans[_borrower][_loanId].collaterals.contracts[k]).safeTransferFrom(
        self,
        self.owner,
        self.loans[_borrower][_loanId].collaterals.ids[k]
      )
    else:
      break

  self.loans[_borrower][_loanId] = empty(Loan)

  self.currentApprovedLoans -= 1
  self.currentIssuedLoans -= 1
  self.totalDefaultedLoans += 1

  return self.loans[_borrower][_loanId]


@external
def cancelApprovedLoan(_loanId: uint256) -> Loan:
  assert self._hasApprovedLoan(msg.sender, _loanId), "The sender does not have an approved loan"
  assert not self._hasStartedLoan(msg.sender, _loanId), "The loan has already been started, please pay the loan"

  self.loans[msg.sender][_loanId] = empty(Loan)

  self.currentApprovedLoans -= 1

  log LoanCanceled(msg.sender, _loanId)

  return self.loans[msg.sender][_loanId]


@external
@payable
def __default__():
  raise "No function called!"
