# @version ^0.3.3


# Interfaces

from vyper.interfaces import ERC20 as IERC20
from interfaces import ILendingPoolCore


# Structs

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool


# Events

event Deposit:
    wallet: address
    amount: uint256
    erc20TokenContract: address

event Withdrawal:
    wallet: address
    amount: uint256
    erc20TokenContract: address

event Compound:
    wallet: address
    amount: uint256
    erc20TokenContract: address

event FundsTransfer:
    wallet: address
    amount: uint256
    erc20TokenContract: address

event FundsReceipt:
    wallet: address
    amount: uint256
    rewardsPool: uint256
    rewardsProtocol: uint256
    erc20TokenContract: address


# Global variables

owner: public(address)
loansContract: public(address)
lendingPoolCoreContract: public(address)
erc20TokenContract: public(address)

protocolWallet: public(address)
protocolFeesShare: public(uint256) # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000

maxCapitalEfficienty: public(uint256) # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
isPoolActive: public(bool)
isPoolDeprecated: public(bool)
isPoolInvesting: public(bool)

whitelistEnabled: public(bool)
whitelistedAddresses: public(HashMap[address, bool])


##### INTERNAL METHODS #####

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


##### EXTERNAL METHODS - VIEW #####

@view
@external
def maxFundsInvestable() -> uint256:
    return self._maxFundsInvestable()


##### EXTERNAL METHODS - NON-VIEW #####

@external
def __init__(
    _erc20TokenContract: address,
    _protocolWallet: address,
    _protocolFeesShare: uint256,
    _maxCapitalEfficienty: uint256,
    _whitelistEnabled: bool
):
    assert _erc20TokenContract != ZERO_ADDRESS, "address is the zero address"
    assert _protocolWallet != ZERO_ADDRESS, "address is the zero address"
    assert _protocolFeesShare <= 10000, "fees share exceeds 10000 bps"
    assert _maxCapitalEfficienty <= 10000, "capital eff exceeds 10000 bps"

    self.owner = msg.sender
    self.erc20TokenContract = _erc20TokenContract
    self.protocolWallet = _protocolWallet
    self.protocolFeesShare = _protocolFeesShare
    self.maxCapitalEfficienty = _maxCapitalEfficienty
    self.isPoolActive = True
    self.isPoolDeprecated = False
    self.isPoolInvesting = False
    self.whitelistEnabled = _whitelistEnabled


