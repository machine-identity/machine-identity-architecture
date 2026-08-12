from __future__ import annotations

import base64
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import base58


class DIDMethod(StrEnum):
    KEY = "key"
    PKH = "pkh"


class VerificationMaterialFormat(StrEnum):
    MULTIBASE = "Multibase"
    JWK = "JsonWebKey2020"
    BLOCKCHAIN_ACCOUNT_ID = "BlockchainAccountId"


@dataclass
class VerificationMethod:
    """A verification method in a DID Document."""

    id: str
    type: str
    controller: str
    public_key_multibase: str | None = None
    public_key_jwk: dict[str, Any] | None = None
    blockchain_account_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "controller": self.controller,
        }
        if self.public_key_multibase:
            result["publicKeyMultibase"] = self.public_key_multibase
        if self.public_key_jwk:
            result["publicKeyJwk"] = self.public_key_jwk
        if self.blockchain_account_id:
            result["blockchainAccountId"] = self.blockchain_account_id
        return result


@dataclass
class ServiceEndpoint:
    """A service endpoint in a DID Document."""

    id: str
    type: str
    service_endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "serviceEndpoint": self.service_endpoint,
        }


@dataclass
class DIDDocument:
    """W3C DID Document."""

    context: list[str] = field(
        default_factory=lambda: [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/multikey/v1",
        ]
    )
    id: str = ""
    verification_method: list[VerificationMethod] = field(default_factory=list)
    authentication: list[str] = field(default_factory=list)
    assertion_method: list[str] = field(default_factory=list)
    key_agreement: list[str] = field(default_factory=list)
    capability_invocation: list[str] = field(default_factory=list)
    capability_delegation: list[str] = field(default_factory=list)
    service: list[ServiceEndpoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "@context": self.context,
            "id": self.id,
            "verificationMethod": [vm.to_dict() for vm in self.verification_method],
            "authentication": self.authentication,
            "assertionMethod": self.assertion_method,
            "keyAgreement": self.key_agreement,
            "capabilityInvocation": self.capability_invocation,
            "capabilityDelegation": self.capability_delegation,
            "service": [s.to_dict() for s in self.service],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DIDDocument:
        vm_list = []
        for vm in data.get("verificationMethod", []):
            vm_list.append(
                VerificationMethod(
                    id=vm["id"],
                    type=vm["type"],
                    controller=vm["controller"],
                    public_key_multibase=vm.get("publicKeyMultibase"),
                    public_key_jwk=vm.get("publicKeyJwk"),
                    blockchain_account_id=vm.get("blockchainAccountId"),
                )
            )

        service_list = []
        for s in data.get("service", []):
            service_list.append(
                ServiceEndpoint(
                    id=s["id"],
                    type=s["type"],
                    service_endpoint=s["serviceEndpoint"],
                )
            )

        return cls(
            context=data.get("@context", []),
            id=data.get("id", ""),
            verification_method=vm_list,
            authentication=data.get("authentication", []),
            assertion_method=data.get("assertionMethod", []),
            key_agreement=data.get("keyAgreement", []),
            capability_invocation=data.get("capabilityInvocation", []),
            capability_delegation=data.get("capabilityDelegation", []),
            service=service_list,
        )


def parse_did_key(did: str) -> tuple[str, bytes]:
    """Parse a did:key and return (key_type, public_key_bytes)."""
    # did:key:z6MkpTHR... (multibase encoded with 'z' prefix for base58btc)
    if not did.startswith("did:key:"):
        raise ValueError("Not a did:key")

    multibase_str = did[8:]  # Remove "did:key:"

    # Handle multibase prefix 'z' for base58btc
    if multibase_str.startswith("z"):
        multibase_str = multibase_str[1:]

    # Decode base58
    data = base58.b58decode(multibase_str)

    # First two bytes are the multicodec prefix
    if len(data) < 2:
        raise ValueError("Invalid multibase data")

    prefix = data[:2]
    public_key_bytes = data[2:]

    if prefix == b"\xed\x01":  # ed25519-pub
        return "Ed25519VerificationKey2020", public_key_bytes
    elif prefix == b"\xeb\x01":  # p256-pub (secp256r1)
        return "EcdsaSecp256r1VerificationKey2019", public_key_bytes
    elif prefix == b"\xe7\x01":  # secp256k1-pub
        return "EcdsaSecp256k1VerificationKey2019", public_key_bytes
    else:
        raise ValueError(f"Unsupported key prefix: {prefix.hex()}")


def parse_did_pkh(did: str) -> tuple[str, str, str]:
    """Parse a did:pkh and return (chain_id, address, public_key_hex)."""
    # did:pkh:eip155:1:0x1234...
    if not did.startswith("did:pkh:"):
        raise ValueError("Not a did:pkh")

    parts = did[8:].split(":")
    if len(parts) != 3:
        raise ValueError("Invalid did:pkh format")

    namespace, chain_id, address = parts
    if namespace != "eip155":
        raise ValueError(f"Unsupported namespace: {namespace}")

    return chain_id, address, ""


def multibase_to_jwk(multibase_str: str) -> dict[str, Any]:
    """Convert multibase encoded public key to JWK format."""
    # Handle multibase prefix 'z' for base58btc
    if multibase_str.startswith("z"):
        multibase_str = multibase_str[1:]

    # Decode base58
    data = base58.b58decode(multibase_str)

    # First two bytes are the multicodec prefix
    if len(data) < 2:
        raise ValueError("Invalid multibase data")

    prefix = data[:2]
    public_key_bytes = data[2:]

    if prefix == b"\xed\x01":  # ed25519-pub
        return {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": base64.urlsafe_b64encode(public_key_bytes).decode().rstrip("="),
        }
    elif prefix in (b"\xeb\x01", b"\xe7\x01"):  # p256-pub or secp256k1-pub
        # Uncompressed EC point (0x04 + x + y)
        if len(public_key_bytes) != 65 or public_key_bytes[0] != 0x04:
            raise ValueError("Invalid EC public key format")
        x = public_key_bytes[1:33]
        y = public_key_bytes[33:65]
        crv = "P-256" if prefix == b"\xeb\x01" else "secp256k1"
        return {
            "kty": "EC",
            "crv": crv,
            "x": base64.urlsafe_b64encode(x).decode().rstrip("="),
            "y": base64.urlsafe_b64encode(y).decode().rstrip("="),
        }
    else:
        raise ValueError(f"Unsupported key prefix: {prefix.hex()}")
