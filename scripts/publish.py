import copy
import hashlib
import json
import logging
import os
from decimal import Decimal
from pathlib import Path

import boto3
import click
from botocore.exceptions import ClientError
from click.exceptions import BadParameter
from vyper.cli.vyper_compile import compile_files

env = os.environ.get("ENV", "dev")
collections_table = f"collections-{env}"
pools_table = f"pool-configs-{env}"
abis_table = f"abis-{env}"
dynamodb = boto3.resource("dynamodb")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


contract_def_to_path = {
    "CollateralVaultCoreV2": "CollateralVaultCoreV2",
    "CollateralVaultOTC": "CollateralVaultOTC",
    "CollateralVaultPeripheral": "CollateralVaultPeripheral",
    "CryptoPunksVaultCore": "CryptoPunksVaultCore",
    "DelegationRegistry": "auxiliary/delegate/DelegationRegistryMock",
    "DelegationRegistryMock": "auxiliary/delegate/DelegationRegistryMock",
    "GenesisPass": "GenesisPass",
    "LendingPoolCore": "LendingPoolCore",
    "LendingPoolERC20OTC": "LendingPoolERC20OTC",
    "LendingPoolEthOTC": "LendingPoolEthOTC",
    "LendingPoolOTC": "LendingPoolEthOTC",
    "LendingPoolLock": "LendingPoolLock",
    "LendingPoolPeripheral": "LendingPoolPeripheral",
    "LiquidationsCore": "LiquidationsCore",
    "LiquidationsOTC": "LiquidationsOTC",
    "LiquidationsPeripheral": "LiquidationsPeripheral",
    "LiquidityControls": "LiquidityControls",
    "LoansPeripheral": "Loans",
    "Loans": "Loans",
    "LoansCore": "LoansCore",
    "LoansOTC": "LoansOTC",
    "LoansOTCPunksFixed": "LoansOTC",
    "WETH9Mock": "auxiliary/token/ERC20",
    "ERC721": "auxiliary/token/ERC721",
    "ERC20": "auxiliary/token/ERC20",
    "Genesis": "GenesisPass",
}

standard_to_otc_keys = {
    "collateral_vault_core": "collateral_vault",
    "collateral_vault_peripheral": "collateral_vault",
    "cryptopunks_vault_core": "collateral_vault",
    "lending_pool_core": "lending_pool",
    "liquidations_core": "liquidations",
    "liquidations_peripheral": "liquidations",
    "loans_core": "loans",
}


def read_file(filename: Path):
    """Read file content."""
    with filename.open(encoding="utf8") as f:
        return f.read()


def write_content_to_file(filename: Path, data: str):
    """Write content to file."""
    with filename.open(mode="w", encoding="utf8") as f:
        f.write(data)


def write_collections_to_dynamodb(data: dict):
    """Write collections to dynamodb collections table"""
    try:
        table = dynamodb.Table(collections_table)

        for collection_key, collection_data in data.items():
            indexed_attrs = list(enumerate(collection_data.items()))
            update_expr = ", ".join(f"#k{i}=:v{i}" for i, (k, v) in indexed_attrs)
            attrs = {f"#k{i}": k for i, (k, v) in indexed_attrs}
            values = {f":v{i}": dynamo_type(v) for i, (k, v) in indexed_attrs}

            table.update_item(
                Key={"collection_key": collection_key},
                UpdateExpression=f"SET {update_expr}",
                ExpressionAttributeNames=attrs,
                ExpressionAttributeValues=values,
            )

    except ClientError:
        logger.exception("Error writing to collections table")


def write_pools_to_dynamodb(data: dict):
    """Write pools to dynamodb pools table"""
    try:
        table = dynamodb.Table(pools_table)

        for pool_id, pool_data in data["pools"].items():
            indexed_attrs = list(enumerate(pool_data.items()))
            update_expr = ", ".join(f"#k{i}=:v{i}" for i, (k, v) in indexed_attrs)
            attrs = {f"#k{i}": k for i, (k, v) in indexed_attrs}
            values = {f":v{i}": v for i, (k, v) in indexed_attrs}

            table.update_item(
                Key={"pool_id": pool_id},
                UpdateExpression=f"SET {update_expr}",
                ExpressionAttributeNames=attrs,
                ExpressionAttributeValues=values,
            )

    except ClientError:
        logger.exception("Error writing to pools table")


def write_abis_to_dynamodb(data: dict):
    """Write abis to dynamodb abis table"""
    try:
        table = dynamodb.Table(abis_table)

        for abi_key, abi in data.items():
            table.update_item(
                Key={"abi_key": abi_key},
                UpdateExpression="SET abi=:v",
                ExpressionAttributeValues={":v": abi},
            )
    except ClientError:
        logger.exception("Error writing to abis table")


