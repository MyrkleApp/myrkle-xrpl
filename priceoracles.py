import datetime
from decimal import Decimal

from xrpl.asyncio.clients import AsyncJsonRpcClient

from xrpl.models import (
    OracleSet,
    AccountObjectType,
    AccountObjects,
    OracleDelete,
    LedgerEntry,
)
from xrpl.models.requests.ledger_entry import Oracle
from xrpl.models.transactions.oracle_set import PriceData


from misc import (
    mm,
    validate_hex_to_symbol,
    validate_symbol_to_hex,
    scale_from_value,
)

from x_constants import M_SOURCE_TAG


# https://xrpl.org/docs/concepts/decentralized-storage/price-oracles


# region POST


def create_price_data(
    base_asset: str,
    quote_asset: str,
    asset_price: str = None,
) -> PriceData:
    """Create price data object for handling oracle transactions
    Args:
        asset_price (str): base asset price in relation to the quote asset e.g: 1 BTC = 1000 USD
    """
    scale = None
    scaled_asset_price = None

    # check if the asset price is a string
    if isinstance(asset_price, str):
        # get scale from the asset price, scale should be between 0-10
        scale = scale_from_value(asset_price)
        scaled_asset_price = int(Decimal(asset_price) * 10**scale)

    return PriceData(
        base_asset=validate_symbol_to_hex(base_asset),
        quote_asset=validate_symbol_to_hex(quote_asset),
        asset_price=scaled_asset_price,
        scale=scale,
    )


