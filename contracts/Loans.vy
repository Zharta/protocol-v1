# @version ^0.3.3


# Interfaces

from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721
from interfaces import ILoansCore
from interfaces import ILendingPoolPeripheral

interface IERC20:
    def allowance(_owner: address, _spender: address) -> uint256: view
    def balanceOf(_account: address) -> uint256: view
    def symbol() -> String[100]: view


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
    collaterals: DynArray[Collateral, 100]
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

ongoingLoans: public(HashMap[address, uint256])

isAcceptingLoans: public(bool)
isDeprecated: public(bool)

whitelistedCollateralsAddresses: public(DynArray[address, 2**50]) # array of all collateral addresses that are or were already whitelisted
whitelistedCollaterals: public(HashMap[address, bool]) # given a collateral address, is the collection whitelisted

loansCoreAddress: public(address)
lendingPoolAddress: public(address)
lendingPoolCoreAddress: public(address)


@external
def __init__(
    _maxAllowedLoans: uint256,
    _maxAllowedLoanDuration: uint256,
    _minLoanAmount: uint256,
    _maxLoanAmount: uint256,
    _loansCoreAddress: address,
    _lendingPoolAddress: address,
    _lendingPoolCoreAddress: address
):
    assert _maxAllowedLoans > 0, "Max allowed loans needs to be higher than 0"
    assert _maxAllowedLoanDuration > 0, "Max duration needs to be higher than 0"
    assert _maxLoanAmount >= _minLoanAmount, "Max loan amount needs to be higher min loan amount"
    assert _loansCoreAddress != ZERO_ADDRESS, "The LoansCore address is the zero address"
    assert _lendingPoolAddress != ZERO_ADDRESS, "The LendingPoolPeripheral address is the zero address"
    assert _lendingPoolCoreAddress != ZERO_ADDRESS, "The LendingPoolCore address is the zero address"

    self.owner = msg.sender
    self.maxAllowedLoans = _maxAllowedLoans
    self.maxAllowedLoanDuration = _maxAllowedLoanDuration
    self.minLoanAmount = _minLoanAmount
    self.maxLoanAmount = _maxLoanAmount
    self.loansCoreAddress = _loansCoreAddress
    self.lendingPoolAddress = _lendingPoolAddress
    self.lendingPoolCoreAddress = _lendingPoolCoreAddress
    self.isAcceptingLoans = True
    self.isDeprecated = False


@internal
def _areCollateralsWhitelisted(_collaterals: DynArray[Collateral, 100]) -> bool:
    for collateral in _collaterals:
        if not self.whitelistedCollaterals[collateral.contractAddress]:
            return False
    return True


@internal
def _areCollateralsOwned(_borrower: address, _collaterals: DynArray[Collateral, 100]) -> bool:
    for collateral in _collaterals:
        if IERC721(collateral.contractAddress).ownerOf(collateral.tokenId) != _borrower:
            return False
    return True


@view
@internal
def _isCollateralApproved(_borrower: address, _operator: address, _contractAddress: address) -> bool:
    return IERC721(_contractAddress).isApprovedForAll(_borrower, _operator)


@view
@internal
def _areCollateralsApproved(_borrower: address, _collaterals: DynArray[Collateral, 100]) -> bool:
    for collateral in _collaterals:
        if not self._isCollateralApproved(_borrower, self, collateral.contractAddress):
            return False
    return True


@external
def changeOwnership(_newOwner: address) -> address:
    assert msg.sender == self.owner, "Only the owner can change the contract ownership"
    assert _newOwner != self.owner, "New owner should be different than the current owner"

    self.owner = _newOwner

    return self.owner


