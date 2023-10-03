from vyper.cli.vyper_compile import compile_files
from pathlib import Path
from botocore.exceptions import ClientError
from click.exceptions import BadParameter
from decimal import Decimal

import click
import json
import boto3
import os
import logging
import hashlib
import copy

env = os.environ.get("ENV", "dev")
prefix = hashlib.sha256("zharta".encode()).hexdigest()[-5:]
bucket_name = f"{prefix}-zharta-contracts-{env}"
collections_table = f"collections-{env}"
pools_table = f"pool-configs-{env}"
abis_table = f"abis-{env}"
s3 = boto3.resource("s3")
dynamodb = boto3.resource("dynamodb")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


contract_def_to_path = {
    "CollateralVaultCoreV2": "CollateralVaultCoreV2",
    "CollateralVaultOTC": "CollateralVaultOTC",
    "CollateralVaultPeripheral": "CollateralVaultPeripheral",
    "CryptoPunksVaultCore": "CryptoPunksVaultCore",
    "DelegationRegistryMock": "auxiliary/delegate/DelegationRegistryMock",
    "GenesisPass": "GenesisPass",
    "LendingPoolCore": "LendingPoolCore",
    "LendingPoolERC20OTC": "LendingPoolERC20OTC",
    "LendingPoolEthOTC": "LendingPoolEthOTC",
    "LendingPoolLock": "LendingPoolLock",
    "LendingPoolPeripheral": "LendingPoolPeripheral",
    "LiquidationsCore": "LiquidationsCore",
    "LiquidationsOTC": "LiquidationsOTC",
    "LiquidationsPeripheral": "LiquidationsPeripheral",
    "LiquidityControls": "LiquidityControls",
    "Loans": "Loans",
    "LoansCore": "LoansCore",
    "LoansOTC": "LoansOTC",
    "WETH9Mock": "auxiliary/token/ERC20",
    "ERC721": "auxiliary/token/ERC721",
}


def read_file(filename: Path):
    """Read file content."""
    with open(filename, "r") as f:
        return f.read()


def write_content_to_file(filename: Path, data: str):
    """Write content to file."""
    with open(filename, "w") as f:
        f.write(data)


def write_content_to_s3(key: Path, data: str):
    """Write content to S3."""
    try:
        kwargs = {"ContentType": "application/json"} if key.as_posix()[-5:] ==".json" else {}
        s3.Bucket(bucket_name).put_object(Key=key.as_posix(), Body=data, **kwargs)
    except ClientError as e:
        logger.error(f"Error writing to S3: {e}")


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

    except ClientError as e:
        logger.error(f"Error writing to collections table: {e}")


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

    except ClientError as e:
        logger.error(f"Error writing to pools table: {e}")


def write_abis_to_dynamodb(data: dict):
    """Write abis to dynamodb abis table"""
    try:
        table = dynamodb.Table(abis_table)

        for abi_key, abi in data.items():
            table.update_item(
                Key={"abi_key": abi_key},
                UpdateExpression=f"SET abi=:v",
                ExpressionAttributeValues={":v": abi},
            )
    except ClientError as e:
        logger.error(f"Error writing to abis table: {e}")


def dynamo_type(val):
    if isinstance(val, float):
        return Decimal(str(val))
    elif isinstance(val, dict):
        return {dynamo_type(k): dynamo_type(v) for k, v in val.items()}
    return val


def abi_key(abi: list) -> str:
    json_dump = json.dumps(abi, sort_keys=True)
    hash = hashlib.sha1(json_dump.encode("utf8"))
    return hash.hexdigest()


@click.command()
@click.option(
    "--write-to-s3",
    "write_to_s3",
    type=bool,
    help="Write files to S3. If value is False, files will be written to local directory "
    "specified by the output-directory parameter."
)
@click.option(
    "--output-directory",
    "output_directory",
    help="Default output directory for files",
)
def build_contract_files(write_to_s3: bool = False, output_directory: str = ""):
    """Build contract (abi and bytecode) files and write to S3 or local directory"""

    # vyper contracts base location
    project_path = Path.cwd() / "contracts"

    # get contract addresses config file
    config_file = Path.cwd() / "configs" / env / "pools.json"
    config = json.loads(read_file(config_file))

    nfts_file = Path.cwd() / "configs" / env / "collections.json"
    nfts = json.loads(read_file(nfts_file))

    if output_directory and not write_to_s3:
        # Check if directory exists and if not create it
        Path(f"{output_directory}/abi").mkdir(parents=True, exist_ok=True)
        Path(f"{output_directory}/bytecode").mkdir(parents=True, exist_ok=True)
    else:
        output_directory = Path("")

    config = {"pools": config["pools"]}

    logger.info("Compiling contract files")
    compiled_contracts = {
        contract_def: compiled
        for contract_def, path in contract_def_to_path.items()
        for compiled in compile_files(
            [project_path / f"{path}.vy"],
            output_formats=["abi_python", "bytecode"],
            root_folder="."
        ).values()
    }

    abis = {k: v["abi"] for k, v in compiled_contracts.items()}
    bytecodes = {k: v["bytecode"] for k, v in compiled_contracts.items()}
    abis_by_key = {abi_key(abi): abi for abi in abis.values()}

    # add abis and abi_keys to pool contracts

    for pool_id, pool_config in config["pools"].items():
        for contract_key, contract in pool_config["contracts"].items():
            if not contract.get("contract"):
                continue

            contract_def = contract.get("contract_def")
            if contract_def and contract_def in abis:
                abi = abis[contract_def]
                contract["abi"] = abi
                contract["abi_key"] = abi_key(abi)
                # logger.info(f"abi for {pool_id=} {contract_key=} {contract_def=} {abi_key(abi)=}")
            else:
                logger.warning(f"no abi found for {pool_id=} {contract_key=} {contract_def=}")

    # write individual abi and bytecode files

    logger.info("Publishing abi and bytecode files")
    for contract_def, contract_path in contract_def_to_path.items():

        abi_path = Path(output_directory) / "abi" / f"{contract_def}.json"
        binary_path = Path(output_directory) / "bytecode" / f"{contract_def}.bin"

        if write_to_s3:
            write_content_to_s3(abi_path, json.dumps(abis[contract_def]))
            write_content_to_s3(binary_path, bytecodes[contract_def])

        elif not write_to_s3 and output_directory:

            write_content_to_file(abi_path, json.dumps(abis[contract_def]))
            write_content_to_file(binary_path, bytecodes[contract_def])
        else:
            raise BadParameter("Invalid combination of parameters")

    config_file = Path(output_directory) / "pools.json"
    nfts_file = Path(output_directory) / "collections.json"

    # write collections and pools files and push to dynamo tables

    if write_to_s3:
        logger.info("Publishing collections and pools to s3")
        write_content_to_s3(config_file, json.dumps(config))
        write_content_to_s3(Path("nfts.json"), json.dumps(nfts))
        if env != "local":
            config_without_abis = copy.deepcopy(config)
            for _, pool_config in config_without_abis["pools"].items():
                for _, contract in pool_config["contracts"].items():
                    if "abi" in contract:
                        del contract["abi"]

            logger.info("Publishing collections and pools to dynamodb")
            write_collections_to_dynamodb(nfts)
            write_pools_to_dynamodb(config_without_abis)

            logger.info("Publishing abis to dynamodb")
            write_abis_to_dynamodb(abis_by_key)

    elif not write_to_s3 and output_directory:
        write_content_to_file(config_file, json.dumps(config))
        write_content_to_file(nfts_file, json.dumps(nfts))

    logger.info("Done")


if __name__ == "__main__":
    build_contract_files()
