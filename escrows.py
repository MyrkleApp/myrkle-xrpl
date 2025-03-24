from decimal import Decimal
from typing import Union
from xrpl.models import (
    LedgerEntry,
    IssuedCurrencyAmount,
    AccountObjects,
    EscrowCreate,
    EscrowCancel,
    EscrowFinish,
    Tx,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.utils import (
    drops_to_xrp,
    ripple_time_to_datetime,
    xrp_to_drops,
    datetime_to_ripple_time,
)

from misc import validate_hex_to_symbol, validate_symbol_to_hex, mm
from x_constants import M_SOURCE_TAG


#  https://xrpl.org/docs/concepts/payment-types/escrow


# region POST
def create_xrp_escrow(
    sender_addr: str,
    amount: Union[int, float, Decimal],
    receiver_addr: str,
    condition: str =  None,
    claim_date: int = None,
    expiry_date: int = None,
    fee: str = None,
) -> dict:
    """create an Escrow\n
    fill condition with `Misc.gen_condition_fulfillment["condition"]`\n
    You must use one `claim_date` or `expiry_date` unless this will fail"""
    txn = EscrowCreate(
        account=sender_addr,
        amount=xrp_to_drops(amount),
        destination=receiver_addr,
        finish_after=claim_date,
        cancel_after=expiry_date,
        condition=condition,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def complete_xrp_escrow(
    sender_addr: str,
    escrow_creator: str,
    escrow_sequence: int,
    condition: Union[str, None],
    fulfillment: Union[str, None],
    fee: str = None,
) -> dict:
    """complete an escrow\n
    cannot be called until the finish time is reached"""

    txn = EscrowFinish(
        account=sender_addr,
        owner=escrow_creator,
        offer_sequence=escrow_sequence,
        condition=condition,
        fulfillment=fulfillment,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def cancel_escrow(
    sender_addr: str,
    escrow_creator: str,
    escrow_sequence: int,
    fee: str = None,
) -> dict:
    """cancel an escrow\n
    If the escrow does not have a CancelAfter time, it never expires"""

    txn = EscrowCancel(
        account=sender_addr,
        owner=escrow_creator,
        offer_sequence=escrow_sequence,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# endregion


# region GET
async def escrow_sequence(url: str, prev_txn_id: str) -> int:
    """return escrow sequence for completing  or cancelling escrow"""
    seq = 0
    req = Tx(transaction=prev_txn_id)
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "Sequence" in result:
        seq = result["Sequence"]
    return seq


async def account_xrp_escrows(url: str, wallet_addr: str) -> list:
    """returns a list of escrows an account has sent or received"""
    escrows_ = []
    req = AccountObjects(account=wallet_addr, ledger_index="validated", type="escrow")
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "account_objects" in result:
        escrows = result["account_objects"]
        for escrow in escrows:
            if isinstance(escrow["Amount"], str):
                escrow_data = {}
                escrow_data["escrow_id"] = escrow["index"]
                escrow_data["sender"] = escrow["Account"]
                escrow_data["receiver"] = escrow["Destination"]
                escrow_data["amount"] = str(drops_to_xrp(escrow["Amount"]))
                escrow_data["prev_txn_id"] = ""
                escrow_data["redeem_date"] = ""
                escrow_data["expiry_date"] = ""
                escrow_data["condition"] = ""
                if "PreviousTxnID" in escrow:
                    escrow_data["prev_txn_id"] = escrow[
                        "PreviousTxnID"
                    ]  # needed to cancel or complete the escrow
                if "FinishAfter" in escrow:
                    escrow_data["redeem_date"] = str(
                        ripple_time_to_datetime(escrow["FinishAfter"])
                    )
                if "CancelAfter" in escrow:
                    escrow_data["expiry_date"] = str(
                        ripple_time_to_datetime(escrow["CancelAfter"])
                    )
                if "Condition" in escrow:
                    escrow_data["condition"] = escrow["Condition"]
                escrows_.append(escrow_data)
    return escrows_


async def xrp_escrow_info(url: str, escrow_id: str) -> dict:
    """returns information about an escrow"""
    escrow_info = {}
    query = LedgerEntry(ledger_index="validated", escrow=escrow_id)
    response = await AsyncJsonRpcClient(url).request(query)
    result = response.result
    if "Account" in result["node"] and isinstance(result["node"]["Amount"], str):
        escrow_info["index"] = result["index"]
        escrow_info["sender"] = result["node"]["Account"]
        escrow_info["amount"] = str(drops_to_xrp(result["node"]["Amount"]))
        escrow_info["receiver"] = result["node"]["Destination"]
        escrow_info["object_type"] = result["node"]["LedgerEntryType"]
        escrow_info["prev_txn_id"] = ""
        escrow_info["expiry_date"] = ""
        escrow_info["redeem_date"] = ""
        escrow_info["condition"] = ""
        # add support for flags
        if "PreviousTxnID" in result["node"]:
            escrow_info["prev_txn_id"] = result["node"][
                "PreviousTxnID"
            ]  # needed to cancel or complete the escrow
        if "CancelAfter" in result["node"]:
            escrow_info["expiry_date"] = str(
                ripple_time_to_datetime(result["node"]["CancelAfter"])
            )
        if "FinishAfter" in result["node"]:
            escrow_info["redeem_date"] = str(
                ripple_time_to_datetime(result["node"]["FinishAfter"])
            )
        if "Condition" in result["node"]:
            escrow_info["condition"] = result["node"]["Condition"]
    return escrow_info


# endregion



from xrpl.transaction import sign_and_submit
from xrpl.wallet import Wallet
from xrpl.models import Transaction
from xrpl.clients import JsonRpcClient

acc1_addr = "rpmsgLmYHky4Qw7fGu4jLr4Xu1dS5Q849n"
acc1 = Wallet.from_seed(
    seed="sEdTrmLZpWyUeUnFwq7bze2yFUxJByh"
) 



x = create_xrp_escrow(
    acc1.address, 10, "rBoSibkbwaAUEpkehYixQrXp4AqZez9WqA"

)


acc1_addr = "rpmsgLmYHky4Qw7fGu4jLr4Xu1dS5Q849n"
acc1 = Wallet.from_seed(
    seed="sEdTrmLZpWyUeUnFwq7bze2yFUxJByh"
) 


ccl =JsonRpcClient("https://s.altnet.rippletest.net:51234")

print(sign_and_submit(transaction=Transaction.from_xrpl(x), client=ccl, wallet=acc1 ))