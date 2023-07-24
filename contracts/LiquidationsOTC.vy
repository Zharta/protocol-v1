# @version 0.3.9

"""
@title LiquidationsOTC
@author [Zharta](https://zharta.io/)
@notice The liquidations peripheral contract exists as the main interface to handle liquidations
"""


# Interfaces

from vyper.interfaces import ERC20 as IERC20
from vyper.interfaces import ERC721 as IERC721

interface ILoans:
    def getLoan(_borrower: address, _loanId: uint256) -> Loan: view
    def erc20TokenContract() -> address: view


interface ILendingPool:
    def lenderFunds(_lender: address) -> InvestorFunds: view
    def erc20TokenContract() -> address: view
    def receiveFundsFromLiquidation(
        _borrower: address,
        _amount: uint256,
        _rewardsAmount: uint256,
        _distributeToProtocol: bool,
        _origin: String[30]
    ): nonpayable
    def receiveFundsFromLiquidationEth(
        _borrower: address,
        _amount: uint256,
        _rewardsAmount: uint256,
        _distributeToProtocol: bool,
        _origin: String[30]
    ): payable
    def receiveCollateralFromLiquidation(
        _borrower: address,
        _amount: uint256,
        _origin: String[30]
    ): nonpayable


interface ICollateralVault:
    def transferCollateralFromLiquidation(_wallet: address, _collateralAddress: address, _tokenId: uint256): nonpayable


interface ISelf:
    def initialize(_owner: address, _gracePeriodDuration: uint256): nonpayable



# Structs


struct Collateral:
    contractAddress: address
    tokenId: uint256
    amount: uint256

struct Loan:
    id: uint256
    amount: uint256
    interest: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    maturity: uint256
    startTime: uint256
    collaterals: DynArray[Collateral, 100]
    paidPrincipal: uint256
    paidInterestAmount: uint256
    started: bool
    invalidated: bool
    paid: bool
    defaulted: bool
    canceled: bool

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool

struct Liquidation:
    lid: bytes32
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    gracePeriodPrice: uint256
    borrower: address
    loanId: uint256
    loansCoreContract: address
    erc20TokenContract: address


# Events

event OwnershipTransferred:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address

event OwnerProposed:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address

event AdminTransferred:
    adminIndexed: indexed(address)
    newAdminIndexed: indexed(address)
    newAdmin: address

event GracePeriodDurationChanged:
    currentValue: uint256
    newValue: uint256

event LoansAddressSet:
    currentValue: address
    newValue: address

event LendingPoolAddressSet:
    currentValue: address
    newValue: address

event CollateralVaultAddressSet:
    currentValue: address
    newValue: address

event LiquidationAdded:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address
    gracePeriodPrice: uint256
    lenderPeriodPrice: uint256
    gracePeriodMaturity: uint256
    lenderPeriodMaturity: uint256
    loansCoreContract: address
    loanId: uint256
    borrower: address

event LiquidationRemoved:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address
    loansCoreContract: address
    loanId: uint256
    borrower: address

event NFTPurchased:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    buyerAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    amount: uint256
    buyerAddress: address
    erc20TokenContract: address
    loansCoreContract: address
    method: String[30] # possible values: GRACE_PERIOD, LENDER_PERIOD, BACKSTOP_PERIOD_NFTX, BACKSTOP_PERIOD_ADMIN

event NFTClaimed:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    buyerAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    amount: uint256
    buyerAddress: address
    erc20TokenContract: address
    loansCoreContract: address
    method: String[30] # possible values: GRACE_PERIOD, LENDER_PERIOD, BACKSTOP_PERIOD_NFTX, BACKSTOP_PERIOD_ADMIN

event PaymentSent:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256

event PaymentReceived:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256


# Global variables

owner: public(address)
proposedOwner: public(address)

gracePeriodDuration: public(uint256)

liquidations: HashMap[bytes32, Liquidation]
liquidatedLoans: HashMap[bytes32, bool]

loansContract: public(ILoans)
lendingPoolContract: public(ILendingPool)
collateralVaultContract: public(ICollateralVault)

wethAddress: immutable(address)

##### INTERNAL METHODS - VIEW #####

@pure
@internal
def _computeLiquidationId(_collateralAddress: address, _collateralId: uint256, _timestamp: uint256) -> bytes32:
    return keccak256(_abi_encode(_collateralAddress, convert(_collateralId, bytes32), convert(_timestamp, bytes32)))


