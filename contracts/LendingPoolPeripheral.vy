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


@view
@internal
def _poolHasFundsToInvest() -> bool:
    fundsAvailable: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable()
    fundsInvested: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsInvested()
    if fundsAvailable + fundsInvested == 0:
        return False
    
    return fundsInvested * 10000 / (fundsAvailable + fundsInvested) < self.maxCapitalEfficienty


@view
@internal
def _maxFundsInvestable() -> int256:
    fundsAvailable: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable()
    fundsInvested: uint256 = ILendingPoolCore(self.lendingPoolCoreContract).fundsInvested()
    return convert(fundsAvailable, int256) - (convert(fundsAvailable, int256) + convert(fundsInvested, int256)) * (10000 - convert(self.maxCapitalEfficienty, int256)) / 10000


##### EXTERNAL METHODS - VIEW #####

@view
@external
def poolHasFundsToInvest() -> bool:
    return self._poolHasFundsToInvest()


@view
@external
def maxFundsInvestable() -> int256:
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
    assert _erc20TokenContract != ZERO_ADDRESS, "The ERC20 contract address is the zero address"
    assert _protocolWallet != ZERO_ADDRESS, "The protocol wallet address is the zero address"
    assert _protocolFeesShare <= 10000, "The protocol fees share can not exceed 10000 bps"
    assert _maxCapitalEfficienty <= 10000, "The capital efficiency can not exceed 10000 bps"

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
def changeOwnership(_address: address) -> address:
    assert msg.sender == self.owner, "Only the owner can change the contract ownership"
    assert _address != ZERO_ADDRESS, "The address is the zero address"
    assert _address != self.owner, "The new owner address should be different than the current one"

    self.owner = _address
    return self.owner


