# Running the models

Python 3.10 or newer is the only requirement; no third-party packages, API
keys, network services, or market-data subscriptions are needed. Check with
`python3 --version`; install from your OS package manager or
[python.org](https://www.python.org/downloads/) if missing.
The entry point also has PEP 723 metadata for optional
[uv](https://docs.astral.sh/uv/getting-started/installation/).

From this skill's root:

```bash
python3 scripts/finance_model.py --help
python3 scripts/finance_model.py project assets/fire-example.json
python3 scripts/finance_model.py simulate assets/fire-example.json
python3 scripts/finance_model.py analyze assets/returns-example.csv
python3 scripts/finance_model.py backtest assets/returns-example.csv \
  --initial-balance 200000 --annual-cashflow -10000 --rolling-years 5
python3 -m unittest discover -s tests -p 'test_*.py'
```

All assets are **invented examples**, including the return history; they
are not advice, historical market observations, or default expectations.
`assets/canada-examples.json` contains separate objects for each Canadian
command. Extract one object into a private local JSON file before running
the matching command.

Commands write JSON to standard output and errors to standard error with
non-zero exit status. Redirect results only to a user-approved private path.
No output files are created automatically and inputs are never edited.
Every result includes input SHA-256, command, and tool version. Backtest
assumptions include CLI parameters; retain the complete invocation as well.

No prices or private data are downloaded by this skill. Obtain authorized,
adjusted total-return data separately, record its provenance, and confirm
currency, frequency, distributions, splits, and coverage before replay.

For model fields and limitations, read [models.md](models.md). For Canadian
rules, read [canadian-rules.md](canadian-rules.md).
