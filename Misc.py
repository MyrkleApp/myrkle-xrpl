import random
from datetime import datetime
from os import urandom
from typing import Union

import requests

# from cryptoconditions import PreimageSha256
from xrpl.asyncio.account import does_account_exist
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.core.addresscodec import (
    classic_address_to_xaddress,
    is_valid_classic_address,
    is_valid_xaddress,
    xaddress_to_classic_address,
)
from xrpl.models import AccountInfo, Memo
from xrpl.utils import (
    datetime_to_ripple_time,
    ripple_time_to_datetime,
    str_to_hex,
    hex_to_str,
)
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet, generate_faucet_wallet

from x_constants import (
    ACCOUNT_ROOT_FLAGS,
    D_DATA,
    D_TYPE,
    NFTOKEN_FLAGS,
    NFTOKEN_OFFER_FLAGS,
    OFFER_FLAGS,
    PAYMENT_FLAGS,
)

# Memo(
#     memo_type=hex_to_str(),
#     memo_data=
# )


async def exist(wallet_addr: str, mainnet: bool = True):
    """check if account exists on the ledger"""
    client = (
        AsyncJsonRpcClient("https://xrplcluster.com")
        if mainnet
        else AsyncJsonRpcClient("https://s.altnet.rippletest.net:51234")
    )
    return await does_account_exist(wallet_addr, client)


def memo_builder(memo_type: str, memo_data: str) -> Memo:
    """used to build memo"""
    return Memo(memo_type=str_to_hex(memo_type), memo_data=str_to_hex(memo_data))


def mm():
    return [memo_builder(D_TYPE, D_DATA)]


def verify_address(wallet_addr: str) -> bool:
    """verify if address is valid"""
    value = False
    if is_valid_classic_address(wallet_addr) or is_valid_xaddress(wallet_addr):
        value = True
    return value


def classic_to_x(
    wallet_address: str, tag: Union[int, None], is_testnet: bool = False
) -> str:
    "convert classic 'r' address to x address"
    return classic_address_to_xaddress(
        classic_address=wallet_address, tag=tag, is_test_network=is_testnet
    )


def x_to_classic(wallet_address: str) -> dict:
    "convert x address to classic 'r' address"
    addr = xaddress_to_classic_address(wallet_address)
    return {"classic_address": addr[0], "tag": addr[1], "is_testnet": addr[2]}


def __convert_datetime_rippletime(obj: datetime) -> int:
    """converts a datetime object to ripple time"""
    return datetime_to_ripple_time(obj)


def __convert_rippletime_datetime(obj: int) -> datetime:
    """converts ripple time to datetime object"""
    return ripple_time_to_datetime(obj)


def get_test_xrp(wallet: Wallet) -> None:
    """fund your account with free 1000 test xrp"""
    testnet_url = "https://s.altnet.rippletest.net:51234"
    client = JsonRpcClient(testnet_url)
    print(generate_faucet_wallet(client, wallet).classic_address)


def symbol_to_hex(symbol: str = None) -> str:
    """symbol_to_hex."""
    if len(symbol) > 3:
        bytes_string = bytes(str(symbol).encode("utf-8"))
        return bytes_string.hex().ljust(40, "0")
    return symbol


def hex_to_symbol(hex: str = None) -> str:
    """hex_to_symbol."""
    if len(hex) > 3:
        bytes_string = bytes.fromhex(str(hex)).decode("utf-8")
        return bytes_string.rstrip("\x00")


def validate_hex_to_symbol(hex: str = None) -> str:
    result = ""
    try:
        result = hex_to_symbol(hex)
    except Exception as e:
        result = hex
    finally:
        return result


def validate_symbol_to_hex(symbol: str = None) -> str:
    result = ""
    try:
        result = symbol_to_hex(symbol)
    except Exception as e:
        result = symbol
    finally:
        return result


def is_hex(hex_string: str) -> bool:
    """check if the string is hex """
    is_hex = False
    try:
        if isinstance(hex_to_symbol(hex_string), str):
            is_hex = True
    except Exception as e:
        is_hex = False
    finally:
        return is_hex





"""
nft and token fees min decimal = 0.001
amm fees min decimal = 0.001

nft fees = 0 - 50% : transfer rates between 0.000% and 50.000% in increments of 0.001%.
token fees = 0 - 100%
amm fees = 0 - 1%
"""


def transfer_fee_to_xrp_format(transfer_fee: float) -> int:
    """convert fee to XRP fee format\n
    pass percentage as integer e.g
    `20` = `20%`"""
    base_fee = 1000000000  # 1000000000 == 0%
    val = base_fee * transfer_fee
    val = val / 100
    return int(val + base_fee)


def xrp_format_to_transfer_fee(format: int) -> float:
    """convert xrp fee format to usable fee in percentage"""
    base_fee = 1_000_000_000  # 1000000000 == 0%
    val = format - base_fee
    return val / base_fee * 100


