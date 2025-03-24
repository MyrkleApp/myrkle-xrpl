from pydoc import cli
from xrpl.models import (
    AccountInfo,
    AccountSet,
    IssuedCurrencyAmount,
    AccountLines,
    Payment,
    TrustSet,
    AccountSetAsfFlag,
    TrustSetFlag,
    GatewayBalances,
    Transaction,
    Clawback,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient
from misc import (
    mm,
    is_hex,
    transfer_fee_to_xrp_format,
    validate_symbol_to_hex,
    xrp_format_to_transfer_fee,
    validate_hex_to_symbol,
)
from x_constants import M_SOURCE_TAG

# region POST
"""4 step process to creating a token; must use 2 new accounts"""


# 1
def accountset_issuer(
    issuer_addr: str, ticksize: int, transferfee: float, domain: str, fee: str = None
) -> dict:
    txn = AccountSet(
        account=issuer_addr,
        set_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE,
        tick_size=ticksize,
        transfer_rate=transfer_fee_to_xrp_format(transferfee),
        domain=validate_symbol_to_hex(domain),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# 2
def accountset_manager(manager_addr: str, domain: str, fee: str = None) -> dict:
    txn = AccountSet(
        account=manager_addr,
        set_flag=AccountSetAsfFlag.ASF_REQUIRE_AUTH,
        domain=validate_symbol_to_hex(domain),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# 3
def create_trustline(
    manager_addr: str,
    issuer_addr: str,
    token_name: str,
    total_supply: str,
    fee: str = None,
) -> dict:
    txn = TrustSet(
        account=manager_addr,
        limit_amount=IssuedCurrencyAmount(
            currency=validate_symbol_to_hex(token_name),
            issuer=issuer_addr,
            value=total_supply,
        ),
        source_tag=M_SOURCE_TAG,
        # flags=TrustSetFlag.TF_SET_NO_RIPPLE,
        fee=fee,
        memos=mm(),
    )
    return txn.to_xrpl()


# 4
def create_token(
    issuer_addr: str,
    manager_addr: str,
    token_name: str,
    total_supply: str,
    fee: str = None,
) -> dict:
    txn = Payment(
        account=issuer_addr,
        destination=manager_addr,
        amount=IssuedCurrencyAmount(
            currency=validate_symbol_to_hex(token_name),
            issuer=issuer_addr,
            value=total_supply,
        ),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def burn_token(
    sender_addr: str, token: str, issuer: str, amount: float, fee: str = None
) -> dict:
    """burn a token"""
    txn = Payment(
        account=sender_addr,
        destination=issuer,
        amount=IssuedCurrencyAmount(
            currency=validate_symbol_to_hex(token), issuer=issuer, value=amount
        ),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def add_token(
    sender_addr: str,
    token: str,
    issuer: str,
    rippling: bool = False,
    is_lp_token: bool = False,
    fee: str = None,
) -> dict:
    """enable transacting with a token"""
    flag = TrustSetFlag.TF_SET_NO_RIPPLE
    cur = token if is_lp_token else validate_symbol_to_hex(token)
    if rippling:
        flag = TrustSetFlag.TF_CLEAR_NO_RIPPLE
    cur = IssuedCurrencyAmount(currency=cur, issuer=issuer, value=1_000_000_000)
    txn = TrustSet(
        account=sender_addr,
        limit_amount=cur,
        flags=flag,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# can only be called if user empties balance
def remove_token(sender_addr: str, token: str, issuer: str, fee: str = None) -> dict:
    """disable transacting with a token"""
    trustset_cur = IssuedCurrencyAmount(
        currency=validate_symbol_to_hex(token), issuer=issuer, value=0
    )
    txn = TrustSet(
        account=sender_addr,
        limit_amount=trustset_cur,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def modify_token_freeze_state(
    sender_addr: str,
    target_addr: str,
    token_name: str,
    freeze: bool = False,
    fee: str = None,
) -> dict:
    """Freeze a token for an account, only the issuer can call this"""
    state = TrustSetFlag.TF_CLEAR_FREEZE
    if freeze:
        state = TrustSetFlag.TF_SET_FREEZE
    cur = IssuedCurrencyAmount(
        currency=validate_symbol_to_hex(token_name),
        issuer=target_addr,
        value=1_000_000_000,
    )
    txn = TrustSet(
        account=sender_addr,
        limit_amount=cur,
        flags=state,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# only the issuer can call this
def token_clawback(
    sender_addr: str, token: str, amount: str, target_addr: str, fee: str = None
):
    """clawback a token from an account"""
    txn = Clawback(
        account=sender_addr,
        amount=IssuedCurrencyAmount(
            currency=validate_symbol_to_hex(token),
            issuer=target_addr,
            value=amount,
        ),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# endregion


# region GET


async def get_token_info(url: str, issuer: str) -> dict:
    token_info = {}
    query = AccountInfo(account=issuer, ledger_index="validated")
    response = await AsyncJsonRpcClient(url).request(query)
    result = response.result
    if "account_data" in result:
        account_data = result["account_data"]
        token_info["index"] = account_data["index"]
        token_info["issuer"] = account_data["Account"]
        token_info["tick_size"] = (
            account_data["TickSize"] if "TickSize" in account_data else 0
        )
        token_info["domain"] = (
            validate_hex_to_symbol(account_data["Domain"])
            if "Domain" in account_data
            else ""
        )
        token_info["email"] = (
            validate_hex_to_symbol(account_data["EmailHash"])
            if "EmailHash" in account_data
            else ""
        )
        token_info["transfer_fee"] = (
            xrp_format_to_transfer_fee(account_data["TransferRate"])
            if "TransferRate" in account_data
            else 0
        )
    return token_info


# using gateway balance is compulsory, no choice - although some node may not accept the request
async def created_tokens_issuer(url: str, wallet_addr: str) -> list:
    """returns all tokens an account has created as the issuer"""
    created_assets = []
    req = GatewayBalances(account=wallet_addr, ledger_index="validated")
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "obligations" in result:
        obligations = result["obligations"]
        for key, value in obligations.items():
            asset = {}
            asset["token"] = validate_hex_to_symbol(key)
            asset["amount"] = value
            asset["issuer"] = wallet_addr
            asset["domain"] = ""
            acc_info = AccountInfo(account=wallet_addr, ledger_index="validated")
            account_data = await AsyncJsonRpcClient(url).request(acc_info)
            account_data = account_data.result["account_data"]
            if "Domain" in account_data:
                asset["domain"] = validate_hex_to_symbol(account_data["Domain"])
            created_assets.append(asset)
    return created_assets


async def created_tokens_manager(url: str, wallet_addr: str) -> list:
    """returns all tokens an account thas created as the manager"""
    created_assets = []
    req = GatewayBalances(account=wallet_addr, ledger_index="validated")
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "assets" in result:
        assets = result["assets"]
        for issuer, issuings in assets.items():
            for iss_cur in issuings:
                asset = {}
                asset["issuer"] = issuer
                asset["token"] = validate_hex_to_symbol(iss_cur["currency"])
                asset["amount"] = iss_cur["value"]
                asset["manager"] = wallet_addr
                asset["domain"] = ""
                acc_info = AccountInfo(
                    account=asset["cold_address"], ledger_index="validated"
                )
                account_data = await AsyncJsonRpcClient(url).request(acc_info)
                account_data = account_data.result["account_data"]
                if "Domain" in account_data:
                    asset["domain"] = validate_hex_to_symbol(account_data["Domain"])
                created_assets.append(asset)
    return created_assets


async def account_tokens(url: str, wallet_addr: str) -> list:
    """returns all tokens except LP tokens a wallet address is holding with their respective issuers, limit and balances"""
    assets = []
    acc_info = AccountLines(account=wallet_addr, ledger_index="validated")
    response = await AsyncJsonRpcClient(url).request(acc_info)
    result = response.result
    if "lines" in result:
        lines = result["lines"]
        for line in lines:
            if isinstance(is_hex(line["currency"]), Exception):
                pass
            else:
                asset = {}
                # filter lp tokens
                asset["token"] = validate_hex_to_symbol(line["currency"])
                asset["issuer"] = line["account"]
                asset["amount"] = line["balance"]
                asset["limit"] = line["limit"]  # the max an account can handle
                asset["freeze_status"] = False
                asset["ripple_status"] = False
                if "no_ripple" in line:
                    asset["ripple_status"] = line[
                        "no_ripple"
                    ]  # no ripple = true, means rippling is disabled which is good; else bad
                if "freeze" in line:
                    asset["freeze_status"] = line["freeze"]
                """Query for domain and transfer rate with info.get_token_info()"""
                assets.append(asset)
    return assets


# endregion


from xrpl.clients import JsonRpcClient
from xrpl.transaction import submit_and_wait, sign_and_submit

client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")

from xrpl.wallet import Wallet, generate_faucet_wallet

m = Wallet.from_seed(seed="sEdTYgXS4mDuZq1DD5iiQgq11TQCjAz")

for i in range(100):
    w = generate_faucet_wallet(client=client)
    sign_and_submit(
        transaction=Transaction.from_xrpl(add_token(m.address, "USD", w.address)),
        client=client,
        wallet=m,
    )
    print(f"done {i}")
