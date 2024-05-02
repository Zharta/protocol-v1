from dataclasses import dataclass
from functools import partial, partialmethod
from typing import Any, Callable, Optional

from ape import project
from ape.contracts.base import ContractInstance

from .basetypes import ContractConfig, DeploymentContext, InternalContract, MinimalProxy
from .transactions import Transaction


def with_pool(f, pool):
    return partial(f, pool=pool)


@dataclass
class CollateralVaultCoreV2Contract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        delegation_registry_key: str,
        collateral_vault_peripheral_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.CollateralVaultCoreV2,
            version=version,
            abi_key=abi_key,
            container_name="CollateralVaultCoreV2",
            deployment_deps={delegation_registry_key},
            deployment_args_contracts=[delegation_registry_key],
            config_deps={collateral_vault_peripheral_key: self.set_cvperiph},
        )
        self.collateral_vault_peripheral_key = collateral_vault_peripheral_key
        if address:
            self.load_contract(address)

    def set_cvperiph(self, context: DeploymentContext, *, dryrun: bool = False):
        execute(
            context,
            self.key,
            "setCollateralVaultPeripheralAddress",
            self.collateral_vault_peripheral_key,
            dryrun=dryrun,
        )


@dataclass
class CryptoPunksVaultCoreContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        nft_contract_key: str,
        delegation_registry_key: str,
        collateral_vault_peripheral_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.CryptoPunksVaultCore,
            version=version,
            abi_key=abi_key,
            container_name="CryptoPunksVaultCore",
            deployment_deps={nft_contract_key, delegation_registry_key},
            deployment_args=[nft_contract_key, delegation_registry_key],
            config_deps={collateral_vault_peripheral_key: self.set_cvperiph},
        )
        self.collateral_vault_peripheral_key = collateral_vault_peripheral_key
        if address:
            self.load_contract(address)

    def set_cvperiph(self, context: DeploymentContext, *, dryrun: bool = False):
        execute(context, self.key, "setCollateralVaultPeripheralAddress", self.collateral_vault_peripheral_key, dryrun=dryrun)


@dataclass
class CollateralVaultPeripheralContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        collateral_vault_core_key: str,
        punks_contract_key: str,
        punks_vault_core_key: str,
        liquidations_peripheral_key: str,
        token_keys: str,
        loans_peripheral_keys: str,
        address: str | None = None,
    ):
        _tokens_keys = token_keys.split(",")
        _loans_peripheral_keys = loans_peripheral_keys.split(",")
        super().__init__(
            key,
            None,
            project.CollateralVaultPeripheral,
            version=version,
            abi_key=abi_key,
            container_name="CollateralVaultPeripheral",
            deployment_deps={collateral_vault_core_key},
            deployment_args=[collateral_vault_core_key],
            config_deps={
                liquidations_peripheral_key: self.set_liquidationsperiph,
                punks_vault_core_key: self.add_punksvault,
            }
            | {
                loans: partialmethod(self.add_loansperiph, token_key=token, loans_key=loans)
                for loans, token in zip(_loans_peripheral_keys, _tokens_keys)
            },
        )
        self.collateral_vault_core_key = collateral_vault_core_key
        self.punks_contract_key = punks_contract_key
        self.punks_vault_core_key = punks_vault_core_key
        self.liquidations_peripheral_key = liquidations_peripheral_key
        if address:
            self.load_contract(address)

    def set_liquidationsperiph(self, context: DeploymentContext, *, dryrun: bool = False):
        execute(context, self.key, "setLiquidationsPeripheralAddress", self.liquidations_peripheral_key, dryrun=dryrun)

    def add_punksvault(self, context: DeploymentContext, *, dryrun: bool = False):
        execute(context, self.key, "addVault", self.punks_contract_key, self.punks_vault_core_key, dryrun=dryrun)

    def add_loansperiph(self, context: DeploymentContext, *, token_key, loans_key, dryrun: bool = False):
        execute(context, self.key, "addLoansPeripheralAddress", token_key, loans_key, dryrun=dryrun)


