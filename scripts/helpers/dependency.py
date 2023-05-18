from typing import Callable
from collections import defaultdict
from functools import partial
from .types import DeploymentContext, InternalContract, ContractConfig
from .transactions import Transaction


class DependencyManager:
    def __init__(self, context: DeploymentContext, changed: set[str]):
        self.context = context
        self.changed = changed
        self._build_dependencies()
        self._build_deployment_order()
        self._build_deployment_set()

    def _build_dependencies(self) -> tuple[dict, dict]:
        internal_contracts = [c for c in self.context.contract.values() if isinstance(c, InternalContract)]
        dep_dependencies_set = {(dep, c.key()) for c in internal_contracts for dep in c.deployment_dependencies(self.context)}
        config_dependencies_set1 = {(k, v) for c in internal_contracts for k, v in c.config_dependencies(self.context).items()}
        config_dependencies_set2 = {(c.key(), v) for c in internal_contracts for k, v in c.config_dependencies(self.context).items()}
        self.deployment_dependencies = groupby_first(dep_dependencies_set, set(self.context.keys()))
        self.config_dependencies = groupby_first(config_dependencies_set1 | config_dependencies_set2, set(self.context.keys()))

    def _build_deployment_set(self):
        dependencies = self.deployment_dependencies
        undeployed = {k for k, c in self.context.contract.items() if c.deployable(self.context) and c.contract is None}
        # nodes = set(dependencies.keys()) | {w for v in dependencies.values() for w in v} | set(self.config_dependencies.keys()) | undeployed
        nodes = set(self.context.contract.keys()) | set(self.context.config.keys())
        starting_set = self.changed | undeployed
        vis = {n: False for n in nodes}

        def _dfs(n: str):
            vis[n] = True
            for d in dependencies[n]:
                if not vis[d]:
                    _dfs(d)

        for d in starting_set:
            if not vis[d]:
                _dfs(d)

        self.deployment_set = {k for k in vis if vis[k] and k in self.context.contract}
        self.transaction_set = {
            k: set(txs)
            for k, txs in self.config_dependencies.items()
            if k in (self.deployment_set | self.changed)
        }

    def _build_deployment_order(self):
        sorted_dependencies = topological_sort(self.deployment_dependencies)
        external_deployable = {
            k for k, c in self.context.contract.items()
            if not isinstance(c, InternalContract) and c.deployable(self.context)
        }
        internal_deployable_sorted = [c for c in sorted_dependencies if c not in external_deployable]
        self.deployment_order = list(external_deployable) + internal_deployable_sorted

    def build_transaction_set(self) -> set[Callable]:
        tx_set = {tx for k, txs in self.transaction_set.items() for tx in txs}
        # workaround to deal with partial functions
        tx_dict = {repr(x): x for x in tx_set}
        return set(tx_dict.values())

    def build_contract_deploy_set(self) -> list[ContractConfig]:
        return [
            self.context.contract[k]
            for k in self.deployment_order
            if k in self.deployment_set
        ]


def topological_sort(dependencies: dict[str, set[str]]) -> list[str]:
    nodes = set(dependencies.keys()) | {w for v in dependencies.values() for w in v}
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


def groupby_first(tuples: set[tuple], extended_keys: set[str] = None) -> dict[str, set[str]]:
    res = defaultdict(set)
    for k in (extended_keys or set()):
        res[k] = set()
    for k, v in tuples:
        res[k].add(v)
    return dict(res)
