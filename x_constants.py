XURLS_ = {
    "TESTNET_URL": "https://s.altnet.rippletest.net:51234",
    "MAINNET_URL": "https://xrplcluster.com",
    "TESTNET_TXNS": "https://testnet.xrpl.org/transactions/",
    "MAINNET_TXNS": "https://livenet.xrpl.org/transactions/",
    "MAINNET_ACCOUNT": "https://livenet.xrpl.org/accounts/",
    "TESTNET_ACCOUNT": "https://testnet.xrpl.org/accounts/",
}



"""
xrp max decimals is 6
0.000001
"""
M_SOURCE_TAG = 10011001
D_TYPE = "Done-with-Myrkle"
D_DATA = "https://myrkle.app"

ACCOUNT_ROOT_FLAGS = [
    # TODO: add nftoken minter and clawback 
    {
        "flagname": "lsfDefaultRipple",
        "hex": 0x00800000,
        "decimal": 8388608,
        "asf": "asfDefaultRipple",
        "description": "Enable rippling on this addresses's trust lines by default. Required for issuing addresses; discouraged for others."
    },
    {
        "flagname": "lsfDepositAuth",
        "hex": 0x01000000,
        "decimal": 16777216,
        "asf": "asfDepositAuth",
        "description": "This account can only receive funds from transactions it sends, and from preauthorized accounts, It has DepositAuth enabled."
    },
    {
        "flagname": "lsfDisableMaster",
        "hex": 0x00100000,
        "decimal": 1048576,
        "asf": "asfDisableMaster",
        "description": "Disallows use of the master key to sign transactions for this account."
    },
    {
        "flagname": "lsfDisallowIncomingCheck",
        "hex": 0x08000000,
        "decimal": 134217728,
        "asf": "asfDisallowIncomingCheck",
        "description": ""
    },
    {
        "flagname": "lsfDisallowIncomingNFTokenOffer",
        "hex": 0x04000000,
        "decimal": 134217728,
        "asf": "asfDisallowIncomingNFTokenOffer",
        "description": ""
    },
    {
        "flagname": "lsfDisallowIncomingPayChan",
        "hex": 0x10000000,
        "decimal": 268435456,
        "asf": "asfDisallowIncomingPayChan",
        "description": ""
    },
    {
        "flagname": "lsfDisallowIncomingTrustline",
        "hex": 0x20000000,
        "decimal": 536870912,
        "asf": "asfDisallowIncomingTrustline",
        "description": ""
    },
    {
        "flagname": "lsfDisallowXRP",
        "hex": 0x00080000,
        "decimal": 524288,
        "asf": "asfDisallowXRP",
        "description": "Client applications should not send XRP to this account. Not enforced by rippled."
    },
    {
        "flagname": "lsfGlobalFreeze",
        "hex": 0x00400000,
        "decimal": 4194304,
        "asf": "asfGlobalFreeze",
        "description": "Freeze all assets issued by this account"
    },    
    {
        "flagname": "lsfNoFreeze",
        "hex": 0x00200000,
        "decimal": 2097152,
        "asf": "asfNoFreeze",
        "description": "This address cannot freeze trust lines connected to it. Once enabled, cannot be disabled."
    },
    {
        "flagname": "lsfPasswordSpent",
        "hex": 0x00010000,
        "decimal": 65536,
        "asf": "",
        "description": "The account has used its free SetRegularKey transaction."
    },
    {
        "flagname": "lsfRequireAuth",
        "hex": 0x00040000,
        "decimal": 262144,
        "asf": "asfRequireAuth",
        "description": "This account must individually approve other users for those users to hold this account's tokens."
    },
    {
        "flagname": "lsfRequireDestTag",
        "hex": 0x00020000,
        "decimal": 131072,
        "asf": "asfRequireDest",
        "description": "Requires incoming payments to specify a Destination Tag."
    }, 
    # {
    #     "flagname": "lsfAMM",
    #     "hex": 0x02000000,
    #     "decimal": 33554432,
    #     "asf": "",
    #     "description": "This account is an Automated Market Maker instance.",
    # },  
]

NFTOKEN_FLAGS = [
    {
        "flagname": "tfBurnable",
        "hex": 0x00000001,
        "decimal": 1,
        "description": "Allow the issuer (or an entity authorized by the issuer) to destroy the minted NFToken. (The NFToken's owner can always do so.)",
    },
    {
        "flagname": "tfOnlyXRP",
        "hex": 0x00000002,
        "decimal": 2,
        "description": "The minted NFToken can only be bought or sold for XRP. This can be desirable if the token has a transfer fee and the issuer does not want to receive fees in non-XRP currencies.",
    },
    {
        "flagname": "tfTransferable",
        "hex": 0x00000008,
        "decimal": 8,
        "description": "The minted NFToken can be transferred to others. If this flag is not enabled, the token can still be transferred from or to the issuer.",
    },
]

NFTOKEN_OFFER_FLAGS = [
    {
        "flagname": "tfSellNFToken",
        "hex": 0x00000001,
        "decimal": 1,
        "description": "If enabled, the offer is a sell offer. Otherwise, the offer is a buy offer.",
    },
]

OFFER_FLAGS = [
    {
        "flagname": "tfPassive",
        "hex": 0x00010000,
        "decimal": 65536,
        "description": "If enabled, the Offer does not consume Offers that exactly match it, and instead becomes an Offer object in the ledger. It still consumes Offers that cross it.",
    },
    {
        "flagname": "tfImmediateOrCancel",
        "hex": 0x00020000,
        "decimal": 131072,
        "description": "Treat the Offer as an Immediate or Cancel order . The Offer never creates an Offer object in the ledger: it only trades as much as it can by consuming existing Offers at the time the transaction is processed. If no Offers match, it executes 'successfully' without trading anything. In this case, the transaction still uses the result code tesSUCCESS.",
    },
    {
        "flagname": "tfFillOrKill",
        "hex": 0x00040000,
        "decimal": 131072,
        "description": "Treat the offer as a Fill or Kill order . The Offer never creates an Offer object in the ledger, and is canceled if it cannot be fully filled at the time of execution. By default, this means that the owner must receive the full TakerPays amount; if the tfSell flag is enabled, the owner must be able to spend the entire TakerGets amount instead.",
    },
    {
        "flagname": "tfSell",
        "hex": 0x00080000,
        "decimal": 524288,
        "description": "Exchange the entire TakerGets amount, even if it means obtaining more than the TakerPays amount in exchange.",
    },
]

PAYMENT_FLAGS = [
    {
        "flagname": "tfNoDirectRipple",
        "hex": 0x00010000,
        "decimal": 65536,
        "description": "Do not use the default path; only use paths included in the Paths field. This is intended to force the transaction to take arbitrage opportunities. Most clients do not need this.",
    },
    {
        "flagname": "tfPartialPayment",
        "hex": 0x00020000,
        "decimal": 131072,
        "description": "The partial payment flag allows a payment to succeed by reducing the amount received.",
    },
    {
        "flagname": "tfLimitQuality",
        "hex": 0x00040000,
        "decimal": 262144,
        "description": "The Limit quality flag allows you to set a minimum quality of conversions that you are willing to take.",
    },
]