@dataclass
class LendingPoolCoreContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        token_key: str,
        lending_pool_peripheral_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LendingPoolCore,
            version=version,
            abi_key=abi_key,
            container_name="LendingPoolCore",
            deployment_deps={token_key},
            deployment_args=[token_key],
            config_deps={lending_pool_peripheral_key: self.set_lpperiph},
        )
        self.lending_pool_peripheral_key = lending_pool_peripheral_key
        if address:
            self.load_contract(address)

    def set_lpperiph(self, context: DeploymentContext, *, dryrun: bool = False):
        execute(context, self.key, "setLendingPoolPeripheralAddress", self.lending_pool_peripheral_key, dryrun=dryrun)


@dataclass
class LendingPoolLockContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        token_key: str,
        lending_pool_peripheral_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LendingPoolLock,
            version=version,
            abi_key=abi_key,
            container_name="LendingPoolLock",
            deployment_deps={token_key},
            deployment_args=[token_key],
            config_deps={lending_pool_peripheral_key: self.set_lpperiph},
        )
        self.lending_pool_peripheral_key = lending_pool_peripheral_key
        if address:
            self.load_contract(address)

    def set_lpperiph(self, context: DeploymentContext, *, dryrun: bool = False):
        execute(context, self.key, "setLendingPoolPeripheralAddress", self.lending_pool_peripheral_key, dryrun=dryrun)


@dataclass
class ERC20Contract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        name: str,
        symbol: str,
        decimals: int,
        supply: int,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.WETH9Mock,
            version=version,
            abi_key=abi_key,
            container_name="WETH9Mock",
            deployment_args=[name, symbol, decimals, supply],
        )
        if address:
            self.load_contract(address)


@dataclass
class CryptoPunksContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.CryptoPunksMarketMock,
            version=version,
            abi_key=abi_key,
            container_name="CryptoPunksMarketMock",
            nft=True,
        )
        if address:
            self.load_contract(address)


@dataclass
class DelegationRegistryContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.DelegationRegistryMock,
            version=version,
            abi_key=abi_key,
            container_name="DelegationRegistryMock",
        )
        if address:
            self.load_contract(address)


@dataclass
class LendingPoolPeripheralContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        lending_pool_core_key: str,
        lending_pool_lock_key: str,
        token_key: str,
        loans_peripheral_key: str,
        liquidations_peripheral_key: str,
        liquidity_controls_key: str,
        protocol_wallet_fees: int,
        protocol_fees_share: int,
        max_capital_efficiency: int,
        whitelisted: bool,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LendingPoolPeripheral,
            version=version,
            abi_key=abi_key,
            container_name="LendingPoolPeripheral",
            deployment_deps={lending_pool_core_key, lending_pool_lock_key, token_key},
            deployment_args=[
                lending_pool_core_key,
                lending_pool_lock_key,
                token_key,
                protocol_wallet_fees,
                protocol_fees_share,
                max_capital_efficiency,
                whitelisted
            ],
            config_deps={
                loans_peripheral_key: self.set_loansperiph,
                liquidations_peripheral_key: self.set_liquidationsperiph,
                liquidity_controls_key: self.set_liquiditycontrols,
            },
        )
        self.loans_peripheral_key = loans_peripheral_key
        self.liquidations_peripheral_key = liquidations_peripheral_key
        self.liquidity_controls_key = liquidity_controls_key
        if address:
            self.load_contract(address)


    def set_loansperiph(self, context: DeploymentContext):
        execute(context, self.key, "setLoansPeripheralAddress", self.loans_peripheral_key)

    def set_liquidationsperiph(self, context: DeploymentContext):
        execute(context, self.key, "setLiquidationsPeripheralAddress", self.liquidations_peripheral_key)

    def set_liquiditycontrols(self, context: DeploymentContext):
        execute(context, self.key, "setLiquidityControlsAddress", self.liquidity_controls_key)


