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

env = os.environ.get("ENV", "dev")
prefix = hashlib.sha256("zharta".encode()).hexdigest()[-5:]
bucket_name = f"{prefix}-zharta-contracts-{env}"
collections_table = f"collections-{env}"
s3 = boto3.resource("s3")
dynamodb = boto3.resource("dynamodb")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

contracts = [
    "CryptoPunksVaultCore",
    "CollateralVaultCore",
    "CollateralVaultCoreV2",
    "CollateralVaultPeripheral",
    "LendingPoolCore",
    "LendingPoolLock",
    "LendingPoolPeripheral",
    "LiquidationsCore",
    "LiquidationsPeripheral",
    "LiquidityControls",
    "Loans",
    "LoansCore",
    "auxiliary/token/ERC20",
    "auxiliary/token/ERC721",
    "debug/SignatureDebug",
    "auxiliary/delegate/DelegationRegistryMock",
]

# A map between the contract name on the contracts addresses configuration file and
# the contract vyper file name
contracts_mapped = {
    "CryptoPunksVaultCore": "cryptopunks_vault_core",
    "CollateralVaultCoreV2": "collateral_vault_core",
    "CollateralVaultPeripheral": "collateral_vault_peripheral",
    "LendingPoolCore": "lending_pool_core",
    "LendingPoolLock": "lending_pool_lock",
    "LendingPoolPeripheral": "lending_pool",
    "LiquidationsCore": "liquidations_core",
    "LiquidationsPeripheral": "liquidations_peripheral",
    "LiquidityControls": "liquidity_controls",
    "Loans": "loans",
    "LoansCore": "loans_core",
    "auxiliary/token/ERC20": "token",
    "auxiliary/token/ERC721": "ERC721",
    "debug/SignatureDebug": "signature_debug",
    "auxiliary/delegate/DelegationRegistryMock": "delegation_registry",
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
        s3.Bucket(bucket_name).put_object(Key=key.as_posix(), Body=data)
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


def dynamo_type(val):
    if isinstance(val, float):
        return Decimal(str(val))
    elif isinstance(val, dict):
        return {dynamo_type(k): dynamo_type(v) for k, v in val.items()}
    return val


def migration_patch(config):
    """ temporary adjustement to abstract the collateral vault core migration from the apis """
    weth_config = config["tokens"]["WETH"]
    if "collateral_vault_core2" in weth_config:
        weth_config["collateral_vault_core"] = weth_config["collateral_vault_core2"]
        del weth_config["collateral_vault_core2"]

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
    config_file = Path.cwd() / "configs" / env / "contracts.json"
    config = json.loads(read_file(config_file))
    migration_patch(config)

    nfts_file = Path.cwd() / "configs" / env / "collections.json"
    nfts = json.loads(read_file(nfts_file))

    if output_directory and not write_to_s3:
        # Check if directory exists and if not create it
        Path(f"{output_directory}/abi").mkdir(parents=True, exist_ok=True)
        Path(f"{output_directory}/bytecode").mkdir(parents=True, exist_ok=True)
    else:
        output_directory = Path("")

    for contract in contracts:
        contract_output_name = contract.split("/")[-1]

        # Extract abi from compiled contract
        logger.info(f"Compiling {contract} abi file")
        abi_python = list(
            compile_files(
                [project_path / f"{contract}.vy"],
                output_formats=["abi_python"],
                root_folder=".",
            ).values()
        )[0].get("abi")

        # Update contracts config with abi content
        mapped_contract = contracts_mapped.get(contract, None)
        if mapped_contract:
            try:
                config["tokens"]["WETH"][mapped_contract]["abi"] = abi_python
            except KeyError:
                pass

        # Update nfts config with abi content but only for ERC721 contract
        if contract == "auxiliary/token/ERC721":
            addresses = {nft["contract_address"] for key, nft in nfts.items()}
            nfts_final = [{"contract": address, "abi": abi_python} for address in addresses if address]

        # Extract bytecode from compiled contract
        logger.info(f"Compiling {contract} binary file")
        bytecode = list(
            compile_files(
                [project_path / f"{contract}.vy"],
                output_formats=["bytecode"],
                root_folder=".",
            ).values()
        )[0].get("bytecode")

        abi_path = Path(output_directory) / "abi" / f"{contract_output_name}.json"
        binary_path = Path(output_directory) / "bytecode" / f"{contract_output_name}.bin"

        if write_to_s3:
            write_content_to_s3(abi_path, json.dumps(abi_python))
            write_content_to_s3(binary_path, bytecode)

        elif not write_to_s3 and output_directory:
            write_content_to_file(abi_path, json.dumps(abi_python))
            write_content_to_file(binary_path, bytecode)

        else:
            raise BadParameter("Invalid combination of parameters")

    config_file = Path(output_directory) / "contracts.json"
    nfts_file = Path(output_directory) / "collections.json"

    if write_to_s3:
        write_content_to_s3(config_file, json.dumps(config))
        write_content_to_s3(Path("nfts.json"), json.dumps(nfts_final))
        if env != "local":
            write_collections_to_dynamodb(nfts)

    elif not write_to_s3 and output_directory:
        write_content_to_file(config_file, json.dumps(config))
        write_content_to_file(nfts_file, json.dumps(nfts_final))


if __name__ == "__main__":
    build_contract_files()
