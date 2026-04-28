---
name: "kusto"
description: "Kusto Query Language (KQL) coding conventions and best practices"
applyTo: "**/*.kql,**/*.csl"
---

# Kusto Query Language (KQL) Best Practices

Kusto Query Language (KQL) is a read-only query language for processing structured, semi-structured, and unstructured data. It is used across Microsoft services including Azure Data Explorer, Azure Monitor / Log Analytics, Microsoft Sentinel, Microsoft Defender, and Azure Resource Graph. KQL uses a pipe-based data flow model where tabular data flows left-to-right through operators separated by `|`.

Follow these guidelines when writing KQL queries.

## General Principles

* KQL is **read-only** — queries never modify data.
* KQL is **case-sensitive** — table names, column names, operators, and keywords are all case-sensitive.
* Data flows through a pipeline: `Source | Operator1 | Operator2 | ...`
* Each operator receives tabular input, transforms it, and emits tabular output.
* Prefer clarity and readability — place each operator on its own line, prefixed with `|`.

## Core Syntax

### Tabular Expressions

The fundamental KQL pattern is a tabular data source piped through a chain of operators:

```kusto
StormEvents
| where StartTime between (datetime(2007-11-01) .. datetime(2007-12-01))
| where State == "FLORIDA"
| summarize count() by EventType
| sort by count_ desc
| take 10
```

### `let` Statements

Use `let` to bind names to expressions, define constants, and create reusable query-scoped functions. This improves readability and avoids repetition.

* Every `let` statement must end with a semicolon.
* Do not place blank lines between `let` statements or between `let` and other statements.
* Remember that `let` binds a name to a *calculation*, not an evaluated value — use `materialize()` if the result is referenced multiple times.

```kusto
let threshold = 50;
let region = "West";
let MultiplyByN = (val:long, n:long) { val * n };
MyTable
| where Score > threshold and Region == region
| extend adjusted = MultiplyByN(Score, 2)
```

### `set` Statements

Use `set` to control query execution properties:

```kusto
set query_take_max_records = 100;
StormEvents
```

## Key Operators

### Filtering

* `where` — filter rows by a predicate. Apply immediately after the table reference.
* `distinct` — return unique combinations of specified columns.
* `take` / `limit` — return N rows (no guaranteed order). Useful for exploring unknown datasets.
* `search` — full-text search across columns. Avoid using `*`; specify target columns.

### Projection

* `project` — select, rename, and reorder columns. Use to trim output to only needed columns.
* `project-away` — exclude specific columns.
* `extend` — add calculated columns while keeping all existing columns.

### Aggregation

* `summarize` — group rows and compute aggregations. The primary aggregation operator.
* `count` — shorthand for `summarize count()`.
* `top` — return the top N rows sorted by an expression.

### Joins

* `join` — merge rows from two tables on matching columns.
* `lookup` — extend a fact table with values from a small dimension table.
* `union` — combine rows from multiple tables.

The **default** join flavor is `innerunique` (not `inner` like SQL). This deduplicates the left side, which may not be intended. Always specify the join kind explicitly:

```kusto
// Good: explicit join kind
T1 | join kind=inner (T2) on SharedKey

// Bad: relies on default innerunique behavior
T1 | join (T2) on SharedKey
```

### Parsing and Transformation

* `parse` — extract multiple values from a string column by pattern. Prefer over multiple `extract()` calls when strings share a common format.
* `extract` — extract a value using regex. Use for non-uniform patterns.
* `mv-expand` — expand dynamic arrays into multiple rows.
* `mv-apply` — apply a subquery to each element of a dynamic array.

### Visualization

Use `render` as the **last** operator to produce visual output:

```kusto
StormEvents
| summarize count() by State
| top 10 by count_
| render barchart
```

## Performance Optimization

Performance is critical for KQL queries running against large datasets. Follow these guidelines in order of importance.

### 1. Filter Early and Aggressively

Apply `where` clauses immediately after the table reference. Reduce data volume before any joins, projections, or aggregations.

```kusto
// Good: filter first
StormEvents
| where StartTime > ago(7d)
| where State == "TEXAS"
| summarize count() by EventType

// Bad: filter after expensive operations
StormEvents
| summarize count() by EventType, State
| where State == "TEXAS"
```

### 2. Order Predicates for Index Usage

When combining multiple `where` conditions, order them to maximize index utilization:

1. **`datetime` predicates first** — eliminates entire data shards via partitioning
2. **`string` term-level predicates** (`has`, `has_cs`, `in`) — uses the term index
3. **Selective numeric predicates**
4. **Column-scanning predicates last** (`contains`, `matches regex`) — slowest

### 3. Use `has` Instead of `contains`

KQL builds a **term index** on string columns (terms are alphanumeric sequences of 3+ characters). The `has` operator leverages this index; `contains` does not and falls back to a full column scan.

```kusto
// Good: uses term index — fast
Logs | where Message has "error"

// Bad: full column scan — slow
Logs | where Message contains "error"
```

Only use `contains` when you need true substring matching (e.g., matching within a word).

### 4. Prefer Case-Sensitive Operators