@external
def changeOwnership(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero address"
    assert _address != self.owner, "new owner address is the same"

    self.owner = _address


@external
def changeMaxCapitalEfficiency(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value <= 10000, "capital eff exceeds 10000 bps"
    assert _value != self.maxCapitalEfficienty, "new value is the same"

    self.maxCapitalEfficienty = _value


@external
def changeProtocolWallet(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero address"
    assert _address != self.protocolWallet, "new value is the same"

    self.protocolWallet = _address


@external
def changeProtocolFeesShare(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value <= 10000, "fees share exceeds 10000 bps"
    assert _value != self.protocolFeesShare, "new value is the same"

    self.protocolFeesShare = _value


@external
def changePoolStatus(_flag: bool):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.isPoolActive != _flag, "new value is the same"

    self.isPoolActive = _flag
  
    if not _flag:
        self.isPoolInvesting = False

    if _flag and not self.isPoolInvesting and self._poolHasFundsToInvestAfterWithdraw(0):
        self.isPoolInvesting = True


@external
def setLendingPoolCoreAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero address"
    assert _address != self.lendingPoolCoreContract, "new value is the same"

    self.lendingPoolCoreContract = _address


@external
def setLoansPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero address"
    assert _address != self.loansContract, "new value is the same"

    self.loansContract = _address


@external
def deprecate():
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert not self.isPoolDeprecated, "pool is already deprecated"

    self.isPoolDeprecated = True
    self.isPoolActive = False
    self.isPoolInvesting = False


@external
def changeWhitelistStatus(_flag: bool):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.whitelistEnabled != _flag, "new value is the same"

    self.whitelistEnabled = _flag


@external
def addWhitelistedAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.whitelistEnabled, "whitelist is disabled"
    assert not self.whitelistedAddresses[_address], "address is already whitelisted"

    self.whitelistedAddresses[_address] = True


@external
def removeWhitelistedAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.whitelistEnabled, "whitelist is disabled"
    assert self.whitelistedAddresses[_address], "address is not whitelisted"

    self.whitelistedAddresses[_address] = False


@external
def deposit(_amount: uint256):
    # _amount should be passed in wei

    assert not self.isPoolDeprecated, "pool is deprecated, withdraw"
    assert self.isPoolActive, "pool is not active right now"
    assert _amount > 0, "_amount has to be higher than 0"
    assert self._fundsAreAllowed(msg.sender, self.lendingPoolCoreContract, _amount), "not enough funds allowed"

    if self.whitelistEnabled and not self.whitelistedAddresses[msg.sender]:
        raise "msg.sender is not whitelisted"

    if not self.isPoolInvesting and self._poolHasFundsToInvestAfterDeposit(_amount):
        self.isPoolInvesting = True

    if not ILendingPoolCore(self.lendingPoolCoreContract).deposit(msg.sender, _amount):
        raise "error creating deposit"

    log Deposit(msg.sender, _amount, self.erc20TokenContract)


@external
def withdraw(_amount: uint256):
    # _amount should be passed in wei

    assert _amount > 0, "_amount has to be higher than 0"
    assert ILendingPoolCore(self.lendingPoolCoreContract).computeWithdrawableAmount(msg.sender) >= _amount, "_amount more than withdrawable"
    assert ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable() >= _amount, "available funds less than amount"

    if self.isPoolInvesting and not self._poolHasFundsToInvestAfterWithdraw(_amount):
        self.isPoolInvesting = False

    if not ILendingPoolCore(self.lendingPoolCoreContract).withdraw(msg.sender, _amount):
        raise "error withdrawing funds"

    log Withdrawal(msg.sender, _amount, self.erc20TokenContract)


@external
def sendFunds(_to: address, _amount: uint256):
    # _amount should be passed in wei

    assert not self.isPoolDeprecated, "pool is deprecated"
    assert self.isPoolActive, "pool is inactive"
    assert self.isPoolInvesting, "max capital eff reached"
    assert msg.sender == self.loansContract, "msg.sender is not the loans addr"
    assert _to != ZERO_ADDRESS, "_to is the zero address"
    assert _amount > 0, "_amount has to be higher than 0"
    assert _amount <= self._maxFundsInvestable(), "insufficient liquidity"

    if self.isPoolInvesting and not self._poolHasFundsToInvestAfterInvestment(_amount):
        self.isPoolInvesting = False

    if not ILendingPoolCore(self.lendingPoolCoreContract).sendFunds(_to, _amount):
        raise "error sending funds in LPCore"

    log FundsTransfer(_to, _amount, self.erc20TokenContract)


@external
def receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256):
    # _amount and _rewardsAmount should be passed in wei

    assert msg.sender == self.loansContract, "msg.sender is not the loans addr"
    assert _borrower != ZERO_ADDRESS, "_borrower is the zero address"
    assert self._fundsAreAllowed(_borrower, self.lendingPoolCoreContract, _amount + _rewardsAmount), "insufficient liquidity"
    assert _amount + _rewardsAmount > 0, "amount should be higher than 0"
    
    rewardsProtocol: uint256 = _rewardsAmount * self.protocolFeesShare / 10000
    rewardsPool: uint256 = _rewardsAmount - rewardsProtocol

    if not self.isPoolInvesting and self._poolHasFundsToInvestAfterPayment(_amount, rewardsPool):
        self.isPoolInvesting = True

    if not ILendingPoolCore(self.lendingPoolCoreContract).receiveFunds(_borrower, _amount, rewardsPool):
        raise "error receiving funds in LPCore"
    
    if not ILendingPoolCore(self.lendingPoolCoreContract).transferProtocolFees(_borrower, self.protocolWallet, rewardsProtocol):
        raise "error transferring protocol fees"

    log FundsReceipt(msg.sender, _amount, rewardsPool, rewardsProtocol, self.erc20TokenContract)


@external
@payable
def __default__():
  if msg.value > 0:
    send(msg.sender, msg.value)
