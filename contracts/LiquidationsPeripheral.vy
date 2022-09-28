# @version ^0.3.6


# Interfaces

from vyper.interfaces import ERC20 as IERC20
from vyper.interfaces import ERC721 as IERC721
from interfaces import ILiquidationsCore
from interfaces import ILoansCore
from interfaces import ILendingPoolPeripheral
from interfaces import ICollateralVaultPeripheral

interface ISushiRouter:
    def getAmountsOut(amountIn: uint256, path: DynArray[address, 2]) -> DynArray[uint256, 2]: view

interface INFTXVaultFactory:
    def vaultsForAsset(assetAddress: address) -> DynArray[address, 20]: view

interface INFTXVault:
    def vaultId() -> uint256: view
    def allValidNFTs(tokenIds: DynArray[uint256, 1]) -> bool: view

interface INFTXMarketplaceZap:
    def mintAndSell721WETH(vaultId: uint256, ids: DynArray[uint256, 1], minWethOut: uint256, path: DynArray[address, 2], to: address): nonpayable


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
    lockPeriodEnd: uint256
    activeForRewards: bool

struct Liquidation:
    lid: bytes32
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    lenderPeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    gracePeriodPrice: uint256
    lenderPeriodPrice: uint256
    borrower: address
    loanId: uint256
    loansCoreContract: address
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

event LendersPeriodDurationChanged:
    currentValue: uint256
    newValue: uint256

event AuctionPeriodDurationChanged:
    currentValue: uint256
    newValue: uint256

event LiquidationsCoreAddressSet:
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

event NFTXVaultFactoryAddressSet:
    currentValue: address
    newValue: address

event NFTXMarketplaceZapAddressSet:
    currentValue: address
    newValue: address

event SushiRouterAddressSet:
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
    method: String[20] # possible values: GRACE_PERIOD, LENDER_PERIOD, BACKSTOP_PERIOD_NFTX

event AdminWithdrawal:
    collateralAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    wallet: address


# Global variables

owner: public(address)
proposedOwner: public(address)

gracePeriodDuration: public(uint256)
lenderPeriodDuration: public(uint256)
auctionPeriodDuration: public(uint256)

liquidationsCoreAddress: public(address)
loansCoreAddresses: public(HashMap[address, address]) # mapping between ERC20 contract and LoansCore
lendingPoolPeripheralAddresses: public(HashMap[address, address]) # mapping between ERC20 contract and LendingPoolCore
collateralVaultPeripheralAddress: public(address)
nftxVaultFactoryAddress: public(address)
nftxMarketplaceZapAddress: public(address)
sushiRouterAddress: public(address)
wethAddress: immutable(address)

lenderMinDepositAmount: public(uint256)

##### INTERNAL METHODS #####

@pure
@internal
def _computeNFTPrice(principal: uint256, interestAmount: uint256, apr: uint256, duration: uint256) -> uint256:
    return principal + interestAmount + (principal * apr * duration) / 315360000000 # 315360000000 = 365 days in seconds * 10000 base percentage points


@pure
@internal
def _computeLoanInterestAmount(principal: uint256, interest: uint256, duration: uint256) -> uint256:
    return principal * interest * duration / 25920000000 # 25920000000 = 30 days * 10000 base percentage points


@pure
@internal
def _computeLiquidationInterestAmount(principal: uint256, interestAmount: uint256, apr: uint256, duration: uint256) -> uint256:
    return interestAmount + (principal * apr * duration) / 315360000000 # 315360000000 = 365 days in seconds * 10000 base percentage points


@view
@internal
def _getNFTXVaultAddrFromCollateralAddr(_collateralAddress: address) -> address:
    vault_addrs: DynArray[address, 20] = INFTXVaultFactory(self.nftxVaultFactoryAddress).vaultsForAsset(_collateralAddress)
    
    if len(vault_addrs) == 0:
        return empty(address)
    
    return vault_addrs[len(vault_addrs) - 1]


@view
@internal
def _getNFTXVaultIdFromCollateralAddr(_collateralAddress: address) -> uint256:
    vault_addr: address = self._getNFTXVaultAddrFromCollateralAddr(_collateralAddress)
    return INFTXVault(vault_addr).vaultId()


@view
@internal
def _getAutoLiquidationPrice(_collateralAddress: address, _tokenId: uint256) -> uint256:
    vault_addr: address = self._getNFTXVaultAddrFromCollateralAddr(_collateralAddress)

    if vault_addr == empty(address):
        return 0

    if not INFTXVault(vault_addr).allValidNFTs([_tokenId]):
        return 0

    amountsOut: DynArray[uint256, 2] = ISushiRouter(self.sushiRouterAddress).getAmountsOut(as_wei_value(0.9, "ether"), [vault_addr, wethAddress])

    return amountsOut[1]


