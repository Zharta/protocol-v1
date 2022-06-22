# @version ^0.3.3


# Interfaces

from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721
from vyper.interfaces import ERC20 as IERC20
from interfaces import ILoansCore
from interfaces import ILendingPoolPeripheral

interface IERC20Symbol:
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

event OwnershipTransferred:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event OwnerProposed:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event MaxAllowedLoansChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event MaxLoansChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event MaxLoanDurationChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event MinLoanAmountChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event MaxLoanAmountChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event CollateralToWhitelistAdded:
    erc20TokenContractIndexed: indexed(address)
    value: address
    erc20TokenContract: address

event CollateralToWhitelistRemoved:
    erc20TokenContractIndexed: indexed(address)
    value: address
    erc20TokenContract: address

event LendingPoolPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event ContractStatusChanged:
    erc20TokenContractIndexed: indexed(address)
    value: bool
    erc20TokenContract: address

event ContractDeprecated:
    erc20TokenContractIndexed: indexed(address)
    erc20TokenContract: address

event LoanCreated:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanValidated:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanInvalidated:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanPayment:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    amount: uint256
    erc20TokenContract: address

event LoanPaid:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanDefaulted:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    amount: uint256
    erc20TokenContract: address

event PendingLoanCanceled:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    erc20TokenContract: address


# Global variables

owner: public(address)
proposedOwner: public(address)

maxAllowedLoans: public(uint256)
maxAllowedLoanDuration: public(uint256)
minLoanAmount: public(uint256)
maxLoanAmount: public(uint256)

ongoingLoans: public(HashMap[address, uint256])