@dataclass
class LoansCoreContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        loans_peripheral_key: str,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LoansCore,
            version=version,
            abi_key=abi_key,
            container_name="LoansCore",
            config_deps={loans_peripheral_key: self.set_loansperiph},
        )
        self.loans_peripheral_key = loans_peripheral_key
        if address:
            self.load_contract(address)

    def set_loansperiph(self, context: DeploymentContext):
        execute(context, self.key, "setLoansPeripheral", self.loans_peripheral_key)


@dataclass
class LoansPeripheralContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        liquidations_peripheral_key: str,
        liquidity_controls_key: str,
        lending_pool_peripheral_key: str,
        collateral_vault_peripheral_key: str,
        loans_core_key: str,
        genesis_key: str,
        accrual_period: int = 24 * 60 * 60,
        is_payable: bool,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.Loans,
            version=version,
            abi_key=abi_key,
            container_name="Loans",
            deployment_deps={loans_core_key, lending_pool_peripheral_key, collateral_vault_peripheral_key, genesis_key},
            deployment_args=[accrual_period, loans_core_key, lending_pool_peripheral_key, collateral_vault_peripheral_key, genesis_key, is_payable],
            config_deps={
                liquidations_peripheral_key: self.set_liquidationsperiph,
                liquidity_controls_key: self.set_liquiditycontrols,
                lending_pool_peripheral_key: self.set_lpperiph,
                collateral_vault_peripheral_key: self.set_cvperiph,
            },
        )
        self.liquidations_peripheral_key = liquidations_peripheral_key
        self.liquidity_controls_key = liquidity_controls_key
        self.lending_pool_peripheral_key = lending_pool_peripheral_key
        self.collateral_vault_peripheral_key = collateral_vault_peripheral_key
        if address:
            self.load_contract(address)

    def set_liquidationsperiph(self, context: DeploymentContext):
        execute(context, self.key, "setLiquidationsPeripheralAddress", self.liquidations_peripheral_key)

    def set_liquiditycontrols(self, context: DeploymentContext):
        execute(context, self.key, "setLiquidityControlsAddress", self.liquidity_controls_key)

    def set_lpperiph(self, context: DeploymentContext):
        configured_address = execute_read(context, self.key, "lendingPoolPeripheralContract")
        if configured_address != context[self.lending_pool_peripheral_key].address() or context.dryrun:
            execute(context, self.key, "setLendingPoolPeripheralAddress", self.lending_pool_peripheral_key)

    def set_cvperiph(self, context: DeploymentContext):
        configured_address = execute_read(context, self.key, "collateralVaultPeripheralContract")
        if configured_address != context[self.collateral_vault_peripheral_key].address() or context.dryrun:
            execute(context, self.key, "setCollateralVaultPeripheralAddress", self.collateral_vault_peripheral_key)


@dataclass
class LiquidationsCoreContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        liquidations_peripheral_key: str,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LiquidationsCore,
            version=version,
            abi_key=abi_key,
            container_name="LiquidationsCore",
            config_deps={liquidations_peripheral_key: self.set_liquidationsperiph},
        )
        self.liquidations_peripheral_key = liquidations_peripheral_key
        if address:
            self.load_contract(address)

    def set_liquidationsperiph(self, context: DeploymentContext):
        execute(context, self.key, "setLiquidationsPeripheralAddress", self.liquidations_peripheral_key)


