# @version ^0.3.6


# Interfaces

from vyper.interfaces import ERC20 as IERC20
from interfaces import ILendingPoolCore
from interfaces import ILiquidityControls


# Structs

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    lockPeriodEnd: uint256
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

event LiquidityControlsAddressSet:
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

event InvestingStatusChanged:
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
    erc20TokenContract: address


# Global variables

owner: public(address)
proposedOwner: public(address)

loansContract: public(address)
lendingPoolCoreContract: public(address)
erc20TokenContract: public(address)
liquidationsPeripheralContract: public(address)
liquidityControlsContract: public(address)

protocolWallet: public(address)
protocolFeesShare: public(uint256) # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000

maxCapitalEfficienty: public(uint256) # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
isPoolActive: public(bool)
isPoolDeprecated: public(bool)
isPoolInvesting: public(bool)

whitelistEnabled: public(bool)
whitelistedAddresses: public(HashMap[address, bool])


##### INTERNAL METHODS - VIEW #####

@view
@internal
def _fundsAreAllowed(_owner: address, _spender: address, _amount: uint256) -> bool:
    amountAllowed: uint256 = IERC20(self.erc20TokenContract).allowance(_owner, _spender)
    return _amount <= amountAllowed


@pure
@internal
def _poolHasFundsToInvest(_fundsAvailable: uint256, _fundsInvested: uint256, _capitalEfficienty: uint256) -> bool:
    if _fundsAvailable + _fundsInvested == 0:
        return False
    
    return _fundsInvested * 10000 / (_fundsAvailable + _fundsInvested) < _capitalEfficienty


@view
@internal
def _poolHasFundsToInvestAfterDeposit(_amount: uint256) -> bool:
    fundsAvailable: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable() + _amount
    fundsInvested: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsInvested()

    return self._poolHasFundsToInvest(fundsAvailable, fundsInvested, self.maxCapitalEfficienty)


@view
@internal
def _poolHasFundsToInvestAfterPayment(_amount: uint256, _rewards: uint256) -> bool:
    fundsAvailable: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable() + _amount + _rewards
    fundsInvested: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsInvested() - _amount

    return self._poolHasFundsToInvest(fundsAvailable, fundsInvested, self.maxCapitalEfficienty)


@view
@internal
def _poolHasFundsToInvestAfterWithdraw(_amount: uint256) -> bool:
    fundsAvailable: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable() - _amount
    fundsInvested: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsInvested()
    
    return self._poolHasFundsToInvest(fundsAvailable, fundsInvested, self.maxCapitalEfficienty)


@view
@internal
def _poolHasFundsToInvestAfterInvestment(_amount: uint256) -> bool:
    fundsAvailable: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable() - _amount
    fundsInvested: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsInvested() + _amount
    
    return self._poolHasFundsToInvest(fundsAvailable, fundsInvested, self.maxCapitalEfficienty)


@view
@internal
def _maxFundsInvestable() -> uint256:
    fundsAvailable: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable()
    fundsInvested: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsInvested()

    fundsBuffer: uint256 = (fundsAvailable + fundsInvested) * (10000 - self.maxCapitalEfficienty) / 10000

    if fundsBuffer > fundsAvailable:
        return 0
    
    return fundsAvailable - fundsBuffer


@view
@internal
def _theoreticalMaxFundsInvestable(_amount: uint256) -> uint256:
    fundsAvailable: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable()
    fundsInvested: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsInvested()

    return (fundsAvailable + fundsInvested + _amount) * self.maxCapitalEfficienty / 10000


@view
@internal
def _computeLockPeriodEnd(_lender: address) -> uint256:
    lockPeriodEnd: uint256 = 0
    if ILendingPoolCore(self.lendingPoolCoreContract).funds(_lender).lockPeriodEnd <= block.timestamp:
        lockPeriodEnd = block.timestamp + ILiquidityControls(self.liquidityControlsContract).lockPeriodDuration()
    else:
        lockPeriodEnd = ILendingPoolCore(self.lendingPoolCoreContract).funds(msg.sender).lockPeriodEnd
    
    return lockPeriodEnd


