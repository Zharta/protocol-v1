from brownie import Contract
from brownie.network.account import LocalAccount
from dataclasses import dataclass


@dataclass
class Transaction:
    @staticmethod
    def lpcore_set_lpperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLendingPoolPeripheralAddress(
            address, {"from": owner}
        )

    @staticmethod
    def lpperiph_set_loansperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLoansPeripheralAddress(address, {"from": owner})

    @staticmethod
    def lpperiph_set_liquidationsperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLiquidationsPeripheralAddress(
            address, {"from": owner}
        )

    @staticmethod
    def lpperiph_set_liquiditycontrols(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLiquidityControlsAddress(address, {"from": owner})

    @staticmethod
    def cvcore_set_cvperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setCollateralVaultPeripheralAddress(
            address, {"from": owner}
        )

    @staticmethod
    def cvperiph_add_loansperiph(
        contract_instance: Contract,
        weth_address: str,
        address: str,
        owner: LocalAccount,
    ):
        return contract_instance.addLoansPeripheralAddress(
            weth_address, address, {"from": owner}
        )

    @staticmethod
    def cvperiph_set_liquidationsperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLiquidationsPeripheralAddress(
            address, {"from": owner}
        )

    @staticmethod
    def loanscore_set_loansperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLoansPeripheral(address, {"from": owner})

    @staticmethod
    def loansperiph_set_liquidationsperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLiquidationsPeripheralAddress(
            address, {"from": owner}
        )

    @staticmethod
    def loansperiph_set_liquiditycontrols(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLiquidityControlsAddress(address, {"from": owner})

    @staticmethod
    def loansperiph_set_lpperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLendingPoolPeripheralAddress(
            address, {"from": owner}
        )

    @staticmethod
    def loansperiph_set_cvperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setCollateralVaultPeripheralAddress(
            address, {"from": owner}
        )

    @staticmethod
    def liquidationscore_set_liquidationsperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLiquidationsPeripheralAddress(
            address, {"from": owner}
        )

    @staticmethod
    def liquidationscore_add_loanscore(
        contract_instance: Contract,
        weth_address: str,
        address: str,
        owner: LocalAccount,
    ):
        return contract_instance.addLoansCoreAddress(
            weth_address, address, {"from": owner}
        )

    @staticmethod
    def liquidationsperiph_set_liquidationscore(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setLiquidationsCoreAddress(address, {"from": owner})

    @staticmethod
    def liquidationsperiph_add_loanscore(
        contract_instance: Contract,
        weth_address: str,
        address: str,
        owner: LocalAccount,
    ):
        return contract_instance.addLoansCoreAddress(
            weth_address, address, {"from": owner}
        )

    @staticmethod
    def liquidationsperiph_add_lpperiph(
        contract_instance: Contract,
        weth_address: str,
        address: str,
        owner: LocalAccount,
    ):
        return contract_instance.addLendingPoolPeripheralAddress(
            weth_address, address, {"from": owner}
        )

    @staticmethod
    def liquidationsperiph_set_cvperiph(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setCollateralVaultPeripheralAddress(
            address, {"from": owner}
        )

    @staticmethod
    def liquidationsperiph_set_nftxvaultfactory(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setNFTXVaultFactoryAddress(address, {"from": owner})

    @staticmethod
    def liquidationsperiph_set_nftxmarketplacezap(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setNFTXMarketplaceZapAddress(address, {"from": owner})

    @staticmethod
    def liquidationsperiph_set_sushirouter(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.setSushiRouterAddress(address, {"from": owner})

    @staticmethod
    def loansperiph_add_collateral(
        contract_instance: Contract, address: str, owner: LocalAccount
    ):
        return contract_instance.addCollateralToWhitelist(address, {"from": owner})

    @staticmethod
    def loansperiph_add_collaterals(
        contract_instance: Contract, nft_contracts: list, owner: LocalAccount
    ):
        return [
            Transaction.loansperiph_add_collateral(
                contract_instance, nft_contract, owner
            )
            for nft_contract in nft_contracts
        ]

    @staticmethod
    def liquiditycontrols_change_collectionborrowableamount(
        contract_instance: Contract, address: str, value_wei: int, owner: LocalAccount
    ):
        return contract_instance.changeMaxCollectionBorrowableAmount(
            True, address, value_wei, {"from": owner}
        )

    @staticmethod
    def liquiditycontrols_change_collectionborrowableamounts(
        contract_instance: Contract,
        nft_contracts: list,
        values_wei: list,
        owner: LocalAccount,
    ):
        return [
            Transaction.liquiditycontrols_change_collectionborrowableamount(
                contract_instance, nft_contract, value_wei, owner
            )
            for nft_contract, value_wei in zip(nft_contracts, values_wei)
        ]


@dataclass
class ConfigDependencies:
    @staticmethod
    def lp_core():
        return [Transaction.lpcore_set_lpperiph]

    @staticmethod
    def lp_periph():
        return [
            Transaction.lpcore_set_lpperiph,
            Transaction.lpperiph_set_loansperiph,
            Transaction.liquidationsperiph_add_lpperiph,
            Transaction.lpperiph_set_liquiditycontrols,
            Transaction.loansperiph_set_lpperiph,
        ]

    @staticmethod
    def cv_core():
        return [Transaction.cvcore_set_cvperiph]

    @staticmethod
    def cv_periph():
        return [
            Transaction.cvcore_set_cvperiph,
            Transaction.cvperiph_add_loansperiph,
            Transaction.cvperiph_set_liquidationsperiph,
            Transaction.liquidationsperiph_set_cvperiph,
            Transaction.loansperiph_set_cvperiph,
        ]

    @staticmethod
    def loans_core():
        return [
            Transaction.loanscore_set_loansperiph,
            Transaction.liquidationscore_add_loanscore,
            Transaction.liquidationsperiph_add_loanscore,
        ]

    @staticmethod
    def loans_periph():
        return [
            Transaction.lpperiph_set_loansperiph,
            Transaction.cvperiph_add_loansperiph,
            Transaction.loanscore_set_loansperiph,
            Transaction.loansperiph_set_liquidationsperiph,
            Transaction.loansperiph_set_liquiditycontrols,
            Transaction.loansperiph_add_collaterals,
        ]

    @staticmethod
    def liquidations_core():
        return [
            Transaction.liquidationscore_set_liquidationsperiph,
            Transaction.liquidationscore_add_loanscore,
        ]

    @staticmethod
    def liquidations_periph():
        return [
            Transaction.liquidationsperiph_set_liquidationscore,
            Transaction.lpperiph_set_liquidationsperiph,
            Transaction.cvperiph_set_liquidationsperiph,
            Transaction.loansperiph_set_liquidationsperiph,
            Transaction.liquidationscore_set_liquidationsperiph,
            Transaction.liquidationsperiph_add_loanscore,
            Transaction.liquidationsperiph_add_lpperiph,
            Transaction.liquidationsperiph_set_cvperiph,
            Transaction.liquidationsperiph_set_nftxvaultfactory,
            Transaction.liquidationsperiph_set_nftxmarketplacezap,
            Transaction.liquidationsperiph_set_sushirouter,
        ]

    @staticmethod
    def liquidity_controls():
        return [
            Transaction.lpperiph_set_liquiditycontrols,
            Transaction.loansperiph_set_liquiditycontrols,
            Transaction.liquiditycontrols_change_collectionborrowableamounts,
        ]


@dataclass
class DeployDependencies:
    @staticmethod
    def cv_core():
        return ["collateral_vault_periph"]

    @staticmethod
    def lp_core():
        return ["lending_pool"]

    @staticmethod
    def loans_core():
        return ["loans"]


class DependencyManager:
    def __init__(self, contracts_to_deploy: list):
        self.contracts_to_deploy = contracts_to_deploy

    def _is_included_in_contract_deployment(self, tx: Transaction) -> bool:
        if "loans" in self.contracts_to_deploy:
            if tx == Transaction.loansperiph_set_cvperiph:
                return True
            elif tx == Transaction.loansperiph_set_lpperiph:
                return True
        if "liquidations_peripheral" in self.contracts_to_deploy:
            if tx == Transaction.liquidationsperiph_set_liquidationscore:
                return True
        return False

    def _remove_duplicates(self, txs: list):
        result = []
        for tx in txs:
            if (
                tx != []
                and tx not in result
                and not self._is_included_in_contract_deployment(tx)
            ):
                result.append(tx)
        return result

    def build_transaction_set(self):
        result = []

        for contract in self.contracts_to_deploy:
            match contract:
                case "collateral_vault_core":
                    result.extend(ConfigDependencies.cv_core())
                    deploy_dependencies = [
                        DependencyManager([entry]).build_transaction_set()
                        for entry in DeployDependencies.cv_core()
                    ]
                    result.extend(deploy_dependencies[0])
                case "collateral_vault_peripheral":
                    result.extend(ConfigDependencies.cv_periph())
                case "lending_pool_core":
                    result.extend(ConfigDependencies.lp_core())
                    deploy_dependencies = [
                        DependencyManager([entry]).build_transaction_set()
                        for entry in DeployDependencies.lp_core()
                    ]
                    result.extend(deploy_dependencies[0])
                case "lending_pool":
                    result.extend(ConfigDependencies.lp_periph())
                case "liquidations_peripheral":
                    result.extend(ConfigDependencies.liquidations_periph())
                case "liquidations_core":
                    result.extend(ConfigDependencies.liquidations_core())
                case "liquidity_controls":
                    result.extend(ConfigDependencies.liquidity_controls())
                case "loans":
                    result.extend(ConfigDependencies.loans_periph())
                case "loans_core":
                    result.extend(ConfigDependencies.loans_core())
                    deploy_dependencies = [
                        DependencyManager([entry]).build_transaction_set()
                        for entry in DeployDependencies.loans_core()
                    ]
                    result.extend(deploy_dependencies[0])
                case _:
                    pass

        return self._remove_duplicates(result)

    def build_contract_deploy_set(self):
        result = []

        for contract in self.contracts_to_deploy:
            result.append(contract)

            match contract:
                case "collateral_vault_core":
                    result.extend(DeployDependencies.cv_core())
                case "lending_pool_core":
                    result.extend(DeployDependencies.lp_core())
                case "loans_core":
                    result.extend(DeployDependencies.loans_core())
                case _:
                    pass

        return result