@pure
@internal
def _computeLiquidationKey(_collateralAddress: address, _collateralId: uint256) -> bytes32:
    return keccak256(_abi_encode(_collateralAddress, convert(_collateralId, bytes32)))


@pure
@internal
def _computeLiquidatedLoansKey(_borrower: address, _loansCoreContract: address, _loanId: uint256) -> bytes32:
    return keccak256(_abi_encode(_borrower, _loansCoreContract, convert(_loanId, bytes32)))


@view
@internal
def _isLoanLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256) -> bool:
    return self.liquidatedLoans[self._computeLiquidatedLoansKey(_borrower, _loansCoreContract, _loanId)]


@view
@internal
def _getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)]


@pure
@internal
def _penaltyFee(_principal: uint256) -> uint256:
    return min(250 * _principal / 10000, as_wei_value(0.2, "ether"))


@pure
@internal
def _computeNFTPrice(principal: uint256, interestAmount: uint256) -> uint256:
    return principal + interestAmount + self._penaltyFee(principal)


@pure
@internal
def _computeLoanInterestAmount(principal: uint256, interest: uint256, duration: uint256) -> uint256:
    return principal * interest * duration / 25920000000 # 25920000000 = 30 days * 10000 base percentage points



##### INTERNAL METHODS - WRITE #####

@internal
def _addLiquidation(
    _collateralAddress: address,
    _tokenId: uint256,
    _startTime: uint256,
    _gracePeriodMaturity: uint256,
    _lenderPeriodMaturity: uint256,
    _principal: uint256,
    _interestAmount: uint256,
    _apr: uint256,
    _gracePeriodPrice: uint256,
    _lenderPeriodPrice: uint256,
    _borrower: address,
    _loanId: uint256,
    _loansCoreContract: address,
    _erc20TokenContract: address
) -> bytes32:
    liquidationKey: bytes32 = self._computeLiquidationKey(_collateralAddress, _tokenId)
    assert self.liquidations[liquidationKey].startTime == 0, "liquidation already exists"
    assert not self.liquidatedLoans[self._computeLiquidatedLoansKey(_borrower, _loansCoreContract, _loanId)], "loan already liquidated"

    lid: bytes32 = self._computeLiquidationId(_collateralAddress, _tokenId, block.timestamp)
    self.liquidations[liquidationKey] = Liquidation(
        {
            lid: lid,
            collateralAddress: _collateralAddress,
            tokenId: _tokenId,
            startTime: _startTime,
            gracePeriodMaturity: _gracePeriodMaturity,
            principal: _principal,
            interestAmount: _interestAmount,
            apr: _apr,
            gracePeriodPrice: _gracePeriodPrice,
            borrower: _borrower,
            loanId: _loanId,
            loansCoreContract: _loansCoreContract,
            erc20TokenContract: _erc20TokenContract,
        }
    )
    return lid


@internal
def _addLoanToLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256):
    self.liquidatedLoans[self._computeLiquidatedLoansKey(_borrower, _loansCoreContract, _loanId)] = True


@internal
def _removeLiquidation(_collateralAddress: address, _tokenId: uint256):
    liquidationKey: bytes32 = self._computeLiquidationKey(_collateralAddress, _tokenId)
    assert self.liquidations[liquidationKey].startTime > 0, "liquidation not found"
    self.liquidations[liquidationKey] = empty(Liquidation)


##### EXTERNAL METHODS - VIEW #####


@view
@external
def liquidationsCoreAddress() -> address:
    return self


@view
@external
def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)]


@view
@external
def getLiquidationStartTime(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].startTime

@view
@external
def getLiquidationGracePeriodMaturity(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].gracePeriodMaturity

@view
@external
def getLiquidationPrincipal(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].principal

@view
@external
def getLiquidationInterestAmount(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].interestAmount

@view
@external
def getLiquidationAPR(_collateralAddress: address, _tokenId: uint256) -> uint256:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].apr

@view
@external
def getLiquidationBorrower(_collateralAddress: address, _tokenId: uint256) -> address:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].borrower

@view
@external
def getLiquidationERC20Contract(_collateralAddress: address, _tokenId: uint256) -> address:
    return self.liquidations[self._computeLiquidationKey(_collateralAddress, _tokenId)].erc20TokenContract

@view
@external
def isLoanLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256) -> bool:
    return self._isLoanLiquidated(_borrower, _loansCoreContract, _loanId)


