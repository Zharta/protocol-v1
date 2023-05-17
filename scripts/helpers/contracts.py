from typing import Optional, Any
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


@dataclass
class CollateralVaultCoreV2Contract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "collateral_vault_core",
            contract,
            CollateralVaultCoreV2,
            scope=scope,
            container_name="CollateralVaultCoreV2",
            deployment_deps={"delegation_registry"},
            config_deps={
                f"{scope}.collateral_vault_peripheral": partial(Transaction.cvcore_set_cvperiph, scope=scope),
            },
            deployment_args_contracts=["delegation_registry"],
        )


@dataclass
class CryptoPunksVaultCoreContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "cryptopunks_vault_core",
            contract,
            CryptoPunksVaultCore,
            scope=scope,
            container_name="CryptoPunksVaultCore",
            deployment_deps={"punk", "delegation_registry"},
            config_deps={
                f"{scope}.collateral_vault_peripheral": partial(Transaction.punksvault_set_cvperiph, scope=scope),
            },
            deployment_args_contracts=["punk", "delegation_registry"],
        )


@dataclass
class CollateralVaultPeripheralContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "collateral_vault_peripheral",
            contract,
            CollateralVaultPeripheral,
            scope=scope,
            container_name="CollateralVaultPeripheral",
            deployment_deps={f"{scope}.collateral_vault_core"},
            config_deps={
                "liquidations_peripheral": partial(Transaction.cvperiph_set_liquidationsperiph, scope=scope),
                f"{scope}.loans": partial(Transaction.cvperiph_add_loansperiph, scope=scope),
                f"{scope}.cryptopunks_vault_core": partial(Transaction.cvperiph_add_punksvault, scope=scope),
            },
            deployment_args_contracts=[f"{scope}.collateral_vault_core"],
        )


@dataclass
class LendingPoolCoreContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "lending_pool_core",
            contract,
            LendingPoolCore,
            scope=scope,
            container_name="LendingPoolCore",
            deployment_deps=[f"{scope}.token"],
            config_deps={f"{scope}.lending_pool_peripheral": partial(Transaction.lpcore_set_lpperiph, scope=scope)},
            deployment_args_contracts=[f"{scope}.token"],
        )


@dataclass
class LendingPoolLockContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "lending_pool_lock",
            contract,
            LendingPoolLock,
            scope=scope,
            container_name="LendingPoolLock",
            deployment_deps=[f"{scope}.token"],
            config_deps={
                f"{scope}.lending_pool_peripheral": partial(Transaction.lplock_set_lpperiph, scope=scope),
            },
            deployment_args_contracts=[f"{scope}.token"],
        )


@dataclass
class WETH9MockContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "token",
            contract,
            WETH9Mock,
            scope=scope,
            container_name="WETH9Mock",
            deployment_deps=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return ["WETH", "WETH", 18, 1000]

    def config_key(self):
        return "token"


@dataclass
class USDCMockContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "token",
            contract,
            WETH9Mock,
            scope=scope,
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

    def __init__(self, contract: Optional[ProjectContract] = None):
        super().__init__(
            "delegation_registry",
            contract,
            DelegationRegistryMock,
            container_name="DelegationRegistryMock",
            deployment_deps=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return []


@dataclass
class LendingPoolPeripheralContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "lending_pool_peripheral",
            contract,
            LendingPoolPeripheral,
            scope=scope,
            container_name="LendingPoolPeripheral",
            deployment_deps={f"{scope}.lending_pool_core", f"{scope}.lending_pool_lock", f"{scope}-token"},
            config_deps={
                f"{scope}.loans": partial(Transaction.lpperiph_set_loansperiph, scope=scope),
                "liquidations_peripheral": partial(Transaction.lpperiph_set_liquidationsperiph, scope=scope),
                f"{scope}.liquidity_controls": partial(Transaction.lpperiph_set_liquiditycontrols, scope=scope),
            },
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            context[f"{self.scope}.lending_pool_core"].contract,
            context[f"{self.scope}.lending_pool_lock"].contract,
            context[f"{self.scope}.token"].contract,
            context.owner,
            2500,
            8000,
            False,
        ]

    def config_key(self):
        return "lending_pool"


