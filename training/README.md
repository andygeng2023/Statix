# Statix training

Run from the repository root after installing requirements:

    python -m training.train

The trainer downloads historical daily data for the configured universe, builds a shared feature set, creates rolling sequences, trains a compact PatchTST-style temporal transformer with classification and return heads, evaluates a chronological holdout, and writes `artifacts/statix_model.pt`.

For a larger training set, expand `training/universe.txt`. For very large production universes, use a licensed bulk/streaming market-data provider rather than high-frequency Yahoo polling.

The deployed app never retrains on page load. It loads the exported artifact and performs CPU inference.