##### EXTERNAL METHODS - WRITE #####
@external
def __init__(_wethAddress: address):
    assert _wethAddress != empty(address)  # reason: address is the zero address

    self.owner = msg.sender
    wethAddress = _wethAddress


@external
def initialize(_owner: address, _gracePeriodDuration: uint256):
    assert _owner != empty(address), "owner is the zero address"
    assert self.owner == empty(address), "already initialized"
    assert _gracePeriodDuration > 0  # reason: duration is 0

    self.owner = _owner
    self.gracePeriodDuration = _gracePeriodDuration


@external
def create_proxy(_gracePeriodDuration: uint256) -> address:
    proxy: address = create_minimal_proxy_to(self)
    ISelf(proxy).initialize(msg.sender, _gracePeriodDuration)
    return proxy


@external
def proposeOwner(_address: address):
    assert msg.sender == self.owner  # reason: msg.sender is not the owner
    assert _address != empty(address)  # reason: address it the zero address

    self.proposedOwner = _address

    log OwnerProposed(
        self.owner,
        _address,
        self.owner,
        _address,
    )


@external
def claimOwnership():
    assert msg.sender == self.proposedOwner  # reason: msg.sender is not the proposed

    log OwnershipTransferred(
        self.owner,
        self.proposedOwner,
        self.owner,
        self.proposedOwner,
    )

    self.owner = self.proposedOwner
    self.proposedOwner = empty(address)


@external
def setGracePeriodDuration(_duration: uint256):
    assert msg.sender == self.owner  # reason: msg.sender is not the owner
    assert _duration > 0  # reason: duration is 0

    log GracePeriodDurationChanged(
        self.gracePeriodDuration,
        _duration
    )

    self.gracePeriodDuration = _duration


@external
def setLoansContract(_address: address):
    assert msg.sender == self.owner  #reason: msg.sender is not the owner
    assert _address != empty(address)  # reason: address is the zero addr

    log LoansAddressSet(self.loansContract.address, _address)

    self.loansContract = ILoans(_address)


@external
def setLendingPoolContract(_address: address):
    assert msg.sender == self.owner  # reason: msg.sender is not the owner
    assert _address != empty(address)  # reason: address is the zero addr

    log LendingPoolAddressSet(self.lendingPoolContract.address, _address)

    self.lendingPoolContract = ILendingPool(_address)


@external
def setCollateralVaultPeripheralAddress(_address: address):
    assert msg.sender == self.owner  # reason: msg.sender is not the owner
    assert _address != empty(address)  # reason: address is the zero addr

    log CollateralVaultAddressSet(self.collateralVaultContract.address, _address)

    self.collateralVaultContract = ICollateralVault(_address)



@external
def addLiquidation(_borrower: address, _loanId: uint256, _erc20TokenContract: address):

    borrowerLoan: Loan = self.loansContract.getLoan(_borrower, _loanId)
    assert borrowerLoan.defaulted, "loan is not defaulted"
    assert not self._isLoanLiquidated(_borrower, self.loansContract.address, _loanId), "loan already liquidated"

    # APR from loan duration (maturity)
    loanAPR: uint256 = borrowerLoan.interest * 12

    for collateral in borrowerLoan.collaterals:
        assert self._getLiquidation(collateral.contractAddress, collateral.tokenId).startTime == 0, "liquidation already exists"

        principal: uint256 = collateral.amount
        interestAmount: uint256 = self._computeLoanInterestAmount(
            principal,
            borrowerLoan.interest,
            borrowerLoan.maturity - borrowerLoan.startTime
        )

        gracePeriodPrice: uint256 = self._computeNFTPrice(principal, interestAmount)

        lid: bytes32 = self._addLiquidation(
            collateral.contractAddress,
            collateral.tokenId,
            block.timestamp,
            block.timestamp + self.gracePeriodDuration,
            block.timestamp + self.gracePeriodDuration,
            principal,
            interestAmount,
            loanAPR,
            gracePeriodPrice,
            gracePeriodPrice,
            _borrower,
            _loanId,
            self.loansContract.address,
            _erc20TokenContract
        )

        log LiquidationAdded(
            _erc20TokenContract,
            collateral.contractAddress,
            lid,
            collateral.contractAddress,
            collateral.tokenId,
            _erc20TokenContract,
            gracePeriodPrice,
            gracePeriodPrice,
            block.timestamp + self.gracePeriodDuration,
            block.timestamp + self.gracePeriodDuration,
            self.loansContract.address,
            _loanId,
            _borrower
        )

    self._addLoanToLiquidated(_borrower, self.loansContract.address, _loanId)


