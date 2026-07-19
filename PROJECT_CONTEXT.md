# Project Context — Cybersecurity Threat Detection Platform

Paste this whole document into GitHub Copilot Chat (or your IDE's AI context)
before asking it to make changes. It explains what exists, why it's built the
way it is, and which parts are load-bearing so nothing gets "helpfully" broken.

## What this project is

A 4-module cybersecurity threat detection platform, built module-by-module,
each one depending on the previous ones' real outputs (not mocked/stubbed).

- **Module 1** — Statistical anomaly detection on network traffic.
  IsolationForest + OneClassSVM ensemble on 8 engineered features. Outputs
  `anomaly_score` (0-100) and `predict_network_anomaly(df)`.
- **Module 2** — Phishing/content detection + Bayesian risk fusion.
  TF-IDF + LightGBM (beat Naive Bayes in a real comparison) across 5
  channels (email/sms/url/login_attempt/api_payload). Outputs
  `phishing_probability` via `predict_phishing()`, and fuses it with
  Module 1's `anomaly_score` via `bayesian_risk_adjustment()` (real Bayes'
  rule in log-odds space, not a weighted average) into
  `final_risk_probability`.
- **Module 3** — Explainable AI dashboard (Streamlit + Plotly + SHAP + LIME).
  3 pages (Threat Overview, Explainability, Threat Explorer). SHAP runs on a
  surrogate LightGBM model (not Module 1's actual ensemble — see "Key
  decisions" below for why). Outputs `generate_xai_report()`.
- **Module 4** — SOC assistant orchestrator. Wires all 3 modules into one
  pipeline (`main.py`), and generates a full incident-response playbook via
  `generate_response_playbook()` — but **only** when
  `final_risk_probability > 70`; otherwise returns the literal string
  `"No response required."` and just logs the event.

Each module lives in its own folder (`module1/`, `module2/`, `module3/`,
`module4/`), each with its own `src/`, `data/`, `models/`, and `README.md`.
All 4 module folders sit side by side in the same parent directory — the
cross-module code depends on that exact layout.

## Critical architectural constraint — DO NOT let Copilot "fix" this

**Every module has its own `src/utils.py`, and Modules 1 and 2 both have
`src/predict.py`.** This is deliberate, not duplication to clean up. If you
import more than one module's source directory into the same Python
process, Python's `sys.modules` cache serves whichever `utils`/`predict`
loaded first to *every* subsequent `from utils import ...` call, anywhere —
silently feeding one module's code with another module's internals. This
was discovered and fixed during Module 2's build (confirmed via a debugging
session where AUC mysteriously dropped to ~0.50 — random — due to exactly
this bug), and the fix was reused in Modules 3 and 4.

**The fix:** every cross-module call goes through an isolated subprocess
(see `module_bridge.py` / `module_bridge.py`-equivalent in each later
module). Data is exchanged via temp JSON files, not stdout or CLI args
(stdout carries logging noise; CLI args hit OS length limits on large
batches). The one exception: pickled sklearn/lightgbm model artifacts are
safe to load directly via `joblib.load()` across modules, since unpickling
a plain model object doesn't execute the source module's `utils.py`.

**If you ask Copilot to refactor, merge utils files, or "reduce
duplication" across modules, it will very likely reintroduce this bug.**
Tell it explicitly not to touch the subprocess-bridge pattern, or scope its
context to one module at a time.

## Key decisions worth knowing before you change anything

- **Module 1's risk bands (Low/Medium/High) and Module 2's (Low/Medium/
  Critical) are different scales, calibrated differently.** Module 1's
  cutoffs (25/55) were empirically derived from its actual score
  distribution. Module 2's cutoffs (40/70) are fixed per the original spec.
  They are not directly comparable — don't merge them into one scale
  without re-deriving.
