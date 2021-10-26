# @version ^0.2.0


# InvestmentPool external interface
interface InvestmentPool:
  def sendFunds(_to: address, _amount: uint256) -> uint256: nonpayable
  def receivePayback(_amount: uint256, _interestAmount: uint256) -> uint256: payable

interface CollateralContract:
  def supportsInterface(_interfaceID: bytes32) -> bool: view
  def getApproved(tokenId: uint256) -> address: view
  def isApprovedForAll(owner: address, operator: address) -> bool: view
  def safeTransferFrom(_from: address, _to: address, tokenId: uint256): nonpayable
  def transferFrom(_from: address, _to: address, tokenId: uint256): nonpayable


struct Collaterals:
  size: uint256
  contracts: address[10]
  ids: uint256[10]


struct Loan:
  amount: uint256
  interest: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
  paidAmount: uint256
  paidAmountInterest: uint256
  maturity: uint256
  collaterals: Collaterals
  approved: bool
  issued: bool
  defaulted: bool
  paid: bool

event LoanStarted:
  borrower: address

event LoanPaid:
  borrower: address

event LoanCanceled:
  borrower: address  

owner: public(address)

invPool: public(InvestmentPool)
invPoolAddress: public(address)

whitelistedCollaterals: HashMap[address, address]

loans: HashMap[address, Loan] # Only one loan per address/user

currentApprovedLoans: public(uint256)
totalApprovedLoans: public(uint256)

currentIssuedLoans: public(uint256)
totalIssuedLoans: public(uint256)

totalPaidLoans: public(uint256)

totalDefaultedLoans: public(uint256)


@external
def __init__():
  self.owner = msg.sender


@external
def setInvestmentPoolAddress(_address: address) -> address:
  assert msg.sender == self.owner, "Only the contract owner can set the investment pool address!"

  self.invPool = InvestmentPool(_address)
  self.invPoolAddress = _address
  return self.invPoolAddress


@view
@internal
def _hasApprovedLoan(_address: address) -> bool:
  return self.loans[_address].approved == True


@view
@internal
def _hasStartedLoan(_address: address) -> bool:
  return self.loans[_address].issued == True


@internal
def _areCollateralsWhitelisted(_addresses: address[10]) -> bool:
  for _address in _addresses:
    if _address != empty(address):
      if self.whitelistedCollaterals[_address] == empty(address):
        return False
    else:
      break
  return True


@view
@internal
def _isCollateralApproved(_borrower: address, _operator: address, _contractAddress: address) -> bool:
  return CollateralContract(_contractAddress).isApprovedForAll(_borrower, _operator)


@view
@internal
def _areCollateralsApproved(_borrower: address) -> bool:
  for k in range(10):
    if self.loans[_borrower].collaterals.contracts[k] != empty(address):
      if not self._isCollateralApproved(_borrower, self, self.loans[_borrower].collaterals.contracts[k]):
        return False
    else:
      break

  return True


@view
@external
def isCollateralWhitelisted(_address: address) -> bool:
  return self.whitelistedCollaterals[_address] != empty(address)


@external
def addCollateralToWhitelist(_address: address) -> bool:
  assert msg.sender == self.owner, "Only the contract owner can add collateral addresses to the whitelist!"
  assert _address.is_contract == True, "The _address sent does not have a contract deployed!"

  self.whitelistedCollaterals[_address] = _address

  return True


@external
def removeCollateralFromWhitelist(_address: address) -> bool:
  assert msg.sender == self.owner, "Only the contract owner can add collateral addresses to the whitelist!"

  self.whitelistedCollaterals[_address] = empty(address)

  return True


@view
@external
def loanDetails() -> Loan:
  assert self._hasApprovedLoan(msg.sender), "The sender does not have an approved loan!"
  
  return self.loans[msg.sender]


@external
def newLoan(
  _borrower: address,
  _amount: uint256,
  _interest: uint256,
  _maturity: uint256,
  _collateralsAddresses: address[10],
  _collateralsIds: uint256[10]

) -> Loan:
  assert msg.sender == self.owner, "Only the contract owner can create loans!"
  assert self._hasApprovedLoan(_borrower) == False, "The sender already has an approved loan!"
  assert self._areCollateralsWhitelisted(_collateralsAddresses), "The collaterals are not all whitelisted!"
  assert block.timestamp <= _maturity, "Maturity can not be in the past!"

  loan: Loan = Loan(
    {
      amount: _amount,
      interest: _interest,
      paidAmount: 0,
      paidAmountInterest: 0,
      maturity: _maturity,
      collaterals: empty(Collaterals),
      approved: True,
      issued: False,
      defaulted: False,
      paid: False
    }
  )
  
  for k in range(10):
    if _collateralsAddresses[k] != empty(address):
      loan.collaterals.size += 1
      loan.collaterals.contracts[k] = _collateralsAddresses[k]
      loan.collaterals.ids[k] = _collateralsIds[k]
    else:
      break

  self.loans[_borrower] = loan
  self.currentApprovedLoans += 1
  self.totalApprovedLoans += 1

  return self.loans[_borrower]