@dataclass
class LiquidationsPeripheralContract(InternalContract):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        grace_period_duration: int = 2 * 86400,
        lender_period_duration: int = 2 * 86400,
        auction_period_duration: int = 2 * 86400,
        liquidations_core_key: str,
        collateral_vault_peripheral_key: str,
        weth_contract_key: str,
        wpunks_contract_key: str,
        token_keys: str,
        loans_core_keys: str,
        lending_pool_peripheral_keys: str,
        max_penalty_fee_keys: str,
        sushi_router_key: str | None = None,
        nftx_vault_factory_key: str | None = None,
        nftx_marketplace_zap_key: str | None = None,
        abi_key: str,
        address: str | None = None,
    ):
        _tokens_keys = token_keys.split(",")
        _loans_core_keys = loans_core_keys.split(",")
        _lending_pool_peripheral_keys = lending_pool_peripheral_keys.split(",")
        _max_penalty_fee_keys = max_penalty_fee_keys.split(",")
        super().__init__(
            key,
            None,
            project.LiquidationsPeripheral,
            version=version,
            abi_key=abi_key,
            container_name="LiquidationsPeripheral",
            deployment_deps={liquidations_core_key, weth_contract_key},
            deployment_args=[liquidations_core_key, grace_period_duration, lender_period_duration, auction_period_duration, weth_contract_key],
            config_deps={
                collateral_vault_peripheral_key: self.set_cvperiph,
                liquidations_core_key: self.set_liquidationscore,
                wpunks_contract_key: self.set_wpunks,
                sushi_router_key: self.set_sushirouter,
                nftx_vault_factory_key: self.set_nftxvaultfactory,
                nftx_marketplace_zap_key: self.set_nftxmarketplacezap,
            }
            | {
                loans_core: partialmethod(self.add_loanscore, token_key=token, loans_core_key=loans_core),
                for token, loans_core in zip(_tokens_keys, _loans_core_keys)
            },
            | {
                lpp: partialmethod(self.add_lpperiph, token_key=token, lending_pool_peripheral_key=lpp),
                for token, lpp in zip(_tokens_keys, _lending_pool_peripheral_keys)
            },
            | {
                max_fee_key: partialmethod(self.set_max_fee, token_key=token, max_fee_key=max_fee_key),
                for token, max_fee_key in zip(_tokens_keys, _max_penalty_fee_keys)
            },
        )
        self.liquidations_core_key = liquidations_core_key
        self.collateral_vault_peripheral_key = collateral_vault_peripheral_key
        self.sushi_router_key = sushi_router_key
        self.nftx_vault_factory_key = nftx_vault_factory_key
        self.nftx_marketplace_zap_key = nftx_marketplace_zap_key
        self.wpunks_contract_key = wpunks_contract_key
        if address:
            self.load_contract(address)

    def add_loanscore(self, context: DeploymentContext, *, loans_core_key, token_key):
        execute(context, self.key, "addLoansCoreAddress", token_key, loans_core_key)

    def add_lpperiph(context: DeploymentContext, *, lending_pool_peripheral_key, token_key):
        execute(context, self.key, "addLendingPoolPeripheralAddress", token_key, lending_pool_peripheral_key)

    def set_cvperiph(self, context: DeploymentContext):
        execute(context, self.key, "setCollateralVaultPeripheralAddress", self.collateral_vault_peripheral_key)

    def set_liquidationscore(self, context: DeploymentContext):
        configured_address = execute_read(context, self.key, "liquidationsCoreAddress")
        if configured_address != context[self.liquidations_core_key].address() or context.dryrun:
            execute(context, self.key, "setLiquidationsCoreAddress", self.liquidations_core_key)

    def set_wpunks(self, context: DeploymentContext):
        execute(context, self.key, "setWrappedPunksAddress", self.wpunks_contract_key)

    def set_nftxvaultfactory(self, context: DeploymentContext):
        if self.nftx_vault_factory_key:
            execute(context, self.key, "setNFTXVaultFactoryAddress", self.nftx_vault_factory_key)

    def set_nftxmarketplacezap(self, context: DeploymentContext):
        if self.nftx_marketplace_zap_key:
            execute(context, self.key, "setNFTXMarketplaceZapAddress", self.nftx_marketplace_zap_key)

    def set_sushirouter(self, context: DeploymentContext):
        if self.sushi_router_key:
            execute(context, self.key, "setSushiRouterAddress", self.sushi_router_key)


    def set_max_fee(self, context: DeploymentContext, *, token_key, max_fee_key):
        max_fee = context[max_fee_key]
        contract_instance = context[self.key].contract
        if not contract_instance:
            print(f"[{pool}] Skipping setMaxPenaltyFee for undeployed {self.key}")
            return
        erc20_contract_address = context[token_key].address()
        args = [erc20_contract_address, max_fee]

        current_value = execute_read(context, self.key, "maxPenaltyFee", erc20_contract_address)
        if current_value != max_fee:
            print(f"[{pool}] Changing maxPenaltyFee for {self.key}, from {current_value} to {max_fee}")
            execute(context, self.key, "setMaxPenaltyFee", token_key, max_fee)
        else:
            print(f"[{pool}] Skip setMaxPenaltyFee for {self.key}, current value is already {max_fee}")


