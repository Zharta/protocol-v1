from typing import Optional, Any, Callable
from functools import partial
from ape.contracts.base import ContractInstance
from dataclasses import dataclass
from .basetypes import InternalContract, DeploymentContext, MinimalProxy
from .transactions import Transaction

from ape import project


def with_pool(f, pool):
    return partial(f, pool=pool)


@dataclass
class CollateralVaultCoreV2Contract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "collateral_vault_core",
            contract,
            project.CollateralVaultCoreV2,
            scope=scope,
            pools=pools,
            container_name="CollateralVaultCoreV2",
            deployment_deps={"delegation_registry"},
            deployment_args_contracts=["delegation_registry"],
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        return {context[pool, "collateral_vault_peripheral"]: with_pool(Transaction.cvcore_set_cvperiph, pool) for pool in self.pools}


@dataclass
class CryptoPunksVaultCoreContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "cryptopunks_vault_core",
            contract,
            project.CryptoPunksVaultCore,
            scope=scope,
            pools=pools,
            container_name="CryptoPunksVaultCore",
            deployment_deps={"punk", "delegation_registry"},
            config_deps={
                f"{scope}.collateral_vault_peripheral": partial(Transaction.punksvault_set_cvperiph, scope=scope),
            },
            deployment_args_contracts=["punk", "delegation_registry"],
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        return {context[pool, "collateral_vault_peripheral"]: with_pool(Transaction.punksvault_set_cvperiph, pool) for pool in self.pools}


@dataclass
class CollateralVaultPeripheralContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "collateral_vault_peripheral",
            contract,
            project.CollateralVaultPeripheral,
            scope=scope,
            pools=pools,
            container_name="CollateralVaultPeripheral",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        set_liquidationsperiph = { context[pool, "liquidations_peripheral"]: with_pool(Transaction.cvperiph_set_liquidationsperiph, pool) for pool in self.pools}
        add_loansperiph = { context[pool, "loans"]: with_pool(Transaction.cvperiph_add_loansperiph, pool) for pool in self.pools}
        add_punksvault = { context[pool, "cryptopunks_vault_core"]: with_pool(Transaction.cvperiph_add_punksvault, pool) for pool in self.pools}
        return set_liquidationsperiph | add_loansperiph | add_punksvault

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context[c].contract for c in self.deployment_dependencies(context)]

    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return {context[pool, "collateral_vault_core"] for pool in self.pools}


@dataclass
class LendingPoolCoreContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "lending_pool_core",
            contract,
            project.LendingPoolCore,
            scope=scope,
            pools=pools,
            container_name="LendingPoolCore",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        return {context[self.pools[0], "lending_pool_peripheral"]: with_pool(Transaction.lpcore_set_lpperiph, self.pools[0])}

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context[c].contract for c in self.deployment_dependencies(context)]

    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return {context[pool, "token"] for pool in self.pools}


@dataclass
class LendingPoolLockContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "lending_pool_lock",
            contract,
            project.LendingPoolLock,
            scope=scope,
            pools=pools,
            container_name="LendingPoolLock",
            deployment_deps=[f"{scope}.token"],
            config_deps={
                f"{scope}.lending_pool_peripheral": partial(Transaction.lplock_set_lpperiph, scope=scope),
            },
            deployment_args_contracts=[f"{scope}.token"],
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        pool = self.pools[0]
        return {context[pool, "lending_pool_peripheral"]: with_pool(Transaction.lplock_set_lpperiph, pool)}

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context[c].contract for c in self.deployment_dependencies(context)]

    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return {context[pool, "token"] for pool in self.pools}


@dataclass
class WETH9MockContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "token",
            contract,
            project.WETH9Mock,
            scope=scope,
            pools=pools,
            container_name="WETH9Mock",
            deployment_deps=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return ["WETH", "WETH", 18, 1000]

    def config_key(self):
        return "token"


@dataclass
class USDCMockContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "token",
            contract,
            project.WETH9Mock,
            scope=scope,
            pools=pools,
            container_name="WETH9Mock",
            deployment_deps=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return ["USDC", "USDC", 6, int(1e9)]

    def config_key(self):
        return "token"


@dataclass
class CryptoPunksMockContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance] = None):
        super().__init__(
            "punk",
            contract,
            project.CryptoPunksMarketMock,
            container_name="CryptoPunksMarketMock",
            deployment_deps=[],
        )
        self.nft = True

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return []


