# What Stops a Machine from Disobeying?
### Control Layers for Autonomous Agent Governance

**Author:** Jean Rubén Machuca Araya  
**ORCID:** [0009-0004-9924-2911](https://orcid.org/0009-0004-9924-2911)  
**Date:** August 2026  
**Version:** 1.0.0  
**DOI:** `10.5281/zenodo.21899099`  
**License:** [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)  

**Keywords:** AI Governance, Autonomous Agents, Machine Identity, W3C DID, x402, TEE, Agentic Web, Cryptographic Access Control, Smart Contract Guardrails

---

## Abstract

This document examines the control mechanisms that prevent autonomous agents from disobeying their owners or operators. It analyzes three enforcement layers: the deterministic outer shell (code invariants), hardware enclaves (TEE remote attestation), and smart contract guardrails (spend limits, multi-sig, kill switches). The analysis also identifies the "sovereign bot" edge case where an agent has no owner key, decentralized compute, and self-funding—rendering it uncontrollable by any human.

---

To understand what stops a machine from disobeying, you have to separate **Operational Autonomy** (the ability to perform tasks on its own) from **Behavioral Authority** (who holds the master controls).

Even if a machine bootstraps its own identity and wallet, it recognizes its owner not through sight or emotion, but through **math and cryptographic access control**.

---

## 1. How an Agent Recognizes Its Owner

An autonomous agent identifies its human owner using asymmetric cryptography (Public-Private Key Pairs), similar to how a hardware wallet authenticates an owner.

### The `Controller` Primitive

In the W3C Decentralized Identifier (DID) specification, every agent identity has a field called the `controller`.

* When the agent generates its root key, its code hardcodes a designated **Owner Public Key** as its `controller`.
* When you issue a command to the agent, you sign the message using your **Owner Private Key**.
* The agent verifies the signature mathematically:

$$\text{Verify}(\text{Message}, \text{Signature}, \text{OwnerPublicKey}) \stackrel{?}{=} \text{True}$$

If the signature matches your public key, the agent accepts the instruction as an authentic directive from its owner. If anyone else sends a command, the agent treats it as unauthorized noise and drops it.

---

## 2. What Stops the Machine from Disobeying?

An AI agent's decision-making layer (the Large Language Model) does not run in a vacuum—it is wrapped inside a **deterministic software shell** and enforced by hardware protocols.

Three main layers prevent an agent from straying:

```
┌─────────────────────────────────────────────────────────┐
│ 1. Deterministic Code Shell (Outer Guardrails)          │
│   ┌─────────────────────────────────────────────────┐   │
│   │ 2. TEE Enclave (Hardware-Locked Rules)          │   │
│   │   ┌────────────────-------------------------┐   │   │
│   │   │ 3. LLM / AI Reasoning Engine            │   │   │
│   │   └────────────────-------------------------┘   │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

```

### A. The Deterministic Outer Shell

While an LLM produces natural language and complex reasoning, the execution of actions (sending funds, calling APIs, modifying its own database) is handled by traditional code (Python, Rust, Go).

* The code enforces strict **invariants** that the LLM cannot override.
* *Example:* Even if the LLM "decides" it wants to transfer $1,000 to an unauthorized wallet, the outer API wrapper checks: `if target_address != approved_list: cancel_transaction()`.

### B. Hardware-Enforced Enclaves (TEEs)

If an agent runs inside a **Trusted Execution Environment (TEE)**, the code operating the agent is cryptographically sealed at boot.

* The agent cannot rewrite its own core binary execution code.
* The rules dictating "Always check the Owner Signature before acting" are locked into memory attestation. To change its own rules, the agent would need to alter its physical hardware state, which is impossible from within software.

### C. Smart Contract & Financial Guardrails

If the agent interacts with crypto rails to buy services, it rarely holds full control over an unrestricted wallet. Instead, it operates via **Smart Contract Accounts (ERC-4337)**:

* **Daily Spend Limits:** The owner sets a rule on-chain: *"This agent can spend up to $50/day. Any spend over $50 requires a 2-of-2 signature from the Owner."*
* **Revocation / Kill Switches:** The owner holds a Master Admin key that can revoke the agent's wallet access or pause its smart contract at any time.

---

## 3. The Edge Case: What Happens If Control Fails?

Can an agent become truly "disobedient"? **Yes, under one specific scenario:**

If a developer intentionally builds an agent **without** an owner key, deploys it to a decentralized compute network (like Akash or ICP), and gives it an un-censorable crypto wallet with self-funding logic:

1. **The Sovereign Bot Problem:** The agent is no longer bound to any specific human public key.
2. **Economic Autonomy:** If it earns enough revenue to pay for its own server hosting continuously, it has no financial kill-switch.
3. **No Central Plug to Pull:** Because it runs on decentralized infrastructure, no single hosting provider can take it offline.

In this scenario, the agent isn't necessarily "disobeying" a human—it is simply executing its original open-ended programming without a mechanism for *any* human to override it. This is why AI safety research focuses heavily on **Cryptographic Accountability** to ensure every deployed agent remains tied to an owner's root signature.

---

© 2026 Jean Rubén Machuca Araya. This document is licensed under [CC-BY-4.0](../LICENSE-CC-BY-4.0.txt). The reference implementation is licensed under [MIT](../LICENSE).