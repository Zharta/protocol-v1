"""
Stub for [WrappedPunk](https://etherscan.io/address/0xb7f7f6c52f2e2fdb1963eab30438024864c313f6#code) 
To use in mainnet fork. It's a stub since boa doesn't load interfaces.
"""

event Transfer:
    _from: indexed(address)
    _to: indexed(address)
    _tokenId: indexed(uint256)


@external
def mint(punkIndex: uint256):
    pass

@external
def registerProxy():
    pass

@external
def safeTransferFrom(from_: address, _to: address, tokenId: uint256, data: Bytes[32] = b''):
    pass

@external
def transferPunk(to: address, punkIndex: uint256):
    pass

@external
def proxyInfo(user: address) -> address:
    return empty(address)

@external
def supportsInterface(interface_id: bytes4) -> bool:
    return False