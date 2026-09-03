# NPL-CANONICAL · Progress Ledger

> Canonical progress index for developers. This file tracks verified milestones reported by the canonical NPL build chain. It does **not** claim that every local ZIP/checkpoint is already pushed to GitHub. Code synchronization must be verified separately.

## Current canonical milestone

- Version: `0.13.0-context-intelligence-c11`
- Phase: `C11 · CONTEXT INTELLIGENCE · CONFLICTÓMETRO BRIDGE + PERSON×CONTEXT`
- Global progress ledger: `42/100`
- Tests: `659/659 PASS`
- Brain Gate: `FAIL` unchanged
- Brain Runtime: `FAIL` unchanged
- Conflictómetro Runtime: `NOT_CONNECTED`
- Latest local/checkpoint reported for C11: `3e14c21`

## Milestones

| Block | Canonical version | Main capability added | Reported total tests | Global progress |
|---|---|---|---:|---:|
| Foundation | `0.2.0-human-model-foundation1` | HSG, Event/Session, Evidence, Memory, Hypothesis, Uncertainty, Temporal, Profile, NBA contracts | 8 | — |
| C1 | `0.3.0-human-model-c1` | First real Experience → Evidence → HSG vertical slice | 20 | 16/100 |
| C2 | `0.4.0-human-model-c2` | Cross-experience + cross-context learning | 36 | 18/100 |
| C3 | `0.5.0-human-model-c3` | Generalization, longitudinal memory, semantic compaction | 60 | 21/100 |
| C4 | `0.6.0-human-model-c4` | Active Human Modeling: unknown → experiment → prediction → recalibration | 91 | 9/100* |
| C5 | `0.7.0-human-model-c5` | Explainable Profile + Living Worldline | 137 | 11/100 |
| C6 | `0.8.0-living-brain-c6` | Human Model ↔ Living Brain knowledge/overlay architecture | 194 | 14/100 |
| C7 | `0.9.0-experience-genome-c7` | Experience Genome + deterministic compiler | 267 | 18/100 |
| C8 | `0.10.0-adaptive-games-c8` | Adaptive Gameplay OS + advanced logical games | 339 | 24/100 |
| C9 | `0.11.0-goal-nof1-c9` | Goal Graph + N-of-1 + Personal Playbook | 429 | 30/100 |
| C10 | `0.12.0-social-intelligence-c10` | Intent-first Social Intelligence + fair exposure + Relationship Graph | 539 | 36/100 |
| C11 | `0.13.0-context-intelligence-c11` | Context Intelligence + Person×Context + Conflictómetro bridge contract | 659 | 42/100 |

\* Progress scoring contract changed around C4; do not interpret the temporary drop as a functional rollback.

## Architectural spine

NPL is being developed as one living, revisable human model rather than disconnected modules:

`Events → Observations → Evidence → HSG/Memory → Profile/Worldline → Active Selector → Experiences/Games → Goals/N-of-1 → Social → Context → back into evidence/model updates`

The canonical brain is a projection/navigation layer over evidence, exploration, uncertainty and longitudinal history. It is **not** a biological activation meter. Social matching is purpose-limited and must not expose the private Human Model. Context can contextualize or generate hypotheses but cannot write traits/diagnoses/identity.

## Current blockers intentionally not faked

- Local Three/Draco decoder runtime for the protected canonical `brain.glb` is still unresolved, so `BRAIN_RUNTIME=FAIL`.
- Conflictómetro adapter exists as a contract, but no real external runtime/data connection has been claimed.
- Final visual/product UI is not yet elevated; many advanced visual view-models and interaction contracts exist but need a dedicated integration/design pass.
- Production realtime, messaging, cloud scale and deployment are not yet elevated.

## Developer synchronization policy from now on

1. Preserve every canonical block and non-regression gate.
2. Keep this ledger updated at least every **10 canonical versions/major blocks**, and preferably at every major phase gate.
3. For each 10-version milestone, create a developer snapshot containing: canonical version, architecture delta, capability registry delta, tests/gates, known blockers, migrations, protected assets/hashes, and next phase.
4. Do not equate a local Git checkpoint reported by a build with a remote GitHub commit until the remote repository has been checked.
5. Prefer source-level commits/branches over replacing one opaque ZIP whenever the canonical source tree is available for sync.

## Next canonical direction

`C12 · MASTER VISUAL / PRODUCT INTEGRATION + CONNECTIVITY ORCHESTRATION`

C12 should not merely beautify screens. It should expose the already-built model as a coherent, highly interactive product and add a connectivity/orchestration layer so Profile, Worldline, Brain, Games, Goals, Social and Context behave as coordinated views/actions of the same underlying state. The design goal is brain-like coordination: distributed specialized systems, shared event/evidence substrate, selective routing, feedback loops, context-sensitive activation, and no single module pretending to be the whole system.
