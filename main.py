"""
main.py — CLI entry point
Validates user input, calls the client, prints results.

Usage examples:
  python main.py --symbol BTCUSDT --side BUY  --type MARKET --qty 0.01
  python main.py --symbol ETHUSDT --side SELL --type LIMIT  --qty 0.1 --price 2000
"""

import argparse
import logging
import os
import getpass
import sys
from pathlib import Path

from binance_client import BinanceClient

# ── logging setup (file + console) ────────────────────────────────────────────

def setup_logging(log_file: str = "orders.log"):
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt))
    root_logger.addHandler(file_handler)

logger = logging.getLogger("binance.cli")


def load_env_file(env_path: str = ".env") -> None:
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


# ── input validation ───────────────────────────────────────────────────────────

VALID_SIDES = {"BUY", "SELL"}
VALID_TYPES = {"MARKET", "LIMIT"}

def validate(args) -> str | None:
    """Return an error string if something is wrong, else None."""
    if args.side.upper() not in VALID_SIDES:
        return f"Invalid side '{args.side}'. Choose BUY or SELL."
    if args.type.upper() not in VALID_TYPES:
        return f"Invalid type '{args.type}'. Choose MARKET or LIMIT."
    if args.qty <= 0:
        return f"Quantity must be > 0, got {args.qty}."
    if args.type.upper() == "LIMIT":
        if args.price is None:
            return "--price is required for LIMIT orders."
        if args.price <= 0:
            return f"Price must be > 0, got {args.price}."
    return None


# ── output formatting ──────────────────────────────────────────────────────────

def print_summary(args):
    print("Order request")
    print(f"symbol: {args.symbol.upper()}")
    print(f"side: {args.side.upper()}")
    print(f"type: {args.type.upper()}")
    print(f"qty: {args.qty}")
    if args.type.upper() == "LIMIT":
        print(f"price: {args.price}")
    print()

def print_response(data: dict):
    print("Order response")
    print(f"orderId: {data.get('orderId', 'N/A')}")
    print(f"status: {data.get('status', 'N/A')}")
    print(f"executedQty: {data.get('executedQty', 'N/A')}")
    avg = data.get("avgPrice") or data.get("price", "N/A")
    print(f"avgPrice: {avg}")
    print(f"symbol: {data.get('symbol', 'N/A')}")
    print(f"side: {data.get('side', 'N/A')}")
    print(f"type: {data.get('type', 'N/A')}")
    print()


def print_status(args, data: dict):
    print("Order status")
    print(f"symbol: {args.symbol.upper()}")
    print(f"orderId: {args.order_id}")
    print(f"status: {data.get('status', 'N/A')}")
    print(f"executedQty: {data.get('executedQty', 'N/A')}")
    avg = data.get("avgPrice") or data.get("price", "N/A")
    print(f"avgPrice: {avg}")
    print(f"side: {data.get('side', 'N/A')}")
    print(f"type: {data.get('type', 'N/A')}")
    print(f"updateTime: {data.get('updateTime', 'N/A')}")
    print()


def print_orders(symbol: str, orders: list[dict]):
    print("Orders")
    print(f"symbol: {symbol.upper()}")
    print(f"count: {len(orders)}")
    print()

    for order in orders:
        print(f"orderId: {order.get('orderId', 'N/A')}")
        print(f"status: {order.get('status', 'N/A')}")
        print(f"side: {order.get('side', 'N/A')}")
        print(f"type: {order.get('type', 'N/A')}")
        print(f"origQty: {order.get('origQty', 'N/A')}")
        print(f"executedQty: {order.get('executedQty', 'N/A')}")
        print(f"price: {order.get('price', 'N/A')}")
        print(f"updateTime: {order.get('updateTime', 'N/A')}")
        print()


