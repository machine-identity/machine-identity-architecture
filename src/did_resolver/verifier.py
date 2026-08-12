from __future__ import annotations

import base58
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from .types import DIDDocument, VerificationMethod


class DIDVerifier:
    """Verifies signatures against DID Documents."""

    def verify_signature(
        self,
        did_doc: DIDDocument,
        message: bytes,
        signature: bytes,
        verification_method_id: str,
    ) -> bool:
        """Verify a signature using a verification method from a DID Document."""
        # Find the verification method
        vm = self._get_verification_method(did_doc, verification_method_id)
        if not vm:
            return False

        # Get public key
        public_key = self._get_public_key(vm)
        if not public_key:
            return False

        # Verify based on key type
        if isinstance(public_key, ed25519.Ed25519PublicKey):
            return self._verify_ed25519(public_key, message, signature)
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            return self._verify_ecdsa(public_key, message, signature)
        else:
            return False

    def _get_verification_method(
        self,
        did_doc: DIDDocument,
        verification_method_id: str,
    ) -> VerificationMethod | None:
        for vm in did_doc.verification_method:
            if vm.id == verification_method_id:
                return vm
        return None

    def _get_public_key(self, vm: VerificationMethod):
        """Extract public key from verification method."""
        if vm.public_key_multibase:
            multibase_str = vm.public_key_multibase
            # Handle multibase prefix 'z' for base58btc
            if multibase_str.startswith('z'):
                multibase_str = multibase_str[1:]

            # Decode base58
            data = base58.b58decode(multibase_str)

            # First two bytes are the multicodec prefix
            if len(data) < 2:
                return None

            prefix = data[:2]
            public_key_bytes = data[2:]

            if prefix == b"\xed\x01":  # ed25519-pub
                return ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            elif prefix == b"\xeb\x01":  # p256-pub (secp256r1)
                if len(public_key_bytes) != 65 or public_key_bytes[0] != 0x04:
                    return None
                return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), public_key_bytes)
            elif prefix == b"\xe7\x01":  # secp256k1-pub
                if len(public_key_bytes) != 65 or public_key_bytes[0] != 0x04:
                    return None
                return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
        return None

    def _verify_ed25519(
        self,
        public_key: ed25519.Ed25519PublicKey,
        message: bytes,
        signature: bytes,
    ) -> bool:
        try:
            public_key.verify(signature, message)
            return True
        except InvalidSignature:
            return False

    def _verify_ecdsa(
        self,
        public_key: ec.EllipticCurvePublicKey,
        message: bytes,
        signature: bytes,
    ) -> bool:
        try:
            # Handle both raw (r||s) and DER-encoded signatures
            if len(signature) == 64:
                # Raw r||s format
                r = int.from_bytes(signature[:32], "big")
                s = int.from_bytes(signature[32:], "big")
                der_sig = self._encode_dss_signature(r, s)
            else:
                # Assume DER format
                der_sig = signature

            public_key.verify(der_sig, message, ec.ECDSA(hashes.SHA256()))
            return True
        except (InvalidSignature, ValueError):
            return False

    def _encode_dss_signature(self, r: int, s: int) -> bytes:
        from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
        return encode_dss_signature(r, s)

    def verify_challenge_response(
        self,
        did_doc: DIDDocument,
        challenge: bytes,
        response: bytes,
        verification_method_id: str,
    ) -> bool:
        """Verify a challenge-response authentication."""
        return self.verify_signature(did_doc, challenge, response, verification_method_id)
