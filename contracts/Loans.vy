# @version ^0.3.6


# Interfaces

from vyper.interfaces import ERC165 as IERC165
from vyper.interfaces import ERC721 as IERC721
from vyper.interfaces import ERC20 as IERC20
from interfaces import ILoansCore
from interfaces import ICollateralVaultPeripheral
from interfaces import ILiquidityControls

interface IERC20Symbol:
    def symbol() -> String[100]: view

interface ILendingPoolPeripheral:
    def maxFundsInvestable() -> uint256: view 
    def erc20TokenContract() -> address: view
    def sendFunds(_to: address, _amount: uint256): nonpayable
    def receiveFunds(_borrower: address, _amount: uint256, _rewardsAmount: uint256): nonpayable
    def lendingPoolCoreContract() -> address: view

interface ILiquidationsPeripheral:
    def addLiquidation(_borrower: address, _loanId: uint256, _erc20TokenContract: address): nonpayable

interface INonERC721Vault:
    def collateralOwner(_tokenId: uint256) -> address: view
    def isApproved(_tokenId: uint256, _wallet: address) -> bool: view



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


struct EIP712Domain:
    name: String[100]
    version: String[10]
    chain_id: uint256
    verifying_contract: address

struct ReserveMessageContent:
    amount: uint256
    interest: uint256
    maturity: uint256
    collaterals: DynArray[Collateral, 100]
    deadline: uint256


# Events

event OwnershipTransferred:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event OwnerProposed:
    ownerIndexed: indexed(address)
    proposedOwnerIndexed: indexed(address)
    owner: address
    proposedOwner: address
    erc20TokenContract: address

event MaxLoansChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event MaxLoanDurationChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event MaxLoanAmountChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event InterestAccrualPeriodChanged:
    erc20TokenContractIndexed: indexed(address)
    currentValue: uint256
    newValue: uint256
    erc20TokenContract: address

event CollateralToWhitelistAdded:
    erc20TokenContractIndexed: indexed(address)
    value: address
    erc20TokenContract: address

event CollateralToWhitelistRemoved:
    erc20TokenContractIndexed: indexed(address)
    value: address
    erc20TokenContract: address

event LendingPoolPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event CollateralVaultPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LiquidationsPeripheralAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event LiquidityControlsAddressSet:
    erc20TokenContractIndexed: indexed(address)
    currentValue: address
    newValue: address
    erc20TokenContract: address

event WalletsWhitelistStatusChanged:
    erc20TokenContractIndexed: indexed(address)
    value: bool
    erc20TokenContract: address

event WhitelistedWalletAdded:
    erc20TokenContractIndexed: indexed(address)
    value: address
    erc20TokenContract: address

event WhitelistedWalletRemoved:
    erc20TokenContractIndexed: indexed(address)
    value: address
    erc20TokenContract: address

event ContractStatusChanged:
    erc20TokenContractIndexed: indexed(address)
    value: bool
    erc20TokenContract: address

event ContractDeprecated:
    erc20TokenContractIndexed: indexed(address)
    erc20TokenContract: address

event LoanCreated:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanPayment:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    principal: uint256
    interestAmount: uint256
    erc20TokenContract: address

event LoanPaid:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    erc20TokenContract: address

event LoanDefaulted:
    walletIndexed: indexed(address)
    wallet: address
    loanId: uint256
    amount: uint256
    erc20TokenContract: address


# Global variables

owner: public(address)
proposedOwner: public(address)

maxAllowedLoans: public(uint256)
maxAllowedLoanDuration: public(uint256)
maxLoanAmount: public(uint256)
interestAccrualPeriod: public(uint256)

isAcceptingLoans: public(bool)
isDeprecated: public(bool)

whitelistedCollaterals: public(HashMap[address, bool]) # given a collateral address, is the collection whitelisted

loansCoreContract: public(address)
lendingPoolPeripheralContract: public(address)
collateralVaultPeripheralContract: public(address)
liquidationsPeripheralContract: public(address)
liquidityControlsContract: public(address)

