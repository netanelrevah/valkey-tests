# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is valkey-tests

A Python port of the Valkey TCL test suite. Uses `nrevah-pytcl` (the `../pytcl` workspace package) to parse and evaluate TCL test files and converts them into pytest test cases.

## Commands

```bash
uv sync --all-extras      # Install all dependencies
uv run pytest             # Run all tests
uv run ruff check .       # Lint
uv run mypy valkeytests/  # Type check
```

To regenerate test files and check translation stats, use the PowerShell script:

```powershell
pwsh scripts/generate.ps1 --valkey-directory "C:\data\gitrepositories\github.com\valkey-io\valkey" --skip-errors --stats
```



## Workflow

**Always run pre-commit before committing and fix all failures before proceeding:**

```bash
uv run pre-commit run --all-files
```

Only commit once all hooks pass.

## Architecture

**Key directories**:
- `valkeytests/` — main package
  - `create_test_files.py` — generates Python test files from TCL sources
  - `compare_tests.py` — compares test outputs
- `tests/` — pytest suite
  - `conftest.py` — shared fixtures
  - `utils.py` — test utilities
  - `valkey_test_client.py` — client for talking to a Valkey server
  - `test_valkeytests/` — tests for the valkeytests package itself

**Dependencies**:
- `nrevah-pytcl` (`../pytcl`, editable) — TCL parser/evaluator; extend this when new typed AST nodes are needed
- `nrevah-parametrization` (`../parametrization`, editable) — `@Parametrization.case` decorator

## TCL → Python Translation Plan

The main project goal: translate Valkey TCL test bodies into real Python, replacing `assert False` stubs.
`create_test_files.py` generates the Python files; pytcl (`../pytcl`) provides the typed AST.
Python emission lives only in `valkeytests/`; pytcl is extended only to add richer AST nodes.

### How to continue in a new session

1. Run `pwsh scripts/generate.ps1 --valkey-directory "C:\data\gitrepositories\github.com\valkey-io\valkey" --skip-errors --stats` to see coverage
2. Check `git log` on both repos to see what was last added
3. Pick the next phase item or the top untranslated command from `--stats`
4. Follow the iterative loop: add typed node to pytcl → add emission rule → add test → re-run stats

### Architecture

```
valkeytests/create_test_files.py
  TCLTestFileGenerator.generate_test()
    └── TCLBodyTranslator.translate(body: TCLScript, expected: str | None) -> list[str]
          walks pytcl AST, emits Python; unknown commands → # TODO stub

pytcl/pytcl/commands.py  (extend with new nodes as needed)
  TCLCommandCatch    body: TCLScript, var_name: str | None
  TCLCommandProc     name: str, params: list[str], body: TCLScript
  TCLCommandSet      name: str, value: TCLCommandArguments
  TCLCommandReturn   value: TCLCommandArguments | None
  TCLCommandIncr     name: str, amount: int
  TCLCommandString   subcommand: str, args: list[TCLCommandArguments]
  TCLCommandListOp   op: str, args: list[TCLCommandArguments]   (lindex/lrange/llength/lappend/lassign)
  TCLCommandDict     subcommand: str, args: ...
  TCLCommandArray    subcommand: str, args: ...

tests/helpers.py  (Python equivalents of TCL test framework helpers)
  tcl_split(s)                  splits TCL list string into Python list
  wait_for_condition(fn, ms)
  assert_encoding / assert_type / assert_range / assert_morethan / assert_lessthan
```

### Two test body patterns

**Pattern A** — trailing expected arg (last body expression is the result):
```tcl
test {GET item} { r set x foo; r get x } {foo}
```
→ emit `assert <last_expr> == "foo"`

**Pattern B** — inline assertions, no trailing expected:
```tcl
test "SETNX" { assert_equal 1 [r setnx k v]; assert_equal "v" [r get k] }
```
→ emit each assertion directly

### Command translation map

| TCL | Python |
|---|---|
| `r cmd a b` | `r.cmd(a, b)` |
| `set x val` | `x = val` |
| `incr x ?n?` | `x += n` |
| `assert_equal a b` | `assert a == b` |
| `assert_match pat val` | `assert fnmatch(val, pat)` |
| `assert_error "*pat*" {body}` | `with pytest.raises(Exception, match=...)` |
| `assert expr` | `assert expr` |
| `catch {body} var` | `try: ... except Exception as _e: var = str(_e)` |
| `string repeat s n` | `s * n` |
| `string length s` | `len(s)` |
| `string match pat s` | `fnmatch(s, pat)` |
| `string range s a b` | `s[a:b+1]` |
| `string trim/trimleft/trimright s` | `s.strip()/.lstrip()/.rstrip()` |
| `lindex lst i` | `lst[i]` |
| `lrange lst a b` | `lst[a:b+1]` |
| `llength lst` | `len(lst)` |
| `lassign lst a b` | `a, b = lst` |
| `lappend lst val` | `lst.append(val)` |
| `list a b c` | `[a, b, c]` |
| `after ms` | `time.sleep(ms / 1000)` |
| `puts msg` | skip |
| `proc name {args} {body}` | module-level `def name(args):` |
| `array set d {k v}` | `d = {"k": "v"}` |
| `dict get d k` | `d[k]` |

### Known limits (these stay as stubs)

- **Dynamic variable names**: `set var_$i x` — name contains substitution, can't transpile statically
- **`upvar` / `global`** — scope bridging, rare in unit tests, too complex
- **`exec`** — shell commands, skip
- **`proc` inside test bodies that access caller vars** — needs upvar analysis; lift simple cases only
- **TCL list ↔ string coercion** — when a variable is used as both a string and list, emit
  `tcl_split(x)[i]` and add a `tcl_split` helper that splits on whitespace respecting braces

### Phase order (by ROI)

1. **Infrastructure**: `TCLBodyTranslator` class + `--stats` CLI flag
2. **Core** (unlocks ~60%): `r`, `set`, `assert_equal`, `assert_match`, `assert_error`, Pattern A
3. **Control flow**: `if/foreach` (pytcl has these), `for`, `while`, `return`, `incr`, `lappend`
4. **String ops**: `TCLCommandString` in pytcl + emission rules
5. **List ops**: `lindex/lrange/llength/lassign/list` + `tcl_split` helper
6. **catch**: `TCLCommandCatch` in pytcl + `try/except` emission
7. **Framework helpers**: `wait_for_condition`, `assert_encoding`, `assert_type`, etc. in `helpers.py`
8. **proc**: file-scope proc lifting to module-level `def`
9. **dict / array**: map to Python dicts

## Code Style

- No comments or docstrings — ever. Don't restate what code does; extract instead.
- No nested `if` — use fast returns.
- DRY: extract to variables/functions/constants when it aids readability.
- Imports at top of file only.
- Use `is`/direct evaluation instead of `== True`/`== False`.

## General

- Do not create example test files, do not create `.md` files to explain solutions.
- When changing something globally, work gradually — small steps without loading full context.
- Read `CLAUDE.local.md` if it exists for machine-specific context.

## Workflow

When the user corrects a workflow mistake (e.g., wrong command, missing `.gitignore` entries), save the correction here — CLAUDE.md is loaded every session and is the authoritative source for project rules.

## Unordered Notes

- When you want to run code to check if things work, create a test case instead and run pytest. This way you have a permanent record of the behavior.
- When running commands from root directory, NEVER run "cd && <command>", just run the command.