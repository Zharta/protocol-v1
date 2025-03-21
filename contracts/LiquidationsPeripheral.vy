# @version 0.4.1

"""
@title LiquidationsPeripheral
@author [Zharta](https://zharta.io/)
@notice The liquidations peripheral contract exists as the main interface to handle liquidations
@dev Uses a `LiquidationsCore` contract to store state
"""


# Interfaces

from ethereum.ercs import IERC20
from ethereum.ercs import IERC721

interface ILiquidationsCore:
    def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation: view
    def getLiquidationStartTime(_collateralAddress: address, _tokenId: uint256) -> uint256: view
    def isLoanLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256) -> bool: view
    def addLiquidation(
        _collateralAddress: address,
        _tokenId: uint256,
        _startTime: uint256,
        _gracePeriodMaturity: uint256,
        _lenderPeriodMaturity: uint256,
        _principal: uint256,
        _interestAmount: uint256,
        _apr: uint256,
        _gracePeriodPrice: uint256,
        _lenderPeriodPrice: uint256,
        _borrower: address,
        _loanId: uint256,
        _loansCoreContract: address,
        _erc20TokenContract: address
    ) -> bytes32: nonpayable
    def addLoanToLiquidated(_borrower: address, _loansCoreContract: address, _loanId: uint256): nonpayable
    def removeLiquidation(_collateralAddress: address, _tokenId: uint256): nonpayable

interface ILoansCore:
    def getLoan(_borrower: address, _loanId: uint256) -> Loan: view

interface ILendingPoolPeripheral:
    def lenderFunds(_lender: address) -> InvestorFunds: view
    def receiveFundsFromLiquidation(
        _borrower: address,
        _amount: uint256,
        _rewardsAmount: uint256,
        _distributeToProtocol: bool,
        _investedAmount: uint256,
        _origin: String[30]
    ): nonpayable
    def receiveFundsFromLiquidationEth(
        _borrower: address,
        _amount: uint256,
        _rewardsAmount: uint256,
        _distributeToProtocol: bool,
        _investedAmount: uint256,
        _origin: String[30]
    ): payable
    def lendingPoolCoreContract() -> address: view
    def protocolFeesShare() -> uint256: view

interface ICollateralVaultPeripheral:
    def vaultAddress(_collateralAddress: address, _tokenId: uint256) -> address: view
    def isCollateralInVault(_collateralAddress: address, _tokenId: uint256) -> bool: view
    def transferCollateralFromLiquidation(_wallet: address, _collateralAddress: address, _tokenId: uint256): nonpayable
    def collateralVaultCoreDefaultAddress() -> address: view

interface ISushiFactory:
    def getPair(tokenA: address, tokenB: address) -> address: view

interface ISushiRouter:
    def factory() -> address: view
    def getAmountsOut(amountIn: uint256, path: DynArray[address, 2]) -> DynArray[uint256, 2]: view
    def swapExactTokensForTokens(
        amountIn: uint256,
        amountsOutMin: uint256,
        path: DynArray[address, 2],
        to: address,
        dealine: uint256
    ) -> DynArray[uint256, 2]: nonpayable

interface INFTXVaultFactory:
    def vaultsForAsset(assetAddress: address) -> DynArray[address, 2**10]: view

interface INFTXVault:
    def vaultId() -> uint256: view
    def allValidNFTs(tokenIds: DynArray[uint256, 1]) -> bool: view
    def mintFee() -> uint256: view

interface INFTXMarketplaceZap:
    def mintAndSell721WETH(vaultId: uint256, ids: DynArray[uint256, 1], minWethOut: uint256, path: DynArray[address, 2], to: address): nonpayable

interface IVault:
    def vaultName() -> String[30]: view

interface CryptoPunksMarket:
    def offerPunkForSaleToAddress(punkIndex: uint256, minSalePriceInWei: uint256, toAddress: address): nonpayable

interface WrappedPunk:
    def burn(punkIndex: uint256): nonpayable


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

event WrappedPunksAddressSet:
    currentValue: address
    newValue: address

event CryptoPunksAddressSet:
    currentValue: address
    newValue: address

event MaxPenaltyFeeSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

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
    loansCoreContract: address
    method: String[30] # possible values: GRACE_PERIOD, LENDER_PERIOD, BACKSTOP_PERIOD_NFTX, BACKSTOP_PERIOD_ADMIN

