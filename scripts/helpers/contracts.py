from typing import Optional, Any
from brownie.network.contract import ProjectContract
from types import InternalContract, DeploymentContext
from transactions import Transactions
from dataclasses import dataclass

from brownie import (
    LendingPoolCore,
    LendingPoolPeripheral,
    CollateralVaultCore,
    CollateralVaultPeripheral,
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
                "collateral_vault_peripheral": Transactions.cvcore_set_cvperiph,
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
                "liquidations_peripheral": Transactions.cvperiph_set_liquidationsperiph,
                "loans": Transactions.cvperiph_add_loansperiph,
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
            deployment_deps=["token"],
            config_deps={"lending_pool_peripheral", Transactions.lpcore_set_lpperiph},
            deployment_args_contracts=["token"],
        )


@dataclass
class LendingPoolPeripheralContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "lending_pool_peripheral",
            contract,
            LendingPoolPeripheral,
            container_name="LendingPoolPeripheral",
            deployment_deps={"lending_pool_core", "weth"},
            config_deps={
                "loans": Transactions.lpperiph_set_loansperiph,
                "liquidations_peripheral": Transactions.lpperiph_set_liquidationsperiph,
                "liquidity_controls": Transactions.lpperiph_set_liquiditycontrols,
            },
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            context.contracts["lending_pool_core"],
            context.contracts["weth"],
            context.owner,
            2500,
            7000,
            False,
        ]


@dataclass
class LoansCoreContract(InternalContract):

    def __init__(self, contract: Optional[ProjectContract]):
        super().__init__(
            "loans_core",
            contract,
            LoansCore,
            container_name="LoansCore",
            deployment_deps={},
            config_deps={"loans": Transactions.loanscore_set_loansperiph},
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
                "liquidations_peripheral": Transactions.loansperiph_set_liquidationsperiph,
                "liquidity_controls": Transactions.loansperiph_set_liquiditycontrols,
                "lending_pool_peripheral": Transactions.loansperiph_set_lpperiph,
                "collateral_vault_peripheral": Transactions.loansperiph_set_cvperiph,
                "cool_cats": Transactions.loansperiph_add_collateral_cool_cats,
                "hashmasks": Transactions.loansperiph_add_collateral_hashmasks,
                "bakc": Transactions.loansperiph_add_collateral_bakc,
                "doodles": Transactions.loansperiph_add_collateral_doodles,
                "wow": Transactions.loansperiph_add_collateral_wow,
                "mayc": Transactions.loansperiph_add_collateral_mayc,
                "veefriends": Transactions.loansperiph_add_collateral_veefriends,
                "pudgy_penguins": Transactions.loansperiph_add_collateral_pudgy_penguins,
                "bayc": Transactions.loansperiph_add_collateral_bayc,
                "wpunks": Transactions.loansperiph_add_collateral_wpunks,
                "cryptopunks": Transactions.loansperiph_add_collateral_cryptopunks,
            },
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            1000000,
            31 * 86400,
            web3.toWei(10000, "ether"),
            24 * 60 * 60,
            context.contracts["loans_core"],
            context.contracts["lending_pool_peripheral"],
            context.contracts["collateral_vault_peripheral"],
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
                "liquidations_core": Transactions.liquidationscore_set_liquidationsperiph,
                "loans_core": Transactions.liquidationscore_add_loanscore,

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
            deployment_deps={"liquidations_core", "token", "collateral_vault_peripheral"},
            config_deps={
                "liquidations_core": Transactions.liquidationsperiph_set_liquidationscore,
                "loans_core": Transactions.liquidationsperiph_add_loanscore,
                "lending_pool_peripheral": Transactions.liquidationsperiph_add_lpperiph,
                "collateral_vault_peripheral": Transactions.liquidationsperiph_set_cvperiph,
                "nftxvaultfactory": Transactions.liquidationsperiph_set_nftxvaultfactory,
                "nftxmarketplacezap": Transactions.liquidationsperiph_set_nftxmarketplacezap,
                "sushirouter, ": Transactions.liquidationsperiph_set_sushirouter,
            },
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            context.contracts["liquidations_core"],
            2 * 86400,
            2 * 86400,
            2 * 86400,
            context.contracts["token"],
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
            config_deps={"nft_borrowable_amounts": Transactions.liquiditycontrols_change_collectionborrowableamounts},
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
