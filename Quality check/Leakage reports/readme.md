# Quality Control

Spatial-leakage audit logs for the SENSERO train/validation/test split.

| File | Description |
|---|---|
| `leakage_swap_log.csv` | Identity-preserving eval→train swaps performed to enforce the 5 km buffer |
| `leakage_residual.csv` | Eval–train pairs remaining below 5,000 m (min distance: 4,218 m; no footprint overlap at any scale) |
| `leakage_failures.csv` | Evaluation patches where no buffer-compliant same-label replacement was available |
