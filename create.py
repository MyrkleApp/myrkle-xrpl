
# neccesar imports
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models import Transaction
from xrpl.utils import xrp_to_drops, datetime_to_ripple_time, str_to_hex
from xrpl.transaction import sign_and_submit
from datetime import datetime, timedelta
from checks import create_xrp_check


# define client
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

# check creator
check_creator = Wallet.from_seed("sEd78tf6uyrTztP8KwWoL6V7uVQTNCz")

# check receiver
check_receiver = "ry3frFHsRG4m9J4Qo8v6B3u1CGuHDsrwW"

# build check create transaction
check_create = create_xrp_check(
    sender_addr=check_creator.address,
    receiver_addr=check_receiver,
    amount=10,
    # optional
    invoice_id=str_to_hex("CREATE CHECK WITH INVOICE ID: 01"),
    expiry_date=datetime_to_ripple_time(datetime.now() + timedelta(days=1)),
)

# sign and submit
response = sign_and_submit(
    transaction=Transaction.from_xrpl(check_create),
    wallet=check_creator,
    client=client,
)

# print result
print(response.result)