@dataclass
class DelegationRegistryMockContract(InternalContract):

    def __init__(self, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "delegation_registry",
            contract,
            project.DelegationRegistryMock,
            pools=pools,
            container_name="DelegationRegistryMock",
            deployment_deps=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return []


@dataclass
class LendingPoolPeripheralContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "lending_pool_peripheral",
            contract,
            project.LendingPoolPeripheral,
            scope=scope,
            pools=pools,
            container_name="LendingPoolPeripheral",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        set_loansperiph = {
            context[pool, "loans"]: with_pool(Transaction.lpperiph_set_loansperiph, pool) for pool in self.pools
        }
        set_liquidationsperiph = {
            context[pool, "liquidations_peripheral"]: with_pool(Transaction.lpperiph_set_liquidationsperiph, pool)
            for pool in self.pools
        }
        set_liquiditycontrols = {
            context[pool, "liquidity_controls"]: with_pool(Transaction.lpperiph_set_liquiditycontrols, pool) for pool in self.pools
        }
        return set_loansperiph | set_liquidationsperiph | set_liquiditycontrols


    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return set().union(
            {context[pool, "lending_pool_core"] for pool in self.pools},
            {context[pool, "lending_pool_lock"] for pool in self.pools},
            {context[pool, "token"] for pool in self.pools},
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        pool = self.pools[0]
        whitelisted = context.config.get(f"lpp_whitelist_enabled.{pool}", False)
        protocol_wallet_fees = context.config.get(f"lpp_protocol_wallet_fees.{pool}", context.owner)
        protocol_fees_share = context.config.get(f"lpp_protocol_fees_share.{pool}", 2500)
        max_capital_efficiency = context.config.get(f"lpp_max_capital_efficiency.{pool}", 8000)
        return [
            context[context[pool, "lending_pool_core"]].contract,
            context[context[pool, "lending_pool_lock"]].contract,
            context[context[pool, "token"]].contract,
            protocol_wallet_fees,
            protocol_fees_share,
            max_capital_efficiency,
            whitelisted,
        ]

    def config_key(self):
        return "lending_pool"


@dataclass
class LoansCoreContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "loans_core",
            contract,
            project.LoansCore,
            scope=scope,
            pools=pools,
            container_name="LoansCore",
            deployment_deps={},
            deployment_args_contracts=[],
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        return {context[pool, "loans"]: with_pool(Transaction.loanscore_set_loansperiph, pool) for pool in self.pools}


@dataclass
class LoansPeripheralContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "loans",
            contract,
            project.Loans,
            scope=scope,
            pools=pools,
            container_name="Loans",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        set_liquidationsperiph = {
            context[pool, "liquidations_peripheral"]: with_pool(Transaction.loansperiph_set_liquidationsperiph, pool)
            for pool in self.pools
        }
        set_liquiditycontrols = {
            context[pool, "liquidity_controls"]: with_pool(Transaction.loansperiph_set_liquiditycontrols, pool) for pool in self.pools
        }
        set_lpperiph = {
            context[pool, "lending_pool_peripheral"]: with_pool(Transaction.loansperiph_set_lpperiph, pool) for pool in self.pools
        }
        set_cvperiph = {
            context[pool, "collateral_vault_peripheral"]: with_pool(Transaction.loansperiph_set_cvperiph, pool) for pool in self.pools
        }
        return set_liquidationsperiph | set_liquiditycontrols | set_lpperiph | set_cvperiph


    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return set().union(
            {context[pool, "loans_core"] for pool in self.pools},
            {context[pool, "lending_pool_peripheral"] for pool in self.pools},
            {context[pool, "collateral_vault_peripheral"] for pool in self.pools},
            {context[pool, "genesis"] for pool in self.pools},
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        pool = self.pools[0]
        is_payable = context.config.get(f"loansperipheral_ispayable.{pool}", False)
        return [
            24 * 60 * 60,
            context[context[pool, "loans_core"]].contract,
            context[context[pool, "lending_pool_peripheral"]].contract,
            context[context[pool, "collateral_vault_peripheral"]].contract,
            context[context[pool, "genesis"]].contract,
            is_payable,
        ]


@dataclass
class LiquidationsCoreContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "liquidations_core",
            contract,
            project.LiquidationsCore,
            scope=scope,
            pools=pools,
            container_name="LiquidationsCore",
            deployment_deps={},
            deployment_args_contracts=[],
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        return {context[pool, "liquidations_peripheral"]: with_pool(Transaction.liquidationscore_set_liquidationsperiph, pool) for pool in self.pools}


@dataclass
class LiquidationsPeripheralContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "liquidations_peripheral",
            contract,
            project.LiquidationsPeripheral,
            scope=scope,
            pools=pools,
            container_name="LiquidationsPeripheral",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        add_loanscore = {
            context[pool, "loans_core"]: with_pool(Transaction.liquidationsperiph_add_loanscore, pool) for pool in self.pools
        }
        add_lpperiph = {
            context[pool, "lending_pool_peripheral"]: with_pool(Transaction.liquidationsperiph_add_lpperiph, pool) for pool in self.pools
        }
        set_cvperiph = {
            context[pool, "collateral_vault_peripheral"]: with_pool(Transaction.liquidationsperiph_set_cvperiph, pool) for pool in self.pools
        }
        set_liquidatonscore = {
            context[pool, "liquidations_core"]: with_pool(Transaction.liquidationsperiph_set_liquidationscore, pool) for pool in self.pools
        }
        nftxvaultfactory = {
            "nftxvaultfactory": with_pool(Transaction.liquidationsperiph_set_nftxvaultfactory, pool) for pool in self.pools
        }
        nftxmarketplacezap = {
            "nftxmarketplacezap": with_pool(Transaction.liquidationsperiph_set_nftxmarketplacezap, pool) for pool in self.pools
        }
        sushirouter = {
            "sushirouter": with_pool(Transaction.liquidationsperiph_set_sushirouter, pool) for pool in self.pools
        }
        wpunk = { "wpunk": with_pool(Transaction.liquidationsperiph_set_wpunks, pool) for pool in self.pools }

        return add_loanscore | add_lpperiph | set_cvperiph | set_liquidatonscore | nftxvaultfactory | nftxmarketplacezap | sushirouter | wpunk


    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return set().union(
            {context[pool, "liquidations_core"] for pool in self.pools},
            {context[pool, "token"] for pool in self.pools},
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        pool = self.pools[0]
        return [
            context[context[pool, "liquidations_core"]].contract,
            2 * 86400,
            2 * 86400,
            2 * 86400,
            context[context[pool, "token"]].contract,
        ]


@dataclass
class LiquidityControlsContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "liquidity_controls",
            contract,
            project.LiquidityControls,
            scope=scope,
            pools=pools,
            container_name="LiquidityControls",
            deployment_deps={},
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        return {"nft_borrowable_amounts": with_pool(Transaction.liquiditycontrols_change_collectionborrowableamounts, pool) for pool in self.pools}

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            False,
            1500,
            False,
            7 * 24 * 60 * 60,
            False,
            1500,
            False,
        ]


@dataclass
class GenesisContract(InternalContract):

    def __init__(self, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "genesis",
            contract,
            project.GenesisPass,
            container_name="GenesisPass",
            pools=pools,
            deployment_deps={},
            config_deps={},
            deployment_args_contracts=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context["genesis_owner"]]


@dataclass
class CollateralVaultOTCImplContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance] = None):
        super().__init__(
            "collateral_vault_otc_impl",
            contract,
            project.CollateralVaultOTC,
            container_name="CollateralVaultOTC",
            deployment_deps={"punk", "delegation_registry"},
            config_deps={},
            deployment_args_contracts=["punk", "delegation_registry"],
        )


@dataclass
class CollateralVaultOTCContract(MinimalProxy):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "collateral_vault",
            contract,
            project.CollateralVaultOTC,
            scope=scope,
            pools=pools,
            container_name="CollateralVaultOTC",
            deployment_deps={"collateral_vault_otc_impl"},
            impl="collateral_vault_otc_impl",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        set_liquidations = { context[pool, "liquidations"]: with_pool(Transaction.cvotc_set_liquidations, pool) for pool in self.pools}
        add_loansperiph = { context[pool, "loans"]: with_pool(Transaction.cvotc_add_loansperiph, pool) for pool in self.pools}
        return set_liquidations | add_loansperiph


@dataclass
class LendingPoolOTCEthImplContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance] = None):
        super().__init__(
            "lending_pool_otc_weth_impl",
            contract,
            project.CollateralVaultOTC,
            container_name="LendingPoolOTC",
            deployment_deps={"token"},
            config_deps={},
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context[context["weth", "token"]].contract, True]