event AdminWithdrawal:
    collateralAddressIndexed: indexed(address)
    liquidationId: bytes32
    collateralAddress: address
    tokenId: uint256
    wallet: address

event PaymentSent:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256

event PaymentReceived:
    walletIndexed: indexed(address)
    wallet: address
    amount: uint256


# Global variables

owner: public(address)
admin: public(address)
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
wrappedPunksAddress: public(address)
cryptoPunksAddress: public(address)
wethAddress: immutable(address)

maxPenaltyFee: public(HashMap[address, uint256])

##### INTERNAL METHODS - VIEW #####

@pure
@internal
def _penaltyFee(_principal: uint256, _max_penalty_fee: uint256) -> uint256:
    return min(250 * _principal // 10000, _max_penalty_fee) if _max_penalty_fee > 0 else (250 * _principal // 10000)


@pure
@internal
def _computeNFTPrice(principal: uint256, interestAmount: uint256, _max_penalty_fee: uint256) -> uint256:
    return principal + interestAmount + self._penaltyFee(principal, _max_penalty_fee)


@pure
@internal
def _computeLoanAPR(loanInterest: uint256, loanMaturity: uint256, loanStartTime: uint256) -> uint256:
    return loanInterest * 31536000 // (loanMaturity - loanStartTime) # 31536000 = 365 days * 24 hours * 60 minutes * 60 seconds


@pure
@internal
def _computeLoanInterestAmount(principal: uint256, interest: uint256) -> uint256:
    return principal * interest // 10000


@view
@internal
def _getNFTXVaultAddrFromCollateralAddr(_collateralAddress: address) -> address:
    if self.nftxVaultFactoryAddress == empty(address):
        return empty(address)

    vaultAddrs: DynArray[address, 2**10] = staticcall INFTXVaultFactory(self.nftxVaultFactoryAddress).vaultsForAsset(_collateralAddress)

    if len(vaultAddrs) == 0:
        return empty(address)

    return vaultAddrs[len(vaultAddrs) - 1]


@view
@internal
def _getNFTXVaultIdFromCollateralAddr(_collateralAddress: address) -> uint256:
    vaultAddr: address = self._getNFTXVaultAddrFromCollateralAddr(_collateralAddress)
    return staticcall INFTXVault(vaultAddr).vaultId()


@view
@internal
def _getNFTXVaultMintFee(vaultAddr: address) -> uint256:
    return staticcall INFTXVault(vaultAddr).mintFee()


@view
@internal
def _getConvertedAutoLiquidationPrice(_ethLiquidationPrice: uint256, _erc20TokenContract: address) -> uint256:
    amountsOut: DynArray[uint256, 2] = staticcall ISushiRouter(self.sushiRouterAddress).getAmountsOut(_ethLiquidationPrice, [wethAddress, _erc20TokenContract])
    return amountsOut[1]


@view
@internal
def _getAutoLiquidationPrice(_collateralAddress: address, _tokenId: uint256) -> uint256:
    vaultAddr: address = self._getNFTXVaultAddrFromCollateralAddr(_collateralAddress)

    if vaultAddr == empty(address):
        return 0

    if not staticcall INFTXVault(vaultAddr).allValidNFTs([_tokenId]):
        return 0

    # wrong setup of Sushi router
    if staticcall ISushiRouter(self.sushiRouterAddress).factory() == empty(address):
        return 0

    # token pair does not exist
    if staticcall ISushiFactory(staticcall ISushiRouter(self.sushiRouterAddress).factory()).getPair(vaultAddr, wethAddress) == empty(address):
        return 0

    mintFee: uint256 = self._getNFTXVaultMintFee(vaultAddr)
    amountsOut: DynArray[uint256, 2] = staticcall ISushiRouter(self.sushiRouterAddress).getAmountsOut(as_wei_value(1, "ether") - mintFee, [vaultAddr, wethAddress])

    return amountsOut[1]


@pure
@internal
def _isCollateralInArray(_collaterals: DynArray[Collateral, 100], _collateralAddress: address, _tokenId: uint256) -> bool:
    for collateral: Collateral in _collaterals:
        if collateral.contractAddress == _collateralAddress and collateral.tokenId == _tokenId:
            return True
    return False


@view
@internal
def _unwrappedCollateralAddressIfWrapped(_collateralAddress: address) -> address:
    if _collateralAddress == self.wrappedPunksAddress:
        return self.cryptoPunksAddress
    return _collateralAddress

@internal
def _unwrapCollateral(_collateralAddress: address, _tokenId: uint256):
    if _collateralAddress == self.wrappedPunksAddress:
        extcall WrappedPunk(self.wrappedPunksAddress).burn(_tokenId)


##### INTERNAL METHODS - WRITE #####

@internal
def _removeLiquidationAndTransfer(_collateralAddress: address, _tokenId: uint256, _liquidation: Liquidation, _origin: String[30]):

    extcall ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

    log LiquidationRemoved(
        _liquidation.erc20TokenContract,
        _liquidation.collateralAddress,
        _liquidation.lid,
        _liquidation.collateralAddress,
        _liquidation.tokenId,
        _liquidation.erc20TokenContract,
        _liquidation.loansCoreContract,
        _liquidation.loanId,
        _liquidation.borrower
    )

    extcall ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(msg.sender, _collateralAddress, _tokenId)

    log NFTPurchased(
        _liquidation.erc20TokenContract,
        _collateralAddress,
        msg.sender,
        _liquidation.lid,
        _collateralAddress,
        _tokenId,
        _liquidation.gracePeriodPrice,
        msg.sender,
        _liquidation.erc20TokenContract,
        _liquidation.loansCoreContract,
        _origin
    )


@internal
def _swapWETHForERC20Token(_wethValue: uint256, _erc20MinValue: uint256, _erc20TokenContract: address) -> uint256:
    extcall IERC20(wethAddress).approve(self.sushiRouterAddress, _wethValue)
    return (extcall ISushiRouter(self.sushiRouterAddress).swapExactTokensForTokens(
        _wethValue,
        _erc20MinValue,
        [wethAddress, _erc20TokenContract],
        self,
        block.timestamp
    ))[1]

##### EXTERNAL METHODS - VIEW #####

@view
@external
def onERC721Received(_operator: address, _from: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4:
    return method_id("onERC721Received(address,address,uint256,bytes)", output_type=bytes4)

@view
@external
def getLiquidation(_collateralAddress: address, _tokenId: uint256) -> Liquidation:
    return staticcall ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)


##### EXTERNAL METHODS - WRITE #####
@deploy
def __init__(_liquidationsCoreAddress: address, _gracePeriodDuration: uint256, _lenderPeriodDuration: uint256, _auctionPeriodDuration: uint256, _wethAddress: address):
    assert _liquidationsCoreAddress != empty(address), "address is the zero address"
    assert _wethAddress != empty(address), "address is the zero address"
    assert _gracePeriodDuration > 0, "duration is 0"
    assert _lenderPeriodDuration > 0, "duration is 0"
    assert _auctionPeriodDuration > 0, "duration is 0"

    self.owner = msg.sender
    self.admin = msg.sender
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
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
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
    assert _erc20TokenContract != empty(address), "erc20TokenAddr is the zero addr"
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
def setWrappedPunksAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"

    log WrappedPunksAddressSet(
        self.wrappedPunksAddress,
        _address
    )

    self.wrappedPunksAddress = _address


@external
def setCryptoPunksAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "address is the zero addr"

    log CryptoPunksAddressSet(
        self.cryptoPunksAddress,
        _address
    )

    self.cryptoPunksAddress = _address


@external
def setMaxPenaltyFee(_erc20TokenContract: address, _fee: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _erc20TokenContract != empty(address), "addr is the zero addr"

    log MaxPenaltyFeeSet(
        _erc20TokenContract,
        self.maxPenaltyFee[_erc20TokenContract],
        _fee,
        _erc20TokenContract
    )

    self.maxPenaltyFee[_erc20TokenContract] = _fee


@external
def addLiquidation(
    _borrower: address,
    _loanId: uint256,
    _erc20TokenContract: address
):
    borrowerLoan: Loan = staticcall ILoansCore(self.loansCoreAddresses[_erc20TokenContract]).getLoan(_borrower, _loanId)
    assert borrowerLoan.defaulted, "loan is not defaulted"
    assert not staticcall ILiquidationsCore(self.liquidationsCoreAddress).isLoanLiquidated(_borrower, self.loansCoreAddresses[_erc20TokenContract], _loanId), "loan already liquidated"

    # APR from loan duration (maturity)
    loanAPR: uint256 = self._computeLoanAPR(borrowerLoan.interest, borrowerLoan.maturity, borrowerLoan.startTime)

    for collateral: Collateral in borrowerLoan.collaterals:
        assert (staticcall ILiquidationsCore(self.liquidationsCoreAddress).getLiquidationStartTime(collateral.contractAddress, collateral.tokenId)) == 0, "liquidation already exists"

        principal: uint256 = collateral.amount
        interestAmount: uint256 = self._computeLoanInterestAmount(principal, borrowerLoan.interest)

        gracePeriodPrice: uint256 = self._computeNFTPrice(principal, interestAmount, self.maxPenaltyFee[_erc20TokenContract])
        unwrappedCollateralAddress: address = self._unwrappedCollateralAddressIfWrapped(collateral.contractAddress)

        lid: bytes32 = extcall ILiquidationsCore(self.liquidationsCoreAddress).addLiquidation(
            collateral.contractAddress,
            collateral.tokenId,
            block.timestamp,
            block.timestamp + self.gracePeriodDuration,
            block.timestamp + self.gracePeriodDuration + self.lenderPeriodDuration,
            principal,
            interestAmount,
            loanAPR,
            gracePeriodPrice,
            gracePeriodPrice,
            _borrower,
            _loanId,
            self.loansCoreAddresses[_erc20TokenContract],
            _erc20TokenContract
        )

        log LiquidationAdded(
            _erc20TokenContract,
            collateral.contractAddress,
            lid,
            collateral.contractAddress,
            collateral.tokenId,
            _erc20TokenContract,
            gracePeriodPrice,
            gracePeriodPrice,
            block.timestamp + self.gracePeriodDuration,
            block.timestamp + self.gracePeriodDuration + self.lenderPeriodDuration,
            self.loansCoreAddresses[_erc20TokenContract],
            _loanId,
            _borrower
        )

    extcall ILiquidationsCore(self.liquidationsCoreAddress).addLoanToLiquidated(_borrower, self.loansCoreAddresses[_erc20TokenContract], _loanId)


@payable
@external
def payLoanLiquidationsGracePeriod(_loanId: uint256, _erc20TokenContract: address):
    receivedAmount: uint256 = msg.value
    ethPayment: bool = receivedAmount > 0

    loan: Loan = staticcall ILoansCore(self.loansCoreAddresses[_erc20TokenContract]).getLoan(msg.sender, _loanId)
    assert loan.defaulted, "loan is not defaulted"

    if ethPayment:
        log PaymentReceived(msg.sender, msg.sender, receivedAmount)
    paidAmount: uint256 = 0

    for collateral: Collateral in loan.collaterals:
        liquidation: Liquidation = staticcall ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(collateral.contractAddress, collateral.tokenId)

        assert block.timestamp <= liquidation.gracePeriodMaturity, "liquidation out of grace period"
        assert not ethPayment or receivedAmount >= paidAmount + liquidation.gracePeriodPrice, "insufficient value received"

        extcall ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(collateral.contractAddress, collateral.tokenId)

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

        _lendingPoolPeripheral : address = self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]

        if ethPayment:
            extcall ILendingPoolPeripheral(_lendingPoolPeripheral).receiveFundsFromLiquidationEth(
                liquidation.borrower,
                liquidation.principal,
                liquidation.gracePeriodPrice - liquidation.principal,
                True,
                liquidation.principal,
                "liquidation_grace_period",
                value=liquidation.gracePeriodPrice
            )
            log PaymentSent(_lendingPoolPeripheral, _lendingPoolPeripheral, liquidation.gracePeriodPrice)
            paidAmount += liquidation.gracePeriodPrice

        else:
            extcall ILendingPoolPeripheral(_lendingPoolPeripheral).receiveFundsFromLiquidation(
                liquidation.borrower,
                liquidation.principal,
                liquidation.gracePeriodPrice - liquidation.principal,
                True,
                liquidation.principal,
                "liquidation_grace_period"
            )


        extcall ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(
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
            liquidation.loansCoreContract,
            "GRACE_PERIOD"
        )

    excessAmount: uint256 = receivedAmount - paidAmount
    if excessAmount > 0:
        send(msg.sender, excessAmount)
        log PaymentSent(msg.sender, msg.sender,excessAmount)


@payable
@external
def buyNFTLenderPeriod(_collateralAddress: address, _tokenId: uint256):
    liquidation: Liquidation = staticcall ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)
    assert block.timestamp > liquidation.gracePeriodMaturity, "liquidation in grace period"
    assert block.timestamp <= liquidation.lenderPeriodMaturity, "liquidation out of lender period"
    assert (staticcall ILendingPoolPeripheral(self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]).lenderFunds(msg.sender)).currentAmountDeposited > 0, "msg.sender is not a lender"

    lendingPoolPeripheral: address = self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]

    receivedAmount: uint256 = msg.value
    ethPayment: bool = receivedAmount > 0
    if ethPayment:
        assert receivedAmount >= liquidation.lenderPeriodPrice, "insufficient value received"
        log PaymentReceived(msg.sender, msg.sender, receivedAmount)
        extcall ILendingPoolPeripheral(lendingPoolPeripheral).receiveFundsFromLiquidationEth(
            msg.sender,
            liquidation.principal,
            liquidation.lenderPeriodPrice - liquidation.principal,
            True,
            liquidation.principal,
            "liquidation_lenders_period",
            value=liquidation.lenderPeriodPrice
        )
        log PaymentSent(lendingPoolPeripheral, lendingPoolPeripheral, liquidation.lenderPeriodPrice)
    else:
        extcall ILendingPoolPeripheral(lendingPoolPeripheral).receiveFundsFromLiquidation(
            msg.sender,
            liquidation.principal,
            liquidation.lenderPeriodPrice - liquidation.principal,
            True,
            liquidation.principal,
            "liquidation_lenders_period"
        )

    self._removeLiquidationAndTransfer(_collateralAddress, _tokenId, liquidation, "LENDER_PERIOD")

    if ethPayment:
        excessAmount: uint256 = receivedAmount - liquidation.lenderPeriodPrice
        if excessAmount > 0:
            send(msg.sender, excessAmount)
            log PaymentSent(msg.sender, msg.sender,excessAmount)


