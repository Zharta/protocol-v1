# @version ^0.3.4


# Interfaces

from vyper.interfaces import ERC20 as IERC20
from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721
from interfaces import ILiquidationsCore
from interfaces import ILoansCore
from interfaces import ILendingPoolPeripheral
from interfaces import ICollateralVaultPeripheral

interface ISushiRouter:
    def getAmountsOut(amountIn: uint256, path: address[2]) -> uint256[2]: view

interface INFTXVaultFactory:
    def vaultsForAsset(assetAddress: address) -> DynArray[address, 10]: view

interface INFTXVault:
    def vaultId() -> uint256: view
    def allValidNFTs(tokenIds: uint256[1]) -> bool: view

interface INFTXMarketplaceZap:
    def mintAndSell721WETH(vaultId: uint256, ids: uint256[1], minWethOut: uint256, path: address[2], to: address): nonpayable


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
    collaterals: DynArray[Collateral, 20]
    paidAmount: uint256
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
    activeForRewards: bool

struct Liquidation:
    lid: bytes32
    collateralAddress: address
    tokenId: uint256
    startTime: uint256
    gracePeriodMaturity: uint256
    buyNowPeriodMaturity: uint256
    principal: uint256
    interestAmount: uint256
    apr: uint256 # parts per 10000, e.g. 2.5% is represented by 250 parts per 10000
    gracePeriodPrice: uint256
    buyNowPeriodPrice: uint256
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

event LiquidationsPeriodDurationChanged:
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
    buyNowPeriodPrice: uint256

event LiquidationRemoved:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    erc20TokenContract: address

event NFTPurchased:
    erc20TokenContractIndexed: indexed(address)
    collateralAddressIndexed: indexed(address)
    fromIndexed: indexed(address)
    collateralAddress: address
    tokenId: uint256
    amount: uint256
    _from: address
    erc20TokenContract: address


# Global variables

owner: public(address)
proposedOwner: public(address)

gracePeriodDuration: public(uint256)
buyNowPeriodDuration: public(uint256)
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
    return principal + interestAmount + (principal * apr * duration) / 315360000000 # 315360000000 = 365 days in seconds times 10000 base percentage points


@pure
@internal
def _computeLiquidationInterestAmount(principal: uint256, interestAmount: uint256, apr: uint256, duration: uint256) -> uint256:
    return interestAmount + (principal * apr * duration) / 315360000000 # 315360000000 = 365 days in seconds times 10000 base percentage points


@view
@internal
def _getNFTXVaultAddrFromCollateralAddr(_collateralAddress: address) -> address:
    vault_addrs: DynArray[address, 10] = INFTXVaultFactory(self.nftxVaultFactoryAddress).vaultsForAsset(_collateralAddress)
    return vault_addrs[len(vault_addrs) - 1]


@view
@internal
def _getNFTXVaultIdFromCollateralAddr(_collateralAddress: address) -> uint256:
    vault_addr: address = self._getNFTXVaultAddrFromCollateralAddr(_collateralAddress)
    return INFTXVault(vault_addr).vaultId()


@view
@internal
def _getAutoLiquidationPrice(_collateralAddress: address, _tokenId: uint256) -> uint256:
    # vault_addrs: DynArray[address, 10] = INFTXVaultFactory(self.nftxVaultFactoryAddress).vaultsForAsset(_collateralAddress)
    # vault_addr: address = vault_addrs[len(vault_addrs) - 1]
    vault_addr: address = self._getNFTXVaultAddrFromCollateralAddr(_collateralAddress)

    assert INFTXVault(vault_addr).allValidNFTs([_tokenId]), "collateral not accepted"

    amountsOut: uint256[2] = ISushiRouter(self.sushiRouterAddress).getAmountsOut(as_wei_value(0.9, "ether"), [vault_addr, wethAddress])

    return amountsOut[1]


@pure
@internal
def _isCollateralInArray(_collaterals: DynArray[Collateral, 20], _collateralAddress: address, _tokenId: uint256) -> bool:
    for collateral in _collaterals:
        if collateral.contractAddress == _collateralAddress and collateral.tokenId == _tokenId:
            return True
    return False


