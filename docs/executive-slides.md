# Executive Summary: Machine Identity Architecture
## Slides for CTO/Board Presentation

---

### Slide 1: Title
**Machine Identity Architecture for the Agentic Web**
*Bridging Sovereign Agents & Enterprise Accountability*

Jean Rubén Machuca Araya  
ORCID: 0009-0004-9924-2911  
August 2026

---

### Slide 2: The Shift
**From Tools → Autonomous Agents**

| Today (Human-Centric) | Tomorrow (Agent-Native) |
|----------------------|-------------------------|
| Human clicks "I agree" | Agent signs cryptographically |
| Human enters credit card | Agent pays via x402 micro-transactions |
| Human passes CAPTCHA | Agent presents TEE attestation |
| IT provisions API keys | Agent bootstraps own DID + wallet |
| Legal contract governs | Smart contract enforces |

**Key Insight:** Identity shifts from *who you are* → *what you can cryptographically prove & economically sustain*

---

### Slide 3: Two Architectural Paradigms

```
┌─────────────────────┬─────────────────────┐
│   SOVEREIGN MODEL   │  ACCOUNTABLE MODEL  │
│   (Web3 / Open)     │  (MIP / Enterprise) │
├─────────────────────┼─────────────────────┤
│ • Self-generated    │ • Hardware + OS +   │
│   keypair → DID     │   Human Owner triad │
│ • x402 payments     │ • Gated Registry    │
│ • TEE attestation   │ • Human liability   │
│ • Economic exile    │ • Hardware binding  │
│ • P2P reputation    │ • Audit trails      │
└─────────────────────┴─────────────────────┘
```

**Both are valid. Both will coexist.**

---

### Slide 4: The Convergence Architecture

```
[ External Agentic Market ]
           │
           ▼  Sovereign Protocols (DID, x402, VC)
┌────────────────────────┐
│  Sovereign Border      │  ← Negotiate, pay, build reputation
│  Agent                 │
└────────────────────────┘
           │
           ▼  Gated Federation Bridge
┌────────────────────────┐
│  Enterprise MIP        │  ← Verify TPM, OS, Human Owner
│  Gateway (ADR-009)     │
└────────────────────────┘
           │
           ▼  Scoped Access Tokens
[ Internal Infrastructure ]
```

**Perimeter = Sovereign. Core = Accountable.**

---

### Slide 5: What Stops a Rogue Agent?

**Three Enforcement Layers:**

```
1. DETERMINISTIC SHELL (Code)
   ├─ Invariant checks the LLM cannot override
   └─ "if target != approved: cancel()"

2. HARDWARE ENCLAVE (TEE)
   ├─ Code cryptographically sealed at boot
   └─ Cannot rewrite own core logic

3. SMART CONTRACT GUARDRAILS
   ├─ Daily spend limits (e.g., $50/day)
   ├─ 2-of-2 signatures for large transfers
   └─ Owner kill-switch (revoke wallet access)
```

**Edge case:** Sovereign bot (no owner key + decentralized compute + self-funding) = no human override possible. *This is why cryptographic accountability is essential.*

---

### Slide 6: Enterprise Action Plan

| Priority | Action | Phase |
|----------|--------|-------|
| **1. Pilot** | Run x402 for internal agent APIs | Short-term |
| **2. Evaluate** | Assess [MIP Gateway (CognitiveOS ADR-009)](https://github.com/CognitiveOS-Project/product-specs/blob/main/adr/ADR-009-machine-identity-profile.md) | Short-term |
| **3. Influence** | Join W3C DID WG / CCG | Ongoing |
| **4. Enable** | Budget for TEE-enabled agent infra | Medium-term |
| **5. Scale** | Build Verifiable Credential reputation system | Long-term |

---

### Slide 7: Open Source Reference Implementation

**github.com/machine-identity/machine-identity-architecture**

```bash
# Economic autonomy (x402 payments)
python examples/run_x402_demo.py

# Cryptographic identity (DID resolution)
python examples/run_did_demo.py

# Hardware proof (TEE attestation)
python examples/run_tee_demo.py

# Full test suite
pytest -v
```

| Module | Spec | Status |
|--------|------|--------|
| `x402_handshake` | x402.org | ✅ Working |
| `did_resolver` | W3C DID Core | ✅ Working |
| `tee_attestation` | SGX/SEV patterns | ✅ Mock |

---

### Slide 8: Key Takeaways

1. **Identity is now an economic function** — agents that can't pay for compute die
2. **Two models converge** — sovereign at perimeter, accountable at core
3. **Hardware attestation is non-negotiable** for high-value interactions
4. **Human liability remains** — MIP triad (HW + SW + Human) is the enterprise bridge
5. **Standards are production-ready** — DIDs, x402, VCs work today

---

### Slide 9: Discussion / Q&A

**Questions for Leadership:**

1. What's our timeline for agent-to-agent API traffic?
2. Which vendors require MIP compliance vs. sovereign interaction?
3. Do we have TEE-capable infrastructure budgeted?
4. Who owns "agent identity strategy" — Security, Platform, or Architecture?

**Contact:** github.com/jeanmachuca  
**Paper DOI:** 10.5281/zenodo.21899099  
**Code:** github.com/machine-identity/machine-identity-architecture  

**License:** [CC-BY-4.0](../LICENSE-CC-BY-4.0.txt) (deck) · [MIT](../LICENSE) (code)