@dataclass
class LiquidityControlsContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        max_pool_share_enabled: bool = False,
        max_pool_share: int = 1500,
        lock_period_enabled: bool = False,
        lock_period_duration: int = 7 * 24 * 60 * 60,
        max_loans_pool_share_enabled: bool = False,
        max_loans_pool_share: int = 1500,
        max_collection_borrowable_amount_enabled: bool = False,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LiquidityControls,
            version=version,
            abi_key=abi_key,
            container_name="LiquidityControls",
            deployment_args=[
                max_pool_share_enabled,
                max_pool_share,
                lock_period_enabled,
                lock_period_duration,
                max_loans_pool_share_enabled,
                max_loans_pool_share,
                max_collection_borrowable_amount_enabled
            ],
        )
        if address:
            self.load_contract(address)


@dataclass
class GenesisContract(InternalContract):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        genesis_owner: str,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.GenesisPass,
            version=version,
            abi_key=abi_key,
            container_name="GenesisPass",
            deployment_args=[genesis_owner],
        )
        if address:
            self.load_contract(address)


@dataclass
class CollateralVaultOTCImplContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        punks_contract_key: str,
        delegation_registry_key: str,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.CollateralVaultOTC,
            version=version,
            abi_key=abi_key,
            container_name="CollateralVaultOTC",
            deployment_deps={punks_contract_key, delegation_registry_key},
            deployment_args=[punks_contract_key, delegation_registry_key],
        )
        if address:
            self.load_contract(address)


@dataclass
class CollateralVaultOTCContract(MinimalProxy):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        collateral_vault_otc_impl_key: str,
        loans_key: str,
        liquidations_key: str,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.CollateralVaultOTC,
            version=version,
            abi_key=abi_key,
            container_name="CollateralVaultOTC",
            impl=collateral_vault_otc_impl_key,
            deployment_deps={collateral_vault_otc_impl_key},
            config_deps={
                loans_key: self.set_loans,
                liquidations_key: self.set_liquidations,
            },
        )
        self.loans_key = loans_key
        self.liquidations_key = liquidations_key
        if address:
            self.load_contract(address)

    def set_loans(self, context: DeploymentContext):
        execute(context, self.key, "setLoansAddress", self.loans_key)

    def set_liquidations(self, context: DeploymentContext):
        execute(context, self.key, "setLiquidationsPeripheralAddress", self.liquidations_key)



@dataclass
class LendingPoolEthOTCImplContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        weth_token_key: str,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LendingPoolEthOTC,
            version=version,
            abi_key=abi_key,
            container_name="LendingPoolEthOTC",
            deployment_deps={weth_token_key},
            deployment_args=[weth_token_key],
        )
        if address:
            self.load_contract(address)


@dataclass
class LendingPoolERC20OTCImplContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        address: str | None = None,
        token_key: str,
    ):
        super().__init__(
            key,
            None,
            project.LendingPoolERC20OTC,
            version=version,
            abi_key=abi_key,
            container_name="LendingPoolERC20OTC",
            deployment_deps={token_key},
            deployment_args=[token_key],
        )
        if address:
            self.load_contract(address)


