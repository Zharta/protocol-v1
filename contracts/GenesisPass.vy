# @version 0.3.7

## Interfaces

from vyper.interfaces import ERC165
from vyper.interfaces import ERC721

implements: ERC721
implements: ERC165

## Events

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

# Global variables


# @dev Mapping from NFT ID to the address that owns it.
idToOwner: HashMap[uint256, address]

# @dev Mapping from owner address to count of his tokens.
ownerToNFTokenCount: HashMap[address, uint256]

# @dev Address of minter, who can mint a token
minter: address

# @dev Address of minter, who can mint a token
distributor: immutable(address)

totalSupply: public(uint256)

BASE_URL: constant(String[7]) = "ipfs://"

INITIAL_SUPPLY: constant(uint256) = 100

SUPPORTED_INTERFACES: constant(bytes4[3]) = [
    0x01ffc9a7, # ERC165 interface ID of ERC165
    0x80ac58cd, # ERC165 interface ID of ERC721
    0x5b5e139f, # ERC165 interface ID of the ERC-721 metadata extension
]

name: public(immutable(String[19]))
symbol: public(immutable(String[3]))

## Constructor

@external
def __init__(_initialMintWallet: address):

    distributor = _initialMintWallet
    name = "Zharta Genesis Pass"
    symbol = "ZGP"

    self.minter = msg.sender

    for i in range(1, INITIAL_SUPPLY+1):
        self.idToOwner[i] = _initialMintWallet
    self.ownerToNFTokenCount[_initialMintWallet] = INITIAL_SUPPLY
    self.totalSupply = INITIAL_SUPPLY



## External View Functions

@pure
@external
def supportsInterface(interface_id: bytes4) -> bool:
    return interface_id in SUPPORTED_INTERFACES


@view
@external
def balanceOf(_owner: address) -> uint256:
    assert _owner != ZERO_ADDRESS, "owner is zero addr"
    return self.ownerToNFTokenCount[_owner]


@view
@external
def ownerOf(_tokenId: uint256) -> address:
    owner: address = self.idToOwner[_tokenId]
    assert owner != ZERO_ADDRESS, "owner is zero addr"
    return owner


@view
@external
def getApproved(_tokenId: uint256) -> address:
    return empty(address)


@view
@external
def isApprovedForAll(_owner: address, _operator: address) -> bool:
    return False


@view
@external
def tokenURI(tokenId: uint256) -> String[132]:
    return concat(BASE_URL, uint2str(tokenId))


## External Write Functions

@external
def transferFrom(_from: address, _to: address, _tokenId: uint256):
    """
    @notice Only allows transfers from the distribution wallet setted in the contract constructor to allow distribution of pre minted tokens
    """
    assert msg.sender == distributor, "not supported"
    assert msg.sender == _from, "not supported"
    assert _to != ZERO_ADDRESS, "to is zero addr"
    assert self.idToOwner[_tokenId] == distributor, "token not owned"

    self.idToOwner[_tokenId] = _to
    self.ownerToNFTokenCount[_from] -= 1
    self.ownerToNFTokenCount[_to] += 1

    log Transfer(_from, _to, _tokenId)


@external
def safeTransferFrom(_from: address, _to: address, _tokenId: uint256, _data: Bytes[1024]=b""):
    """
    @notice Not supported
    """
    raise "not supported"

@external
def approve(_approved: address, _tokenId: uint256):
    """
    @notice Not supported
    """
    raise "not supported"


@external
def setApprovalForAll(_operator: address, _approved: bool):
    """
    @notice Not supported
    """
    raise "not supported"


@external
def mint(_to: address, _tokenId: uint256) -> bool:
    """
    @notice Mints a new token, only allows minting by the minter, set in the constructor as the contract deployer
    @param _to The address that will receive the minted token
    @param _tokenId The token id to mint
    @return A boolean that indicates if the operation was successful
    """
    assert msg.sender == self.minter, "sender is not minter"
    assert _to != ZERO_ADDRESS, "to is zero addr"
    assert self.idToOwner[_tokenId] == ZERO_ADDRESS, "token already minted"

    self.idToOwner[_tokenId] = _to
    self.ownerToNFTokenCount[_to] += 1
    self.totalSupply += 1

    log Transfer(ZERO_ADDRESS, _to, _tokenId)
    return True



