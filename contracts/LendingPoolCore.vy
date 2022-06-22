# @version ^0.3.3


# Interfaces

from vyper.interfaces import ERC20 as IERC20


# Structs

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool


# Events

event OwnershipTransferred:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address


# Global variables

owner: public(address)
proposedOwner: public(address)

lendingPoolPeripheral: public(address)
erc20TokenContract: public(address)

funds: public(HashMap[address, InvestorFunds])
lenders: public(DynArray[address, 2**50])
knownLenders: public(HashMap[address, bool])
activeLenders: public(uint256)


fundsAvailable: public(uint256)
fundsInvested: public(uint256)
totalFundsInvested: public(uint256)
totalRewards: public(uint256)
totalSharesBasisPoints: public(uint256)


##### INTERNAL METHODS #####

@view
@internal
def _fundsAreAllowed(_owner: address, _spender: address, _amount: uint256) -> bool:
    amountAllowed: uint256 = IERC20(self.erc20TokenContract).allowance(_owner, _spender)
    return _amount <= amountAllowed


@view
@internal
def _computeShares(_amount: uint256) -> uint256:
    if self.totalSharesBasisPoints == 0:
        return _amount
    return self.totalSharesBasisPoints * _amount / (self.fundsAvailable + self.fundsInvested)


@view
@internal
def _computeWithdrawableAmount(_lender: address) -> uint256:
    if self.totalSharesBasisPoints == 0:
        return 0
    return (self.fundsAvailable + self.fundsInvested) * self.funds[_lender].sharesBasisPoints / self.totalSharesBasisPoints


##### EXTERNAL METHODS - VIEW #####

@view
@external
def lendersArray() -> DynArray[address, 2**50]:
  return self.lenders


@view
@external
def computeWithdrawableAmount(_lender: address) -> uint256:
    return self._computeWithdrawableAmount(_lender)


##### EXTERNAL METHODS - NON-VIEW #####

@external
def __init__(
    _erc20TokenContract: address
):
    assert _erc20TokenContract != ZERO_ADDRESS, "The address is the zero address"

    self.owner = msg.sender
    self.erc20TokenContract = _erc20TokenContract


@external
def proposeOwner(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "_address it the zero address"
    assert self.owner != _address, "proposed owner addr is the owner"
    assert self.proposedOwner != _address, "proposed owner addr is the same"

    self.proposedOwner = _address


@external
def claimOwnership():
    assert msg.sender == self.proposedOwner, "msg.sender is not the proposed"

    log OwnershipTransferred(self.owner, self.proposedOwner, self.owner, self.proposedOwner, self.erc20TokenContract)

    self.owner = self.proposedOwner
    self.proposedOwner = ZERO_ADDRESS


@external
def setLendingPoolPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero address"
    assert _address != self.lendingPoolPeripheral, "new value is the same"

    self.lendingPoolPeripheral = _address


@external
def deposit(_lender: address, _amount: uint256) -> bool:
    # _amount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "msg.sender is not LP peripheral"
    assert _lender != ZERO_ADDRESS, "The _address is the zero address"
    assert _amount > 0, "_amount has to be higher than 0"
    assert self._fundsAreAllowed(_lender, self, _amount), "Not enough funds allowed"

    sharesAmount: uint256 = self._computeShares(_amount)

    if self.funds[_lender].currentAmountDeposited > 0:
        self.funds[_lender].totalAmountDeposited += _amount
        self.funds[_lender].currentAmountDeposited += _amount
        self.funds[_lender].sharesBasisPoints += sharesAmount
    elif self.funds[_lender].currentAmountDeposited == 0 and self.knownLenders[_lender]:
        self.funds[_lender].totalAmountDeposited += _amount
        self.funds[_lender].currentAmountDeposited = _amount
        self.funds[_lender].sharesBasisPoints = sharesAmount
        self.funds[_lender].activeForRewards = True

        self.activeLenders += 1
    else:
        self.funds[_lender] = InvestorFunds(
            {
                currentAmountDeposited: _amount,
                totalAmountDeposited: _amount,
                totalAmountWithdrawn: 0,
                sharesBasisPoints: sharesAmount,
                activeForRewards: True
            }
        )
        self.lenders.append(_lender)
        self.knownLenders[_lender] = True
        self.activeLenders += 1

    self.fundsAvailable += _amount
    self.totalSharesBasisPoints += sharesAmount

    return IERC20(self.erc20TokenContract).transferFrom(_lender, self, _amount)


@external
def withdraw(_lender: address, _amount: uint256) -> bool:
    # _amount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "msg.sender is not LP peripheral"
    assert _amount > 0, "_amount has to be higher than 0"
    assert _lender != ZERO_ADDRESS, "The _lender is the zero address"
    assert self._computeWithdrawableAmount(_lender) >= _amount, "_amount more than withdrawable"
    assert self.fundsAvailable >= _amount, "Available funds less than amount"

    newDepositAmount: uint256 = self._computeWithdrawableAmount(_lender) - _amount
    newLenderSharesAmount: uint256 = self._computeShares(newDepositAmount)
    self.totalSharesBasisPoints -= (self.funds[_lender].sharesBasisPoints - newLenderSharesAmount)

    self.funds[_lender] = InvestorFunds(
        {
            currentAmountDeposited: newDepositAmount,
            totalAmountDeposited: self.funds[_lender].totalAmountDeposited,
            totalAmountWithdrawn: self.funds[_lender].totalAmountWithdrawn + _amount,
            sharesBasisPoints: newLenderSharesAmount,
            activeForRewards: True
        }
    )

    if self.funds[_lender].currentAmountDeposited == 0:
        self.funds[_lender].activeForRewards = False
        self.activeLenders -= 1

    self.fundsAvailable -= _amount

    return IERC20(self.erc20TokenContract).transfer(_lender, _amount)


@external
def sendFunds(_to: address, _amount: uint256) -> bool:
  # _amount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "msg.sender is not LP peripheral"
    assert _to != ZERO_ADDRESS, "_to is the zero address"
    assert _amount > 0, "_amount has to be higher than 0"
    assert IERC20(self.erc20TokenContract).balanceOf(self) >= _amount, "Insufficient balance"

    self.fundsAvailable -= _amount
    self.fundsInvested += _amount
    self.totalFundsInvested += _amount

    return IERC20(self.erc20TokenContract).transfer(_to, _amount)


@external
def receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256) -> bool:
    # _amount and _rewardsAmount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "msg.sender is not LP peripheral"
    assert _borrower != ZERO_ADDRESS, "_borrower is the zero address"
    assert _amount + _rewardsAmount > 0, "Amount has to be higher than 0"
    assert _amount <= self.fundsInvested, "Too much funds received"
    assert self._fundsAreAllowed(_borrower, self, _amount), "Not enough funds allowed"

    self.fundsAvailable += _amount + _rewardsAmount
    self.fundsInvested -= _amount
    self.totalRewards += _rewardsAmount

    return IERC20(self.erc20TokenContract).transferFrom(_borrower, self, _amount + _rewardsAmount)


@external
def transferProtocolFees(_borrower: address, _protocolWallet: address, _amount: uint256) -> bool:
    # _amount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "msg.sender is not LP peripheral"
    assert _protocolWallet != ZERO_ADDRESS, "_protocolWallet is the zero address"
    assert _borrower != ZERO_ADDRESS, "_borrower is the zero address"
    assert _amount > 0, "_amount should be higher than 0"

    return IERC20(self.erc20TokenContract).transferFrom(_borrower, _protocolWallet, _amount)