@external
def liquidateNFTX(_collateralAddress: address, _tokenId: uint256):
    raise "deprecated"
    # assert msg.sender == self.admin, "msg.sender is not the admin"

    # liquidation: Liquidation = staticcall ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)
    # assert block.timestamp > liquidation.lenderPeriodMaturity, "liquidation within lender period"

    # extcall ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

    # log LiquidationRemoved(
    #     liquidation.erc20TokenContract,
    #     liquidation.collateralAddress,
    #     liquidation.lid,
    #     liquidation.collateralAddress,
    #     liquidation.tokenId,
    #     liquidation.erc20TokenContract,
    #     liquidation.loansCoreContract,
    #     liquidation.loanId,
    #     liquidation.borrower
    # )

    # unwrappedCollateralAddress: address = self._unwrappedCollateralAddressIfWrapped(_collateralAddress)
    # autoLiquidationPrice: uint256 = self._getAutoLiquidationPrice(unwrappedCollateralAddress, _tokenId)
    # vault: address = staticcall ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).vaultAddress(_collateralAddress, _tokenId)

    # assert autoLiquidationPrice > 0, "NFTX liq price is 0 or none"

    # extcall ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(self, _collateralAddress, _tokenId)

    # wrappedCollateral: bool = unwrappedCollateralAddress != _collateralAddress

    # if wrappedCollateral:
    #     self._unwrapCollateral(_collateralAddress, _tokenId)


    # if wrappedCollateral:
    #     if unwrappedCollateralAddress == self.cryptoPunksAddress:
    #         extcall CryptoPunksMarket(unwrappedCollateralAddress).offerPunkForSaleToAddress(_tokenId, 0, self.nftxMarketplaceZapAddress)
    #     else:
    #         raise "Unsupported collateral"

    # elif staticcall IVault(vault).vaultName() == "erc721":
    #     extcall IERC721(_collateralAddress).approve(self.nftxMarketplaceZapAddress, _tokenId)

    # elif staticcall IVault(vault).vaultName() == "cryptopunks":
    #     extcall CryptoPunksMarket(_collateralAddress).offerPunkForSaleToAddress(_tokenId, 0, self.nftxMarketplaceZapAddress)

    # else:
    #     raise "Unsupported collateral"


    # extcall INFTXMarketplaceZap(self.nftxMarketplaceZapAddress).mintAndSell721WETH(
    #     self._getNFTXVaultIdFromCollateralAddr(unwrappedCollateralAddress),
    #     [_tokenId],
    #     autoLiquidationPrice,
    #     [self._getNFTXVaultAddrFromCollateralAddr(unwrappedCollateralAddress), wethAddress],
    #     self
    # )

    # if liquidation.erc20TokenContract != wethAddress:
    #     convertedAutoLiquidationPrice: uint256 = self._getConvertedAutoLiquidationPrice(autoLiquidationPrice, liquidation.erc20TokenContract)
    #     autoLiquidationPrice = self._swapWETHForERC20Token(autoLiquidationPrice, convertedAutoLiquidationPrice, liquidation.erc20TokenContract)

    # lp_peripheral_address: address = self.lendingPoolPeripheralAddresses[liquidation.erc20TokenContract]
    # lp_core_address: address = staticcall ILendingPoolPeripheral(lp_peripheral_address).lendingPoolCoreContract()

    # extcall IERC20(liquidation.erc20TokenContract).approve(
    #     lp_core_address,
    #     autoLiquidationPrice
    # )

    # principal: uint256 = liquidation.principal
    # interestAmount: uint256 = 0
    # distributeToProtocol: bool = True

    # if autoLiquidationPrice < liquidation.principal: # LP loss scenario
    #     principal = autoLiquidationPrice
    # elif autoLiquidationPrice > liquidation.principal:
    #     interestAmount = autoLiquidationPrice - liquidation.principal
    #     protocolFeesShare: uint256 = staticcall ILendingPoolPeripheral(lp_peripheral_address).protocolFeesShare()
    #     if interestAmount <= liquidation.interestAmount * (10000 - protocolFeesShare) // 10000: # LP interest less than expected and/or protocol interest loss
    #         distributeToProtocol = False

    # extcall ILendingPoolPeripheral(lp_peripheral_address).receiveFundsFromLiquidation(
    #     self,
    #     principal,
    #     interestAmount,
    #     distributeToProtocol,
    #     liquidation.principal,
    #     "liquidation_nftx"
    # )

    # log NFTPurchased(
    #     liquidation.erc20TokenContract,
    #     _collateralAddress,
    #     self.nftxMarketplaceZapAddress,
    #     liquidation.lid,
    #     _collateralAddress,
    #     _tokenId,
    #     autoLiquidationPrice,
    #     self.nftxMarketplaceZapAddress,
    #     liquidation.erc20TokenContract,
    #     liquidation.loansCoreContract,
    #     "BACKSTOP_PERIOD_NFTX"
    # )


