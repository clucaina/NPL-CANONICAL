# NPL-CANONICAL · Progress Ledger

> Canonical developer-facing progress index. This file tracks verified milestone reports from the NPL build chain. It does **not** imply that a local ZIP/checkpoint has been pushed as source code; source synchronization is tracked separately.

## Current canonical milestone

- Version: `0.14.0-cognitive-fabric-c12`
- Phase: `C12 · COGNITIVE FABRIC + MASTER VISUAL / PRODUCT INTEGRATION`
- Global progress ledger: `50/100`
- Tests: `739/739 PASS`
- Visual QA: `PASS`
- Interaction QA: `PASS`
- Mobile QA: `PASS`
- Brain Gate: `FAIL` unchanged
- Brain Runtime: `FAIL` unchanged
- Conflictómetro Runtime: `NOT_CONNECTED`
- Production: `NOT_ELEVATED`
- Final visual: `NOT_CLAIMED`
- C12 source sync: `false` — local canonical checkpoint reported as `d62c506`; remote source tree not yet synchronized

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
| C12 | `0.14.0-cognitive-fabric-c12` | Cognitive Fabric, selective signal routing, real Product UI V1, cross-surface flows and visual/mobile QA | 739 | 50/100 |

\* Progress scoring contract changed around C4; do not interpret the temporary drop as a functional rollback.

## Architectural spine

NPL is one living, revisable human model rather than disconnected apps:

`Events → Observations → Evidence → HSG/Memory → Profile/Worldline → Active Selector → Experiences/Games → Goals/N-of-1 → Social → Context → governed feedback into evidence/model updates`

C12 adds a coordination layer over this spine: specialized systems exchange purpose-limited signals through a Cognitive Fabric rather than coupling directly. Routing is selective, privacy-aware and context-sensitive; accidental recursive loops are blocked. Profile, Worldline, Brain, Games, Goals, Social and Context now have a common shell, global focus and cross-surface navigation.

## C12 product state

- Real Product UI V1 exists for Home, Profile, Worldline, Brain shell, Games, Goals/Playbook, Social and Context.
- Home uses Profile constellation + Worldline + Routes as the protagonist while canonical Brain Runtime remains blocked; no pseudobrain is substituted.
- Profile is a human-map/constellation, not a score table.
- Worldline supports temporal scrub, before/after, filters and context overlay.
- Brain shell exposes the canonical 437-structure textual explorer/search/modes/inspector/routes/history while the compressed GLB runtime remains unproven.
- Games expose real multi-stage interaction but final premium game art remains pending.
- Social remains intent-first, finite and protected by the private Human Model firewall.
- Context remains Person / Context / Hypothesis separated; Conflictómetro real runtime is not connected.
- Eight required browser cross-surface flows passed without forced clicks.
- Sixteen browser screenshots (desktop/mobile) were manually inspected and visual regression baselines recorded.

## Current blockers intentionally not faked

- `BRAIN_RUNTIME=FAIL`: local Three/Draco runtime for the protected canonical `brain.glb` remains unresolved/unproven.
- `CONFLICTOMETRO_RUNTIME=NOT_CONNECTED`: adapter contract exists, real territorial runtime does not.
- Production/cloud/realtime/messaging are not elevated.
- Final premium visual/art direction is not claimed; C12 is `PRODUCT_UI_V1`, not final design.
- Remote GitHub still does not contain the C12 source tree/ZIP checkpoint; only developer-facing progress artifacts are being synchronized here until the canonical source/ZIP is supplied to this chat or pushed by the build environment.

## Developer synchronization policy

1. Preserve every canonical block and non-regression gate.
2. Update this ledger at every major phase gate.
3. At least every 10 canonical blocks/versions, publish a developer snapshot with architecture delta, capability delta, tests/gates, visual state, blockers, migrations, protected assets and next phase.
4. Never equate a local Git checkpoint with a remote GitHub commit until remote verification succeeds.
5. Prefer a visible source tree and normal commits over replacing one opaque ZIP whenever the canonical source tree is available.
6. Keep protected brain asset/hash contracts unchanged unless an explicit migration is reviewed.

## Next canonical direction

The build reports `C13 · PRODUCTION / CLOUD · Phase L`, but production should **not** become the sole priority yet. The recommended C13 scope is `PRODUCT INTELLIGENCE + BACKEND SCALE READINESS + VISUAL/INTERACTION DEEPENING`: harden persistence, selective recomputation, queues/caches/provider boundaries and observability while continuing to increase genuine user-facing interaction, design quality and connectivity. Production deployment may remain gated until the source tree, secrets, runtime blockers and release QA are available.
