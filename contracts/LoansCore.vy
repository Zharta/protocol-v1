# @version ^0.3.2


# Structs

struct Collateral:
    contractAddress: address
    tokenId: uint256


struct Loan:
    id: uint256
    amount: uint256
    interest: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    maturity: uint256
    startTime: uint256
    collaterals: DynArray[Collateral, 10]
    paidAmount: uint256
    started: bool


struct TopStats:
    highestSingleCollateralLoan: Loan
    highestCollateralBundleLoan: Loan
    highestRepayment: Loan
    highestDefaultedLoan: Loan


# Global variables

owner: public(address)
loansPeripheral: public(address)

loans: HashMap[address, DynArray[Loan, 10]]
loanIdsUsed: HashMap[address, bool[10]]
nextLoanId: public(HashMap[address, uint256])

maxAllowedLoans: public(uint256)

# key: bytes32 == _abi_encoded(token_address, token_id) -> map(borrower_address, loan_id)
collateralsInLoans: public(HashMap[bytes32, HashMap[address, uint256]]) # given a collateral and a borrower, what is the loan id
collateralsInLoansUsed: public(HashMap[bytes32, HashMap[address, HashMap[uint256, bool]]]) # given a collateral, a borrower and a loan id, is the collateral still used in that loan id
collateralKeys: DynArray[bytes32, 2**50] # array of collaterals expressed by their keys
collateralsUsed: public(HashMap[bytes32, bool]) # given a collateral, is it being used in a loan
collateralsData: public(HashMap[bytes32, Collateral]) # given a collateral key, what is its data
collateralsIdsByAddress: public(HashMap[address, DynArray[uint256, 2**50]]) # given a collateral address, what are the token ids that were already in a loan

# Stats
topStats: TopStats


##### INTERNAL METHODS #####

@view
@internal
def _checkNextLoanId(_borrower: address) -> uint256:
    for index in range(10):
        if not self.loanIdsUsed[_borrower][index]:
            return index
    return 2*50 # arbitrarly large number


# @view
# @internal
# def _loanWithIdExists(_borrower: address, _loanId: uint256) -> bool:
#     return self.loanIdsUsed[_borrower][_loanId]


@view
@internal
def _isLoanCreated(_borrower: address, _loanId: uint256) -> bool:
    return self.loanIdsUsed[_borrower][_loanId]
    # if self.loanIdsUsed[_borrower][_loanId]:
    #     return not self.loans[_borrower][_loanId].started
    # return False


@view
@internal
def _isLoanStarted(_borrower: address, _loanId: uint256) -> bool:
    if self.loanIdsUsed[_borrower][_loanId]:
        return self.loans[_borrower][_loanId].started
    return False


@view
@internal
def _computeCollateralKey(_collateralAddress: address, _collateralId: uint256) -> bytes32:
  return keccak256(_abi_encode(_collateralAddress, convert(_collateralId, bytes32)))


@internal
def _addCollateralToLoan(_borrower: address, _collateral: Collateral, _loanId: uint256):
  key: bytes32 = self._computeCollateralKey(_collateral.contractAddress, _collateral.tokenId)
  self.collateralsInLoans[key][_borrower] = _loanId
  self.collateralsInLoansUsed[key][_borrower][_loanId] = True


@internal
def _removeCollateralFromLoan(_borrower: address, _collateral: Collateral, _loanId: uint256):
  key: bytes32 = self._computeCollateralKey(_collateral.contractAddress, _collateral.tokenId)
  self.collateralsInLoansUsed[key][_borrower][_loanId] = False


@internal
def _updateCollaterals(_collateral: Collateral, _toRemove: bool):
  key: bytes32 = self._computeCollateralKey(_collateral.contractAddress, _collateral.tokenId)

  if key not in self.collateralKeys and not _toRemove:
    self.collateralKeys.append(key)
    self.collateralsUsed[key] = True
    self.collateralsData[key] = _collateral
  elif key in self.collateralKeys:
    self.collateralsUsed[key] = not _toRemove

  if _collateral.tokenId not in self.collateralsIdsByAddress[_collateral.contractAddress] and not _toRemove:
    self.collateralsIdsByAddress[_collateral.contractAddress].append(_collateral.tokenId)


