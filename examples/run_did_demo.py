#!/usr/bin/env python3
"""
DID Resolver Demo

Demonstrates W3C DID resolution and verification for did:key and did:pkh methods.
"""

from cryptography.hazmat.primitives.asymmetric import ed25519

from did_resolver import (
    DIDResolver,
    DIDVerifier,
    create_did_key_from_private_key,
)


def demo_did_key():

    # Generate Ed25519 key pair
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes_raw()
    public_key = private_key.public_key()
    public_key.public_bytes_raw()

    # Create did:key from private key
    did = create_did_key_from_private_key(private_bytes, "ed25519")

    # Resolve the DID
    resolver = DIDResolver()
    did_doc = resolver.resolve(did)

    for _vm in did_doc.verification_method:
        pass

    # Sign a challenge
    challenge = b"autonomous-agent-challenge-2026"
    signature = private_key.sign(challenge)

    # Verify using DID Document
    verifier = DIDVerifier()
    vm_id = did_doc.verification_method[0].id
    verifier.verify_signature(did_doc, challenge, signature, vm_id)


    return did, did_doc


def demo_did_pkh():

    # Example did:pkh (Ethereum address)
    did = "did:pkh:eip155:1:0x742d35Cc6634C0532925a3b8D4C0532925a3b8D4C"

    resolver = DIDResolver()
    did_doc = resolver.resolve(did)

    for _vm in did_doc.verification_method:
        pass

    return did, did_doc


def demo_cross_verification():

    # Create two agents
    alice_private = ed25519.Ed25519PrivateKey.generate()
    alice_bytes = alice_private.private_bytes_raw()
    alice_did = create_did_key_from_private_key(alice_bytes, "ed25519")

    bob_private = ed25519.Ed25519PrivateKey.generate()
    bob_bytes = bob_private.private_bytes_raw()
    bob_did = create_did_key_from_private_key(bob_bytes, "ed25519")


    # Resolve each other's DIDs
    resolver = DIDResolver()
    alice_doc = resolver.resolve(alice_did)
    bob_doc = resolver.resolve(bob_did)

    # Alice sends signed message to Bob
    message = b"Hello Bob, this is Alice. Task completed: data-analysis-2026"
    alice_signature = alice_private.sign(message)

    # Bob verifies Alice's signature using Alice's DID Document
    verifier = DIDVerifier()
    alice_vm_id = alice_doc.verification_method[0].id
    verifier.verify_signature(alice_doc, message, alice_signature, alice_vm_id)


    # Bob responds
    response = b"Thanks Alice! Payment sent via x402."
    bob_signature = bob_private.sign(response)

    bob_vm_id = bob_doc.verification_method[0].id
    verifier.verify_signature(bob_doc, response, bob_signature, bob_vm_id)




def main():
    demo_did_key()
    demo_did_pkh()
    demo_cross_verification()


if __name__ == "__main__":
    main()
