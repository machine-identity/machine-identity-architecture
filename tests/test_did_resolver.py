from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric import ed25519

from src.did_resolver import (
    DIDDocument,
    DIDResolver,
    DIDVerifier,
    create_did_key_from_private_key,
)


def test_did_key_resolution():
    """Test resolving a did:key DID."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes_raw()

    did = create_did_key_from_private_key(private_bytes, "ed25519")
    assert did.startswith("did:key:")

    resolver = DIDResolver()
    doc = resolver.resolve(did)

    assert isinstance(doc, DIDDocument)
    assert doc.id == did
    assert len(doc.verification_method) == 1

    vm = doc.verification_method[0]
    assert vm.type == "Ed25519VerificationKey2020"
    assert vm.controller == did
    assert vm.public_key_multibase is not None
    assert vm.public_key_jwk is not None
    assert vm.public_key_jwk["kty"] == "OKP"
    assert vm.public_key_jwk["crv"] == "Ed25519"

    assert doc.authentication == [vm.id]
    assert doc.assertion_method == [vm.id]


def test_did_pkh_resolution():
    """Test resolving a did:pkh DID."""
    did = "did:pkh:eip155:1:0x742d35Cc6634C0532925a3b8D4C0532925a3b8D4C"

    resolver = DIDResolver()
    doc = resolver.resolve(did)

    assert isinstance(doc, DIDDocument)
    assert doc.id == did
    assert len(doc.verification_method) == 1

    vm = doc.verification_method[0]
    assert vm.type == "EcdsaSecp256k1RecoveryMethod2020"
    assert vm.controller == did
    assert vm.blockchain_account_id == "eip155:1:0x742d35Cc6634C0532925a3b8D4C0532925a3b8D4C"

    assert doc.authentication == [vm.id]


def test_did_verification():
    """Test verifying signatures against DID Document."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes_raw()

    did = create_did_key_from_private_key(private_bytes, "ed25519")

    resolver = DIDResolver()
    doc = resolver.resolve(did)

    message = b"test message for verification"
    signature = private_key.sign(message)

    verifier = DIDVerifier()
    vm_id = doc.verification_method[0].id

    valid = verifier.verify_signature(doc, message, signature, vm_id)
    assert valid

    # Wrong signature should fail
    wrong_signature = b"x" * 64
    valid = verifier.verify_signature(doc, message, wrong_signature, vm_id)
    assert not valid

    # Wrong message should fail
    wrong_message = b"wrong message"
    valid = verifier.verify_signature(doc, wrong_message, signature, vm_id)
    assert not valid


def test_cross_agent_verification():
    """Test two agents verifying each other's signatures."""
    alice_private = ed25519.Ed25519PrivateKey.generate()
    alice_bytes = alice_private.private_bytes_raw()
    alice_did = create_did_key_from_private_key(alice_bytes, "ed25519")

    bob_private = ed25519.Ed25519PrivateKey.generate()
    bob_bytes = bob_private.private_bytes_raw()
    bob_did = create_did_key_from_private_key(bob_bytes, "ed25519")

    resolver = DIDResolver()
    alice_doc = resolver.resolve(alice_did)
    bob_doc = resolver.resolve(bob_did)

    verifier = DIDVerifier()

    # Alice signs, Bob verifies using Alice's DID Document
    message = b"Hello from Alice"
    alice_sig = alice_private.sign(message)
    alice_vm = alice_doc.verification_method[0].id

    valid = verifier.verify_signature(alice_doc, message, alice_sig, alice_vm)
    assert valid

    # Bob signs, Alice verifies using Bob's DID Document
    response = b"Hello from Bob"
    bob_sig = bob_private.sign(response)
    bob_vm = bob_doc.verification_method[0].id

    valid = verifier.verify_signature(bob_doc, response, bob_sig, bob_vm)
    assert valid


def test_did_document_serialization():
    """Test DID Document to/from dict."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes_raw()

    did = create_did_key_from_private_key(private_bytes, "ed25519")

    resolver = DIDResolver()
    doc = resolver.resolve(did)

    data = doc.to_dict()
    assert data["id"] == did
    assert len(data["verificationMethod"]) == 1

    doc2 = DIDDocument.from_dict(data)
    assert doc2.id == doc.id
    assert len(doc2.verification_method) == 1
    assert doc2.verification_method[0].id == doc.verification_method[0].id
