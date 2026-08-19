# Model recommendation explanations

The Alpha 2 selector remains the decision authority. The recommendation
reporter adds a human-readable, machine-checkable explanation for each model
in its fit ladder: storage admission, system-memory fit, usable GPU-memory
fit, exact-profile evidence, and the pinned runtime route for the selected
model.

Run `python scripts/alpha2-model-recommendation-report.py --profile <profile>
--evidence <evidence>`. The report performs no download, fallback, promotion,
or policy change. A missing runtime route is shown as blocked rather than
silently switching engines.

`scripts/alpha2-model-recommendation-matrix.py` runs the explanation layer
across every deterministic hardware fixture. Its generated evidence is marked
synthetic and cannot admit a model; it protects selector ordering, runtime
routing, and rejection explanations from regression while physical evidence
remains the source of product claims.