@dataclass
class LendingPoolOTCContract(MinimalProxy):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        implementation_key: str,
        token_key: str,
        protocol_wallet_fees: int,
        protocol_fees_share: int,
        lender: str,
        liquidations_key: str,
        loans_key: str,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LendingPoolEthOTC,
            version=version,
            abi_key=abi_key,
            container_name="LendingPoolEthOTC",
            impl=implementation_key,
            deployment_deps={implementation_key},
            deployment_args=[protocol_wallet_fees, protocol_fees_share, lender],
            config_deps={
                liquidations_key: self.set_liquidations,
                loans_key: self.set_loans,
            },
        )
        self.liquidations_key = liquidations_key
        self.loans_key = loans_key
        if address:
            self.load_contract(address)

    def set_loans(self, context: DeploymentContext):
        execute(context, self.key, "setLoansPeripheralAddress", self.loans_key)

    def set_liquidations(self, context: DeploymentContext):
        execute(context, self.key, "setLiquidationsPeripheralAddress", self.liquidations_key)


@dataclass
class LiquidationsOTCImplContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LiquidationsOTC,
            version=version,
            abi_key=abi_key,
            container_name="LiquidationsOTC",
        )
        if address:
            self.load_contract(address)


@dataclass
class LiquidationsOTCContract(MinimalProxy):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        implementation_key: str,
        loans_key: str,
        lending_pool_key: str,
        collateral_vault_key: str,
        grace_period_duration: int = 2 * 86400,
        max_penalty_fee: int,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LiquidationsOTC,
            version=version,
            abi_key=abi_key,
            container_name="LiquidationsOTC",
            impl=implementation_key,
            deployment_deps={implementation_key, loans_key, lending_pool_key, collateral_vault_key},
            deployment_args=[grace_period_duration, loans_key, lending_pool_key, collateral_vault_key],
        )
        self.max_penalty_fee = max_penalty_fee
        if address:
            self.load_contract(address)

    def set_max_penalty_fee(self, context: DeploymentContext):
        if self.max_penalty_fee:
            execute(context, self.key, "setMaxPenaltyFee", self.max_penalty_fee)

    def deploy(self, context: DeploymentContext):
        super().deploy(context)
        self.set_max_penalty_fee(context)


@dataclass
class LoansOTCImplContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LoansOTC,
            version=version,
            abi_key=abi_key,
            container_name="LoansOTC",
        )
        if address:
            self.load_contract(address)


@dataclass
class LoansOTCPunksFixedImplContract(ContractConfig):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        token_key: str,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LoansOTC,
            version=version,
            abi_key=abi_key,
            container_name="LoansOTCPunksFixed",
            deployment_deps={token_key},
            deployment_args=[token_key],
        )
        if address:
            self.load_contract(address)


@dataclass
class LoansOTCContract(MinimalProxy):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        loans_otc_impl_key: str,
        interest_accrual_period: int = 24 * 60 * 60,
        lending_pool_key: str,
        collateral_vault_key: str,
        liquidations_key: str,
        genesis_key: str,
        is_payable: bool,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LoansOTC,
            version=version,
            abi_key=abi_key,
            container_name="LoansOTC",
            impl=loans_otc_impl_key,
            deployment_deps={loans_otc_impl_key, lending_pool_key, collateral_vault_key, genesis_key},
            deployment_args=[interest_accrual_period, lending_pool_key, collateral_vault_key, genesis_key, is_payable],
            config_deps={
                liquidations_key: self.set_liquidations,
                lending_pool_key: self.set_lendingpool,
                collateral_vault_key: self.set_collateral_vault,
            },
        )
        self.lending_pool_key = lending_pool_key
        self.collateral_vault_key = collateral_vault_key
        self.liquidations_key = liquidations_key
        if address:
            self.load_contract(address)

    def set_liquidations(self, context: DeploymentContext):
        execute(context, self.key, "setLiquidationsPeripheralAddress", self.liquidations_key)

    def set_lendingpool(self, context: DeploymentContext):
        configured_address = execute_read(context, self.key, "lendingPoolContract")
        if configured_address != context[self.lending_pool_key].address() or context.dryrun:
            execute(context, self.key, "setLendingPoolPeripheralAddress", self.lending_pool_key)

    def set_collateral_vault(self, context: DeploymentContext):
        configured_address = execute_read(context, self.key, "collateralVaultContract")
        if configured_address != context[self.collateral_vault_key].address() or context.dryrun:
            execute(context, self.key, "setCollateralVaultPeripheralAddress", self.collateral_vault_key)


