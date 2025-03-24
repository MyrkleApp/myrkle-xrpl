import asyncio
from xrpl.models import DIDDelete, DIDSet, LedgerEntry
from xrpl.asyncio.clients import AsyncJsonRpcClient

from x_constants import M_SOURCE_TAG

from misc import validate_symbol_to_hex, mm


# https://xrpl.org/docs/concepts/decentralized-storage/decentralized-identifiers


# region POST
def create_did(
    sender_addr: str,
    did_document: str = None,
    data: str = None,
    uri: str = None,
    fee: str = None,
) -> dict:
    """
    You must include either Data, DIDDocument, or URI.
    If all three fields are missing, the transaction fails.
    data: The public attestations of identity credentials associated with the DID.
    did: The DID document associated with the DID.
    uri: The Universal Resource Identifier associated with the DID.
    """
    txn = DIDSet(
        account=sender_addr,
        did_document=validate_symbol_to_hex(did_document),
        data=validate_symbol_to_hex(data),
        uri=validate_symbol_to_hex(uri),
        source_tag=M_SOURCE_TAG,
        memos=mm(),
        fee=fee,
    )
    return txn.to_xrpl()


def update_did(
    sender_addr: str,
    did_document: str = None,
    data: str = None,
    uri: str = None,
    fee: str = None,
) -> dict:
    """
    You must include either Data, DIDDocument, or URI.
    If all three fields are missing, the transaction fails.
    data: The public attestations of identity credentials associated with the DID.
    did: The DID document associated with the DID.
    uri: The Universal Resource Identifier associated with the DID.
    """
    txn = DIDSet(
        account=sender_addr,
        did_document=validate_symbol_to_hex(did_document),
        data=validate_symbol_to_hex(data),
        uri=validate_symbol_to_hex(uri),
        source_tag=M_SOURCE_TAG,
        memos=mm(),
        fee=fee,
    )
    return txn.to_xrpl()


def delete_did(sender_addr: str, fee: str = None) -> dict:
    txn = DIDDelete(account=sender_addr, source_tag=M_SOURCE_TAG, memos=mm(), fee=fee)
    return txn.to_xrpl()


# endregion


# region GET


async def account_did(url: str, wallet_addr: str) -> dict:
    """returns the did of an account"""
    did = {}
    req = LedgerEntry(ledger_index="validated", did=wallet_addr)
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    print(result)
    if "index" in result and "Account" in result["node"]:
        did["index"] = result["node"]["index"]
        did["did_document"] = result["node"]["DIDDocument"]
        did["data"] = result["node"]["Data"]
        did["uri"] = result["node"]["URI"]
    return did


# unecessary
# async def did_info(url: str, wallet_addr: str) -> dict:
#     pass

# endregion