@external
def adminWithdrawal(_walletAddress: address, _collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"

    liquidation: Liquidation = staticcall ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)
    assert block.timestamp > liquidation.lenderPeriodMaturity, "liq not out of lenders period"

    extcall ILiquidationsCore(self.liquidationsCoreAddress).removeLiquidation(_collateralAddress, _tokenId)

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

    extcall ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).transferCollateralFromLiquidation(
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

@external
def adminLiquidation(_principal: uint256, _interestAmount: uint256, _loanPrincipal: uint256, _liquidationId: bytes32, _erc20TokenContract: address, _collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert not staticcall ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).isCollateralInVault(_collateralAddress, _tokenId), "collateral still owned by vault"

    liquidation: Liquidation = staticcall ILiquidationsCore(self.liquidationsCoreAddress).getLiquidation(_collateralAddress, _tokenId)
    assert liquidation.lid == empty(bytes32), "collateral still in liquidation"

    extcall ILendingPoolPeripheral(self.lendingPoolPeripheralAddresses[_erc20TokenContract]).receiveFundsFromLiquidation(
        msg.sender,
        _principal,
        _interestAmount,
        True,
        _loanPrincipal,
        "admin_liquidation"
    )

    log NFTPurchased(
        _erc20TokenContract,
        _collateralAddress,
        msg.sender,
        _liquidationId,
        _collateralAddress,
        _tokenId,
        _principal + _interestAmount,
        msg.sender,
        _erc20TokenContract,
        self.loansCoreAddresses[_erc20TokenContract],
        "BACKSTOP_PERIOD_ADMIN"
    )

@external
def storeERC721CollateralToVault(_collateralAddress: address, _tokenId: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert staticcall IERC721(_collateralAddress).ownerOf(_tokenId) == self, "collateral not owned by contract"

    vault: address = staticcall ICollateralVaultPeripheral(self.collateralVaultPeripheralAddress).vaultAddress(_collateralAddress, _tokenId)
    extcall IERC721(_collateralAddress).safeTransferFrom(self, vault, _tokenId, b"")