def dynamo_type(val):
    if isinstance(val, float):
        return Decimal(str(val))
    if isinstance(val, dict):
        return {dynamo_type(k): dynamo_type(v) for k, v in val.items()}
    return val


def abi_key(abi: list) -> str:
    json_dump = json.dumps(abi, sort_keys=True)
    _hash = hashlib.sha1(json_dump.encode("utf8"))
    return _hash.hexdigest()


def normalized_pool_configs(pools, abis):
    pools = copy.deepcopy(pools)
    common = pools.get("common", {})

    for pool_id, pool_config in pools["pools"].items():
        contracts = pool_config["contracts"]

        # fix missing standard keys in otc contracts
        for standard_key, otc_key in standard_to_otc_keys.items():
            if standard_key not in contracts and otc_key in contracts:
                contracts[standard_key] = contracts[otc_key]

        # fix missing token key when token contract is shared
        if "token" not in contracts:
            token_key = contracts["lending_pool"]["properties"]["token_key"]
            namespace, key = token_key.split(".")
            contracts["token"] = pools[namespace][key]

        # fix possible missing keys
        contracts["genesis"] = contracts.get("genesis", common.get("genesis"))
        contracts["delegation_registry"] = contracts.get("delegation_registry", common.get("delegation_registry"))
        contracts["liquidity_controls"] = contracts.get("liquidity_controls", {"contract": ""})

        # add abi_key to contracts and remove unwanted fields
        for contract_key, contract in contracts.items():
            if not contract.get("contract"):
                continue

            contract_def = contract.get("contract_def")
            if contract_def and contract_def in abis:
                contract["abi_key"] = abi_key(abis[contract_def])
            else:
                logger.warning(f"no abi found for {pool_id=} {contract_key=} {contract_def=}")  # noqa: G004

            contract.pop("abi", None)
            contract.pop("properties", None)
            contract.pop("alias", None)

    # return just the pools section
    return {"pools": pools["pools"]}


@click.command()
@click.option(
    "--write-to-cloud",
    "write_to_cloud",
    type=bool,
    default=True,
    help="Write files to cloud. If value is False, files will be written to local directory "
    "specified by the output-directory parameter.",
)
@click.option(
    "--output-directory",
    "output_directory",
    default="",
    help="Default output directory for files",
)
def cli(*, write_to_cloud: bool = False, output_directory: str = ""):
    """Build contract (abi and bytecode) files and write to cloud or local directory"""

    # vyper contracts base location
    project_path = Path.cwd() / "contracts"
    output_directory = Path(output_directory)
    if write_to_cloud and env == "local":
        raise BadParameter("Cannot write to cloud in local environment")

    # get contract addresses config file
    pools = json.loads(read_file(Path.cwd() / "configs" / env / "pools.json"))
    nfts = json.loads(read_file(Path.cwd() / "configs" / env / "collections.json"))

    if not write_to_cloud:
        # Check if directory exists and if not create it
        Path(f"{output_directory}/abi").mkdir(parents=True, exist_ok=True)
        Path(f"{output_directory}/bytecode").mkdir(parents=True, exist_ok=True)

    logger.info("Compiling contract files")
    compiled_contracts = {
        contract_def: compiled
        for contract_def, path in contract_def_to_path.items()
        for compiled in compile_files(
            [project_path / f"{path}.vy"], output_formats=["abi_python", "bytecode"], root_folder="."
        ).values()
    }

    abis = {k: v["abi"] for k, v in compiled_contracts.items()}
    bytecodes = {k: v["bytecode"] for k, v in compiled_contracts.items()}
    abis_by_key = {abi_key(abi): abi for abi in abis.values()}

    # write individual abi and bytecode files
    if not write_to_cloud:
        logger.info("Publishing abi and bytecode files")
        for contract_def in contract_def_to_path:
            abi_path = Path(output_directory) / "abi" / f"{contract_def}.json"
            binary_path = Path(output_directory) / "bytecode" / f"{contract_def}.bin"

            write_content_to_file(abi_path, json.dumps(abis[contract_def]))
            write_content_to_file(binary_path, bytecodes[contract_def])

    # add abis and abi_keys to pool contracts
    pools = normalized_pool_configs(pools, abis)

    # write collections and pools files and push to dynamo tables

    if write_to_cloud:
        logger.info("Publishing collections and pools to dynamodb")
        write_collections_to_dynamodb(nfts)
        write_pools_to_dynamodb(pools)

        logger.info("Publishing abis to dynamodb")
        write_abis_to_dynamodb(abis_by_key)

    else:
        write_content_to_file(output_directory / "pools.json", json.dumps(pools, indent=2, sort_keys=True))
        write_content_to_file(output_directory / "collections.json", json.dumps(nfts, indent=2, sort_keys=True))

    logger.info("Done")
