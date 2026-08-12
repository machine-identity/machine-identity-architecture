from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from eth_account import Account
from eth_account.messages import encode_defunct
from pydantic import BaseModel, validator


class Network(str):
    """Supported blockchain networks for x402 payments."""
    BASE_SEPOLIA = "base-sepolia"
    BASE = "base"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"


class Currency(str):
    """Supported payment currencies."""
    USDC = "USDC"
    ETH = "ETH"


@dataclass
class PaymentRequirements:
    """x402 Payment Requirements object (sent in 402 response)."""
    scheme: str = "exact"
    network: str = Network.BASE_SEPOLIA
    max_amount_required: str = "0.001"
    resource: str = ""
    description: str = "Payment required for API access"
    mime_type: str = "application/json"
    pay_to: str = ""
    max_timeout_seconds: int = 300
    asset: str = Currency.USDC
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "scheme": self.scheme,
            "network": self.network,
            "maxAmountRequired": self.max_amount_required,
            "resource": self.resource,
            "description": self.description,
            "mimeType": self.mime_type,
            "payTo": self.pay_to,
            "maxTimeoutSeconds": self.max_timeout_seconds,
            "asset": self.asset,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PaymentRequirements:
        return cls(
            scheme=data.get("scheme", "exact"),
            network=data.get("network", Network.BASE_SEPOLIA),
            max_amount_required=data.get("maxAmountRequired", "0.001"),
            resource=data.get("resource", ""),
            description=data.get("description", "Payment required for API access"),
            mime_type=data.get("mimeType", "application/json"),
            pay_to=data.get("payTo", ""),
            max_timeout_seconds=data.get("maxTimeoutSeconds", 300),
            asset=data.get("asset", Currency.USDC),
            extra=data.get("extra", {}),
        )


@dataclass
class PaymentPayload:
    """x402 Payment Payload (sent by client in Authorization header)."""
    x402_version: int = 1
    scheme: str = "exact"
    network: str = Network.BASE_SEPOLIA
    payload: dict = field(default_factory=dict)

    def to_header(self) -> str:
        return f"x402 {json.dumps(self.to_dict())}"

    def to_dict(self) -> dict:
        return {
            "x402Version": self.x402_version,
            "scheme": self.scheme,
            "network": self.network,
            "payload": self.payload,
        }

    @classmethod
    def from_header(cls, header: str) -> PaymentPayload:
        if not header.startswith("x402 "):
            raise ValueError("Invalid x402 header format")
        data = json.loads(header[5:])
        return cls(
            x402_version=data.get("x402Version", 1),
            scheme=data.get("scheme", "exact"),
            network=data.get("network", Network.BASE_SEPOLIA),
            payload=data.get("payload", {}),
        )


@dataclass
class VerifyResponse:
    """x402 Verify Response (returned by server after payment verification)."""
    success: bool
    payer: str = ""
    transaction_hash: str = ""
    error: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "payer": self.payer,
            "transactionHash": self.transaction_hash,
            "error": self.error,
            "extra": self.extra,
        }


class ExactPaymentPayload(BaseModel):
    """Exact payment scheme payload structure."""
    authorization: dict
    amount: str
    currency: str
    network: str
    pay_to: str
    resource: str
    nonce: str
    timestamp: int

    @validator("authorization")
    def validate_auth(cls, v):
        required = ["from", "to", "value", "validAfter", "validBefore", "nonce", "signature"]
        for field_name in required:
            if field_name not in v:
                raise ValueError(f"Missing required authorization field: {field_name}")
        return v


def create_payment_message(
    from_address: str,
    to_address: str,
    value: str,
    valid_after: int,
    valid_before: int,
    nonce: str,
) -> bytes:
    """Create EIP-712 style message for payment authorization."""
    message = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "PaymentAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ],
        },
        "primaryType": "PaymentAuthorization",
        "domain": {
            "name": "x402",
            "version": "1",
            "chainId": 84532,  # Base Sepolia
            "verifyingContract": to_address,
        },
        "message": {
            "from": from_address,
            "to": to_address,
            "value": value,
            "validAfter": valid_after,
            "validBefore": valid_before,
            "nonce": nonce,
        },
    }
    return json.dumps(message, separators=(",", ":")).encode()


def sign_payment_authorization(
    private_key: str,
    from_address: str,
    to_address: str,
    value: str,
    valid_after: int,
    valid_before: int,
    nonce: str,
) -> str:
    """Sign a payment authorization with the client's private key."""
    account = Account.from_key(private_key)
    message = create_payment_message(
        from_address, to_address, value, valid_after, valid_before, nonce
    )
    encoded = encode_defunct(message)
    signed = account.sign_message(encoded)
    return signed.signature.hex()


def verify_payment_signature(
    from_address: str,
    to_address: str,
    value: str,
    valid_after: int,
    valid_before: int,
    nonce: str,
    signature: str,
) -> bool:
    """Verify a payment authorization signature."""
    try:
        message = create_payment_message(
            from_address, to_address, value, valid_after, valid_before, nonce
        )
        encoded = encode_defunct(message)
        recovered = Account.recover_message(encoded, signature=bytes.fromhex(signature))
        return recovered.lower() == from_address.lower()
    except Exception:
        return False


def verify_exact_payment(
    payload: ExactPaymentPayload, requirements: PaymentRequirements
) -> VerifyResponse:
    """Verify an exact payment payload against requirements."""
    auth = payload.authorization

    # Check pay_to matches
    if auth["to"].lower() != requirements.pay_to.lower():
        return VerifyResponse(success=False, error="Invalid pay_to address")

    # Check amount matches
    if auth["value"] != requirements.max_amount_required:
        return VerifyResponse(success=False, error="Invalid amount")

    # Check network matches
    if payload.network != requirements.network:
        return VerifyResponse(success=False, error="Invalid network")

    # Check currency matches
    if payload.currency != requirements.asset:
        return VerifyResponse(success=False, error="Invalid currency")

    # Check resource matches
    if payload.resource != requirements.resource:
        return VerifyResponse(success=False, error="Invalid resource")

    # Check timestamp validity
    now = int(time.time())
    if not (auth["validAfter"] <= now <= auth["validBefore"]):
        return VerifyResponse(success=False, error="Payment authorization expired")

    # Verify signature
    if not verify_payment_signature(
        from_address=auth["from"],
        to_address=auth["to"],
        value=auth["value"],
        valid_after=auth["validAfter"],
        valid_before=auth["validBefore"],
        nonce=auth["nonce"],
        signature=auth["signature"],
    ):
        return VerifyResponse(success=False, error="Invalid signature")

    return VerifyResponse(
        success=True,
        payer=auth["from"],
        transaction_hash="",  # Would be filled after on-chain verification
    )
