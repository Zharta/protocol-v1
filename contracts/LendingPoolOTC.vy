# @version 0.3.9

"""
@title LendingPoolPeripheralOTC
@author [Zharta](https://zharta.io/)
@notice The lending pool contract implements the lending pool logic. Each instance works with a corresponding loans contract to implement an isolated lending market.
@dev Uses a `LendingPoolCore` contract to store state
"""

# Interfaces

from vyper.interfaces import ERC20 as IERC20

interface IWETH:
    def deposit(): payable
    def withdraw(_amount: uint256): nonpayable


# Structs

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool

# Events

event OwnerProposed:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event OwnershipTransferred:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event MaxCapitalEfficiencyChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event ProtocolWalletChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event ProtocolFeesShareChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event LoansPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LiquidationsPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event WhitelistStatusChanged:
    erc20TokenContractIndexed: indexed(address)
    value: bool
    erc20TokenContract: address

event WhitelistAddressAdded:
    erc20TokenContractIndexed: indexed(address)
    value: address
    erc20TokenContract: address

event WhitelistAddressRemoved:
    erc20TokenContractIndexed: indexed(address)
    value: address
    erc20TokenContract: address

event ContractStatusChanged:
    erc20TokenContractIndexed: indexed(address)
    value: bool
    erc20TokenContract: address

event ContractDeprecated:
    erc20TokenContractIndexed: indexed(address)
    erc20TokenContract: address

event Deposit:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256
    erc20TokenContract: address

event Withdrawal:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256
    erc20TokenContract: address

event FundsTransfer:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256
    erc20TokenContract: address

event FundsReceipt:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256
    rewardsPool: uint256
    rewardsProtocol: uint256
    investedAmount: uint256
    erc20TokenContract: address
    fundsOrigin: String[30]

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

loansContract: public(address)
lendingPoolCoreContract: public(address)
erc20TokenContract: public(immutable(address))
liquidationsPeripheralContract: public(address)

protocolWallet: public(address)
protocolFeesShare: public(uint256) # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000

isPoolActive: public(bool)
isPoolDeprecated: public(bool)


# core

funds: InvestorFunds
lender: address

fundsAvailable: public(uint256)
fundsInvested: public(uint256)
totalFundsInvested: public(uint256)
totalRewards: public(uint256)
totalSharesBasisPoints: public(uint256)


##### INTERNAL METHODS - VIEW #####

@view
@internal
def _fundsAreAllowed(_owner: address, _spender: address, _amount: uint256) -> bool:
    amountAllowed: uint256 = IERC20(erc20TokenContract).allowance(_owner, _spender)
    return _amount <= amountAllowed


@view
@internal
def _poolHasFundsToInvestAfterDeposit(_amount: uint256) -> bool:
    return self.fundsAvailable + _amount > 0


@view
@internal
def _poolHasFundsToInvestAfterPayment(_amount: uint256, _rewards: uint256) -> bool:
    return self.fundsAvailable + _amount + _rewards> 0


@view
@internal
def _poolHasFundsToInvestAfterWithdraw(_amount: uint256) -> bool:
    return self.fundsAvailable > _amount


@view
@internal
def _poolHasFundsToInvestAfterInvestment(_amount: uint256) -> bool:
    return self.fundsAvailable > _amount


@view
@internal
def _computeWithdrawableAmount() -> uint256:
    return self.fundsAvailable + self.fundsInvested


##### INTERNAL METHODS - WRITE #####


@internal
def _deposit(_amount: uint256, _payer: address):
    assert msg.sender == self.lender, "msg.sender is not the lender"
    assert not self.isPoolDeprecated, "pool is deprecated, withdraw"
    assert self.isPoolActive, "pool is not active right now"
    assert _amount > 0, "_amount has to be higher than 0"
    assert _payer != empty(address), "The _payer is the zero address"

    assert self._fundsAreAllowed(_payer, self, _amount), "Not enough funds allowed"

    self.funds.totalAmountDeposited += _amount
    self.funds.currentAmountDeposited += _amount
    if not self.funds.activeForRewards:
        self.funds.activeForRewards = True

    
    self.fundsAvailable += _amount

    if not IERC20(erc20TokenContract).transferFrom(_payer, self, _amount):
        raise "error creating deposit"

    log Deposit(msg.sender, msg.sender, _amount, erc20TokenContract)


