# @version ^0.3.7


# Interfaces


# Structs

struct Collateral:
    contractAddress: address
    tokenId: uint256
    amount: uint256


struct EIP712Domain:
    name: String[100]
    version: String[10]
    chain_id: uint256
    verifying_contract: address

struct ReserveMessageContent:
    amount: uint256
    interest: uint256
    maturity: uint256
    collaterals: DynArray[Collateral, 100]
    deadline: uint256


# Events

event SignatureFragment:
    name: String[100]
    value: bytes32

# Global variables

owner: public(address)

loansContract: public(address)

ZHARTA_DOMAIN_NAME: constant(String[6])    = "Zharta"
ZHARTA_DOMAIN_VERSION: constant(String[1]) = "1"

COLLATERAL_TYPE_DEF: constant(String[66])  = "Collateral(address contractAddress,uint256 tokenId,uint256 amount)"
RESERVE_TYPE_DEF: constant(String[229]) = "ReserveMessageContent(address borrower,uint256 amount,uint256 interest,uint256 maturity,Collateral[] collaterals,bool[] delegations,uint256 deadline,uint256 nonce)" \
                                             "Collateral(address contractAddress,uint256 tokenId,uint256 amount)"
DOMAIN_TYPE_HASH: constant(bytes32)        = keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
COLLATERAL_TYPE_HASH: constant(bytes32)    = keccak256(COLLATERAL_TYPE_DEF)
RESERVE_TYPE_HASH: constant(bytes32)       = keccak256(RESERVE_TYPE_DEF)


@external
def __init__(_loansContract: address):
    self.owner = msg.sender
    self.loansContract = _loansContract



@view
@external
def chain_id() -> uint256:
    return chain.id


@external
def loans_reserve(
    _borrower: address,
    _amount: uint256,
    _interest: uint256,
    _maturity: uint256,
    _collaterals: DynArray[Collateral, 100],
    _delegations: DynArray[bool, 100],
    _deadline: uint256,
    _nonce: uint256,
    _v: uint256,
    _r: uint256,
    _s: uint256
) -> address:

    reserve_sig_domain_separator: bytes32 = keccak256(
        _abi_encode(
            DOMAIN_TYPE_HASH,
            keccak256(ZHARTA_DOMAIN_NAME),
            keccak256(ZHARTA_DOMAIN_VERSION),
            chain.id,
            self.loansContract
        )
    )


    log SignatureFragment("domain_type_hash", DOMAIN_TYPE_HASH)
    log SignatureFragment("reserve_type_hash", RESERVE_TYPE_HASH)
    log SignatureFragment("collateral_type_hash", COLLATERAL_TYPE_HASH)
    log SignatureFragment("reserve_sig_domain_separator", reserve_sig_domain_separator)

    collaterals_data_hash: DynArray[bytes32, 100] = []
    for c in _collaterals:
        collaterals_data_hash.append(keccak256(_abi_encode(COLLATERAL_TYPE_HASH, c.contractAddress, c.tokenId, c.amount)))
    log SignatureFragment("collaterals_data_hash", keccak256(slice(_abi_encode(collaterals_data_hash), 32*2, 32*len(_collaterals))))
    log SignatureFragment("delegations_data_hash", keccak256(slice(_abi_encode(_delegations), 32*2, 32*len(_delegations))))

    data_hash: bytes32 = keccak256(_abi_encode(
                RESERVE_TYPE_HASH,
                _borrower,
                _amount,
                _interest,
                _maturity,
                keccak256(slice(_abi_encode(collaterals_data_hash), 32*2, 32*len(_collaterals))),
                keccak256(slice(_abi_encode(_delegations), 32*2, 32*len(_delegations))),
                _deadline,
                _nonce,
                ))
    log SignatureFragment("data_hash", data_hash)

    sig_hash: bytes32 = keccak256(concat(convert("\x19\x01", Bytes[2]), _abi_encode(reserve_sig_domain_separator, data_hash)))
    log SignatureFragment("sig_hash", sig_hash)

    signer: address = ecrecover(sig_hash, _v, _r, _s)
    return signer