@external
def startApprovedLoan() -> Loan:
  assert self._hasApprovedLoan(msg.sender) == True, "The sender does not have an approved loan!"
  assert self._areCollateralsApproved(msg.sender) == True, "The collaterals are not all approved to be transferred!"

  self.loans[msg.sender].issued = True
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
    if self.loans[msg.sender].collaterals.contracts[k] != empty(address):
      CollateralContract(self.loans[msg.sender].collaterals.contracts[k]).transferFrom(
        msg.sender,
        self,
        self.loans[msg.sender].collaterals.ids[k]
      )
    else:
      break
  
  self.invPool.sendFunds(msg.sender, self.loans[msg.sender].amount)

  log LoanStarted(msg.sender)

  return self.loans[msg.sender]


@payable
@external
def payLoan() -> Loan:
  assert self._hasStartedLoan(msg.sender), "The sender does not have an issued loan!"
  assert block.timestamp <= self.loans[msg.sender].maturity, "The maturity of the loan has already been reached. The loan is defaulted!"
  assert msg.value > 0, "The value sent needs to be higher than 0!"

  maxPayment: uint256 = self.loans[msg.sender].amount * (10000 + self.loans[msg.sender].interest) / 10000
  allowedPayment: uint256 = maxPayment - self.loans[msg.sender].paidAmount - self.loans[msg.sender].paidAmountInterest
  assert msg.value <= allowedPayment, "The value sent is higher than the amount left to be paid!"

  paidAmount: uint256 = msg.value * 10000 / (10000 + self.loans[msg.sender].interest)
  paidAmountInterest: uint256 = msg.value - paidAmount

  if msg.value == allowedPayment:
    for k in range(10):
      if self.loans[msg.sender].collaterals.contracts[k] != empty(address):
        CollateralContract(self.loans[msg.sender].collaterals.contracts[k]).safeTransferFrom(
          self,
          msg.sender,
          self.loans[msg.sender].collaterals.ids[k]
        )
      else:
        break

    self.loans[msg.sender] = empty(Loan)
    self.currentApprovedLoans -= 1
    self.currentIssuedLoans -= 1
    self.totalPaidLoans += 1
  else:
    self.loans[msg.sender].paidAmount += paidAmount
    self.loans[msg.sender].paidAmountInterest += paidAmountInterest

  raw_call(self.invPoolAddress, _abi_encode(paidAmount, paidAmountInterest, method_id=method_id("receiveFunds(uint256,uint256)")), value=msg.value)

  log LoanPaid(msg.sender)

  return self.loans[msg.sender]


@external
def cancelApprovedLoan() -> Loan:
  assert self._hasApprovedLoan(msg.sender), "The sender does not have an approved loan!"
  assert self._hasStartedLoan(msg.sender) == False, "The loan has already been started, please pay the loan."

  self.loans[msg.sender] = empty(Loan)

  self.currentApprovedLoans -= 1

  log LoanCanceled(msg.sender)

  return self.loans[msg.sender]


@external
def settleDefaultedLoan(_borrower: address) -> Loan:
  assert msg.sender == self.owner, "Only the contract owner can default loans!"
  assert self._hasStartedLoan(_borrower), "The sender does not have an issued loan!"
  assert block.timestamp > self.loans[_borrower].maturity, "The maturity of the loan has not been reached yet!"

  for k in range(10):
    if self.loans[_borrower].collaterals.contracts[k] != empty(address):
      CollateralContract(self.loans[_borrower].collaterals.contracts[k]).safeTransferFrom(
        self,
        self.owner,
        self.loans[_borrower].collaterals.ids[k]
      )
    else:
      break

  self.loans[_borrower] = empty(Loan)

  self.currentApprovedLoans -= 1
  self.currentIssuedLoans -= 1
  self.totalDefaultedLoans += 1

  return self.loans[_borrower]



@external
@payable
def __default__():
  raise "No function called!"