@internal
def _addLoan(_borrower: address, _loan: Loan):
    if len(self.loans[_borrower]) == self.nextLoanId[_borrower]:
        self.loans[_borrower].append(_loan)
    elif len(self.loans[_borrower]) >= self.nextLoanId[_borrower] + 1:
        self.loans[_borrower][self.nextLoanId[_borrower]] = _loan
    self.loanIdsUsed[_borrower][self.nextLoanId[_borrower]] = True
    self.nextLoanId[_borrower] = self._checkNextLoanId(_borrower)


@internal
def _removeLoan(_borrower: address, _loanId: uint256):
    if self.loanIdsUsed[_borrower][_loanId]:
        self.loans[_borrower][_loanId] = empty(Loan)
        self.nextLoanId[_borrower] = _loanId
        self.loanIdsUsed[_borrower][_loanId] = False


@internal
def _updateLoanPaidAmount(_borrower: address, _loanId: uint256, _paidAmount: uint256):
    if self.loanIdsUsed[_borrower][_loanId]:
        self.loans[_borrower][_loanId].paidAmount += _paidAmount


@internal
def _updateHighestSingleCollateralLoan(_borrower: address, _loanId: uint256):
    if len(self.loans[_borrower][_loanId].collaterals) == 1 and self.topStats.highestSingleCollateralLoan.amount < self.loans[_borrower][_loanId].amount:
        self.topStats.highestSingleCollateralLoan = self.loans[_borrower][_loanId]
  

@internal
def _updateHighestCollateralBundleLoan(_borrower: address, _loanId: uint256):
    if len(self.loans[_borrower][_loanId].collaterals) > 1 and self.topStats.highestCollateralBundleLoan.amount < self.loans[_borrower][_loanId].amount:
        self.topStats.highestCollateralBundleLoan = self.loans[_borrower][_loanId]


@internal
def _updateHighestRepayment(_borrower: address, _loanId: uint256):
    if self.topStats.highestRepayment.amount < self.loans[_borrower][_loanId].amount:
        self.topStats.highestRepayment = self.loans[_borrower][_loanId]


@internal
def _updateHighestDefaultedLoan(_borrower: address, _loanId: uint256):
    if self.topStats.highestDefaultedLoan.amount < self.loans[_borrower][_loanId].amount:
        self.topStats.highestDefaultedLoan = self.loans[_borrower][_loanId]


##### EXTERNAL METHODS #####

@external
def __init__(_loansPeripheral: address, _maxAllowedLoans: uint256):
    self.owner = msg.sender
    self.loansPeripheral = _loansPeripheral
    self.maxAllowedLoans = _maxAllowedLoans


@external
def changeOwnership(_newOwner: address) -> address:
    assert msg.sender == self.owner, "Only the owner can change the contract ownership"
    assert self.owner != _newOwner, "The new owner should be different than the current owner"

    self.owner = _newOwner

    return self.owner


@external
def changeLoansPeripheral(_newLoansPeripheral: address) -> address:
    assert msg.sender == self.owner, "Only the owner can change the contract ownership"
    assert _newLoansPeripheral != self.loansPeripheral, "The new loans peripheral address should be different than the current one"

    self.loansPeripheral = _newLoansPeripheral

    return self.loansPeripheral


@view
@external
def isLoanCreated(_borrower: address, _loanId: uint256) -> bool:
    return self._isLoanCreated(_borrower, _loanId)


@view
@external
def isLoanStarted(_borrower: address, _loanId: uint256) -> bool:
    return self._isLoanStarted(_borrower, _loanId)


@view
@external
def getLoanIdsUsedByAddress(_borrower: address) -> bool[10]:
  return self.loanIdsUsed[_borrower]