def nft_fee_to_xrp_format(nft_fee: float) -> int:
    """convert nft fee in percentage to XRP fee format\n
    pass percentage as integer e.g
    `20` = `20%`"""
    assert nft_fee <= 50
    max_fee = 50000
    return int((max_fee * nft_fee) / 50)


def xrp_format_to_nft_fee(format: int) -> float:
    """convert xrp fee format to usable fee in percentage"""
    assert format <= 50000
    max_fee = 50
    return (max_fee * format) / 50000


def amm_fee_to_xrp_format(amm_fee: float) -> int:
    """converts 1% to 1000"""
    assert amm_fee <= 1
    max_fee = 1000
    return int((amm_fee * max_fee) / 1)


def xrp_format_to_amm_fee(format: int) -> float:
    """converts 1000 to 1%"""
    assert format <= 1000
    max_fee = 1
    return (max_fee * format) / 1000


def bytes_generator() -> bytes:
    """generates a random byte"""
    return urandom(random.randint(32, 128))


# def gen_condition_fulfillment_1() -> dict:
#     """Generate a condition and fulfillment for escrows"""
#     fufill = PreimageSha256(preimage=urandom(32))
#     return {
#         "condition": str.upper(fufill.condition_binary.hex()),
#         "fulfillment": str.upper(fufill.serialize_binary().hex()),
#     }


async def token_market_info(token: str, issuer: str) -> dict:
    """retrieve token market info, use to retrieve token price; image; \n
    see x_constants.market_info_type\n
    will probably only work on mainnet"""
    return requests.get(
        f"https://s1.xrplmeta.org/token/{validate_symbol_to_hex(token)}:{issuer}"
    ).json()


async def account_is_amm(wallet_addr: str, mainnet: bool = True) -> bool:
    """check if an address is an amm instance, should evaluate to false if sending token or xrp\n
    if true, dont send token"""
    amm_flag = False
    client = (
        AsyncJsonRpcClient("https://xrplcluster.com")
        if mainnet
        else AsyncJsonRpcClient("https://s.altnet.rippletest.net:51234")
    )

    acc_info = AccountInfo(account=wallet_addr, ledger_index="validated")
    response = await client.request(acc_info)
    result = response.result
    if "account_data" in result:
        flag = result["account_data"]["Flags"]
        for root_flags in ACCOUNT_ROOT_FLAGS:
            check_flag = root_flags["hex"]
            if check_flag & flag == 0x02000000:
                amm_flag = True
    return amm_flag


def parse_offer_flags(offer_flag: int) -> list:
    flags = []
    for flag in OFFER_FLAGS:
        if flag["hex"] & offer_flag == flag["hex"]:
            flags.append(flag)
    return flags


def parse_account_flags(account_flag: int) -> list:
    """returns all the flags associated with an account"""
    flags = []
    for flag in ACCOUNT_ROOT_FLAGS:
        if flag["hex"] & account_flag == flag["hex"]:
            flags.append(flag)
    return flags


def parse_nft_flags(nft_flag: int) -> list:
    flags = []
    for flag in NFTOKEN_FLAGS:
        if flag["hex"] & nft_flag == flag["hex"]:
            flags.append(flag)
    return flags


def parse_nft_offer_flags(offer_flag: int) -> list:
    flags = []
    for flag in NFTOKEN_OFFER_FLAGS:
        if flag["hex"] & offer_flag == flag["hex"]:
            flags.append(flag)
    return flag


def parse_pay_txn_flag(pay_flag: int) -> list:
    flags = []
    for flag in PAYMENT_FLAGS:
        if flag["hex"] & pay_flag == flag["hex"]:
            flags.append(flag)
    return flags


# def get_test_xrp(wallet: Wallet = None) -> None:
#     """fund your account with free 1000 test xrp"""
#     testnet_url = "http://s.devnet.rippletest.net:51234"
#     testnet_url = "https://s.altnet.rippletest.net:51234"
#     client = JsonRpcClient(testnet_url)
#     print(generate_faucet_wallet(client).seed)
#     print()


# print(get_test_xrp())

# sEdTrmLZpWyUeUnFwq7bze2yFUxJByh

wals = [Wallet.from_seed(seed= "sEdS1jTVU58HsPeL4xhPkziphnxFDHz"),
Wallet.from_seed(seed= "sEdVdthdYnRRLqBXAD76QC7CatoLqU8"),
Wallet.from_seed(seed= "sEdTrmLZpWyUeUnFwq7bze2yFUxJByh"),
 Wallet.from_seed(seed= "sEd7Nh8MGkfpfhfh2Q7R7RVK9zPGhKa"),
Wallet.from_seed(seed= "sEd7gZdeatsAwuMJp2uhbJ9vgFfohMd"),]

print(wals[1].address)

for i in wals:
    get_test_xrp(i)
    print(i.address)
   
