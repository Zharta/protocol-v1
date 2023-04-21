from dataclasses import dataclass
from typing import Callable, Optional
from .types import DeploymentContext, Environment
from brownie import chain


@dataclass
class Transaction:

    @staticmethod
    def lpcore_set_lpperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.lending_pool_core", "setLendingPoolPeripheralAddress", f"{scope}.lending_pool_peripheral", dryrun=dryrun)

    @staticmethod
    def lplock_set_lpperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.lending_pool_lock", "setLendingPoolPeripheralAddress", f"{scope}.lending_pool_peripheral", dryrun=dryrun)

    @staticmethod
    def lpperiph_set_loansperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.lending_pool_peripheral", "setLoansPeripheralAddress", f"{scope}.loans", dryrun=dryrun)

    @staticmethod
    def lpperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.lending_pool_peripheral", "setLiquidationsPeripheralAddress", "liquidations_peripheral", dryrun=dryrun)

    @staticmethod
    def lpperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.lending_pool_peripheral", "setLiquidityControlsAddress", f"{scope}.liquidity_controls", dryrun=dryrun)

    @staticmethod
    def cvcore_set_cvperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.collateral_vault_core", "setCollateralVaultPeripheralAddress", f"{scope}.collateral_vault_peripheral", dryrun=dryrun)

    @staticmethod
    def punksvault_set_cvperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.cryptopunks_vault_core", "setCollateralVaultPeripheralAddress", f"{scope}.collateral_vault_peripheral", dryrun=dryrun)

    @staticmethod
    def cvperiph_add_loansperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.collateral_vault_peripheral", "addLoansPeripheralAddress", f"{scope}.token", f"{scope}.loans", dryrun=dryrun)

    @staticmethod
    def cvperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.collateral_vault_peripheral", "setLiquidationsPeripheralAddress", "liquidations_peripheral", dryrun=dryrun)

    @staticmethod
    def cvperiph_add_punksvault(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.collateral_vault_peripheral", "addVault", "punk", f"{scope}.cryptopunks_vault_core", dryrun=dryrun)

    @staticmethod
    def loanscore_set_loansperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.loans_core", "setLoansPeripheral", f"{scope}.loans", dryrun=dryrun)

    @staticmethod
    def loansperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.loans", "setLiquidationsPeripheralAddress", "liquidations_peripheral", dryrun=dryrun)

    @staticmethod
    def loansperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, f"{scope}.loans", "setLiquidityControlsAddress", f"{scope}.liquidity_controls", dryrun=dryrun)

    @staticmethod
    def loansperiph_set_lpperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        lending_pool_peripheral = context[f"{scope}.lending_pool_peripheral"].contract
        if execute_read(context, f"{scope}.loans", "lendingPoolPeripheralContract", dryrun=dryrun) != lending_pool_peripheral or dryrun:
            execute(context, f"{scope}.loans", "setLendingPoolPeripheralAddress", f"{scope}.lending_pool_peripheral", dryrun=dryrun)

    @staticmethod
    def loansperiph_set_cvperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        collateral_vault_peripheral = context[f"{scope}.collateral_vault_peripheral"].contract
        if execute_read(context, f"{scope}.loans", "collateralVaultPeripheralContract", dryrun=dryrun) != collateral_vault_peripheral or dryrun:
            execute(context, f"{scope}.loans", "setCollateralVaultPeripheralAddress", f"{scope}.collateral_vault_peripheral", dryrun=dryrun)

    @staticmethod
    def liquidationscore_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, "liquidations_core", "setLiquidationsPeripheralAddress", "liquidations_peripheral", dryrun=dryrun)

    @staticmethod
    def liquidationscore_add_loanscore(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, "liquidations_core", "addLoansCoreAddress", f"{scope}.token", f"{scope}.loans_core", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_liquidationscore(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        liquidations_core = context["liquidations_core"].contract
        if execute_read(context, "liquidations_peripheral", "liquidationsCoreAddress", dryrun=dryrun) != liquidations_core or dryrun:
            execute(context, "liquidations_peripheral", "setLiquidationsCoreAddress", "liquidations_core", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_add_loanscore(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, "liquidations_peripheral", "addLoansCoreAddress", f"{scope}.token", f"{scope}.loans_core", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_add_lpperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, "liquidations_peripheral", "addLendingPoolPeripheralAddress", f"{scope}.token", f"{scope}.lending_pool_peripheral", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_cvperiph(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, "liquidations_peripheral", "setCollateralVaultPeripheralAddress", f"{scope}.collateral_vault_peripheral", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_wpunks(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        execute(context, "liquidations_peripheral", "setWrappedPunksAddress", "wpunk", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_nftxvaultfactory(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        if context.env in [Environment.local, Environment.prod]:
            execute(context, "liquidations_peripheral", "setNFTXVaultFactoryAddress", "nftxvaultfactory", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_nftxmarketplacezap(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        if context.env in [Environment.local, Environment.prod]:
            execute(context, "liquidations_peripheral", "setNFTXMarketplaceZapAddress", "nftxmarketplacezap", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_sushirouter(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        if context.env in [Environment.local, Environment.prod]:
            execute(context, "liquidations_peripheral", "setSushiRouterAddress", "sushirouter", dryrun=dryrun)

    @staticmethod
    def liquiditycontrols_change_collectionborrowableamounts(context: DeploymentContext, dryrun: bool = False, scope: Optional[str] = None):
        nft_borrowable_amounts = context[f"{scope}.nft_borrowable_amounts"]
        contract_instance = context[f"{scope}.liquidity_controls"].contract
        for nft, value_eth in nft_borrowable_amounts.items():
            value_wei = value_eth * 1e18
            address = context[nft].address()
            args = [True, address, value_wei, {"from": context.owner} | context.gas_options()]
            if not address:
                print(f"Skipping changeMaxCollectionBorrowableAmount for undeployed {nft}")
                continue
            current_value = contract_instance.maxCollectionBorrowableAmount(address)
            if current_value != value_wei:
                print(f"Changing MaxCollectionBorrowableAmount for {nft}, from {current_value/1e18} to {value_wei/1e18} eth")
                print(f"## {scope}.liquidity_controls.changeMaxCollectionBorrowableAmount({','.join(str(a) for a in args)}")
                if not dryrun:
                    contract_instance.changeMaxCollectionBorrowableAmount(*args)
            else:
                print(f"Skip changeMaxCollectionBorrowableAmount for {nft}, current value is already {value_wei/1e18} eth")


def execute_read(context: DeploymentContext, contract: str, func: str, *args, dryrun: bool = False, options=None):
    contract_instance = context.contract[contract].contract
    print(f"## {contract}.{func}({','.join(args)})")
    if not dryrun:
        function = getattr(contract_instance, func)
        deploy_args = [context[a].address() for a in args]
        return function(*deploy_args, {"from": context.owner} | (options or {}))

def execute(context: DeploymentContext, contract: str, func: str, *args, dryrun: bool = False, options=None):
    contract_instance = context.contract[contract].contract
    print(f"## {contract}.{func}({','.join(args)})", {"from": context.owner} | context.gas_options() | (options or {}))
    if not dryrun:
        function = getattr(contract_instance, func)
        deploy_args = [context[a].address() for a in args]
        return function(*deploy_args, {"from": context.owner} | context.gas_options() | (options or {}))
