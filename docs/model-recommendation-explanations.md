# Model recommendation explanations

The Alpha 2 selector remains the decision authority. The recommendation
reporter explains each model in its fit ladder in readable, machine-checkable
terms: storage admission, system-memory fit, usable GPU-memory fit,
exact-profile evidence, and the selected model's pinned runtime route.

Run `python scripts/alpha2-model-recommendation-report.py --profile <profile>
--evidence <evidence>`. The report performs no download, fallback, promotion,
or policy change. A missing runtime route is shown as blocked rather than
silently switching engines.

`scripts/alpha2-model-recommendation-matrix.py` runs the explanation layer
across every deterministic hardware fixture. It marks the generated evidence
as synthetic, so it cannot admit a model. The matrix protects selector
ordering, runtime routing, and rejection explanations from regression while
physical evidence remains the source of product claims.
