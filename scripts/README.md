# Helper scripts

## build_contract_files.py

This scripts automates the process of building all contract `abi` and `bytecode` files and also the config files needed for other microservices. 
Ths files can either be exported to the local filesystem or uploaded to buckets on AWS S3.

This script will:

- dump all contract `abi` files into a subdirectory named `abi`
- dump all contract `bytecode` files into a subdirectory named `bytecode`
- create a `contracts.json` with the contract addresses and their respective `abi` configurations. This file is created from the [`contracts.json`](../configs/local/contracts.json) template file - there are several sub-directories for each environment (local, dev, int or prod).
- create a `nfts.json` with the contract addresses and their respective `abi` configurations for the nfts. This file is created from the [`nfts.json`](../configs/local/nfts.json) template file - there are several sub-directories for each environment (local, dev, int or prod).

Usage:

To export to local directory:

```
make install
source .venv/bin/activate
ENV=<environment> python scripts/build_contract_files.py --output-directory=<output local directory>
```

To export all data to AWS S3:

```
make install
source .venv/bin/activate
ENV=<environment> AWS_PROFILE=<your aws profile> python scripts/build_contract_files.py --write-to-s3=True 
```