walletWhitelistEnabled: public(bool)
walletsWhitelisted: public(HashMap[address, bool])

collectionsAmount: HashMap[address, uint256] # aux variable

ZHARTA_DOMAIN_NAME: constant(String[6])    = "Zharta"
ZHARTA_DOMAIN_VERSION: constant(String[1]) = "1"

COLLATERAL_TYPE_DEF: constant(String[66])  = "Collateral(address contractAddress,uint256 tokenId,uint256 amount)"
RESERVE_TYPE_DEF: constant(String[179])    = "ReserveMessageContent(uint256 amount,uint256 interest,uint256 maturity,Collateral[] collaterals,uint256 deadline)" \
                                             "Collateral(address contractAddress,uint256 tokenId,uint256 amount)"
DOMAIN_TYPE_HASH: constant(bytes32)        = keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
COLLATERAL_TYPE_HASH: constant(bytes32)    = keccak256(COLLATERAL_TYPE_DEF)
RESERVE_TYPE_HASH: constant(bytes32)       = keccak256(RESERVE_TYPE_DEF)

reserve_message_typehash: bytes32
reserve_sig_domain_separator: bytes32

@external
def __init__(
    _maxAllowedLoans: uint256,
    _maxAllowedLoanDuration: uint256,
    _maxLoanAmount: uint256,
    _interestAccrualPeriod: uint256,
    _loansCoreContract: address,
    _lendingPoolPeripheralContract: address,
    _collateralVaultPeripheralContract: address
):
    assert _maxAllowedLoans > 0, "value for max loans is 0"
    assert _maxAllowedLoanDuration > 0, "valor for max duration is 0"
    assert _loansCoreContract != empty(address), "address is the zero address"
    assert _lendingPoolPeripheralContract != empty(address), "address is the zero address"
    assert _collateralVaultPeripheralContract != empty(address), "address is the zero address"

    self.owner = msg.sender
    self.maxAllowedLoans = _maxAllowedLoans
    self.maxAllowedLoanDuration = _maxAllowedLoanDuration
    self.maxLoanAmount = _maxLoanAmount
    self.interestAccrualPeriod = _interestAccrualPeriod
    self.loansCoreContract = _loansCoreContract
    self.lendingPoolPeripheralContract = _lendingPoolPeripheralContract
    self.collateralVaultPeripheralContract = _collateralVaultPeripheralContract
    self.isAcceptingLoans = True

    self.reserve_sig_domain_separator = keccak256(
        _abi_encode(
            DOMAIN_TYPE_HASH,
            keccak256(ZHARTA_DOMAIN_NAME),
            keccak256(ZHARTA_DOMAIN_VERSION),
            chain.id,
            self
        )
    )

@internal
def _areCollateralsWhitelisted(_collaterals: DynArray[Collateral, 100]) -> bool:
    for collateral in _collaterals:
        if not self.whitelistedCollaterals[collateral.contractAddress]:
            return False
    return True


@internal
def _areCollateralsOwned(_borrower: address, _collaterals: DynArray[Collateral, 100]) -> bool:
    for collateral in _collaterals:
        if IERC721(collateral.contractAddress).ownerOf(collateral.tokenId) != _borrower:
            return False
    return True


@view
@internal
def _isCollateralApprovedForVault(_borrower: address, _vault: address, _contractAddress: address, _tokenId: uint256) -> bool:
    is_erc721: bool = _vault == ICollateralVaultPeripheral(self.collateralVaultPeripheralContract).collateralVaultCoreDefaultAddress()
    if is_erc721:
        return IERC721(_contractAddress).isApprovedForAll(_borrower, _vault) or IERC721(_contractAddress).getApproved(_tokenId) == _vault
    else:
        return INonERC721Vault(_vault).isApproved(_tokenId, _vault)


