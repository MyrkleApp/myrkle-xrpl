
from misc import validate_hex_to_symbol
from xrpl.utils import (
    drops_to_xrp,
    ripple_time_to_datetime,
    xrp_to_drops,
    datetime_to_ripple_time,
)
from xrpl.models import (AccountOffers, OfferCreateFlag, OfferCancel, BookOffers, IssuedCurrency, XRP, OfferCreate, IssuedCurrencyAmount, LedgerEntry)
from xrpl.models.requests.ledger_entry import Offer
from typing import Union
from misc import validate_hex_to_symbol, validate_symbol_to_hex, mm
from x_constants import M_SOURCE_TAG, OFFER_FLAGS
from xrpl.asyncio.clients import AsyncJsonRpcClient



# https://xrpl.org/docs/concepts/tokens/decentralized-exchange/offers

# region POST

def create_order_book_liquidity(sender_addr: str, buy: Union[float, IssuedCurrencyAmount], sell: Union[float, IssuedCurrencyAmount], expiry_date: int = None, fee: str = None) -> dict:
    """create an offer as passive; it doesn't immediately consume offers that match it, just stays on the ledger as an object for liquidity"""
    flags = [OfferCreateFlag.TF_PASSIVE]
    tx_dict = {}
    if isinstance(buy, float) and isinstance(sell, IssuedCurrencyAmount): # check if give == xrp and get == asset
        txn = OfferCreate(account=sender_addr, taker_pays=xrp_to_drops(buy), taker_gets=sell, flags=flags, expiration=expiry_date, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
        tx_dict = txn.to_xrpl()
    if isinstance(buy, IssuedCurrencyAmount) and isinstance(sell, float): # check if give == asset and get == xrp
        txn = OfferCreate(account=sender_addr, taker_pays=buy, taker_gets=xrp_to_drops(sell), flags=flags, expiration=expiry_date, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
        tx_dict = txn.to_xrpl()
    if isinstance(buy, IssuedCurrencyAmount) and isinstance(sell, IssuedCurrencyAmount): # check if give and get are == asset
        txn = OfferCreate(account=sender_addr, taker_pays=buy, taker_gets=sell, flags=flags, expiration=expiry_date, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
        tx_dict = txn.to_xrpl()
    return tx_dict

def order_book_swap(sender_addr: str, buy: Union[float, IssuedCurrencyAmount], sell: Union[float, IssuedCurrencyAmount], tf_sell: bool = False, tf_fill_or_kill: bool = False, tf_immediate_or_cancel: bool = False, fee: str = None) -> dict:
    """create an offer that either matches with existing offers to get entire sell amount or cancels\n
    if swap_all is enabled, this will force exchange all the paying units regardless of profit or loss\n

    if tecKILLED is the result, exchange didnt go through because all of the `buy` couldnt be obtained. recommend enabling swap_all
    """
    flags = []
    if tf_sell:
        flags.append(OfferCreateFlag.TF_SELL)
    if tf_fill_or_kill:
        flags.append(OfferCreateFlag.TF_FILL_OR_KILL)
    if tf_immediate_or_cancel:
        flags.append(OfferCreateFlag.TF_IMMEDIATE_OR_CANCEL)
    tx_dict = {}
    if isinstance(buy, float) and isinstance(sell, IssuedCurrencyAmount): # check if give == xrp and get == asset
        txn = OfferCreate(account=sender_addr, taker_pays=xrp_to_drops(buy), taker_gets=sell, flags=flags, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
        tx_dict = txn.to_xrpl()
    if isinstance(buy, IssuedCurrencyAmount) and isinstance(sell, float): # check if give == asset and get == xrp
        txn = OfferCreate(account=sender_addr, taker_pays=buy, taker_gets=xrp_to_drops(sell), flags=flags, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
        tx_dict = txn.to_xrpl()
    if isinstance(buy, IssuedCurrencyAmount) and isinstance(sell, IssuedCurrencyAmount): # check if give and get are == asset
        txn = OfferCreate(account=sender_addr, taker_pays=buy, taker_gets=sell, flags=flags, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
        tx_dict = txn.to_xrpl()
    return tx_dict


def cancel_offer(sender_addr: str, offer_seq: int, fee: str = None) -> dict:
    """cancel an offer"""
    txn = OfferCancel(account=sender_addr, offer_sequence=offer_seq, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# endregion


# region GET


def parse_offer_flags(offer_flag: int) -> list:
    flags = []
    for flag in OFFER_FLAGS:
        if flag["hex"] & offer_flag == flag["hex"]:
            flags.append(flag)
    return flags

async def account_offers(url: str, wallet_addr: str) -> list:
    """return all offers an account created"""
    offer_list = []
    req = AccountOffers(account=wallet_addr, ledger_index="validated")
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "offers" in result:
        offers = result["offers"]
        for offer in offers:
            of = {}
            of["flags"] = offer["flags"]
            of["sequence"] = offer["seq"]
            of["quality"] = offer["quality"]# str(drops_to_xrp(offer["quality"])) # rate is subject to error from the blockchain because xrp returned in this call has no decimal  # The exchange rate of the offer, as the ratio of the original taker_pays divided by the original taker_gets. rate = pay/get
            if isinstance(offer["taker_pays"], dict):
                of["buy_token"] = validate_hex_to_symbol(offer["taker_pays"]["currency"])
                of["buy_issuer"] = offer["taker_pays"]["issuer"]
                of["buy_amount"] = offer["taker_pays"]["value"]
            elif isinstance(offer["taker_pays"], str):
                of["buy_token"] = "XRP"
                of["buy_issuer"] = ""
                of["buy_amount"] = str(drops_to_xrp(offer["taker_pays"]))

            if isinstance(offer["taker_gets"], dict):
                of["sell_token"] = validate_hex_to_symbol(offer["taker_gets"]["currency"])
                of["sell_issuer"] = offer["taker_gets"]["issuer"]
                of["sell_amount"] = offer["taker_gets"]["value"]
            elif isinstance(offer["taker_gets"], str):
                of["sell_token"] = "XRP"
                of["sell_issuer"] = ""
                of["sell_amount"] = str(drops_to_xrp(offer["taker_gets"]))

            of["rate"] = float(of["sell_amount"])/float(of["buy_amount"])
            offer_list.append(of)
    return offer_list


async def account_order_book_liquidity(url: str, wallet_addr: str) -> list:
    """return all offers that are liquidity[with passive flag] an account created"""
    offer_list = []

    req = AccountOffers(account=wallet_addr, ledger_index="validated")
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "offers" in result:
        offers = result["offers"]
        for offer in offers:
            # returns all the offers with the passive flag, see passive for more info
            if 0x00010000 & offer["flags"] == 0x00010000:
                of = {}
                of["flags"] =  parse_offer_flags(offer["flags"])
                of["sequence"] = offer["seq"]
                of["quality"] = offer["quality"]# str(drops_to_xrp(offer["quality"])) # rate is subject to error from the blockchain because xrp returned in this call has no decimal  # The exchange rate of the offer, as the ratio of the original taker_pays divided by the original taker_gets. rate = pay/get
                if isinstance(offer["taker_pays"], dict):
                    of["buy_token"] = validate_hex_to_symbol(offer["taker_pays"]["currency"])
                    of["buy_issuer"] = offer["taker_pays"]["issuer"]
                    of["buy_amount"] = offer["taker_pays"]["value"]
                elif isinstance(offer["taker_pays"], str):
                    of["buy_token"] = "XRP"
                    of["buy_issuer"] = ""
                    of["buy_amount"] = str(drops_to_xrp(offer["taker_pays"]))
                if isinstance(offer["taker_gets"], dict):
                    of["sell_token"] = validate_hex_to_symbol(offer["taker_gets"]["currency"])
                    of["sell_issuer"] = offer["taker_gets"]["issuer"]
                    of["sell_amount"] = offer["taker_gets"]["value"]
                elif isinstance(offer["taker_gets"], str):
                    of["sell_token"] = "XRP"
                    of["sell_issuer"] = ""
                    of["sell_amount"] = str(drops_to_xrp(offer["taker_gets"]))
                of["rate"] = float(of["sell_amount"])/float(of["buy_amount"])
                offer_list.append(of)
    return offer_list


async def sort_best_offer(url: str, buy: Union[XRP, IssuedCurrency], sell: Union[XRP, IssuedCurrency], best_buy: bool = False, best_sell: bool = False) -> dict:
    """return all available orders and best {option} first, choose either best_buy or best_sell"""
    best = {}

    if best_sell:
        req = BookOffers(taker_gets=sell, taker_pays=buy, ledger_index="validated")
        response = await  AsyncJsonRpcClient(url).request(req)
        result = response.result
        if "offers" in result:
            offers: list = result["offers"]
            # sort offer list and return highest rate first
            offers.sort(key=lambda object: object["quality"], reverse=True)
            index = 0
            for offer in offers:
                of = {}
                of["creator"] = offer["Account"]
                of["offer_id"] = offer["index"]
                of["flags"] = parse_offer_flags(offer["Flags"])
                of["sequence"] = offer["Sequence"] # offer id
                of["rate"] = offer["quality"]
                of["creator_liquidity"] = ""
                if "owner_funds" in offer:
                    of["creator_liquidity"] = offer["owner_funds"] # available amount the offer creator of `sell_token` is currently holding
                if isinstance(offer["TakerPays"], dict):
                    of["buy_token"] = validate_hex_to_symbol(offer["TakerPays"]["currency"])
                    of["buy_issuer"] = offer["TakerPays"]["issuer"]
                    of["buy_amount"] = offer["TakerPays"]["value"]
                elif isinstance(offer["TakerPays"], str):
                    of["buy_token"] = "XRP"
                    of["buy_issuer"] = ""
                    of["buy_amount"] = str(drops_to_xrp(offer["TakerPays"]))

                if isinstance(offer["TakerGets"], dict):
                    of["sell_token"] = validate_hex_to_symbol(offer["TakerGets"]["currency"])
                    of["sell_issuer"] = offer["TakerGets"]["issuer"]
                    of["sell_amount"] = offer["TakerGets"]["value"]
                elif isinstance(offer["TakerGets"], str):
                    of["sell_token"] = "XRP"
                    of["sell_issuer"] = ""
                    of["sell_amount"] = str(drops_to_xrp(offer["TakerGets"]))                    
                index += 1
                best[index] = of

    if best_buy:
        req = BookOffers(taker_gets=sell, taker_pays=buy, ledger_index="validated")
        response = await AsyncJsonRpcClient(url).request(req)
        result = response.result
        if "offers" in result:
            offers: list = result["offers"]
            # sort offer list and return lowest rate first
            offers.sort(key=lambda object: object["quality"])
            index = 0
            for offer in offers:
                of = {}
                of["creator"] = offer["Account"]
                of["offer_id"] = offer["index"]
                of["flags"] = parse_offer_flags(offer["Flags"])
                of["sequence"] = offer["Sequence"] # offer id
                of["rate"] = offer["quality"]
                of["creator_liquidity"] = ""
                if "owner_funds" in offer:
                    of["creator_liquidity"] = offer["owner_funds"] # available amount the offer creator is currently holding
                if isinstance(offer["TakerPays"], dict):
                    of["buy_token"] = validate_hex_to_symbol(offer["TakerPays"]["currency"])
                    of["buy_issuer"] = offer["TakerPays"]["issuer"]
                    of["buy_amount"] = offer["TakerPays"]["value"]
                elif isinstance(offer["TakerPays"], str):
                    of["buy_token"] = "XRP"
                    of["buy_issuer"] = ""
                    of["buy_amount"] = str(drops_to_xrp(offer["TakerPays"]))

                if isinstance(offer["TakerGets"], dict):
                    of["sell_token"] = validate_hex_to_symbol(offer["TakerGets"]["currency"])
                    of["sell_issuer"] = offer["TakerGets"]["issuer"]
                    of["sell_amount"] = offer["TakerGets"]["value"]
                elif isinstance(offer["TakerGets"], str):
                    of["sell_token"] = "XRP"
                    of["sell_issuer"] = ""
                    of["sell_amount"] = str(drops_to_xrp(offer["TakerGets"]))                    
                index += 1
                best[index] = of
    return best


async def offer_info(url: str, offer_id: str = None, offer_creator: str = None, sequence: int = None) -> dict:
    """returns information about an offer
    Make use of only the offer_id param, else use both sequence and creator\n
    either cannot go together
    """
    offer_info = {}

    query = LedgerEntry(
        ledger_index="validated", offer=Offer(account=offer_creator, seq=sequence)
    )
    if offer_id != None:
        query = LedgerEntry(ledger_index="validated", offer=offer_id)
    response = await AsyncJsonRpcClient(url).request(query)
    result = response.result
    if "node" in result:
        offer_info["offer_id"] = result["index"]
        offer_info["creator"] = result["node"]["Account"]
        offer_info["sequence"] = result["node"]["Sequence"]
        offer_info["object_type"] = result["node"]["LedgerEntryType"]
        offer_info["expiry_date"] = (
            str(ripple_time_to_datetime(result["node"]["Expiration"]))
            if "Expiration" in result["node"]
            else ""
        )
        offer_info["flags"] = parse_offer_flags(result["node"]["Flags"])

        if isinstance(result["node"]["TakerPays"], dict):
            offer_info["buy_token"] = validate_hex_to_symbol(
                result["node"]["TakerPays"]["currency"]
            )
            offer_info["buy_issuer"] = result["node"]["TakerPays"]["issuer"]
            offer_info["buy_amount"] = result["node"]["TakerPays"]["value"]
        elif isinstance(result["node"]["TakerPays"], str):
            offer_info["buy_token"] = "XRP"
            offer_info["buy_issuer"] = ""
            offer_info["buy_amount"] = str(
                drops_to_xrp(result["node"]["TakerPays"])
            )

        if isinstance(result["node"]["TakerGets"], dict):
            offer_info["sell_token"] = validate_hex_to_symbol(
                result["node"]["TakerGets"]["currency"]
            )
            offer_info["sell_issuer"] = result["node"]["TakerGets"]["issuer"]
            offer_info["sell_amount"] = result["node"]["TakerGets"]["value"]
        elif isinstance(result["node"]["TakerGets"], str):
            offer_info["sell_token"] = "XRP"
            offer_info["sell_issuer"] = ""
            offer_info["sell_amount"] = str(
                drops_to_xrp(result["node"]["TakerGets"])
            )
    return offer_info

async def all_offers(url: str, pay: Union[XRP, IssuedCurrency], receive: Union[XRP, IssuedCurrency]) -> list:
    """returns all offers for 2 pairs"""
    all_offers_list = []
    req = BookOffers(taker_gets=pay, taker_pays=receive, ledger_index="validated")
    response =await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "offers" in result:
        offers = result["offers"]
        for offer in offers:
            of = {}
            of["creator"] = offer["Account"]
            of["offer_id"] = offer["index"]
            of["sequence"] = offer["Sequence"] # offer id
            of["rate"] = offer["quality"]
            of["flags"] = offer["Flags"]
            of["creator_liquidity"] = ""
            if "owner_funds" in offer and isinstance(offer["TakerGets"], str):
                of["creator_liquidity"] = f'{float(drops_to_xrp(offer["owner_funds"]))} XRP' # Amount of the TakerGets currency the side placing the offer has available to be traded.
            if "owner_funds" in offer and isinstance(offer["TakerGets"], dict):
                of["creator_liquidity"] = f'{offer["owner_funds"]}  {validate_hex_to_symbol(offer["TakerGets"]["currency"])}' # Amount of the TakerGets currency the side placing the offer has available to be traded.
            if isinstance(offer["TakerPays"], dict):
                of["buy_token"] = validate_hex_to_symbol(offer["TakerPays"]["currency"])
                of["buy_issuer"] = offer["TakerPays"]["issuer"]
                of["buy_amount"] = offer["TakerPays"]["value"]
            elif isinstance(offer["TakerPays"], str):
                of["buy_token"] = "XRP"
                of["buy_issuer"] = ""
                of["buy_amount"] = str(drops_to_xrp(offer["TakerPays"]))

            if isinstance(offer["TakerGets"], dict):
                of["sell_token"] = validate_hex_to_symbol(offer["TakerGets"]["currency"])
                of["sell_issuer"] = offer["TakerGets"]["issuer"]
                of["sell_amount"] = offer["TakerGets"]["value"]
            elif isinstance(offer["TakerGets"], str):
                of["sell_token"] = "XRP"
                of["sell_issuer"] = ""
                of["sell_amount"] = str(drops_to_xrp(offer["TakerGets"]))
            all_offers_list.append(of)
    return all_offers_list

# endregion
