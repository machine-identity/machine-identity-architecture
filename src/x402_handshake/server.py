from __future__ import annotations

import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

from .types import (
    Currency,
    ExactPaymentPayload,
    Network,
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    verify_exact_payment,
)


@dataclass
class X402Server:
    """Server that enforces x402 payment requirements on protected endpoints."""

    pay_to_address: str
    network: str = Network.BASE_SEPOLIA
    asset: str = Currency.USDC
    default_amount: str = "0.001"
    default_timeout: int = 300
    resource_prefix: str = "/api/"

    def create_payment_requirements(
        self,
        resource: str,
        amount: str | None = None,
        description: str = "Payment required for API access",
    ) -> PaymentRequirements:
        """Create payment requirements for a specific resource."""
        return PaymentRequirements(
            scheme="exact",
            network=self.network,
            max_amount_required=amount or self.default_amount,
            resource=resource,
            description=description,
            pay_to=self.pay_to_address,
            max_timeout_seconds=self.default_timeout,
            asset=self.asset,
        )

    def payment_required_response(
        self,
        requirements: PaymentRequirements,
        status_code: int = 402,
    ) -> tuple[int, dict[str, Any], dict[str, str]]:
        """Generate a 402 response with payment requirements."""
        body = {
            "error": "Payment Required",
            "message": requirements.description,
            "x402": requirements.to_dict(),
        }
        headers = {
            "Content-Type": "application/json",
            "X-Payment-Requirements": json.dumps(requirements.to_dict()),
        }
        return status_code, body, headers

    def verify_payment(
        self, authorization_header: str, requirements: PaymentRequirements
    ) -> VerifyResponse:
        """Verify an x402 payment authorization header."""
        try:
            payment_payload = PaymentPayload.from_header(authorization_header)
        except Exception as e:
            return VerifyResponse(success=False, error=f"Invalid payment header: {e}")

        if payment_payload.scheme != "exact":
            return VerifyResponse(
                success=False, error=f"Unsupported scheme: {payment_payload.scheme}"
            )

        try:
            exact_payload = ExactPaymentPayload(**payment_payload.payload)
        except Exception as e:
            return VerifyResponse(success=False, error=f"Invalid payment payload: {e}")

        return verify_exact_payment(exact_payload, requirements)

    def protect(
        self, amount: str | None = None, description: str | None = None
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        """Decorator to protect an endpoint with x402 payment."""

        def decorator(
            func: Callable[..., Awaitable[Any]],
        ) -> Callable[..., Awaitable[Any]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # This would be integrated with a web framework (FastAPI, etc.)
                # For demo purposes, we show the pattern
                self.create_payment_requirements(
                    resource=getattr(func, "__name__", "unknown"),
                    amount=amount,
                    description=description or f"Access to {func.__name__}",
                )
                # In real implementation, extract auth header from request
                # verification = self.verify_payment(auth_header, requirements)
                # if not verification.success:
                #     return self.payment_required_response(requirements)
                return await func(*args, **kwargs)

            return wrapper

        return decorator


class MockPaymentVerifier:
    """Mock verifier for testing without blockchain interaction."""

    def __init__(self) -> None:
        self.verified_payments: list[dict[str, Any]] = []

    def verify_and_settle(self, verification: VerifyResponse) -> VerifyResponse:
        """Simulate on-chain verification and settlement."""
        if not verification.success:
            return verification

        # In production: verify transaction on-chain via RPC
        # For mock: simulate success
        mock_tx_hash = f"0x{''.join(['a'] * 64)}"
        self.verified_payments.append(
            {
                "payer": verification.payer,
                "amount": "0.001",
                "tx_hash": mock_tx_hash,
                "timestamp": time.time(),
            }
        )

        return VerifyResponse(
            success=True,
            payer=verification.payer,
            transaction_hash=mock_tx_hash,
        )

    def get_payment_history(self) -> list[dict[str, Any]]:
        return self.verified_payments