@pure
@internal
def _isCollateralInArray(_collaterals: DynArray[Collateral, 100], _collateralAddress: address, _tokenId: uint256) -> bool:
    for collateral in _collaterals:
        if collateral.contractAddress == _collateralAddress and collateral.tokenId == _tokenId:
            return True
    return False


@pure
@internal
def _getCollateralAmount(_collaterals: DynArray[Collateral, 100], _collateralAddress: address, _tokenId: uint256) -> uint256:
    for collateral in _collaterals:
        if collateral.contractAddress == _collateralAddress and collateral.tokenId == _tokenId:
            return collateral.amount
    return max_value(uint256)


##### EXTERNAL METHODS - VIEW #####

@view
@external
def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    return ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)


##### EXTERNAL METHODS - WRITE #####
@external
def __init__(_liquidationsCoreAddress: address, _gracePeriodDuration: uint256, _lenderPeriodDuration: uint256, _auctionPeriodDuration: uint256, _wethAddress: address):
    assert _liquidationsCoreAddress != empty(address), "address is the zero address"
    assert _liquidationsCoreAddress.is_contract, "address is not a contract"
    assert _wethAddress != empty(address), "address is the zero address"
    assert _wethAddress.is_contract, "address is not a contract"
    assert _gracePeriodDuration > 0, "duration is 0"
    assert _lenderPeriodDuration > 0, "duration is 0"
    assert _auctionPeriodDuration > 0, "duration is 0"

    self.owner = msg.sender
    self.liquidationsCoreAddress = _liquidationsCoreAddress
    self.gracePeriodDuration = _gracePeriodDuration
    self.lenderPeriodDuration = _lenderPeriodDuration
    self.auctionPeriodDuration = _auctionPeriodDuration
    wethAddress = _wethAddress