@view
@external
def getLoanAmount(_borrower: address, _loanId: uint256) -> uint256:
    if self.loanIdsUsed[_borrower][_loanId]:
        return self.loans[_borrower][_loanId].amount
    return 0


@view
@external
def getLoanMaturity(_borrower: address, _loanId: uint256) -> uint256:
    if self.loanIdsUsed[_borrower][_loanId]:
        return self.loans[_borrower][_loanId].maturity
    return 0


@view
@external
def getLoanInterest(_borrower: address, _loanId: uint256) -> uint256:
    if self.loanIdsUsed[_borrower][_loanId]:
        return self.loans[_borrower][_loanId].interest
    return 0


@view
@external
def getLoanCollaterals(_borrower: address, _loanId: uint256) -> DynArray[Collateral, 10]:
    if self.loanIdsUsed[_borrower][_loanId]:
        return self.loans[_borrower][_loanId].collaterals
    return empty(DynArray[Collateral, 10])


@view
@external
def getLoanStartTime(_borrower: address, _loanId: uint256) -> uint256:
    if self.loanIdsUsed[_borrower][_loanId]:
        return self.loans[_borrower][_loanId].startTime
    return 0


@view
@external
def getLoanPaidAmount(_borrower: address, _loanId: uint256) -> uint256:
    if self.loanIdsUsed[_borrower][_loanId]:
        return self.loans[_borrower][_loanId].paidAmount
    return 0


@view
@external
def getLoanStarted(_borrower: address, _loanId: uint256) -> bool:
    if self.loanIdsUsed[_borrower][_loanId]:
        return self.loans[_borrower][_loanId].started
    return False


@view
@external
def getPendingBorrowerLoan(_borrower: address, _loanId: uint256) -> Loan:
  if self._isLoanCreated(_borrower, _loanId):
    return self.loans[_borrower][_loanId]
  return empty(Loan)


@view
@external
def getPendingBorrowerLoans(_borrower: address) -> DynArray[Loan, 10]:
  result: DynArray[Loan, 10] = []
  _loans: DynArray[Loan, 10] = self.loans[_borrower]
  for loan in _loans:
    if not loan.started and loan.amount > 0:
      result.append(loan)
  return result


@view
@external
def getBorrowerLoan(_borrower: address, _loanId: uint256) -> Loan:
  if self._isLoanStarted(_borrower, _loanId):
    return self.loans[_borrower][_loanId]
  return empty(Loan)


@view
@external
def getBorrowerLoans(_borrower: address) -> DynArray[Loan, 10]:
  result: DynArray[Loan, 10] = []
  _loans: DynArray[Loan, 10] = self.loans[_borrower]
  for loan in _loans:
    if loan.started and loan.amount > 0:
      result.append(loan)
  return result


@view
@external
def getHighestSingleCollateralLoan() -> Loan:
    return self.topStats.highestSingleCollateralLoan


@view
@external
def getHighestCollateralBundleLoan() -> Loan:
    return self.topStats.highestCollateralBundleLoan


@view
@external
def getHighestRepayment() -> Loan:
    return self.topStats.highestRepayment


@view
@external
def getHighestDefaultedLoan() -> Loan:
    return self.topStats.highestDefaultedLoan


@view
@external
def collateralKeysArray() -> DynArray[bytes32, 2**50]:
  return self.collateralKeys


@view
@external
def getCollateralsIdsByAddress(_address: address) -> DynArray[uint256, 2**50]:
  return self.collateralsIdsByAddress[_address]


@external
def addCollateralToLoan(_borrower: address, _collateral: Collateral, _loanId: uint256):
    assert msg.sender == self.loansPeripheral, "Only loans peripheral address can add collaterals to loans"
    assert self._isLoanCreated(_borrower, _loanId), "No loan created for borrower with passed id"

    self._addCollateralToLoan(_borrower, _collateral, _loanId)


