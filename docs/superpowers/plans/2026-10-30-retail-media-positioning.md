# Retail Media Positioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the current sponsored-product simulator into a position-aware RL experiment that demonstrably balances advertiser value, shopper relevance, conversion, campaign delivery, and company CPC revenue.

**Architecture:** Keep the finite NumPy simulator and tabular Q-learning architecture. Extend the configuration with per-position commercial value and per-campaign conversion value, enrich the learned state with the sponsored position, and calculate a transparent scalar reward from conversion value, realized CPC revenue, delivery deficit, CVR loss, and premium-position concentration. Compare it with bid-only, relevance-only, rotation, and the existing policies on identical traffic.

**Tech Stack:** Python >=3.11, NumPy, unittest, JSON/CSV, standalone HTML.

**Spec:** `docs/superpowers/specs/2026-10-25-retail-media-design.md` plus the approved project direction in this conversation: position 1 remains organic; sponsored positions remain 3, 4, 5, 6, 11, 12, 13 and 14; prompt history is out of scope.

## Global Constraints

- Position 1 remains organic; do not add sponsored placement there.
- Retain exactly 20 products per block and eight sponsored slots: 3, 4, 5, 6, 11, 12, 13, 14.
- Monetary quantities use integer USD cents; existing CPC charging remains click-only and may never exceed budget.
- Preserve reproducible seeded traffic and strict separation between training and evaluation seeds.
- Do not add a dependency beyond NumPy or replace Q-learning with DQN/PPO.
- Preserve current artifacts until a new model is trained deliberately; model schema/version must reject incompatible legacy artifacts.
- Do not add or update the collaborative prompt-history deliverable.

## Review Focus

- A premium sponsored slot changes visibility and agent state but never permits position 1 sponsorship.
- A high-CPC campaign can lose a premium slot to a more relevant, higher expected-value campaign.
- A campaign with insufficient remaining budget is never selected even when it has the highest bid.
- Position-aware models cannot load an old position-agnostic model artifact.
- Evaluation compares policies on the same seed-level traffic and reports position distributions without mutating Q-values.

---

## File Structure

- `retail_media/config.py`: validates position metadata, campaign value fields, and a new model schema fingerprint.
- `retail_media/default_config.json`: declares the fixed sponsored positions and their commercial multipliers plus campaign economics.
- `retail_media/environment.py`: applies position effects, exposes position-aware state and records placement/value events.
- `retail_media/agent.py`: upgrades the persisted state schema and Q-state projection.
- `retail_media/experiment.py`: adds bid-only and rotation baselines, reward accounting, aggregation, and statistical comparisons.
- `retail_media/reporting.py`, `retail_media/report.html`: presents position allocation, CVR, CPC revenue, conversion value, delivery and trade-off examples.
- `tests/test_mvp.py`: covers each new contract using real simulator instances.
- `README.md`: explains the commercial objective, results, reproducibility, limitations and how to run the new experiment.

### Task 1: Configuration for commercial positions and campaign value

**Files:**
- Modify: `retail_media/config.py`
- Modify: `retail_media/default_config.json`
- Modify: `tests/test_mvp.py`

**Interfaces:**
- Produces: `Config.position_multipliers: tuple[float, ...]` aligned to `sponsored_slots`; each brand requires `conversion_value_cents: int`.
- Produces: `Config.position_multiplier(position: int) -> float` for valid sponsored positions.

- [ ] Write failing tests that a valid configuration returns the literal multiplier for positions 3 and 14, rejects missing/misaligned/nonpositive multipliers, and rejects an invalid campaign conversion value.
- [ ] Run `python -m unittest tests.test_mvp.EnvironmentTests` and confirm the new tests fail because the fields/method do not exist.
- [ ] Add the validated fields and lookup method to `Config`, preserving the current eight-slot constraint and fingerprinting campaign economics.
- [ ] Declare decreasing positive multipliers in `default_config.json` for slots 3, 4, 5, 6, 11, 12, 13 and 14, and conversion value in cents for every campaign.
- [ ] Run `python -m unittest discover -s tests -v` with `PYTHONUTF8=1` and confirm all tests pass.
- [ ] Commit: `feat: configure position and campaign value`.

### Task 2: Position-aware simulator events

