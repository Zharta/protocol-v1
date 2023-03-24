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

# Functions

@view
@external
def totalSupply() -> uint256:
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
def supportsInterface(interface_id: bytes4) -> bool:
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
def isApprovedForAll(_owner: address, _operator: address) -> bool:
    pass

@view
@external
def tokenURI(tokenId: uint256) -> String[110]:
    pass

@external
def transferFrom(_from: address, _to: address, _tokenId: uint256):
    pass

@external
def safeTransferFrom(_from: address, _to: address, _tokenId: uint256, _data: Bytes[1024]):
    pass

@external
def approve(_approved: address, _tokenId: uint256):
    pass

@external
def setApprovalForAll(_operator: address, _approved: bool):
    pass

@external
def mint(_to: address, _tokenId: uint256) -> bool:
    pass