@internal
def _withdraw(_amount: uint256, _receiver: address):
    assert _amount > 0, "_amount has to be higher than 0"
    assert _receiver != empty(address), "The receiver is the zero addr"
    assert msg.sender == self.lender, "The sender is not the lender"
    
    withdrawable: uint256 = self._computeWithdrawableAmount()
    assert withdrawable >= _amount, "_amount more than withdrawable"
    assert self.fundsAvailable >= _amount, "available funds less than amount"

    newDepositAmount: uint256 = withdrawable - _amount

    self.funds.currentAmountDeposited = newDepositAmount
    self.funds.totalAmountWithdrawn += _amount
    if newDepositAmount == 0:
        self.funds.activeForRewards = False

    self.fundsAvailable -= _amount

    if not IERC20(erc20TokenContract).transfer(_receiver, _amount):
        raise "error withdrawing funds"

    log Withdrawal(msg.sender, msg.sender, _amount, erc20TokenContract)


@internal
def _sendFunds(_to: address, _receiver: address, _amount: uint256):
    assert not self.isPoolDeprecated, "pool is deprecated"
    assert self.isPoolActive, "pool is inactive"
    assert msg.sender == self.lender, "msg.sender is not the lender"
    assert _to != empty(address), "_to is the zero address"
    assert _amount > 0, "_amount has to be higher than 0"
    assert _amount <= self.fundsAvailable, "insufficient liquidity"
    assert IERC20(erc20TokenContract).balanceOf(self) >= _amount, "Insufficient balance"

    self.fundsAvailable -= _amount
    self.fundsInvested += _amount
    self.totalFundsInvested += _amount

    if not IERC20(erc20TokenContract).transfer(_to, _amount):
        raise "error sending funds in LPOTC"

    log FundsTransfer(_to, _to, _amount, erc20TokenContract)


@internal
def _receiveFunds(_borrower: address, _payer: address, _amount: uint256, _rewardsAmount: uint256):
    assert msg.sender == self.loansContract, "msg.sender is not the loans addr"
    assert _borrower != empty(address), "_borrower is the zero address"
    assert _amount + _rewardsAmount > 0, "amount should be higher than 0"

    rewardsProtocol: uint256 = _rewardsAmount * self.protocolFeesShare / 10000
    rewardsPool: uint256 = _rewardsAmount - rewardsProtocol

    self._transferReceivedFunds(_borrower, _payer, _amount, rewardsPool, rewardsProtocol, _amount, "loan")


@internal
def _transferReceivedFunds(
    _borrower: address,
    _payer: address,
    _amount: uint256,
    _rewardsPool: uint256,
    _rewardsProtocol: uint256,
    _investedAmount: uint256,
    _origin: String[30]
):

    assert _payer != empty(address), "_borrower is the zero address"
    assert IERC20(erc20TokenContract).allowance(_payer, self) >= _amount + _rewardsPool + _rewardsProtocol, "insufficient value received"

    self.fundsAvailable += _amount + _rewardsPool
    self.fundsInvested -= _investedAmount
    self.totalRewards += _rewardsPool

    if not IERC20(erc20TokenContract).transferFrom(_payer, self, _amount + _rewardsPool):
        raise "error receiving funds in LPOTC"

    if _rewardsProtocol > 0:
        assert self.protocolWallet != empty(address), "protocolWallet is zero addr"
        if not IERC20(erc20TokenContract).transferFrom(_payer, self.protocolWallet, _rewardsProtocol):
            raise "error transferring protocol fees"

    log FundsReceipt(
        _borrower,
        _borrower,
        _amount,
        _rewardsPool,
        _rewardsProtocol,
        _investedAmount,
        erc20TokenContract,
        _origin
    )


