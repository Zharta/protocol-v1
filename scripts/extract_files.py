import os

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

base_directory = "../collaterals-service/tests"
# base_directory = "~/Desktop"

for contract in contracts:
    if contract.startswith("auxiliary"):
        contract_output_name = contract.split("/")[-1]
    else:
        contract_output_name = contract
    os.system(f"vyper -f bytecode contracts/{contract}.vy -o {base_directory}/bytecode/{contract_output_name}.bin")
    os.system(f"vyper -f abi_python contracts/{contract}.vy -o {base_directory}/abi/{contract_output_name}.json")