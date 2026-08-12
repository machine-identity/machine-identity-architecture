from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .types import (
    ExactPaymentPayload,
    PaymentPayload,
    PaymentRequirements,
    sign_payment_authorization,
)


@dataclass
class X402Client:
    """Client for making x402-paid requests to servers."""

    private_key: str
    account_address: str
    base_url: str = ""
    timeout: float = 30.0

    def __post_init__(self) -> None:
        from eth_account import Account

        self.account = Account.from_key(self.private_key)
        if not self.account_address:
            self.account_address = self.account.address
        self.client = httpx.Client(timeout=self.timeout)

    def request_with_payment(
        self,
        method: str,
        path: str,
        requirements: PaymentRequirements,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Make a request, handle 402 response, pay, and retry.
        """
        url = f"{self.base_url}{path}" if self.base_url else path
        request_headers = headers or {}
        request_headers["Content-Type"] = "application/json"

        # First request - expect 402
        response = self.client.request(method, url, json=json_data, headers=request_headers)

        if response.status_code != 402:
            return response

        # Parse payment requirements from 402 response
        try:
            error_data = response.json()
            payment_reqs = error_data.get("x402", {})
            if not payment_reqs:
                # Try to parse from headers
                x402_header = response.headers.get("X-Payment-Requirements")
                if x402_header:
                    payment_reqs = json.loads(x402_header)
        except Exception:
            return response

        requirements = PaymentRequirements.from_dict(payment_reqs)

        # Create payment payload
        payment_payload = self._create_payment_payload(requirements)

        # Retry with payment
        request_headers["Authorization"] = payment_payload.to_header()
        response = self.client.request(method, url, json=json_data, headers=request_headers)

        return response

    def _create_payment_payload(self, requirements: PaymentRequirements) -> PaymentPayload:
        """Create a signed payment payload for the given requirements."""
        nonce = secrets.token_hex(32)
        valid_after = int(time.time()) - 60  # Allow 1 min clock skew
        valid_before = valid_after + requirements.max_timeout_seconds

        signature = sign_payment_authorization(
            private_key=self.private_key,
            from_address=self.account_address,
            to_address=requirements.pay_to,
            value=requirements.max_amount_required,
            valid_after=valid_after,
            valid_before=valid_before,
            nonce=nonce,
        )

        auth = {
            "from": self.account_address,
            "to": requirements.pay_to,
            "value": requirements.max_amount_required,
            "validAfter": valid_after,
            "validBefore": valid_before,
            "nonce": f"0x{nonce}",
            "signature": f"0x{signature}",
        }

        payload = ExactPaymentPayload(
            authorization=auth,
            amount=requirements.max_amount_required,
            currency=requirements.asset,
            network=requirements.network,
            pay_to=requirements.pay_to,
            resource=requirements.resource,
            nonce=f"0x{nonce}",
            timestamp=int(time.time()),
        )

        return PaymentPayload(
            x402_version=1,
            scheme="exact",
            network=requirements.network,
            payload=payload.dict(),
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> X402Client:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()
