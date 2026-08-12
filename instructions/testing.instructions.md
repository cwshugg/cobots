---
name: "testing"
description: "Language-agnostic testing best practices and conventions"
applyTo: "**"
---

<!--
This file was authored originally for the Cobots Collective by synthesizing
widely accepted testing best practices.
There is no single awesome-copilot source file for this content.
- Scribs
-->

# Testing Best Practices

Follow these guidelines when writing and organizing tests. These principles are language-agnostic and apply to unit, integration, and end-to-end testing in any technology stack.

## General Principles

* Every new feature and bug fix should have corresponding tests.
* Tests are production code — apply the same quality standards (readability, maintainability, naming) to tests as you do to application code.
* Tests should be fast, isolated, deterministic, and repeatable.
* A failing test should clearly communicate *what* failed, *where*, and *why*.

## Test-Driven Development (TDD)

TDD is a development practice where tests are written before the implementation:

1. **Red**: Write a failing test that describes the desired behavior.
2. **Green**: Write the minimum code necessary to make the test pass.
3. **Refactor**: Clean up the implementation while keeping all tests green.

TDD is not required for every change, but it is highly effective for:

* Well-defined behavior with clear inputs and outputs.
* Bug fixes — write a test that reproduces the bug first, then fix it.
* Complex logic where correctness is critical.

## Test Organization

### Unit Tests

* Test individual functions, methods, or classes in isolation.
* Mock or stub external dependencies (databases, APIs, file systems).
* Keep unit tests fast — they should run in milliseconds.
* Place unit tests alongside or near the code they test.

### Integration Tests

* Test the interaction between multiple components (e.g., a service and its database, or two services communicating).
* Use real dependencies where practical (e.g., a test database), or well-configured fakes.
* Accept that integration tests are slower than unit tests — run them in CI but keep the suite manageable.

### End-to-End (E2E) Tests

* Test complete user workflows through the full application stack.
* Use E2E tests sparingly — they are slow, brittle, and expensive to maintain.
* Focus E2E tests on critical user paths (login, checkout, core workflows).
* Avoid duplicating coverage already handled by unit and integration tests.

### The Testing Pyramid

Follow the testing pyramid as a general guide for test distribution:

* **Many** unit tests (fast, cheap, isolated).
* **Some** integration tests (moderate speed, test component interactions).
* **Few** E2E tests (slow, expensive, test critical paths only).

## Test Naming

* Use descriptive names that state the expected behavior, not the implementation.
* A reader should understand the test's purpose without reading the body.

```text
# Good test names
test_returns_empty_list_when_no_items_match
test_raises_validation_error_for_negative_amount
test_creates_user_and_sends_welcome_email

# Bad test names
test_function1
test_edge_case
test_bug_fix
```

## Test Structure

Follow the **Arrange-Act-Assert** (AAA) pattern:

1. **Arrange**: Set up the test data and preconditions.
2. **Act**: Execute the code under test.
3. **Assert**: Verify the result matches expectations.

Keep each section short and clearly separated. Each test should test one behavior.

```python
def test_discount_applied_to_order_total():
    # Arrange
    order = Order(items=[Item(price=100), Item(price=50)])
    discount = Discount(percentage=10)

    # Act
    total = order.apply_discount(discount)

    # Assert
    assert total == 135.0
```

## Test Behavior

* Derive tests from each observed behavior and its expected result.
    * Have the test assert the expected state/output for correctness; do not rely on "the test did not return an error" as the only verification of correctness.
* For a bug fix, include the input or state that triggered the defect and assert the corrected behavior, so the test fails if that defect returns.

## Mocking and Stubbing

* Mock external dependencies (network calls, databases, file I/O) — not the code under test.
* Prefer fakes (lightweight, in-memory implementations) over mocks when feasible.
* Avoid mocking too deeply — if a test requires complex mock setups, it may be testing the wrong thing or the code may need refactoring.
* Verify interactions (that a function was called) only when the *side effect* is the behavior you're testing.

## Test Data and Fixtures

* Use factory functions or builders to create test data — avoid copy-pasting raw data across tests.
* Keep test data minimal: include only the fields relevant to the test.
* Use fixtures (setup/teardown) for shared preconditions, but avoid fixtures that are too large or too magical.

## Coverage

* Use code coverage tools to identify untested paths, but do not treat coverage percentage as a quality metric on its own.
* High coverage with weak assertions is worse than moderate coverage with strong assertions.
* Focus on covering critical paths, edge cases, and error-handling branches.
* Aim for meaningful coverage: if a line is covered, ensure the test actually verifies its behavior.

## Testing Anti-Patterns

* **Testing implementation details**: Tests should verify behavior (inputs → outputs), not internal state or private methods. Implementation changes should not break tests unless behavior changes.
* **Flaky tests and test interdependence**: Tests must not pass and fail intermittently or depend on execution order or shared mutable state.
    * Isolate process-global or shared mutable state, restore it reliably, and clean up test state between runs.
    * Use synchronization and repeated runs for timing-sensitive code to establish that results are repeatable.
    * Fix or quarantine flaky tests immediately.
* **Slow tests**: A slow test suite discourages developers from running tests. Keep unit tests fast; run slow tests in CI.
* **Excessive mocking**: If every dependency is mocked, the test may not be verifying real behavior. Balance mocking with integration-level tests.
* **Copy-paste test code**: Repeated setup logic should be extracted into helpers or fixtures.
* **Ignoring failures**: Never mark failing tests as "skip" or "expected failure" without a clear plan to fix them.

## Continuous Integration

* CI must run the full test suite on every pull request.
* Fail the build on any test failure — do not allow broken tests to be merged.
* Run unit tests first (fast feedback), then integration tests, then E2E tests.
* Report test results and coverage in a format that is easy to review (e.g., CI summary, coverage reports).

## Validation and Evidence

* During development, run the smallest directly relevant automated check first.
* Before requesting review, run the repository-defined test gates that apply to the change.

