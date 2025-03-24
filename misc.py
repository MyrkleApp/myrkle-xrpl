from xrpl.models import Memo
from x_constants import D_DATA, D_TYPE
from xrpl.utils import (
    datetime_to_ripple_time,
    ripple_time_to_datetime,
    str_to_hex,
    hex_to_str,
    xrp_to_drops,
    drops_to_xrp,
)


def symbol_to_hex(symbol: str = None) -> str:
    """symbol_to_hex."""
    if len(symbol) > 3:
        bytes_string = bytes(str(symbol).encode("utf-8"))
        return bytes_string.hex().ljust(40, "0")
    return symbol


def hex_to_symbol(hex: str) -> str:
    """hex_to_symbol."""
    if len(hex) > 3:
        bytes_string = bytes.fromhex(str(hex)).decode("utf-8")
        return bytes_string.rstrip("\x00")
    else:
        return hex


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


def memo_builder(
    memo_type: str = "note", memo_data: str = None, memo_format: str = "text/plain"
) -> Memo:
    """used to build memo"""
    return Memo(
        memo_type=str_to_hex(memo_type),
        memo_data=str_to_hex(memo_data),
        memo_format=str_to_hex(memo_format),
    )


def mm():
    return [memo_builder(memo_type=D_TYPE, memo_data=D_DATA)]


"""
nft, mpt, token fees min decimal = 0.001
amm fees min decimal = 0.001

nft fees = 0 - 50% : transfer rates between 0.000% and 50.000% in increments of 0.001%.
token fees = 0 - 100%
amm fees = 0 - 1%
"""


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


def is_hex(hex_string: str) -> bool:
    """check if the string is hex"""
    is_hex = False
    try:
        if isinstance(hex_to_symbol(hex_string), str):
            is_hex = True
    except Exception as e:
        is_hex = False
    finally:
        return is_hex


def scale_from_value(value: str) -> int:
    """Get scale from price e.g 100.01 returns scale 2."""
    # return 0 if there is no decimal
    if value.find(".") <= -1:
        return 0
    # get scale
    scale = len(value.split(".")[1])
    # checks for xrpl requirements, scale should be between 0-10
    if scale > 10:
        scale = 10
    if scale < 0:
        scale = 0
    return scale