@dataclass
class LoansOTCPunksFixedContract(MinimalProxy):
    def __init__(
        self,
        *,
        key: str,
        version: str | None = None,
        loans_otc_impl_key: str,
        interest_accrual_period: int = 24 * 60 * 60,
        lending_pool_key: str,
        collateral_vault_key: str,
        liquidations_key: str,
        genesis_key: str,
        is_payable: bool,
        abi_key: str,
        address: str | None = None,
    ):
        super().__init__(
            key,
            None,
            project.LoansOTCPunksFixed,
            version=version,
            abi_key=abi_key,
            container_name="LoansOTCPunksFixed",
            impl=loans_otc_impl_key,
            deployment_deps={loans_otc_impl_key, lending_pool_key, collateral_vault_key, genesis_key},
            deployment_args=[interest_accrual_period, lending_pool_key, collateral_vault_key, genesis_key, is_payable],
            config_deps={
                liquidations_key: self.set_liquidations,
                lending_pool_key: self.set_lendingpool,
                collateral_vault_key: self.set_collateral_vault,
            },
        )
        self.lending_pool_key = lending_pool_key
        self.collateral_vault_key = collateral_vault_key
        self.liquidations_key = liquidations_key
        if address:
            self.load_contract(address)

    def set_liquidations(self, context: DeploymentContext):
        execute(context, self.key, "setLiquidationsPeripheralAddress", self.liquidations_key)

    def set_lendingpool(self, context: DeploymentContext):
        configured_address = execute_read(context, self.key, "lendingPoolContract")
        if configured_address != context[self.lending_pool_key].address() or context.dryrun:
            execute(context, self.key, "setLendingPoolPeripheralAddress", self.lending_pool_key)

    def set_collateral_vault(self, context: DeploymentContext):
        configured_address = execute_read(context, self.key, "collateralVaultContract")
        if configured_address != context[self.collateral_vault_key].address() or context.dryrun:
            execute(context, self.key, "setCollateralVaultPeripheralAddress", self.collateral_vault_key)


def execute_read(context: DeploymentContext, contract: str, func: str, *args, options=None):
    contract_instance = context.contract[contract].contract
    print(f"## {contract}.{func}({','.join(args)})")
    if not context.dryrun:
        args_values = [context.get(c, c) for c in args]
        args_values = [v.address() if isinstance(v, ContractConfig) else v for v in args_values]
        # function = getattr(contract_instance, func)
        # args_values = [context[a].address() for a in args]
        # return function(*args_values, **({"sender": context.owner} | (options or {})))
        # return function(*args_values, **(options or {}))
        return contract_instance.call_view_method(func, *args_values, **(options or {}))


def execute(context: DeploymentContext, contract: str, func: str, *args, options=None):
    contract_instance = context.contract[contract].contract
    print(f"## {contract}.{func}({','.join(args)})", {"from": context.owner} | context.gas_options() | (options or {}))
    if not context.dryrun:
        function = getattr(contract_instance, func)
        args_values = [context.get(c, c) for c in args]
        args_values = [v.address() if isinstance(v, ContractConfig) else v for v in args_values]
        print(f"{function=} {args_values=}")
        return function(*args_values, **({"sender": context.owner} | context.gas_options() | (options or {})))

        # deploy_args = [context[a].address() for a in args]
        # print(f"{function=} {deploy_args=}")
        # return function(*deploy_args, **({"sender": context.owner} | context.gas_options() | (options or {})))



        values = [context.get(c, c) for c in self.deployment_args]
        return [v.contract if isinstance(v, ContractConfig) else v for v in values]
