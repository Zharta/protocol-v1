from typing import Callable
from types import DeploymentContext, InternalContract
from itertools import groupby
from transactions import Transaction
from types import ContractConfig


class DependencyManager:
    def __init__(self, context: DeploymentContext, changed_contracts: set[str], changed_configs: set[str]):
        # self.contracts_to_deploy = contracts_to_deploy
        self.context = context
        self.changed_contracts = changed_contracts
        self.changed_configs = changed_configs
        (deployment_dependencies, config_dependencies) = _build_dependencies(context)
        self.deployment_dependencies = deployment_dependencies
        self.config_dependencies = config_dependencies
        self.deployment_order = _build_deployment_order(deployment_dependencies)
        self.deployment_set = self._build_deployment_set()

    def _build_deployment_set(self):
        dependencies = self.deployment_dependencies
        nodes = {dependencies.keys()} | {dependencies.values()}
        vis = {n: False in nodes for n in nodes}

        def _dfs(n: str):
            vis[n] = True
            for d in dependencies[n]:
                if not vis[d]:
                    _dfs(d)

        for d in (self.changed_contracts | self.changed_configs):
            if not vis[d]:
                _dfs(d)

        self.deployment_set = {k for k, v in vis if v and k in self.context.contract}
        self.transaction_set = {
            k: {tx for tx in txs if not self._is_included_in_contract_deployment(tx)}
            for k, txs in self.config_dependencies
            if k in (self.deployment_set | self.changed_configs)
        }

    def _is_included_in_contract_deployment(self, tx: Transaction) -> bool:
        if "loans" in self.deployment_set:
            if tx == Transaction.loansperiph_set_cvperiph:
                return True
            elif tx == Transaction.loansperiph_set_lpperiph:
                return True
        if "liquidations_peripheral" in self.deployment_set:
            if tx == Transaction.liquidationsperiph_set_liquidationscore:
                return True
        return False

    def build_transaction_set(self) -> set[Callable]:
        return self.transaction_set

    def build_contract_deploy_set(self) -> list[ContractConfig]:
        return [
            self.context.contract[k]
            for k in self.deployment_order
            if k in self.deployment_set
        ]


def _build_dependencies(context: DeploymentContext) -> tuple[dict, dict]:
    internal_contracts = {c for c in context.contract.values() if isinstance(c, InternalContract)}

    dep_dependencies_set = {(dep, c.name) for c in internal_contracts for dep in c.deployment_dependencies()}
    config_dependencies_set1 = {(k, v) for c in internal_contracts for k, v in c.config_dependencies()}
    config_dependencies_set2 = {(c.name, v) for c in internal_contracts for k, v in c.config_dependencies()}

    dep_dependencies = {k: set(v) for k, v in groupby(dep_dependencies_set, lambda x: x[0])}
    config_dependencies = {k: set(v) for k, v in groupby(config_dependencies_set1 | config_dependencies_set2, lambda x: x[0])}
    return (dep_dependencies, config_dependencies)


def _build_deployment_order(dependencies: dict[str, set(str)]) -> list[str]:
    nodes = {dependencies.keys()} | {dependencies.values()}
    vis = {n: False for n in nodes}
    stack = list()

    def _dfs(n: str):
        vis[n] = True
        for d in dependencies[n]:
            if not vis[d]:
                _dfs(d)
        stack.append(n)

    for d in vis.keys():
        if not vis[d]:
            _dfs(d)
    return stack[::-1]
