from typing import Optional, Any
from ape.contracts.base import ContractInstance
from dataclasses import dataclass
from .basetypes import InternalContract, DeploymentContext
from .transactions import Transaction

from ape import project


@dataclass
class CollateralVaultCoreContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "collateral_vault_core",
            contract,
            project.CollateralVaultCore,
            container_name="CollateralVaultCore",
            deployment_deps={},
            config_deps={
                "collateral_vault_peripheral": Transaction.cvcore_set_cvperiph,
            },
            deployment_args_contracts=[],
        )


# @dataclass
# class CollateralVaultCoreV2Contract(InternalContract):

#     def __init__(self, contract: Optional[ContractInstance]):
#         super().__init__(
#             "collateral_vault_core2",
#             contract,
#             project.CollateralVaultCoreV2,
#             container_name="CollateralVaultCoreV2",
#             deployment_deps={"delegation_registry"},
#             config_deps={
#                 "collateral_vault_peripheral": Transaction.cvcore2_set_cvperiph,
#             },
#             deployment_args_contracts=["delegation_registry"],
#         )


@dataclass
class CryptoPunksVaultCoreContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "cryptopunks_vault_core",
            contract,
            project.CryptoPunksVaultCore,
            container_name="CryptoPunksVaultCore",
            deployment_deps={"punk"},
            # deployment_deps={"punk", "delegation_registry"},
            config_deps={
                "collateral_vault_peripheral": Transaction.punksvault_set_cvperiph,
            },
            # deployment_args_contracts=["punk", "delegation_registry"],
            deployment_args_contracts=["punk"],
        )


@dataclass
class CollateralVaultPeripheralContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "collateral_vault_peripheral",
            contract,
            project.CollateralVaultPeripheral,
            container_name="CollateralVaultPeripheral",
            # deployment_deps={"collateral_vault_core", "collateral_vault_core2"},
            deployment_deps={"collateral_vault_core"},
            config_deps={
                "liquidations_peripheral": Transaction.cvperiph_set_liquidationsperiph,
                "loans": Transaction.cvperiph_add_loansperiph,
                "cryptopunks_vault_core": Transaction.cvperiph_add_punksvault,
            },
            # deployment_args_contracts=["collateral_vault_core2", "collateral_vault_core"],
            deployment_args_contracts=["collateral_vault_core"],
        )


@dataclass
class LendingPoolCoreContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "lending_pool_core",
            contract,
            project.LendingPoolCore,
            container_name="LendingPoolCore",
            deployment_deps=["weth"],
            config_deps={"lending_pool_peripheral": Transaction.lpcore_set_lpperiph},
            deployment_args_contracts=["weth"],
        )


@dataclass
class LendingPoolLockContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "lending_pool_lock",
            contract,
            project.LendingPoolLock,
            container_name="LendingPoolLock",
            deployment_deps=["weth"],
            config_deps={
                "lending_pool_peripheral": Transaction.lplock_set_lpperiph,
            },
            deployment_args_contracts=["weth"],
        )


@dataclass
class WETH9MockContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "weth",
            contract,
            project.WETH9Mock,
            container_name="WETH9Mock",
            deployment_deps=[],
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return ["WETH", "WETH", 18, 1000]

    def config_key(self):
        return "token"


@dataclass
class CryptoPunksMockContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
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


# @dataclass
# class DelegationRegistryMockContract(InternalContract):

#     def __init__(self, contract: Optional[ContractInstance]):
#         super().__init__(
#             "delegation_registry",
#             contract,
#             project.DelegationRegistryMock,
#             container_name="DelegationRegistryMock",
#             deployment_deps=[],
#         )

#     def deployment_args(self, context: DeploymentContext) -> list[Any]:
#         return []


@dataclass
class LendingPoolPeripheralContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "lending_pool_peripheral",
            contract,
            project.LendingPoolPeripheral,
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

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "loans_core",
            contract,
            project.LoansCore,
            container_name="LoansCore",
            deployment_deps={},
            config_deps={"loans": Transaction.loanscore_set_loansperiph},
            deployment_args_contracts=[],
        )


@dataclass
class LoansPeripheralContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "loans",
            contract,
            project.Loans,
            container_name="Loans",
            deployment_deps={"loans_core", "lending_pool_peripheral", "collateral_vault_peripheral"},
            config_deps={
                "liquidations_peripheral": Transaction.loansperiph_set_liquidationsperiph,
                "liquidity_controls": Transaction.loansperiph_set_liquiditycontrols,
                "lending_pool_peripheral": Transaction.loansperiph_set_lpperiph,
                "collateral_vault_peripheral": Transaction.loansperiph_set_cvperiph,
            },
        )

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [
            24 * 60 * 60,
            context["loans_core"].contract,
            context["lending_pool_peripheral"].contract,
            context["collateral_vault_peripheral"].contract,
        ]


@dataclass
class LiquidationsCoreContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "liquidations_core",
            contract,
            project.LiquidationsCore,
            container_name="LiquidationsCore",
            deployment_deps={},
            config_deps={
                "liquidations_peripheral": Transaction.liquidationscore_set_liquidationsperiph,
            },
            deployment_args_contracts=[],
        )


@dataclass
class LiquidationsPeripheralContract(InternalContract):

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "liquidations_peripheral",
            contract,
            project.LiquidationsPeripheral,
            container_name="LiquidationsPeripheral",
            deployment_deps={"liquidations_core", "weth", "collateral_vault_peripheral"},
            config_deps={
                "liquidations_core": Transaction.liquidationsperiph_set_liquidationscore,
                "loans_core": Transaction.liquidationsperiph_add_loanscore,
                "lending_pool_peripheral": Transaction.liquidationsperiph_add_lpperiph,
                "collateral_vault_peripheral": Transaction.liquidationsperiph_set_cvperiph,
                "nftxvaultfactory": Transaction.liquidationsperiph_set_nftxvaultfactory,
                "nftxmarketplacezap": Transaction.liquidationsperiph_set_nftxmarketplacezap,
                "sushirouter": Transaction.liquidationsperiph_set_sushirouter,
                "punk": Transaction.liquidationsperiph_set_wpunks,
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

    def __init__(self, contract: Optional[ContractInstance]):
        super().__init__(
            "liquidity_controls",
            contract,
            project.LiquidityControls,
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
