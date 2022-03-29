# @version ^0.3.2


# Interfaces

from interfaces import ILoansCore

interface ILendingPool:
    def sendFunds(_to: address, _amount: uint256) -> uint256: nonpayable
    def receiveFunds(_owner: address, _amount: uint256, _rewardsAmount: uint256) -> uint256: nonpayable
    def maxFundsInvestable() -> int256: view
    def erc20TokenContract() -> address: view

interface ICollateral:
    def supportsInterface(_interfaceID: bytes32) -> bool: view
    def ownerOf(tokenId: uint256) -> address: view
    def getApproved(tokenId: uint256) -> address: view
    def isApprovedForAll(owner: address, operator: address) -> bool: view
    def safeTransferFrom(_from: address, _to: address, tokenId: uint256): nonpayable
    def transferFrom(_from: address, _to: address, tokenId: uint256): nonpayable

interface IERC20:
    def allowance(_owner: address, _spender: address) -> uint256: view
    def balanceOf(_account: address) -> uint256: view
    def symbol() -> String[10]: view


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
    invalidated: bool
    paid: bool
    defaulted: bool
    canceled: bool


# Events

event LoanCreated:
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanValidated:
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanInvalidated:
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanPayment:
    wallet: address
    loanId: uint256
    amount: uint256
    erc20TokenContract: address

event LoanPaid:
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanDefaulted:
    wallet: address
    loanId: uint256
    amount: uint256
    erc20TokenContract: address

event PendingLoanCanceled:
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanCanceled:
    wallet: address
    loanId: uint256
    erc20TokenContract: address


# Global variables

owner: public(address)
maxAllowedLoans: public(uint256)
maxAllowedLoanDuration: public(uint256)
minLoanAmount: public(uint256)
maxLoanAmount: public(uint256)

isAcceptingLoans: public(bool)
isDeprecated: public(bool)

whitelistedCollateralsAddresses: public(DynArray[address, 2**50]) # array of all collateral addresses that are or were already whitelisted
whitelistedCollaterals: public(HashMap[address, bool]) # given a collateral address, is the collection whitelisted

loansCore: ILoansCore
loansCoreAddress: public(address)

lendingPool: ILendingPool
lendingPoolAddress: public(address)


@external
def __init__(
    _maxAllowedLoans: uint256,
    _maxAllowedLoanDuration: uint256,
    _minLoanAmount: uint256,
    _maxLoanAmount: uint256
):
    self.owner = msg.sender
    self.maxAllowedLoans = _maxAllowedLoans
    self.maxAllowedLoanDuration = _maxAllowedLoanDuration
    self.minLoanAmount = _minLoanAmount
    self.maxLoanAmount = _maxLoanAmount
    self.isAcceptingLoans = True
    self.isDeprecated = False


@internal
def _areCollateralsWhitelisted(_collaterals: DynArray[Collateral, 10]) -> bool:
    for collateral in _collaterals:
        if not self.whitelistedCollaterals[collateral.contractAddress]:
            return False
    return True


@internal
def _areCollateralsOwned(_borrower: address, _collaterals: DynArray[Collateral, 10]) -> bool:
    for collateral in _collaterals:
        if ICollateral(collateral.contractAddress).ownerOf(collateral.tokenId) != _borrower:
            return False
    return True


@view
@internal
def _isCollateralApproved(_borrower: address, _operator: address, _contractAddress: address) -> bool:
    return ICollateral(_contractAddress).isApprovedForAll(_borrower, _operator)


@view
@internal
def _areCollateralsApproved(_borrower: address, _collaterals: DynArray[Collateral, 10]) -> bool:
    for collateral in _collaterals:
        if not self._isCollateralApproved(_borrower, self, collateral.contractAddress):
            return False
    return True


@external
def changeOwnership(_newOwner: address) -> address:
    assert msg.sender == self.owner, "Only the owner can change the contract ownership"

    self.owner = _newOwner

    return self.owner


