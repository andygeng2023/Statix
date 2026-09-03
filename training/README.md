# Statix training

Run from the repository root:

    python -m training.train

The command downloads five years of daily data for every symbol in `universe.txt`, creates the shared feature set, trains one global classifier/regressor ensemble, evaluates a chronological holdout, and writes `artifacts/model.joblib`.

For a larger model, expand `universe.txt`. For production-scale scans (2,000–10,000 symbols), use a market-data provider with bulk/streaming access rather than relying on Yahoo polling.
