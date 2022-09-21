from vyper.cli.vyper_compile import compile_files
from pathlib import Path
from botocore.exceptions import ClientError
from click.exceptions import BadParameter

import click
import json
import boto3
import os
import logging
import hashlib

env = os.environ.get("ENV", "dev")
prefix = hashlib.sha256("zharta".encode()).hexdigest()[-5:]
bucket_name = f"{prefix}-zharta-contracts-{env}"
s3 = boto3.resource("s3")

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

contracts = [
    "CollateralVaultCore",
    "CollateralVaultPeripheral",
    "LendingPoolCore",
    "LendingPoolPeripheral",
    "LiquidationsCore",
    "LiquidationsPeripheral",
    "LiquidityControls",
    "Loans",
    "LoansCore",
    "auxiliary/token/ERC20",
    "auxiliary/token/ERC721",
]

# A map between the contract name on the contracts addresses configuration file and 
# the contract vyper file name
contracts_mapped = {
    "CollateralVaultCore": "collateral_vault_core",
    "CollateralVaultPeripheral": "collateral_vault_peripheral",
    "LendingPoolCore": "lending_pool_core",
    "LendingPoolPeripheral": "lending_pool",
    "LiquidationsCore": "liquidations_core",
    "LiquidationsPeripheral": "liquidations_peripheral",
    "LiquidityControls": "liquidity_controls",
    "Loans": "loans",
    "LoansCore": "loans_core",
    "auxiliary/token/ERC20": "token",
    # "auxiliary/token/ERC721": "ERC721",
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
def build_contract_files(write_to_s3: bool = True, output_directory: str = ""):
    """Build contract (abi and bytecode) files and write to S3 or local directory"""

    # vyper contracts base location
    project_path = Path.cwd() / "contracts"

    # get contract addresses config file
    config_file = Path.cwd() / "configs" / f"contracts_{env}.json"
    config = json.loads(read_file(config_file))

    if output_directory and not write_to_s3:
        # Check if directory exists and if not create it
        Path(f"{output_directory}/abi").mkdir(parents=True, exist_ok=True)
        Path(f"{output_directory}/bytecode").mkdir(parents=True, exist_ok=True)
    else:
        output_directory = Path("")

    for contract in contracts:
        if contract.startswith("auxiliary"):
            contract_output_name = contract.split("/")[-1]
        else:
            contract_output_name = contract

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
            config["tokens"]["WETH"][mapped_contract]["abi"] = abi_python

        # Extract bytecode from compiled contract
        logger.info(f"Compiling {contract} binary file")
        bytecode = list(
            compile_files(
                [project_path / f"{contract}.vy"],
                output_formats=["bytecode"],
                root_folder=".",
            ).values()
        )[0].get("bytecode")

        config_file = Path(output_directory) / "contracts.json"
        abi_path = Path(output_directory) / "abi" / f"{contract_output_name}.abi"
        binary_path = Path(output_directory) / "bytecode" / f"{contract_output_name}.bin"

        if write_to_s3:
            write_content_to_s3(abi_path, json.dumps(abi_python))
            write_content_to_s3(binary_path, bytecode)
            write_content_to_s3(config_file, json.dumps(config))

        elif not write_to_s3 and output_directory:
            write_content_to_file(abi_path, json.dumps(abi_python))
            write_content_to_file(binary_path, bytecode)
            write_content_to_file(config_file, json.dumps(config))

        else:
            raise BadParameter("Invalid combination of parameters")


if __name__ == "__main__":
    build_contract_files()
