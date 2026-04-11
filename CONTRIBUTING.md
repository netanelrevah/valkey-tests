# Contributing

## Architecture

**Key directories**:
- `valkey_tests_generator/` — generator package
  - `create_test_files.py` — generates Python test files from TCL sources
  - `argument_translators.py` — translates TCL argument expressions to Python
  - `statement_translators.py` — translates TCL statements to Python
  - `command_generators.py` — handles `test`, `foreach`, `if` command structures
- `tests/` — pytest suite for the generator itself
  - `conftest.py` — shared fixtures
  - `valkey_test_client.py` — client for talking to a Valkey server
  - `test_valkeytests/` — tests for the generator package
- `valkey_tests/` — generated Python test files (do not edit manually)

**Dependencies**:
- `nrevah-pytcl` (`../pytcl`, editable) — TCL parser/evaluator; extend this when new typed AST nodes are needed
- `nrevah-parametrization` (`../parametrization`, editable) — `@Parametrization.case` decorator

**Generator entry point**:

```
valkey_tests_generator/create_test_files.py
  TCLTestFileGenerator.generate_test()
    └── TCLBodyTranslator.translate(body: TCLScript, expected: str | None) -> list[str]
          walks pytcl AST, emits Python; unknown commands → # TODO stub
```

## TCL → Python Translation

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
| `r cmd a b` | `r.run('cmd', a, b)` |
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
| `$var(key)` | `var["key"]` |
| `create_$type args` | `globals()[f"create_{type}"](args)` |
| `{*}$list` | `r.run(*list[1:])` |
| `::tls::status [$s channel]` | `s.tls_status()` |
| `file normalize path` | `"path"` |

### Known limits

- **Dynamic variable names**: `set var_$i x` — name contains substitution, can't transpile statically
- **`upvar` / `global`** — scope bridging, too complex
- **`exec`** — shell commands, skip
- **`proc` inside test bodies that access caller vars** — needs upvar analysis
- **`::tls::status` fields beyond `cipher`/`protocol`** — not mapped

## Workflow

**Always run pre-commit before committing and fix all failures before proceeding:**

```bash
uv run pre-commit run --all-files
```

Only commit once all hooks pass.

## Development Loop

To regenerate test files and check translation stats:

```powershell
pwsh scripts/generate.ps1 --valkey-directory "<valkey-repo>" --skip-errors --stats
```

To add support for a new TCL construct:
1. If it requires a new AST node: extend `nrevah-pytcl` (`../pytcl/pytcl/commands.py`)
2. Add an `ArgumentTranslator` or `ExpressionTranslator` in `argument_translators.py`, or a `StatementTranslator` in `statement_translators.py`
3. Add a test in `tests/test_valkeytests/test_create_test_files.py`
4. Re-run stats to verify improvement

## Code Style

See [CODE_STYLE.md](CODE_STYLE.md).