@internal
def _receiveFundsFromLiquidation(
    _borrower: address,
    _payer: address,
    _amount: uint256,
    _rewardsAmount: uint256,
    _distributeToProtocol: bool,
    _investedAmount: uint256,
    _origin: String[30]
):
    assert msg.sender == self.liquidationsPeripheralContract, "msg.sender is not the BN addr"
    assert _borrower != empty(address), "_borrower is the zero address"
    assert _amount + _rewardsAmount > 0, "amount should be higher than 0"

    rewardsProtocol: uint256 = 0
    rewardsPool: uint256 = 0
    if _distributeToProtocol:
        rewardsProtocol = _rewardsAmount * self.protocolFeesShare / 10000
        rewardsPool = _rewardsAmount - rewardsProtocol
    else:
        rewardsPool = _rewardsAmount

    self._transferReceivedFunds(_borrower, _payer, _amount, rewardsPool, rewardsProtocol, _investedAmount, _origin)


@internal
def _unwrap_and_send(_to: address, _amount: uint256):
    IWETH(erc20TokenContract).withdraw(_amount)
    send(_to, _amount)
    log PaymentSent(_to, _to, _amount)


@internal
def _wrap_and_approve(_to: address, _amount: uint256):
    IWETH(erc20TokenContract).deposit(value=_amount)
    log PaymentSent(erc20TokenContract, erc20TokenContract, _amount)
    IERC20(erc20TokenContract).approve(_to, _amount)


##### EXTERNAL METHODS - VIEW #####

@view
@external
def maxFundsInvestable() -> uint256:
    return self.fundsAvailable


@view
@external
def theoreticalMaxFundsInvestable() -> uint256:
    return self.fundsAvailable + self.fundsInvested


@view
@external
def theoreticalMaxFundsInvestableAfterDeposit(_amount: uint256) -> uint256:
    return self.fundsAvailable + self.fundsInvested + _amount


@view
@external
def lenderFunds(_lender: address) -> InvestorFunds:
    return self.funds if _lender == self.lender else empty(InvestorFunds)
    # TODO keep this for compatibility?


@view
@external
def lockedAmount(_lender: address) -> uint256:
    return 0
    # TODO keep this for compatibility?


@view
@external
def lendersArray() -> DynArray[address, 2**0]:
  return [self.lender]
# TODO keep it?


@view
@external
def computeWithdrawableAmount(_lender: address) -> uint256:
    return self._computeWithdrawableAmount() if _lender == self.lender else 0


@view
@external
def fundsInPool() -> uint256:
    return self.fundsAvailable + self.fundsInvested


@view
@external
def currentAmountDeposited(_lender: address) -> uint256:
    return self.funds.currentAmountDeposited if _lender == self.lender else 0
# USED BY LiquidityControls


@view
@external
def totalAmountDeposited(_lender: address) -> uint256:
    return self.funds.totalAmountDeposited if _lender == self.lender else 0


@view
@external
def totalAmountWithdrawn(_lender: address) -> uint256:
    return self.funds.totalAmountWithdrawn if _lender == self.lender else 0


@view
@external
def sharesBasisPoints(_lender: address) -> uint256:
    return 10000 if _lender == self.lender else 0


@view
@external
def activeForRewards(_lender: address) -> bool:
    return self.funds.activeForRewards if _lender == self.lender else False



##### EXTERNAL METHODS - NON-VIEW #####

@external
def __init__(
    _erc20TokenContract: address,
    _protocolWallet: address,
    _protocolFeesShare: uint256
):
    assert _erc20TokenContract != empty(address), "address is the zero address"
    assert _protocolWallet != empty(address), "address is the zero address"
    assert _protocolFeesShare <= 10000, "fees share exceeds 10000 bps"

    self.owner = msg.sender
    erc20TokenContract = _erc20TokenContract
    self.protocolWallet = _protocolWallet
    self.protocolFeesShare = _protocolFeesShare
    self.isPoolActive = True


@external
@payable
def __default__():
    assert msg.sender == erc20TokenContract, "msg.sender is not the WETH addr"
    # log PaymentReceived(msg.sender, msg.sender, msg.value)


