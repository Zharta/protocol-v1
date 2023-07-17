from dataclasses import dataclass
from typing import Optional
from .basetypes import DeploymentContext, Environment
from functools import partial
import types


@dataclass
class Transaction:

    @staticmethod
    def lpcore_set_lpperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "lending_pool_core"],
            "setLendingPoolPeripheralAddress",
            context[pool, "lending_pool_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def lplock_set_lpperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "lending_pool_lock"],
            "setLendingPoolPeripheralAddress",
            context[pool, "lending_pool_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def lpperiph_set_loansperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "lending_pool_peripheral"],
            "setLoansPeripheralAddress",
            context[pool, "loans"],
            dryrun=dryrun
        )

    @staticmethod
    def lpotc_set_loansperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "lending_pool"],
            "setLoansPeripheralAddress",
            context[pool, "loans"],
            dryrun=dryrun
        )

    @staticmethod
    def lpotc_set_liquidations(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "lending_pool"],
            "setLiquidationsPeripheralAddress",
            context[pool, "liquidations"],
            dryrun=dryrun
        )

    @staticmethod
    def lpperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "lending_pool_peripheral"],
            "setLiquidationsPeripheralAddress",
            context[pool, "liquidations_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def lpperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "lending_pool_peripheral"],
            "setLiquidityControlsAddress",
            context[pool, "liquidity_controls"],
            dryrun=dryrun
        )

    @staticmethod
    def cvcore_set_cvperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "collateral_vault_core"],
            "setCollateralVaultPeripheralAddress",
            context[pool, "collateral_vault_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def punksvault_set_cvperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "cryptopunks_vault_core"],
            "setCollateralVaultPeripheralAddress",
            context[pool, "collateral_vault_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def cvperiph_add_loansperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "collateral_vault_peripheral"],
            "addLoansPeripheralAddress",
            context[pool, "token"],
            context[pool, "loans"],
            dryrun=dryrun
        )

    @staticmethod
    def cvotc_add_loansperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "collateral_vault"],
            "addLoansPeripheralAddress",
            context[pool, "token"],
            context[pool, "loans"],
            dryrun=dryrun
        )

    @staticmethod
    def cvperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "collateral_vault_peripheral"],
            "setLiquidationsPeripheralAddress",
            context[pool, "liquidations_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def cvotc_set_liquidations(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "collateral_vault"],
            "setLiquidationsPeripheralAddress",
            context[pool, "liquidations"],
            dryrun=dryrun
        )

    @staticmethod
    def cvperiph_add_punksvault(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "collateral_vault_peripheral"],
            "addVault",
            "punk",
            context[pool, "cryptopunks_vault_core"],
            dryrun=dryrun
        )

    @staticmethod
    def loanscore_set_loansperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "loans_core"],
            "setLoansPeripheral",
            context[pool, "loans"],
            dryrun=dryrun
        )

    @staticmethod
    def loansperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "loans"],
            "setLiquidationsPeripheralAddress",
            context[pool, "liquidations_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def loansperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "loans"],
            "setLiquidityControlsAddress",
            context[pool, "liquidity_controls"],
            dryrun=dryrun
        )

    @staticmethod
    def loansperiph_set_lpperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        lpp = context[pool, "lending_pool_peripheral"]
        lp = context[pool, "loans"]
        lpp_address = context[lpp].contract
        if execute_read(context, lp, "lendingPoolPeripheralContract", dryrun=dryrun) != lpp_address or dryrun:
            execute(context, lp, "setLendingPoolPeripheralAddress", lpp, dryrun=dryrun)

    @staticmethod
    def loansperiph_set_cvperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        cvp = context[pool, "collateral_vault_peripheral"]
        lp = context[pool, "loans"]
        cvp_address = context[cvp].contract
        if execute_read(context, lp, "collateralVaultPeripheralContract", dryrun=dryrun) != cvp_address or dryrun:
            execute(context, lp, "setCollateralVaultPeripheralAddress", cvp, dryrun=dryrun)

    @staticmethod
    def loansotcperiph_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "loans"],
            "setLiquidationsPeripheralAddress",
            context[pool, "liquidations"],
            dryrun=dryrun
        )

    @staticmethod
    def loansotcperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "loans"],
            "setLiquidityControlsAddress",
            context[pool, "liquidity_controls"],
            dryrun=dryrun
        )

    @staticmethod
    def loansotcperiph_set_lpperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        lpp = context[pool, "lending_pool"]
        lp = context[pool, "loans"]
        lpp_address = context[lpp].contract
        if execute_read(context, lp, "lendingPoolPeripheralContract", dryrun=dryrun) != lpp_address or dryrun:
            execute(context, lp, "setLendingPoolPeripheralAddress", lpp, dryrun=dryrun)

    @staticmethod
    def loansotcperiph_set_cvperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        cvp = context[pool, "collateral_vault"]
        lp = context[pool, "loans"]
        cvp_address = context[cvp].contract
        if execute_read(context, lp, "collateralVaultPeripheralContract", dryrun=dryrun) != cvp_address or dryrun:
            execute(context, lp, "setCollateralVaultPeripheralAddress", cvp, dryrun=dryrun)

    @staticmethod
    def liquidationscore_set_liquidationsperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations_core"],
            "setLiquidationsPeripheralAddress",
            context[pool, "liquidations_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def liquidationscore_add_loanscore(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations_core"],
            "addLoansCoreAddress",
            context[pool, "token"],
            context[pool, "loans_core"],
            dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_set_liquidationscore(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        lc = context[pool, "liquidations_core"]
        lp = context[pool, "liquidations_peripheral"]
        lc_address = context[lc].contract
        if execute_read(context, lp, "liquidationsCoreAddress", dryrun=dryrun) != lc_address or dryrun:
            execute(context, lp, "setLiquidationsCoreAddress", lc, dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_add_loanscore(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations_peripheral"],
            "addLoansCoreAddress",
            context[pool, "token"],
            context[pool, "loans_core"],
            dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_add_lpperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations_peripheral"],
            "addLendingPoolPeripheralAddress",
            context[pool, "token"],
            context[pool, "lending_pool_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_set_cvperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations_peripheral"],
            "setCollateralVaultPeripheralAddress",
            context[pool, "collateral_vault_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def liquidationsotc_add_loanscore(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations"],
            "addLoansCoreAddress",
            context[pool, "token"],
            context[pool, "loans_core"],
            dryrun=dryrun
        )

    @staticmethod
    def liquidationsotc_add_lpperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations"],
            "addLendingPoolPeripheralAddress",
            context[pool, "token"],
            context[pool, "lending_pool_peripheral"],
            dryrun=dryrun
        )

    @staticmethod
    def liquidationsotc_set_cvperiph(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations"],
            "setCollateralVaultPeripheralAddress",
            context[pool, "collateral_vault"],
            dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_set_wpunks(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations_peripheral"],
            "setWrappedPunksAddress",
            "wpunk",
            dryrun=dryrun
        )

    @staticmethod
    def liquidationsperiph_set_nftxvaultfactory(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        if context.env in [Environment.local, Environment.prod]:
            execute(context, context[pool, "liquidations_peripheral"], "setNFTXVaultFactoryAddress", "nftxvaultfactory", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_nftxmarketplacezap(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        if context.env in [Environment.local, Environment.prod]:
            execute(context, context[pool, "liquidations_peripheral"], "setNFTXMarketplaceZapAddress", "nftxmarketplacezap", dryrun=dryrun)

    @staticmethod
    def liquidationsperiph_set_sushirouter(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        if context.env in [Environment.local, Environment.prod]:
            execute(context, context[pool, "liquidations_peripheral"], "setSushiRouterAddress", "sushirouter", dryrun=dryrun)

    @staticmethod
    def liquiditycontrols_change_collectionborrowableamounts(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        #TODO remove this?
        return
        nft_borrowable_amounts = context["nft_borrowable_amounts"]
        contract = context[pool, "liquidity_controls"]
        contract_instance = context[contract].contract
        if not contract_instance:
            print(f"[{pool}] Skipping changeMaxCollectionBorrowableAmount for undeployed {contract}")
            return
        for (amount_pool, nft), value_eth in nft_borrowable_amounts.items():
            if amount_pool != pool:
                continue

            erc20_contract = context[pool, "token"]
            erc20_contract_instance = context[erc20_contract].contract
            decimals = erc20_contract_instance.decimals() if erc20_contract_instance else 18
            value_with_decimals = int(value_eth * 10**decimals)

            address = context[nft].address()
            args = [True, address, value_with_decimals]
            kwargs = {"sender": context.owner} |  context.gas_options()
            if not address:
                print(f"[{pool}] Skipping changeMaxCollectionBorrowableAmount for undeployed {nft}")
                continue
            current_value = contract_instance.maxCollectionBorrowableAmount(address)
            if current_value != value_with_decimals:
                print(f"[{pool}] Changing MaxCollectionBorrowableAmount for {nft}, from {current_value/10**decimals} to {value_with_decimals/10**decimals} eth")
                print(f"## {contract}.changeMaxCollectionBorrowableAmount({','.join(str(a) for a in args)}")
                if not dryrun:
                    contract_instance.changeMaxCollectionBorrowableAmount(*args, **kwargs)
            else:
                print(f"[{pool}] Skip changeMaxCollectionBorrowableAmount for {nft}, current value is already {value_with_decimals/10**decimals} eth")


def execute_read(context: DeploymentContext, contract: str, func: str, *args, dryrun: bool = False, options=None):
    contract_instance = context.contract[contract].contract
    print(f"## {contract}.{func}({','.join(args)})")
    if not dryrun:
        function = getattr(contract_instance, func)
        deploy_args = [context[a].address() for a in args]
        return function(*deploy_args, **({"sender": context.owner} | (options or {})))


def execute(context: DeploymentContext, contract: str, func: str, *args, dryrun: bool = False, options=None):
    contract_instance = context.contract[contract].contract
    print(f"## {contract}.{func}({','.join(args)})", {"from": context.owner} | context.gas_options() | (options or {}))
    if not dryrun:
        function = getattr(contract_instance, func)
        deploy_args = [context[a].address() for a in args]
        return function(*deploy_args, **({"sender": context.owner} | context.gas_options() | (options or {})))