Case-sensitive operators are faster than their case-insensitive counterparts.

* Use `==` instead of `=~`
* Use `has_cs` instead of `has` when case is known
* Use `in` instead of `in~`

For case-insensitive comparisons, use `=~` directly — do **not** call `tolower()` or `toupper()` on the column:

```kusto
// Good
Events | where Name =~ "critical"

// Bad: prevents index usage
Events | where tolower(Name) == "critical"
```

### 5. Filter on Source Columns, Not Calculated Columns

Filtering on source columns allows the engine to use indexes. Filtering on `extend`-ed columns does not.

```kusto
// Good: predicate on source column
T | where SourceCol > 100

// Bad: predicate on calculated column
T | extend Calc = SourceCol * 2 | where Calc > 200
```

### 6. Join Optimization

* Place the **smaller table on the left** side of standard joins.
* Use `in` instead of `left semi join` for single-column filtering.
* Use `lookup` instead of `join` when the right side is small (< tens of MB).
* Use `hint.strategy=broadcast` when the left side is small (< 100 MB).
* Use `hint.shufflekey=<key>` when both sides are large with high-cardinality keys.

### 7. Materialize Repeated Subqueries

When a `let`-bound tabular expression is used multiple times, wrap it in `materialize()` to compute it once. Push filters and projections inside the `materialize()` call to minimize cached data.

```kusto
let baseData = materialize(
    StormEvents
    | where StartTime > ago(30d)
    | project State, EventType, DamageProperty
);
baseData | summarize TotalDamage = sum(DamageProperty) by State;
baseData | summarize EventCount = count() by EventType
```

### 8. DateTime and Dynamic Column Tips

* Store dates as `datetime`, not `long`. Convert Unix timestamps at ingestion time using update policies.
* For dynamic column lookups on large datasets, pre-filter with `has` before parsing:

```kusto
// Good: pre-filter with term index, then parse
T | where DynamicCol has "Rare" | where DynamicCol.Key == "Rare"

// Bad: parses JSON on every row
T | where DynamicCol.Key == "Rare"
```

### 9. Limit Results on Unknown Datasets

When exploring unfamiliar data, always append `| take N` or `| count` to avoid returning excessive data.

## Anti-Patterns to Avoid

* Don't use `contains` when `has` would suffice — it is orders of magnitude slower.
* Don't use `tolower(Col) == "value"` — use `Col =~ "value"` instead.
* Don't filter on calculated columns when the predicate can be expressed against source columns.
* Don't use `search *` — specify target columns to avoid full-text scans across all columns.
* Don't use multiple `extract()` calls on uniformly-formatted strings — use `parse` instead.
* Don't rely on the default `innerunique` join flavor — always specify `kind=` explicitly.
* Don't reference a `let`-bound subquery multiple times without `materialize()`.
* Don't convert data types before filtering — reduce the dataset first, then convert.
* Don't use wildcard table references in `union` — specify tables explicitly.

## Security

### Query Parameters (Injection Prevention)

Always use **query parameters** when incorporating user-provided input. This is the KQL equivalent of SQL parameterized queries and prevents injection attacks.

```kusto
declare query_parameters(maxInjured:long = 90);
StormEvents
| where InjuriesDirect + InjuriesIndirect > maxInjured
```

### Row-Level Security

Use `restrict access to (...)` to limit which tables or views are visible to subsequent statements. This is used by middle-tier applications to enforce row-level security:

```kusto
let SafeView = MyTable | where UserId == "current_user";
restrict access to (SafeView);
```

### General Security Practices

* Never embed credentials or secrets in queries.
* Use parameterized queries for all user-provided input.
* Leverage role-based access control (RBAC) to control query access.
* Management commands (starting with `.`) are syntactically separated from queries, providing a basic security boundary.

## SQL-to-KQL Quick Reference

For users coming from SQL, here are the most common translations:

| SQL | KQL |
|---|---|
| `SELECT * FROM T` | `T` |
| `SELECT col1, col2 FROM T` | `T \| project col1, col2` |
| `SELECT TOP 100 * FROM T` | `T \| take 100` |
| `SELECT * FROM T WHERE col = 'x'` | `T \| where col == "x"` |
| `SELECT * FROM T WHERE col LIKE '%x%'` | `T \| where col has "x"` |
| `SELECT col, COUNT(*) FROM T GROUP BY col` | `T \| summarize count() by col` |
| `SELECT DISTINCT col FROM T` | `T \| distinct col` |
| `SELECT * FROM T ORDER BY col` | `T \| sort by col` |
| `SELECT * FROM T1 JOIN T2 ON T1.k = T2.k` | `T1 \| join kind=inner (T2) on k` |
| `SELECT * FROM T1 UNION SELECT * FROM T2` | `union T1, T2` |

Key differences from SQL:

* KQL uses `==` for equality (not `=`).
* KQL uses double quotes for strings (not single quotes).
* The default join is `innerunique`, not `inner`.
* KQL has no `INSERT`, `UPDATE`, or `DELETE` — it is read-only.
* You can translate SQL to KQL by prefixing a SQL query with `-- explain`.