@external
def proposeOwner(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address it the zero address"
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
    self.proposedOwner = empty(address)


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
def setLendersPeriodDuration(_duration: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _duration > 0, "duration is 0"
    assert _duration != self.lenderPeriodDuration, "new value is the same"

    log LendersPeriodDurationChanged(
        self.lenderPeriodDuration,
        _duration
    )

    self.lenderPeriodDuration = _duration


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
def setLiquidationsCoreAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert self.liquidationsCoreAddress != _address, "new value is the same"

    log LiquidationsCoreAddressSet(
        self.liquidationsCoreAddress,
        _address,
    )

    self.liquidationsCoreAddress = _address


@external
def addLoansCoreAddress(_erc20TokenContract: address, _address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
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
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.loansCoreAddresses[_erc20TokenContract] != empty(address), "address not found"

    log LoansCoreAddressRemoved(
        _erc20TokenContract,
        self.loansCoreAddresses[_erc20TokenContract],
        _erc20TokenContract
    )

    self.loansCoreAddresses[_erc20TokenContract] = empty(address)


@external
def addLendingPoolPeripheralAddress(_erc20TokenContract: address, _address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert _address.is_contract, "address is not a contract"
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
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
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
    assert _erc20TokenContract.is_contract, "erc20TokenAddr is not a contract"
    assert self.lendingPoolPeripheralAddresses[_erc20TokenContract] != empty(address), "address not found"

    log LendingPoolPeripheralAddressRemoved(
        _erc20TokenContract,
        self.lendingPoolPeripheralAddresses[_erc20TokenContract],
        _erc20TokenContract
    )

    self.lendingPoolPeripheralAddresses[_erc20TokenContract] = empty(address)


@external
def setCollateralVaultPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert self.collateralVaultPeripheralAddress != _address, "new value is the same"

    log CollateralVaultPeripheralAddressSet(
        self.collateralVaultPeripheralAddress,
        _address
    )

    self.collateralVaultPeripheralAddress = _address


@external
def setNFTXVaultFactoryAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert self.nftxVaultFactoryAddress != _address, "new value is the same"

    log NFTXVaultFactoryAddressSet(
        self.nftxVaultFactoryAddress,
        _address
    )

    self.nftxVaultFactoryAddress = _address


@external
def setNFTXMarketplaceZapAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert self.nftxMarketplaceZapAddress != _address, "new value is the same"

    log NFTXMarketplaceZapAddressSet(
        self.nftxMarketplaceZapAddress,
        _address
    )

    self.nftxMarketplaceZapAddress = _address


@external
def setSushiRouterAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"
    assert self.sushiRouterAddress != _address, "new value is the same"

    log SushiRouterAddressSet(
        self.sushiRouterAddress,
        _address
    )

    self.sushiRouterAddress = _address


@external
def addLiquidation(
    _collateralAddress: address,
    _tokenId: uint256,
    _borrower: address,
    _loanId: uint256,
    _erc20TokenContract: address
):
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"
    
    borrowerLoan: Loan = ILoansCore(self.loansCoreAddresses[_erc20TokenContract]).getLoan(_borrower, _loanId)
    assert borrowerLoan.defaulted, "loan is not defaulted"
    assert self._isCollateralInArray(borrowerLoan.collaterals, _collateralAddress, _tokenId), "collateral not in loan"

    principal: uint256 = self._getCollateralAmount(borrowerLoan.collaterals, _collateralAddress, _tokenId)
    interestAmount: uint256 = self._computeLoanInterestAmount(
        principal,
        borrowerLoan.interest,
        borrowerLoan.maturity - borrowerLoan.startTime
    )
    # # APR from loan duration (maturity)
    apr: uint256 = borrowerLoan.interest * 12

    gracePeriodPrice: uint256 = self._computeNFTPrice(principal, interestAmount, apr, self.gracePeriodDuration)
    protocolPrice: uint256 = self._computeNFTPrice(principal, interestAmount, apr, self.gracePeriodDuration + self.lenderPeriodDuration)
    autoLiquidationPrice: uint256 = self._getAutoLiquidationPrice(_collateralAddress, _tokenId)
    # autoLiquidationPrice: uint256 = 0
    lenderPeriodPrice: uint256 = 0

    if protocolPrice > autoLiquidationPrice:
        lenderPeriodPrice = protocolPrice
    else:
        lenderPeriodPrice = autoLiquidationPrice

    lid: bytes32 = ILiquidationsCore(self.liquidationsCoreAddress).addLiquidation(
        _collateralAddress,
        _tokenId,
        block.timestamp,
        block.timestamp + self.gracePeriodDuration,
        block.timestamp + self.gracePeriodDuration + self.lenderPeriodDuration,
        principal,
        interestAmount,
        apr,
        gracePeriodPrice,
        lenderPeriodPrice,
        _borrower,
        _loanId,
        self.loansCoreAddresses[_erc20TokenContract],
        _erc20TokenContract
    )

    log LiquidationAdded(
        _erc20TokenContract,
        _collateralAddress,
        lid,
        _collateralAddress,
        _tokenId,
        _erc20TokenContract,
        gracePeriodPrice,
        lenderPeriodPrice,
        block.timestamp + self.gracePeriodDuration,
        block.timestamp + self.gracePeriodDuration + self.lenderPeriodDuration,
        self.loansCoreAddresses[_erc20TokenContract],
        _loanId,
        _borrower
    )


@external
def payLoanLiquidationsGracePeriod(_loanId: uint256, _erc20TokenContract: address):
    loan: Loan = ILoansCore(self.loansCoreAddresses[_erc20TokenContract]).getLoan(msg.sender, _loanId)

    assert loan.defaulted, "loan is not defaulted"

    for collateral in loan.collaterals:
        liquidation: Liquidation = ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(collateral.contractAddress, collateral.tokenId)

        assert block.timestamp <= liquidation.gracePeriodMaturity, "liquidation out of grace period"

        ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(collateral.contractAddress, collateral.tokenId)

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

        ILendingPoolPeripheral(self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]).receiveFundsFromLiquidation(
            liquidation.borrower,
            liquidation.principal,
            liquidation.gracePeriodPrice - liquidation.principal,
            True,
            "liquidation_grace_period"
        )

        ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(
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
            "GRACE_PERIOD"
        )


@external
def buyNFTGracePeriod(_collateralAddress: address, _tokenId: uint256):
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"
    
    liquidation: Liquidation = ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)
    assert block.timestamp <= liquidation.gracePeriodMaturity, "liquidation out of grace period"
    assert msg.sender == liquidation.borrower, "msg.sender is not borrower"

    ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

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

    ILendingPoolPeripheral(self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]).receiveFundsFromLiquidation(
        liquidation.borrower,
        liquidation.principal,
        liquidation.gracePeriodPrice - liquidation.principal,
        True,
        "liquidation_grace_period"
    )

    ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(msg.sender, _collateralAddress, _tokenId)

    log NFTPurchased(
        liquidation.erc20TokenContract,
        _collateralAddress,
        msg.sender,
        liquidation.lid,
        _collateralAddress,
        _tokenId,
        liquidation.gracePeriodPrice,
        msg.sender,
        liquidation.erc20TokenContract,
        "GRACE_PERIOD"
    )


@external
def buyNFTLenderPeriod(_collateralAddress: address, _tokenId: uint256):
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"
    
    liquidation: Liquidation = ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)
    assert block.timestamp > liquidation.gracePeriodMaturity, "liquidation in grace period"
    assert block.timestamp <= liquidation.lenderPeriodMaturity, "liquidation out of lender period"

    ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

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

    fundsSender: address = msg.sender
    lenderPeriodInterestAmount: uint256 = self._computeLiquidationInterestAmount(
        liquidation.principal,
        liquidation.interestAmount,
        liquidation.apr,
        self.gracePeriodDuration + self.lenderPeriodDuration
    )
    if liquidation.lenderPeriodPrice > liquidation.principal + lenderPeriodInterestAmount:
        fundsSender = self
        IERC20(liquidation.erc20TokenContract).transferFrom(
            msg.sender,
            self,
            liquidation.lenderPeriodPrice
        )
        IERC20(liquidation.erc20TokenContract).approve(
            self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract],
            liquidation.principal + lenderPeriodInterestAmount
        )
        IERC20(liquidation.erc20TokenContract).transfer(
            liquidation.borrower,
            liquidation.lenderPeriodPrice - (liquidation.principal + lenderPeriodInterestAmount)
        )

    ILendingPoolPeripheral(self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]).receiveFundsFromLiquidation(
        fundsSender,
        liquidation.principal,
        lenderPeriodInterestAmount,
        True,
        "liquidation_lenders_period"
    )

    ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(msg.sender, _collateralAddress, _tokenId)

    log NFTPurchased(
        liquidation.erc20TokenContract,
        _collateralAddress,
        msg.sender,
        liquidation.lid,
        _collateralAddress,
        _tokenId,
        liquidation.lenderPeriodPrice,
        msg.sender,
        liquidation.erc20TokenContract,
        "LENDER_PERIOD"
    )


