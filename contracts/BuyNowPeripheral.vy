# @version ^0.3.3


# Interfaces

from vyper.interfaces import ERC20 as IERC20
from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721
from interfaces import IBuyNowCore
from interfaces import ILendingPoolPeripheral
from interfaces import ICollateralVaultPeripheral

interface ILoansCore:
    def getLoanCollaterals(_borrower: address, _loanId: uint256) -> DynArray[Collateral, 100]: view
    def getLoanDefaulted(_borrower: address, _loanId: uint256) -> bool: view

# interface ILendingPoolCore:
#     def getLenderCurrentAmountDeposited(_lender: address) -> uint256: view


# Structs

struct Collateral:
    contractAddress: address
    tokenId: uint256

struct InvestorFunds:
    currentAmountDeposited: uint256
    totalAmountDeposited: uint256
    totalAmountWithdrawn: uint256
    sharesBasisPoints: uint256
    activeForRewards: bool

struct Liquidation:
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    buyNowPeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    borrower: address
    erc20TokenContract: address
    inAuction: bool


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

event GracePeriodDurationChanged:
    currentValue: uint256
    newValue: uint256

event BuyNowPeriodDurationChanged:
    currentValue: uint256
    newValue: uint256

event AuctionPeriodDurationChanged:
    currentValue: uint256
    newValue: uint256

event BuyNowCoreAddressSet:
    currentValue: address
    newValue: address

event LoansCoreAddressAdded:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LoansCoreAddressRemoved:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    erc20TokenContract: address

event LendingPoolPeripheralAddressAdded:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LendingPoolPeripheralAddressRemoved:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    erc20TokenContract: address

event CollateralVaultPeripheralAddressSet:
    currentValue: address
    newValue: address

event LiquidationAdded:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address

event LiquidationRemoved:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address

event NFTPurchased:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    amount: uint256
    erc20TokenContract: address


# Global variables

owner: public(address)
proposedOwner: public(address)

gracePeriodDuration: public(uint256)
buyNowPeriodDuration: public(uint256)
auctionPeriodDuration: public(uint256)

buyNowCoreAddress: public(address)
loansCoreAddresses: public(HashMap[address, address]) # mapping between ERC20 contract and LoansCore
lendingPoolPeripheralAddresses: public(HashMap[address, address]) # mapping between ERC20 contract and LendingPoolCore
collateralVaultPeripheralAddress: public(address)

lenderMinDepositAmount: public(uint256)

##### INTERNAL METHODS #####

@internal
def _isCollateralInArray(_collateralAddress: address, _tokenId: uint256, _collaterals: DynArray[Collateral, 100]) -> bool:
    for collateral in _collaterals:
        if collateral.contractAddress == _collateralAddress and collateral.tokenId == _tokenId:
            return True
    return False


@pure
@internal
def _computeNFTPrice(principal: uint256, interestAmount: uint256, apr: uint256, days: uint256) -> uint256:
    return principal + interestAmount + (principal * apr * days) / 365


@pure
@internal
def _computeInterestAmount(principal: uint256, interestAmount: uint256, apr: uint256, days: uint256) -> uint256:
    return interestAmount + (principal * apr * days) / 365


##### EXTERNAL METHODS - VIEW #####

@view
@external
def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    return IBuyNowCore(self.buyNowCoreAddress).getLiquidation(_collateralAddress, _tokenId)


##### EXTERNAL METHODS - WRITE #####
@external
def __init__(_buyNowCoreAddress: address, _gracePeriodDuration: uint256, _buyNowPeriodDuration: uint256, _auctionPeriodDuration: uint256):
    assert _buyNowCoreAddress != ZERO_ADDRESS, "address is the zero address"
    assert _buyNowCoreAddress.is_contract, "address is not a contract"
    assert _gracePeriodDuration > 0, "duration is 0"
    assert _buyNowPeriodDuration > 0, "duration is 0"
    assert _auctionPeriodDuration > 0, "duration is 0"

    self.owner = msg.sender
    self.buyNowCoreAddress = _buyNowCoreAddress
    self.gracePeriodDuration = _gracePeriodDuration
    self.buyNowPeriodDuration = _buyNowPeriodDuration
    self.auctionPeriodDuration = _auctionPeriodDuration