@external
def proposeOwner(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address it the zero address"
    assert self.owner != _address, "proposed owner addr is the owner"
    assert self.proposedOwner != _address, "proposed owner addr is the same"

    self.proposedOwner = _address

    log OwnerProposed(
        self.owner,
        _address,
        self.owner,
        _address,
        erc20TokenContract
    )


@external
def claimOwnership():
    assert msg.sender == self.proposedOwner, "msg.sender is not the proposed"

    log OwnershipTransferred(
        self.owner,
        self.proposedOwner,
        self.owner,
        self.proposedOwner,
        erc20TokenContract
    )

    self.owner = self.proposedOwner
    self.proposedOwner = empty(address)


@external
def changeProtocolWallet(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address != self.protocolWallet, "new value is the same"

    log ProtocolWalletChanged(
        erc20TokenContract,
        self.protocolWallet,
        _address,
        erc20TokenContract
    )

    self.protocolWallet = _address


@external
def changeProtocolFeesShare(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value <= 10000, "fees share exceeds 10000 bps"
    assert _value != self.protocolFeesShare, "new value is the same"

    log ProtocolFeesShareChanged(
        erc20TokenContract,
        self.protocolFeesShare,
        _value,
        erc20TokenContract
    )

    self.protocolFeesShare = _value


@external
def setLoansPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert _address != self.loansContract, "new value is the same"

    log LoansPeripheralAddressSet(
        erc20TokenContract,
        self.loansContract,
        _address,
        erc20TokenContract
    )

    self.loansContract = _address


@external
def setLiquidationsPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert _address != self.liquidationsPeripheralContract, "new value is the same"

    log LiquidationsPeripheralAddressSet(
        erc20TokenContract,
        self.liquidationsPeripheralContract,
        _address,
        erc20TokenContract
    )

    self.liquidationsPeripheralContract = _address


@external
def changePoolStatus(_flag: bool):
    assert msg.sender == self.owner, "msg.sender is not the owner"

    self.isPoolActive = _flag

    log ContractStatusChanged(
        erc20TokenContract,
        _flag,
        erc20TokenContract
    )


@external
def deprecate():
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert not self.isPoolDeprecated, "pool is already deprecated"

    self.isPoolDeprecated = True
    self.isPoolActive = False

    log ContractStatusChanged(
        erc20TokenContract,
        False,
        erc20TokenContract
    )

    log ContractDeprecated(
        erc20TokenContract,
        erc20TokenContract
    )


@external
def deposit(_amount: uint256):

    """
    @notice Deposits the given amount of the ERC20 in the lending pool
    @dev Logs the `Deposit` event
    @param _amount Value to deposit
    """

    assert self._fundsAreAllowed(msg.sender, self.lendingPoolCoreContract, _amount), "not enough funds allowed"
    self._deposit(_amount, msg.sender)



@external
@payable
def depositEth():

    """
    @notice Deposits the sent amount in the lending pool
    @dev Logs the `Deposit` event
    """

    log PaymentReceived(msg.sender, msg.sender, msg.value)

    self._wrap_and_approve(self.lendingPoolCoreContract, msg.value)
    self._deposit(msg.value, self)


@external
def withdraw(_amount: uint256):
    """
    @notice Withdrawals the given amount of ERC20 from the lending pool
    @dev Logs the `Withdrawal`
    @param _amount Value to withdraw
    """
    self._withdraw(_amount, msg.sender)


@external
def withdrawEth(_amount: uint256):
    """
    @notice Withdrawals the given amount of ETH from the lending pool
    @dev Logs the `Withdrawal`
    @param _amount Value to withdraw in wei
    """
    self._withdraw(_amount, self)
    self._unwrap_and_send(msg.sender, _amount)



@external
def sendFunds(_to: address, _amount: uint256):
    """
    @notice Sends funds in the pool ERC20 to a borrower as part of a loan creation
    @dev Logs the `FundsTransfer`
    @param _to The wallet address to transfer the funds to
    @param _amount Value to transfer
    """

    self._sendFunds(_to, _to, _amount)


@external
def sendFundsEth(_to: address, _amount: uint256):
    """
    @notice Sends funds in ETH to a borrower as part of a loan creation
    @dev Logs the `FundsTransfer`
    @param _to The wallet address to transfer the funds to
    @param _amount Value to transfer in wei
    """

    self._sendFunds(_to, self, _amount)
    self._unwrap_and_send(_to, _amount)


@payable
@external
def receiveFundsEth(_borrower: address, _amount: uint256, _rewardsAmount: uint256):

    """
    @notice Receive funds in ETH from a borrower as part of a loan payment
    @dev Logs the `FundsReceipt`
    @param _borrower The wallet address to receive the funds from
    @param _amount Value of the loans principal to receive in wei
    @param _rewardsAmount Value of the loans interest (including the protocol fee share) to receive in wei
    """

    _received_amount: uint256 = msg.value
    assert _received_amount > 0, "amount should be higher than 0"
    assert _received_amount == _amount + _rewardsAmount, "recv amount not match partials"

    log PaymentReceived(msg.sender, msg.sender, _amount + _rewardsAmount)

    self._wrap_and_approve(self.lendingPoolCoreContract, _received_amount)
    self._receiveFunds(_borrower, self, _amount, _rewardsAmount)


@external
def receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256):

    """
    @notice Receive funds in the pool ERC20 from a borrower as part of a loan payment
    @dev Logs the `FundsReceipt`
    @param _borrower The wallet address to receive the funds from
    @param _amount Value of the loans principal to receive
    @param _rewardsAmount Value of the loans interest (including the protocol fee share) to receive
    """

    assert self._fundsAreAllowed(_borrower, self.lendingPoolCoreContract, _amount + _rewardsAmount), "insufficient liquidity"
    self._receiveFunds(_borrower, _borrower, _amount, _rewardsAmount)


@external
def receiveFundsFromLiquidation(
    _borrower: address,
    _amount: uint256,
    _rewardsAmount: uint256,
    _distributeToProtocol: bool,
    _investedAmount: uint256,
    _origin: String[30]
):

    """
    @notice Receive funds from a liquidation in the pool ERC20
    @dev Logs the `FundsReceipt`
    @param _borrower The wallet address to receive the funds from
    @param _amount Value of the loans principal to receive
    @param _rewardsAmount Value of the rewards after liquidation (including the protocol fee share) to receive
    @param _distributeToProtocol Wether to distribute the protocol fees or not
    @param _origin Identification of the liquidation method
    """

    assert self._fundsAreAllowed(_borrower, self.lendingPoolCoreContract, _amount + _rewardsAmount), "insufficient liquidity"
    self._receiveFundsFromLiquidation(_borrower, _borrower, _amount, _rewardsAmount, _distributeToProtocol, _investedAmount, _origin)


@payable
@external
def receiveFundsFromLiquidationEth(
    _borrower: address,
    _amount: uint256,
    _rewardsAmount: uint256,
    _distributeToProtocol: bool,
    _investedAmount: uint256,
    _origin: String[30]
):

    """
    @notice Receive funds from a liquidation in ETH
    @dev Logs the `FundsReceipt`
    @param _borrower The wallet address to receive the funds from
    @param _amount Value of the loans principal to receive in wei
    @param _rewardsAmount Value of the rewards after liquidation (including the protocol fee share) to receive in wei
    @param _distributeToProtocol Wether to distribute the protocol fees or not
    @param _origin Identification of the liquidation method
    """

    receivedAmount: uint256 = msg.value

    assert receivedAmount == _amount + _rewardsAmount, "recv amount not match partials"

    log PaymentReceived(msg.sender, msg.sender, receivedAmount)

    self._wrap_and_approve(self.lendingPoolCoreContract, receivedAmount)
    self._receiveFundsFromLiquidation(_borrower, self, _amount, _rewardsAmount, _distributeToProtocol, _investedAmount, _origin)


#### CORE





# Global variables



##### INTERNAL METHODS #####



##### EXTERNAL METHODS - VIEW #####



##### EXTERNAL METHODS - NON-VIEW #####