def prompt_if_missing(args):
    if not args.symbol:
        args.symbol = input("Symbol (e.g. BTCUSDT): ").strip()

    if getattr(args, "order_id", None) is None and not getattr(args, "list_orders", False) and not args.side:
        args.side = input("Side (BUY/SELL): ").strip()

    if getattr(args, "order_id", None) is None and not getattr(args, "list_orders", False):
        if not args.type:
            args.type = input("Order type (MARKET/LIMIT): ").strip()

        if args.qty is None:
            qty_text = input("Quantity: ").strip()
            args.qty = float(qty_text)

        if args.type and args.type.upper() == "LIMIT" and args.price is None:
            price_text = input("Price for LIMIT order: ").strip()
            args.price = float(price_text)

    return args


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    setup_logging()
    load_env_file()

    parser = argparse.ArgumentParser(description="Binance Futures Testnet order placer")
    parser.add_argument("--list-orders", action="store_true", help="List existing orders for a symbol")
    parser.add_argument("--order-id", type=int, help="Check the status of an existing order")
    parser.add_argument("--symbol", help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side",   help="BUY or SELL")
    parser.add_argument("--type",   help="MARKET or LIMIT")
    parser.add_argument("--qty",    type=float, help="Order quantity")
    parser.add_argument("--price",  type=float, default=None,  help="Limit price (LIMIT orders only)")
    parser.add_argument("--wait-seconds", type=float, default=5.0, help="How long to wait for the final order status after placing the order")
    args = parser.parse_args()

    args = prompt_if_missing(args)

    if args.list_orders:
        if not args.symbol:
            err = "--symbol is required when listing orders."
            logger.error("Validation error: %s", err)
            print(f"Error: {err}")
            sys.exit(1)

        api_key    = os.getenv("BINANCE_TESTNET_API_KEY")
        api_secret = os.getenv("BINANCE_TESTNET_API_SECRET")

        if not api_key or not api_secret:
            print("Binance Testnet credentials not found in env vars.")
            api_key = input("API key: ").strip()
            api_secret = getpass.getpass("API secret: ").strip()

            if not api_key or not api_secret:
                print("Error: API key and secret are required.")
                sys.exit(1)

        client = BinanceClient(api_key, api_secret)

        try:
            orders = client.list_orders(args.symbol)
            print_orders(args.symbol, orders)
            print("Success: orders retrieved.")
            return
        except ValueError as e:
            logger.error("List orders failed: %s", e)
            print(f"Error: {e}")
            sys.exit(1)
        except (ConnectionError, TimeoutError) as e:
            logger.error("Network error: %s", e)
            print(f"Error: Network error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.exception("Unexpected error")
            print(f"Error: Unexpected error: {e}")
            sys.exit(1)

    if args.order_id is not None:
        if not args.symbol:
            err = "--symbol is required when checking order status."
            logger.error("Validation error: %s", err)
            print(f"Error: {err}")
            sys.exit(1)

        api_key    = os.getenv("BINANCE_TESTNET_API_KEY")
        api_secret = os.getenv("BINANCE_TESTNET_API_SECRET")

        if not api_key or not api_secret:
            print("Binance Testnet credentials not found in env vars.")
            api_key = input("API key: ").strip()
            api_secret = getpass.getpass("API secret: ").strip()

            if not api_key or not api_secret:
                print("Error: API key and secret are required.")
                sys.exit(1)

        client = BinanceClient(api_key, api_secret)

        try:
            response = client.get_order(args.symbol, int(args.order_id))
            print_status(args, response)
            print("Success: order status retrieved.")
            return
        except ValueError as e:
            logger.error("Status lookup failed: %s", e)
            print(f"Error: {e}")
            sys.exit(1)
        except (ConnectionError, TimeoutError) as e:
            logger.error("Network error: %s", e)
            print(f"Error: Network error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.exception("Unexpected error")
            print(f"Error: Unexpected error: {e}")
            sys.exit(1)

    # ── validate ───────────────────────────────────────────────────────────────
    err = validate(args)
    if err:
        logger.error("Validation error: %s", err)
        print(f"Error: {err}")
        sys.exit(1)

    # ── read credentials from env (never hardcode keys) ───────────────────────
    api_key    = os.getenv("BINANCE_TESTNET_API_KEY")
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET")

    if not api_key or not api_secret:
        print("Binance Testnet credentials not found in env vars.")
        api_key = input("API key: ").strip()
        api_secret = getpass.getpass("API secret: ").strip()

        if not api_key or not api_secret:
            print("Error: API key and secret are required.")
            sys.exit(1)

    client = BinanceClient(api_key, api_secret)

    # ── print what we're about to send ────────────────────────────────────────
    print_summary(args)
    logger.info("Placing %s %s order for %s qty=%s price=%s",
                args.type, args.side, args.symbol, args.qty, args.price)

    # ── place order ───────────────────────────────────────────────────────────
    try:
        if args.type.upper() == "MARKET":
            response = client.place_market_order(args.symbol, args.side, args.qty)
        else:
            response = client.place_limit_order(args.symbol, args.side, args.qty, args.price)

        order_id = response.get("orderId")
        if order_id:
            latest_response = client.wait_for_order_final_status(
                args.symbol,
                int(order_id),
                timeout_seconds=args.wait_seconds,
            )
            if latest_response:
                response = latest_response

        print_response(response)
        logger.info("Order placed successfully. orderId=%s", response.get("orderId"))
        print("Success: order placed.")

    except ValueError as e:
        # API-level error (wrong symbol, bad params, etc.)
        logger.error("Order failed: %s", e)
        print(f"Error: {e}")
        sys.exit(1)

    except (ConnectionError, TimeoutError) as e:
        logger.error("Network error: %s", e)
        print(f"Error: Network error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.exception("Unexpected error")
        print(f"Error: Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()