@pure
@internal
def _getCollateralAmount(_collaterals: DynArray[Collateral, 20], _collateralAddress: address, _tokenId: uint256) -> uint256:
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
def __init__(_liquidationsCoreAddress: address, _gracePeriodDuration: uint256, _buyNowPeriodDuration: uint256, _auctionPeriodDuration: uint256, _wethAddress: address):
    assert _liquidationsCoreAddress != empty(address), "address is the zero address"
    assert _liquidationsCoreAddress.is_contract, "address is not a contract"
    assert _wethAddress != empty(address), "address is the zero address"
    assert _wethAddress.is_contract, "address is not a contract"
    assert _gracePeriodDuration > 0, "duration is 0"
    assert _buyNowPeriodDuration > 0, "duration is 0"
    assert _auctionPeriodDuration > 0, "duration is 0"

    self.owner = msg.sender
    self.liquidationsCoreAddress = _liquidationsCoreAddress
    self.gracePeriodDuration = _gracePeriodDuration
    self.buyNowPeriodDuration = _buyNowPeriodDuration
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
def setLiquidationsPeriodDuration(_duration: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _duration > 0, "duration is 0"
    assert _duration != self.buyNowPeriodDuration, "new value is the same"

    log LiquidationsPeriodDurationChanged(
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
    interestAmount: uint256 = principal * borrowerLoan.interest / 10000
    # # APR from loan duration (maturity)
    apr: uint256 = borrowerLoan.interest * 12

    gracePeriodPrice: uint256 = self._computeNFTPrice(principal, interestAmount, apr, self.gracePeriodDuration)
    protocolPrice: uint256 = self._computeNFTPrice(principal, interestAmount, apr, self.buyNowPeriodDuration)
    # autoLiquidationPrice: uint256 = self._getAutoLiquidationPrice(_collateralAddress, _tokenId)
    autoLiquidationPrice: uint256 = 0
    buyNowPeriodPrice: uint256 = 0
    
    if protocolPrice > autoLiquidationPrice:
        buyNowPeriodPrice = protocolPrice
    else:
        buyNowPeriodPrice = autoLiquidationPrice

    lid: bytes32 = ILiquidationsCore(self.liquidationsCoreAddress).addLiquidation(
        _collateralAddress,
        _tokenId,
        block.timestamp,
        block.timestamp + self.gracePeriodDuration,
        block.timestamp + self.gracePeriodDuration + self.buyNowPeriodDuration,
        principal,
        interestAmount,
        apr,
        gracePeriodPrice,
        buyNowPeriodPrice,
        _borrower,
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
        buyNowPeriodPrice
    )


@external
def buyNFTGracePeriod(_collateralAddress: address, _tokenId: uint256):
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"
    assert block.timestamp <= ILiquidationsCore(self.liquidationsCoreAddress).getLiquidationGracePeriodMaturity(_collateralAddress, _tokenId), "liquidation out of grace period"
    assert msg.sender == ILiquidationsCore(self.liquidationsCoreAddress).getLiquidationBorrower(_collateralAddress, _tokenId), "msg.sender is not borrower"
    assert not ILiquidationsCore(self.liquidationsCoreAddress).isLiquidationInAuction(_collateralAddress, _tokenId), "liquidation is in auction"

    liquidation: Liquidation = ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)

    ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

    log LiquidationRemoved(
        liquidation.erc20TokenContract,
        liquidation.collateralAddress,
        liquidation.lid,
        liquidation.collateralAddress,
        liquidation.tokenId,
        liquidation.erc20TokenContract
    )

    # IERC20(liquidation.erc20TokenContract).transferFrom(msg.sender, liquidation.gracePeriodPrice)
    # IERC20(liquidation.erc20TokenContract).approve(self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract], liquidation.gracePeriodPrice)

    ILendingPoolPeripheral(self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]).receiveFundsFromLiquidation(
        liquidation.borrower,
        liquidation.principal,
        liquidation.gracePeriodPrice - liquidation.principal
    )

    ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(msg.sender, _collateralAddress, _tokenId)

    log NFTPurchased(
        liquidation.erc20TokenContract,
        _collateralAddress,
        msg.sender,
        _collateralAddress,
        _tokenId,
        liquidation.gracePeriodPrice,
        msg.sender,
        liquidation.erc20TokenContract
    )