def create_price_oracle(
    sender_addr: str,
    oracle_document_id: int,
    provider: str,
    uri: str,
    last_update_time: int,
    asset_class: str,
    price_data_series: list[PriceData],  # max 10
    fee: str = None,
) -> dict:
    """Create a price oracle object"""
    txn = OracleSet(
        account=sender_addr,
        oracle_document_id=oracle_document_id,
        provider=validate_symbol_to_hex(provider),
        uri=validate_symbol_to_hex(uri),
        # max time into the future is 5 minutes max into the past is 4
        # uses normal date time to timestamp not ripple time
        # update_time = int((datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp())
        last_update_time=last_update_time,
        asset_class=validate_symbol_to_hex(
            asset_class
        ),  # maxlength in hex to string 16
        price_data_series=price_data_series,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def delete_price_oracle(
    sender_addr: str,
    oracle_document_id: int,
    fee: str = None,
) -> dict:
    """Delete a price oracle object"""
    txn = OracleDelete(
        account=sender_addr,
        oracle_document_id=oracle_document_id,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# add token pair
def update_token_pair(
    sender_addr: str,
    oracle_doc_id: int,
    last_update_time: int,
    price_data: list[PriceData],
    fee: str = None,
) -> dict:
    """Add / update an existing token pair to an existing oracle, must pass in all the previous token pairs too"""

    txn = OracleSet(
        account=sender_addr,
        oracle_document_id=oracle_doc_id,
        price_data_series=price_data,
        last_update_time=last_update_time,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# remove token pair: remove asset price field
# TODO: may have to update, because to delete requires to remove the asset price field, and removing it causes an error
def delete_token_pair(
    sender_addr: str,
    oracle_doc_id: int,
    base_asset: str,
    quote_asset: str,
    last_update_time: int,
    previous_price_data: list[PriceData],
    fee: str = None,
) -> dict:
    """Delete a token pair from an existing oracle, must pass in all the previous token pairs too"""
    price_data = create_price_data(base_asset, quote_asset)
    txn = OracleSet(
        account=sender_addr,
        oracle_document_id=oracle_doc_id,
        price_data_series=[price_data, *previous_price_data],
        last_update_time=last_update_time,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/path-and-order-book-methods/get_aggregate_price
# TODO: price_oracle_aggregate -  seems unnecessary

# endregion


# region GET


async def account_price_oracles(url: str, wallet_addr: str) -> list:
    oracles_ = []
    req = AccountObjects(
        account=wallet_addr,
        ledger_index="validated",
        type=AccountObjectType.ORACLE,
    )
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "account_objects" in result:
        oracles = result["account_objects"]
        for oracle in oracles:
            oracle_data = {}
            price_data_ = []
            oracle_data["oracle_id"] = oracle["index"]
            oracle_data["owner"] = oracle["Owner"]
            oracle_data["provider"] = validate_hex_to_symbol(oracle["Provider"])
            oracle_data["asset_class"] = validate_hex_to_symbol(oracle["AssetClass"])
            oracle_data["uri"] = (
                validate_hex_to_symbol(oracle["URI"]) if "URI" in oracle else ""
            )
            oracle_data["last_update_time"] = (
                str(datetime.datetime.fromtimestamp(oracle["LastUpdateTime"]))
                if "LastUpdateTime" in oracle
                else ""
            )
            oracle_data["price_data_series"] = (
                oracle["PriceDataSeries"] if "PriceDataSeries" in oracle else []
            )
            # sort price data series if any
            if "PriceDataSeries" in oracle and len(oracle["PriceDataSeries"]) > 0:
                price_data_series = oracle["PriceDataSeries"]
                for price_data_serie in price_data_series:
                    # print(
                    #     validate_hex_to_symbol(
                    #         price_data_serie["PriceData"]["BaseAsset"]
                    #     )
                    # )
                    price_data = {}
                    price_data["base_asset"] = validate_hex_to_symbol(
                        price_data_serie["PriceData"]["BaseAsset"]
                    )
                    price_data["quote_asset"] = validate_hex_to_symbol(
                        price_data_serie["PriceData"]["QuoteAsset"]
                    )
                    price_data["scale"] = (
                        price_data_serie["PriceData"]["Scale"]
                        if "Scale" in price_data_serie["PriceData"]
                        else ""
                    )
                    price_data["scaled_asset_price"] = (
                        int(price_data_serie["PriceData"]["AssetPrice"], 16)
                        if "AssetPrice" in price_data_serie["PriceData"]
                        else ""
                    )

                    # one base asset = this amount of quote asset
                    price_data["asset_price"] = (
                        (
                            int(price_data_serie["PriceData"]["AssetPrice"], 16)
                            / 10 ** price_data_serie["PriceData"]["Scale"]
                        )
                        if "AssetPrice" in price_data_serie["PriceData"]
                        and "Scale" in price_data_serie["PriceData"]
                        else ""
                    )
                    price_data_.append(price_data)
                oracle_data["price_data_series"] = price_data_
            oracles_.append(oracle_data)
    return oracles_


#  VERY UNNECESSARY
async def price_oracle_info(url: str, oracle_creator: str, oracle_id: str) -> dict:
    """returns information about a check"""
    oracle_info = {}
    req = LedgerEntry(
        ledger_index="validated",
        oracle=Oracle(account=oracle_creator, oracle_document_id=oracle_id),
    )
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "node" in result and "Owner" in result["node"]:
        oracle_info["oracle_id"] = result["node"]["index"]
        oracle_info["owner"] = result["node"]["Owner"]
        oracle_info["provider"] = validate_hex_to_symbol(result["node"]["Provider"])
        oracle_info["asset_class"] = validate_hex_to_symbol(
            result["node"]["AssetClass"]
        )
        oracle_info["uri"] = (
            validate_hex_to_symbol(result["node"]["URI"])
            if "URI" in result["node"]
            else ""
        )
        oracle_info["last_update_time"] = (
            str(datetime.datetime.fromtimestamp(result["node"]["LastUpdateTime"]))
            if "LastUpdateTime" in result["node"]
            else ""
        )

        oracle_info["object_type"] = result["node"]["LedgerEntryType"]
        oracle_info["price_data_series"] = (
            result["node"]["PriceDataSeries"]
            if "PriceDataSeries" in result["node"]
            else []
        )
        # sort price data series if any
        if (
            "PriceDataSeries" in result["node"]
            and len(result["node"]["PriceDataSeries"]) > 0
        ):
            price_data_series = result["node"]["PriceDataSeries"]
            price_data_ = []
            for price_data_serie in price_data_series:
                price_data = {}
                price_data["base_asset"] = validate_hex_to_symbol(
                    price_data_serie["PriceData"]["BaseAsset"]
                )
                price_data["quote_asset"] = validate_hex_to_symbol(
                    price_data_serie["PriceData"]["QuoteAsset"]
                )
                price_data["scale"] = (
                    price_data_serie["PriceData"]["Scale"]
                    if "Scale" in price_data_serie["PriceData"]
                    else ""
                )
                price_data["scaled_asset_price"] = (
                    int(price_data_serie["PriceData"]["AssetPrice"], 16)
                    if "AssetPrice" in price_data_serie["PriceData"]
                    else ""
                )

                # one base asset = this amount of quote asset
                price_data["asset_price"] = (
                    (
                        int(price_data_serie["PriceData"]["AssetPrice"], 16)
                        / 10 ** price_data_serie["PriceData"]["Scale"]
                    )
                    if "AssetPrice" in price_data_serie["PriceData"]
                    and "Scale" in price_data_serie["PriceData"]
                    else ""
                )
                price_data_.append(price_data)
            oracle_info["price_data_series"] = price_data_
    return oracle_info


# endregion
