from __future__ import annotations

import base58
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from .types import (
    DIDDocument,
    VerificationMethod,
    multibase_to_jwk,
    parse_did_key,
    parse_did_pkh,
)


class DIDResolver:
    """Resolves W3C DIDs to DID Documents."""

    def __init__(self) -> None:
        self._cache: dict[str, DIDDocument] = {}

    def resolve(self, did: str) -> DIDDocument:
        """Resolve a DID to its DID Document."""
        # Check cache
        if did in self._cache:
            return self._cache[did]

        # Determine method and resolve
        if did.startswith("did:key:"):
            doc = self._resolve_did_key(did)
        elif did.startswith("did:pkh:"):
            doc = self._resolve_did_pkh(did)
        else:
            raise ValueError(f"Unsupported DID method: {did}")

        # Cache and return
        self._cache[did] = doc
        return doc

    def _resolve_did_key(self, did: str) -> DIDDocument:
        """Resolve a did:key DID."""
        key_type, public_key_bytes = parse_did_key(did)

        # Create multibase encoding for the verification method
        multibase_str = did[8:]  # Remove "did:key:"
        vm_id = f"{did}#{multibase_str}"

        # Create verification method
        vm = VerificationMethod(
            id=vm_id,
            type=key_type,
            controller=did,
            public_key_multibase=multibase_str,
            public_key_jwk=multibase_to_jwk(multibase_str),
        )

        # Build DID Document
        doc = DIDDocument(
            id=did,
            verification_method=[vm],
            authentication=[vm_id],
            assertion_method=[vm_id],
            key_agreement=[vm_id] if key_type != "Ed25519VerificationKey2020" else [],
            capability_invocation=[vm_id],
            capability_delegation=[vm_id],
        )

        return doc

    def _resolve_did_pkh(self, did: str) -> DIDDocument:
        """Resolve a did:pkh DID."""
        chain_id, address, _ = parse_did_pkh(did)

        # For did:pkh, the verification method references the blockchain account
        vm_id = f"{did}#blockchain-account"

        vm = VerificationMethod(
            id=vm_id,
            type="EcdsaSecp256k1RecoveryMethod2020",
            controller=did,
            blockchain_account_id=f"eip155:{chain_id}:{address}",
        )

        doc = DIDDocument(
            id=did,
            verification_method=[vm],
            authentication=[vm_id],
            assertion_method=[vm_id],
            capability_invocation=[vm_id],
            capability_delegation=[vm_id],
        )

        return doc


def create_did_key_from_private_key(private_key_bytes: bytes, key_type: str = "ed25519") -> str:
    """Create a did:key from a private key."""
    if key_type == "ed25519":
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        # Encode as multibase (base58btc) - Ed25519 prefix is 0xed01
        multibase_bytes = b"\xed\x01" + public_bytes
        multibase_str = "z" + base58.b58encode(multibase_bytes).decode()
    elif key_type == "secp256k1":
        ec_private_key = ec.derive_private_key(
            int.from_bytes(private_key_bytes, "big"), ec.SECP256K1()
        )
        ec_public_key = ec_private_key.public_key()
        public_bytes = ec_public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        # secp256k1 prefix is 0xe701
        multibase_bytes = b"\xe7\x01" + public_bytes
        multibase_str = "z" + base58.b58encode(multibase_bytes).decode()
    else:
        raise ValueError(f"Unsupported key type: {key_type}")

    return f"did:key:{multibase_str}"