@external
def buyNFTBuyNowPeriod(_collateralAddress: address, _tokenId: uint256):
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"
    assert block.timestamp > ILiquidationsCore(self.liquidationsCoreAddress).getLiquidationGracePeriodMaturity(_collateralAddress, _tokenId), "liquidation in grace period"
    assert block.timestamp <= ILiquidationsCore(self.liquidationsCoreAddress).getLiquidationBuyNowPeriodMaturity(_collateralAddress, _tokenId), "liquidation out of buynow period"
    assert not ILiquidationsCore(self.liquidationsCoreAddress).isLiquidationInAuction(_collateralAddress, _tokenId), "liquidation is in auction"

    liquidation: Liquidation = ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)

    ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

    log LiquidationRemoved(
        liquidation.erc20TokenContract,
        liquidation.collateralAddress,
        liquidation.lid,
        liquidation.collateralAddress,
        liquidation.tokenId,
        liquidation.erc20TokenContract
    )

    fundsSender: address = msg.sender
    buyNowPeriodInterestAmount: uint256 = self._computeLiquidationInterestAmount(
        liquidation.principal,
        liquidation.interestAmount,
        liquidation.apr, self.buyNowPeriodDuration
    )
    if liquidation.buyNowPeriodPrice > liquidation.principal + buyNowPeriodInterestAmount:
        fundsSender = self
        IERC20(liquidation.erc20TokenContract).transferFrom(
            msg.sender,
            self,
            liquidation.buyNowPeriodPrice
        )
        IERC20(liquidation.erc20TokenContract).approve(
            self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract],
            liquidation.principal + buyNowPeriodInterestAmount
        )
        IERC20(liquidation.erc20TokenContract).transfer(
            liquidation.borrower,
            liquidation.buyNowPeriodPrice - (liquidation.principal + buyNowPeriodInterestAmount)
        )

    ILendingPoolPeripheral(self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]).receiveFundsFromLiquidation(
        fundsSender,
        liquidation.principal,
        buyNowPeriodInterestAmount
    )

    ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(msg.sender, _collateralAddress, _tokenId)

    log NFTPurchased(
        liquidation.erc20TokenContract,
        _collateralAddress,
        msg.sender,
        _collateralAddress,
        _tokenId,
        liquidation.buyNowPeriodPrice,
        msg.sender,
        liquidation.erc20TokenContract
    )


@external
def liquidateNFTX(_collateralAddress: address, _tokenId: uint256):
    assert IERC721(_collateralAddress).ownerOf(_tokenId) == ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).collateralVaultCoreAddress(), "collateral not owned by vault"
    assert block.timestamp > ILiquidationsCore(self.liquidationsCoreAddress).getLiquidationBuyNowPeriodMaturity(_collateralAddress, _tokenId), "liquidation out of buynow period"
    assert not ILiquidationsCore(self.liquidationsCoreAddress).isLiquidationInAuction(_collateralAddress, _tokenId), "liquidation is in auction"

    liquidation: Liquidation = ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)

    ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

    log LiquidationRemoved(
        liquidation.erc20TokenContract,
        liquidation.collateralAddress,
        liquidation.lid,
        liquidation.collateralAddress,
        liquidation.tokenId,
        liquidation.erc20TokenContract
    )

    autoLiquidationPrice: uint256 = self._getAutoLiquidationPrice(_collateralAddress, _tokenId)

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

    IERC20(liquidation.erc20TokenContract).approve(
        self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract],
        autoLiquidationPrice
    )

    principal: uint256 = liquidation.principal
    interestAmount: uint256 = 0
    if autoLiquidationPrice <= liquidation.principal:
        principal = autoLiquidationPrice
    else:
        interestAmount = autoLiquidationPrice - liquidation.principal

    ILendingPoolPeripheral(self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]).receiveFundsFromLiquidation(
        self,
        principal,
        interestAmount
    )

    log NFTPurchased(
        liquidation.erc20TokenContract,
        _collateralAddress,
        self.nftxMarketplaceZapAddress,
        _collateralAddress,
        _tokenId,
        autoLiquidationPrice,
        self.nftxMarketplaceZapAddress,
        liquidation.erc20TokenContract
    )


@external
def liquidateOpenSea():
    pass



