# valkey-tests

A Python port of the Valkey TCL test suite. Uses `nrevah-pytcl` (the `../pytcl` workspace package) to parse and evaluate TCL test files and converts them into pytest test cases.

## Setup

```bash
uv sync --all-extras      # Install all dependencies
```

## Running Tests

```bash
uv run pytest             # Run all tests
uv run ruff check .       # Lint
uv run mypy valkeytests/  # Type check
```

## Regenerating Test Files

```powershell
pwsh scripts/generate.ps1 --valkey-directory "<valkey-repo>" --skip-errors --stats
```

## Contributing

See [CONTRIBUTION.md](CONTRIBUTION.md) and [CODE_STYLE.md](CODE_STYLE.md).