**Files:**
- Modify: `retail_media/environment.py`
- Modify: `tests/test_mvp.py`

**Interfaces:**
- Consumes: `Config.position_multiplier(position)` and campaign `conversion_value_cents`.
- Produces: `RetailMediaEnv.state()` with a position feature; `step()` info includes `position_multiplier`, `cpc_revenue_cents`, and `conversion_value_cents`.

- [ ] Write failing tests showing slot 3 has higher sponsored visibility than slot 14 for the same product/draw and that event data records the configured multiplier and realized values.
- [ ] Run the focused test and confirm it fails because position metadata is absent.
- [ ] Apply the multiplier to sponsored visibility only, preserve organic position 1, and emit the event fields from real clicks/purchases.
- [ ] Add aggregate revenue and conversion-value metrics without changing click-only charging.
- [ ] Run the focused test and full suite with UTF-8; confirm green.
- [ ] Commit: `feat: simulate position-aware commercial outcomes`.

### Task 3: Position-aware Q-learning schema and reward

**Files:**
- Modify: `retail_media/agent.py`
- Modify: `retail_media/environment.py`
- Modify: `retail_media/experiment.py`
- Modify: `tests/test_mvp.py`

**Interfaces:**
- Produces: state projection `(intent, depth, sponsored_position_group)` and model schema `intent_depth_position_v3`.
- Produces: transparent reward components for conversion value, realized CPC revenue, delivery deficit and CVR guardrail.

- [ ] Write failing tests proving equivalent intent/depth at different sponsored position groups acquire independent Q-values and that loading a v2 artifact is rejected.
- [ ] Run the focused tests and confirm the legacy projection/schema causes the intended failure.
- [ ] Update state projection, artifact version/schema and Q-learning metadata; keep masking, pacing and epsilon-greedy behavior intact.
- [ ] Replace opaque reward constants with named, reported components while retaining terminal delivery penalty and CVR multiplier logic.
- [ ] Run full tests with UTF-8; train a small smoke model in a separate artifacts directory.
- [ ] Commit: `feat: learn position-aware campaign allocation`.

### Task 4: Baselines and decision proof

**Files:**
- Modify: `retail_media/experiment.py`
- Modify: `tests/test_mvp.py`

**Interfaces:**
- Produces policies `bid`, `rotation`, `relevance`, `organic`, `random`, `untrained`, and `rl`.
- Produces position-by-brand summary rows and a deterministic counterfactual trace.

- [ ] Write failing tests that bid-only chooses the highest valid CPC option, rotation changes eligible brands fairly, and all policies receive paired traffic per seed.
- [ ] Run focused tests and confirm policy names/selection behavior are absent.
- [ ] Implement selection and aggregate position/brand/revenue/conversion metrics.
- [ ] Add a deterministic trace assertion where a higher-CPC but irrelevant product loses to a relevant product under the value-aware policy.
- [ ] Run full tests and an independent seeded evaluation.
- [ ] Commit: `feat: compare position allocation policies`.

### Task 5: Report, README, retraining and delivery evidence

**Files:**
- Modify: `retail_media/reporting.py`
- Modify: `retail_media/report.html`
- Modify: `README.md`
- Modify: `tests/test_mvp.py`
- Regenerate: `artifacts/model.npz`, `artifacts/training.csv`, `artifacts/training.json`, `reports/evaluation.csv`, `reports/evaluation.json`, `reports/demo.html`

**Interfaces:**
- Consumes the Task 4 evaluation result.
- Produces a standalone report with position allocation and trade-off evidence.

- [ ] Write a failing report test requiring position distribution, CPC revenue, conversion value and an explanatory trace in generated standalone HTML.
- [ ] Run it and confirm current report lacks the data.
- [ ] Render the new metrics and explanatory allocation example; update README with objective, configuration, exact results and limitations.
- [ ] Train with final locked configuration, evaluate on held-out seeds, visually inspect `reports/demo.html`, and run full tests with UTF-8.
- [ ] Commit: `docs: report position-aware RL results`.

## Self-Review

- Configuration, simulation, policy representation, policy comparison, reporting and reproducible results each map to a task.
- The position-1 restriction, higher-bid counterexample, budget safety, artifact compatibility and paired evaluation each have an owning test.
- Prompt history, PDF, video and slides are explicitly excluded from this engineering increment.
