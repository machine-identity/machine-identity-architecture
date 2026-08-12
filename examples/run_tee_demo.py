#!/usr/bin/env python3
"""
TEE Attestation Demo

Demonstrates mock TEE remote attestation quote generation and verification.
"""

import time

from tee_attestation import (
    AttestationQuote,
    QuoteGenerator,
    QuoteVerifier,
    create_mock_measurements,
)


def main():

    # Create mock measurements for agent code
    agent_code_hash = "sha256:agent-v1.0.0:main.py:dependencies.lock"
    signer_hash = "sha256:creator-key:ed25519:pubkey"

    mr_enclave, mr_signer = create_mock_measurements(agent_code_hash, signer_hash)


    # Create quote generator (simulates TEE hardware)
    generator = QuoteGenerator()

    # Agent generates attestation quote with report_data binding to its identity
    report_data = b"agent-did:key:z6MkpTHR...|task:data-analysis|nonce:abc123"

    quote = generator.generate_quote(
        mr_enclave=mr_enclave,
        mr_signer=mr_signer,
        report_data=report_data,
        isv_prod_id=1,
        isv_svn=1,
    )


    # Verifier checks the quote (simulates remote verifier)
    verifier = QuoteVerifier(trusted_signing_keys=[generator.signing_key])

    valid, message = verifier.verify(
        quote=quote,
        expected_mr_enclave=mr_enclave,
        expected_mr_signer=mr_signer,
        expected_report_data=report_data,
    )


    # Test tampering detection
    tampered_quote = AttestationQuote(
        version=quote.version,
        timestamp=quote.timestamp,
        tee_type=quote.tee_type,
        mr_enclave="tampered_" + quote.mr_enclave,  # Tampered!
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

    valid2, message2 = verifier.verify(
        quote=tampered_quote,
        expected_mr_enclave=mr_enclave,
        expected_mr_signer=mr_signer,
        expected_report_data=report_data,
    )


    # Test expired quote
    old_quote = AttestationQuote(
        version=quote.version,
        timestamp=int(time.time()) - 7200,  # 2 hours ago
        tee_type=quote.tee_type,
        mr_enclave=quote.mr_enclave,
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

    valid3, message3 = verifier.verify(
        quote=old_quote,
        expected_mr_enclave=mr_enclave,
        expected_mr_signer=mr_signer,
        expected_report_data=report_data,
        max_age_seconds=3600,  # 1 hour max age
    )




if __name__ == "__main__":
    main()
