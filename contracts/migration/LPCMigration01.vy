# @version ^0.3.6

# Interfaces

from interfaces import ILendingPoolCore

# Structs

interface ILegacyLendingPoolCore:
    def lockPeriodEnd(_lender: address) -> uint256: view
    def funds(arg0: address) -> LegacyInvestorFunds: view
    def lendersArray() -> DynArray[address, 2**5]: view

struct LegacyInvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    lockPeriodEnd: uint256
    activeForRewards: bool

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    lockPeriodEnd: uint256
    activeForRewards: bool

# Events


# Global variables

owner: public(address)
oldContract: public(address)
newContract: public(address)

##### INTERNAL METHODS #####


##### EXTERNAL METHODS - VIEW #####


##### EXTERNAL METHODS - WRITE #####

@external
def __init__(_from: address, _to: address):
    assert _from != empty(address), "address it the zero address"
    assert _to != empty(address), "address it the zero address"
    self.owner = msg.sender
    self.oldContract = _from
    self.newContract = _to


@external
def migrate():
    assert msg.sender == self.owner, "msg.sender is not the owner"

    ILendingPoolCore(self.oldContract).claimOwnership()
    ILendingPoolCore(self.newContract).claimOwnership()

    ILendingPoolCore(self.newContract).migrate(self.oldContract)

    ILendingPoolCore(self.newContract).proposeOwner(self.owner)

    selfdestruct(self.owner)
