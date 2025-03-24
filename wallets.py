from xrpl.models import (
    NFTokenAcceptOffer,
    NFTokenCreateOffer,
    NFTokenCreateOfferFlag,
    MPTAmount,
)
from xrpl.utils import (
    drops_to_xrp,
    ripple_time_to_datetime,
    xrp_to_drops,
    datetime_to_ripple_time,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.transaction.main import sign_and_submit
import requests

from misc import (
    memo_builder,
    validate_hex_to_symbol,
    validate_symbol_to_hex,
    mm,
    nft_fee_to_xrp_format,
    xrp_format_to_nft_fee,
)
from x_constants import M_SOURCE_TAG, PAYMENT_FLAGS
from xrpl.wallet import Wallet
from decimal import Decimal
from typing import Union

from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.clients import JsonRpcClient
from xrpl.asyncio.ledger import get_fee
from xrpl.models import (
    AccountInfo,
    AccountLines,
    AccountNFTs,
    AccountTx,
    IssuedCurrencyAmount,
    Memo,
    NFTokenAcceptOffer,
    NFTokenCreateOffer,
    NFTokenCreateOfferFlag,
    Payment,
    PaymentFlag,
    Tx,
)
from xrpl.utils import drops_to_xrp, ripple_time_to_datetime, xrp_to_drops

from misc import (
    is_hex,
    memo_builder,
    validate_hex_to_symbol,
    validate_symbol_to_hex,
    xrp_format_to_nft_fee,
)

from x_constants import D_DATA, D_TYPE, M_SOURCE_TAG


# https://xrpl.org/docs/references/protocol/transactions/types/payment#example-payment-json

# region POST


def send_xrp(
    sender_addr: str,
    receiver_addr: str,
    amount: Union[float, Decimal, int],
    destination_tag: int = None,
    note: str = None,
    fee: str = None,
) -> dict:
    """send xrp"""
    txn = Payment(
        account=sender_addr,
        amount=xrp_to_drops(amount),
        destination=receiver_addr,
        destination_tag=destination_tag,
        source_tag=M_SOURCE_TAG,
        fee=fee,
        memos=[memo_builder(memo_data=note)],
    )
    return txn.to_xrpl()


# TODO: set to send token, no support for AMM bs
def send_token(
    sender_addr: str,
    receiver_addr: str,
    token: str,
    amount: str,
    issuer: str,
    partial: bool = False,
    is_lp_token: bool = False,
    destination_tag: int = None,
    note: str = None,
    fee: str = None,
) -> dict:
    """send asset...
    if token has fee - enable partial
    max amount = 15 decimal places"""
    cur = token if is_lp_token else validate_symbol_to_hex(token)
    flags = 0
    if partial:
        flags = PaymentFlag.TF_PARTIAL_PAYMENT.value
    txn = Payment(
        account=sender_addr,
        destination=receiver_addr,
        amount=IssuedCurrencyAmount(currency=cur, issuer=issuer, value=amount),
        destination_tag=destination_tag,
        fee=fee,
        flags=flags,
        send_max=IssuedCurrencyAmount(currency=cur, issuer=issuer, value=amount),
        memos=[memo_builder(memo_data=note)],
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def send_nft(
    sender_addr: str, nftoken_id: str, receiver: str, note: str = None, fee: str = None
) -> dict:
    """send an nft - by creating a zero-amount sell transaction"""
    txn = NFTokenCreateOffer(
        account=sender_addr,
        nftoken_id=nftoken_id,
        amount="0",
        destination=receiver,
        flags=NFTokenCreateOfferFlag.TF_SELL_NFTOKEN.value,
        memos=[memo_builder(memo_data=note)],
        source_tag=M_SOURCE_TAG,
        fee=fee,
    )
    return txn.to_xrpl()


def receive_nft(sender_addr: str, nft_sell_id: str, fee: str = None) -> dict:
    """receive an nft"""
    txn = NFTokenAcceptOffer(
        account=sender_addr,
        nftoken_sell_offer=nft_sell_id,
        fee=fee,
        source_tag=M_SOURCE_TAG,
        memos=mm(),
    )
    return txn.to_xrpl()


# TODO: send mpt token
def send_mpt_token(
    sender_addr: str,
    mpt_issuance_id: str,
    amount: str,
    receiver_addr: str,
    fee: str = None,
) -> dict:
    txn = Payment(
        account=sender_addr,
        amount=MPTAmount(
            mpt_issuance_id=mpt_issuance_id,
            value=amount,
        ),
        send_max=MPTAmount(
            mpt_issuance_id=mpt_issuance_id,
            value=amount,
        ),
        destination=receiver_addr,
        fee=fee,
        source_tag=M_SOURCE_TAG,
        memos=mm(),
    )
    return txn.to_xrpl()


# endregion


# region GET


def parse_pay_txn_flag(pay_flag: int) -> list:
    flags = []
    for flag in PAYMENT_FLAGS:
        if flag["hex"] & pay_flag == flag["hex"]:
            flags.append(flag)
    return flags


async def get_network_fee(url: str) -> str:
    """return transaction fee, to populate interface and carry out transactions"""
    return await get_fee(await AsyncJsonRpcClient(url))


# TODO: will have to update to match the new xrpl reserve
async def xrp_balance(url: str, wallet_addr: str) -> dict:
    """return xrp balance and objects count"""
    _balance = 0
    owner_count = 0
    balance = 0
    acc_info = AccountInfo(account=wallet_addr, ledger_index="validated")
    response = await AsyncJsonRpcClient(url).request(acc_info)
    result = response.result
    if "account_data" in result:
        _balance = int(result["account_data"]["Balance"]) - 10000000
        owner_count = int(result["account_data"]["OwnerCount"])
        balance = _balance - (2000000 * owner_count)
    return {"object_count": owner_count, "balance": str(drops_to_xrp(str(balance)))}


async def xrp_transactions(url: str, wallet_addr: str) -> dict:
    """return all xrp payment transactions an address has carried out"""
    transactions_dict = {}
    sent = []
    received = []
    acc_tx = AccountTx(account=wallet_addr)
    response = await AsyncJsonRpcClient(url).request(acc_tx)
    result = response.result
    if "transactions" in result:
        for transaction in result["transactions"]:
            if transaction["tx"]["TransactionType"] == "Payment":
                transact = {}
                transact["sender"] = transaction["tx"]["Account"]
                transact["receiver"] = transaction["tx"]["Destination"]
                transact["amount"] = (
                    str(drops_to_xrp(str(transaction["meta"]["delivered_amount"])))
                    if "delivered_amount" in transaction["meta"]
                    and isinstance(transaction["meta"]["delivered_amount"], str)
                    else str(drops_to_xrp(str(transaction["tx"]["Amount"])))
                )
                transact["fee"] = str(drops_to_xrp(str(transaction["tx"]["Fee"])))
                transact["timestamp"] = str(
                    ripple_time_to_datetime(transaction["tx"]["date"])
                )
                transact["result"] = transaction["meta"]["TransactionResult"]
                transact["txid"] = transaction["tx"]["hash"]
                transact["tx_type"] = transaction["tx"]["TransactionType"]
                # transact["memo"] = transaction["tx"]["Memo"] // this is a list that contains dicts 'parse later'
                if transact["sender"] == wallet_addr:
                    sent.append(transact)
                elif transact["sender"] != wallet_addr:
                    received.append(transact)
    transactions_dict["sent"] = sent
    transactions_dict["received"] = received
    return transactions_dict


async def token_transactions(url: str, wallet_addr: str) -> dict:
    """return all token payment transactions an account has carried out"""
    transactions_dict = {}
    sent = []
    received = []
    acc_tx = AccountTx(account=wallet_addr)
    response = await AsyncJsonRpcClient(url).request(acc_tx)
    result = response.result
    if "transactions" in result:
        for transaction in result["transactions"]:
            if transaction["tx"]["TransactionType"] == "Payment" and isinstance(
                transaction["tx"]["Amount"], dict
            ):
                transact = {}
                transact["sender"] = transaction["tx"]["Account"]
                transact["receiver"] = transaction["tx"]["Destination"]
                transact["token"] = (
                    validate_hex_to_symbol(
                        transaction["meta"]["delivered_amount"]["currency"]
                    )
                    if "delivered_amount" in transaction["meta"]
                    and isinstance(transaction["meta"]["delivered_amount"], dict)
                    else validate_hex_to_symbol(transaction["tx"]["Amount"]["currency"])
                )
                transact["issuer"] = (
                    transaction["meta"]["delivered_amount"]["issuer"]
                    if "delivered_amount" in transaction["meta"]
                    and isinstance(transaction["meta"]["delivered_amount"], dict)
                    else validate_hex_to_symbol(transaction["tx"]["Amount"]["issuer"])
                )
                transact["amount"] = (
                    transaction["meta"]["delivered_amount"]["value"]
                    if "delivered_amount" in transaction["meta"]
                    and isinstance(transaction["meta"]["delivered_amount"], dict)
                    else validate_hex_to_symbol(transaction["tx"]["Amount"]["value"])
                )
                transact["fee"] = str(drops_to_xrp(str(transaction["tx"]["Fee"])))
                transact["timestamp"] = str(
                    ripple_time_to_datetime(transaction["tx"]["date"])
                )
                transact["result"] = transaction["meta"]["TransactionResult"]
                transact["txid"] = transaction["tx"]["hash"]
                transact["tx_type"] = transaction["tx"]["TransactionType"]
                # transact["memo"] = transaction["tx"]["Memo"] // this is a list that contains dicts 'parse later'
                if transact["sender"] == wallet_addr:
                    sent.append(transact)
                elif transact["sender"] != wallet_addr:
                    received.append(transact)
    transactions_dict["sent"] = sent
    transactions_dict["received"] = received
    return transactions_dict


async def payment_transactions(url: str, wallet_addr: str) -> dict:
    """return all payment transactions for xrp and tokens both sent and received"""
    transactions = []
    acc_tx = AccountTx(account=wallet_addr)
    response = await AsyncJsonRpcClient(url).request(acc_tx)
    result = response.result
    if "transactions" in result:
        for transaction in result["transactions"]:
            if transaction["tx"]["TransactionType"] == "Payment":
                transact = {}
                transact["sender"] = transaction["tx"]["Account"]
                transact["receiver"] = transaction["tx"]["Destination"]
                if isinstance(transaction["tx"]["Amount"], str):
                    transact["token"] = "XRP"
                    transact["issuer"] = ""
                    transact["amount"] = (
                        str(drops_to_xrp(str(transaction["meta"]["delivered_amount"])))
                        if "delivered_amount" in transaction["meta"]
                        and isinstance(transaction["meta"]["delivered_amount"], str)
                        else str(drops_to_xrp(str(transaction["tx"]["Amount"])))
                    )
                if (
                    isinstance(transaction["tx"]["Amount"], dict)
                    or "delivered_amount" in transaction["meta"]
                    and isinstance(transaction["meta"]["delivered_amount"], dict)
                ):
                    transact["token"] = (
                        validate_hex_to_symbol(
                            transaction["meta"]["delivered_amount"]["currency"]
                        )
                        if "delivered_amount" in transaction["meta"]
                        and isinstance(transaction["meta"]["delivered_amount"], dict)
                        else validate_hex_to_symbol(
                            transaction["tx"]["Amount"]["currency"]
                        )
                    )
                    transact["issuer"] = (
                        transaction["meta"]["delivered_amount"]["issuer"]
                        if "delivered_amount" in transaction["meta"]
                        and isinstance(transaction["meta"]["delivered_amount"], dict)
                        else validate_hex_to_symbol(
                            transaction["tx"]["Amount"]["issuer"]
                        )
                    )
                    transact["amount"] = (
                        transaction["meta"]["delivered_amount"]["value"]
                        if "delivered_amount" in transaction["meta"]
                        and isinstance(transaction["meta"]["delivered_amount"], dict)
                        else transaction["tx"]["Amount"]["value"]
                    )
                transact["fee"] = str(drops_to_xrp(str(transaction["tx"]["Fee"])))
                transact["timestamp"] = str(
                    ripple_time_to_datetime(transaction["tx"]["date"])
                )
                transact["result"] = transaction["meta"]["TransactionResult"]
                transact["txid"] = transaction["tx"]["hash"]
                transact["tx_type"] = transaction["tx"]["TransactionType"]
                # transact["memo"] = transaction["tx"]["Memo"] // this is a list that contains dicts 'parse later'
                transactions.append(transact)
    return transactions


async def payment_transaction_info(url: str, txid: str) -> dict:
    """return more information on a single payment transaction"""
    pay_dict = {}
    query = Tx(transaction=txid)
    response = await AsyncJsonRpcClient(url).request(query)
    result = response.result
    if "Account" in result:
        pay_dict["sender"] = result["Account"]
        pay_dict["receiver"] = result["Destination"]
        if isinstance(result["Amount"], str):
            pay_dict["token"] = "XRP"
            pay_dict["issuer"] = ""
            pay_dict["amount"] = (
                str(drops_to_xrp(str(result["meta"]["delivered_amount"])))
                if "delivered_amount" in result["meta"]
                and isinstance(result["meta"]["delivered_amount"], str)
                else str(drops_to_xrp(str(result["Amount"])))
            )
        if (
            isinstance(result["Amount"], dict)
            or "delivered_amount" in result["meta"]
            and isinstance(result["meta"]["delivered_amount"], dict)
        ):
            pay_dict["token"] = (
                validate_hex_to_symbol(result["meta"]["delivered_amount"]["currency"])
                if "delivered_amount" in result["meta"]
                and isinstance(result["meta"]["delivered_amount"], dict)
                else validate_hex_to_symbol(result["Amount"]["currency"])
            )
            pay_dict["issuer"] = (
                result["meta"]["delivered_amount"]["issuer"]
                if "delivered_amount" in result["meta"]
                and isinstance(result["meta"]["delivered_amount"], dict)
                else validate_hex_to_symbol(result["Amount"]["issuer"])
            )
            pay_dict["amount"] = (
                result["meta"]["delivered_amount"]["value"]
                if "delivered_amount" in result["meta"]
                and isinstance(result["meta"]["delivered_amount"], dict)
                else result["Amount"]["value"]
            )
        pay_dict["fee"] = str(drops_to_xrp(result["Fee"]))
        pay_dict["date"] = str(ripple_time_to_datetime(result["date"]))
        pay_dict["txid"] = result["hash"]
        pay_dict["tx_type"] = result["TransactionType"]
        pay_dict["flags"] = (
            parse_pay_txn_flag(result["Flags"]) if "Flags" in result else []
        )  # work on transaction flags later
        pay_dict["sequence"] = result["Sequence"]
        pay_dict["in_ledger"] = result["inLedger"]
        pay_dict["signature"] = result["TxnSignature"]
        pay_dict["index"] = result["meta"]["TransactionIndex"]
        pay_dict["result"] = result["meta"]["TransactionResult"]
        pay_dict["ledger_state"] = result["validated"]
    return pay_dict


# endregion
