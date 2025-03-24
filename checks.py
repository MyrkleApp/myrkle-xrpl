from decimal import Decimal
from typing import Union
from xrpl.models import (
    CheckCreate,
    CheckCash,
    CheckCancel,
    LedgerEntry,
    IssuedCurrencyAmount,
    AccountObjects,
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


# https://xrpl.org/docs/concepts/payment-types/checks

# TODO: i will eventually have to convert the datetime object sammy sends to ripple time object to pass for creating check and other time related objects


# region POST
def create_xrp_check(
    sender_addr: str,
    receiver_addr: str,
    amount: Union[int, float, Decimal],
    expiry_date: int = None,
    invoice_id: str = None,
    fee: str = None,
) -> dict:
    """create xrp check"""
    txn = CheckCreate(
        account=sender_addr,
        destination=receiver_addr,
        invoice_id=invoice_id,
        send_max=xrp_to_drops(amount),
        expiration=expiry_date,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def cash_xrp_check(
    sender_addr: str, check_id: str, amount: Union[int, Decimal, float], fee: str = None
) -> dict:
    """cash a check, only the receiver defined on creation can cash a check"""
    txn = CheckCash(
        account=sender_addr,
        check_id=check_id,
        amount=xrp_to_drops(amount),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def create_token_check(
    sender_addr: str,
    receiver_addr: str,
    token: str,
    amount: str,
    issuer: str,
    expiry_date: Union[int, None],
    fee: str = None,
) -> dict:
    """create a token check"""
    txn = CheckCreate(
        account=sender_addr,
        destination=receiver_addr,
        send_max=IssuedCurrencyAmount(
            currency=validate_symbol_to_hex(token), issuer=issuer, value=amount
        ),
        expiration=expiry_date,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def cash_token_check(
    sender_addr: str,
    check_id: str,
    token: str,
    amount: str,
    issuer: str,
    fee: str = None,
) -> dict:
    """cash a check, only the receiver defined on creation
    can cash a check"""
    txn = CheckCash(
        account=sender_addr,
        check_id=check_id,
        amount=IssuedCurrencyAmount(
            currency=validate_symbol_to_hex(token), issuer=issuer, value=amount
        ),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def cancel_check(sender_addr: str, check_id: str, fee: str = None) -> dict:
    """cancel a check"""
    txn = CheckCancel(
        account=sender_addr,
        check_id=check_id,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# endregion


# region GET
async def account_checks(url: str, wallet_addr: str) -> list:
    """return a list of checks an account sent or received"""
    checks_ = []
    req = AccountObjects(account=wallet_addr, ledger_index="validated", type="check")
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "account_objects" in result:
        account_checks = result["account_objects"]
        for check in account_checks:
            check_data = {}
            check_data["check_id"] = check["index"]
            check_data["sender"] = check["Account"]
            check_data["receiver"] = check["Destination"]
            check_data["expiry_date"] = ""
            if isinstance(check["SendMax"], str):
                check_data["token"] = "XRP"
                check_data["issuer"] = ""
                check_data["amount"] = str(drops_to_xrp(check["SendMax"]))
            if isinstance(check["SendMax"], dict):
                check_data["token"] = validate_hex_to_symbol(
                    check["SendMax"]["currency"]
                )
                check_data["issuer"] = check["SendMax"]["issuer"]
                check_data["amount"] = check["SendMax"]["value"]
            if "Expiration" in check:
                check_data["expiry_date"] = str(
                    ripple_time_to_datetime(check["Expiration"])
                )
            checks_.append(check_data)
    return checks_


async def check_info(url: str, check_id: str) -> dict:
    """returns information about a check"""
    check_info = {}
    query = LedgerEntry(ledger_index="validated", check=check_id)
    response = await AsyncJsonRpcClient(url).request(query)
    result = response.result
    if "Account" in result["node"]:
        check_info["index"] = result["index"]
        check_info["sender"] = result["node"]["Account"]
        check_info["receiver"] = result["node"]["Destination"]
        check_info["sequence"] = result["node"]["Sequence"]
        check_info["object_type"] = result["node"]["LedgerEntryType"]
        check_info["expiry_date"] = ""
        if "Expiration" in result["node"]:
            check_info["expiry_date"] = str(
                ripple_time_to_datetime(result["node"]["Expiration"])
            )
        # add support for flags
        if isinstance(result["node"]["SendMax"], str):
            check_info["token"] = "XRP"
            check_info["issuer"] = ""
            check_info["amount"] = str(drops_to_xrp(result["node"]["SendMax"]))
        elif isinstance(result["node"]["SendMax"], dict):
            check_info["token"] = validate_hex_to_symbol(
                result["node"]["SendMax"]["currency"]
            )
            check_info["issuer"] = result["node"]["SendMax"]["issuer"]
            check_info["amount"] = result["node"]["SendMax"]["value"]
    return check_info


# endregion
