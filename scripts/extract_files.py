from vyper.cli.vyper_compile import compile_files
from vyper import compile_codes

import os
import json
import boto3


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

# base_directory = "../collaterals-service/tests"
base_directory = "/Users/rodrigo/Desktop/tests"


def write_to_file(filename, data):
    with open(filename, "w") as f:
        f.write(data)


def write_to_s3(filename, data):
    s3 = boto3.resource("s3")
    s3.Bucket("vyper-files").put_object(Key=filename, Body=data)


for contract in contracts:
    if contract.startswith("auxiliary"):
        contract_output_name = contract.split("/")[-1]
    else:
        contract_output_name = contract

    abi_python = list(
        compile_files(
            [f"contracts/{contract}.vy"], output_formats=["abi_python"], root_folder="."
        ).values()
    )
    bytecode = list(
        compile_files(
            [f"contracts/{contract}.vy"], output_formats=["bytecode"], root_folder="."
        ).values()
    )[0]

    # Write abi_python to file
    with open(f"{base_directory}/{contract_output_name}.abi", "w") as f:
        f.write(json.dumps(abi_python))

    # Write bytecode to file
    with open(f"{base_directory}/{contract_output_name}.bin", "w") as f:
        f.write(bytecode.get("bytecode"))

    # os.system(f"vyper -f bytecode contracts/{contract}.vy -o {base_directory}/bytecode/{contract_output_name}.bin")
    # os.system(f"vyper -f abi_python contracts/{contract}.vy -o {base_directory}/abi/{contract_output_name}.json")
