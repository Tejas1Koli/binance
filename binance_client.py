"""Binance Futures Testnet API layer."""

import hashlib
import hmac
import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


logger = logging.getLogger("binance.client")

BASE_URL = "https://testnet.binancefuture.com"


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()

    def _sign(self, params: dict) -> dict:
        """Add timestamp + HMAC-SHA256 signature to a param dict."""
        params = dict(params)
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        params["signature"] = hmac.new(
            self.api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return params

    def _post(self, path: str, params: dict) -> dict:
        """Sign + POST; raise on HTTP or API errors; return parsed JSON."""
        signed = self._sign(params)
        url = BASE_URL + path
        body = urlencode(signed).encode("utf-8")

        logger.info(
            "POST %s params=%s",
            url,
            {k: v for k, v in signed.items() if k != "signature"},
        )

        request = Request(
            url,
            data=body,
            method="POST",
            headers={
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        try:
            with urlopen(request, timeout=10) as response:
                payload = response.read().decode("utf-8")
                logger.info("Response HTTP %s: %s", response.status, payload[:400])
                data = json.loads(payload) if payload else {}
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else ""
            logger.error("HTTP error %s: %s", exc.code, error_body)
            try:
                data = json.loads(error_body) if error_body else {}
            except json.JSONDecodeError:
                data = {}
            if isinstance(data, dict) and data.get("code", 0) < 0:
                msg = data.get("msg", "Unknown API error")
                raise ValueError(f"Binance API error {data['code']}: {msg}") from exc
            raise ValueError(error_body or f"Binance HTTP error {exc.code}") from exc
        except URLError as exc:
            logger.error("Network failure: %s", exc)
            raise ConnectionError(f"Cannot reach Binance Testnet: {exc}") from exc

        if isinstance(data, dict) and data.get("code", 0) < 0:
            msg = data.get("msg", "Unknown API error")
            logger.error("Binance API error %s: %s", data["code"], msg)
            raise ValueError(f"Binance API error {data['code']}: {msg}")

        return data

    def _get(self, path: str, params: dict) -> dict:
        """Sign + GET; raise on HTTP or API errors; return parsed JSON."""
        signed = self._sign(params)
        query_string = urlencode(signed)
        url = f"{BASE_URL}{path}?{query_string}"

        logger.info(
            "GET %s params=%s",
            url,
            {k: v for k, v in signed.items() if k != "signature"},
        )

        request = Request(
            url,
            method="GET",
            headers={"X-MBX-APIKEY": self.api_key},
        )

        try:
            with urlopen(request, timeout=10) as response:
                payload = response.read().decode("utf-8")
                logger.info("Response HTTP %s: %s", response.status, payload[:400])
                data = json.loads(payload) if payload else {}
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else ""
            logger.error("HTTP error %s: %s", exc.code, error_body)
            try:
                data = json.loads(error_body) if error_body else {}
            except json.JSONDecodeError:
                data = {}
            if isinstance(data, dict) and data.get("code", 0) < 0:
                msg = data.get("msg", "Unknown API error")
                raise ValueError(f"Binance API error {data['code']}: {msg}") from exc
            raise ValueError(error_body or f"Binance HTTP error {exc.code}") from exc
        except URLError as exc:
            logger.error("Network failure: %s", exc)
            raise ConnectionError(f"Cannot reach Binance Testnet: {exc}") from exc

        if isinstance(data, dict) and data.get("code", 0) < 0:
            msg = data.get("msg", "Unknown API error")
            logger.error("Binance API error %s: %s", data["code"], msg)
            raise ValueError(f"Binance API error {data['code']}: {msg}")

        return data

    def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity,
        }
        return self._post("/fapi/v1/order", params)

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> dict:
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "LIMIT",
            "quantity": quantity,
            "price": price,
            "timeInForce": "GTC",
        }
        return self._post("/fapi/v1/order", params)

    def get_order(self, symbol: str, order_id: int) -> dict:
        return self._get(
            "/fapi/v1/order",
            {
                "symbol": symbol.upper(),
                "orderId": order_id,
            },
        )

    def list_orders(self, symbol: str, limit: int = 50) -> list[dict]:
        data = self._get(
            "/fapi/v1/allOrders",
            {
                "symbol": symbol.upper(),
                "limit": limit,
            },
        )
        return data if isinstance(data, list) else [data]

    def wait_for_order_final_status(
        self,
        symbol: str,
        order_id: int,
        timeout_seconds: float = 5.0,
        poll_interval_seconds: float = 0.5,
    ) -> dict:
        """Poll the order status for a short window and return the latest response."""
        deadline = time.time() + timeout_seconds
        latest = None
        terminal_statuses = {"FILLED", "CANCELED", "REJECTED", "EXPIRED"}

        while time.time() < deadline:
            latest = self.get_order(symbol, order_id)
            status = str(latest.get("status", "")).upper()
            if status in terminal_statuses or status == "PARTIALLY_FILLED":
                return latest
            time.sleep(poll_interval_seconds)

        return latest or self.get_order(symbol, order_id)