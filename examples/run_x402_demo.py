#!/usr/bin/env python3
"""
x402 Handshake Demo

Demonstrates the HTTP 402 Payment Required flow for agent-to-agent micropayments.
"""

import secrets

from eth_account import Account

from x402_handshake import (
    Currency,
    MockPaymentVerifier,
    Network,
    X402Client,
    X402Server,
)


def main():
    print("=" * 60)
    print("x402 HANDSHAKE DEMO")
    print("=" * 60)

    # Setup: Create server (API provider) and client (agent)
    server_private_key = secrets.token_hex(32)
    server_account = Account.from_key(server_private_key)
    server_pay_to = server_account.address

    client_private_key = secrets.token_hex(32)
    client_account = Account.from_key(client_private_key)

    print(f"\n📡 Server (API Provider): {server_pay_to}")
    print(f"🤖 Client (Autonomous Agent): {client_account.address}")

    # Create server with payment requirements
    server = X402Server(
        pay_to_address=server_pay_to,
        network=Network.BASE_SEPOLIA,
        asset=Currency.USDC,
        default_amount="0.001",  # $0.001 USDC
    )

    # Create payment requirements for a resource
    resource = "/api/v1/agent-task"
    requirements = server.create_payment_requirements(
        resource=resource,
        amount="0.001",
        description="Execute autonomous agent task",
    )

    print("\n💰 Payment Requirements:")
    print(f"   Resource: {requirements.resource}")
    print(f"   Amount: {requirements.max_amount_required} {requirements.asset}")
    print(f"   Network: {requirements.network}")
    print(f"   Pay To: {requirements.pay_to}")

    # Create client
    client = X402Client(
        private_key=client_private_key,
        account_address=client_account.address,
        base_url="http://localhost:8000",  # Mock base URL
    )

    # Simulate the handshake
    print("\n🔄 Simulating x402 Handshake...")
    print("   1. Client requests resource (expects 402)")
    print("   2. Server responds with 402 + PaymentRequirements")
    print("   3. Client creates signed payment authorization")
    print("   4. Client retries with Authorization: x402 header")
    print("   5. Server verifies payment and grants access")

    # Create payment payload (what client would send)
    payment_payload = client._create_payment_payload(requirements)
    print("\n📝 Payment Payload (Authorization header):")
    print(f"   {payment_payload.to_header()[:200]}...")

    # Verify payment (server side)
    verification = server.verify_payment(payment_payload.to_header(), requirements)
    print("\n✅ Payment Verification:")
    print(f"   Success: {verification.success}")
    print(f"   Payer: {verification.payer}")
    print(f"   Error: {verification.error}")

    # Mock settlement
    verifier = MockPaymentVerifier()
    settlement = verifier.verify_and_settle(verification)
    print("\n💎 Mock Settlement:")
    print(f"   Success: {settlement.success}")
    print(f"   Transaction Hash: {settlement.transaction_hash}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE - x402 handshake working!")
    print("=" * 60)


if __name__ == "__main__":
    main()
