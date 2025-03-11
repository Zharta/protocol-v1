# @version 0.4.1

"""
Stub for [CryptoPunksMarket](https://etherscan.io/token/0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb#code)
To use in mainnet fork. It's a stub since boa doesn't load interfaces.
"""


# Events

event Assign:
    toAddress: indexed(address)
    punkIndex: uint256

event Transfer:
    fromAddress: indexed(address)
    toAddress: indexed(address)
    value: uint256

event PunkTransfer:
    fromAddress: indexed(address)
    toAddress: indexed(address)
    punkIndex: uint256

event PunkOffered:
    punkIndex: indexed(uint256)
    minValue: uint256
    toAddress: indexed(address)

event PunkBidEntered:
    punkIndex: indexed(uint256)
    value: uint256
    fromAddress: indexed(address)

event PunkBidWithdrawn:
    punkIndex: indexed(uint256)
    value: uint256
    fromAddress: indexed(address)

event PunkBought:
    punkIndex: indexed(uint256)
    value: uint256
    fromAddress: indexed(address)
    toAddress: indexed(address)

event PunkNoLongerForSale:
    punkIndex: indexed(uint256)


# Functions

@external
def punkIndexToAddress(punkIndex: uint256) -> address:
    return empty(address)

@external
def transferPunk(to: address, punkIndex: uint256):
    pass

@external
def offerPunkForSaleToAddress(punkIndex: uint256, minSalePriceInWei: uint256, toAddress: address):
    pass
