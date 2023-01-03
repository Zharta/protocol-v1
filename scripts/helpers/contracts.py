from typing import Optional, Any
from brownie.network.contract import ProjectContract
from dataclasses import dataclass
from .types import InternalContract, DeploymentContext
from .transactions import Transaction

from brownie import (
    LendingPoolCore,
    LendingPoolLock,
    LendingPoolPeripheral,
    CollateralVaultCore,
    CollateralVaultPeripheral,
    LPCMigration01,
    LoansCore,
    Loans,
    LiquidationsCore,
    LiquidationsPeripheral,
    LiquidityControls,
    web3
)


@dataclass
class CollateralVaultCoreContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "collateral_vault_core",
            contract,
            CollateralVaultCore,
            container_name="CollateralVaultCore",
            deployment_deps={},
            config_deps={
                "collateral_vault_peripheral": Transaction.cvcore_set_cvperiph,
            },
            deployment_args_contracts=[],
        )


@dataclass
class CollateralVaultPeripheralContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "collateral_vault_peripheral",
            contract,
            CollateralVaultPeripheral,
            container_name="CollateralVaultPeripheral",
            deployment_deps={"collateral_vault_core"},
            config_deps={
                "liquidations_peripheral": Transaction.cvperiph_set_liquidationsperiph,
                "loans": Transaction.cvperiph_add_loansperiph,
            },
            deployment_args_contracts=["collateral_vault_core"],
        )


@dataclass
class LendingPoolCoreContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "lending_pool_core",
            contract,
            LendingPoolCore,
            container_name="LendingPoolCore",
            deployment_deps=["weth"],
            config_deps={"lending_pool_peripheral": Transaction.lpcore_set_lpperiph},
            deployment_args_contracts=["weth"],
        )


@dataclass
class LendingPoolLockContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "lending_pool_lock",
            contract,
            LendingPoolLock,
            container_name="LendingPoolLock",
            deployment_deps=["weth"],
            config_deps={
                "lending_pool_peripheral": Transaction.lplock_set_lpperiph,
                "lenders_with_active_locks": Transaction.lplock_migrate
            },
            deployment_args_contracts=["weth"],
        )


@dataclass
class LPCMigration01Contract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "lpc_migration_01",
            contract,
            LPCMigration01,
            container_name="LPCMigration01",
            deployment_deps=["lending_pool_core", "legacy_lending_pool_core"],
            config_deps={"run_lpc_migration_01": Transaction.lpc_migration_migrate},
            deployment_args_contracts=["legacy_lending_pool_core", "lending_pool_core"],
        )


@dataclass
class LendingPoolPeripheralContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "lending_pool_peripheral",
            contract,
            LendingPoolPeripheral,
            container_name="LendingPoolPeripheral",
            deployment_deps={"lending_pool_core", "lending_pool_lock", "weth"},
            config_deps={
                "loans": Transaction.lpperiph_set_loansperiph,
                "liquidations_peripheral": Transaction.lpperiph_set_liquidationsperiph,
                "liquidity_controls": Transaction.lpperiph_set_liquiditycontrols,
            },
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            context["lending_pool_core"].contract,
            context["lending_pool_lock"].contract,
            context["weth"].contract,
            context.owner,
            2500,
            7000,
            False,
        ]

    def config_key(self):
        return "lending_pool"


@dataclass
class LoansCoreContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "loans_core",
            contract,
            LoansCore,
            container_name="LoansCore",
            deployment_deps={},
            config_deps={"loans": Transaction.loanscore_set_loansperiph},
            deployment_args_contracts=[],
        )


@dataclass
class LoansPeripheralContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "loans",
            contract,
            Loans,
            container_name="Loans",
            deployment_deps={"loans_core", "lending_pool_peripheral", "collateral_vault_peripheral"},
            config_deps={
                "liquidations_peripheral": Transaction.loansperiph_set_liquidationsperiph,
                "liquidity_controls": Transaction.loansperiph_set_liquiditycontrols,
                "lending_pool_peripheral": Transaction.loansperiph_set_lpperiph,
                "collateral_vault_peripheral": Transaction.loansperiph_set_cvperiph,
                "cool_cats": Transaction.loansperiph_add_collateral_cool_cats,
                "hashmasks": Transaction.loansperiph_add_collateral_hashmasks,
                "bakc": Transaction.loansperiph_add_collateral_bakc,
                "doodles": Transaction.loansperiph_add_collateral_doodles,
                "wow": Transaction.loansperiph_add_collateral_wow,
                "mayc": Transaction.loansperiph_add_collateral_mayc,
                "veefriends": Transaction.loansperiph_add_collateral_veefriends,
                "pudgy_penguins": Transaction.loansperiph_add_collateral_pudgy_penguins,
                "bayc": Transaction.loansperiph_add_collateral_bayc,
                "wpunks": Transaction.loansperiph_add_collateral_wpunks,
                "cryptopunks": Transaction.loansperiph_add_collateral_punks,
            },
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            1000000,
            31 * 86400,
            web3.toWei(10000, "ether"),
            24 * 60 * 60,
            context["loans_core"].contract,
            context["lending_pool_peripheral"].contract,
            context["collateral_vault_peripheral"].contract,
        ]


@dataclass
class LiquidationsCoreContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "liquidations_core",
            contract,
            LiquidationsCore,
            container_name="LiquidationsCore",
            deployment_deps={},
            config_deps={
                "liquidations_core": Transaction.liquidationscore_set_liquidationsperiph,
            },
            deployment_args_contracts=[],
        )


@dataclass
class LiquidationsPeripheralContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "liquidations_peripheral",
            contract,
            LiquidationsPeripheral,
            container_name="LiquidationsPeripheral",
            deployment_deps={"liquidations_core", "weth", "collateral_vault_peripheral"},
            config_deps={
                "liquidations_core": Transaction.liquidationsperiph_set_liquidationscore,
                "loans_core": Transaction.liquidationsperiph_add_loanscore,
                "lending_pool_peripheral": Transaction.liquidationsperiph_add_lpperiph,
                "collateral_vault_peripheral": Transaction.liquidationsperiph_set_cvperiph,
                "nftxvaultfactory": Transaction.liquidationsperiph_set_nftxvaultfactory,
                "nftxmarketplacezap": Transaction.liquidationsperiph_set_nftxmarketplacezap,
                "sushirouter, ": Transaction.liquidationsperiph_set_sushirouter,
            },
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            context["liquidations_core"].contract,
            2 * 86400,
            2 * 86400,
            2 * 86400,
            context["weth"].contract,
        ]


@dataclass
class LiquidityControlsContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "liquidity_controls",
            contract,
            LiquidityControls,
            container_name="LiquidityControls",
            deployment_deps={},
            config_deps={"nft_borrowable_amounts": Transaction.liquiditycontrols_change_collectionborrowableamounts},
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
