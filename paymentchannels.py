from datetime import timedelta
from decimal import Decimal

from typing import Union

from xrpl.core.binarycodec import encode_for_signing_claim
from xrpl.core.keypairs import sign, is_valid_message 
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models import ( AccountObjects,
                       PaymentChannelCreate,
                         PaymentChannelFund, ChannelVerify, 
                         PaymentChannelClaim, PaymentChannelClaimFlag, )
from xrpl.utils import drops_to_xrp, ripple_time_to_datetime, xrp_to_drops, datetime_to_ripple_time

from misc import mm, validate_hex_to_symbol, validate_symbol_to_hex

from x_constants import M_SOURCE_TAG

# https://xrpl.org/docs/concepts/payment-types/payment-channels



# ## region POST

# settle delay max = 2**32-1 time in seconds, Amount of time the source address must wait before closing the channel if it has unclaimed XRP. can be 0 - 4294967295 seconds[136.193 years]
# TODO: i'll have convert the settle delay to seconds independent of ripple time stuff
def create_xrp_payment_channel(sender_addr: str, public_key: str, amount: Union[int, float, Decimal], receiver: str, settle_delay: int, immutable_expiry_date: int = None, destination_tag: int = None, fee: str = None) :
    txn = PaymentChannelCreate(account=sender_addr, amount=xrp_to_drops(amount), destination=receiver, settle_delay=settle_delay, public_key=public_key, cancel_after=immutable_expiry_date, destination_tag=destination_tag, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# https://xrpl.org/docs/references/protocol/transactions/types/paymentchannelclaim#paymentchannelclaim-fields
# Signature can be none if the function caller if the payment channel creator. To Send XRP from the channel to the destination with or without a signed Claim.
def claim_xrp_payment_channel_funds(sender_addr: str, public_key: str, channel_id: str, amount: Union[int, float, Decimal], signature: str = None, fee: str = None) -> dict:
    txn = PaymentChannelClaim(account=sender_addr, channel=channel_id, signature=signature, amount=xrp_to_drops(amount), balance=xrp_to_drops(amount), public_key=public_key, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# only the payment channel sender can call this - https://xrpl.org/docs/references/protocol/transactions/types/paymentchannelfund/
#  Can set new Expiration time to set for the channel, in seconds since the Ripple Epoch. This must be later than either the current time plus the SettleDelay of the channel, or the existing Expiration of the channel.
def update_xrp_payment_channel(sender_addr: str, channel_id: str, amount: Union[int, float, Decimal], expiry_date: int = None, fee: str = None) -> dict:
    txn = PaymentChannelFund(account=sender_addr, channel=channel_id, amount=xrp_to_drops(amount), expiration=expiry_date, source_tag=M_SOURCE_TAG, memos=mm(), fee=fee)
    return txn.to_xrpl()

def renew_payment_channel(sender_addr: str, channel_id: str, fee: str = None) -> dict:
    """Clear the channel's Expiration time, different from the immutable cancel after time"""
    txn = PaymentChannelClaim(account=sender_addr, channel=channel_id, flags=PaymentChannelClaimFlag.TF_RENEW, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def close_payment_channel(sender_addr: str, channel_id: str, fee: str = None) -> dict:
    txn = PaymentChannelClaim(account=sender_addr, channel=channel_id, flags=PaymentChannelClaimFlag.TF_CLOSE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# TODO: modify to match wallet signing requirements
# requires private key
def offline_generate_xrp_payment_channel_signature(channel_id: str, amount: Union[int, Decimal, float], private_key: str) -> str:
    data = encode_for_signing_claim({"channel": channel_id, "amount": xrp_to_drops(amount)})
    return sign(data, private_key)

def offline_verify_xrp_payment_channel_signature(channel_id: str, amount: Union[int, float, Decimal], public_key: str, signature: str) -> bool:
    """check the validity of a signature that can be used to redeem a specific amount of XRP from a payment channel."""
    value = False
    data = encode_for_signing_claim({"channel": channel_id, "amount": xrp_to_drops(amount)})
    value = is_valid_message(data, signature, public_key)
    return value


# endregion 



### region GET

async def online_verify_xrp_payment_channel_signature(url: str, channel_id: str, amount: Union[int, float, Decimal], public_key: str, signature: str) -> bool:
    """check the validity of a signature that can be used to redeem a specific amount of XRP from a payment channel."""
    value = False
    req = ChannelVerify(channel_id=channel_id, amount=xrp_to_drops(amount), public_key=public_key, signature=signature)
    response =  await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "signature_verified" in result:
        value = result["signature_verified"]
    return value   

async def account_xrp_payment_channels(url: str, wallet_addr: str) -> list:
    """return a list of the payment channels created by an account"""
    paymentchannels_ = []
    req = AccountObjects(account=wallet_addr,  type="payment_channel")
    response =  await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "account_objects" in result:
        account_paymentchannels = result["account_objects"]
        for paymentchannel in account_paymentchannels:
            paymentchannel_data = {}
            #  condition to check if the amount is xrp
            if isinstance(paymentchannel["Amount"], str):
                paymentchannel_data["channel_id"] = paymentchannel["index"]
                paymentchannel_data["sender"] = paymentchannel["Account"]
                paymentchannel_data["amount_deposited"] = str(drops_to_xrp(paymentchannel["Amount"]))
                paymentchannel_data["amount_paid_out"] = str(drops_to_xrp(paymentchannel["Balance"]))
                paymentchannel_data["amount_remaining"] = str(drops_to_xrp(str(int(paymentchannel["Amount"]) - int(paymentchannel["Balance"]))))
                paymentchannel_data["receiver"] = paymentchannel["Destination"]
                paymentchannel_data["settle_delay"] = str(timedelta(seconds=(paymentchannel["SettleDelay"])))
                paymentchannel_data["public_key"] = paymentchannel["PublicKey"]
                paymentchannel_data["immutable_expiry_date"] = str(ripple_time_to_datetime(paymentchannel["CancelAfter"])) if "CancelAfter" in paymentchannel else ''
                paymentchannel_data["expiry_date"] = str(ripple_time_to_datetime(paymentchannel["Expiration"])) if "Expiration" in paymentchannel else ''
                paymentchannel_data["destination_tag"] = paymentchannel["DestinationTag"] if "DestinationTag" in paymentchannel else ''
                paymentchannels_.append(paymentchannel_data)
    return paymentchannels_

#TODO: complete me
async def xrp_payment_channel_info(url:str, channel_id: str) -> dict:
    pass


# endregion

# from xrpl.wallet import Wallet
# from xrpl.clients import JsonRpcClient
# from xrpl.models import Transaction

# from xrpl.transaction.main  import  sign_and_submit
# from datetime import datetime

# # C:\Users\oamba\Desktop\XRPLv3\venv\Lib\site-packages\xrpl\asyncio\transaction\main.py

# acc1_addr = "rpmsgLmYHky4Qw7fGu4jLr4Xu1dS5Q849n"
# acc1 = Wallet.from_seed(seed="sEdTrmLZpWyUeUnFwq7bze2yFUxJByh")

# # print(acc1)

# url = "https://s.altnet.rippletest.net:51234"
# client = JsonRpcClient(url)

# x = create_xrp_payment_channel(acc1.classic_address, acc1.public_key, 10, "rNSrjYiN1Lorv7nzJnna5jkh91ZqcA8KsG", 100, datetime_to_ripple_time(datetime.now() + timedelta(days=10)), 100101)



# print(sign_and_submit(Transaction.from_xrpl({'Account': 'rpmsgLmYHky4Qw7fGu4jLr4Xu1dS5Q849n', 'TransactionType': 'EscrowCreate', 'Flags': 0, 'Memos': [{'Memo': {'MemoData': '68747470733a2f2f6d79726b6c652e617070', 'MemoFormat': 'text/plain', 'MemoType': '446f6e652d776974682d4d79726b6c65'}}], 'SourceTag': 10011001, 'SigningPubKey': '', 'Amount': '10000000', 'Destination': 'rBoSibkbwaAUEpkehYixQrXp4AqZez9WqA'}),client=client, wallet= acc1 ))