@payable
@external
def payLoanLiquidationsGracePeriod(_loanId: uint256, _erc20TokenContract: address):
    receivedAmount: uint256 = msg.value
    ethPayment: bool = receivedAmount > 0

    loan: Loan = self.loansContract.getLoan(msg.sender, _loanId)
    assert loan.defaulted, "loan is not defaulted"

    if ethPayment:
        log PaymentReceived(msg.sender, msg.sender, receivedAmount)
    paidAmount: uint256 = 0

    for collateral in loan.collaterals:
        liquidation: Liquidation = self._getLiquidation(collateral.contractAddress, collateral.tokenId)

        assert block.timestamp <= liquidation.gracePeriodMaturity, "liquidation out of grace period"
        assert not ethPayment or receivedAmount >= paidAmount + liquidation.gracePeriodPrice, "insufficient value received"

        self._removeLiquidation(collateral.contractAddress, collateral.tokenId)

        log LiquidationRemoved(
            liquidation.erc20TokenContract,
            liquidation.collateralAddress,
            liquidation.lid,
            liquidation.collateralAddress,
            liquidation.tokenId,
            liquidation.erc20TokenContract,
            liquidation.loansCoreContract,
            liquidation.loanId,
            liquidation.borrower
        )

        _lendingPoolPeripheral : address = self.lendingPoolContract.address

        if ethPayment:
            self.lendingPoolContract.receiveFundsFromLiquidationEth(
                liquidation.borrower,
                liquidation.principal,
                liquidation.gracePeriodPrice - liquidation.principal,
                True,
                "liquidation_grace_period",
                value=liquidation.gracePeriodPrice
            )
            log PaymentSent(_lendingPoolPeripheral, _lendingPoolPeripheral, liquidation.gracePeriodPrice)
            paidAmount += liquidation.gracePeriodPrice

        else:
            self.lendingPoolContract.receiveFundsFromLiquidation(
                liquidation.borrower,
                liquidation.principal,
                liquidation.gracePeriodPrice - liquidation.principal,
                True,
                "liquidation_grace_period"
            )


        self.collateralVaultContract.transferCollateralFromLiquidation(
            msg.sender,
            collateral.contractAddress,
            collateral.tokenId
        )

        log NFTPurchased(
            liquidation.erc20TokenContract,
            collateral.contractAddress,
            msg.sender,
            liquidation.lid,
            collateral.contractAddress,
            collateral.tokenId,
            liquidation.gracePeriodPrice,
            msg.sender,
            liquidation.erc20TokenContract,
            liquidation.loansCoreContract,
            "GRACE_PERIOD"
        )

    excessAmount: uint256 = receivedAmount - paidAmount
    if excessAmount > 0:
        send(msg.sender, excessAmount)
        log PaymentSent(msg.sender, msg.sender,excessAmount)


@external
def claim(_collateralAddress: address, _tokenId: uint256):
    liquidation: Liquidation = self._getLiquidation(_collateralAddress, _tokenId)
    assert block.timestamp > liquidation.gracePeriodMaturity, "liquidation in grace period"

    assert self.lendingPoolContract.address != empty(address), "lendingPool not configured"
    assert self.lendingPoolContract.lenderFunds(msg.sender).currentAmountDeposited > 0, "msg.sender is not a lender"


    self._removeLiquidation(_collateralAddress, _tokenId)

    log LiquidationRemoved(
        liquidation.erc20TokenContract,
        liquidation.collateralAddress,
        liquidation.lid,
        liquidation.collateralAddress,
        liquidation.tokenId,
        liquidation.erc20TokenContract,
        liquidation.loansCoreContract,
        liquidation.loanId,
        liquidation.borrower
    )

    self.collateralVaultContract.transferCollateralFromLiquidation(msg.sender, _collateralAddress, _tokenId)

    log NFTClaimed(
        liquidation.erc20TokenContract,
        _collateralAddress,
        msg.sender,
        liquidation.lid,
        _collateralAddress,
        _tokenId,
        liquidation.gracePeriodPrice,
        msg.sender,
        liquidation.erc20TokenContract,
        liquidation.loansCoreContract,
        "OTC_CLAIM"
    )

    self.lendingPoolContract.receiveCollateralFromLiquidation(
        liquidation.borrower,
        liquidation.principal,
        "OTC_CLAIM"
    )

