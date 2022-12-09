from dataclasses import dataclass
from typing import Callable
from .types import DeploymentContext


@dataclass
class Transaction:

    @staticmethod
    def lpcore_set_lpperiph(context: DeploymentContext, dryrun: bool = False):
        execute(context, "lending_pool_core", "setLendingPoolPeripheralAddress", "lending_pool_peripheral", dryrun=dryrun)

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
    def loansperiph_add_collateral_cool_cats(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "cool_cats", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_hashmasks(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "hashmasks", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_bakc(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "bakc", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_doodles(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "doodles", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_wow(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "wow", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_mayc(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "mayc", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_veefriends(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "veefriends", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_pudgy_penguins(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "pudgy_penguins", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_bayc(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "bayc", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_wpunks(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "wpunks", dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_punks(context: DeploymentContext, dryrun: bool = False):
        execute(context, "loans", "addCollateralToWhitelist", "punks", dryrun=dryrun)

    @staticmethod
    def liquiditycontrols_change_collectionborrowableamounts(context: DeploymentContext, dryrun: bool = False):
        nft_borrowable_amounts = context["nft_borrowable_amounts"]
        contract_instance = context["liquidity_controls"].contract
        for nft, value_wei in nft_borrowable_amounts.items():
            address = context[nft].address()
            args = [True, address, value_wei, {"from": context.owner}]
            if dryrun:
                print(f"## liquidity_controls.changeMaxCollectionBorrowableAmount({','.join(str(a) for a in args)}")
            elif contract_instance.maxCollectionBorrowableAmount(address) != value_wei:
                print(f"## liquidity_controls.changeMaxCollectionBorrowableAmount({','.join(str(a) for a in args)}")
                contract_instance.changeMaxCollectionBorrowableAmount(*args)
            else:
                print(f"Skip changeMaxCollectionBorrowableAmount for {nft}, current addres is already {address}")


def execute(context: DeploymentContext, contract: str, func: str, *args, dryrun: bool = False):
    contract_instance = context.contract[contract].contract
    print(f"## {contract}.{func}({','.join(args)})")
    if not dryrun:
        function = getattr(contract_instance, func)
        deploy_args = [context[a].address() for a in args]
        function(*deploy_args, {"from": context.owner})