@external
def removeCollateralFromLoan(_borrower: address, _collateral: Collateral, _loanId: uint256):
    assert msg.sender == self.loansPeripheral, "Only loans peripheral address can add remove collaterals from loans"
    assert self._isLoanCreated(_borrower, _loanId), "No loan created for borrower with passed id"
    
    self._removeCollateralFromLoan(_borrower, _collateral, _loanId)


@external
def updateCollaterals(_collateral: Collateral, _toRemove: bool):
    assert msg.sender == self.loansPeripheral, "Only loans peripheral address can update collaterals"

    self._updateCollaterals(_collateral, _toRemove)


@external
def addLoan(
    _borrower: address,
    _amount: uint256,
    _interest: uint256,
    _maturity: uint256,
    _collaterals: DynArray[Collateral, 10]
) -> uint256:
    assert msg.sender == self.loansPeripheral, "Only defined loans peripheral can add loans"
    assert self.nextLoanId[_borrower] < self.maxAllowedLoans, "Max number of loans for borrower already reached"

    newLoan: Loan = Loan(
        {
            id: self.nextLoanId[_borrower],
            amount: _amount,
            interest: _interest,
            maturity: _maturity,
            startTime: block.timestamp,
            paidAmount: 0,
            started: False,
            collaterals: _collaterals
        }
    )

    self._addLoan(_borrower, newLoan)

    return newLoan.id


@external
def removeLoan(_borrower: address, _loanId: uint256):
    assert msg.sender == self.loansPeripheral, "Only defined loans peripheral can remove loans"
    assert self._isLoanCreated(_borrower, _loanId), "No loan created for borrower with passed id"

    self._removeLoan(_borrower, _loanId)


@external
def updateLoanStarted(_borrower: address, _loanId: uint256):
    assert msg.sender == self.loansPeripheral, "Only defined loans peripheral can update loans"
    assert self._isLoanCreated(_borrower, _loanId), "No loan created for borrower with passed id"
    assert not self._isLoanStarted(_borrower, _loanId), "Loan already started"

    self.loans[_borrower][_loanId].started = True


@external
def updateLoanPaidAmount(_borrower: address, _loanId: uint256, _paidAmount: uint256):
    assert msg.sender == self.loansPeripheral, "Only defined loans peripheral can update loans"
    assert self._isLoanCreated(_borrower, _loanId), "No loan created for borrower with passed id"
    assert self._isLoanStarted(_borrower, _loanId), "The loan has not been started yet"
    maxPayment: uint256 = self.loans[_borrower][_loanId].amount * (10000 + self.loans[_borrower][_loanId].interest) / 10000
    allowedPayment: uint256 = maxPayment - self.loans[_borrower][_loanId].paidAmount
    assert _paidAmount <= allowedPayment, "The amount paid is higher than the amount left to be paid"
  
    self._updateLoanPaidAmount(_borrower, _loanId, _paidAmount)


@external
def updateHighestSingleCollateralLoan(_borrower: address, _loanId: uint256):
    assert msg.sender == self.loansPeripheral, "Only defined loans peripheral can update stats"
  
    self._updateHighestSingleCollateralLoan(_borrower, _loanId)
  

@external
def updateHighestCollateralBundleLoan(_borrower: address, _loanId: uint256):
    assert msg.sender == self.loansPeripheral, "Only defined loans peripheral can update stats"

    self._updateHighestCollateralBundleLoan(_borrower, _loanId)


@external
def updateHighestRepayment(_borrower: address, _loanId: uint256):
    assert msg.sender == self.loansPeripheral, "Only defined loans peripheral can update stats"

    self._updateHighestRepayment(_borrower, _loanId)


@external
def updateHighestDefaultedLoan(_borrower: address, _loanId: uint256):
    assert msg.sender == self.loansPeripheral, "Only defined loans peripheral can update stats"

    self._updateHighestDefaultedLoan(_borrower, _loanId)


@external
@payable
def __default__():
    if msg.value > 0:
        send(msg.sender, msg.value)