@dataclass
class LoansCoreContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "loans_core",
            contract,
            LoansCore,
            scope=scope,
            container_name="LoansCore",
            deployment_deps={},
            config_deps={f"{scope}.loans": partial(Transaction.loanscore_set_loansperiph, scope=scope)},
            deployment_args_contracts=[],
        )


@dataclass
class LoansPeripheralContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "loans",
            contract,
            Loans,
            scope=scope,
            container_name="Loans",
            deployment_deps={f"{scope}.loans_core", f"{scope}.lending_pool_peripheral", f"{scope}.collateral_vault_peripheral", "genesis"},
            config_deps={
                "liquidations_peripheral": partial(Transaction.loansperiph_set_liquidationsperiph, scope=scope),
                f"{scope}.liquidity_controls": partial(Transaction.loansperiph_set_liquiditycontrols, scope=scope),
                f"{scope}.lending_pool_peripheral": partial(Transaction.loansperiph_set_lpperiph, scope=scope),
                f"{scope}.collateral_vault_peripheral": partial(Transaction.loansperiph_set_cvperiph, scope=scope),
            },
            deployment_args_contracts=[f"{scope}.loans_core", f"{scope}.lending_pool_peripheral", f"{scope}.collateral_vault_peripheral", "genesis"],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            24 * 60 * 60,
            context[f"{self.scope}.loans_core"].contract,
            context[f"{self.scope}.lending_pool_peripheral"].contract,
            context[f"{self.scope}.collateral_vault_peripheral"].contract,
            context["genesis"].contract,
        ]


@dataclass
class LiquidationsCoreContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract] = None):
        super().__init__(
            "liquidations_core",
            contract,
            LiquidationsCore,
            container_name="LiquidationsCore",
            deployment_deps={},
            config_deps={
                "liquidations_peripheral": Transaction.liquidationscore_set_liquidationsperiph,
            },
            deployment_args_contracts=[],
        )


@dataclass
class LiquidationsPeripheralContract(InternalContract):

    def __init__(self, scopes: list[str], contract: Optional[ProjectContract] = None):
        super().__init__(
            "liquidations_peripheral",
            contract,
            LiquidationsPeripheral,
            container_name="LiquidationsPeripheral",
            deployment_deps={"liquidations_core", "weth.token"},
            config_deps={
                "liquidations_core": Transaction.liquidationsperiph_set_liquidationscore,
                "nftxvaultfactory": Transaction.liquidationsperiph_set_nftxvaultfactory,
                "nftxmarketplacezap": Transaction.liquidationsperiph_set_nftxmarketplacezap,
                "sushirouter": Transaction.liquidationsperiph_set_sushirouter,
                "wpunk": Transaction.liquidationsperiph_set_wpunks,
            } | {
                k: v for d in [{
                f"{scope}.loans_core": partial(Transaction.liquidationsperiph_add_loanscore, scope=scope),
                f"{scope}.lending_pool_peripheral": partial(Transaction.liquidationsperiph_add_lpperiph, scope=scope),
                f"{scope}.collateral_vault_peripheral": partial(Transaction.liquidationsperiph_set_cvperiph, scope=scope),
                 } for scope in scopes] for k, v in d.items() 
            },
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            context["liquidations_core"].contract,
            2 * 86400,
            2 * 86400,
            2 * 86400,
            context["weth.token"].contract,
        ]


@dataclass
class LiquidityControlsContract(InternalContract):

    def __init__(self, scope: str, contract: Optional[ProjectContract] = None):
        super().__init__(
            "liquidity_controls",
            contract,
            LiquidityControls,
            scope=scope,
            container_name="LiquidityControls",
            deployment_deps={},
            config_deps={"{scope}.nft_borrowable_amounts": partial(Transaction.liquiditycontrols_change_collectionborrowableamounts, scope=scope)},
        )

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

    def __init__(self, contract: Optional[ProjectContract] = None):
        super().__init__(
            "genesis",
            contract,
            GenesisPass,
            container_name="GenesisPass",
            deployment_deps={},
            config_deps={},
            deployment_args_contracts=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context["genesis_owner"]]

