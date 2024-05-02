import types
from dataclasses import dataclass
from functools import partial
from typing import Optional

from .basetypes import DeploymentContext, Environment


@dataclass
class Transaction:
    @staticmethod
    def loansotcperiph_set_liquiditycontrols(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context, context[pool, "loans"], "setLiquidityControlsAddress", context[pool, "liquidity_controls"], dryrun=dryrun
        )

    @staticmethod
    def liquidationscore_add_loanscore(context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None):
        execute(
            context,
            context[pool, "liquidations_core"],
            "addLoansCoreAddress",
            context[pool, "token"],
            context[pool, "loans_core"],
            dryrun=dryrun,
        )

    @staticmethod
    def liquiditycontrols_change_collectionborrowableamounts(
        context: DeploymentContext, dryrun: bool = False, pool: Optional[str] = None
    ):
        # TODO remove this?
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
            kwargs = {"sender": context.owner} | context.gas_options()
            if not address:
                print(f"[{pool}] Skipping changeMaxCollectionBorrowableAmount for undeployed {nft}")
                continue
            current_value = contract_instance.maxCollectionBorrowableAmount(address)
            if current_value != value_with_decimals:
                print(
                    f"[{pool}] Changing MaxCollectionBorrowableAmount for {nft}, from {current_value/10**decimals} to {value_with_decimals/10**decimals} eth"
                )
                print(f"## {contract}.changeMaxCollectionBorrowableAmount({','.join(str(a) for a in args)}")
                if not dryrun:
                    contract_instance.changeMaxCollectionBorrowableAmount(*args, **kwargs)
            else:
                print(
                    f"[{pool}] Skip changeMaxCollectionBorrowableAmount for {nft}, current value is already {value_with_decimals/10**decimals} eth"
                )


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
        print(f"{function=} {deploy_args=}")
        return function(*deploy_args, **({"sender": context.owner} | context.gas_options() | (options or {})))
