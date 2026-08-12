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
    # Setup: Create server (API provider) and client (agent)
    server_private_key = secrets.token_hex(32)
    server_account = Account.from_key(server_private_key)
    server_pay_to = server_account.address

    client_private_key = secrets.token_hex(32)
    client_account = Account.from_key(client_private_key)

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

    # Create client
    client = X402Client(
        private_key=client_private_key,
        account_address=client_account.address,
        base_url="http://localhost:8000",  # Mock base URL
    )

    # Simulate the handshake

    # Create payment payload (what client would send)
    payment_payload = client._create_payment_payload(requirements)

    # Verify payment (server side)
    verification = server.verify_payment(payment_payload.to_header(), requirements)

    # Mock settlement
    verifier = MockPaymentVerifier()
    verifier.verify_and_settle(verification)


if __name__ == "__main__":
    main()