@external
def changeMaxCapitalEfficiency(_value: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the owner can change the max capital efficiency"
    assert _value <= 10000, "The capital efficiency can not exceed 10000 bps"
    assert _value != self.maxCapitalEfficienty, "The new capital efficiency should be different than the current one"

    self.maxCapitalEfficienty = _value
    return self.maxCapitalEfficienty


@external
def changeProtocolWallet(_address: address) -> address:
    assert msg.sender == self.owner, "Only the owner can change the protocol wallet address"
    assert _address != ZERO_ADDRESS, "The address is the zero address"
    assert _address != self.protocolWallet, "The new protocol wallet should be different than the current one"

    self.protocolWallet = _address
    return self.protocolWallet


@external
def changeProtocolFeesShare(_value: uint256) -> uint256:
    assert msg.sender == self.owner, "Only the owner can change the protocol fees share"
    assert _value <= 10000, "The protocol fees share can not exceed 10000 bps"
    assert _value != self.protocolFeesShare, "The new protocol fees share should be different than the current one"

    self.protocolFeesShare = _value
    return self.protocolFeesShare


@external
def changePoolStatus(_flag: bool) -> bool:
    assert msg.sender == self.owner, "Only the owner can change the pool status"
    assert self.isPoolActive != _flag, "The new pool status should be different than the current status"

    self.isPoolActive = _flag
  
    if not _flag:
        self.isPoolInvesting = False

    if _flag and not self.isPoolInvesting and self._poolHasFundsToInvest():
        self.isPoolInvesting = True

    return self.isPoolActive


@external
def setLendingPoolCoreAddress(_address: address) -> address:
    assert msg.sender == self.owner, "Only the contract owner can set the lending pool core address"
    assert _address != ZERO_ADDRESS, "The address is the zero address"
    assert _address != self.lendingPoolCoreContract, "The new LendingPoolCore address should be different than the current one"

    self.lendingPoolCoreContract = _address
    return self.lendingPoolCoreContract


@external
def setLoansPeripheralAddress(_address: address) -> address:
    assert msg.sender == self.owner, "Only the contract owner can set the loans address"
    assert _address != ZERO_ADDRESS, "The address is the zero address"
    assert _address != self.loansContract, "The new Loans address should be different than the current one"

    self.loansContract = _address
    return self.loansContract


@external
def deprecate() -> bool:
    assert msg.sender == self.owner, "Only the owner can change the pool to deprecated"
    assert not self.isPoolDeprecated, "The pool is already deprecated"

    self.isPoolDeprecated = True
    self.isPoolActive = False
    self.isPoolInvesting = False

    return self.isPoolDeprecated


@external
def changeWhitelistStatus(_flag: bool) -> bool:
    assert msg.sender == self.owner, "Only the owner can change the whitelist status"
    assert self.whitelistEnabled != _flag, "The new whitelist status should be different than the current status"

    self.whitelistEnabled = _flag
    return _flag


@external
def addWhitelistedAddress(_address: address):
    assert msg.sender == self.owner, "Only the owner can add addresses to the whitelist"
    assert self.whitelistEnabled, "The whitelist is disabled"
    assert not self.whitelistedAddresses[_address], "The address is already whitelisted"

    self.whitelistedAddresses[_address] = True


@external
def removeWhitelistedAddress(_address: address):
    assert msg.sender == self.owner, "Only the owner can remove addresses from the whitelist"
    assert self.whitelistEnabled, "The whitelist is disabled"
    assert self.whitelistedAddresses[_address], "The address is not whitelisted"

    self.whitelistedAddresses[_address] = False


@external
def deposit(_amount: uint256) -> bool:
    # _amount should be passed in wei

    assert not self.isPoolDeprecated, "Pool is deprecated, please withdraw any outstanding deposit"
    assert self.isPoolActive, "Pool is not active right now"
    assert _amount > 0, "Amount deposited has to be higher than 0"
    assert self._fundsAreAllowed(msg.sender, self.lendingPoolCoreContract, _amount), "Insufficient funds allowed to be transfered"

    if self.whitelistEnabled and not self.whitelistedAddresses[msg.sender]:
        raise "The whitelist is enabled and the sender is not whitelisted"

    if not ILendingPoolCore(self.lendingPoolCoreContract).deposit(msg.sender, _amount):
        raise "Error creating deposit"

    if not self.isPoolInvesting and self._poolHasFundsToInvest():
        self.isPoolInvesting = True

    if not ILendingPoolCore(self.lendingPoolCoreContract).transferDeposit(msg.sender, _amount):
        raise "Error transferring deposit"

    log Deposit(msg.sender, _amount, self.erc20TokenContract)

    return True


@external
def withdraw(_amount: uint256) -> bool:
    # _amount should be passed in wei

    assert _amount > 0, "Amount withdrawn has to be higher than 0"
    assert ILendingPoolCore(self.lendingPoolCoreContract).computeWithdrawableAmount(msg.sender) >= _amount, "The sender has insufficient liquidity for withdrawal"
    assert ILendingPoolCore(self.lendingPoolCoreContract).fundsAvailable() >= _amount, "The pool has insufficient liquidity for withdrawal"

    if self.isPoolInvesting and not self._poolHasFundsToInvest():
        self.isPoolInvesting = False

    if not ILendingPoolCore(self.lendingPoolCoreContract).withdraw(msg.sender, _amount):
        raise "Error withdrawing funds"

    log Withdrawal(msg.sender, _amount, self.erc20TokenContract)

    return True


@external
def sendFunds(_to: address, _amount: uint256) -> bool:
    # _amount should be passed in wei

    assert not self.isPoolDeprecated, "Pool is deprecated"
    assert self.isPoolActive, "The pool is not active and is not investing more right now"
    assert self.isPoolInvesting, "Max capital efficiency reached, the pool is not investing more right now"
    assert msg.sender == self.loansContract, "Only the loans contract address can request to send funds"
    assert _to != ZERO_ADDRESS, "The address to transfer funds to is the zero address"
    assert _amount > 0, "The amount to send should be higher than 0"
    assert convert(_amount, int256) <= self._maxFundsInvestable(), "No sufficient deposited funds to perform the transaction"

    if not ILendingPoolCore(self.lendingPoolCoreContract).sendFunds(_to, _amount):
        raise "Error sending funds in LPCore"

    if self.isPoolInvesting and not self._poolHasFundsToInvest():
        self.isPoolInvesting = False

    log FundsTransfer(_to, _amount, self.erc20TokenContract)

    return True


@external
def receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256) -> bool:
    # _amount and _rewardsAmount should be passed in wei

    assert msg.sender == self.loansContract, "The sender address is not the loans contract address"
    assert _borrower != ZERO_ADDRESS, "The borrower address is the zero address"
    assert self._fundsAreAllowed(_borrower, self.lendingPoolCoreContract, _amount + _rewardsAmount), "Insufficient funds allowed to be transfered"
    assert _amount + _rewardsAmount > 0, "The sent value should be higher than 0"
    
    rewardsProtocol: uint256 = _rewardsAmount * self.protocolFeesShare / 10000
    rewardsPool: uint256 = _rewardsAmount - rewardsProtocol

    if not ILendingPoolCore(self.lendingPoolCoreContract).receiveFunds(_borrower, _amount, _rewardsAmount):
        raise "Error receiving funds in LPCore"
    
    if not ILendingPoolCore(self.lendingPoolCoreContract).transferProtocolFees(self.protocolWallet, rewardsProtocol):
        raise "Error transferring funds to protocol wallet"

    if not ILendingPoolCore(self.lendingPoolCoreContract).updateLiquidity(_amount, rewardsPool):
        raise "Error updating liquidity data"

    if not self.isPoolInvesting and self._poolHasFundsToInvest():
        self.isPoolInvesting = True

    log FundsReceipt(msg.sender, _amount, rewardsPool, rewardsProtocol, self.erc20TokenContract)

    return True


@external
@payable
def __default__():
  if msg.value > 0:
    send(msg.sender, msg.value)
