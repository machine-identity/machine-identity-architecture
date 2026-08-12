from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AttestationQuote:
    """Mock TEE attestation quote."""

    version: int = 1
    timestamp: int = field(default_factory=lambda: int(time.time()))
    tee_type: str = "mock"
    mr_enclave: str = ""  # Measurement of enclave code
    mr_signer: str = ""  # Measurement of signer
    rt_mr0: str = ""  # Runtime measurement register 0
    rt_mr1: str = ""  # Runtime measurement register 1
    rt_mr2: str = ""  # Runtime measurement register 2
    rt_mr3: str = ""  # Runtime measurement register 3
    report_data: bytes = b""  # User-defined data (64 bytes)
    isv_prod_id: int = 1
    isv_svn: int = 1
    signature: bytes = b""
    signing_cert: bytes = b""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "teeType": self.tee_type,
            "mrEnclave": self.mr_enclave,
            "mrSigner": self.mr_signer,
            "rtMr0": self.rt_mr0,
            "rtMr1": self.rt_mr1,
            "rtMr2": self.rt_mr2,
            "rtMr3": self.rt_mr3,
            "reportData": self.report_data.hex() if self.report_data else "",
            "isvProdId": self.isv_prod_id,
            "isvSvn": self.isv_svn,
            "signature": self.signature.hex() if self.signature else "",
            "signingCert": self.signing_cert.hex() if self.signing_cert else "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AttestationQuote:
        return cls(
            version=data.get("version", 1),
            timestamp=data.get("timestamp", int(time.time())),
            tee_type=data.get("teeType", "mock"),
            mr_enclave=data.get("mrEnclave", ""),
            mr_signer=data.get("mrSigner", ""),
            rt_mr0=data.get("rtMr0", ""),
            rt_mr1=data.get("rtMr1", ""),
            rt_mr2=data.get("rtMr2", ""),
            rt_mr3=data.get("rtMr3", ""),
            report_data=bytes.fromhex(data["reportData"]) if data.get("reportData") else b"",
            isv_prod_id=data.get("isvProdId", 1),
            isv_svn=data.get("isvSvn", 1),
            signature=bytes.fromhex(data["signature"]) if data.get("signature") else b"",
            signing_cert=bytes.fromhex(data["signingCert"]) if data.get("signingCert") else b"",
        )


class QuoteGenerator:
    """Generates mock TEE attestation quotes."""

    def __init__(self, signing_key: bytes | None = None):
        self.signing_key = signing_key or secrets.token_bytes(32)
        self._quote_counter = 0

    def generate_quote(
        self,
        mr_enclave: str,
        mr_signer: str,
        report_data: bytes,
        rt_mr0: str = "",
        rt_mr1: str = "",
        rt_mr2: str = "",
        rt_mr3: str = "",
        isv_prod_id: int = 1,
        isv_svn: int = 1,
    ) -> AttestationQuote:
        """Generate a mock attestation quote."""
        self._quote_counter += 1

        # Ensure report_data is exactly 64 bytes
        if len(report_data) > 64:
            report_data = report_data[:64]
        elif len(report_data) < 64:
            report_data = report_data.ljust(64, b"\x00")

        quote = AttestationQuote(
            version=1,
            timestamp=int(time.time()),
            tee_type="mock-sgx",
            mr_enclave=mr_enclave,
            mr_signer=mr_signer,
            rt_mr0=rt_mr0 or mr_enclave,
            rt_mr1=rt_mr1 or mr_signer,
            rt_mr2=rt_mr2,
            rt_mr3=rt_mr3,
            report_data=report_data,
            isv_prod_id=isv_prod_id,
            isv_svn=isv_svn,
        )

        # Sign the quote
        quote_data = self._quote_to_bytes(quote)
        quote.signature = hmac.new(self.signing_key, quote_data, hashlib.sha256).digest()
        quote.signing_cert = b"MOCK_CERT_" + self.signing_key[:16]

        return quote

    def _quote_to_bytes(self, quote: AttestationQuote) -> bytes:
        """Serialize quote for signing."""
        parts = [
            str(quote.version).encode(),
            str(quote.timestamp).encode(),
            quote.tee_type.encode(),
            quote.mr_enclave.encode(),
            quote.mr_signer.encode(),
            quote.rt_mr0.encode(),
            quote.rt_mr1.encode(),
            quote.rt_mr2.encode(),
            quote.rt_mr3.encode(),
            quote.report_data,
            str(quote.isv_prod_id).encode(),
            str(quote.isv_svn).encode(),
        ]
        return b"|".join(parts)


class QuoteVerifier:
    """Verifies TEE attestation quotes."""

    def __init__(self, trusted_signing_keys: list[bytes] | None = None):
        self.trusted_signing_keys = trusted_signing_keys or []

    def verify(
        self,
        quote: AttestationQuote,
        expected_mr_enclave: str | None = None,
        expected_mr_signer: str | None = None,
        expected_report_data: bytes | None = None,
        max_age_seconds: int = 3600,
    ) -> tuple[bool, str]:
        """
        Verify an attestation quote.
        Returns (is_valid, error_message).
        """
        # Check timestamp
        now = int(time.time())
        if quote.timestamp < now - max_age_seconds:
            return False, f"Quote expired (age: {now - quote.timestamp}s > {max_age_seconds}s)"

        # Check mr_enclave
        if expected_mr_enclave and quote.mr_enclave != expected_mr_enclave:
            return False, (
                f"MRENCLAVE mismatch: expected {expected_mr_enclave}, got {quote.mr_enclave}"
            )

        # Check mr_signer
        if expected_mr_signer and quote.mr_signer != expected_mr_signer:
            return False, (
                f"MRSIGNER mismatch: expected {expected_mr_signer}, got {quote.mr_signer}"
            )

        # Check report_data
        if expected_report_data:
            expected = expected_report_data.ljust(64, b"\x00")[:64]
            if quote.report_data != expected:
                return False, "REPORT_DATA mismatch"

        # Verify signature
        if not self._verify_signature(quote):
            return False, "Invalid quote signature"

        return True, "Valid"

    def _verify_signature(self, quote: AttestationQuote) -> bool:
        """Verify the quote signature against trusted keys."""
        quote_data = self._quote_to_bytes(quote)
        expected_sig = hmac.new(
            self.trusted_signing_keys[0] if self.trusted_signing_keys else b"default_key",
            quote_data,
            hashlib.sha256,
        ).digest()
        return hmac.compare_digest(quote.signature, expected_sig)

    def _quote_to_bytes(self, quote: AttestationQuote) -> bytes:
        parts = [
            str(quote.version).encode(),
            str(quote.timestamp).encode(),
            quote.tee_type.encode(),
            quote.mr_enclave.encode(),
            quote.mr_signer.encode(),
            quote.rt_mr0.encode(),
            quote.rt_mr1.encode(),
            quote.rt_mr2.encode(),
            quote.rt_mr3.encode(),
            quote.report_data,
            str(quote.isv_prod_id).encode(),
            str(quote.isv_svn).encode(),
        ]
        return b"|".join(parts)


def create_mock_measurements(code_hash: str, signer_hash: str) -> tuple[str, str]:
    """Create mock MRENCLAVE and MRSIGNER from code and signer hashes."""
    mr_enclave = hashlib.sha256(code_hash.encode()).hexdigest()
    mr_signer = hashlib.sha256(signer_hash.encode()).hexdigest()
    return mr_enclave, mr_signer
