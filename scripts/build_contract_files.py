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
    "CryptoPunksVaultCore",
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
    "debug/SignatureDebug",
]

# A map between the contract name on the contracts addresses configuration file and
# the contract vyper file name
contracts_mapped = {
    "CryptoPunksVaultCore": "cryptopunks_vault_core",
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
    "auxiliary/token/ERC721": "ERC721",
    "debug/SignatureDebug": "signature_debug",
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
def build_contract_files(write_to_s3: bool = False, output_directory: str = ""):
    """Build contract (abi and bytecode) files and write to S3 or local directory"""

    # vyper contracts base location
    project_path = Path.cwd() / "contracts"

    # get contract addresses config file
    config_file = Path.cwd() / "configs" / env / f"contracts.json"
    config = json.loads(read_file(config_file))

    nfts_file = Path.cwd() / "configs" / env / f"nfts.json"
    nfts = json.loads(read_file(nfts_file))

    colls_whitelist_file = Path.cwd() / "configs" / env / f"collaterals_whitelist.json"
    colls_whitelist = json.loads(read_file(colls_whitelist_file))

    collection_names_file = Path.cwd() / "configs" / env / f"collection_names.json"
    collection_names = json.loads(read_file(collection_names_file))

    if env != "prod":
        colls_test_file = Path.cwd() / "configs" / env / f"collaterals_test.json"
        colls_test = json.loads(read_file(colls_test_file))

        colls_whitelist_prod_file = Path.cwd() / "configs/prod/collaterals_whitelist.json"
        colls_whitelist_prod = json.loads(read_file(colls_whitelist_prod_file))

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
            nfts_final = []

            for nft in nfts:
                nft["abi"] = abi_python
                nfts_final.append(nft)

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
    nfts_file = Path(output_directory) / "nfts.json"
    colls_whitelist_file = Path(output_directory) / "collaterals_whitelist.json"
    colls_whitelist_prod_file = Path(output_directory) / "collaterals_whitelist_prod.json"
    colls_test_file = Path(output_directory) / "collaterals_test.json"
    collection_names_file = Path(output_directory) / "collection_names.json"

    if write_to_s3:
        write_content_to_s3(config_file, json.dumps(config))
        write_content_to_s3(nfts_file, json.dumps(nfts_final))
        write_content_to_s3(colls_whitelist_file, json.dumps(colls_whitelist))
        write_content_to_s3(collection_names_file, json.dumps(collection_names))
        if env != "prod":
            write_content_to_s3(colls_test_file, json.dumps(colls_test))
            write_content_to_s3(colls_whitelist_prod_file, json.dumps(colls_whitelist_prod))

    elif not write_to_s3 and output_directory:
        write_content_to_file(config_file, json.dumps(config))
        write_content_to_file(nfts_file, json.dumps(nfts_final))
        write_content_to_file(colls_whitelist_file, json.dumps(colls_whitelist))
        write_content_to_file(collection_names_file, json.dumps(collection_names))
        if env != "prod":
            write_content_to_file(colls_test_file, json.dumps(colls_test))
            write_content_to_file(colls_whitelist_prod_file, json.dumps(colls_whitelist_prod))


if __name__ == "__main__":
    build_contract_files()
