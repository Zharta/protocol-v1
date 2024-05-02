# @version 0.3.10


# Interfaces

from vyper.interfaces import ERC20 as IERC20

interface ILegacyLendingPoolCore:
    def lockPeriodEnd(_lender: address) -> uint256: view
    def funds(arg0: address) -> LegacyInvestorFunds: view
    def lendersArray() -> DynArray[address, 2**50]: view

# Structs

struct InvestorLock:
    lockPeriodEnd: uint256
    lockPeriodAmount: uint256


struct LegacyInvestorFunds:
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

event LendingPoolPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address


# Global variables

owner: public(address)
proposedOwner: public(address)

lendingPoolPeripheral: public(address)
erc20TokenContract: public(address)

investorLocks: public(HashMap[address, InvestorLock])
migrationDone: bool

##### INTERNAL METHODS #####



##### EXTERNAL METHODS - VIEW #####



##### EXTERNAL METHODS - NON-VIEW #####

@external
def __init__(_erc20TokenContract: address):
    assert _erc20TokenContract != empty(address), "The address is the zero address"
    self.owner = msg.sender
    self.erc20TokenContract = _erc20TokenContract
    self.migrationDone = False


@external
def migrate(_lendingPoolCoreAddress: address, _lenders: DynArray[address, 100]):
    assert not self.migrationDone, "migration already done"
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _lendingPoolCoreAddress != empty(address), "_address is the zero address"
    assert _lendingPoolCoreAddress.is_contract, "LPCore is not a contract"
    for lender in _lenders:
        investorFunds: LegacyInvestorFunds = ILegacyLendingPoolCore(_lendingPoolCoreAddress).funds(lender)
        self.investorLocks[lender] = InvestorLock({
            lockPeriodEnd: investorFunds.lockPeriodEnd,
            lockPeriodAmount: investorFunds.currentAmountDeposited
        })
    self.migrationDone = True


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
def setLendingPoolPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero address"

    log LendingPoolPeripheralAddressSet(
        self.erc20TokenContract,
        self.lendingPoolPeripheral,
        _address,
        self.erc20TokenContract
    )

    self.lendingPoolPeripheral = _address


@external
def setInvestorLock(_lender: address, _amount: uint256, _lockPeriodEnd: uint256):
    # _amount should be passed in wei
    assert msg.sender == self.lendingPoolPeripheral, "msg.sender is not LP peripheral"
    assert _lender != empty(address), "The _address is the zero address"

    self.investorLocks[_lender] = InvestorLock({
        lockPeriodEnd: _lockPeriodEnd,
        lockPeriodAmount: _amount
    })
