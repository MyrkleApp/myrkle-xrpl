# Myrkle-XRPL

Myrkle is a Web3 super app that simplifies access to the XRP Ledger's native features. It allows users to create and manage objects, view detailed token and NFT data, create and exchange digital assets, and manage escrow transactions and do much more with zero stress.

The code contained in this repo interacts with the XRP Ledger on behalf of Myrkle

## Features - Include but not limited to
- **Wallet Management** – Easily create, import, and manage XRPL wallets.
- **Token & NFT Insights** – View detailed information on assets.
- **Digital Asset Creation** – Issue tokens and mint NFTs effortlessly.
- **Instant Exchange** – Swap tokens and NFTs with minimal friction.
- **Escrow & Checks** – Create and manage escrows and checks seamlessly.
- **DID** – Create and manage your account DID seamlessly.
- **MPTs** – Create and manage multi-purpose tokens.

## Installation

To set up Myrkle-XRPL locally, follow these steps:

### Prerequisites
- Install [Python 3.8+](https://www.python.org/)

- Ensure you have `pip` installed

### Steps
```sh
# Clone the repository
git clone https://github.com/MyrkleApp/myrkle-xrpl.git
cd myrkle-xrpl

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the files
1. Create a file of your choice e.g `checks_test.py` to test the checks package

2. Add the code below to the file
```py

# neccesary imports
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

```

3. Run the code
```sh
python checks_test.py
```

4. The expected output is transaction object reponse in form of a dict


## Contributing
We welcome contributions! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to your fork (`git push origin feature-branch`).
5. Open a Pull Request.


## Contact
For questions, reach out via:
- X: [@MyrkleApp](https://x.com/MyrkleApp)
- website: [xrpl.myrkle.app](https://xrpl.myrkle.app)