@external
def liquidateNFTX(_collateralAddress: address, _tokenId: uint256):
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"

    liquidation: Liquidation = ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)
    assert block.timestamp > liquidation.lenderPeriodMaturity, "liquidation within lender period"

    ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

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

    autoLiquidationPrice: uint256 = self._getAutoLiquidationPrice(_collateralAddress, _tokenId)

    assert autoLiquidationPrice > 0, "NFTX liq price is 0 or none"

    ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).approveBackstopBuyer(
        self._getNFTXVaultAddrFromCollateralAddr(_collateralAddress),
        _collateralAddress,
        _tokenId
    )

    INFTXMarketplaceZap(self.nftxMarketplaceZapAddress).mintAndSell721WETH(
        self._getNFTXVaultIdFromCollateralAddr(_collateralAddress),
        [_tokenId],
        autoLiquidationPrice,
        [wethAddress, self._getNFTXVaultAddrFromCollateralAddr(_collateralAddress)],
        self
    )

    # TODO: swap WETH for liquidation.erc20TokenContract if liquidation.erc20TokenContract != WETH
    # TODO: recompute "autoLiquidationPrice" to be in liquidation.erc20TokenContract if liquidation.erc20TokenContract != WETH

    lp_peripheral_address: address = self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]

    IERC20(liquidation.erc20TokenContract).approve(
        lp_peripheral_address,
        autoLiquidationPrice
    )

    principal: uint256 = liquidation.principal
    interestAmount: uint256 = 0
    distributeToProtocol: bool = True

    if autoLiquidationPrice < liquidation.principal: # LP loss scenario
        principal = autoLiquidationPrice    
    elif autoLiquidationPrice > liquidation.principal:
        interestAmount = autoLiquidationPrice - liquidation.principal
        protocolFeesShare: uint256 = ILendingPoolPeripheral(lp_peripheral_address).protocolFeesShare()
        if interestAmount <= liquidation.interestAmount * (10000 - protocolFeesShare) / 10000: # LP interest less than expected and/or protocol interest loss
            distributeToProtocol = False

    ILendingPoolPeripheral(lp_peripheral_address).receiveFundsFromLiquidation(
        self,
        principal,
        interestAmount,
        distributeToProtocol,
        "liquidation_nftx"
    )

    log NFTPurchased(
        liquidation.erc20TokenContract,
        _collateralAddress,
        self.nftxMarketplaceZapAddress,
        liquidation.lid,
        _collateralAddress,
        _tokenId,
        autoLiquidationPrice,
        self.nftxMarketplaceZapAddress,
        liquidation.erc20TokenContract,
        "BACKSTOP_PERIOD_NFTX"
    )


@external
def adminWithdrawal(_walletAddress: address, _collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"

    liquidation: Liquidation = ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)
    assert block.timestamp > liquidation.lenderPeriodMaturity + self.auctionPeriodDuration, "liq not out of auction period"

    ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

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

    ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(
        _walletAddress,
        _collateralAddress,
        _tokenId
    )

    log AdminWithdrawal(
        _collateralAddress,
        liquidation.lid,
        _collateralAddress,
        _tokenId,
        _walletAddress
    )
