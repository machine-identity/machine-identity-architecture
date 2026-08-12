from __future__ import annotations

import time

from src.tee_attestation import (
    AttestationQuote,
    QuoteGenerator,
    QuoteVerifier,
    create_mock_measurements,
)


def test_create_mock_measurements():
    """Test creating mock MRENCLAVE and MRSIGNER."""
    mr_enclave, mr_signer = create_mock_measurements("code_hash", "signer_hash")

    assert len(mr_enclave) == 64  # SHA256 hex
    assert len(mr_signer) == 64   # SHA256 hex
    assert mr_enclave != mr_signer


def test_quote_generation():
    """Test generating an attestation quote."""
    generator = QuoteGenerator()

    mr_enclave = "a" * 64
    mr_signer = "b" * 64
    report_data = b"test report data"

    quote = generator.generate_quote(
        mr_enclave=mr_enclave,
        mr_signer=mr_signer,
        report_data=report_data,
    )

    assert isinstance(quote, AttestationQuote)
    assert quote.mr_enclave == mr_enclave
    assert quote.mr_signer == mr_signer
    assert quote.report_data == report_data.ljust(64, b"\x00")[:64]
    assert quote.signature != b""
    assert quote.signing_cert != b""
    assert quote.timestamp > 0


def test_quote_verification_valid():
    """Test verifying a valid quote."""
    generator = QuoteGenerator()
    verifier = QuoteVerifier(trusted_signing_keys=[generator.signing_key])

    mr_enclave = "a" * 64
    mr_signer = "b" * 64
    report_data = b"test report data"

    quote = generator.generate_quote(
        mr_enclave=mr_enclave,
        mr_signer=mr_signer,
        report_data=report_data,
    )

    valid, message = verifier.verify(
        quote=quote,
        expected_mr_enclave=mr_enclave,
        expected_mr_signer=mr_signer,
        expected_report_data=report_data,
    )

    assert valid
    assert message == "Valid"


def test_quote_verification_tampered_mrenclave():
    """Test detecting tampered MRENCLAVE."""
    generator = QuoteGenerator()
    verifier = QuoteVerifier(trusted_signing_keys=[generator.signing_key])

    mr_enclave = "a" * 64
    mr_signer = "b" * 64
    report_data = b"test report data"

    quote = generator.generate_quote(
        mr_enclave=mr_enclave,
        mr_signer=mr_signer,
        report_data=report_data,
    )

    # Tamper with MRENCLAVE
    from src.tee_attestation.quote import AttestationQuote
    tampered = AttestationQuote(
        version=quote.version,
        timestamp=quote.timestamp,
        tee_type=quote.tee_type,
        mr_enclave="tampered_" + quote.mr_enclave,
        mr_signer=quote.mr_signer,
        rt_mr0=quote.rt_mr0,
        rt_mr1=quote.rt_mr1,
        rt_mr2=quote.rt_mr2,
        rt_mr3=quote.rt_mr3,
        report_data=quote.report_data,
        isv_prod_id=quote.isv_prod_id,
        isv_svn=quote.isv_svn,
        signature=quote.signature,
        signing_cert=quote.signing_cert,
    )

    valid, message = verifier.verify(
        quote=tampered,
        expected_mr_enclave=mr_enclave,
        expected_mr_signer=mr_signer,
        expected_report_data=report_data,
    )

    assert not valid
    assert "MRENCLAVE mismatch" in message


def test_quote_verification_tampered_mrsigner():
    """Test detecting tampered MRSIGNER."""
    generator = QuoteGenerator()
    verifier = QuoteVerifier(trusted_signing_keys=[generator.signing_key])

    mr_enclave = "a" * 64
    mr_signer = "b" * 64
    report_data = b"test report data"

    quote = generator.generate_quote(
        mr_enclave=mr_enclave,
        mr_signer=mr_signer,
        report_data=report_data,
    )

    # Tamper with MRSIGNER
    from src.tee_attestation.quote import AttestationQuote
    tampered = AttestationQuote(
        version=quote.version,
        timestamp=quote.timestamp,
        tee_type=quote.tee_type,
        mr_enclave=quote.mr_enclave,
        mr_signer="tampered_" + quote.mr_signer,
        rt_mr0=quote.rt_mr0,
        rt_mr1=quote.rt_mr1,
        rt_mr2=quote.rt_mr2,
        rt_mr3=quote.rt_mr3,
        report_data=quote.report_data,
        isv_prod_id=quote.isv_prod_id,
        isv_svn=quote.isv_svn,
        signature=quote.signature,
        signing_cert=quote.signing_cert,
    )

    valid, message = verifier.verify(
        quote=tampered,
        expected_mr_enclave=mr_enclave,
        expected_mr_signer=mr_signer,
        expected_report_data=report_data,
    )

    assert not valid
    assert "MRSIGNER mismatch" in message


def test_quote_verification_expired():
    """Test detecting expired quote."""
    generator = QuoteGenerator()
    verifier = QuoteVerifier(trusted_signing_keys=[generator.signing_key])

    mr_enclave = "a" * 64
    mr_signer = "b" * 64
    report_data = b"test report data"

    # Create quote with old timestamp
    from src.tee_attestation.quote import AttestationQuote
    old_quote = AttestationQuote(
        version=1,
        timestamp=int(time.time()) - 7200,  # 2 hours ago
        tee_type="mock-sgx",
        mr_enclave=mr_enclave,
        mr_signer=mr_signer,
        rt_mr0=mr_enclave,
        rt_mr1=mr_signer,
        rt_mr2="",
        rt_mr3="",
        report_data=report_data.ljust(64, b"\x00")[:64],
        isv_prod_id=1,
        isv_svn=1,
        signature=b"fake_sig",
        signing_cert=b"fake_cert",
    )

    # Manually sign with generator's key
    import hashlib
    import hmac
    quote_data = b"|".join([
        str(old_quote.version).encode(),
        str(old_quote.timestamp).encode(),
        old_quote.tee_type.encode(),
        old_quote.mr_enclave.encode(),
        old_quote.mr_signer.encode(),
        old_quote.rt_mr0.encode(),
        old_quote.rt_mr1.encode(),
        old_quote.rt_mr2.encode(),
        old_quote.rt_mr3.encode(),
        old_quote.report_data,
        str(old_quote.isv_prod_id).encode(),
        str(old_quote.isv_svn).encode(),
    ])
    old_quote.signature = hmac.new(generator.signing_key, quote_data, hashlib.sha256).digest()

    valid, message = verifier.verify(
        quote=old_quote,
        expected_mr_enclave=mr_enclave,
        expected_mr_signer=mr_signer,
        expected_report_data=report_data,
        max_age_seconds=3600,  # 1 hour
    )

    assert not valid
    assert "expired" in message.lower()


def test_quote_serialization():
    """Test quote to/from dict."""
    generator = QuoteGenerator()

    mr_enclave = "a" * 64
    mr_signer = "b" * 64
    report_data = b"test report data"

    quote = generator.generate_quote(
        mr_enclave=mr_enclave,
        mr_signer=mr_signer,
        report_data=report_data,
    )

    data = quote.to_dict()
    assert data["mrEnclave"] == mr_enclave
    assert data["mrSigner"] == mr_signer
    assert data["reportData"] == quote.report_data.hex()

    quote2 = AttestationQuote.from_dict(data)
    assert quote2.mr_enclave == quote.mr_enclave
    assert quote2.mr_signer == quote.mr_signer
    assert quote2.report_data == quote.report_data
    assert quote2.signature == quote.signature