@dataclass
class LendingPoolOTCContract(MinimalProxy):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "lending_pool",
            contract,
            project.LendingPoolOTC,
            scope=scope,
            pools=pools,
            container_name="LendingPoolOTC",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        set_loansperiph = {
            context[pool, "loans"]: with_pool(Transaction.lpotc_set_loansperiph, pool) for pool in self.pools
        }
        set_liquidationsperiph = {
            context[pool, "liquidations"]: with_pool(Transaction.lpotc_set_liquidations, pool)
            for pool in self.pools
        }
        return set_loansperiph | set_liquidationsperiph


    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return set().union(
            {context[pool, "lending_pool"] for pool in self.pools},
            {context[pool, "token"] for pool in self.pools},
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        pool = self.pools[0]
        lender = context.config[f"lender.{pool}"]
        protocol_wallet_fees = context.config.get(f"lpp_protocol_wallet_fees.{pool}", context.owner)
        protocol_fees_share = context.config.get(f"lpp_protocol_fees_share.{pool}", 2500)
        return [protocol_wallet_fees, protocol_fees_share, lender]

    def config_key(self):
        return "lending_pool"



@dataclass
class LiquidationsOTCContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "liquidations",
            contract,
            project.LiquidationsOTC,
            scope=scope,
            pools=pools,
            container_name="LiquidationsOTC",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        add_loanscore = {
            context[pool, "loans_core"]: with_pool(Transaction.liquidationsotc_add_loanscore, pool) for pool in self.pools
        }
        add_lpperiph = {
            context[pool, "lending_pool"]: with_pool(Transaction.liquidationsotc_add_lpperiph, pool) for pool in self.pools
        }
        set_cvperiph = {
            context[pool, "collateral_vault"]: with_pool(Transaction.liquidationsotc_set_cvperiph, pool) for pool in self.pools
        }

        return add_loanscore | add_lpperiph | set_cvperiph


    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return set().union(
            {context[pool, "token"] for pool in self.pools},
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        pool = self.pools[0]
        return [2 * 86400, context[context[pool, "token"]].contract]


@dataclass
class LoansOTCCoreContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "loans_core",
            contract,
            project.LoansCore,
            scope=scope,
            pools=pools,
            container_name="LoansCore",
            deployment_deps={},
            deployment_args_contracts=[],
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        return {context[pool, "loans"]: with_pool(Transaction.loanscore_set_loansperiph, pool) for pool in self.pools}


@dataclass
class LoansOTCPeripheralContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ContractInstance] = None):
        super().__init__(
            "loans",
            contract,
            project.Loans,
            scope=scope,
            pools=pools,
            container_name="Loans",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        set_liquidationsperiph = {
            context[pool, "liquidations"]: with_pool(Transaction.loansotcperiph_set_liquidationsperiph, pool)
            for pool in self.pools
        }
        set_liquiditycontrols = {
            context[pool, "liquidity_controls"]: with_pool(Transaction.loansotcperiph_set_liquiditycontrols, pool) for pool in self.pools
        }
        set_lpperiph = {
            context[pool, "lending_pool"]: with_pool(Transaction.loansotcperiph_set_lpperiph, pool) for pool in self.pools
        }
        set_cvperiph = {
            context[pool, "collateral_vault"]: with_pool(Transaction.loansotcperiph_set_cvperiph, pool) for pool in self.pools
        }
        return set_liquidationsperiph | set_liquiditycontrols | set_lpperiph | set_cvperiph


    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return set().union(
            {context[pool, "loans_core"] for pool in self.pools},
            {context[pool, "lending_pool"] for pool in self.pools},
            {context[pool, "collateral_vault"] for pool in self.pools},
            {context[pool, "genesis"] for pool in self.pools},
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        pool = self.pools[0]
        is_payable = context.config.get(f"loansperipheral_ispayable.{pool}", False)
        return [
            24 * 60 * 60,
            context[context[pool, "loans_core"]].contract,
            context[context[pool, "lending_pool"]].contract,
            context[context[pool, "collateral_vault"]].contract,
            context[context[pool, "genesis"]].contract,
            is_payable,
        ]
