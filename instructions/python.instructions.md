---
name: "python"
description: "Python programming language coding conventions and best practices"
applyTo: "**/*.py"
---

# Python Coding Conventions and Best Practices

## Code Style & Readability

* Follow [**PEP 8**](https://peps.python.org/pep-0008/) for formatting and naming.
* Prefer clear, explicit code over clever one‑liners.
* Use meaningful variable and function names.
* Use `snake_case` for naming functions and variables.
* Use `CamelCase` for naming classes.
* When possible, limit the lengths of lines to 80 characters.

## Project Structure

* Organize code into modules and packages.
* Keep entry points small; move logic into functions/classes.
* Use `__init__.py` intentionally to define public APIs.
* Separate application code, tests, and scripts.

## Functions & Classes

* Keep functions small and single‑purpose.
* Use classes when you need state or behavior grouping, not by default.
* Favor composition over inheritance.

## Typing & Documentation

* Use **type hints** (`typing`) for public functions and complex logic.
* Write **docstrings** for modules, classes, and public functions.
    * Please follow [PEP 257](https://peps.python.org/pep-0257/) for docstring formatting.
* Document *why*, not just *what*.

For example:

```python
def parse_config(path: str) -> dict:
    """Load and validate the application configuration."""
```

## Error Handling

* Fail fast with clear error messages.
* Use exceptions for exceptional cases, not control flow.

```python
try:
    value = int(user_input)
except ValueError as e:
    raise ValueError("user_input must be an integer") from e
```

## Testing

* If you are implementing a complex software system in Python, or you are requested to, please write unit tests for core logic.
* Keep tests fast, isolated, and deterministic.
* Use descriptive test names that state expected behavior.
* Test edge cases and failure paths.

## Dependencies & Environment

* Document dependencies in files, such as `requirements.txt`.
* Always execute code in Python virtual environments unless you are requested not to.
* Avoid unnecessary dependencies; prefer standard library solutions first.
* Keep runtime and dev dependencies separate.

## Logging

* If you are implementing a complex software system in Python, or you are requested to, please add logging to your code.
* Use logging instead of print statements.
    * Use the python `logging` library.

## Syntax & Semantics

* Use a formatter (e.g., `black`) and linter (e.g., `ruff`).

