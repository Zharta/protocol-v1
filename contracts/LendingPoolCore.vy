# @version ^0.3.2


# Interfaces

interface IERC20Token:
    def balanceOf(_owner: address) -> uint256: view
    def allowance(_owner: address, _spender: address) -> uint256: view
    def transfer(_recipient: address, _amount: uint256) -> bool: nonpayable
    def transferFrom(_sender: address, _recipient: address, _amount: uint256) -> bool: nonpayable
    def safeTransferFrom(_sender: address, _recipient: address, _amount: uint256): nonpayable


# Structs

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool


# Events

event Compound:
    wallet: address
    amount: uint256
    erc20TokenContract: address


# Global variables

owner: public(address)
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
    amountAllowed: uint256 = IERC20Token(self.erc20TokenContract).allowance(_owner, _spender)
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
    _lendingPoolPeripheral: address,
    _erc20TokenContract: address
):
    self.owner = msg.sender
    self.lendingPoolPeripheral = _lendingPoolPeripheral
    self.erc20TokenContract = _erc20TokenContract


@external
def changeOwnership(_newOwner: address) -> address:
    assert msg.sender == self.owner, "Only the owner can change the contract ownership"

    self.owner = _newOwner

    return self.owner


@external
def deposit(_lender: address, _amount: uint256) -> bool:
    # _amount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "Only defined lending pool peripheral can deposit"
    assert _amount > 0, "Amount deposited has to be higher than 0"

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

    return True


@external
def transferDeposit(_lender: address, _amount: uint256) -> bool:
    # _amount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "Only defined lending pool peripheral can request a deposit transfer"
    assert _lender != ZERO_ADDRESS, "The lender can not be the empty address"
    assert _amount > 0, "Amount deposited has to be higher than 0"
    assert self._fundsAreAllowed(_lender, self, _amount), "Insufficient funds allowed to be transfered"

    return IERC20Token(self.erc20TokenContract).transferFrom(_lender, self, _amount)


@external
def withdraw(_lender: address, _amount: uint256) -> bool:
    # _amount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "Only defined lending pool peripheral can withdraw"
    assert _amount > 0, "Amount withdrawn has to be higher than 0"
    assert _lender != ZERO_ADDRESS, "The lender can not be the empty address"
    assert self._computeWithdrawableAmount(_lender) >= _amount, "The lender has less funds deposited than the amount requested"
    assert self.fundsAvailable >= _amount, "Not enough funds in the pool to be withdrawn"

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

    if not IERC20Token(self.erc20TokenContract).transfer(_lender, _amount):
        raise "Withdrawal transfer error"

    return True


@external
def sendFunds(_to: address, _amount: uint256) -> bool:
  # _amount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "Only defined lending pool peripheral can send funds"
    assert _amount > 0, "The amount to send should be higher than 0"
    assert IERC20Token(self.erc20TokenContract).balanceOf(self) >= _amount, "Insufficient balance"

    if not IERC20Token(self.erc20TokenContract).transfer(_to, _amount):
        raise "Error sending funds"

    self.fundsAvailable -= _amount
    self.fundsInvested += _amount
    self.totalFundsInvested += _amount

    return True


@external
def receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256) -> bool:
    # _amount and _rewardsAmount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "Only defined lending pool peripheral can receive funds"
    assert _amount + _rewardsAmount > 0, "The sent value should be higher than 0"
    assert self._fundsAreAllowed(_borrower, self, _amount), "Insufficient funds allowed to be transfered"

    if not IERC20Token(self.erc20TokenContract).transferFrom(_borrower, self, _amount + _rewardsAmount):
        return False

    return True


@external
def transferProtocolFees(_protocolWallet: address, _amount: uint256) -> bool:
    # _amount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "Only defined lending pool peripheral can ask for protocol fees"
    assert _amount > 0, "The requested value should be higher than 0"

    if not IERC20Token(self.erc20TokenContract).transfer(_protocolWallet, _amount):
        return False

    return True


@external
def updateLiquidity(_amount: uint256, _rewardsAmount: uint256) -> bool:
    # _amount and _rewardsAmount should be passed in wei

    assert msg.sender == self.lendingPoolPeripheral, "Only defined lending pool peripheral can update liquidity data"
    assert _amount + _rewardsAmount > 0, "The sent value should be higher than 0"
    assert _amount <= self.fundsInvested, "There are more funds being received than expected by the deposited funds variable"

    self.fundsAvailable += _amount + _rewardsAmount
    self.fundsInvested -= _amount
    self.totalRewards += _rewardsAmount

    return True


@external
@payable
def __default__():
  if msg.value > 0:
    send(msg.sender, msg.value)
