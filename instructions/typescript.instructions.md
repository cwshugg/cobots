---
name: "typescript"
description: "TypeScript and JavaScript coding conventions and best practices"
applyTo: "**/*.ts,**/*.tsx,**/*.js,**/*.jsx"
---

<!--
Adapted from the awesome-copilot project:

https://github.com/github/awesome-copilot/blob/main/instructions/nodejs-javascript-vitest.instructions.md

The original is available at the URL above. This version has been expanded to
cover TypeScript more broadly and adapted to match the cobots instruction style.
- Scribs
-->

# TypeScript and JavaScript Best Practices

Follow these guidelines when writing TypeScript or JavaScript code. These conventions emphasize type safety, modern patterns, and maintainability.

## General Principles

* Write clean, readable code that is easy to understand and maintain.
* Use TypeScript for all new projects — JavaScript is acceptable only when TypeScript is not feasible.
* Use ES2022+ features and target Node.js 20+ (or the appropriate minimum version for your project).
* Prefer Node.js built-in modules over external dependencies where possible.
* Use descriptive variable and function names; code should be self-explanatory.

## Type Safety

* Enable `strict` mode in `tsconfig.json`.
* Prefer explicit types over `any`. If `any` is unavoidable, use `unknown` instead and narrow with type guards.
* Use `interface` for object shapes that may be extended; use `type` for unions, intersections, and utility types.
* Use `as const` for literal types and `satisfies` for type-safe inference.
* Prefer `undefined` over `null` for optional values unless interacting with APIs that require `null`.

```typescript
// Good: explicit types and narrowing
function processInput(input: unknown): string {
    if (typeof input === "string") {
        return input.trim();
    }
    throw new Error("Expected a string");
}

// Good: const assertion
const ROLES = ["admin", "editor", "viewer"] as const;
type Role = (typeof ROLES)[number];
```

## Functions and Classes

* Prefer functions over classes unless state and behavior grouping are needed.
* Keep functions small and single-purpose.
* Use arrow functions for callbacks and short expressions; use named `function` declarations for top-level functions.
* Prefer composition over inheritance.

## Async Patterns

* Always use `async`/`await` for asynchronous code — never use raw callbacks.
* Use `node:util` `promisify` to convert callback-based APIs to promises.
* Handle promise rejections explicitly — never leave promises unhandled.
* Use `Promise.all()` for concurrent independent operations; use `Promise.allSettled()` when partial failures are acceptable.

```typescript
// Good: async/await with proper error handling
async function fetchData(url: string): Promise<Data> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json() as Promise<Data>;
}
```

## Module System

* Use ESM (`import`/`export`) for all new code.
* Use `node:` prefix for built-in modules (e.g., `import fs from "node:fs"`).
* Use named exports over default exports for better discoverability and refactoring support.
* Keep barrel files (`index.ts`) minimal to avoid circular dependency issues.

## Error Handling

* Use custom error classes for domain-specific errors.
* Fail fast with clear error messages.
* Never swallow errors silently in `catch` blocks.
* Use `Error` (or subclasses) for thrown values — never throw strings or plain objects.

```typescript
class NotFoundError extends Error {
    constructor(resource: string, id: string) {
        super(`${resource} with id '${id}' not found`);
        this.name = "NotFoundError";
    }
}
```

## Project Structure

* Organize code into modules and keep entry points small.
* Separate application code, tests, and scripts into distinct directories.
* Use consistent file naming: `kebab-case.ts` for modules, `kebab-case.test.ts` for tests.

A typical structure:

```text
src/
    index.ts
    config.ts
    modules/
        users/
            users.service.ts
            users.types.ts
tests/
    modules/
        users/
            users.service.test.ts
```

## Testing

* Use a modern test runner (Vitest, Jest, or the built-in Node.js test runner).
* Write tests for all new features and bug fixes.
* Ensure tests cover edge cases and error handling.
* Never modify production code solely to make it easier to test — write tests that exercise the code as-is.
* Use descriptive test names that state the expected behavior.

```typescript
describe("UserService", () => {
    it("should return a user when given a valid ID", async () => {
        const user = await userService.getById("abc123");
        expect(user).toBeDefined();
        expect(user.id).toBe("abc123");
    });

    it("should throw NotFoundError for an unknown ID", async () => {
        await expect(userService.getById("unknown")).rejects.toThrow(
            NotFoundError
        );
    });
});
```

## Code Style and Formatting

* Use a formatter (Prettier) and linter (ESLint) — configure them and run them in CI.
* Use `const` by default; use `let` only when reassignment is needed; never use `var`.
* Use template literals for string interpolation.
* Prefer `===` and `!==` over `==` and `!=`.

## Dependencies

* Avoid unnecessary dependencies; prefer standard library solutions first.
* Evaluate new dependencies before adding them — check maintenance status, bundle size, and security.
* Keep runtime and dev dependencies separate (`dependencies` vs. `devDependencies`).
* Use a lockfile (`package-lock.json`, `pnpm-lock.yaml`) and commit it to version control.

## Logging

* Use a structured logging library (e.g., pino, winston) instead of `console.log` in production code.
* Never log secrets, tokens, or PII.
* Use appropriate log levels (`debug`, `info`, `warn`, `error`).

## Patterns to Avoid

* Don't use `any` as a type — use `unknown` and narrow instead.
* Don't use `var` — use `const` or `let`.
* Don't use `eval()` or `Function()` constructor with dynamic strings.
* Don't use synchronous I/O (`readFileSync`, `execSync`) in server request handlers.
* Don't ignore TypeScript compiler errors or suppress them with `@ts-ignore` without a clear justification.
* Don't use `!` (non-null assertion) unless the value is provably non-null.
