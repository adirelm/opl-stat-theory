# Data

The ~800 MB OpenPowerlifting CSV is **not committed** to git.

- **Exact pinned snapshot** (reproduces every number in the paper):
  [Release `data-snapshot-2026-06`](https://github.com/adirelm/opl-stat-theory/releases/tag/data-snapshot-2026-06)
  — download `openpowerlifting.csv.gz` and gunzip it to `data/openpowerlifting.csv`.
  Its SHA-256 is pinned in `src/config.py` and verified by `run_all.sh`, which also
  **auto-downloads it** if this directory is empty.
- **Current weekly data** (numbers will differ slightly): `python download_data.py`.

Source: [OpenPowerlifting](https://www.openpowerlifting.org) (public domain, CC0-style waiver).