isAcceptingLoans: public(bool)
isDeprecated: public(bool)

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
    assert _maxAllowedLoans > 0, "value for max loans is 0"
    assert _maxAllowedLoanDuration > 0, "valor for max duration is 0"
    assert _maxLoanAmount >= _minLoanAmount, "max amount is < than min amount"
    assert _loansCoreAddress != ZERO_ADDRESS, "address is the zero address"
    assert _lendingPoolAddress != ZERO_ADDRESS, "address is the zero address"
    assert _lendingPoolCoreAddress != ZERO_ADDRESS, "address is the zero address"

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
def proposeOwner(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "_address it the zero address"
    assert self.owner != _address, "proposed owner addr is the owner"
    assert self.proposedOwner != _address, "proposed owner addr is the same"

    self.proposedOwner = _address

    log OwnerProposed(
        self.owner,
        self.proposedOwner,
        self.owner,
        self.proposedOwner,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@external
def claimOwnership():
    assert msg.sender == self.proposedOwner, "msg.sender is not the proposed"

    log OwnershipTransferred(
        self.owner,
        self.proposedOwner,
        self.owner,
        self.proposedOwner,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )

    self.owner = self.proposedOwner
    self.proposedOwner = ZERO_ADDRESS


@external
def changeMaxAllowedLoans(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value > 0, "value for max loans is 0"
    assert _value != self.maxAllowedLoans, "new max loans value is the same"

    log MaxLoansChanged(
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract(),
        self.maxAllowedLoans,
        _value,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )

    self.maxAllowedLoans = _value


@external
def changeMaxAllowedLoanDuration(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value > 0, "value for max duration is 0"
    assert _value != self.maxAllowedLoanDuration, "new max duration value is the same"

    log MaxLoanDurationChanged(
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract(),
        self.maxAllowedLoanDuration,
        _value,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )

    self.maxAllowedLoanDuration = _value


@external
def changeMinLoanAmount(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value != self.minLoanAmount, "new min loan amount is the same"
    assert _value <= self.maxLoanAmount, "min amount is > than max amount"
    
    log MinLoanAmountChanged(
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract(),
        self.minLoanAmount,
        _value,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )

    self.minLoanAmount = _value


@external
def changeMaxLoanAmount(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value != self.maxLoanAmount, "new max loan amount is the same"
    assert _value >= self.minLoanAmount, "max amount is < than min amount"

    log MaxLoanAmountChanged(
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract(),
        self.maxLoanAmount,
        _value,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )

    self.maxLoanAmount = _value


@external
def addCollateralToWhitelist(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    # No method yet to get the interface_id, so explicitly checking the ERC721 interface_id
    assert IERC165(_address).supportsInterface(0x80ac58cd), "_address is not a ERC721"

    self.whitelistedCollaterals[_address] = True

    log CollateralToWhitelistAdded(
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract(),
        _address,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@external
def removeCollateralFromWhitelist(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.whitelistedCollaterals[_address], "collateral is not whitelisted"

    self.whitelistedCollaterals[_address] = False

    log CollateralToWhitelistRemoved(
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract(),
        _address,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@external
def setLendingPoolPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert self.lendingPoolAddress != _address, "new LPPeriph addr is the same"

    log LendingPoolPeripheralAddressSet(
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract(),
        self.lendingPoolAddress,
        _address,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )

    self.lendingPoolAddress = _address


@external
def changeContractStatus(_flag: bool):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.isAcceptingLoans != _flag, "new contract status is the same"

    self.isAcceptingLoans = _flag

    log ContractStatusChanged(
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract(),
        _flag,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@external
def deprecate():
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert not self.isDeprecated, "contract is already deprecated"

    self.isDeprecated = True
    self.isAcceptingLoans = False

    log ContractDeprecated(
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract(),
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@view
@external
def erc20TokenSymbol() -> String[100]:
    return IERC20Symbol(ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()).symbol()


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
    assert not self.isDeprecated, "contract is deprecated"
    assert self.isAcceptingLoans, "contract is not accepting loans"
    assert block.timestamp <= _maturity, "maturity is in the past"
    assert _maturity - block.timestamp <= self.maxAllowedLoanDuration, "maturity exceeds the max allowed"
    assert self._areCollateralsWhitelisted(_collaterals), "not all NFTs are accepted"
    assert self._areCollateralsOwned(msg.sender, _collaterals), "msg.sender does not own all NFTs"
    assert self._areCollateralsApproved(msg.sender, _collaterals) == True, "not all NFTs are approved"
    assert ILendingPoolPeripheral(self.lendingPoolAddress).maxFundsInvestable() >= _amount, "insufficient liquidity"
    assert self.ongoingLoans[msg.sender] < self.maxAllowedLoans, "max loans already reached"
    assert _amount >= self.minLoanAmount, "loan amount < than the min value"
    assert _amount <= self.maxLoanAmount, "loan amount > than the max value"

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

    log LoanCreated(
        msg.sender,
        msg.sender,
        newLoanId,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )

    return newLoanId


@external
def validate(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert not self.isDeprecated, "contract is deprecated"
    assert self.isAcceptingLoans, "contract is not accepting loans"
    assert ILoansCore(self.loansCoreAddress).isLoanCreated(_borrower, _loanId), "loan not found"
    assert not ILoansCore(self.loansCoreAddress).isLoanStarted(_borrower, _loanId), "loan already validated"
    assert not ILoansCore(self.loansCoreAddress).getLoanInvalidated(_borrower, _loanId), "loan already invalidated"
    assert block.timestamp <= ILoansCore(self.loansCoreAddress).getLoanMaturity(_borrower, _loanId), "maturity is in the past"
    assert self._areCollateralsWhitelisted(ILoansCore(self.loansCoreAddress).getLoanCollaterals(_borrower, _loanId)), "not all NFTs are accepted"
    assert ILendingPoolPeripheral(self.lendingPoolAddress).maxFundsInvestable() >= ILoansCore(self.loansCoreAddress).getLoanAmount(_borrower, _loanId), "insufficient liquidity"

    ILoansCore(self.loansCoreAddress).updateLoanStarted(_borrower, _loanId)
    ILoansCore(self.loansCoreAddress).updateHighestSingleCollateralLoan(_borrower, _loanId)
    ILoansCore(self.loansCoreAddress).updateHighestCollateralBundleLoan(_borrower, _loanId)

    ILendingPoolPeripheral(self.lendingPoolAddress).sendFunds(_borrower, ILoansCore(self.loansCoreAddress).getLoanAmount(_borrower, _loanId))

    log LoanValidated(
        _borrower,
        _borrower,
        _loanId,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@external
def invalidate(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert ILoansCore(self.loansCoreAddress).isLoanCreated(_borrower, _loanId), "loan not found"
    assert not ILoansCore(self.loansCoreAddress).isLoanStarted(_borrower, _loanId), "loan already validated"
    assert not ILoansCore(self.loansCoreAddress).getLoanInvalidated(_borrower, _loanId), "loan already invalidated"

    self.ongoingLoans[_borrower] -= 1
    
    ILoansCore(self.loansCoreAddress).updateInvalidLoan(_borrower, _loanId)

    collaterals: DynArray[Collateral, 100] = ILoansCore(self.loansCoreAddress).getLoanCollaterals(_borrower, _loanId)
    for collateral in collaterals:
        ILoansCore(self.loansCoreAddress).removeCollateralFromLoan(_borrower, collateral, _loanId)
        ILoansCore(self.loansCoreAddress).updateCollaterals(collateral, True)

        IERC721(collateral.contractAddress).safeTransferFrom(self, _borrower, collateral.tokenId, b"")

    log LoanInvalidated(
        _borrower,
        _borrower,
        _loanId,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@external
def pay(_loanId: uint256, _amount: uint256):
    assert ILoansCore(self.loansCoreAddress).isLoanStarted(msg.sender, _loanId), "loan not found"
    assert block.timestamp <= ILoansCore(self.loansCoreAddress).getLoanMaturity(msg.sender, _loanId), "loan maturity reached"
    assert _amount > 0, "_amount has to be higher than 0"
    assert IERC20(ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()).balanceOf(msg.sender) >=_amount, "insufficient balance"
    assert IERC20(ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()).allowance(msg.sender, self.lendingPoolCoreAddress) >= _amount, "insufficient allowance"

    maxPayment: uint256 = ILoansCore(self.loansCoreAddress).getLoanAmount(msg.sender, _loanId) * (10000 + ILoansCore(self.loansCoreAddress).getLoanInterest(msg.sender, _loanId)) / 10000
    allowedPayment: uint256 = maxPayment - ILoansCore(self.loansCoreAddress).getLoanPaidAmount(msg.sender, _loanId)
    assert _amount <= allowedPayment, "_amount is more than needed"

    paidAmount: uint256 = _amount * 10000 / (10000 + ILoansCore(self.loansCoreAddress).getLoanInterest(msg.sender, _loanId))
    paidAmountInterest: uint256 = _amount - paidAmount

    if _amount == allowedPayment:
        self.ongoingLoans[msg.sender] -= 1
        
        ILoansCore(self.loansCoreAddress).updatePaidLoan(msg.sender, _loanId)

    ILoansCore(self.loansCoreAddress).updateLoanPaidAmount(msg.sender, _loanId, paidAmount + paidAmountInterest)
    ILoansCore(self.loansCoreAddress).updateHighestRepayment(msg.sender, _loanId)

    ILendingPoolPeripheral(self.lendingPoolAddress).receiveFunds(msg.sender, paidAmount, paidAmountInterest)

    if _amount == allowedPayment:
        collaterals: DynArray[Collateral, 100] = ILoansCore(self.loansCoreAddress).getLoanCollaterals(msg.sender, _loanId)
        for collateral in collaterals:
            ILoansCore(self.loansCoreAddress).removeCollateralFromLoan(msg.sender, collateral, _loanId)
            ILoansCore(self.loansCoreAddress).updateCollaterals(collateral, True)
            
            IERC721(collateral.contractAddress).safeTransferFrom(self, msg.sender, collateral.tokenId, b"")

        log LoanPaid(
            msg.sender,
            msg.sender,
            _loanId,
            ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
        )

    log LoanPayment(
        msg.sender,
        msg.sender,
        _loanId,
        _amount,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@external
def settleDefault(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert ILoansCore(self.loansCoreAddress).isLoanStarted(_borrower, _loanId), "loan not found"
    assert block.timestamp > ILoansCore(self.loansCoreAddress).getLoanMaturity(_borrower, _loanId), "loan is within maturity period"

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
        _borrower,
        _loanId,
        ILoansCore(self.loansCoreAddress).getLoanAmount(_borrower, _loanId),
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )


@external
def cancelPendingLoan(_loanId: uint256):
    assert ILoansCore(self.loansCoreAddress).isLoanCreated(msg.sender, _loanId), "loan not found"
    assert not ILoansCore(self.loansCoreAddress).isLoanStarted(msg.sender, _loanId), "loan already validated"
    assert not ILoansCore(self.loansCoreAddress).getLoanInvalidated(msg.sender, _loanId), "loan already invalidated"

    self.ongoingLoans[msg.sender] -= 1

    ILoansCore(self.loansCoreAddress).updateCanceledLoan(msg.sender, _loanId)

    collaterals: DynArray[Collateral, 100] = ILoansCore(self.loansCoreAddress).getLoanCollaterals(msg.sender, _loanId)
    for collateral in collaterals:
        ILoansCore(self.loansCoreAddress).removeCollateralFromLoan(msg.sender, collateral, _loanId)
        ILoansCore(self.loansCoreAddress).updateCollaterals(collateral, True)

        IERC721(collateral.contractAddress).safeTransferFrom(self, msg.sender, collateral.tokenId, b"")

    log PendingLoanCanceled(
        msg.sender,
        msg.sender,
        _loanId,
        ILendingPoolPeripheral(self.lendingPoolAddress).erc20TokenContract()
    )
