# Binance Futures Testnet CLI

This is a small Python command-line app for placing **BUY** and **SELL** orders on the **Binance Futures Testnet**.

It supports:
- `MARKET` orders
- `LIMIT` orders
- `BUY` and `SELL`
- simple input prompts if you do not pass flags
- logging to `orders.log`

## What You Need

- Python 3.11 or newer
- a Binance Futures Testnet API key and secret
- an internet connection

## Setup

1. Put your testnet credentials in `.env`:

```dotenv
BINANCE_TESTNET_API_KEY=your_api_key_here
BINANCE_TESTNET_API_SECRET=your_api_secret_here
```

2. Make sure you are using Futures Testnet keys, not mainnet keys.

3. Install dependencies if needed:

```bash
uv sync
```

## Run It

### Place a market order

```bash
python3 main.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

### Place a limit order

```bash
python3 main.py --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 70000
python3 main.py --symbol BTCUSDT --list-orders```

### Check an existing order later

If you already placed an order and want to see its updated status later, run:

```bash
python3 main.py --symbol BTCUSDT --order-id 13687700938
```

### List all existing orders for a symbol

```bash
python3 main.py --symbol BTCUSDT --list-orders
```

## Flags

- `--symbol`: trading pair, for example `BTCUSDT`
- `--side`: `BUY` or `SELL`
- `--type`: `MARKET` or `LIMIT`
- `--qty`: order quantity
- `--price`: required for `LIMIT` orders
- `--wait-seconds`: how long to wait after placing the order before showing the final status
- `--order-id`: check the status of an existing order instead of placing a new one
- `--list-orders`: show all existing orders for a symbol

If you run `python3 main.py` with no flags, the app will ask you for the missing values.

If you want the app to wait longer after placing an order, add something like `--wait-seconds 10`.

If you only want to check a past order, use `--order-id` with `--symbol`.

If you want every order for a symbol, use `--list-orders` with `--symbol`.

## Output

After you place an order, the app prints:

- an order request summary
- order response details like `orderId`, `status`, `executedQty`, and `avgPrice`
- a success or failure message

## Important Notes

- A successful response does not always mean the order is fully filled right away.
- The app now waits briefly after submission and checks the order again so the status is more accurate.
- If you see `Margin is insufficient`, use a smaller quantity.
- If you see `Signature for this request is not valid`, check that your key and secret are correct and belong to Testnet.

## Logs

Request and error details are written to:

```text
orders.log
```

## Example

```bash
python3 main.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

Example output:

```text
Order Request
Symbol : BTCUSDT
Side   : BUY
Type   : MARKET
Qty    : 0.001

Order Response
orderId     : 123456789
status      : FILLED
executedQty : 0.0010
avgPrice    : 68000.00
```

## Troubleshooting

- If the app stops with a usage message, pass the required flags or just run it and answer the prompts.
- If credentials are missing, check `.env`.
- If the order fails, read the message in the terminal and the details in `orders.log`.

