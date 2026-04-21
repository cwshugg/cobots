---
name: "cpp"
description: "C and C++ coding conventions and best practices"
applyTo: "**/*.c,**/*.cpp,**/*.h,**/*.hpp"
---

<!--
Adapted from the awesome-copilot project:

https://github.com/github/awesome-copilot/blob/main/instructions/cmake-vcpkg.instructions.md
https://github.com/github/awesome-copilot/blob/main/instructions/cpp-language-service-tools.instructions.md

The originals are available at the URLs above. This version has been
substantially rewritten and expanded to cover general C/C++ best practices,
adapted to match the cobots instruction style.
- Scribs
-->

# C and C++ Coding Conventions and Best Practices

Follow these guidelines when writing C or C++ code. Prefer modern C++ (C++17 or later) for new projects unless there is a specific reason to target an older standard or plain C.

## General Principles

* Prioritize safety, readability, and maintainability.
* Prefer compile-time checks over runtime checks wherever possible.
* Write code that compiles with zero warnings. Treat warnings as errors during CI (`-Werror`).
* Use consistent naming conventions throughout the project.
* Break down complex functions into smaller, well-named helper functions.

## Memory Safety

### RAII (Resource Acquisition Is Initialization)

* Use RAII for all resource management (memory, file handles, locks, sockets).
* Acquire resources in constructors; release them in destructors.
* Never rely on manual `delete`, `free()`, or explicit cleanup calls when RAII can be used.

### Smart Pointers

* Use `std::unique_ptr` for exclusive ownership (the default choice).
* Use `std::shared_ptr` only when shared ownership is genuinely required.
* Use `std::weak_ptr` to break reference cycles with `std::shared_ptr`.
* Never use raw `new`/`delete` in application code — use `std::make_unique` and `std::make_shared`.

```cpp
// Good: smart pointer with make_unique
auto widget = std::make_unique<Widget>(args...);

// Bad: raw new/delete
Widget* widget = new Widget(args...);
// ... later, easy to forget:
delete widget;
```

### Raw Pointers

* Use raw pointers only for non-owning references where `nullptr` is a valid state.
* Prefer references (`&`) for non-owning, non-nullable parameters.
* In C code, document ownership semantics clearly in comments for every pointer parameter and return value.

## Const Correctness

* Mark variables, parameters, member functions, and return values as `const` whenever they should not be modified.
* Use `const` references (`const T&`) for function parameters that are read-only.
* Use `constexpr` for values and functions that can be evaluated at compile time.

```cpp
// Good: const correctness
std::string format_name(const std::string& first, const std::string& last) {
    return first + " " + last;
}

constexpr int MAX_RETRIES = 3;
```

## Modern C++ Features (C++17/20)

* Use structured bindings for unpacking pairs, tuples, and structs.
* Use `std::optional<T>` for values that may or may not exist.
* Use `std::variant<Ts...>` instead of unions with manual type tags.
* Use `std::string_view` for read-only, non-owning string parameters.
* Use `if constexpr` for compile-time branching in templates.
* Use `[[nodiscard]]` on functions whose return value should not be ignored.
* Use range-based `for` loops and the `<algorithm>` / `<ranges>` headers instead of index-based loops.

```cpp
// Structured bindings (C++17)
auto [key, value] = map.extract(it);

// std::optional
std::optional<User> find_user(int id);

// [[nodiscard]]
[[nodiscard]] bool save(const Config& config);
```

## Error Handling

* Use exceptions for truly exceptional, unrecoverable conditions.
* Use return values (`std::optional`, `std::expected` in C++23, or custom result types) for expected failure modes.
* Never use exceptions for control flow.
* In C code, use explicit error codes and check return values at every call site.
* Document which functions may throw and under what conditions.
* Ensure destructors never throw exceptions.

```cpp
// Good: expected failure via optional
std::optional<Config> load_config(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        return std::nullopt;
    }
    // ... parse and return
}
```

## Build Systems

### CMake

* Use modern CMake (3.14+) with target-based commands.
* Use `target_include_directories`, `target_link_libraries`, and `target_compile_features` instead of global `include_directories` or `link_libraries`.
* Define project metadata: `project(name VERSION x.y.z LANGUAGES CXX)`.
* Use `CMakePresets.json` for reproducible build configurations.
* Use `FetchContent` or a package manager (vcpkg, Conan) for dependencies.

```cmake
cmake_minimum_required(VERSION 3.14)
project(myapp VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(myapp src/main.cpp src/app.cpp)
target_include_directories(myapp PRIVATE ${CMAKE_SOURCE_DIR}/include)
target_compile_options(myapp PRIVATE -Wall -Wextra -Wpedantic)
```

### Compiler Warnings

* Enable a comprehensive set of warnings: `-Wall -Wextra -Wpedantic` (GCC/Clang) or `/W4` (MSVC).
* Treat warnings as errors in CI builds: `-Werror` (GCC/Clang) or `/WX` (MSVC).
* Use static analysis tools (clang-tidy, cppcheck) and integrate them into the build.

## Code Style and Formatting

* Use `clang-format` for automatic formatting. Commit a `.clang-format` configuration file with the project.
* Choose a naming convention and apply it consistently:
    * Common C++ convention: `snake_case` for functions and variables, `PascalCase` for types and classes, `UPPER_CASE` for macros and constants.
    * Common C convention: `snake_case` throughout, `UPPER_CASE` for macros.
* Keep lines under 100 characters when possible.
* Place includes in groups: standard library, third-party, project headers — separated by blank lines.

```cpp
#include <string>
#include <vector>

#include <fmt/core.h>

#include "myapp/config.h"
#include "myapp/utils.h"
```

## Testing

* Write unit tests using a framework such as Google Test, Catch2, or doctest.
* Place tests in a `tests/` directory with descriptive filenames.
* Use test fixtures for shared setup and teardown.
* Test edge cases, error paths, and boundary conditions.
* Integrate tests into the CMake build with `enable_testing()` and `add_test()`.

## Documentation

* Document all public APIs with Doxygen-style comments (`///` or `/** */`).
* Document ownership semantics for pointer parameters and return values.
* Include usage examples in documentation for complex APIs.
* Document thread-safety guarantees for shared data structures.

## Patterns to Avoid

* Don't use raw `new`/`delete` or `malloc`/`free` in C++ when smart pointers or containers are available.
* Don't use C-style casts — use `static_cast`, `dynamic_cast`, `const_cast`, or `reinterpret_cast`.
* Don't use `#define` for constants or inline functions — use `constexpr` and `inline` functions.
* Don't use `using namespace std;` in headers — it pollutes the global namespace.
* Avoid global mutable state. Use dependency injection or thread-safe containers.
* Avoid deep inheritance hierarchies — prefer composition and interfaces (pure virtual classes).
* Don't ignore compiler warnings — fix them or understand why they're safe before suppressing.

## Quality Checklist

Before merging C/C++ code, verify:

* [ ] **Safety**: No raw `new`/`delete` in C++ (use smart pointers); RAII for all resources.
* [ ] **Const correctness**: Parameters, variables, and member functions are `const` where appropriate.
* [ ] **Warnings**: Code compiles with zero warnings under `-Wall -Wextra -Wpedantic`.
* [ ] **Testing**: New functionality has corresponding tests.
* [ ] **Documentation**: Public APIs have Doxygen comments.
* [ ] **Formatting**: Code is formatted with `clang-format`.
