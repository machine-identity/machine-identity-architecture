# Changelog

All notable changes to this project will be documented in this format.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with `src/`, `tests/`, `examples/`, `docs/`, `assets/`
- x402 handshake reference implementation (`src/x402_handshake/`)
  - Payment requirements, payloads, and verification types
  - Client and server implementations
  - Mock payment verifier for testing
- DID resolver reference implementation (`src/did_resolver/`)
  - DID Document, VerificationMethod, ServiceEndpoint types
  - `did:key` and `did:pkh` resolution
  - Signature verification against DID Documents
  - DID creation from private keys
- TEE attestation mock (`src/tee_attestation/`)
  - Attestation quote generation and verification
  - Mock measurements (MRENCLAVE, MRSIGNER)
  - Tamper and expiration detection
- Example scripts for all three implementations
- Comprehensive test suites for all modules
- CI/CD pipeline with linting, type checking, testing
- GitHub Actions workflow for releases and Zenodo deposition
- Documentation: README, paper, executive summary
- Citation files (CITATION.cff, machine_identity.bib)
- MIT License

## [0.1.0] - 2026-08-12

### Added
- Initial release with all reference implementations
- Paper: "The Architecture of Machine Identity: Sovereign Agents, Economic Autonomy, and the Future of AI Governance"
- Supplementary documents: pre-review summary, sovereign model detail, control layers analysis