@external
def changeMaxAllowedLoans(_maxAllowedLoans: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the owner can change the max allowed loans per address"
    assert _maxAllowedLoans > 0, "Max allowed loans should be higher than 0"
    assert _maxAllowedLoans != self.maxAllowedLoans, "New value for max allowed loans should be different than the current value"

    self.maxAllowedLoans = _maxAllowedLoans

    return self.maxAllowedLoans


@external
def changeMaxAllowedLoanDuration(_maxAllowedLoanDuration: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the owner can change the max allowed loan duration"
    assert _maxAllowedLoanDuration > 0, "Max duration needs to be higher than 0"
    assert _maxAllowedLoanDuration != self.maxAllowedLoanDuration, "New value for max duration should be different than the current one"

    self.maxAllowedLoanDuration = _maxAllowedLoanDuration

    return self.maxAllowedLoanDuration


@external
def changeMinLoanAmount(_newMinLoanAmount: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the contract owner can change the min loan amount"
    assert _newMinLoanAmount != self.minLoanAmount, "New value for min loan amount should be different than the current one"
    assert _newMinLoanAmount <= self.maxLoanAmount, "The min loan amount can not be higher than the max loan amount"

    self.minLoanAmount = _newMinLoanAmount

    return self.minLoanAmount


@external
def changeMaxLoanAmount(_newMaxLoanAmount: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the contract owner can change the max loan amount"
    assert _newMaxLoanAmount != self.maxLoanAmount, "New value for max loan amount should be different than the current one"
    assert _newMaxLoanAmount >= self.minLoanAmount, "The max loan amount can not be lower than the min loan amount"

    self.maxLoanAmount = _newMaxLoanAmount

    return self.maxLoanAmount


@external
def addCollateralToWhitelist(_address: address) -> bool:
    assert msg.sender == self.owner, "Only the contract owner can add collateral addresses to the whitelist"
    assert _address != ZERO_ADDRESS, "The address is the zero address"
    assert _address.is_contract == True, "The address sent does not have a deployed contract"
    # No method yet to get the interface_id, so explicitly checking the ERC721 interface_id
    assert IERC165(_address).supportsInterface(0x80ac58cd), "The address is not of a ERC721 contract"

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
def setLoansCoreAddress(_address: address) -> address:
    assert msg.sender == self.owner, "Only the contract owner can set the LoansCore address"
    assert _address != ZERO_ADDRESS, "The address is the zero address"
    assert self.loansCoreAddress != _address, "The new LoansCore address should be different than the current one"

    self.loansCoreAddress = _address
    return self.loansCoreAddress


@external
def setLendingPoolPeripheralAddress(_address: address) -> address:
    assert msg.sender == self.owner, "Only the contract owner can set the investment pool address"
    assert _address != ZERO_ADDRESS, "The address is the zero address"
    assert self.lendingPoolAddress != _address, "The new LendingPoolPeripheral address should be different than the current one"

    self.lendingPoolAddress = _address
    return self.lendingPoolAddress


@external
def setLendingPoolCoreAddress(_address: address) -> address:
    assert msg.sender == self.owner, "Only the contract owner can set the investment pool core address"
    assert _address != ZERO_ADDRESS, "The address is the zero address"
    assert self.lendingPoolCoreAddress != _address, "The new LendingPoolCore address should be different than the current one"

    self.lendingPoolCoreAddress = _address
    return self.lendingPoolCoreAddress


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
def erc20TokenSymbol() -> String[100]:
    return IERC20(ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()).symbol()


@view
@external
def getPendingLoan(_borrower: address, _loanId: uint256) -> Loan:
    return ILoansCore(self.loansCoreAddress).getPendingLoan(_borrower, _loanId)


@view
@external
def getLoan(_borrower: address, _loanId: uint256) -> Loan:
    return ILoansCore(self.loansCoreAddress).getLoan(_borrower, _loanId)


@external
def reserve(
    _amount: uint256,
    _interest: uint256,
    _maturity: uint256,
    _collaterals: DynArray[Collateral, 100]
) -> uint256:
    assert not self.isDeprecated, "The contract is deprecated, no more loans can be created"
    assert self.isAcceptingLoans, "The contract is not accepting more loans right now"
    assert block.timestamp <= _maturity, "Maturity can not be in the past"
    assert _maturity - block.timestamp <= self.maxAllowedLoanDuration, "Maturity can not exceed the max allowed"
    assert self._areCollateralsWhitelisted(_collaterals), "Not all collaterals are whitelisted"
    assert self._areCollateralsOwned(msg.sender, _collaterals), "Not all collaterals are owned by the borrower"
    assert self._areCollateralsApproved(msg.sender, _collaterals) == True, "Not all collaterals are approved to be transferred"
    assert ILendingPoolPeripheral(self.lendingPoolAddress).maxFundsInvestable() >= convert(_amount, int256), "Insufficient funds in the lending pool"
    assert self.ongoingLoans[msg.sender] < self.maxAllowedLoans, "Max number of loans for borrower already reached"
    assert _amount >= self.minLoanAmount, "Loan amount is less than the min loan amount"
    assert _amount <= self.maxLoanAmount, "Loan amount is more than the max loan amount"

    self.ongoingLoans[msg.sender] += 1

    newLoanId: uint256 = ILoansCore(self.loansCoreAddress).addLoan(
        msg.sender,
        _amount,
        _interest,
        _maturity,
        _collaterals
    )

    for collateral in _collaterals:
        ILoansCore(self.loansCoreAddress).addCollateralToLoan(msg.sender, collateral, newLoanId)
        ILoansCore(self.loansCoreAddress).updateCollaterals(collateral, False)

        IERC721(collateral.contractAddress).transferFrom(msg.sender, self, collateral.tokenId)

    log LoanCreated(msg.sender, newLoanId, ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract())

    return newLoanId


@external
def validate(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "Only the contract owner can validate loans"
    assert not self.isDeprecated, "The contract is deprecated, please pay any outstanding loans"
    assert self.isAcceptingLoans, "The contract is not accepting more loans right now, please pay any outstanding loans"
    assert ILoansCore(self.loansCoreAddress).isLoanCreated(_borrower, _loanId), "This loan has not been created for the borrower"
    assert not ILoansCore(self.loansCoreAddress).isLoanStarted(_borrower, _loanId), "The loan was already validated"
    assert not ILoansCore(self.loansCoreAddress).getLoanInvalidated(_borrower, _loanId), "The loan was already invalidated"
    assert block.timestamp <= ILoansCore(self.loansCoreAddress).getLoanMaturity(_borrower, _loanId), "Maturity can not be in the past"
    assert self._areCollateralsWhitelisted(ILoansCore(self.loansCoreAddress).getLoanCollaterals(_borrower, _loanId)), "Not all collaterals are whitelisted"
    assert self._areCollateralsOwned(self, ILoansCore(self.loansCoreAddress).getLoanCollaterals(_borrower, _loanId)), "Not all collaterals are owned by the protocol"
    assert ILendingPoolPeripheral(self.lendingPoolAddress).maxFundsInvestable() >= convert(ILoansCore(self.loansCoreAddress).getLoanAmount(_borrower, _loanId), int256), "Insufficient funds in the lending pool"

    ILoansCore(self.loansCoreAddress).updateLoanStarted(_borrower, _loanId)
    ILoansCore(self.loansCoreAddress).updateHighestSingleCollateralLoan(_borrower, _loanId)
    ILoansCore(self.loansCoreAddress).updateHighestCollateralBundleLoan(_borrower, _loanId)

    ILendingPoolPeripheral(self.lendingPoolAddress).sendFunds(_borrower, ILoansCore(self.loansCoreAddress).getLoanAmount(_borrower, _loanId))

    log LoanValidated(_borrower, _loanId, ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract())


@external
def invalidate(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "Only the contract owner can invalidate loans"
    assert ILoansCore(self.loansCoreAddress).isLoanCreated(_borrower, _loanId), "This loan has not been created for the borrower"
    assert not ILoansCore(self.loansCoreAddress).isLoanStarted(_borrower, _loanId), "The loan was already validated"
    assert not ILoansCore(self.loansCoreAddress).getLoanInvalidated(_borrower, _loanId), "The loan was already invalidated"

    self.ongoingLoans[_borrower] -= 1
    
    ILoansCore(self.loansCoreAddress).updateInvalidLoan(_borrower, _loanId)

    collaterals: DynArray[Collateral, 100] = ILoansCore(self.loansCoreAddress).getLoanCollaterals(_borrower, _loanId)
    for collateral in collaterals:
        ILoansCore(self.loansCoreAddress).removeCollateralFromLoan(_borrower, collateral, _loanId)
        ILoansCore(self.loansCoreAddress).updateCollaterals(collateral, True)

        IERC721(collateral.contractAddress).safeTransferFrom(self, _borrower, collateral.tokenId, b"")

    log LoanInvalidated(_borrower, _loanId, ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract())


@external
def pay(_loanId: uint256, _amountPaid: uint256):
    assert ILoansCore(self.loansCoreAddress).isLoanStarted(msg.sender, _loanId), "The sender has not started a loan with the given ID"
    assert block.timestamp <= ILoansCore(self.loansCoreAddress).getLoanMaturity(msg.sender, _loanId), "The maturity of the loan has already been reached and it defaulted"
    assert _amountPaid > 0, "The amount paid needs to be higher than 0"

    maxPayment: uint256 = ILoansCore(self.loansCoreAddress).getLoanAmount(msg.sender, _loanId) * (10000 + ILoansCore(self.loansCoreAddress).getLoanInterest(msg.sender, _loanId)) / 10000
    allowedPayment: uint256 = maxPayment - ILoansCore(self.loansCoreAddress).getLoanPaidAmount(msg.sender, _loanId)
    borrowerBalance: uint256 = IERC20(ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()).balanceOf(msg.sender)
    lendingPoolAllowance: uint256 = IERC20(ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()).allowance(msg.sender, self.lendingPoolCoreAddress)
    assert _amountPaid <= allowedPayment, "The amount paid is higher than the amount left to be paid"
    assert borrowerBalance >= _amountPaid, "User has insufficient balance for the payment"
    assert lendingPoolAllowance >= _amountPaid, "User did not allow funds to be transferred"

    paidAmount: uint256 = _amountPaid * 10000 / (10000 + ILoansCore(self.loansCoreAddress).getLoanInterest(msg.sender, _loanId))
    paidAmountInterest: uint256 = _amountPaid - paidAmount

    if _amountPaid == allowedPayment:
        self.ongoingLoans[msg.sender] -= 1
        
        ILoansCore(self.loansCoreAddress).updatePaidLoan(msg.sender, _loanId)

    ILoansCore(self.loansCoreAddress).updateLoanPaidAmount(msg.sender, _loanId, paidAmount + paidAmountInterest)
    ILoansCore(self.loansCoreAddress).updateHighestRepayment(msg.sender, _loanId)

    ILendingPoolPeripheral(self.lendingPoolAddress).receiveFunds(msg.sender, paidAmount, paidAmountInterest)

    if _amountPaid == allowedPayment:
        collaterals: DynArray[Collateral, 100] = ILoansCore(self.loansCoreAddress).getLoanCollaterals(msg.sender, _loanId)
        for collateral in collaterals:
            ILoansCore(self.loansCoreAddress).removeCollateralFromLoan(msg.sender, collateral, _loanId)
            ILoansCore(self.loansCoreAddress).updateCollaterals(collateral, True)
            
            IERC721(collateral.contractAddress).safeTransferFrom(self, msg.sender, collateral.tokenId, b"")

        log LoanPaid(msg.sender, _loanId, ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract())

    log LoanPayment(msg.sender, _loanId, _amountPaid, ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract())


@external
def settleDefault(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "Only the contract owner can default loans"
    assert ILoansCore(self.loansCoreAddress).isLoanStarted(_borrower, _loanId), "The _borrower has not started a loan with the given ID"
    assert block.timestamp > ILoansCore(self.loansCoreAddress).getLoanMaturity(_borrower, _loanId), "The maturity of the loan has not been reached yet"

    self.ongoingLoans[_borrower] -= 1

    ILoansCore(self.loansCoreAddress).updateDefaultedLoan(_borrower, _loanId)
    ILoansCore(self.loansCoreAddress).updateHighestDefaultedLoan(_borrower, _loanId)

    collaterals: DynArray[Collateral, 100] = ILoansCore(self.loansCoreAddress).getLoanCollaterals(_borrower, _loanId)
    for collateral in collaterals:
        ILoansCore(self.loansCoreAddress).removeCollateralFromLoan(_borrower, collateral, _loanId)
        ILoansCore(self.loansCoreAddress).updateCollaterals(collateral, True)

        IERC721(collateral.contractAddress).safeTransferFrom(self, self.owner, collateral.tokenId, b"")

    log LoanDefaulted(
        _borrower,
        _loanId,
        ILoansCore(self.loansCoreAddress).getLoanAmount(_borrower, _loanId),
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@external
def cancelPendingLoan(_loanId: uint256):
    assert ILoansCore(self.loansCoreAddress).isLoanCreated(msg.sender, _loanId), "The sender has not created a loan with the given ID"
    assert not ILoansCore(self.loansCoreAddress).isLoanStarted(msg.sender, _loanId), "The loan was already started"
    assert not ILoansCore(self.loansCoreAddress).getLoanInvalidated(msg.sender, _loanId), "The loan was already invalidated"

    self.ongoingLoans[msg.sender] -= 1

    ILoansCore(self.loansCoreAddress).updateCanceledLoan(msg.sender, _loanId)

    collaterals: DynArray[Collateral, 100] = ILoansCore(self.loansCoreAddress).getLoanCollaterals(msg.sender, _loanId)
    for collateral in collaterals:
        ILoansCore(self.loansCoreAddress).removeCollateralFromLoan(msg.sender, collateral, _loanId)
        ILoansCore(self.loansCoreAddress).updateCollaterals(collateral, True)

        IERC721(collateral.contractAddress).safeTransferFrom(self, msg.sender, collateral.tokenId, b"")

    log PendingLoanCanceled(msg.sender, _loanId, ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract())


@external
@payable
def __default__():
    if msg.value > 0:
        send(msg.sender, msg.value)
