# get-datetime

A command-line skill that provides the current datetime in UTC.

## Description

This skill gives agents a simple way to retrieve the current date and time.
Output is always in UTC and formatted as `YYYY-MM-DD_HH-MM-SS` (24-hour format).

## Usage

```bash
python get-datetime.py --now
```

## Arguments

* `--now` - Print the current UTC datetime in `YYYY-MM-DD_HH-MM-SS` format.

## Example

```bash
$ python get-datetime.py --now
2026-03-25_13-29-07
```