@view
@internal
def _areCollateralsApproved(_borrower: address, _collaterals: DynArray[Collateral, 100]) -> bool:
    for collateral in _collaterals:
        vault: address = ICollateralVaultPeripheral(self.collateralVaultPeripheralContract).vaultAddress(collateral.contractAddress)
        if not self._isCollateralApprovedForVault(_borrower, vault, collateral.contractAddress, collateral.tokenId):
            return False
    return True


@pure
@internal
def _collateralsAmounts(_collaterals: DynArray[Collateral, 100]) -> uint256:
    sumAmount: uint256 = 0
    for collateral in _collaterals:
        sumAmount += collateral.amount

    return sumAmount


@internal
def _withinCollectionShareLimit(_collaterals: DynArray[Collateral, 100]) -> bool:
    collections: DynArray[address, 100] = empty(DynArray[address, 100])

    for collateral in _collaterals:
        if collateral.contractAddress not in collections:
            collections.append(collateral.contractAddress)
            self.collectionsAmount[collateral.contractAddress] = 0

        self.collectionsAmount[collateral.contractAddress] += collateral.amount

    for collection in collections:
        result: bool = ILiquidityControls(self.liquidityControlsContract).withinCollectionShareLimit(
            self.collectionsAmount[collection],
            collection,
            self.loansCoreContract,
            ILendingPoolPeripheral(self.lendingPoolPeripheralContract).lendingPoolCoreContract()
        )
        if not result:
            return False

    return True


@pure
@internal
def _loanPayableAmount(
    _amount: uint256,
    _paidAmount: uint256,
    _interest: uint256,
    _maxLoanDuration: uint256,
    _timePassed: uint256,
    _interestAccrualPeriod: uint256
) -> uint256:   
    return (_amount - _paidAmount) * (10000 * _maxLoanDuration + _interest * (_timePassed + _interestAccrualPeriod)) / (10000 * _maxLoanDuration)


@pure
@internal
def _computePeriodPassedInSeconds(_recentTimestamp: uint256, _olderTimestamp: uint256, _period: uint256) -> uint256:
    return (_recentTimestamp - _olderTimestamp) - ((_recentTimestamp - _olderTimestamp) % _period)


@internal
def _recoverReserveSigner(
    _amount: uint256,
    _interest: uint256,
    _maturity: uint256,
    _collaterals: DynArray[Collateral, 100],
    _deadline: uint256,
    _v: uint256,
    _r: uint256,
    _s: uint256
) -> address:
    """
        @notice recovers the sender address of the signed reserve function call
    """
    collaterals_data_hash: DynArray[bytes32, 100] = []
    for c in _collaterals:
        collaterals_data_hash.append(keccak256(_abi_encode(COLLATERAL_TYPE_HASH, c.contractAddress, c.tokenId, c.amount)))

    data_hash: bytes32 = keccak256(_abi_encode(
                RESERVE_TYPE_HASH,
                _amount,
                _interest,
                _maturity,
                keccak256(slice(_abi_encode(collaterals_data_hash), 32*2, 32*len(_collaterals))),
                _deadline,
                ))

    sig_hash: bytes32 = keccak256(concat(convert("\x19\x01", Bytes[2]), _abi_encode(self.reserve_sig_domain_separator, data_hash)))
    signer: address = ecrecover(sig_hash, _v, _r, _s)

    return signer


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
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )


