from dataclasses import dataclass
from typing import Callable
from types import DeploymentContext


def execute(func: Callable, *args, _dryrun: bool = False, **kwargs):
    if _dryrun:
        args_str = ','.join(args)
        kwargs_str = ','.join(f"{k}={v}" for k, v in args.items())
        full_args = ", ".join(args_str, kwargs_str)
        print(f"DRYRUN: {func}({full_args})")
        return None
    else:
        return func(*args, **kwargs)


@dataclass
class Transaction:

    @staticmethod
    def lpcore_set_lpperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["lending_pool_core"]
        execute(
            contract_instance.setLendingPoolPeripheralAddress,
            context.contract["lending_pool_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def lpperiph_set_loansperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["lending_pool_peripheral"]
        execute(contract_instance.setLoansPeripheralAddress, context.contract["loans"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def lpperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["lending_pool_peripheral"]
        execute(
            contract_instance.setLiquidationsPeripheralAddress,
            context.contract["liquidations_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def lpperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["lending_pool_peripheral"]
        execute(
            contract_instance.setLiquidityControlsAddress,
            context.contract["liquidity_controls"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def cvcore_set_cvperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["collateral_vault_core"]
        execute(
            contract_instance.setCollateralVaultPeripheralAddress,
            context.contract["collateral_vault_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def cvperiph_add_loansperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["collateral_vault_peripheral"]
        execute(
            contract_instance.addLoansPeripheralAddress,
            context.contract["loans"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def cvperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["collateral_vault_peripheral"]
        execute(
            contract_instance.setLiquidationsPeripheralAddress,
            context.contract["liquidations_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def loanscore_set_loansperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans_core"]
        execute(
            contract_instance.setLoansPeripheral,
            context.contract["loans"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def loansperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(
            contract_instance.setLiquidationsPeripheralAddress,
            context.contract["liquidations_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def loansperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(
            contract_instance.setLiquidityControlsAddress,
            context.contract["liquidity_controls"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def loansperiph_set_lpperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(
            contract_instance.setLendingPoolPeripheralAddress,
            context.contract["lending_pool_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def loansperiph_set_cvperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(
            contract_instance.setCollateralVaultPeripheralAddress,
            context.contract["collateral_vault_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def liquidationscore_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["liquidations_core"]
        execute(
            contract_instance.setLiquidationsPeripheralAddress,
            context.contract["liquidations_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def liquidationscore_add_loanscore(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["liquidations_core"]
        execute(
            contract_instance.addLoansCoreAddress,
            context.contract["loans_core"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_set_liquidationscore(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["liquidations_peripheral"]
        execute(
            contract_instance.setLiquidationsCoreAddress,
            context.contract["liquidations_core"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_add_loanscore(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["liquidations_peripheral"]
        execute(
            contract_instance.addLoansCoreAddress,
            context.contract["loans_core"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_add_lpperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["liquidations_peripheral"]
        execute(
            contract_instance.addLendingPoolPeripheralAddress,
            context.contract["lending_pool_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_set_cvperiph(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["liquidations_peripheral"]
        execute(
            contract_instance.setCollateralVaultPeripheralAddress,
            context.contract["collateral_vault_peripheral"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_set_nftxvaultfactory(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["liquidations_peripheral"]
        execute(
            contract_instance.setNFTXVaultFactoryAddress,
            context.config["nftxvaultfactory"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_set_nftxmarketplacezap(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["liquidations_peripheral"]
        execute(
            contract_instance.setNFTXMarketplaceZapAddress,
            context.config["nftxmarketplacezap"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_set_sushirouter(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["liquidations_peripheral"]
        execute(
            contract_instance.setSushiRouterAddress,
            context.config["sushirouter"],
            {"from": context.owner},
            _dryrun=dryrun
        )

    @staticmethod
    def loansperiph_add_collateral_cool_cats(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["cool_cats"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_hashmasks(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["hashmasks"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_bakc(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["bakc"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_doodles(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["doodles"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_wow(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["wow"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_mayc(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["mayc"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_veefriends(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["veefriends"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_pudgy_penguins(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["pudgy_penguins"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_bayc(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["bayc"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_wpunks(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["wpunks"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    def loansperiph_add_collateral_cryptopunks(context: DeploymentContext, dryrun: bool = False):
        contract_instance = context.contract["loans"]
        execute(contract_instance.addCollateralToWhitelist, context.contract["cryptopunks"], {"from": context.owner}, _dryrun=dryrun)

    @staticmethod
    @staticmethod
    def liquiditycontrols_change_collectionborrowableamounts(context: DeploymentContext, dryrun: bool = False):
        nft_borrowable_amounts = context.config["nft_borrowable_amounts"]
        contract_instance = context.contract["liquidity_controls"]
        for nft, value_wei in nft_borrowable_amounts:
            address = context.contract[nft].address()
            if contract_instance.maxCollectionBorrowableAmount(address) != value_wei:
                return execute(contract_instance.changeMaxCollectionBorrowableAmount, True, address, value_wei, {"from": context.owner}, _dryrun=dryrun)
            else:
                print(f"Skip changeMaxCollectionBorrowableAmount for {nft}, current addres is already {address}")
