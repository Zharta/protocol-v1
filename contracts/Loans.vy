# @version ^0.2.0


# InvestmentPool external interface
interface InvestmentPool:
  def sendFunds(_to: address, _amount: uint256) -> uint256: nonpayable
  def receivePayback(_amount: uint256, _interestAmount: uint256) -> uint256: payable


interface CollateralContract:
  def supportsInterface(_interfaceID: bytes32) -> bool: view
  def getApproved(tokenId: uint256) -> address: view
  def safeTransferFrom(_from: address, _to: address, tokenId: uint256): nonpayable
  def transferFrom(_from: address, _to: address, tokenId: uint256): nonpayable


struct Collateral:
  contract: address
  id: uint256


struct Loan:
  amount: uint256
  interest: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
  paidAmount: uint256
  paidAmountInterest: uint256
  maturity: uint256
  collateral: Collateral
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


@view
@internal
def _hasApprovedLoan(_address: address) -> bool:
  return self.loans[_address].approved == True


@view
@internal
def _hasStartedLoan(_address: address) -> bool:
  return self.loans[_address].issued == True


@view
@internal
def _isCollateralApproved(_address: address) -> bool:
  return CollateralContract(self.loans[_address].collateral.contract).getApproved(self.loans[_address].collateral.id) == self


@view
@internal
def _collateralAddress(_address: address) -> address:
  return self.loans[_address].collateral.contract


@view
@internal
def _collateralId(_address: address) -> uint256:
  return self.loans[_address].collateral.id


@external
def setInvestmentPoolAddress(_address: address) -> address:
  assert msg.sender == self.owner, "Only the contract owner can set the investment pool address!"

  self.invPool = InvestmentPool(_address)
  self.invPoolAddress = _address
  return self.invPoolAddress


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
  _collateralAddress: address,
  _collateralId: uint256
) -> Loan:
  assert msg.sender == self.owner, "Only the contract owner can create loans!"
  assert self._hasApprovedLoan(_borrower) == False, "The sender already has an approved loan!"
  assert self.whitelistedCollaterals[_collateralAddress] != empty(address), "The collateral address is not whitelisted!"
  assert block.timestamp <= _maturity, "Maturity can not be in the past!"
  

  newCollateral: Collateral = Collateral(
    {
      contract: _collateralAddress,
      id: _collateralId
    }
  )

  loan: Loan = Loan(
    {
      amount: _amount,
      interest: _interest,
      paidAmount: 0,
      paidAmountInterest: 0,
      maturity: _maturity,
      collateral: newCollateral,
      approved: True, issued: False, defaulted: False, paid: False})

  self.loans[_borrower] = loan
  self.currentApprovedLoans += 1
  self.totalApprovedLoans += 1

  return self.loans[_borrower] 


@external
def startApprovedLoan() -> Loan:
  assert self._hasApprovedLoan(msg.sender) == True, "The sender does not have an approved loan!"
  assert self._isCollateralApproved(msg.sender) == True, "The collateral is not approved to be transferred!"

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
  CollateralContract(self._collateralAddress(msg.sender)).transferFrom(
    msg.sender,
    self,
    self._collateralId(msg.sender)
  )
  
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

  collateralAddress: address = self._collateralAddress(msg.sender)
  collateralId: uint256 = self._collateralId(msg.sender)

  paidAmount: uint256 = msg.value * 10000 / (10000 + self.loans[msg.sender].interest)
  paidAmountInterest: uint256 = msg.value - paidAmount

  if msg.value == allowedPayment:
    self.loans[msg.sender] = empty(Loan)
    self.currentApprovedLoans -= 1
    self.currentIssuedLoans -= 1
    self.totalPaidLoans += 1
  else:
    self.loans[msg.sender].paidAmount += paidAmount
    self.loans[msg.sender].paidAmountInterest += paidAmountInterest

  raw_call(self.invPoolAddress, _abi_encode(paidAmount, paidAmountInterest, method_id=method_id("receiveFunds(uint256,uint256)")), value=msg.value)
  
  if msg.value == allowedPayment:
    CollateralContract(collateralAddress).safeTransferFrom(
      self,
      msg.sender,
      collateralId
    )

  log LoanPaid(msg.sender)

  return self.loans[msg.sender]


@external
def settleDefaultedLoan(_borrower: address) -> Loan:
  assert msg.sender == self.owner, "Only the contract owner can default loans!"
  assert self._hasStartedLoan(_borrower), "The sender does not have an issued loan!"
  assert block.timestamp > self.loans[_borrower].maturity, "The maturity of the loan has not been reached yet!"

  collateral_address: address = self._collateralAddress(_borrower)
  collateral_id: uint256 = self._collateralId(_borrower)
  self.loans[_borrower] = empty(Loan)

  self.currentApprovedLoans -= 1
  self.currentIssuedLoans -= 1
  self.totalDefaultedLoans += 1

  CollateralContract(collateral_address).safeTransferFrom(
    self,
    self.owner,
    collateral_id
  )

  return self.loans[_borrower]


@external
def cancelApprovedLoan() -> Loan:
  assert self._hasApprovedLoan(msg.sender), "The sender does not have an approved loan!"
  assert self._hasStartedLoan(msg.sender) == False, "The loan has already been started, please pay the loan."

  self.loans[msg.sender] = empty(Loan)

  self.currentApprovedLoans -= 1

  log LoanCanceled(msg.sender)

  return self.loans[msg.sender]


# @view
# @external
# def onERC721Received(_operator: address, _from: address, _tokenId: uint256, _data: Bytes[1024]) -> Bytes[4]:
    # return method_id("onERC721Received(address,address,uint256,bytes)", output_type=Bytes[4])
    # return 0xf0b9e5ba
#     return 0x150b7a02

@external
@payable
def __default__():
  raise "No function called!"