- **Module 3 explains a surrogate model, not Module 1's real ensemble.**
  `shap` has no native support for OneClassSVM at all, and partial/fragile
  support for sklearn's IsolationForest. Module 3 trains its own LightGBM
  surrogate on Module 1's `processed_features` to predict the same
  ground-truth label, and reports its own fidelity (verified: AUC 0.9999,
  Accuracy 99.6% vs. Module 1's real labels) so it's never presented as if
  it WERE Module 1's actual model. If you touch Module 1's feature
  engineering, the surrogate needs retraining (`build_dataset.py` then
  `xai_engine.py`'s `train_surrogate_model()`).
- **Module 3's `generate_xai_report()` was extended, not renamed**, with an
  optional `live_event` parameter so Module 4 could explain brand-new
  events (not just static dataset rows). Backward compatible — verified.
- **Module 4's LLM narrative sections are template-gated on purpose.**
  YARA/Snort/Sigma rules, MITRE mapping, CVE suggestions, and all commands
  come from a curated, deterministic knowledge base
  (`threat_intel.py`) — never from the LLM. A hallucinated CVE ID or a
  syntactically broken detection rule is worse than none. The generated
  YARA rule was verified to actually *compile* with a real YARA engine; the
  Sigma rule was verified to parse as valid YAML. If you expand the
  CVE/MITRE tables, fact-check every ID against a real source before adding
  it — don't let Copilot autocomplete plausible-looking CVE numbers.
- **The `final_risk_probability > 70` gate is enforced twice, redundantly**
  — once in `main.py` before it even calls the playbook generator, and
  again *inside* `generate_response_playbook()` itself (raises
  `ValueError` if violated). This redundancy is intentional so the gate
  can't be silently bypassed by a future caller. Keep both checks if you
  refactor.
- **No live LLM call was ever tested** — no `GEMINI_API_KEY` was
  available during development. Everything except the actual live API
  round-trip was verified (mock mode, missing-key error path, REST
  response-parsing logic against the real Gemini response shape). **Test this
  for real, with a real key from https://aistudio.google.com/apikey, before
  demo day** — it's the one path in the whole project that's unverified.

## Known, documented limitations (already written up, not hidden)

- Module 1: `packet_entropy` and `packet_std` contribute near-zero signal
  (verified via permutation importance AND independently reconfirmed by
  Module 3's SHAP analysis — two separate methods agreeing).
  Rolling per-source_ip features degrade to window-size-1 on
  shuffled/non-contiguous batches (documented operational caveat, verified
  to reproduce exactly as predicted in Module 3's dataset).
- Module 2: the Bayesian fusion layer needed a `shrinkage` correction after
  validation showed the raw formula was overconfident (a documented,
  known naive-Bayes pathology, not a bug unique to this code) — default
  `shrinkage=0.5`, fittable via `calibrate_shrinkage()` against real labeled
  data.
- Module 2/3: the synthetic phishing dataset needed two passes — the first
  draft hit 1.0000 accuracy, which is a red flag (too easy), not a win.
  Fixed by adding "hard negative"/"hard positive" examples.
- Module 4: `classify_threat_category()` is a small, coarse, auditable
  mapping (6 categories) — deliberately not trying to cover every possible
  attack pattern.

## What's genuinely tested vs. what isn't

Tested: every module's core math (SHAP additivity property verified
numerically, Bayesian layer's degenerate/symmetry cases self-tested, YARA
rule compiled with a real engine, Sigma rule parsed as real YAML), every
cross-module bridge independently before building on top of it, full
clean-room reproduction (delete all generated artifacts, rebuild from
scratch) for every module, and the Streamlit dashboard was both smoke-tested
by direct script execution AND launched as a real headless server returning
HTTP 200.

Not tested: live LLM API calls (see above), and the Streamlit dashboard has
never been opened in an actual browser by a human — only verified
programmatically. Open it yourself before demoing it live.

## Suggested next steps for the hackathon polish pass

1. Top-level README tying all 4 modules into one narrative (judges won't
   read 4 separate READMEs).
2. One-command demo script.
3. Live-test Module 4's LLM path with a real API key.
4. Open the Streamlit dashboard in a real browser at least once before
   presenting.
5. Do NOT let an AI assistant merge/dedupe the per-module `utils.py`/
   `predict.py` files — see the architectural constraint section above.