@external
def claimOwnership():
    assert msg.sender == self.proposedOwner, "msg.sender is not the proposed"

    log OwnershipTransferred(
        self.owner,
        self.proposedOwner,
        self.owner,
        self.proposedOwner,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    self.owner = self.proposedOwner
    self.proposedOwner = empty(address)


@external
def changeMaxAllowedLoans(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value > 0, "value for max loans is 0"
    assert _value != self.maxAllowedLoans, "new max loans value is the same"

    log MaxLoansChanged(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        self.maxAllowedLoans,
        _value,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    self.maxAllowedLoans = _value


@external
def changeMaxAllowedLoanDuration(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value > 0, "value for max duration is 0"
    assert _value != self.maxAllowedLoanDuration, "new max duration value is the same"

    log MaxLoanDurationChanged(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        self.maxAllowedLoanDuration,
        _value,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    self.maxAllowedLoanDuration = _value


@external
def changeMaxLoanAmount(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value != self.maxLoanAmount, "new max loan amount is the same"

    log MaxLoanAmountChanged(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        self.maxLoanAmount,
        _value,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    self.maxLoanAmount = _value


@external
def changeInterestAccrualPeriod(_value: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _value != self.interestAccrualPeriod, "_value is the same"

    log InterestAccrualPeriodChanged(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        self.interestAccrualPeriod,
        _value,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    self.interestAccrualPeriod = _value


@external
def addCollateralToWhitelist(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    # No method yet to get the interface_id, so explicitly checking the ERC721 interface_id
    # assert IERC165(_address).supportsInterface(0x80ac58cd), "_address is not a ERC721"

    self.whitelistedCollaterals[_address] = True

    log CollateralToWhitelistAdded(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        _address,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )


@external
def removeCollateralFromWhitelist(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.whitelistedCollaterals[_address], "collateral is not whitelisted"

    self.whitelistedCollaterals[_address] = False

    log CollateralToWhitelistRemoved(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        _address,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )


@external
def setLendingPoolPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert self.lendingPoolPeripheralContract != _address, "new LPPeriph addr is the same"

    log LendingPoolPeripheralAddressSet(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        self.lendingPoolPeripheralContract,
        _address,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    self.lendingPoolPeripheralContract = _address


@external
def setCollateralVaultPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert self.collateralVaultPeripheralContract != _address, "new LPCore addr is the same"

    log CollateralVaultPeripheralAddressSet(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        self.collateralVaultPeripheralContract,
        _address,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    self.collateralVaultPeripheralContract = _address


@external
def setLiquidationsPeripheralAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert self.liquidationsPeripheralContract != _address, "new LPCore addr is the same"

    log LiquidationsPeripheralAddressSet(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        self.liquidationsPeripheralContract,
        _address,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    self.liquidationsPeripheralContract = _address


@external
def setLiquidityControlsAddress(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert _address.is_contract, "_address is not a contract"
    assert _address != self.liquidityControlsContract, "new value is the same"

    log LiquidityControlsAddressSet(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        self.liquidityControlsContract,
        _address,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    self.liquidityControlsContract = _address


@external
def changeWalletsWhitelistStatus(_flag: bool):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.walletWhitelistEnabled != _flag, "new value is the same"

    self.walletWhitelistEnabled = _flag

    log WalletsWhitelistStatusChanged(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        _flag,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )


@external
def addWhitelistedWallet(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert self.walletWhitelistEnabled, "wallets whitelist is disabled"
    assert not self.walletsWhitelisted[_address], "address is already whitelisted"

    self.walletsWhitelisted[_address] = True

    log WhitelistedWalletAdded(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        _address,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )


@external
def removeWhitelistedWallet(_address: address):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert _address != empty(address), "_address is the zero address"
    assert self.walletWhitelistEnabled, "wallets whitelist is disabled"
    assert self.walletsWhitelisted[_address], "address is not whitelisted"

    self.walletsWhitelisted[_address] = False

    log WhitelistedWalletRemoved(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        _address,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )


@external
def changeContractStatus(_flag: bool):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert self.isAcceptingLoans != _flag, "new contract status is the same"

    self.isAcceptingLoans = _flag

    log ContractStatusChanged(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        _flag,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )


@external
def deprecate():
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert not self.isDeprecated, "contract is already deprecated"

    self.isDeprecated = True
    self.isAcceptingLoans = False

    log ContractDeprecated(
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract(),
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )


@view
@external
def erc20TokenSymbol() -> String[100]:
    return IERC20Symbol(ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()).symbol()


@view
@external
def getLoanPayableAmount(_borrower: address, _loanId: uint256, _timestamp: uint256) -> uint256:
    loan: Loan = ILoansCore(self.loansCoreContract).getLoan(_borrower, _loanId)

    if loan.paid:
        return 0

    if loan.startTime > _timestamp:
        return max_value(uint256)

    if loan.started:
        timePassed: uint256 = self._computePeriodPassedInSeconds(
            _timestamp,
            loan.startTime,
            self.interestAccrualPeriod
        )
        return self._loanPayableAmount(
            loan.amount,
            loan.paidPrincipal,
            loan.interest,
            self.maxAllowedLoanDuration,
            timePassed,
            self.interestAccrualPeriod
        )

    return max_value(uint256)


@external
def reserve(
    _amount: uint256,
    _interest: uint256,
    _maturity: uint256,
    _collaterals: DynArray[Collateral, 100],
    _deadline: uint256,
    _v: uint256,
    _r: uint256,
    _s: uint256
) -> uint256:
    assert not self.isDeprecated, "contract is deprecated"
    assert self.isAcceptingLoans, "contract is not accepting loans"
    assert block.timestamp <= _maturity, "maturity is in the past"
    assert block.timestamp <= _deadline, "deadline has passed"
    assert _maturity - block.timestamp <= self.maxAllowedLoanDuration, "maturity exceeds the max allowed"
    assert self._areCollateralsWhitelisted(_collaterals), "not all NFTs are accepted"
    assert self._areCollateralsOwned(msg.sender, _collaterals), "msg.sender does not own all NFTs"
    assert self._areCollateralsApproved(msg.sender, _collaterals) == True, "not all NFTs are approved"
    assert self._collateralsAmounts(_collaterals) == _amount, "amount in collats != than amount"
    assert ILendingPoolPeripheral(self.lendingPoolPeripheralContract).maxFundsInvestable() >= _amount, "insufficient liquidity"
    assert ILoansCore(self.loansCoreContract).ongoingLoans(msg.sender) < self.maxAllowedLoans, "max loans already reached"
    assert _amount <= self.maxLoanAmount, "loan amount > than the max value"

    assert ILiquidityControls(self.liquidityControlsContract).withinLoansPoolShareLimit(
        msg.sender,
        _amount,
        self.loansCoreContract,
        self.lendingPoolPeripheralContract
    ), "max loans pool share surpassed"
    assert self._withinCollectionShareLimit(_collaterals), "max collection share surpassed"

    if self.walletWhitelistEnabled and not self.walletsWhitelisted[msg.sender]:
        raise "msg.sender is not whitelisted"

    signer: address = self._recoverReserveSigner(_amount, _interest, _maturity, _collaterals, _deadline, _v, _r, _s)
    assert signer == self.owner, "invalid message signature"

    newLoanId: uint256 = ILoansCore(self.loansCoreContract).addLoan(
        msg.sender,
        _amount,
        _interest,
        _maturity,
        _collaterals
    )

    for collateral in _collaterals:
        ILoansCore(self.loansCoreContract).addCollateralToLoan(msg.sender, collateral, newLoanId)
        ILoansCore(self.loansCoreContract).updateCollaterals(collateral, False)

        ICollateralVaultPeripheral(self.collateralVaultPeripheralContract).storeCollateral(
            msg.sender,
            collateral.contractAddress,
            collateral.tokenId,
            ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
        )

    log LoanCreated(
        msg.sender,
        msg.sender,
        newLoanId,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    ILoansCore(self.loansCoreContract).updateLoanStarted(msg.sender, newLoanId)
    ILoansCore(self.loansCoreContract).updateHighestSingleCollateralLoan(msg.sender, newLoanId)
    ILoansCore(self.loansCoreContract).updateHighestCollateralBundleLoan(msg.sender, newLoanId)

    ILendingPoolPeripheral(self.lendingPoolPeripheralContract).sendFunds(
        msg.sender,
        ILoansCore(self.loansCoreContract).getLoanAmount(msg.sender, newLoanId)
    )

    return newLoanId





@external
def pay(_loanId: uint256):
    assert ILoansCore(self.loansCoreContract).isLoanStarted(msg.sender, _loanId), "loan not found"
    assert block.timestamp <= ILoansCore(self.loansCoreContract).getLoanMaturity(msg.sender, _loanId), "loan maturity reached"
    assert not ILoansCore(self.loansCoreContract).getLoanPaid(msg.sender, _loanId), "loan already paid"

    loan: Loan = ILoansCore(self.loansCoreContract).getLoan(msg.sender, _loanId)

    # compute days passed in seconds
    timePassed: uint256 = self._computePeriodPassedInSeconds(
        block.timestamp,
        ILoansCore(self.loansCoreContract).getLoanStartTime(msg.sender, _loanId),
        self.interestAccrualPeriod
    )

    # pro-rata computation of max amount payable based on actual loan duration in days
    paymentAmount: uint256 = self._loanPayableAmount(
        loan.amount,
        loan.paidPrincipal,
        loan.interest,
        self.maxAllowedLoanDuration,
        timePassed,
        self.interestAccrualPeriod
    )

    erc20TokenContract: address = ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    assert IERC20(erc20TokenContract).balanceOf(msg.sender) >= paymentAmount, "insufficient balance"
    assert IERC20(erc20TokenContract).allowance(
        msg.sender,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).lendingPoolCoreContract()
    ) >= paymentAmount, "insufficient allowance"

    paidInterestAmount: uint256 = paymentAmount - loan.amount

    ILoansCore(self.loansCoreContract).updateLoanPaidAmount(msg.sender, _loanId, loan.amount, paidInterestAmount)
    ILoansCore(self.loansCoreContract).updatePaidLoan(msg.sender, _loanId)
    ILoansCore(self.loansCoreContract).updateHighestRepayment(msg.sender, _loanId)

    ILendingPoolPeripheral(self.lendingPoolPeripheralContract).receiveFunds(msg.sender, loan.amount, paidInterestAmount)

    for collateral in loan.collaterals:
        ILoansCore(self.loansCoreContract).removeCollateralFromLoan(msg.sender, collateral, _loanId)
        ILoansCore(self.loansCoreContract).updateCollaterals(collateral, True)

        ICollateralVaultPeripheral(self.collateralVaultPeripheralContract).transferCollateralFromLoan(
            msg.sender,
            collateral.contractAddress,
            collateral.tokenId,
            erc20TokenContract
        )

    log LoanPayment(
        msg.sender,
        msg.sender,
        _loanId,
        loan.amount,
        paidInterestAmount,
        erc20TokenContract
    )
    
    log LoanPaid(
        msg.sender,
        msg.sender,
        _loanId,
        erc20TokenContract
    )


@external
def settleDefault(_borrower: address, _loanId: uint256):
    assert msg.sender == self.owner, "msg.sender is not the owner"
    assert ILoansCore(self.loansCoreContract).isLoanStarted(_borrower, _loanId), "loan not found"
    assert block.timestamp > ILoansCore(self.loansCoreContract).getLoanMaturity(_borrower, _loanId), "loan is within maturity period"
    assert self.liquidationsPeripheralContract != empty(address), "BNPeriph is the zero address"

    ILoansCore(self.loansCoreContract).updateDefaultedLoan(_borrower, _loanId)
    ILoansCore(self.loansCoreContract).updateHighestDefaultedLoan(_borrower, _loanId)

    collaterals: DynArray[Collateral, 100] = ILoansCore(self.loansCoreContract).getLoanCollaterals(_borrower, _loanId)
    for collateral in collaterals:
        ILoansCore(self.loansCoreContract).removeCollateralFromLoan(_borrower, collateral, _loanId)
        ILoansCore(self.loansCoreContract).updateCollaterals(collateral, True)

    ILiquidationsPeripheral(self.liquidationsPeripheralContract).addLiquidation(
        _borrower,
        _loanId,
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )

    log LoanDefaulted(
        _borrower,
        _borrower,
        _loanId,
        ILoansCore(self.loansCoreContract).getLoanAmount(_borrower, _loanId),
        ILendingPoolPeripheral(self.lendingPoolPeripheralContract).erc20TokenContract()
    )