@external
def changeMaxAllowedLoans(_maxAllowedLoans: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the owner can change the max allowed loans per address"

    self.maxAllowedLoans = _maxAllowedLoans

    return self.maxAllowedLoans


@external
def changeMaxAllowedLoanDuration(_maxAllowedLoanDuration: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the owner can change the max allowed loan duration"

    self.maxAllowedLoanDuration = _maxAllowedLoanDuration

    return self.maxAllowedLoanDuration


@external
def addCollateralToWhitelist(_address: address) -> bool:
    assert msg.sender == self.owner, "Only the contract owner can add collateral addresses to the whitelist"
    assert _address.is_contract == True, "The _address sent does not have a contract deployed"

    self.whitelistedCollaterals[_address] = True
    if _address not in self.whitelistedCollateralsAddresses:
        self.whitelistedCollateralsAddresses.append(_address)

    return True


@external
def removeCollateralFromWhitelist(_address: address) -> bool:
    assert msg.sender == self.owner, "Only the contract owner can add collateral addresses to the whitelist"
    assert _address in self.whitelistedCollateralsAddresses, "The collateral is not whitelisted"

    self.whitelistedCollaterals[_address] = False

    return True


@external
def changeMinLoanAmount(_newMinLoanAmount: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the contract owner can change the min loan amount"
    assert _newMinLoanAmount <= self.maxLoanAmount, "The min loan amount can not be higher than the max loan amount"

    self.minLoanAmount = _newMinLoanAmount

    return self.minLoanAmount


@external
def changeMaxLoanAmount(_newMaxLoanAmount: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the contract owner can change the max loan amount"
    assert _newMaxLoanAmount >= self.minLoanAmount, "The max loan amount can not be lower than the min loan amount"

    self.maxLoanAmount = _newMaxLoanAmount

    return self.maxLoanAmount


@external
def setLoansCoreAddress(_address: address) -> address:
    assert msg.sender == self.owner, "Only the contract owner can set the LoansCore address"
    assert self.loansCoreAddress != _address, "The new LoansCore address should be different than the current one"

    self.loansCore = ILoansCore(_address)
    self.loansCoreAddress = _address
    return self.loansCoreAddress


@external
def setLendingPoolAddress(_address: address) -> address:
    assert msg.sender == self.owner, "Only the contract owner can set the investment pool address"

    self.lendingPool = ILendingPool(_address)
    self.lendingPoolAddress = _address
    return self.lendingPoolAddress


@external
def changeContractStatus(_flag: bool) -> bool:
    assert msg.sender == self.owner, "Only the contract owner can change the status of the contract"
    assert self.isAcceptingLoans != _flag, "The new contract status should be different than the current status"

    self.isAcceptingLoans = _flag

    return self.isAcceptingLoans


@external
def deprecate() -> bool:
    assert msg.sender == self.owner, "Only the contract owner can deprecate the contract"
    assert not self.isDeprecated, "The contract is already deprecated"

    self.isDeprecated = True
    self.isAcceptingLoans = False

    return self.isDeprecated


@view
@external
def getWhitelistedCollateralsAddresses() -> DynArray[address, 2**50]:
    return self.whitelistedCollateralsAddresses


@view
@external
def erc20TokenSymbol() -> String[10]:
    return IERC20(self.lendingPool.erc20TokenContract()).symbol()


@view
@external
def getPendingLoan(_borrower: address, _loanId: uint256) -> Loan:
    return self.loansCore.getPendingLoan(_borrower, _loanId)


@view
@external
def getLoan(_borrower: address, _loanId: uint256) -> Loan:
    return self.loansCore.getLoan(_borrower, _loanId)


@external
def reserve(
    _amount: uint256,
    _interest: uint256,
    _maturity: uint256,
    _collaterals: DynArray[Collateral, 10]
) -> uint256:
    assert not self.isDeprecated, "The contract is deprecated, no more loans can be created"
    assert self.isAcceptingLoans, "The contract is not accepting more loans right now"
    assert block.timestamp <= _maturity, "Maturity can not be in the past"
    assert _maturity - block.timestamp <= self.maxAllowedLoanDuration, "Maturity can not exceed the max allowed"
    assert self._areCollateralsWhitelisted(_collaterals), "Not all collaterals are whitelisted"
    assert self._areCollateralsOwned(msg.sender, _collaterals), "Not all collaterals are owned by the borrower"
    assert self._areCollateralsApproved(msg.sender, _collaterals) == True, "Not all collaterals are approved to be transferred"
    assert self.lendingPool.maxFundsInvestable() >= convert(_amount, int256), "Insufficient funds in the lending pool"
    assert _amount >= self.minLoanAmount, "Loan amount is less than the min loan amount"
    assert _amount <= self.maxLoanAmount, "Loan amount is more than the max loan amount"

    newLoanId: uint256 = self.loansCore.addLoan(
        msg.sender,
        _amount,
        _interest,
        _maturity,
        _collaterals
    )

    for collateral in _collaterals:
        ICollateral(collateral.contractAddress).transferFrom(msg.sender, self, collateral.tokenId)

        self.loansCore.addCollateralToLoan(msg.sender, collateral, newLoanId)
        
        self.loansCore.updateCollaterals(collateral, False)

    log LoanCreated(msg.sender, newLoanId, self.lendingPool.erc20TokenContract())

    return newLoanId


@external
def validate(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "Only the contract owner can validate loans"
    assert not self.isDeprecated, "The contract is deprecated, please pay any outstanding loans"
    assert self.isAcceptingLoans, "The contract is not accepting more loans right now, please pay any outstanding loans"
    assert self.loansCore.isLoanCreated(_borrower, _loanId), "This loan has not been created for the borrower"
    assert block.timestamp <= self.loansCore.getLoanMaturity(_borrower, _loanId), "Maturity can not be in the past"
    assert self._areCollateralsWhitelisted(self.loansCore.getLoanCollaterals(_borrower, _loanId)), "Not all collaterals are whitelisted"
    assert self._areCollateralsOwned(self, self.loansCore.getLoanCollaterals(_borrower, _loanId)), "Not all collaterals are owned by the protocol"
    assert self.lendingPool.maxFundsInvestable() >= convert(self.loansCore.getLoanAmount(_borrower, _loanId), int256), "Insufficient funds in the lending pool"

    self.loansCore.updateLoanStarted(_borrower, _loanId)
    
    self.loansCore.updateHighestSingleCollateralLoan(_borrower, _loanId)

    self.loansCore.updateHighestCollateralBundleLoan(_borrower, _loanId)

    self.lendingPool.sendFunds(_borrower, self.loansCore.getLoanAmount(_borrower, _loanId))

    log LoanValidated(_borrower, _loanId, self.lendingPool.erc20TokenContract())


@external
def invalidate(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "Only the contract owner can invalidate loans"
    assert self.loansCore.isLoanCreated(_borrower, _loanId), "This loan has not been created for the borrower"

    collaterals: DynArray[Collateral, 10] = self.loansCore.getLoanCollaterals(_borrower, _loanId)
    for collateral in collaterals:
        ICollateral(collateral.contractAddress).safeTransferFrom(self, _borrower, collateral.tokenId)

        self.loansCore.removeCollateralFromLoan(_borrower, collateral, _loanId)

        self.loansCore.updateCollaterals(collateral, True)
    
    self.loansCore.updateInvalidLoan(_borrower, _loanId)

    log LoanInvalidated(_borrower, _loanId, self.lendingPool.erc20TokenContract())


@external
def pay(_loanId: uint256, _amountPaid: uint256):
    assert self.loansCore.isLoanStarted(msg.sender, _loanId), "The sender has not started a loan with the given ID"
    assert block.timestamp <= self.loansCore.getLoanMaturity(msg.sender, _loanId), "The maturity of the loan has already been reached and it defaulted"
    assert _amountPaid > 0, "The amount paid needs to be higher than 0"

    maxPayment: uint256 = self.loansCore.getLoanAmount(msg.sender, _loanId) * (10000 + self.loansCore.getLoanInterest(msg.sender, _loanId)) / 10000
    allowedPayment: uint256 = maxPayment - self.loansCore.getLoanPaidAmount(msg.sender, _loanId)
    borrowerBalance: uint256 = IERC20(self.lendingPool.erc20TokenContract()).balanceOf(msg.sender)
    lendingPoolAllowance: uint256 = IERC20(self.lendingPool.erc20TokenContract()).allowance(msg.sender, self.lendingPoolAddress)
    assert _amountPaid <= allowedPayment, "The amount paid is higher than the amount left to be paid"
    assert borrowerBalance >= _amountPaid, "User has insufficient balance for the payment"
    assert lendingPoolAllowance >= _amountPaid, "User did not allow funds to be transferred"

    paidAmount: uint256 = _amountPaid * 10000 / (10000 + self.loansCore.getLoanInterest(msg.sender, _loanId))
    paidAmountInterest: uint256 = _amountPaid - paidAmount

    if _amountPaid == allowedPayment:
        collaterals: DynArray[Collateral, 10] = self.loansCore.getLoanCollaterals(msg.sender, _loanId)
        for collateral in collaterals:
            ICollateral(collateral.contractAddress).safeTransferFrom(self, msg.sender, collateral.tokenId)

            self.loansCore.removeCollateralFromLoan(msg.sender, collateral, _loanId)

            self.loansCore.updateCollaterals(collateral, True)

        self.loansCore.updatePaidLoan(msg.sender, _loanId)
        
        log LoanPaid(msg.sender, _loanId, self.lendingPool.erc20TokenContract())

    self.loansCore.updateLoanPaidAmount(msg.sender, _loanId, paidAmount + paidAmountInterest)
    
    self.loansCore.updateHighestRepayment(msg.sender, _loanId)

    self.lendingPool.receiveFunds(msg.sender, paidAmount, paidAmountInterest)

    log LoanPayment(msg.sender, _loanId, _amountPaid, self.lendingPool.erc20TokenContract())


@external
def settleDefault(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "Only the contract owner can default loans"
    assert self.loansCore.isLoanStarted(_borrower, _loanId), "The _borrower has not started a loan with the given ID"
    assert block.timestamp > self.loansCore.getLoanMaturity(_borrower, _loanId), "The maturity of the loan has not been reached yet"

    collaterals: DynArray[Collateral, 10] = self.loansCore.getLoanCollaterals(_borrower, _loanId)
    for collateral in collaterals:
        ICollateral(collateral.contractAddress).safeTransferFrom(self, self.owner, collateral.tokenId)

        self.loansCore.removeCollateralFromLoan(_borrower, collateral, _loanId)

        self.loansCore.updateCollaterals(collateral, True)

    self.loansCore.updateDefaultedLoan(_borrower, _loanId)

    self.loansCore.updateHighestDefaultedLoan(_borrower, _loanId)

    log LoanDefaulted(
        _borrower,
        _loanId,
        self.loansCore.getLoanAmount(_borrower, _loanId),
        self.lendingPool.erc20TokenContract()
    )


@external
def cancelPendingLoan(_loanId: uint256):
    assert self.loansCore.isLoanCreated(msg.sender, _loanId), "The sender has not created a loan with the given ID"

    collaterals: DynArray[Collateral, 10] = self.loansCore.getLoanCollaterals(msg.sender, _loanId)
    for collateral in collaterals:
        ICollateral(collateral.contractAddress).safeTransferFrom(self, msg.sender, collateral.tokenId)

        self.loansCore.removeCollateralFromLoan(msg.sender, collateral, _loanId)

        self.loansCore.updateCollaterals(collateral, True)

    self.loansCore.updateCanceledLoan(msg.sender, _loanId) 

    log PendingLoanCanceled(msg.sender, _loanId, self.lendingPool.erc20TokenContract())


@external
@payable
def __default__():
    if msg.value > 0:
        send(msg.sender, msg.value)
