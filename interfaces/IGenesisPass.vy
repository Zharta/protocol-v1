# Structs

# Events

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    tokenId: indexed(uint256)

event Approval:
    owner: indexed(address)
    approved: indexed(address)
    tokenId: indexed(uint256)

event ApprovalForAll:
    owner: indexed(address)
    operator: indexed(address)
    approved: bool

event ConsecutiveTransfer:
    fromTokenId: indexed(uint256)
    toTokenId: uint256
    fromAddress: indexed(address)
    toAddress: indexed(address)

event OwnershipTransferred:
    previousOwner: indexed(address)
    newOwner: indexed(address)

# Functions

@view
@external
def wallet(arg0: address) -> DynArray[uint256, 4294967296]:
    pass

@view
@external
def isApprovedForAll(arg0: address, arg1: address) -> bool:
    pass

@view
@external
def owner() -> address:
    pass

@view
@external
def totalSupply() -> uint256:
    pass

@view
@external
def contractURI() -> String[34]:
    pass

@view
@external
def name() -> String[19]:
    pass

@view
@external
def symbol() -> String[3]:
    pass

@pure
@external
def supportsInterface(interfaceID: bytes4) -> bool:
    pass

@view
@external
def balanceOf(_owner: address) -> uint256:
    pass

@view
@external
def ownerOf(_tokenId: uint256) -> address:
    pass

@view
@external
def getApproved(_tokenId: uint256) -> address:
    pass

@view
@external
def tokenURI(tokenId: uint256) -> String[110]:
    pass

@external
@view
def tokenByIndex(_index: uint256) -> uint256:
    pass

@external
@view
def tokenOfOwnerByIndex(_owner: address, _index: uint256) -> uint256:
    pass

@external
def transferFrom(_from: address, _to: address, _tokenId: uint256):
    pass

@external
def safeTransferFrom(_from: address, _to: address, _tokenId: uint256, data: Bytes[1024]):
    pass

@external
def approve(_approved: address, _tokenId: uint256):
    pass

@external
def setApprovalForAll(_operator: address, _approved: bool):
    pass

@external
def transferOwnership(_newOwner: address):
    pass

@external
def renounceOwnership():
    pass