##### INTERNAL METHODS - WRITE #####

@internal
def _receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256):
    rewardsProtocol: uint256 = _rewardsAmount * self.protocolFeesShare / 10000
    rewardsPool: uint256 = _rewardsAmount - rewardsProtocol

    if not self.isPoolInvesting and self._poolHasFundsToInvestAfterPayment(_amount, rewardsPool):
        self.isPoolInvesting = True

        log InvestingStatusChanged(
            self.erc20TokenContract,
            True,
            self.erc20TokenContract
        )

    if not ILendingPoolCore(self.lendingPoolCoreContract).receiveFunds(_borrower, _amount, rewardsPool):
        raise "error receiving funds in LPCore"
    
    if not ILendingPoolCore(self.lendingPoolCoreContract).transferProtocolFees(_borrower, self.protocolWallet, rewardsProtocol):
        raise "error transferring protocol fees"

    log FundsReceipt(_borrower, _borrower, _amount, rewardsPool, rewardsProtocol, self.erc20TokenContract)


##### EXTERNAL METHODS - VIEW #####

@view
@external
def maxFundsInvestable() -> uint256:
    return self._maxFundsInvestable()


@view
@external
def theoreticalMaxFundsInvestable() -> uint256:
    return self._theoreticalMaxFundsInvestable(0)


@view
@external
def theoreticalMaxFundsInvestableAfterDeposit(_amount: uint256) -> uint256:
    return self._theoreticalMaxFundsInvestable(_amount)


@view
@external
def lenderFunds(_lender: address) -> InvestorFunds:
    return ILendingPoolCore(self.lendingPoolCoreContract).funds(_lender)


##### EXTERNAL METHODS - NON-VIEW #####

@external
def __init__(
    _lendingPoolCoreContract: address,
    _erc20TokenContract: address,
    _protocolWallet: address,
    _protocolFeesShare: uint256,
    _maxCapitalEfficienty: uint256,
    _whitelistEnabled: bool
):
    assert _lendingPoolCoreContract != empty(address), "address is the zero address"
    assert _erc20TokenContract != empty(address), "address is the zero address"
    assert _protocolWallet != empty(address), "address is the zero address"
    assert _protocolFeesShare <= 10000, "fees share exceeds 10000 bps"
    assert _maxCapitalEfficienty <= 10000, "capital eff exceeds 10000 bps"

    self.owner = msg.sender
    self.lendingPoolCoreContract = _lendingPoolCoreContract
    self.erc20TokenContract = _erc20TokenContract
    self.protocolWallet = _protocolWallet
    self.protocolFeesShare = _protocolFeesShare
    self.maxCapitalEfficienty = _maxCapitalEfficienty
    self.isPoolActive = True
    
    if _whitelistEnabled:
        self.whitelistEnabled = _whitelistEnabled


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
        self.erc20TokenContract
    )


@external
def claimOwnership():
    assert msg.sender == self.proposedOwner, "msg.sender is not the proposed"

    log OwnershipTransferred(
        self.owner,
        self.proposedOwner,
        self.owner,
        self.proposedOwner,
        self.erc20TokenContract
    )

    self.owner = self.proposedOwner
    self.proposedOwner = empty(address)


