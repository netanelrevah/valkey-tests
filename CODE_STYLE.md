# Code Style

## General
- No comments or docstrings — ever. Don't restate what code does; extract instead.
- No nested `if` — use fast returns.
- DRY: extract to variables/functions/constants when it aids readability.
- Use `is`/direct evaluation instead of `== True`/`== False`.
- Line length: 120 characters.
- Target Python 3.11+.

## Imports
- Always start with `from __future__ import annotations`.
- Move imports only needed for type annotations into a `TYPE_CHECKING` block:
  ```python
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from collections.abc import Callable
  ```

## Type Annotations
- Annotate every function parameter and return type.
- Use `|` union syntax, not `Union[...]`.
- Use lowercase generics: `dict[str, T]`, `list[T]`, `set[str]` — never `Dict`, `List`, `Set`.
- Declare class-level mappings with `ClassVar`:
  ```python
  MAPPING: ClassVar[dict[str, SomeTranslator]] = {}
  ```
- Declare type aliases at module level with a `Type` suffix:
  ```python
  FooTranslatorType = type["FooTranslator"]
  ```

## Class Design
- **Registry/decorator pattern** for pluggable dispatch: implement `register` as a classmethod that returns a decorator, then apply it to each concrete subclass:
  ```python
  class Base:
      MAPPING: ClassVar[dict[str, Base]] = {}

      @classmethod
      def register(cls, key: str) -> Callable[[BaseType], BaseType]:
          def decorator(translator_cls: BaseType) -> BaseType:
              cls.MAPPING[key] = translator_cls()
              return translator_cls
          return decorator

  @Base.register("foo")
  class FooImpl(Base): ...
  ```
- Use `raise NotImplementedError` in abstract base methods (no `@abstractmethod` needed).
- Use `Protocol` for interface contracts; protocol methods end with `...`.
- Use `@dataclass` for value-carrying classes; mutable defaults via `field(default_factory=...)`, private fields prefixed with `_`.

## Return Patterns
- Return `None` to signal failure; callers check `if x is None`.
- Use early `return None` to keep the happy path at the bottom — never `elif` after a `return`.
- Use the inline ternary form for short translator results:
  ```python
  return None if args is None else f"len({args[0]})"
  ```
- Use `assert isinstance(x, SomeType)` at the top of a method to narrow the type when the type is guaranteed by the dispatch (MAPPING key).

## Naming
- Classes: `PascalCase`. Functions/variables: `snake_case`. Module-private: `_underscore_prefix`.
- `match` statements preferred over chained `if/elif` for dispatch on string/type keys.