@external
def proposeOwner(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address it the zero address"
    assert self.owner != _address, "proposed owner addr is the owner"
    assert self.proposedOwner != _address, "proposed owner addr is the same"

    self.proposedOwner = _address

    log OwnerProposed(
        self.owner,
        _address,
        self.owner,
        _address,
    )


@external
def claimOwnership():
    assert msg.sender == self.proposedOwner, "msg.sender is not the proposed"

    log OwnershipTransferred(
        self.owner,
        self.proposedOwner,
        self.owner,
        self.proposedOwner,
    )

    self.owner = self.proposedOwner
    self.proposedOwner = ZERO_ADDRESS


@external
def setGracePeriodDuration(_duration: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _duration > 0, "duration is 0"
    assert _duration != self.gracePeriodDuration, "new value is the same"

    log GracePeriodDurationChanged(
        self.gracePeriodDuration,
        _duration
    )

    self.gracePeriodDuration = _duration


@external
def setBuyNowPeriodDuration(_duration: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _duration > 0, "duration is 0"
    assert _duration != self.buyNowPeriodDuration, "new value is the same"

    log BuyNowPeriodDurationChanged(
        self.buyNowPeriodDuration,
        _duration
    )

    self.buyNowPeriodDuration = _duration


@external
def setAuctionPeriodDuration(_duration: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _duration > 0, "duration is 0"
    assert _duration != self.auctionPeriodDuration, "new value is the same"

    log AuctionPeriodDurationChanged(
        self.auctionPeriodDuration,
        _duration
    )

    self.auctionPeriodDuration = _duration


@external
def setBuyNowCoreAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert self.buyNowCoreAddress != _address, "new value is the same"

    log BuyNowCoreAddressSet(
        self.buyNowCoreAddress,
        _address,
    )

    self.buyNowCoreAddress = _address


@external
def addLoansCoreAddress(_erc20TokenContract: address, _address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.loansCoreAddresses[_erc20TokenContract] != _address, "new value is the same"

    log LoansCoreAddressAdded(
        _erc20TokenContract,
        self.loansCoreAddresses[_erc20TokenContract],
        _address,
        _erc20TokenContract
    )

    self.loansCoreAddresses[_erc20TokenContract] = _address


@external
def removeLoansCoreAddress(_erc20TokenContract: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.loansCoreAddresses[_erc20TokenContract] != ZERO_ADDRESS, "address not found"

    log LoansCoreAddressRemoved(
        _erc20TokenContract,
        self.loansCoreAddresses[_erc20TokenContract],
        _erc20TokenContract
    )

    self.loansCoreAddresses[_erc20TokenContract] = ZERO_ADDRESS


@external
def addLendingPoolPeripheralAddress(_erc20TokenContract: address, _address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.lendingPoolPeripheralAddresses[_erc20TokenContract] != _address, "new value is the same"

    log LendingPoolPeripheralAddressAdded(
        _erc20TokenContract,
        self.lendingPoolPeripheralAddresses[_erc20TokenContract],
        _address,
        _erc20TokenContract
    )

    self.lendingPoolPeripheralAddresses[_erc20TokenContract] = _address


@external
def removeLendingPoolPeripheralAddress(_erc20TokenContract: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.lendingPoolPeripheralAddresses[_erc20TokenContract] != ZERO_ADDRESS, "address not found"

    log LendingPoolPeripheralAddressRemoved(
        _erc20TokenContract,
        self.lendingPoolPeripheralAddresses[_erc20TokenContract],
        _erc20TokenContract
    )

    self.lendingPoolPeripheralAddresses[_erc20TokenContract] = ZERO_ADDRESS


@external
def setCollateralVaultPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != ZERO_ADDRESS, "address is the zero addr"
    assert self.collateralVaultPeripheralAddress != _address, "new value is the same"

    log CollateralVaultPeripheralAddressSet(
        self.collateralVaultPeripheralAddress,
        _address
    )

    self.collateralVaultPeripheralAddress = _address


@external
def addLiquidation(
    _collateralAddress: address,
    _tokenId: uint256,
    _principal: uint256,
    _interestAmount: uint256,
    _apr: uint256,
    _borrower: address,
    _loanId: uint256,
    _erc20TokenContract: address
):
    assert _collateralAddress != ZERO_ADDRESS, "collat addr is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"
    assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"
    assert _principal > 0, "principal is 0"
    assert _interestAmount > 0, "interestAmount is 0"
    assert _apr > 0, "apr is 0"
    assert _borrower != ZERO_ADDRESS, "borrower is the zero addr"
    assert _erc20TokenContract != ZERO_ADDRESS, "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert ILoansCore(self.loansCoreAddresses[_erc20TokenContract]).getLoanDefaulted(_borrower, _loanId), "loan is not defaulted"
    assert self._isCollateralInArray(
        _collateralAddress,
        _tokenId,
        ILoansCore(self.loansCoreAddresses[_erc20TokenContract]).getLoanCollaterals(_borrower, _loanId)
    ), "collateral not in loan"

    IBuyNowCore(self.buyNowCoreAddress).addLiquidation(
        _collateralAddress,
        _tokenId,
        block.timestamp,
        block.timestamp + self.gracePeriodDuration,
        block.timestamp + self.gracePeriodDuration + self.buyNowPeriodDuration,
        _principal,
        _interestAmount,
        _apr,
        _borrower,
        _erc20TokenContract
    )

    log LiquidationAdded(
        _erc20TokenContract,
        _collateralAddress,
        _collateralAddress,
        _tokenId,
        _erc20TokenContract
    )


@external
def buyNFT(_collateralAddress: address, _tokenId: uint256):
    assert _collateralAddress != ZERO_ADDRESS, "collat addr is the zero addr"
    assert _collateralAddress.is_contract, "collat addr is not a contract"
    assert IERC165(_collateralAddress).supportsInterface(0x80ac58cd), "collat addr is not a ERC721"
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"

    liquidation: Liquidation = IBuyNowCore(self.buyNowCoreAddress).getLiquidation(_collateralAddress, _tokenId)
    
    if block.timestamp <= liquidation.gracePeriodMaturity:
        assert msg.sender == liquidation.borrower, "msg.sender is not borrower"
    elif block.timestamp <= liquidation.buyNowPeriodMaturity:
        assert ILendingPoolPeripheral(
            self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]
        ).lenderFunds(msg.sender).currentAmountDeposited > self.lenderMinDepositAmount, "msg.sender is not a lender"
    else:
        raise "liquidation out of buying period"
    
    assert not liquidation.inAuction, "liquidation is in auction"

    nftPrice: uint256 = 0
    days: uint256 = 0
    if block.timestamp <= liquidation.gracePeriodMaturity:
        nftPrice = self._computeNFTPrice(liquidation.principal, liquidation.interestAmount, liquidation.apr, 2)
        days = 2
    elif block.timestamp <= liquidation.buyNowPeriodMaturity:
        nftPrice = self._computeNFTPrice(liquidation.principal, liquidation.interestAmount, liquidation.apr, 17)
        days = 17

    IBuyNowCore(self.buyNowCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

    log LiquidationRemoved(
        liquidation.erc20TokenContract,
        liquidation.collateralAddress,
        liquidation.collateralAddress,
        liquidation.tokenId,
        liquidation.erc20TokenContract
    )

    ILendingPoolPeripheral(self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]).receiveFundsFromLiquidation(
        msg.sender,
        liquidation.principal,
        self._computeInterestAmount(liquidation.principal, liquidation.interestAmount, liquidation.apr, days)
    )

    ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(msg.sender, _collateralAddress, _tokenId)

    log NFTPurchased(
        liquidation.erc20TokenContract,
        _collateralAddress,
        _collateralAddress,
        _tokenId,
        nftPrice,
        liquidation.erc20TokenContract
    )


@external
def liquidateNFTXInGracePeriod():
    pass


@external
def liquidateNFTX():
    pass


@external
def liquidateOpenSea():
    pass