@external
def changeMaxCapitalEfficiency(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value <= 10000, "capital eff exceeds 10000 bps"
    assert _value != self.maxCapitalEfficienty, "new value is the same"

    log MaxCapitalEfficiencyChanged(
        self.erc20TokenContract,
        self.maxCapitalEfficienty,
        _value,
        self.erc20TokenContract
    )

    self.maxCapitalEfficienty = _value


@external
def changeProtocolWallet(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address != self.protocolWallet, "new value is the same"

    log ProtocolWalletChanged(
        self.erc20TokenContract,
        self.protocolWallet,
        _address,
        self.erc20TokenContract
    )

    self.protocolWallet = _address


@external
def changeProtocolFeesShare(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value <= 10000, "fees share exceeds 10000 bps"
    assert _value != self.protocolFeesShare, "new value is the same"

    log ProtocolFeesShareChanged(
        self.erc20TokenContract,
        self.protocolFeesShare,
        _value,
        self.erc20TokenContract
    )

    self.protocolFeesShare = _value


@external
def setLoansPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert _address != self.loansContract, "new value is the same"

    log LoansPeripheralAddressSet(
        self.erc20TokenContract,
        self.loansContract,
        _address,
        self.erc20TokenContract
    )

    self.loansContract = _address


@external
def setLiquidationsPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert _address != self.liquidationsPeripheralContract, "new value is the same"

    log LiquidationsPeripheralAddressSet(
        self.erc20TokenContract,
        self.liquidationsPeripheralContract,
        _address,
        self.erc20TokenContract
    )

    self.liquidationsPeripheralContract = _address


@external
def setLiquidityControlsAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert _address != self.liquidityControlsContract, "new value is the same"

    log LiquidityControlsAddressSet(
        self.erc20TokenContract,
        self.liquidityControlsContract,
        _address,
        self.erc20TokenContract
    )

    self.liquidityControlsContract = _address


@external
def changeWhitelistStatus(_flag: bool):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.whitelistEnabled != _flag, "new value is the same"

    self.whitelistEnabled = _flag

    log WhitelistStatusChanged(
        self.erc20TokenContract,
        _flag,
        self.erc20TokenContract
    )


@external
def addWhitelistedAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert self.whitelistEnabled, "whitelist is disabled"
    assert not self.whitelistedAddresses[_address], "address is already whitelisted"

    self.whitelistedAddresses[_address] = True

    log WhitelistAddressAdded(
        self.erc20TokenContract,
        _address,
        self.erc20TokenContract
    )


@external
def removeWhitelistedAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert self.whitelistEnabled, "whitelist is disabled"
    assert self.whitelistedAddresses[_address], "address is not whitelisted"

    self.whitelistedAddresses[_address] = False

    log WhitelistAddressRemoved(
        self.erc20TokenContract,
        _address,
        self.erc20TokenContract
    )


@external
def changePoolStatus(_flag: bool):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.isPoolActive != _flag, "new value is the same"

    self.isPoolActive = _flag
  
    if not _flag:
        self.isPoolInvesting = False

        log InvestingStatusChanged(
            self.erc20TokenContract,
            False,
            self.erc20TokenContract
        )

    if _flag and not self.isPoolInvesting and self._poolHasFundsToInvestAfterWithdraw(0):
        self.isPoolInvesting = True

        log InvestingStatusChanged(
            self.erc20TokenContract,
            True,
            self.erc20TokenContract
        )

    log ContractStatusChanged(
        self.erc20TokenContract,
        _flag,
        self.erc20TokenContract
    )


@external
def deprecate():
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert not self.isPoolDeprecated, "pool is already deprecated"

    self.isPoolDeprecated = True
    self.isPoolActive = False
    self.isPoolInvesting = False

    log ContractStatusChanged(
        self.erc20TokenContract,
        False,
        self.erc20TokenContract
    )

    log InvestingStatusChanged(
        self.erc20TokenContract,
        False,
        self.erc20TokenContract
    )

    log ContractDeprecated(
        self.erc20TokenContract,
        self.erc20TokenContract
    )


@external
def deposit(_amount: uint256):
    # _amount should be passed in wei

    assert not self.isPoolDeprecated, "pool is deprecated, withdraw"
    assert self.isPoolActive, "pool is not active right now"
    assert _amount > 0, "_amount has to be higher than 0"
    assert ILiquidityControls(self.liquidityControlsContract).withinPoolShareLimit(
        msg.sender,
        _amount,
        self,
        self.lendingPoolCoreContract,
        self._theoreticalMaxFundsInvestable(_amount)
    ), "max pool share surpassed"
    assert self._fundsAreAllowed(msg.sender, self.lendingPoolCoreContract, _amount), "not enough funds allowed"

    if self.whitelistEnabled and not self.whitelistedAddresses[msg.sender]:
        raise "msg.sender is not whitelisted"

    if not self.isPoolInvesting and self._poolHasFundsToInvestAfterDeposit(_amount):
        self.isPoolInvesting = True

        log InvestingStatusChanged(
            self.erc20TokenContract,
            True,
            self.erc20TokenContract
        )

    if not ILendingPoolCore(self.lendingPoolCoreContract).deposit(msg.sender, _amount, self._computeLockPeriodEnd(msg.sender)):
        raise "error creating deposit"

    log Deposit(msg.sender, msg.sender, _amount, self.erc20TokenContract)


@external
def withdraw(_amount: uint256):
    # _amount should be passed in wei

    assert _amount > 0, "_amount has to be higher than 0"
    assert ILiquidityControls(self.liquidityControlsContract).outOfLockPeriod(msg.sender, self.lendingPoolCoreContract), "msg.sender within lock period"
    assert ILendingPoolCore(self.lendingPoolCoreContract).computeWithdrawableAmount(msg.sender) >= _amount, "_amount more than withdrawable"
    assert ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable() >= _amount, "available funds less than amount"

    if self.isPoolInvesting and not self._poolHasFundsToInvestAfterWithdraw(_amount):
        self.isPoolInvesting = False

        log InvestingStatusChanged(
            self.erc20TokenContract,
            False,
            self.erc20TokenContract
        )

    if not ILendingPoolCore(self.lendingPoolCoreContract).withdraw(msg.sender, _amount):
        raise "error withdrawing funds"

    log Withdrawal(msg.sender, msg.sender, _amount, self.erc20TokenContract)


@external
def sendFunds(_to: address, _amount: uint256):
    # _amount should be passed in wei

    assert not self.isPoolDeprecated, "pool is deprecated"
    assert self.isPoolActive, "pool is inactive"
    assert self.isPoolInvesting, "max capital eff reached"
    assert msg.sender == self.loansContract, "msg.sender is not the loans addr"
    assert _to != empty(address), "_to is the zero address"
    assert _amount > 0, "_amount has to be higher than 0"
    assert _amount <= self._maxFundsInvestable(), "insufficient liquidity"

    if self.isPoolInvesting and not self._poolHasFundsToInvestAfterInvestment(_amount):
        self.isPoolInvesting = False

        log InvestingStatusChanged(
            self.erc20TokenContract,
            False,
            self.erc20TokenContract
        )

    if not ILendingPoolCore(self.lendingPoolCoreContract).sendFunds(_to, _amount):
        raise "error sending funds in LPCore"

    log FundsTransfer(_to, _to, _amount, self.erc20TokenContract)


@external
def receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256):
    # _amount and _rewardsAmount should be passed in wei

    assert msg.sender == self.loansContract, "msg.sender is not the loans addr"
    assert _borrower != empty(address), "_borrower is the zero address"
    assert self._fundsAreAllowed(_borrower, self.lendingPoolCoreContract, _amount + _rewardsAmount), "insufficient liquidity"
    assert _amount + _rewardsAmount > 0, "amount should be higher than 0"
    
    self._receiveFunds(_borrower, _amount, _rewardsAmount)


@external
def receiveFundsFromLiquidation(_borrower: address, _amount: uint256, _rewardsAmount: uint256):
    # _amount and _rewardsAmount should be passed in wei

    assert msg.sender == self.liquidationsPeripheralContract, "msg.sender is not the BN addr"
    assert _borrower != empty(address), "_borrower is the zero address"
    assert self._fundsAreAllowed(_borrower, self.lendingPoolCoreContract, _amount + _rewardsAmount), "insufficient liquidity"
    assert _amount + _rewardsAmount > 0, "amount should be higher than 0"
    
    self._receiveFunds(_borrower, _amount, _rewardsAmount)
