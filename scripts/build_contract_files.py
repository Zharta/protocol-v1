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


def write_content_to_file(filename: Path, data: str):
    """Write content to file."""
    with open(filename, "w") as f:
        f.write(data)


def write_content_to_s3(key: Path, data: str):
    """Write content to S3."""
    try:
        s3.Bucket(bucket_name).put_object(Key=key.as_posix(), Body=data)
    except ClientError as e:
        print("Error writing to S3: ", e)


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
    project_path = Path.cwd() / "contracts"

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
        )

        # Extract bytecode from compiled contract
        logger.info(f"Compiling {contract} binary file")
        bytecode = list(
            compile_files(
                [project_path / f"{contract}.vy"],
                output_formats=["bytecode"],
                root_folder=".",
            ).values()
        )[0].get("bytecode")

        abi_path = Path(output_directory) / "abi" / f"{contract_output_name}.abi"
        binary_path = Path(output_directory) / "bytecode" / f"{contract_output_name}.bin"

        if write_to_s3:
            write_content_to_s3(abi_path, json.dumps(abi_python))
            write_content_to_s3(binary_path, bytecode)

        elif not write_to_s3 and output_directory:
            write_content_to_file(abi_path, json.dumps(abi_python))
            write_content_to_file(binary_path, bytecode)

        else:
            raise BadParameter("Invalid combination of parameters")


if __name__ == "__main__":
    build_contract_files()
