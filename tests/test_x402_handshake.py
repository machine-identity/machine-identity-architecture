from __future__ import annotations

import secrets

from eth_account import Account

from src.x402_handshake.types import (
    Currency,
    ExactPaymentPayload,
    Network,
    PaymentPayload,
    PaymentRequirements,
    sign_payment_authorization,
    verify_exact_payment,
    verify_payment_signature,
)


def test_payment_requirements_serialization():
    """Test PaymentRequirements to/from dict."""
    req = PaymentRequirements(
        scheme="exact",
        network=Network.BASE_SEPOLIA,
        max_amount_required="0.001",
        resource="/api/test",
        description="Test payment",
        pay_to="0x1234567890123456789012345678901234567890",
        asset=Currency.USDC,
    )

    data = req.to_dict()
    assert data["scheme"] == "exact"
    assert data["network"] == "base-sepolia"
    assert data["maxAmountRequired"] == "0.001"
    assert data["payTo"] == "0x1234567890123456789012345678901234567890"
    assert data["asset"] == "USDC"

    req2 = PaymentRequirements.from_dict(data)
    assert req2.scheme == req.scheme
    assert req2.network == req.network
    assert req2.max_amount_required == req.max_amount_required
    assert req2.pay_to == req.pay_to


def test_payment_payload_header():
    """Test PaymentPayload header encoding/decoding."""
    payload = PaymentPayload(
        x402_version=1,
        scheme="exact",
        network=Network.BASE_SEPOLIA,
        payload={"test": "data"},
    )

    header = payload.to_header()
    assert header.startswith("x402 ")

    payload2 = PaymentPayload.from_header(header)
    assert payload2.x402_version == payload.x402_version
    assert payload2.scheme == payload.scheme
    assert payload2.network == payload.network
    assert payload2.payload == payload.payload


def test_sign_and_verify_payment():
    """Test signing and verifying payment authorization."""
    private_key = secrets.token_hex(32)
    account = Account.from_key(private_key)
    from_address = account.address
    to_address = "0x0987654321098765432109876543210987654321"
    value = "0.001"
    valid_after = 1000000
    valid_before = 2000000
    nonce = "0x" + secrets.token_hex(32)

    signature = sign_payment_authorization(
        private_key=private_key,
        from_address=from_address,
        to_address=to_address,
        value=value,
        valid_after=valid_after,
        valid_before=valid_before,
        nonce=nonce,
    )

    assert signature.startswith("0x") or len(signature) == 130  # 65 bytes hex

    # Verify
    valid = verify_payment_signature(
        from_address=from_address,
        to_address=to_address,
        value=value,
        valid_after=valid_after,
        valid_before=valid_before,
        nonce=nonce,
        signature=signature,
    )
    assert valid

    # Verify with wrong address fails
    valid_wrong = verify_payment_signature(
        from_address="0x1111111111111111111111111111111111111111",
        to_address=to_address,
        value=value,
        valid_after=valid_after,
        valid_before=valid_before,
        nonce=nonce,
        signature=signature,
    )
    assert not valid_wrong


def test_verify_exact_payment():
    """Test full exact payment verification."""
    private_key = secrets.token_hex(32)
    account = Account.from_key(private_key)
    payer = account.address
    pay_to = "0x0987654321098765432109876543210987654321"

    requirements = PaymentRequirements(
        scheme="exact",
        network=Network.BASE_SEPOLIA,
        max_amount_required="0.001",
        resource="/api/test",
        pay_to=pay_to,
        asset=Currency.USDC,
    )

    valid_after = int(__import__("time").time()) - 60
    valid_before = valid_after + 300
    nonce = "0x" + secrets.token_hex(32)

    signature = sign_payment_authorization(
        private_key=private_key,
        from_address=payer,
        to_address=pay_to,
        value="0.001",
        valid_after=valid_after,
        valid_before=valid_before,
        nonce=nonce,
    )

    auth = {
        "from": payer,
        "to": pay_to,
        "value": "0.001",
        "validAfter": valid_after,
        "validBefore": valid_before,
        "nonce": nonce,
        "signature": signature,
    }

    payload = ExactPaymentPayload(
        authorization=auth,
        amount="0.001",
        currency="USDC",
        network="base-sepolia",
        pay_to=pay_to,
        resource="/api/test",
        nonce=nonce,
        timestamp=int(__import__("time").time()),
    )

    result = verify_exact_payment(payload, requirements)
    assert result.success
    assert result.payer == payer


def test_verify_exact_payment_failure_cases():
    """Test payment verification failure cases."""
    private_key = secrets.token_hex(32)
    account = Account.from_key(private_key)
    payer = account.address
    pay_to = "0x0987654321098765432109876543210987654321"
    wrong_pay_to = "0x1111111111111111111111111111111111111111"

    requirements = PaymentRequirements(
        scheme="exact",
        network=Network.BASE_SEPOLIA,
        max_amount_required="0.001",
        resource="/api/test",
        pay_to=pay_to,
        asset=Currency.USDC,
    )

    valid_after = int(__import__("time").time()) - 60
    valid_before = valid_after + 300
    nonce = "0x" + secrets.token_hex(32)

    signature = sign_payment_authorization(
        private_key=private_key,
        from_address=payer,
        to_address=pay_to,
        value="0.001",
        valid_after=valid_after,
        valid_before=valid_before,
        nonce=nonce,
    )

    # Wrong pay_to
    auth = {
        "from": payer,
        "to": wrong_pay_to,
        "value": "0.001",
        "validAfter": valid_after,
        "validBefore": valid_before,
        "nonce": nonce,
        "signature": signature,
    }
    payload = ExactPaymentPayload(
        authorization=auth,
        amount="0.001",
        currency="USDC",
        network="base-sepolia",
        pay_to=wrong_pay_to,
        resource="/api/test",
        nonce=nonce,
        timestamp=int(__import__("time").time()),
    )
    result = verify_exact_payment(payload, requirements)
    assert not result.success
    assert "pay_to" in result.error.lower()

    # Wrong amount
    auth["to"] = pay_to
    auth["value"] = "0.002"
    payload = ExactPaymentPayload(
        authorization=auth,
        amount="0.002",
        currency="USDC",
        network="base-sepolia",
        pay_to=pay_to,
        resource="/api/test",
        nonce=nonce,
        timestamp=int(__import__("time").time()),
    )
    result = verify_exact_payment(payload, requirements)
    assert not result.success
    assert "amount" in result.error.lower()

    # Expired
    auth["value"] = "0.001"
    expired_payload = ExactPaymentPayload(
        authorization=auth,
        amount="0.001",
        currency="USDC",
        network="base-sepolia",
        pay_to=pay_to,
        resource="/api/test",
        nonce=nonce,
        timestamp=int(__import__("time").time()),
    )
    # Manually set expired timestamps
    expired_payload.authorization["validAfter"] = 1000
    expired_payload.authorization["validBefore"] = 2000
    result = verify_exact_payment(expired_payload, requirements)
    assert not result.success
    assert "expired" in result.error.lower()
