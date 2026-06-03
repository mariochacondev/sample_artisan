# sample_artisan

`sample_artisan` is a clean Python starter project with package code, a command-line entry point, and tests.

## Project layout

```text
sample_artisan/
├── pyproject.toml
├── README.md
├── src/
│   └── sample_artisan/
│       ├── __init__.py
│       ├── cli.py
│       └── core.py
└── tests/
    └── test_core.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run

```bash
sample-artisan "hello world"
```

## Test

```bash
pytest
```
