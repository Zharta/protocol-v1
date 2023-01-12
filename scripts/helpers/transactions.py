from dataclasses import dataclass
from typing import Callable
from .types import DeploymentContext


@dataclass
class Transaction:

    @staticmethod
    def lpcore_set_lpperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "lending_pool_core", "setLendingPoolPeripheralAddress", "lending_pool_peripheral", dryrun=dryrun)

    @staticmethod
    def lplock_set_lpperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "lending_pool_lock", "setLendingPoolPeripheralAddress", "lending_pool_peripheral", dryrun=dryrun)

    @staticmethod
    def lpc_migration_migrate(context: DeploymentContext, dryrun: bool = False):
        if not context["run_lpc_migration_01"]:
            print("Skipping lpc_migration_01")
            return
        execute(context, "lending_pool_core", "proposeOwner", "lpc_migration_01", dryrun=dryrun)
        execute(context, "legacy_lending_pool_core", "proposeOwner", "lpc_migration_01", dryrun=dryrun)
        # next line is to make sure no more funds can be moved after migration started
        execute(context, "lending_pool_core", "setLendingPoolPeripheralAddress", "lpc_migration_01", dryrun=dryrun)

        legacy = context["legacy_lending_pool_core"].contract
        lpcore = context["lending_pool_core"].contract
        for lender in legacy.lendersArray():
            funds = legacy.funds(lender)
            print(f"## lpcore.migrateLender({','.join(str(x) for x in [lender, funds[0], funds[1], funds[2], funds[3], funds[5]])})")
            if not dryrun:
                lpcore.migrateLender(lender, funds[0], funds[1], funds[2], funds[3], funds[5], {'from:': context.owner})

        # execute(context, "lpc_migration_01", "migrate", dryrun=dryrun, options={"gas_limit":1200000,"allow_revert":True})
        execute(context, "lpc_migration_01", "migrate", dryrun=dryrun)
        execute(context, "lending_pool_core", "claimOwnership", dryrun=dryrun)

    @staticmethod
    def lplock_migrate(context: DeploymentContext, dryrun: bool = False):
        lending_pool_lock = context["lending_pool_lock"].contract
        legacy_lending_pool_core = context["legacy_lending_pool_core"].contract
        lenders_with_active_locks = context["lenders_with_active_locks"]
        print(f"## lending_pool_lock.migrate(legacy_lending_pool_core, {lenders_with_active_locks})")
        if not dryrun:
            lending_pool_lock.migrate(legacy_lending_pool_core, lenders_with_active_locks, {"from": context.owner})

    @staticmethod
    def lpperiph_set_loansperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "lending_pool_peripheral", "setLoansPeripheralAddress", "loans", dryrun=dryrun)

    @staticmethod
    def lpperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "lending_pool_peripheral", "setLiquidationsPeripheralAddress", "liquidations_peripheral", dryrun=dryrun)

    @staticmethod
    def lpperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False):
        execute(context, "lending_pool_peripheral", "setLiquidityControlsAddress", "liquidity_controls", dryrun=dryrun)

    @staticmethod
    def cvcore_set_cvperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "collateral_vault_core", "setCollateralVaultPeripheralAddress", "collateral_vault_peripheral", dryrun=dryrun)

    @staticmethod
    def cvperiph_add_loansperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "collateral_vault_peripheral", "addLoansPeripheralAddress", "weth", "loans", dryrun=dryrun)

    @staticmethod
    def cvperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "collateral_vault_peripheral", "setLiquidationsPeripheralAddress", "liquidations_peripheral", dryrun=dryrun)

    @staticmethod
    def loanscore_set_loansperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans_core", "setLoansPeripheral", "loans", dryrun=dryrun)

    @staticmethod
    def loansperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "setLiquidationsPeripheralAddress", "liquidations_peripheral", dryrun=dryrun)

    @staticmethod
    def loansperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "setLiquidityControlsAddress", "liquidity_controls", dryrun=dryrun)

    @staticmethod
    def loansperiph_set_lpperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "setLendingPoolPeripheralAddress", "lending_pool_peripheral", dryrun=dryrun)

    @staticmethod
    def loansperiph_set_cvperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "setCollateralVaultPeripheralAddress", "collateral_vault_peripheral", dryrun=dryrun)

    @staticmethod
    def liquidationscore_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "liquidations_core", "setLiquidationsPeripheralAddress", "liquidations_peripheral", dryrun=dryrun)

    @staticmethod
    def liquidationscore_add_loanscore(context: DeploymentContext, dryrun: bool = False):
        execute(context, "liquidations_core", "addLoansCoreAddress", "weth", "loans_core", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_liquidationscore(context: DeploymentContext, dryrun: bool = False):
        execute(context, "liquidations_peripheral", "setLiquidationsCoreAddress", "liquidations_core", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_add_loanscore(context: DeploymentContext, dryrun: bool = False):
        execute(context, "liquidations_peripheral", "addLoansCoreAddress", "weth", "loans_core", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_add_lpperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "liquidations_peripheral", "addLendingPoolPeripheralAddress", "weth", "lending_pool_peripheral", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_cvperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "liquidations_peripheral", "setCollateralVaultPeripheralAddress", "collateral_vault_peripheral", dryrun=dryrun)


    @staticmethod
    def liquidationsperiph_set_nftxvaultfactory(context: DeploymentContext, dryrun: bool = False):
        execute(context, "liquidations_peripheral", "setNFTXVaultFactoryAddress", "nftxvaultfactory", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_nftxmarketplacezap(context: DeploymentContext, dryrun: bool = False):
        execute(context, "liquidations_peripheral", "setNFTXMarketplaceZapAddress", "nftxmarketplacezap", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_sushirouter(context: DeploymentContext, dryrun: bool = False):
        execute(context, "liquidations_peripheral", "setSushiRouterAddress", "sushirouter", dryrun=dryrun)

    @staticmethod
    def liquiditycontrols_change_collectionborrowableamounts(context: DeploymentContext, dryrun: bool = False):
        nft_borrowable_amounts = context["nft_borrowable_amounts"]
        contract_instance = context["liquidity_controls"].contract
        for nft, value_eth in nft_borrowable_amounts.items():
            value_wei = value_eth * 1e18
            address = context[nft].address()
            args = [True, address, value_wei, {"from": context.owner}]
            if dryrun:
                print(f"## liquidity_controls.changeMaxCollectionBorrowableAmount({','.join(str(a) for a in args)}")
            elif contract_instance.maxCollectionBorrowableAmount(address) != value_wei:
                print(f"## liquidity_controls.changeMaxCollectionBorrowableAmount({','.join(str(a) for a in args)}")
                contract_instance.changeMaxCollectionBorrowableAmount(*args)
            else:
                print(f"Skip changeMaxCollectionBorrowableAmount for {nft}, current addres is already {address}")


def execute(context: DeploymentContext, contract: str, func: str, *args, dryrun: bool = False, options=None):
    contract_instance = context.contract[contract].contract
    print(f"## {contract}.{func}({','.join(args)})")
    if not dryrun:
        function = getattr(contract_instance, func)
        deploy_args = [context[a].address() for a in args]
        return function(*deploy_args, {"from": context.owner} | (options or {}))
