from typing import Optional, Any, Callable
from functools import partial
from brownie.network.contract import ProjectContract
from dataclasses import dataclass
from .types import InternalContract, DeploymentContext
from .transactions import Transaction

from brownie import (
    CollateralVaultCoreV2,
    CollateralVaultPeripheral,
    CryptoPunksMarketMock,
    CryptoPunksVaultCore,
    DelegationRegistryMock,
    GenesisPass,
    LendingPoolCore,
    LendingPoolLock,
    LendingPoolPeripheral,
    LiquidationsCore,
    LiquidationsPeripheral,
    LiquidityControls,
    Loans,
    LoansCore,
    WETH9Mock,
)


def with_pool(f, pool):
    return partial(f, pool=pool)

@dataclass
class CollateralVaultCoreV2Contract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "collateral_vault_core",
            contract,
            CollateralVaultCoreV2,
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

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "cryptopunks_vault_core",
            contract,
            CryptoPunksVaultCore,
            scope=scope,
            pools=pools,
            container_name="CryptoPunksVaultCore",
            deployment_deps={"punk", "delegation_registry"},
            deployment_args_contracts=["punk", "delegation_registry"],
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        return {context[pool, "collateral_vault_peripheral"]: with_pool(Transaction.punksvault_set_cvperiph, pool) for pool in self.pools}


@dataclass
class CollateralVaultPeripheralContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "collateral_vault_peripheral",
            contract,
            CollateralVaultPeripheral,
            scope=scope,
            pools=pools,
            container_name="CollateralVaultPeripheral",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        set_liquidationsperiph = { context[pool, "liquidations_peripheral"]: with_pool(Transaction.cvperiph_set_liquidationsperiph, pool) for pool in self.pools}
        add_loansperiph = { context[pool, "loans"]: with_pool(Transaction.loansperiph_set_cvperiph, pool) for pool in self.pools}
        add_punksvault = { context[pool, "cryptopunks_vault_core"]: with_pool(Transaction.cvperiph_add_loansperiph, pool) for pool in self.pools}
        return set_liquidationsperiph | add_loansperiph | add_punksvault

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context[c].contract for c in self.deployment_dependencies(context)]

    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:
        return {context[pool, "collateral_vault_core"] for pool in self.pools}


@dataclass
class LendingPoolCoreContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "lending_pool_core",
            contract,
            LendingPoolCore,
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

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "lending_pool_lock",
            contract,
            LendingPoolLock,
            scope=scope,
            pools=pools,
            container_name="LendingPoolLock",
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

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "token",
            contract,
            WETH9Mock,
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

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "token",
            contract,
            WETH9Mock,
            scope=scope,
            pools=pools,
            container_name="WETH9Mock",
            deployment_deps=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return ["USDC", "USDC", 6, 1e9]

    def config_key(self):
        return "token"


@dataclass
class CryptoPunksMockContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract] = None):
        super().__init__(
            "punk",
            contract,
            CryptoPunksMarketMock,
            container_name="CryptoPunksMarketMock",
            deployment_deps=[],
        )
        self.nft = True

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return []


@dataclass
class DelegationRegistryMockContract(InternalContract):

    def __init__(self, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "delegation_registry",
            contract,
            DelegationRegistryMock,
            pools=pools,
            container_name="DelegationRegistryMock",
            deployment_deps=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return []


@dataclass
class LendingPoolPeripheralContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "lending_pool_peripheral",
            contract,
            LendingPoolPeripheral,
            scope=scope,
            pools=pools,
            container_name="LendingPoolPeripheral",
        )

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        pool = self.pools[0]
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
        return [
            context[context[pool, "lending_pool_core"]].contract,
            context[context[pool, "lending_pool_lock"]].contract,
            context[context[pool, "token"]].contract,
            context.owner,
            2500,
            8000,
            False,
        ]

    def config_key(self):
        return "lending_pool"


@dataclass
class LoansCoreContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "loans_core",
            contract,
            LoansCore,
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

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "loans",
            contract,
            Loans,
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
        return [
            24 * 60 * 60,
            context[context[pool, "loans_core"]].contract,
            context[context[pool, "lending_pool_peripheral"]].contract,
            context[context[pool, "collateral_vault_peripheral"]].contract,
            context[context[pool, "genesis"]].contract,
        ]


@dataclass
class LiquidationsCoreContract(InternalContract):

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "liquidations_core",
            contract,
            LiquidationsCore,
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

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "liquidations_peripheral",
            contract,
            LiquidationsPeripheral,
            scope=scope,
            pools=pools,
            container_name="LiquidationsPeripheral",
        )


    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:
        pool = self.pools[0]
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

    def __init__(self, scope: str, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "liquidity_controls",
            contract,
            LiquidityControls,
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

    def __init__(self, pools: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "genesis",
            contract,
            GenesisPass,
            pools=pools,
            container_name="GenesisPass",
            deployment_deps={},
            config_deps={},
            deployment_args_contracts=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context["genesis_owner"]]

